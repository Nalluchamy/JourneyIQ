import os
import sys
import time
import structlog
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings
from app.core.cache import cache
from app.services.ml.scheduler import SCHEDULER_HEALTH
from app.schemas.response import APIResponse

logger = structlog.get_logger()
router = APIRouter()


async def check_db_connection(db: AsyncSession) -> float | None:
    """Measures the database ping execution speed."""
    try:
        start_time = time.time()
        await db.execute(text("SELECT 1"))
        return (time.time() - start_time) * 1000
    except Exception as e:
        logger.error("Database connection health check failed", error=str(e))
        return None


def check_cache_connection() -> bool:
    """Verifies that the caching client is operational."""
    if cache.use_redis:
        try:
            cache.redis_client.ping()
            return True
        except Exception as e:
            logger.warning("Redis health check failed. Degraded to memory cache.", error=str(e))
            return False
    return True  # Local in-memory fallback is always operational


@router.get("/health", response_model=APIResponse[dict[str, Any]], summary="Get System Health status")
async def get_health(db: AsyncSession = Depends(get_db)) -> Any:
    """Aggregates health diagnostics for all core application services."""
    db_ping = await check_db_connection(db)
    cache_ok = check_cache_connection()
    scheduler_status = SCHEDULER_HEALTH["status"]
    
    is_healthy = db_ping is not None and cache_ok and scheduler_status == "healthy"
    
    return APIResponse(
        success=True,
        message="System status diagnostics collected.",
        data={
            "status": "healthy" if is_healthy else "degraded",
            "database": "connected" if db_ping is not None else "disconnected",
            "cache": "connected" if cache_ok else "degraded",
            "scheduler": scheduler_status,
            "recommendation_engine": "healthy" if scheduler_status == "healthy" else "degraded"
        }
    )


@router.get("/live", summary="Liveness Probe Check")
async def get_live() -> dict[str, str]:
    """Instantaneous container status check (Kubernetes Liveness)."""
    return {"status": "alive"}


@router.get("/ready", summary="Readiness Probe Check")
async def get_ready(db: AsyncSession = Depends(get_db)) -> Any:
    """Determines if the container can receive traffic (Kubernetes Readiness)."""
    db_ping = await check_db_connection(db)
    cache_ok = check_cache_connection()
    scheduler_status = SCHEDULER_HEALTH["status"]
    
    # Ready if DB is online and cache is functioning (scheduler degraded doesn't block web traffic)
    if db_ping is None or not cache_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": "online" if db_ping is not None else "offline",
                "cache": "online" if cache_ok else "offline",
                "scheduler": scheduler_status
            }
        )
        
    return {
        "status": "ready",
        "database": "online",
        "cache": "online",
        "scheduler": scheduler_status
    }


@router.get("/metrics", response_model=APIResponse[dict[str, Any]], summary="Get System Metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)) -> Any:
    """Gathers performance metrics (CPU, Memory, DB Ping speeds)."""
    db_ping_ms = await check_db_connection(db)
    
    memory_mb = 0.0
    cpu_pct = 0.0
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_mb = round(process.memory_info().rss / (1024 * 1024), 2)
        cpu_pct = round(psutil.cpu_percent(), 2)
    except ImportError:
        pass  # Fallback gracefully if psutil package is not installed
        
    return APIResponse(
        success=True,
        message="System performance metrics gathered.",
        data={
            "database_ping_ms": round(db_ping_ms, 2) if db_ping_ms is not None else -1.0,
            "memory_usage_mb": memory_mb,
            "cpu_usage_pct": cpu_pct,
            "python_version": sys.version.split(" ")[0]
        }
    )


@router.get("/version", response_model=APIResponse[dict[str, Any]], summary="Get Application Version")
async def get_version() -> Any:
    """Returns application name, version, and running environment metadata."""
    return APIResponse(
        success=True,
        message="Project build information retrieved.",
        data={
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT
        }
    )
