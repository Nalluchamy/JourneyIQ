# Observability & Monitoring Runbook — JourneyIQ v1.5.0

JourneyIQ provides complete system diagnostic metrics, structured telemetry logs, and health status controllers for operations (DevOps/SRE) teams.

---

## 1. Health Status & Probe Mappings

The backend exposes Kubernetes-friendly endpoints at `/api/v1/...` for monitoring status:

| Probe | Endpoint | Check Type | Verification Details | Expected Response |
|---|---|---|---|---|
| **Liveness** | `GET /api/v1/live` | Process check | Verifies FastAPI process is alive | `{"status": "alive"}` (200) |
| **Readiness** | `GET /api/v1/ready` | Network check | Verifies DB ping + Redis client ping | `{"status": "ready"}` (200) |
| **Diagnostics** | `GET /api/v1/health` | Service check | Returns database uptime, environment, and statuses | Uptime metrics (200) |

---

## 2. Dashboard Component Mapping

The SRE Admin Dashboard maps component status using three classifications:

```mermaid
graph LR
    classDef healthy fill:#10b981,color:#fff;
    classDef warning fill:#f59e0b,color:#fff;
    classDef offline fill:#ef4444,color:#fff;

    H[Healthy] :::healthy
    W[Warning] :::warning
    O[Offline] :::offline
```

- **🟢 Healthy (status: 200)**: All checks passing (database responding, cache operational, model registry loaded).
- **🟡 Warning (status: 200/503)**: A sub-service is degraded (e.g. Redis connection offline but falling back to memory cache; or NVIDIA API key is missing).
- **🔴 Offline (status: 503/unreachable)**: Core services unavailable (database is disconnected, or API gateway is unreachable).

---

## 3. Prometheus Scrape Configuration

JourneyIQ exposes a Prometheus-compatible metrics endpoint at `GET /api/v1/system/prometheus`. 

### Scrape Configuration Example
Add the following target to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'journeyiq-backend'
    metrics_path: '/api/v1/system/prometheus'
    scrape_interval: 15s
    static_configs:
      - targets: ['journeyiq-api.onrender.com:443']
        labels:
          environment: 'production'
```

### Exposed Metrics Reference
- `journeyiq_system_cpu_usage_ratio`: Current CPU utilization (gauge).
- `journeyiq_system_memory_usage_bytes`: Current memory footprint (gauge).
- `journeyiq_db_ping_ms`: Database query execution latency (gauge).
- `journeyiq_cache_hits_total`: Count of cached data hits (counter).
- `journeyiq_ml_inferences_total`: Total Deep Learning NCF model inferences executed (counter).
- `journeyiq_ml_inference_latency_avg_ms`: Average PyTorch inference delay (gauge).
- `journeyiq_log_errors_total`: Count of errors written to logger (counter).

---

## 4. Logging & Log Formats

All application processes emit structured logs to stdout and are archived to `logs/app.log`.

### JSON Log Schema
In production, stdout and file logging output structured JSON for elasticsearch/datadog ingestion:

```json
{
  "timestamp": "2026-07-14T06:18:04.123456Z",
  "level": "info",
  "message": "Request completed",
  "logger": "journeyiq",
  "request_id": "89b53b80-87ef-4a59-a5e2-4148e6c464bf",
  "endpoint": "/api/v1/products",
  "method": "GET",
  "status_code": 200,
  "duration_ms": 14.5
}
```
