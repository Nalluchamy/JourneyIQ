# System Diagnostics & Monitoring - JourneyIQ

JourneyIQ has comprehensive diagnostic checkpoints, telemetry, and structured tracing to assist DevOps and SRE teams.

## 1. Diagnostics & Health Endpoints
The health and diagnostics controller exposes standard Kubernetes-friendly status probes:
- **Liveness probe**: `GET /api/v1/system/live` - Returns 200 with `{"status": "alive"}` indicating the container is up.
- **Readiness probe**: `GET /api/v1/system/ready` - Checks the availability of:
  - Database connection
  - Redis cache availability
  - Background ML Recommendation Scheduler status
- **Diagnostics check**: `GET /api/v1/system/health` - Performs deep status checks and lists components health.
- **Prometheus metrics**: `GET /api/v1/system/metrics` - Emits CPU usage, RAM utilization, active database connection counts, and request-rate stats.
- **Version info**: `GET /api/v1/system/version` - Returns current commit metadata.

## 2. Request Correlation Tracing (`X-Request-ID`)
Every request receives or generates a unique correlation ID:
- Returned in the HTTP header `X-Request-ID`.
- Propagated to all structured structured logs (`structlog`), DB Audit entries, and error reports for easy request tracing.

## 3. Slow Query Alerting
SQLAlchemy engine executes execution hooks:
- Any database transaction taking **longer than 500 milliseconds** triggers a warning alert log detailing the execution duration, target SQL statement, current endpoint, user, and `X-Request-ID`.

## 4. Audit Log System
Critical security and transaction events (login/logout failures, checkouts, addresses, password updates) are saved in the `AuditLog` database table for historical auditing.
