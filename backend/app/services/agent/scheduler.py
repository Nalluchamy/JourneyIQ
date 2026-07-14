import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.session import AsyncSessionLocal
from app.services.agent.orchestrator import AgentOrchestrator

logger = logging.getLogger("journeyiq")

# Global health status tracking for scheduler checks
AGENT_SCHEDULER_HEALTH = {
    "status": "healthy",
    "last_run": None,
    "consecutive_failures": 0,
    "last_error": None
}

scheduler = AsyncIOScheduler()


async def run_scheduled_agent_orchestrator() -> None:
    """
    Executes the full Agent orchestrator run loop in the background:
    Perceive/Observe -> Analyze -> Plan.
    """
    logger.info("Executing scheduled Agent loop run step")
    try:
        async with AsyncSessionLocal() as db:
            orchestrator = AgentOrchestrator(db)
            await orchestrator.run_orchestrator_loop()
            
        AGENT_SCHEDULER_HEALTH["status"] = "healthy"
        AGENT_SCHEDULER_HEALTH["consecutive_failures"] = 0
        AGENT_SCHEDULER_HEALTH["last_run"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        logger.info("Scheduled Agent loop executed successfully")
    except Exception as e:
        AGENT_SCHEDULER_HEALTH["consecutive_failures"] += 1
        AGENT_SCHEDULER_HEALTH["last_error"] = str(e)
        AGENT_SCHEDULER_HEALTH["status"] = "degraded"
        logger.error(f"Scheduled Agent loop execution failed: {e}")


def start_agent_scheduler() -> None:
    """
    Starts the APScheduler background loops.
    """
    logger.info("Starting background Agent scheduler task loops")
    # Execute every 5 minutes (configurable interval)
    scheduler.add_job(
        run_scheduled_agent_orchestrator,
        trigger="interval",
        minutes=5,
        id="agent_orchestrator_loop",
        replace_existing=True
    )
    scheduler.start()


def stop_agent_scheduler() -> None:
    """
    Gracefully stops the APScheduler loops.
    """
    logger.info("Stopping background Agent scheduler task loops")
    scheduler.shutdown()


# Import datetime here inside functions or at the top if clean
import datetime
