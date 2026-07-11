import datetime
import structlog
from typing import Any, Optional

logger = structlog.get_logger()

# Bounded memory cache storage
_MEM_CACHE: dict[str, tuple[datetime.datetime, Any]] = {}


class ApplicationCache:
    """Caching service with Redis integration and graceful in-memory fallbacks."""

    def __init__(self):
        self.redis_client = None
        self.use_redis = False
        
        try:
            from app.core.config import settings
            redis_url = getattr(settings, "REDIS_URL", None)
            if redis_url:
                import redis
                # Initialize connection with quick timeout limits
                self.redis_client = redis.from_url(redis_url, socket_timeout=1.5, socket_connect_timeout=1.5)
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Connected to Redis cache successfully.")
        except Exception as e:
            logger.warning(
                "Redis connection failed or not configured. Falling back to in-memory caching.",
                error=str(e)
            )

    def get(self, key: str) -> Optional[Any]:
        if self.use_redis and self.redis_client:
            try:
                import pickle
                val = self.redis_client.get(key)
                if val:
                    return pickle.loads(val)
            except Exception as e:
                logger.warning("Redis GET failed. Falling back to in-memory cache.", error=str(e))
        
        # Memory Cache Fallback
        if key in _MEM_CACHE:
            expire_at, val = _MEM_CACHE[key]
            if datetime.datetime.now() < expire_at:
                return val
            else:
                del _MEM_CACHE[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 900) -> None:
        if self.use_redis and self.redis_client:
            try:
                import pickle
                self.redis_client.setex(key, ttl_seconds, pickle.dumps(value))
                return
            except Exception as e:
                logger.warning("Redis SET failed. Falling back to in-memory cache.", error=str(e))
                
        # Memory Cache Fallback
        expire_at = datetime.datetime.now() + datetime.timedelta(seconds=ttl_seconds)
        _MEM_CACHE[key] = (expire_at, value)

    def delete(self, key: str) -> None:
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
                return
            except Exception as e:
                logger.warning("Redis DELETE failed. Falling back to in-memory cache.", error=str(e))
        
        # Memory Cache Fallback
        if key in _MEM_CACHE:
            del _MEM_CACHE[key]

    def clear(self) -> None:
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.flushdb()
                return
            except Exception as e:
                logger.warning("Redis FLUSH failed. Falling back to in-memory cache.", error=str(e))
        _MEM_CACHE.clear()


cache = ApplicationCache()
