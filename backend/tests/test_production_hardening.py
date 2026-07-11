import asyncio
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.core.cache import cache
from app.core.rate_limiter import InMemoryRateLimiter
from app.main import app


@pytest.mark.anyio
async def test_system_endpoints(client: AsyncClient) -> None:
    """Verifies that all versioned /system endpoints exist and return valid responses."""
    # 1. Liveness
    res = await client.get("/api/v1/system/live")
    assert res.status_code == 200
    assert res.json() == {"status": "alive"}

    # 2. Readiness
    res = await client.get("/api/v1/system/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"

    # 3. Health
    res = await client.get("/api/v1/system/health")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "database" in res.json()["data"]

    # 4. Metrics
    res = await client.get("/api/v1/system/metrics")
    assert res.status_code == 200
    assert "memory_usage_mb" in res.json()["data"]

    # 5. Version
    res = await client.get("/api/v1/system/version")
    assert res.status_code == 200
    assert res.json()["data"]["project"] == "JourneyIQ"


@pytest.mark.anyio
async def test_security_headers_and_correlation_id(client: AsyncClient) -> None:
    """Verifies that CSP, frame, cross-origin protection headers, and request correlation IDs are injected."""
    res = await client.get("/api/v1/system/live")
    assert res.status_code == 200

    # Check Security headers
    assert res.headers["X-Frame-Options"] == "DENY"
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert "Content-Security-Policy" in res.headers
    assert "Referrer-Policy" in res.headers

    # Check Request ID (Correlation ID) is present in response headers
    assert "X-Request-ID" in res.headers


@pytest.mark.anyio
async def test_timeout_middleware_trigger(client: AsyncClient) -> None:
    """Mocks a request timeout to verify the Gateway Timeout HTTP 504 response formatting."""
    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
        res = await client.get("/api/v1/system/live")
        assert res.status_code == 504
        assert res.json()["success"] is False
        assert res.json()["error"] == "GatewayTimeout"
        assert "request_id" in res.json()


@pytest.mark.anyio
async def test_rate_limiter_unit() -> None:
    """Tests the sliding window rate limiter logic in isolation."""
    from app.core.config import settings
    original_env = settings.ENVIRONMENT
    settings.ENVIRONMENT = "production"
    
    try:
        limiter = InMemoryRateLimiter(requests_limit=2, window_seconds=60)

        request = Mock()
        request.client.host = "127.0.0.1"
        request.state.user = None
        request.state.request_id = "test-request-id"
        request.url.path = "/api/v1/system/live"

        # Allow first 2 requests
        await limiter(request)
        await limiter(request)

        # Exceed limit on the 3rd request -> raise HTTP 429
        with pytest.raises(HTTPException) as exc_info:
            await limiter(request)
        
        assert exc_info.value.status_code == 429
        assert exc_info.value.detail["error"] == "TooManyRequests"
    finally:
        settings.ENVIRONMENT = original_env


def test_caching_coordinator() -> None:
    """Verifies cache SET, GET, DELETE operations run and fallback gracefully."""
    cache.clear()
    
    # Assert get on non-existent key returns None
    assert cache.get("non_existent_key") is None

    # Assert set and get works
    cache.set("test_key", {"data": "journeyiq"}, ttl_seconds=10)
    assert cache.get("test_key") == {"data": "journeyiq"}

    # Assert delete works
    cache.delete("test_key")
    assert cache.get("test_key") is None
