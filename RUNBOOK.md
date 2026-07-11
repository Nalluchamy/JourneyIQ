# JourneyIQ — Production Monitoring Runbook

> **Version:** 1.0.0 | **Last Updated:** 2026-07-11

This runbook provides step-by-step procedures for monitoring, diagnosing, and resolving production issues in JourneyIQ.

---

## Table of Contents

- [Service Health Checks](#service-health-checks)
- [Common Issues & Resolutions](#common-issues--resolutions)
  - [Database Connection Failures](#1-database-connection-failures)
  - [Redis Unavailable](#2-redis-unavailable)
  - [Model Not Loaded](#3-model-not-loaded)
  - [Scheduler Degraded](#4-scheduler-degraded)
  - [High Error Rate](#5-high-error-rate)
  - [Authentication Failures](#6-authentication-failures)
- [Escalation Procedures](#escalation-procedures)
- [Log Analysis](#log-analysis)
  - [Structured Log Queries](#structured-log-queries)
  - [Error Pattern Detection](#error-pattern-detection)
  - [Request Tracing](#request-tracing)
- [Performance Troubleshooting](#performance-troubleshooting)
  - [Slow Queries](#slow-queries)
  - [High Memory Usage](#high-memory-usage)
  - [CPU Spikes](#cpu-spikes)
  - [API Latency](#api-latency)
- [Prometheus Scrape Configuration](#prometheus-scrape-configuration)

---

## Service Health Checks

### Quick Status Check

Run all health endpoints in sequence to assess overall system health:

```bash
BASE_URL="https://api.journeyiq.com"

# 1. Basic health (DB connectivity + uptime)
curl -s "${BASE_URL}/api/v1/health" | jq '.'

# 2. Aggregated system health (DB + Cache + Scheduler + ML)
curl -s "${BASE_URL}/api/v1/system/health" | jq '.'

# 3. Kubernetes liveness probe
curl -s "${BASE_URL}/api/v1/system/live" | jq '.'

# 4. Kubernetes readiness probe (returns 503 if not ready)
curl -s -w "\nHTTP Status: %{http_code}\n" "${BASE_URL}/api/v1/system/ready" | jq '.'

# 5. System metrics (CPU, memory, DB ping)
curl -s "${BASE_URL}/api/v1/system/metrics" | jq '.'

# 6. Deployment configuration (masked secrets)
curl -s "${BASE_URL}/api/v1/system/deployment" | jq '.'

# 7. Runtime information (uptime, PID, platform)
curl -s "${BASE_URL}/api/v1/system/runtime" | jq '.'

# 8. Model registry (active model, checkpoints, inference)
curl -s "${BASE_URL}/api/v1/system/models" | jq '.'

# 9. Cache statistics (hits, misses, Redis status)
curl -s "${BASE_URL}/api/v1/system/cache" | jq '.'

# 10. Database pool metrics (connections, DB size)
curl -s "${BASE_URL}/api/v1/system/database" | jq '.'

# 11. Log telemetry (error counts, file size)
curl -s "${BASE_URL}/api/v1/system/logs" | jq '.'

# 12. Prometheus metrics (plain text format)
curl -s "${BASE_URL}/api/v1/system/prometheus"

# 13. NGINX healthz endpoint
curl -s "https://www.journeyiq.com/healthz" | jq '.'
```

### Expected Healthy Response

```json
{
  "success": true,
  "message": "System status diagnostics collected.",
  "data": {
    "status": "healthy",
    "database": "connected",
    "cache": "connected",
    "scheduler": "healthy",
    "recommendation_engine": "healthy"
  }
}
```

### Interpreting Status Values

| Component | Status | Meaning | Action |
|---|---|---|---|
| **Overall** | `healthy` | All services operational | None |
| **Overall** | `degraded` | One or more services impaired | Investigate sub-components |
| **Database** | `connected` | DB responding to `SELECT 1` | None |
| **Database** | `disconnected` | DB unreachable | See [Database Connection Failures](#1-database-connection-failures) |
| **Cache** | `connected` | Redis or in-memory cache operational | None |
| **Cache** | `degraded` | Redis down, using in-memory fallback | See [Redis Unavailable](#2-redis-unavailable) |
| **Scheduler** | `healthy` | Last pipeline run succeeded | None |
| **Scheduler** | `degraded` | Pipeline failed after all retries | See [Scheduler Degraded](#4-scheduler-degraded) |

---

## Common Issues & Resolutions

### 1. Database Connection Failures

**Symptoms:**
- `/api/v1/health` returns `503` with `"database": "disconnected"`
- `/api/v1/system/ready` returns `503`
- Backend logs show: `Health check database verification failed`

**Diagnosis:**

```bash
# Check if PostgreSQL container is running
docker ps | grep journeyiq_db

# Check container health
docker inspect --format='{{.State.Health.Status}}' journeyiq_db_prod

# Test connectivity from backend container
docker exec journeyiq_backend_prod python -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.environ['DATABASE_URL'].replace('+asyncpg', ''))
with engine.connect() as conn:
    print(conn.execute(text('SELECT 1')).scalar())
"

# Check PostgreSQL logs
docker logs journeyiq_db_prod --tail 50
```

**Resolution:**

| Cause | Fix |
|---|---|
| PostgreSQL container stopped | `docker compose -f docker-compose.prod.yml up -d db` |
| Container OOM killed | Increase memory: add `mem_limit: 2g` to compose |
| Connection pool exhausted | Restart backend: `docker restart journeyiq_backend_prod` |
| Incorrect DATABASE_URL | Verify env var: `docker exec journeyiq_backend_prod env \| grep DATABASE` |
| Disk full | Check: `docker exec journeyiq_db_prod df -h /var/lib/postgresql/data` |
| Max connections reached | Check: `docker exec journeyiq_db_prod psql -U postgres -c "SELECT count(*) FROM pg_stat_activity"` |

---

### 2. Redis Unavailable

**Symptoms:**
- `/api/v1/system/cache` shows `"type": "in_memory"` or `"redis_connected": false`
- Warning logs: `Redis health check failed. Degraded to memory cache.`

**Diagnosis:**

```bash
# Check Redis container
docker ps | grep journeyiq_redis

# Test Redis connectivity
docker exec journeyiq_redis_prod redis-cli ping
# Expected: PONG

# Check Redis memory usage
docker exec journeyiq_redis_prod redis-cli info memory

# Check Redis logs
docker logs journeyiq_redis_prod --tail 30
```

**Resolution:**

| Cause | Fix |
|---|---|
| Redis container stopped | `docker compose -f docker-compose.prod.yml up -d redis` |
| Redis OOM | Set maxmemory: `docker exec journeyiq_redis_prod redis-cli CONFIG SET maxmemory 256mb` |
| REDIS_URL not configured | Set env var in `.env`: `REDIS_URL=redis://redis:6379/0` |
| Network isolation | Verify both on same Docker network: `docker network inspect journeyiq_net_prod` |

> [!NOTE]
> JourneyIQ automatically falls back to an in-memory cache when Redis is unavailable. The application remains functional but cache is not shared across workers and is lost on restart.

---

### 3. Model Not Loaded

**Symptoms:**
- `/api/v1/system/models` shows `"active_version": "v0.0"` or missing evaluation metrics
- Recommendation endpoints return empty results or errors
- Logs show: `Failed to read model_metadata.json`

**Diagnosis:**

```bash
# Check if model files exist
docker exec journeyiq_backend_prod ls -la /app/models/

# Check model metadata
docker exec journeyiq_backend_prod cat /app/models/model_metadata.json

# Check if latest.pt is valid
docker exec journeyiq_backend_prod python -c "
import torch
checkpoint = torch.load('/app/models/latest.pt', map_location='cpu', weights_only=False)
print('Keys:', list(checkpoint.keys()))
print('Users:', checkpoint.get('num_users', 'N/A'))
print('Products:', checkpoint.get('num_products', 'N/A'))
"
```

**Resolution:**

| Cause | Fix |
|---|---|
| No training has run yet | Trigger manual training (see below) |
| Model files missing | Restore from backup: `tar -xzf backups/models/latest.tar.gz -C backend/` |
| Corrupted checkpoint | Rollback: `curl -X POST localhost:8000/api/v1/system/models/rollback/{version}` |
| Insufficient training data | Ensure products, users, and events exist in the database |

**Trigger Manual Training:**

```bash
docker exec journeyiq_backend_prod python -c "
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.deep_learning.train import train_ncf_model

async def train():
    async with AsyncSessionLocal() as db:
        result = await train_ncf_model(db)
        print('Training complete:', result)

asyncio.run(train())
"
```

---

### 4. Scheduler Degraded

**Symptoms:**
- `/api/v1/system/health` shows `"scheduler": "degraded"`
- Recommendations are stale (not updating daily)
- Logs show: `Daily recommendation pipeline completely failed after all retries`

**Diagnosis:**

```bash
# Check scheduler health status
curl -s http://localhost:8000/api/v1/system/health | jq '.data.scheduler'

# Check last scheduler error in logs
docker exec journeyiq_backend_prod grep -i "pipeline.*failed" /app/logs/app.log | tail -5

# Check scheduler health internals
docker exec journeyiq_backend_prod python -c "
from app.services.ml.scheduler import SCHEDULER_HEALTH
import json
print(json.dumps(SCHEDULER_HEALTH, indent=2, default=str))
"
```

**Resolution:**

The scheduler retries automatically (4 attempts with exponential backoff: 5s → 10s → 20s → 40s). If it reaches `degraded` state:

1. Check the `last_error` field for the root cause
2. Fix the underlying issue (DB, data, memory)
3. Restart the backend to reset the scheduler:

```bash
docker restart journeyiq_backend_prod
```

> [!WARNING]
> The scheduler resets on container restart. If the root cause isn't fixed, it will fail again within 24 hours and return to `degraded` state.

---

### 5. High Error Rate

**Symptoms:**
- `/api/v1/system/logs` shows high `error_ratio_pct`
- Prometheus metric `journeyiq_log_errors_total` is increasing rapidly

**Diagnosis:**

```bash
# Check error ratio
curl -s http://localhost:8000/api/v1/system/logs | jq '.data'

# Get last 20 errors from structured log
docker exec journeyiq_backend_prod \
  grep '"level": "error"' /app/logs/app.log | tail -20 | jq '.'

# Count errors by type
docker exec journeyiq_backend_prod \
  grep '"level": "error"' /app/logs/app.log | \
  jq -r '.event' | sort | uniq -c | sort -rn | head -10
```

**Resolution:**

| Error Rate | Severity | Action |
|---|---|---|
| < 1% | Normal | Monitor, no action |
| 1–5% | Warning | Investigate top error events |
| 5–10% | High | Escalate, check recent deployments |
| > 10% | Critical | Consider rollback, page on-call |

---

### 6. Authentication Failures

**Symptoms:**
- Users report being logged out unexpectedly
- 401 Unauthorized responses on previously working tokens
- Logs show JWT validation errors

**Diagnosis:**

```bash
# Check JWT configuration
curl -s http://localhost:8000/api/v1/system/deployment | jq '.data | {jwt_algorithm, access_token_expire_minutes}'

# Verify JWT_SECRET is set
docker exec journeyiq_backend_prod python -c "
from app.core.config import settings
print('JWT_SECRET set:', bool(settings.JWT_SECRET))
print('Algorithm:', settings.JWT_ALGORITHM)
print('Token expire mins:', settings.ACCESS_TOKEN_EXPIRE_MINUTES)
"
```

**Resolution:**

| Cause | Fix |
|---|---|
| JWT_SECRET changed between deployments | Set consistent secret across all instances |
| Token expired | Normal behavior; client should refresh token |
| Clock skew between servers | Sync NTP: `timedatectl set-ntp true` |
| SECRET_KEY is default value | Set production secret: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |

---

## Escalation Procedures

### Severity Levels

| Level | Criteria | Response Time | Notification |
|---|---|---|---|
| **P1 — Critical** | Service completely down, data loss risk | 15 minutes | Page on-call + team lead |
| **P2 — High** | Major feature broken, degraded performance | 1 hour | Slack alert + on-call |
| **P3 — Medium** | Minor feature broken, workaround available | 4 hours | Slack alert |
| **P4 — Low** | Cosmetic issues, non-critical bugs | Next business day | Ticket |

### Escalation Matrix

| Issue | First Responder | Escalation | Final Escalation |
|---|---|---|---|
| Database outage | On-call engineer | DBA / Platform team | Engineering lead |
| ML model failure | On-call engineer | ML engineer | ML team lead |
| Security incident | On-call engineer | Security team | CTO |
| Infrastructure failure | On-call engineer | DevOps team | Engineering lead |
| Performance degradation | On-call engineer | Backend team | Engineering lead |

### Escalation Checklist

Before escalating, collect:

- [ ] Current service health status (all endpoints)
- [ ] Relevant log excerpts (last 50 error lines)
- [ ] Time issue first detected
- [ ] Impact scope (all users / specific users / specific feature)
- [ ] Recent deployments or config changes
- [ ] Attempted remediation steps and results

---

## Log Analysis

### Structured Log Queries

JourneyIQ writes structured JSON logs to `logs/app.log`. Use `jq` for analysis:

```bash
# All errors in the last hour
docker exec journeyiq_backend_prod \
  cat /app/logs/app.log | jq 'select(.level == "error")' | tail -50

# Errors with stack traces
docker exec journeyiq_backend_prod \
  grep '"level": "error"' /app/logs/app.log | \
  jq 'select(.exc_info != null) | {event, error: .exc_info[:200]}'

# Slow requests (> 500ms)
docker exec journeyiq_backend_prod \
  grep '"Request completed"' /app/logs/app.log | \
  jq 'select(.duration_ms > 500) | {endpoint, method, duration_ms, status_code}'

# Failed requests (5xx)
docker exec journeyiq_backend_prod \
  grep '"Request completed"' /app/logs/app.log | \
  jq 'select(.status_code >= 500) | {endpoint, method, duration_ms, status_code, request_id}'

# Request volume by endpoint
docker exec journeyiq_backend_prod \
  grep '"Request started"' /app/logs/app.log | \
  jq -r '.endpoint' | sort | uniq -c | sort -rn | head -20
```

### Error Pattern Detection

```bash
# Top 10 most frequent error messages
docker exec journeyiq_backend_prod \
  grep '"level": "error"' /app/logs/app.log | \
  jq -r '.event' | sort | uniq -c | sort -rn | head -10

# Errors grouped by hour
docker exec journeyiq_backend_prod \
  grep '"level": "error"' /app/logs/app.log | \
  jq -r '.timestamp[:13]' | sort | uniq -c

# Database-related errors
docker exec journeyiq_backend_prod \
  grep -i "database\|sqlalchemy\|postgresql\|connection" /app/logs/app.log | \
  grep '"level": "error"' | tail -20

# ML/Training errors
docker exec journeyiq_backend_prod \
  grep -i "ncf\|training\|model\|inference\|torch" /app/logs/app.log | \
  grep '"level": "error"' | tail -20
```

### Request Tracing

Each request is tagged with a unique `request_id`. Trace a specific request:

```bash
# Find all log entries for a specific request
REQUEST_ID="abc-123-def-456"
docker exec journeyiq_backend_prod \
  grep "${REQUEST_ID}" /app/logs/app.log | jq '.'
```

---

## Performance Troubleshooting

### Slow Queries

**Detection:**

```bash
# Check DB ping latency
curl -s http://localhost:8000/api/v1/system/metrics | jq '.data.database_ping_ms'
# Expected: < 50ms

# Check database connection pool
curl -s http://localhost:8000/api/v1/system/database | jq '.data'

# Find slow requests in logs
docker exec journeyiq_backend_prod \
  grep '"Request completed"' /app/logs/app.log | \
  jq 'select(.duration_ms > 1000) | {endpoint, duration_ms}' | head -20
```

**Resolution:**

| Symptom | Cause | Fix |
|---|---|---|
| DB ping > 50ms | Network latency or load | Check DB server resources |
| Many checked-out connections | Connection leak | Restart backend, check async session cleanup |
| Specific endpoint slow | Missing index | Add database index, optimize query |
| All endpoints slow | DB overloaded | Scale DB, add read replicas |

```bash
# Check PostgreSQL active queries
docker exec journeyiq_db_prod psql -U postgres -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration,
       query, state
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT ILIKE '%pg_stat_activity%'
ORDER BY duration DESC
LIMIT 10;"
```

### High Memory Usage

**Detection:**

```bash
# Check via API
curl -s http://localhost:8000/api/v1/system/metrics | jq '.data.memory_usage_mb'

# Check via Docker
docker stats --no-stream journeyiq_backend_prod

# Detailed process memory
docker exec journeyiq_backend_prod python -c "
import psutil, os
p = psutil.Process(os.getpid())
print(f'RSS: {p.memory_info().rss / 1024 / 1024:.1f} MB')
print(f'VMS: {p.memory_info().vms / 1024 / 1024:.1f} MB')
"
```

**Resolution:**

| Memory Level | Status | Action |
|---|---|---|
| < 256 MB | Normal | No action |
| 256–512 MB | Elevated | Monitor, may be training |
| 512 MB–1 GB | High | Check for memory leaks, large datasets |
| > 1 GB | Critical | Restart container, investigate leaks |

```bash
# Restart to free memory
docker restart journeyiq_backend_prod

# Add memory limit to docker-compose
# mem_limit: 1g
```

### CPU Spikes

**Detection:**

```bash
# Check via API
curl -s http://localhost:8000/api/v1/system/metrics | jq '.data.cpu_usage_pct'

# Docker stats
docker stats --no-stream

# Check if training is running
docker exec journeyiq_backend_prod \
  grep "NCF training" /app/logs/app.log | tail -5
```

**Expected CPU Patterns:**

| Time | CPU | Cause |
|---|---|---|
| During training (daily 3 AM) | 60–90% | NCF model training — **normal** |
| During evaluation | 30–50% | Generating predictions for all users — **normal** |
| Idle / normal traffic | 5–15% | API request handling — **normal** |
| Sustained > 80% outside training | — | **Investigate** |

### API Latency

**Detection:**

```bash
# Check average inference latency
curl -s http://localhost:8000/api/v1/system/models | jq '.data.inference_statistics.average_latency_ms'

# Benchmark specific endpoints
for i in {1..10}; do
  curl -s -o /dev/null -w "%{time_total}\n" http://localhost:8000/api/v1/health
done

# P95 latency from logs
docker exec journeyiq_backend_prod \
  grep '"Request completed"' /app/logs/app.log | \
  jq -r '.duration_ms' | sort -n | \
  awk 'BEGIN{c=0} {a[c++]=$1} END{print "P50:", a[int(c*0.5)], "P95:", a[int(c*0.95)], "P99:", a[int(c*0.99)]}'
```

**Expected Latencies:**

| Endpoint | Target | Max Acceptable |
|---|---|---|
| `/health` | < 50ms | 200ms |
| `/system/live` | < 5ms | 50ms |
| `/system/metrics` | < 100ms | 500ms |
| Recommendation endpoints | < 200ms | 500ms |
| Product CRUD | < 100ms | 300ms |
| Authentication | < 100ms | 300ms |

---

## Prometheus Scrape Configuration

### Basic Setup

```yaml
# prometheus.yml
global:
  scrape_interval: 30s
  evaluation_interval: 30s

scrape_configs:
  - job_name: 'journeyiq-backend'
    scrape_interval: 30s
    metrics_path: '/api/v1/system/prometheus'
    static_configs:
      - targets: ['backend:8000']
        labels:
          app: 'journeyiq'
          component: 'backend'
          environment: 'production'

  - job_name: 'journeyiq-nginx'
    scrape_interval: 60s
    metrics_path: '/healthz'
    static_configs:
      - targets: ['frontend:80']
        labels:
          app: 'journeyiq'
          component: 'nginx'
```

### Available Prometheus Metrics

| Metric Name | Type | Description |
|---|---|---|
| `journeyiq_system_cpu_usage_ratio` | gauge | CPU usage as ratio (0.0–1.0) |
| `journeyiq_system_memory_usage_bytes` | gauge | Process RSS memory in bytes |
| `journeyiq_db_ping_ms` | gauge | Database round-trip latency in ms |
| `journeyiq_db_pool_size` | gauge | Max connection pool size |
| `journeyiq_db_pool_checked_out` | gauge | Active (in-use) connections |
| `journeyiq_cache_hits_total` | counter | Total cache hits |
| `journeyiq_cache_misses_total` | counter | Total cache misses |
| `journeyiq_ml_inferences_total` | counter | Total NCF inference requests |
| `journeyiq_ml_inference_latency_avg_ms` | gauge | Average inference latency in ms |
| `journeyiq_ml_model_val_loss` | gauge | Active model validation loss |
| `journeyiq_log_errors_total` | counter | Total error log entries |

### Grafana Dashboard Panels (Recommended)

| Panel | Query | Visualization |
|---|---|---|
| Service Uptime | `up{job="journeyiq-backend"}` | Stat (green/red) |
| DB Latency | `journeyiq_db_ping_ms` | Time series |
| Memory Usage | `journeyiq_system_memory_usage_bytes / 1024 / 1024` | Gauge (MB) |
| Cache Hit Ratio | `rate(journeyiq_cache_hits_total[5m]) / (rate(journeyiq_cache_hits_total[5m]) + rate(journeyiq_cache_misses_total[5m]))` | Percentage gauge |
| ML Inference Rate | `rate(journeyiq_ml_inferences_total[5m])` | Time series |
| Error Rate | `rate(journeyiq_log_errors_total[5m])` | Time series with threshold |
| Model Quality | `journeyiq_ml_model_val_loss` | Gauge with thresholds |

### Alert Rules

```yaml
# prometheus_alerts.yml
groups:
  - name: journeyiq
    rules:
      - alert: JourneyIQDown
        expr: up{job="journeyiq-backend"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "JourneyIQ backend is down"

      - alert: HighDBLatency
        expr: journeyiq_db_ping_ms > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database latency exceeds 100ms"

      - alert: HighErrorRate
        expr: rate(journeyiq_log_errors_total[5m]) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Error rate exceeds 1 error/second"

      - alert: HighMemory
        expr: journeyiq_system_memory_usage_bytes > 1073741824
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage exceeds 1GB for 15 minutes"

      - alert: MLInferenceStalled
        expr: increase(journeyiq_ml_inferences_total[1h]) == 0
        for: 2h
        labels:
          severity: warning
        annotations:
          summary: "No ML inferences in the last 2 hours"

      - alert: ModelQualityDegraded
        expr: journeyiq_ml_model_val_loss > 0.5
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Model validation loss exceeds 0.5"
```

---

*For backup and disaster recovery, see [BACKUP.md](BACKUP.md). For deployment checklist, see [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md).*
