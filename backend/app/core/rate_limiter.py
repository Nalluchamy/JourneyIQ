from collections import defaultdict
import time

from fastapi import HTTPException, Request, status
from app.core.config import settings


class InMemoryRateLimiter:
    """IP-based sliding-window rate limiter for protecting REST routes."""

    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.history: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, request: Request) -> None:
        if settings.ENVIRONMENT == "testing":
            return
        # Resolve client IP address (or fallback to unknown)
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean timestamps falling outside the active window range
        self.history[client_ip] = [
            t for t in self.history[client_ip] if now - t < self.window_seconds
        ]

        if len(self.history[client_ip]) >= self.requests_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )

        self.history[client_ip].append(now)
