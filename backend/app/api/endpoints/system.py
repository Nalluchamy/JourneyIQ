import json
import os
import sys
import time
from typing import Any

import psutil
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.config import settings
from app.db.session import engine, get_db
from app.schemas.response import APIResponse
from app.services.deep_learning.registry import NCFModelRegistry
from app.services.ml.scheduler import SCHEDULER_HEALTH

logger = structlog.get_logger()
router = APIRouter()
LOG_FILE_PATH = "logs/app.log"
PROCESS_START_TIME = time.time()


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
    return True


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

    process = psutil.Process(os.getpid())
    memory_mb = round(process.memory_info().rss / (1024 * 1024), 2)
    cpu_pct = round(psutil.cpu_percent(), 2)

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


@router.get("/deployment", response_model=APIResponse[dict[str, Any]], summary="Get Deployment settings")
async def get_deployment() -> Any:
    """Retrieves masked SaaS cloud settings configuration."""
    return APIResponse(
        success=True,
        message="Deployment variables retrieved.",
        data={
            "environment": settings.ENVIRONMENT,
            "backend_url": settings.BACKEND_URL,
            "frontend_url": settings.FRONTEND_URL,
            "jwt_algorithm": settings.JWT_ALGORITHM,
            "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "require_email_verification": settings.REQUIRE_EMAIL_VERIFICATION,
            "secret_key_masked": "********" if settings.SECRET_KEY else "not-configured",
            "jwt_secret_masked": "********" if settings.JWT_SECRET else "not-configured"
        }
    )


@router.get("/runtime", response_model=APIResponse[dict[str, Any]], summary="Get System Runtime properties")
async def get_runtime() -> Any:
    """Retrieves active CPU, threads, platform, and process load info."""
    process = psutil.Process(os.getpid())
    memory_mb = round(process.memory_info().rss / (1024 * 1024), 2)

    return APIResponse(
        success=True,
        message="Runtime environments statistics aggregated.",
        data={
            "platform": sys.platform,
            "cpu_count": os.cpu_count() or 1,
            "threads_active": len(process.threads()),
            "memory_usage_mb": memory_mb,
            "uptime_seconds": round(time.time() - PROCESS_START_TIME, 2),
            "pid": os.getpid(),
            "python_path": sys.executable
        }
    )


@router.get("/models", response_model=APIResponse[dict[str, Any]], summary="Get Model Registry status")
async def get_models() -> Any:
    """Gathers deep learning model version checks and accuracy stats."""
    active = NCFModelRegistry.get_active_model()
    checkpoints = NCFModelRegistry.list_checkpoints()
    inference = NCFModelRegistry.get_inference_telemetry()

    return APIResponse(
        success=True,
        message="MLOps model metadata stats read.",
        data={
            "active_model": active,
            "inference_statistics": inference,
            "checkpoints_registry": checkpoints
        }
    )


@router.post("/models/rollback/{version_id}", response_model=APIResponse[dict[str, Any]], summary="Trigger Model rollback")
async def post_models_rollback(version_id: str) -> Any:
    """Performs manual rollback to a versioned model state file in the registry."""
    success = NCFModelRegistry.rollback_to_version(version_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint version {version_id} not found or rollback failed."
        )
    return APIResponse(
        success=True,
        message=f"Model registry rolled back to version {version_id}."
    )


@router.get("/cache", response_model=APIResponse[dict[str, Any]], summary="Get Caching metrics")
async def get_cache() -> Any:
    """Retrieves cache hit/miss records and Redis operational flags."""
    stats = cache.get_stats()
    return APIResponse(
        success=True,
        message="Cache statistics retrieved.",
        data={
            "type": "redis" if cache.use_redis else "in_memory",
            "redis_connected": check_cache_connection(),
            "redis_url_configured": bool(settings.REDIS_URL),
            "stats": stats
        }
    )


@router.get("/database", response_model=APIResponse[dict[str, Any]], summary="Get Database pool metrics")
async def get_database(db: AsyncSession = Depends(get_db)) -> Any:
    """Fetches SQLAlchemy active/idle connection pool and database byte size."""
    pool_size = 0
    checked_out = 0
    checked_in = 0
    overflow = 0

    if hasattr(engine, "pool"):
        pool = engine.pool
        pool_size = pool.size()
        checked_in = pool.checkedin() if hasattr(pool, "checkedin") else 0
        checked_out = pool.checkedout() if hasattr(pool, "checkedout") else 0
        overflow = pool.overflow() if hasattr(pool, "overflow") else 0

    tables_count = 0
    db_size_bytes = 0
    try:
        # Check dialect
        if "sqlite" in str(db.bind.url):
            # SQLite specific queries
            db_size_res = await db.execute(text("PRAGMA page_count;"))
            page_count = db_size_res.scalar() or 0
            page_size_res = await db.execute(text("PRAGMA page_size;"))
            page_size = page_size_res.scalar() or 0
            db_size_bytes = page_count * page_size

            tables_count_res = await db.execute(text("SELECT count(*) FROM sqlite_master WHERE type='table'"))
            tables_count = tables_count_res.scalar() or 0
        else:
            # PostgreSQL specific queries
            db_size_res = await db.execute(text("SELECT pg_database_size(current_database())"))
            db_size_bytes = db_size_res.scalar() or 0

            tables_count_res = await db.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"))
            tables_count = tables_count_res.scalar() or 0
    except Exception as e:
        logger.warning("Failed to retrieve database schema metrics", error=str(e))

    return APIResponse(
        success=True,
        message="Database performance metrics gathered.",
        data={
            "pool_size": pool_size,
            "connections_checked_out": checked_out,
            "connections_checked_in": checked_in,
            "overflow_connections": overflow,
            "tables_count": tables_count,
            "database_size_bytes": db_size_bytes
        }
    )


@router.get("/logs", response_model=APIResponse[dict[str, Any]], summary="Get Log telemetry")
async def get_logs() -> Any:
    """Calculates log file capacity and scans for warning/error rates."""
    lines_count = 0
    error_count = 0
    warning_count = 0
    file_size_bytes = 0

    if os.path.exists(LOG_FILE_PATH):
        file_size_bytes = os.path.getsize(LOG_FILE_PATH)
        try:
            with open(LOG_FILE_PATH) as f:
                for line in f:
                    lines_count += 1
                    try:
                        record = json.loads(line)
                        level = record.get("level", "").lower()
                        if level in ("error", "fatal"):
                            error_count += 1
                        elif level in ("warning", "warn"):
                            warning_count += 1
                    except Exception:
                        pass
        except Exception as e:
            logger.warning("Error scanning log file", error=str(e))

    return APIResponse(
        success=True,
        message="Log stats parsed.",
        data={
            "log_file_location": LOG_FILE_PATH,
            "file_size_bytes": file_size_bytes,
            "lines_count": lines_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "error_ratio_pct": round((error_count / lines_count) * 100, 2) if lines_count > 0 else 0.0
        }
    )


@router.get("/prometheus", response_class=PlainTextResponse, summary="Get Prometheus Text metrics")
async def get_prometheus(db: AsyncSession = Depends(get_db)) -> str:
    """Exposes application, system, database, scheduler, cache, and ML NCF metrics in Prometheus text format."""
    db_ping = await check_db_connection(db)

    # OS/System stats
    process = psutil.Process(os.getpid())
    memory_mb = round(process.memory_info().rss / (1024 * 1024), 2)
    cpu_pct = round(psutil.cpu_percent(), 2)

    # Database connection pool stats
    pool_size = 0
    checked_out = 0
    if hasattr(engine, "pool"):
        pool = engine.pool
        pool_size = pool.size()
        checked_out = pool.checkedout() if hasattr(pool, "checkedout") else 0

    # Cache stats
    cache_stats = cache.get_stats()

    # ML Inference stats
    ml_stats = NCFModelRegistry.get_inference_telemetry()
    active_model = NCFModelRegistry.get_active_model()
    best_val_loss = active_model.get("best_val_loss", 0.0)

    # Log stats
    error_count = 0
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH) as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record.get("level", "").lower() in ("error", "fatal"):
                            error_count += 1
                    except Exception:
                        pass
        except Exception:
            pass

    # Build Prometheus Text response format
    lines = [
        "# HELP journeyiq_system_cpu_usage_ratio CPU usage ratio",
        "# TYPE journeyiq_system_cpu_usage_ratio gauge",
        f"journeyiq_system_cpu_usage_ratio {cpu_pct / 100.0:.4f}",
        "",
        "# HELP journeyiq_system_memory_usage_bytes Process memory usage in bytes",
        "# TYPE journeyiq_system_memory_usage_bytes gauge",
        f"journeyiq_system_memory_usage_bytes {memory_mb * 1024 * 1024:.1f}",
        "",
        "# HELP journeyiq_db_ping_ms Database ping latency in milliseconds",
        "# TYPE journeyiq_db_ping_ms gauge",
        f"journeyiq_db_ping_ms {db_ping if db_ping is not None else -1.0:.2f}",
        "",
        "# HELP journeyiq_db_pool_size Database connection pool maximum size",
        "# TYPE journeyiq_db_pool_size gauge",
        f"journeyiq_db_pool_size {pool_size}",
        "",
        "# HELP journeyiq_db_pool_checked_out Database active connections checked out",
        "# TYPE journeyiq_db_pool_checked_out gauge",
        f"journeyiq_db_pool_checked_out {checked_out}",
        "",
        "# HELP journeyiq_cache_hits_total Total cache hits",
        "# TYPE journeyiq_cache_hits_total counter",
        f"journeyiq_cache_hits_total {cache_stats['hits']}",
        "",
        "# HELP journeyiq_cache_misses_total Total cache misses",
        "# TYPE journeyiq_cache_misses_total counter",
        f"journeyiq_cache_misses_total {cache_stats['misses']}",
        "",
        "# HELP journeyiq_ml_inferences_total Total Deep Learning inference requests",
        "# TYPE journeyiq_ml_inferences_total counter",
        f"journeyiq_ml_inferences_total {ml_stats['total_inference_calls']}",
        "",
        "# HELP journeyiq_ml_inference_latency_avg_ms Average NCF inference latency in ms",
        "# TYPE journeyiq_ml_inference_latency_avg_ms gauge",
        f"journeyiq_ml_inference_latency_avg_ms {ml_stats['average_latency_ms']:.4f}",
        "",
        "# HELP journeyiq_ml_model_val_loss Active model validation loss score",
        "# TYPE journeyiq_ml_model_val_loss gauge",
        f"journeyiq_ml_model_val_loss {best_val_loss:.5f}",
        "",
        "# HELP journeyiq_log_errors_total Total error logs recorded",
        "# TYPE journeyiq_log_errors_total counter",
        f"journeyiq_log_errors_total {error_count}"
    ]
    return "\n".join(lines) + "\n"


@router.post("/demo-reset", response_model=APIResponse[dict[str, Any]], summary="Reset and re-seed database with demo data")
async def post_demo_reset(db: AsyncSession = Depends(get_db)) -> Any:
    """Resets all transaction, order, history, and analytic tables, then re-seeds clean demo database records."""
    try:
        # Ensure parent path is in python path to load seed script
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        if base_dir not in sys.path:
            sys.path.append(base_dir)

        from seed import clear_database, seed_database

        # Clear database records
        await clear_database(db)

        # Re-run seed database script
        await seed_database()

        # Invalidate the application cache stats
        cache.clear()

        return APIResponse(
            success=True,
            message="Database successfully reset and re-seeded with demo records.",
            data={"status": "completed"}
        )
    except Exception as e:
        logger.error("Demo database reset and seed failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database reset failed: {e!s}"
        )

