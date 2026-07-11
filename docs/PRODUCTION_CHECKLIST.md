# JourneyIQ — Production Deployment Checklist

> **Version:** 1.0.0 | **Last Updated:** 2026-07-11

Use this checklist for every production deployment. Complete each section in order and obtain sign-off before proceeding to the next.

---

## Deployment Information

| Field | Value |
|---|---|
| **Deployment Date** | __________________ |
| **Deployed By** | __________________ |
| **Release Version** | __________________ |
| **Git Commit SHA** | __________________ |
| **Environment** | ☐ Staging ☐ Production |
| **Deployment Method** | ☐ Docker Compose ☐ Kubernetes ☐ PaaS (Render/Railway) |

---

## 1. Pre-Deployment Checks

> [!IMPORTANT]
> All pre-deployment checks must pass before initiating the deployment process.

### Environment & Configuration

- [ ] All required environment variables are set in `.env.production`:
  - [ ] `DATABASE_URL` — PostgreSQL connection with `asyncpg` driver
  - [ ] `SECRET_KEY` — Unique, cryptographically random (≥ 64 chars)
  - [ ] `JWT_SECRET` — Unique, cryptographically random (≥ 64 chars)
  - [ ] `ENVIRONMENT` — Set to `production`
  - [ ] `FRONTEND_URL` — Production frontend URL (for CORS)
  - [ ] `BACKEND_URL` — Production backend URL
  - [ ] `REDIS_URL` — Redis connection string (if using Redis)
  - [ ] `POSTGRES_USER` — Database user
  - [ ] `POSTGRES_PASSWORD` — Strong, unique password
  - [ ] `POSTGRES_DB` — Database name
- [ ] No default/example secrets present in production config
- [ ] `.env.production` is **NOT** committed to version control
- [ ] `VITE_BACKEND_URL` set for frontend build

### Secrets Rotation

- [ ] `SECRET_KEY` rotated since last deployment (if scheduled)
- [ ] `JWT_SECRET` rotated since last deployment (if scheduled)
- [ ] Database password rotated (if scheduled)
- [ ] Previous JWT tokens will be invalidated (inform users if JWT_SECRET changed)

### Database

- [ ] Database backup taken before deployment
  ```bash
  docker exec journeyiq_db_prod pg_dump -U postgres -d postgres | gzip > backup_pre_deploy.sql.gz
  ```
- [ ] Backup checksum verified
- [ ] All Alembic migrations are committed and tested
- [ ] `alembic upgrade head` tested in staging environment
- [ ] No pending migration conflicts

### Code

- [ ] All CI pipeline checks passing (green ✅ on GitHub)
- [ ] Code review completed and approved
- [ ] No critical or high-severity Dependabot alerts
- [ ] Feature branch merged to `main`
- [ ] Git tag created for release: `git tag -a v{version} -m "Release v{version}"`

---

## 2. Build Verification

### Backend Build

- [ ] Backend Docker image builds successfully:
  ```bash
  docker compose -f docker-compose.prod.yml build backend
  ```
- [ ] No build warnings or errors in output
- [ ] Python dependencies install without conflicts
- [ ] PyTorch loads successfully in container:
  ```bash
  docker run --rm journeyiq-backend python -c "import torch; print(torch.__version__)"
  ```

### Frontend Build

- [ ] Frontend builds successfully:
  ```bash
  cd frontend && npm ci && npm run build
  ```
- [ ] `dist/` directory created with `index.html` and `assets/`
- [ ] No TypeScript compilation errors
- [ ] No ESLint critical errors
- [ ] `VITE_BACKEND_URL` correctly embedded in built bundle:
  ```bash
  grep -r "VITE_BACKEND_URL\|api.journeyiq" frontend/dist/assets/*.js | head -3
  ```

### Docker Images

- [ ] All Docker images build successfully:
  ```bash
  docker compose -f docker-compose.prod.yml build
  ```
- [ ] Image sizes are reasonable (no bloat):
  ```bash
  docker images | grep journeyiq
  ```
- [ ] No deprecated base images (check for security advisories)

### Lint & Quality

- [ ] `ruff check backend` — No errors
- [ ] `black --check backend` — Formatting correct
- [ ] `isort --check-only backend` — Imports sorted
- [ ] `mypy backend` — Type checks pass
- [ ] `pip-audit -r backend/requirements.txt` — No known CVEs
- [ ] `npm run lint` (frontend) — No critical ESLint errors
- [ ] `npm run format:check` (frontend) — Prettier formatting correct

---

## 3. Deployment Verification

### Container Status

- [ ] All containers are running:
  ```bash
  docker compose -f docker-compose.prod.yml ps
  ```
- [ ] Expected containers present:
  - [ ] `journeyiq_db_prod` — Status: `Up (healthy)`
  - [ ] `journeyiq_redis_prod` — Status: `Up (healthy)`
  - [ ] `journeyiq_backend_prod` — Status: `Up (healthy)`
  - [ ] `journeyiq_ml_service_prod` — Status: `Up (healthy)`
  - [ ] `journeyiq_frontend_prod` — Status: `Up`
- [ ] No containers in restart loop (`docker ps` shows stable uptime)

### Health Endpoints

- [ ] Basic health check returns `200`:
  ```bash
  curl -s http://localhost/api/v1/health | jq '.status'
  # Expected: "healthy"
  ```
- [ ] System health check returns `200`:
  ```bash
  curl -s http://localhost/api/v1/system/health | jq '.data.status'
  # Expected: "healthy"
  ```
- [ ] Liveness probe returns `200`:
  ```bash
  curl -s http://localhost/api/v1/system/live | jq '.status'
  # Expected: "alive"
  ```
- [ ] Readiness probe returns `200` (not `503`):
  ```bash
  curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v1/system/ready
  # Expected: 200
  ```

### Database Connectivity

- [ ] Database shows `connected`:
  ```bash
  curl -s http://localhost/api/v1/system/health | jq '.data.database'
  # Expected: "connected"
  ```
- [ ] Database ping latency < 50ms:
  ```bash
  curl -s http://localhost/api/v1/system/metrics | jq '.data.database_ping_ms'
  ```
- [ ] Alembic migrations current:
  ```bash
  docker exec journeyiq_backend_prod alembic current
  ```
- [ ] Database pool metrics healthy:
  ```bash
  curl -s http://localhost/api/v1/system/database | jq '.data'
  ```

### Cache Operation

- [ ] Cache shows `connected`:
  ```bash
  curl -s http://localhost/api/v1/system/cache | jq '.data'
  ```
- [ ] Redis is responding (if configured):
  ```bash
  docker exec journeyiq_redis_prod redis-cli ping
  # Expected: PONG
  ```

### Scheduler Status

- [ ] Scheduler shows `healthy`:
  ```bash
  curl -s http://localhost/api/v1/system/health | jq '.data.scheduler'
  # Expected: "healthy"
  ```
- [ ] Scheduler task is running (check backend logs):
  ```bash
  docker logs journeyiq_backend_prod 2>&1 | grep -i "scheduler" | tail -5
  ```

---

## 4. Security Verification

### HTTPS/TLS

- [ ] HTTPS is enabled and working:
  ```bash
  curl -vI https://api.journeyiq.com 2>&1 | grep "SSL connection"
  ```
- [ ] HTTP redirects to HTTPS:
  ```bash
  curl -s -o /dev/null -w "%{http_code}" http://api.journeyiq.com
  # Expected: 301 or 302
  ```
- [ ] SSL certificate is valid and not expiring within 30 days:
  ```bash
  echo | openssl s_client -connect api.journeyiq.com:443 2>/dev/null | openssl x509 -noout -dates
  ```
- [ ] SSL Labs grade A or higher: `https://www.ssllabs.com/ssltest/`

### CORS Configuration

- [ ] CORS allows the production frontend URL:
  ```bash
  curl -s http://localhost/api/v1/system/deployment | jq '.data.frontend_url'
  ```
- [ ] Preflight OPTIONS requests succeed:
  ```bash
  curl -s -X OPTIONS -H "Origin: https://www.journeyiq.com" \
    -H "Access-Control-Request-Method: GET" \
    http://localhost/api/v1/health -I | grep -i "access-control"
  ```

### JWT & Authentication

- [ ] JWT secrets are production-grade (not default values):
  ```bash
  curl -s http://localhost/api/v1/system/deployment | jq '.data | {jwt_secret_masked, secret_key_masked}'
  # Expected: "********" (not "not-configured")
  ```
- [ ] Token expiration configured:
  ```bash
  curl -s http://localhost/api/v1/system/deployment | jq '.data.access_token_expire_minutes'
  # Expected: 15 (or configured value)
  ```

### Security Headers

- [ ] All security headers present in NGINX responses:
  ```bash
  curl -sI http://localhost/ | grep -iE "x-frame|x-content|x-xss|referrer|content-security"
  ```
  - [ ] `X-Frame-Options: DENY`
  - [ ] `X-Content-Type-Options: nosniff`
  - [ ] `X-XSS-Protection: 1; mode=block`
  - [ ] `Referrer-Policy: strict-origin-when-cross-origin`
  - [ ] `Content-Security-Policy` — present and configured

### Content Security Policy

- [ ] CSP header is active and not blocking legitimate resources:
  ```bash
  curl -sI http://localhost/ | grep -i "content-security-policy"
  ```
- [ ] CSP allows required origins:
  - [ ] `'self'` for default-src
  - [ ] Supabase domains for connect-src
  - [ ] Google Fonts for style-src/font-src
  - [ ] Backend URL for connect-src

---

## 5. Monitoring Verification

### Prometheus Endpoint

- [ ] Prometheus endpoint is scraping:
  ```bash
  curl -s http://localhost/api/v1/system/prometheus | head -20
  ```
- [ ] All expected metrics present:
  - [ ] `journeyiq_system_cpu_usage_ratio`
  - [ ] `journeyiq_system_memory_usage_bytes`
  - [ ] `journeyiq_db_ping_ms`
  - [ ] `journeyiq_cache_hits_total`
  - [ ] `journeyiq_ml_inferences_total`
  - [ ] `journeyiq_log_errors_total`

### Log Files

- [ ] Application log file is being written:
  ```bash
  docker exec journeyiq_backend_prod ls -la /app/logs/app.log
  ```
- [ ] Logs are in JSON format (production mode):
  ```bash
  docker exec journeyiq_backend_prod tail -1 /app/logs/app.log | jq '.'
  ```
- [ ] NGINX access log is being written:
  ```bash
  docker exec journeyiq_frontend_prod ls -la /var/log/nginx/access.log
  ```

### Error Rates

- [ ] Error rate is normal (< 1%):
  ```bash
  curl -s http://localhost/api/v1/system/logs | jq '.data.error_ratio_pct'
  ```
- [ ] No unexpected errors in recent logs:
  ```bash
  docker logs journeyiq_backend_prod --tail 100 2>&1 | grep -i error | head -10
  ```

---

## 6. ML Verification

### Model Status

- [ ] ML model is loaded and active:
  ```bash
  curl -s http://localhost/api/v1/system/models | jq '.data.active_model.active_version'
  # Expected: "v{timestamp}" (not "v0.0")
  ```
- [ ] Model framework shows `pytorch`:
  ```bash
  curl -s http://localhost/api/v1/system/models | jq '.data.active_model.framework'
  ```

### Inference

- [ ] Inference endpoint is responding (no errors in logs):
  ```bash
  docker logs journeyiq_backend_prod 2>&1 | grep -i "inference\|NCFPredictor" | tail -5
  ```
- [ ] Inference statistics are being tracked:
  ```bash
  curl -s http://localhost/api/v1/system/models | jq '.data.inference_statistics'
  ```

### Evaluation Metrics

- [ ] Evaluation metrics file exists:
  ```bash
  docker exec journeyiq_backend_prod cat /app/models/evaluation_metrics.json | jq '.'
  ```
- [ ] Metrics are within acceptable ranges:
  - [ ] `precision_at_10` > 0.10
  - [ ] `recall_at_10` > 0.05
  - [ ] `hit_rate` > 0.30
  - [ ] `ndcg` > 0.15
  - [ ] `coverage` > 0.20

### Model Registry

- [ ] Checkpoints are listed:
  ```bash
  curl -s http://localhost/api/v1/system/models | jq '.data.checkpoints_registry | length'
  # Expected: ≥ 1
  ```

---

## 7. Backup Verification

### Backup Scripts

- [ ] Backup script runs without errors:
  ```bash
  python scripts/backup.py --type database --output backups/db/ --dry-run
  ```
- [ ] Database backup creates valid archive:
  ```bash
  docker exec journeyiq_db_prod pg_dump -U postgres -d postgres | gzip > /tmp/test_backup.sql.gz
  ls -la /tmp/test_backup.sql.gz  # Should be > 0 bytes
  ```

### Checksum Validation

- [ ] SHA-256 checksums generate and validate:
  ```bash
  sha256sum backups/db/latest_backup.sql.gz > /tmp/test.sha256
  sha256sum -c /tmp/test.sha256
  # Expected: OK
  ```

### Restore Test

- [ ] Restore has been tested in staging (within last 30 days):
  - [ ] Database restore completed successfully
  - [ ] Model restore completed successfully
  - [ ] All endpoints responding after restore
- [ ] Restore documentation is current and accessible

---

## 8. Performance Verification

### API Response Times

- [ ] API response times within SLA:
  ```bash
  # Health endpoint < 500ms
  curl -s -o /dev/null -w "Time: %{time_total}s\n" http://localhost/api/v1/health
  ```
  - [ ] `/api/v1/health` — < 500ms
  - [ ] `/api/v1/system/live` — < 100ms
  - [ ] `/api/v1/system/metrics` — < 500ms
  - [ ] Product endpoints — < 500ms
  - [ ] Recommendation endpoints — < 500ms

### Database Performance

- [ ] Database ping < 50ms:
  ```bash
  curl -s http://localhost/api/v1/system/metrics | jq '.data.database_ping_ms'
  ```
- [ ] Connection pool not exhausted:
  ```bash
  curl -s http://localhost/api/v1/system/database | jq '.data | {pool_size, connections_checked_out}'
  ```

### Resource Usage

- [ ] Memory usage is stable:
  ```bash
  curl -s http://localhost/api/v1/system/metrics | jq '.data.memory_usage_mb'
  # Expected: < 512 MB under normal load
  ```
- [ ] CPU usage is normal:
  ```bash
  curl -s http://localhost/api/v1/system/metrics | jq '.data.cpu_usage_pct'
  # Expected: < 30% under normal load
  ```
- [ ] No container OOM kills:
  ```bash
  docker inspect journeyiq_backend_prod | jq '.[0].State.OOMKilled'
  # Expected: false
  ```

---

## 9. Rollback Plan

> [!WARNING]
> Document the rollback procedure **before** deploying. If the deployment fails, execute the rollback immediately.

### Rollback Triggers

A rollback should be initiated if any of these occur after deployment:

- [ ] Health endpoint returns `503` for > 5 minutes
- [ ] Error rate exceeds 10% for > 10 minutes
- [ ] Database connection failures persist after container restart
- [ ] Critical user-facing functionality is broken
- [ ] Security vulnerability discovered in the release

### Rollback Steps

**For Docker Compose:**

```bash
# 1. Stop current deployment
docker compose -f docker-compose.prod.yml down

# 2. Checkout previous release
git checkout v{previous_version}

# 3. Rebuild and deploy
docker compose -f docker-compose.prod.yml up --build -d

# 4. Restore database if migrations were run
gunzip -c backup_pre_deploy.sql.gz | \
  docker exec -i journeyiq_db_prod psql -U postgres -d postgres

# 5. Verify rollback
curl -s http://localhost/api/v1/health | jq '.'
curl -s http://localhost/api/v1/system/version | jq '.data.version'
```

**For Kubernetes:**

```bash
# 1. Rollback deployment
kubectl rollout undo -n journeyiq deployment/journeyiq-backend

# 2. Verify rollback
kubectl rollout status -n journeyiq deployment/journeyiq-backend

# 3. Restore database if needed
# (Follow database restore procedure in BACKUP.md)
```

**For ML Model:**

```bash
# Rollback to previous model version
curl -X POST http://localhost:8000/api/v1/system/models/rollback/{previous_version_id}

# Restart backend to reload model
docker restart journeyiq_backend_prod
```

### Rollback Verification

- [ ] Previous version is running (`/api/v1/system/version`)
- [ ] Health check passes
- [ ] Database connectivity restored
- [ ] User authentication working
- [ ] Core features operational

---

## 10. Sign-Off

### Deployment Approved By

| Role | Name | Signature | Date |
|---|---|---|---|
| **Deployer** | __________________ | __________________ | __________________ |
| **Reviewer** | __________________ | __________________ | __________________ |
| **QA Lead** | __________________ | __________________ | __________________ |
| **Tech Lead** | __________________ | __________________ | __________________ |

### Post-Deployment Notes

```
_____________________________________________________________________________

_____________________________________________________________________________

_____________________________________________________________________________

_____________________________________________________________________________
```

### Deployment Result

- [ ] ✅ **SUCCESS** — All checks passed, deployment is live
- [ ] ⚠️ **PARTIAL** — Deployed with known issues (documented above)
- [ ] ❌ **ROLLED BACK** — Deployment failed, reverted to previous version

---

*For detailed deployment guides, see [DEPLOYMENT.md](DEPLOYMENT.md). For production monitoring, see [RUNBOOK.md](RUNBOOK.md). For backup procedures, see [BACKUP.md](BACKUP.md).*
