import asyncio
import time

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.product import Product
from app.models.user import User
from app.services.deep_learning.dataset import build_interaction_matrix
from app.services.deep_learning.evaluate import DeepLearningEvaluator
from app.services.deep_learning.predict import NCFPredictor
from app.services.deep_learning.train import train_ncf_model
from app.services.ml.recommendation_service import RecommendationService

logger = structlog.get_logger()

# Global status tracking for container readiness checks
SCHEDULER_HEALTH = {
    "status": "healthy",
    "last_run": None,
    "consecutive_failures": 0,
    "last_error": None
}

_scheduler_task: asyncio.Task | None = None


async def run_ncf_evaluation_pipeline(db: AsyncSession) -> None:
    """Pre-generates NCF predictions and runs precision/recall/NDCG evaluation."""
    users = (await db.execute(select(User).where(User.is_deleted == False))).scalars().all()
    products = (await db.execute(select(Product).where(Product.is_deleted == False, Product.is_active == True))).scalars().all()
    product_ids = [p.id for p in products]

    interactions = await build_interaction_matrix(db)
    ground_truth = {}
    for item in interactions:
        u_id = item["user_id"]
        p_id = item["product_id"]
        if u_id not in ground_truth:
            ground_truth[u_id] = []
        ground_truth[u_id].append(p_id)

    predictor = NCFPredictor()
    recommendations = {}
    for user in users:
        recs = await predictor.recommend_for_user(user.id, db, limit=10)
        recommendations[user.id] = [r["product"].id for r in recs if r.get("product")]

    DeepLearningEvaluator.evaluate_and_save(recommendations, ground_truth, product_ids, k=10)


async def run_daily_pipeline() -> None:
    """Runs recommendation computation loop with retry policies."""
    while True:
        logger.info("Running scheduled daily recommendations generation")
        success = False
        backoff = 5.0

        # 1 initial run + 3 retries = 4 total attempts
        for attempt in range(4):
            try:
                async with AsyncSessionLocal() as db:
                    # 1. Existing Hybrid Recommender
                    service = RecommendationService(db)
                    await service.compute_and_persist_recommendations()

                    # 2. Deep Learning Model Training
                    logger.info("Starting scheduled daily NCF model training")
                    await train_ncf_model(db)

                    # 3. Deep Learning Metrics Evaluation
                    logger.info("Starting scheduled NCF model evaluation")
                    await run_ncf_evaluation_pipeline(db)

                success = True
                SCHEDULER_HEALTH["status"] = "healthy"
                SCHEDULER_HEALTH["consecutive_failures"] = 0
                SCHEDULER_HEALTH["last_run"] = time.time()
                logger.info("Daily recommendations generation completed successfully")
                break
            except Exception as e:
                SCHEDULER_HEALTH["consecutive_failures"] += 1
                SCHEDULER_HEALTH["last_error"] = str(e)
                logger.error(
                    "Recommendation pipeline attempt failed",
                    attempt=attempt + 1,
                    error=str(e)
                )
                if attempt < 3:
                    logger.info(f"Retrying pipeline execution in {backoff} seconds...")
                    await asyncio.sleep(backoff)
                    backoff *= 2.0

        if not success:
            SCHEDULER_HEALTH["status"] = "degraded"
            logger.error("Daily recommendation pipeline completely failed after all retries.")

        # Sleep for 24 hours
        await asyncio.sleep(86400)


async def run_hourly_metrics_logger() -> None:
    """Simulates updating trending models/metrics hourly and refreshes inference caches."""
    while True:
        logger.info("Running scheduled hourly update for trending products and NCF model state")
        try:
            # Re-read/load latest.pt weights into predictor instance
            predictor = NCFPredictor()
            predictor._load_model()
            logger.info("Hourly NCF model weights refresh completed successfully")
        except Exception as e:
            logger.error("Failed to reload NCF model weights hourly", error=str(e))

        # Sleep for 1 hour
        await asyncio.sleep(3600)


def start_scheduler() -> None:
    """Start background loops."""
    global _scheduler_task
    logger.info("Starting background recommendations scheduler tasks")
    loop = asyncio.get_event_loop()
    _scheduler_task = loop.create_task(asyncio.gather(
        run_daily_pipeline(),
        run_hourly_metrics_logger()
    ))


def stop_scheduler() -> None:
    """Cancel background loops."""
    global _scheduler_task
    if _scheduler_task:
        logger.info("Stopping background recommendations scheduler tasks")
        _scheduler_task.cancel()

