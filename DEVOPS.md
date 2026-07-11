# JourneyIQ — DevOps Operations Guide

> **Version:** 1.0.0 | **Last Updated:** 2026-07-11

This guide covers Docker operations, NGINX configuration, CI/CD pipelines, structured logging, and production monitoring for JourneyIQ.

---

## Table of Contents

- [Docker Operations](#docker-operations)
  - [Essential Commands](#essential-commands)
  - [Development vs Production Compose](#development-vs-production-compose)
  - [Container Management](#container-management)
- [NGINX Configuration](#nginx-configuration)
  - [Reverse Proxy](#reverse-proxy)
  - [SSL/TLS Certificate Setup](#ssltls-certificate-setup)
  - [Security Headers](#security-headers)
- [GitHub Actions CI/CD](#github-actions-cicd)
  - [Pipeline Overview](#pipeline-overview)
  - [Backend Checks](#backend-checks)
  - [Frontend Checks](#frontend-checks)
  - [Security Scanning](#security-scanning)
- [Logging Architecture](#logging-architecture)
  - [structlog Configuration](#structlog-configuration)
  - [Log Output Format](#log-output-format)
  - [Log File Management](#log-file-management)
- [Monitoring Endpoints](#monitoring-endpoints)

---

## Docker Operations

### Essential Commands

```bash
# ──────────────────────────────────────────
# Build
# ──────────────────────────────────────────

# Build all services
docker compose -f docker-compose.prod.yml build

# Build a specific service
docker compose -f docker-compose.prod.yml build backend

# Build with no cache (clean rebuild)
docker compose -f docker-compose.prod.yml build --no-cache

# ──────────────────────────────────────────
# Run
# ──────────────────────────────────────────

# Start all services (detached)
docker compose -f docker-compose.prod.yml up -d

# Start with build
docker compose -f docker-compose.prod.yml up --build -d

# Start a specific service
docker compose -f docker-compose.prod.yml up -d backend

# ──────────────────────────────────────────
# Stop
# ──────────────────────────────────────────

# Stop all services (preserve volumes)
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes (DESTROYS DATA)
docker compose -f docker-compose.prod.yml down -v

# Stop a specific service
docker compose -f docker-compose.prod.yml stop backend

# ──────────────────────────────────────────
# Logs
# ──────────────────────────────────────────

# Follow all logs
docker compose -f docker-compose.prod.yml logs -f

# Follow backend logs only
docker compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker logs journeyiq_backend_prod --tail 100

# Logs with timestamps
docker logs journeyiq_backend_prod --tail 50 -t

# ──────────────────────────────────────────
# Exec (Interactive Shell)
# ──────────────────────────────────────────

# Shell into backend container
docker exec -it journeyiq_backend_prod /bin/bash

# Run a one-off command
docker exec journeyiq_backend_prod python -c "from app.core.config import settings; print(settings.ENVIRONMENT)"

# Run Alembic migrations inside container
docker exec journeyiq_backend_prod alembic upgrade head

# Connect to PostgreSQL
docker exec -it journeyiq_db_prod psql -U postgres -d postgres

# Redis CLI
docker exec -it journeyiq_redis_prod redis-cli

# ──────────────────────────────────────────
# Inspect
# ──────────────────────────────────────────

# List running containers
docker compose -f docker-compose.prod.yml ps

# Container resource usage
docker stats --no-stream

# Inspect a container
docker inspect journeyiq_backend_prod

# View container health status
docker inspect --format='{{.State.Health.Status}}' journeyiq_backend_prod
```

---

### Development vs Production Compose

JourneyIQ ships two Docker Compose configurations optimized for different environments:

| Aspect | `docker-compose.dev.yml` | `docker-compose.prod.yml` |
|---|---|---|
| **Purpose** | Local development | Production deployment |
| **Volumes** | Source code mounted (`./backend:/app`) for hot-reload | No source mounts; code baked into image |
| **Ports** | All services exposed (`8000`, `5173`, `5432`, `8001`) | Only frontend exposed (`80`, `443`); backend internal |
| **Environment** | `ENVIRONMENT=development` | `ENVIRONMENT=production` |
| **Redis** | Not included | Included with health checks |
| **Restart Policy** | `always` | `always` |
| **Health Checks** | Basic | Full with `service_healthy` dependency conditions |
| **Frontend** | Vite dev server on `:5173` | NGINX serving static `dist/` on `:80`/`:443` |
| **Networking** | `journeyiq_net_dev` | `journeyiq_net_prod` |
| **Secrets** | Hardcoded dev values | Env var references (`${SECRET_KEY}`) |

#### Usage

```bash
# Development (with hot-reload)
docker compose -f docker-compose.dev.yml up --build

# Production
docker compose -f docker-compose.prod.yml up --build -d
```

> [!WARNING]
> Never use `docker-compose.dev.yml` in production. It exposes database ports, uses insecure default secrets, and mounts local source code.

---

### Container Management

#### Restarting a Single Service

```bash
# Restart backend without rebuilding
docker compose -f docker-compose.prod.yml restart backend

# Rebuild and restart backend only
docker compose -f docker-compose.prod.yml up --build -d backend
```

#### Scaling (Compose)

```bash
# Scale backend to 3 replicas (remove container_name first)
docker compose -f docker-compose.prod.yml up -d --scale backend=3
```

#### Pruning

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Full system cleanup
docker system prune -a --volumes
```

---

## NGINX Configuration

The NGINX configuration lives at `nginx/nginx.conf` and serves two primary roles:

1. **Static file server** for the React SPA (`/usr/share/nginx/html`)
2. **Reverse proxy** for backend API traffic (`/api/v1/`)

### Reverse Proxy

All requests matching `/api/v1/*` are proxied to the backend container:

```nginx
location /api/v1/ {
    proxy_pass http://backend:8000/api/v1/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Request-ID $http_x_request_id;

    # Timeouts matching production hardening limits
    proxy_read_timeout 30s;
    proxy_connect_timeout 30s;
    proxy_send_timeout 30s;
}
```

Key features:
- **WebSocket support** via `Upgrade`/`Connection` headers
- **Request tracing** via `X-Request-ID` pass-through
- **30-second timeouts** for production hardening
- **Client IP forwarding** via `X-Real-IP` and `X-Forwarded-For`

### SPA Client-Side Routing

React Router requires a fallback to `index.html` for client-side routes:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### Health Check Endpoint

A lightweight `/healthz` probe for load balancer and orchestrator checks:

```nginx
location /healthz {
    access_log off;
    return 200 '{"status":"healthy"}';
    add_header Content-Type application/json;
}
```

### SSL/TLS Certificate Setup

#### Option 1 — Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone -d api.journeyiq.com -d www.journeyiq.com

# Certificates will be at:
# /etc/letsencrypt/live/api.journeyiq.com/fullchain.pem
# /etc/letsencrypt/live/api.journeyiq.com/privkey.pem
```

#### Option 2 — Mount into Docker

Add an NGINX SSL server block and mount certificates:

```yaml
# docker-compose.prod.yml override
frontend:
  volumes:
    - /etc/letsencrypt/live/api.journeyiq.com/fullchain.pem:/etc/nginx/ssl/fullchain.pem:ro
    - /etc/letsencrypt/live/api.journeyiq.com/privkey.pem:/etc/nginx/ssl/privkey.pem:ro
```

Add to `nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name api.journeyiq.com;

    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # ... same location blocks as port 80 server ...
}

server {
    listen 80;
    server_name api.journeyiq.com;
    return 301 https://$host$request_uri;
}
```

#### Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Add cron for automatic renewal
echo "0 3 * * * certbot renew --quiet && docker restart journeyiq_frontend_prod" | sudo crontab -
```

### Security Headers

The following headers are set on all responses from NGINX:

| Header | Value | Purpose |
|---|---|---|
| `X-Frame-Options` | `DENY` | Prevents clickjacking by disabling iframe embedding |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-type sniffing attacks |
| `X-XSS-Protection` | `1; mode=block` | Enables browser XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controls referrer information leakage |
| `Content-Security-Policy` | See below | Restricts resource loading origins |

**CSP Policy:**
```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval';
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
font-src 'self' https://fonts.gstatic.com;
img-src 'self' data: blob:;
connect-src 'self' https://*.supabase.co wss://*.supabase.co
            http://localhost:8000 https://api.journeyiq.com;
```

### Gzip Compression

NGINX compresses responses at level 6 for these content types:
- `application/json`, `application/javascript`
- `text/css`, `text/plain`, `text/html`
- `image/svg+xml`, `font/opentype`
- And 15+ additional MIME types

### Static Asset Caching

```nginx
location ~* \.(?:css|js|woff2?|svg|gif|jpe?g|png|ico|json)$ {
    expires 1y;
    add_header Cache-Control "public, max-age=31536000, immutable";
    access_log off;
}
```

---

## GitHub Actions CI/CD

### Pipeline Overview

The CI pipeline is defined in `.github/workflows/ci.yml` and runs on every push or pull request targeting `main`/`master`.

```
┌─────────────────────────────────────────────────────┐
│                   CI Pipeline                       │
├──────────────────────┬──────────────────────────────┤
│   backend-checks     │     frontend-checks          │
│   (runs in parallel) │     (runs in parallel)       │
├──────────────────────┼──────────────────────────────┤
│ 1. Checkout code     │ 1. Checkout code             │
│ 2. Setup Python 3.13 │ 2. Setup Node.js 20          │
│ 3. Install deps      │ 3. npm ci                    │
│ 4. Ruff linter       │ 4. ESLint check              │
│ 5. Black formatter   │ 5. Prettier formatter check  │
│ 6. Isort imports     │ 6. Build frontend            │
│ 7. Mypy type checker │                              │
│ 8. pip-audit (CVEs)  │                              │
│ 9. Pytest + coverage │                              │
└──────────────────────┴──────────────────────────────┘
```

### Backend Checks

| Step | Tool | Purpose |
|---|---|---|
| **Lint** | `ruff check backend` | Fast Python linter (replaces flake8/pylint) |
| **Format** | `black --check backend` | Code style enforcement (PEP 8 compliant) |
| **Imports** | `isort --check-only backend` | Import ordering validation |
| **Types** | `mypy backend` | Static type checking |
| **Vulnerability Scan** | `pip-audit -r backend/requirements.txt` | CVE detection in dependencies |
| **Tests** | `pytest --cov=app --cov-report=xml` | Unit/integration tests with coverage report |

### Frontend Checks

| Step | Tool | Purpose |
|---|---|---|
| **Lint** | `npm run lint` | ESLint static analysis |
| **Format** | `npm run format:check` | Prettier code formatting validation |
| **Build** | `npm run build` | Verify production build succeeds |

### Security Scanning

> [!TIP]
> Enable these additional GitHub features for comprehensive security:
> - **Dependabot** — Automated dependency update PRs (`Settings → Security → Dependabot`)
> - **CodeQL** — Static analysis for security vulnerabilities (`Security → Code scanning`)
> - **Secret Scanning** — Detect accidentally committed credentials

#### Adding CodeQL (Recommended)

Create `.github/workflows/codeql.yml`:

```yaml
name: CodeQL Analysis
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 6 AM UTC

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    strategy:
      matrix:
        language: ['python', 'javascript']
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3
```

---

## Logging Architecture

### structlog Configuration

JourneyIQ uses [structlog](https://www.structlog.org/) for structured, contextual logging configured in `backend/app/core/logging_config.py`.

```
┌────────────────────┐
│   Application Code │
│   structlog.get_   │
│   logger()         │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Shared Processors │
│  • contextvars     │
│  • add_log_level   │
│  • add_logger_name │
│  • TimeStamper     │ (ISO 8601)
│  • StackInfo       │
│  • exc_info        │
│  • UnicodeDecoder  │
└────────┬───────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────────┐
│ stdout │ │ File       │
│ Handler│ │ Handler    │
│        │ │            │
│ Dev:   │ │ logs/      │
│ Color  │ │ app.log    │
│ Console│ │ (JSON)     │
│        │ │            │
│ Prod:  │ │ Always     │
│ JSON   │ │ JSON       │
└────────┘ └────────────┘
```

### Log Output Format

#### Development (Console)

```
2026-07-11T09:14:30Z [info     ] Request started    endpoint=/api/v1/health method=GET request_id=abc-123
```

#### Production (JSON)

```json
{
  "event": "Request started",
  "level": "info",
  "logger": "journeyiq",
  "timestamp": "2026-07-11T09:14:30.123456Z",
  "request_id": "abc-123",
  "endpoint": "/api/v1/health",
  "method": "GET"
}
```

### Request Context Injection

Every HTTP request automatically gets:
- **`request_id`** — Unique UUID (from `X-Request-ID` header or auto-generated)
- **`endpoint`** — Request URL path
- **`method`** — HTTP method
- **`duration_ms`** — Total processing time (logged on completion)
- **`status_code`** — Response status (logged on completion)

### Log File Management

| File | Path | Format | Contents |
|---|---|---|---|
| Application log | `logs/app.log` | JSON (one object per line) | All application events |
| NGINX access log | `/var/log/nginx/access.log` | Combined format | HTTP request access records |
| NGINX error log | `/var/log/nginx/error.log` | Standard | NGINX errors and warnings |

#### Log Rotation (Recommended)

```bash
# /etc/logrotate.d/journeyiq
/path/to/JourneyIQ/backend/logs/app.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    copytruncate
}
```

### Prometheus Metrics Endpoint

The `/api/v1/system/prometheus` endpoint exposes metrics in Prometheus text format:

```
# HELP journeyiq_system_cpu_usage_ratio CPU usage ratio
# TYPE journeyiq_system_cpu_usage_ratio gauge
journeyiq_system_cpu_usage_ratio 0.0523

# HELP journeyiq_system_memory_usage_bytes Process memory usage in bytes
# TYPE journeyiq_system_memory_usage_bytes gauge
journeyiq_system_memory_usage_bytes 157286400.0

# HELP journeyiq_db_ping_ms Database ping latency in milliseconds
# TYPE journeyiq_db_ping_ms gauge
journeyiq_db_ping_ms 2.45

# HELP journeyiq_ml_inferences_total Total Deep Learning inference requests
# TYPE journeyiq_ml_inferences_total counter
journeyiq_ml_inferences_total 1247

# HELP journeyiq_ml_inference_latency_avg_ms Average NCF inference latency in ms
# TYPE journeyiq_ml_inference_latency_avg_ms gauge
journeyiq_ml_inference_latency_avg_ms 12.3400

# HELP journeyiq_log_errors_total Total error logs recorded
# TYPE journeyiq_log_errors_total counter
journeyiq_log_errors_total 3
```

#### Prometheus Scrape Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'journeyiq'
    scrape_interval: 30s
    metrics_path: '/api/v1/system/prometheus'
    static_configs:
      - targets: ['backend:8000']
        labels:
          app: 'journeyiq'
          environment: 'production'
```

---

## Monitoring Endpoints

All monitoring endpoints are under the `/api/v1/system/` prefix and the `/api/v1/` prefix.

| Endpoint | Method | Purpose | Auth Required |
|---|---|---|---|
| `/api/v1/health` | `GET` | Basic health check with DB connectivity and uptime | No |
| `/api/v1/system/health` | `GET` | Aggregated health: DB, cache, scheduler, ML engine | No |
| `/api/v1/system/live` | `GET` | Kubernetes liveness probe (instant `{"status": "alive"}`) | No |
| `/api/v1/system/ready` | `GET` | Kubernetes readiness probe (checks DB + cache + scheduler) | No |
| `/api/v1/system/metrics` | `GET` | CPU, memory, DB ping latency, Python version | No |
| `/api/v1/system/deployment` | `GET` | Masked deployment configuration (env, URLs, JWT settings) | No |
| `/api/v1/system/runtime` | `GET` | Platform, CPU count, threads, PID, uptime, memory | No |
| `/api/v1/system/models` | `GET` | NCF model registry: active model, checkpoints, inference stats | No |
| `/api/v1/system/cache` | `GET` | Cache type (Redis/memory), hit/miss stats, connection status | No |
| `/api/v1/system/database` | `GET` | Connection pool size, checked in/out, overflow, DB size, table count | No |
| `/api/v1/system/logs` | `GET` | Log file size, line count, error/warning counts, error ratio | No |
| `/api/v1/system/prometheus` | `GET` | All metrics in Prometheus text exposition format | No |
| `/api/v1/system/version` | `GET` | Project name, version, environment | No |

> [!WARNING]
> In production, consider adding authentication or IP-allowlisting to the `/system/*` endpoints to prevent information disclosure. These endpoints expose internal infrastructure details.

### Quick Health Check Script

```bash
#!/bin/bash
BASE_URL="${1:-http://localhost:8000}"

echo "=== JourneyIQ Health Check ==="
endpoints=(
  "/api/v1/health"
  "/api/v1/system/health"
  "/api/v1/system/live"
  "/api/v1/system/ready"
  "/api/v1/system/metrics"
  "/api/v1/system/models"
  "/api/v1/system/cache"
  "/api/v1/system/database"
  "/api/v1/system/logs"
  "/api/v1/system/version"
)

for ep in "${endpoints[@]}"; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}${ep}")
  if [ "$status" -eq 200 ]; then
    echo "✅ ${ep} → ${status}"
  else
    echo "❌ ${ep} → ${status}"
  fi
done
```

---

*For ML model operations, see [MLOPS.md](MLOPS.md). For production setup, see [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md).*
