import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging_config import logger
from app.db.session import get_db

router = APIRouter()

# Record backend startup timestamp
START_TIME = time.time()


@router.get("/health", status_code=200)
async def health_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Enhanced health check endpoint verifying database connectivity.

    Returns:
        dict: Health status payload including version, uptime,
            and database connectivity.
    """
    uptime = time.time() - START_TIME
    db_connected = False

    try:
        # Execute simple query SELECT 1 to verify db is alive
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_connected = True
    except Exception as e:
        logger.error("Health check database verification failed", error=str(e))

    if not db_connected:
        logger.error("Health check failed - Database disconnected")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "uptime_seconds": round(uptime, 2),
            },
        )

    return {
        "status": "healthy",
        "database": "connected",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": round(uptime, 2),
    }


@router.get("/live", status_code=200)
async def liveness_check() -> dict[str, str]:
    """Liveness probe to confirm backend process is running."""
    return {"status": "alive"}


@router.get("/ready", status_code=200)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Readiness probe verifying DB and cache connectivity."""
    db_connected = False
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_connected = True
    except Exception as e:
        logger.error("Readiness check database connection failed", error=str(e))

    # Verify cache
    from app.core.cache import cache
    cache_ok = True
    if cache.use_redis:
        try:
            cache.redis_client.ping()
        except Exception:
            cache_ok = False

    if not db_connected or not cache_ok:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "online" if db_connected else "offline",
                "cache": "online" if cache_ok else "offline"
            }
        )

    return {
        "status": "ready",
        "database": "online",
        "cache": "online"
    }

