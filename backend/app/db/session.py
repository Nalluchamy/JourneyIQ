from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.logging_config import logger

# Ensure database URL uses asyncpg for async PostgreSQL connections
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

logger.info(
    "Initializing async database connection pool", target_host=db_url.split("@")[-1]
)

# Create the async engine
engine_kwargs = {
    "echo": False,
    "future": True,
}
# Only apply connection pooling settings for PostgreSQL
if not db_url.startswith("sqlite"):
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 10
    if settings.ENVIRONMENT.lower() in ("production", "prod", "staging"):
        engine_kwargs["connect_args"] = {"ssl": "require"}

engine = create_async_engine(db_url, **engine_kwargs)

# Slow Query Logging Event Listeners
import time

from sqlalchemy import event


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, execmany):
    context._query_start_time = time.time()

@event.listens_for(engine.sync_engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, execmany):
    if hasattr(context, "_query_start_time"):
        total_time = time.time() - context._query_start_time
        if total_time > 0.5:
            logger.warning(
                "Slow database query detected",
                query=statement,
                duration_ms=round(total_time * 1000, 2),
            )

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Dependency injection generator for database sessions.

    Yields:
        AsyncSession: The database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(
                "Database session transaction error. Rolling back...", error=str(e)
            )
            await session.rollback()
            raise
        finally:
            await session.close()
