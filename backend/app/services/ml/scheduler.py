import asyncio
import structlog
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.db.session import SessionLocal
from app.services.ml.recommendation_service import RecommendationService

logger = structlog.get_logger()

# Global cancel handle
_scheduler_task: asyncio.Task | None = None


async def run_daily_pipeline() -> None:
    """Runs recommendation computation loop."""
    while True:
        logger.info("Running scheduled daily recommendations generation")
        async with SessionLocal() as db:
            service = RecommendationService(db)
            try:
                await service.compute_and_persist_recommendations()
            except Exception as e:
                logger.error("Error in scheduled recommendation pipeline", error=str(e))
        
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
