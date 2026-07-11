import time
import structlog
from fastapi import Request, HTTPException, status

logger = structlog.get_logger()

# Thread-safe in-memory store for rate limiting requests
RATE_LIMIT_STORE: dict[str, list[float]] = {}


class RateLimit:
    """Sliding window rate-limiter dependency checking client IP or User ID."""

    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if auth profile is set on request state
        user_id = None
        user_obj = getattr(request.state, "user", None)
        if user_obj:
            user_id = getattr(user_obj, "id", None)
            
        client_key = f"user_{user_id}" if user_id else f"ip_{client_ip}"
        path = request.url.path
        
        limit_key = f"{client_key}:{path}"
        now = time.time()
        
        if limit_key not in RATE_LIMIT_STORE:
            RATE_LIMIT_STORE[limit_key] = []
            
        # Clean older requests outside window
        RATE_LIMIT_STORE[limit_key] = [
            t for t in RATE_LIMIT_STORE[limit_key] if now - t < self.window_seconds
        ]
        
        if len(RATE_LIMIT_STORE[limit_key]) >= self.max_requests:
            logger.warning(
                "Rate limit exceeded",
                limit_key=limit_key,
                path=path,
                count=len(RATE_LIMIT_STORE[limit_key])
            )
            request_id = getattr(request.state, "request_id", "unknown")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "success": False,
                    "error": "TooManyRequests",
                    "message": f"Rate limit exceeded. Limit is {self.max_requests} requests per {self.window_seconds}s.",
                    "request_id": request_id
                }
            )
            
        RATE_LIMIT_STORE[limit_key].append(now)
