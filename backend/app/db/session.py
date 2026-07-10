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
engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    pool_pre_ping=True,  # checks connection health before utilizing
    pool_size=20,  # baseline size of pool
    max_overflow=10,  # max temporary connections beyond pool_size
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
