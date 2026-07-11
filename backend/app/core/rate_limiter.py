from collections import defaultdict
import time
import structlog
from fastapi import HTTPException, Request, status
from app.core.config import settings

logger = structlog.get_logger()


class InMemoryRateLimiter:
    """IP/User-based sliding-window rate limiter for protecting REST routes."""

    def __init__(self, requests_limit: int, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.history: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, request: Request) -> None:
        if settings.ENVIRONMENT == "testing":
            return
        
        client_ip = request.client.host if request.client else "unknown"
        
        # Resolve user ID context if exists
        user_id = None
        user_obj = getattr(request.state, "user", None)
        if user_obj:
            user_id = getattr(user_obj, "id", None)
            
        client_key = f"user_{user_id}" if user_id else f"ip_{client_ip}"
        path = request.url.path
        limit_key = f"{client_key}:{path}"
        now = time.time()

        # Clean timestamps falling outside the active window range
        self.history[limit_key] = [
            t for t in self.history[limit_key] if now - t < self.window_seconds
        ]

        if len(self.history[limit_key]) >= self.requests_limit:
            logger.warning("Rate limit exceeded", key=limit_key, path=path, count=len(self.history[limit_key]))
            request_id = getattr(request.state, "request_id", "unknown")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "success": False,
                    "error": "TooManyRequests",
                    "message": f"Rate limit exceeded. Maximum of {self.requests_limit} requests per {self.window_seconds}s allowed.",
                    "request_id": request_id
                }
            )

        self.history[limit_key].append(now)
