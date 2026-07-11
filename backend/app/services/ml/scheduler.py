import asyncio
import time
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
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
                    service = RecommendationService(db)
                    await service.compute_and_persist_recommendations()
                
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
    """Simulates updating trending models/metrics hourly."""
    while True:
        logger.info("Running scheduled hourly update for trending products")
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
