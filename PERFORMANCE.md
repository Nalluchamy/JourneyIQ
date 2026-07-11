# Performance Architecture & Caching - JourneyIQ

JourneyIQ is optimized for sub-second responses and low resource consumption using multi-tiered caching, compression, and request timeouts.

## 1. Multi-Tier Caching & Graceful Fallback
Caching routes are controlled via the core `app/core/cache.py` client:
- **Primary Tier**: Redis Cache - Stores serialized JSON responses (like dashboard analytics metrics or AI recommendations).
- **Graceful Fallback**: If Redis is offline or experiences socket timeouts, the caching layer automatically falls back to an **In-Memory dict-based cache**, logs a warning, and continues serving requests without downtime.

## 2. API Execution Limit (30 Seconds)
To prevent long-running requests or hanging database sessions, all REST API requests are governed by a **30-second timeout middleware**:
- If a request does not complete within 30 seconds, `asyncio.timeout` interrupts the task.
- The middleware intercepts the error and returns a clean `504 Gateway Timeout` HTTP response.

## 3. Response Compression
JourneyIQ leverages GZip compression for payloads exceeding 500 bytes to minimize network transmission latency and speed up storefront rendering.
