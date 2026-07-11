# JourneyIQ — Production Setup Guide

> **Version:** 1.0.0 | **Last Updated:** 2026-07-11

This guide walks through setting up JourneyIQ for production deployment from a fresh server to a fully operational system.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Step 1 — Clone Repository](#step-1--clone-repository)
- [Step 2 — Backend Setup](#step-2--backend-setup)
- [Step 3 — Frontend Setup](#step-3--frontend-setup)
- [Step 4 — Environment Configuration](#step-4--environment-configuration)
- [Step 5 — Docker Deployment](#step-5--docker-deployment)
- [Step 6 — Kubernetes Deployment](#step-6--kubernetes-deployment)
- [Step 7 — SSL/TLS Certificate Setup](#step-7--ssltls-certificate-setup)
- [Step 8 — DNS Configuration](#step-8--dns-configuration)
- [Step 9 — Post-Deployment Verification](#step-9--post-deployment-verification)

---

## Prerequisites

### Required Software

| Software | Minimum Version | Purpose | Install Guide |
|---|---|---|---|
| **Python** | 3.13+ | Backend runtime, ML training | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 20 LTS | Frontend build toolchain | [nodejs.org](https://nodejs.org/) |
| **Docker** | 24+ | Container runtime | [docker.com](https://docs.docker.com/get-docker/) |
| **Docker Compose** | v2.20+ | Multi-container orchestration | Bundled with Docker Desktop |
| **PostgreSQL** | 16+ | Primary database | [postgresql.org](https://www.postgresql.org/download/) (or use Docker) |
| **Git** | 2.40+ | Version control | [git-scm.com](https://git-scm.com/) |

### Optional Software

| Software | Version | Purpose |
|---|---|---|
| **Redis** | 7+ | Production caching layer |
| **kubectl** | 1.28+ | Kubernetes deployment |
| **Certbot** | 2+ | SSL certificate management |
| **NGINX** | 1.25+ | Reverse proxy (included in Docker) |

### System Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| **CPU** | 2 vCPUs | 4 vCPUs |
| **RAM** | 4 GB | 8 GB |
| **Storage** | 20 GB SSD | 50 GB SSD |
| **OS** | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| **Network** | Ports 80, 443 open | Ports 80, 443, 22 open |

### Verify Prerequisites

```bash
# Check all versions
python --version          # ≥ 3.13
node --version            # ≥ 20.x
npm --version             # ≥ 10.x
docker --version          # ≥ 24.x
docker compose version    # ≥ 2.20
git --version             # ≥ 2.40
```

> [!IMPORTANT]
> Python 3.13 is required because the codebase uses modern type hints (`list[int]`, `dict[str, Any]`, `type | None`) that are only available in Python 3.10+, and specific 3.13 features.

---

## Step 1 — Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-org/JourneyIQ.git
cd JourneyIQ

# Verify project structure
ls -la
# Expected: backend/ frontend/ nginx/ k8s/ ml-service/ docker-compose.*.yml
```

### Directory Structure Overview

```
JourneyIQ/
├── backend/                    # FastAPI + PyTorch backend
│   ├── app/                    # Application source code
│   │   ├── api/endpoints/      # Route handlers
│   │   ├── core/               # Config, security, logging, cache
│   │   ├── db/                 # Database session, base classes
│   │   ├── middleware/         # Security headers, timeout
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── services/           # Business logic, ML, deep learning
│   ├── migrations/             # Alembic database migrations
│   ├── models/                 # Trained PyTorch model checkpoints
│   ├── tests/                  # Pytest test suite
│   ├── Dockerfile              # Backend container image
│   └── requirements.txt        # Python dependencies
├── frontend/                   # React + Vite + Tailwind SPA
│   ├── src/                    # React source code
│   ├── dist/                   # Built static files (after npm run build)
│   ├── Dockerfile              # Frontend container image
│   ├── package.json            # Node.js dependencies
│   └── vite.config.ts          # Vite build configuration
├── ml-service/                 # Standalone ML microservice
├── nginx/
│   └── nginx.conf              # NGINX reverse proxy config
├── k8s/                        # Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
├── .github/workflows/          # CI/CD pipeline definitions
│   └── ci.yml
├── docker-compose.yml          # Default compose
├── docker-compose.dev.yml      # Development compose
├── docker-compose.prod.yml     # Production compose
├── .env.example                # Environment variable template
└── .env                        # Local environment (not in git)
```

---

## Step 2 — Backend Setup

### Option A — Direct Python Setup (Without Docker)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; import torch; print('FastAPI:', fastapi.__version__); print('PyTorch:', torch.__version__)"
```

### Database Migrations

```bash
# Ensure DATABASE_URL is set in environment or .env
# Run all pending migrations
alembic upgrade head

# Verify migration status
alembic current

# If you need to create a new migration
alembic revision --autogenerate -m "description of changes"
```

### Seed Data (Optional)

```bash
# If a seed script exists
python -m app.db.seed

# Or manually create initial admin user
python -c "
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

async def seed():
    async with AsyncSessionLocal() as db:
        admin = User(
            email='admin@journeyiq.com',
            hashed_password=get_password_hash('ChangeMeInProduction!'),
            first_name='Admin',
            last_name='User',
            role='admin',
            is_verified=True
        )
        db.add(admin)
        await db.commit()
        print('Admin user created')

asyncio.run(seed())
"
```

### Start Backend (Development)

```bash
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Using gunicorn (production)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

---

## Step 3 — Frontend Setup

```bash
cd frontend

# Install dependencies (clean install)
npm ci

# Build for production
npm run build

# Verify build output
ls -la dist/
# Expected: index.html, assets/ directory with JS/CSS bundles
```

### Development Server (Optional)

```bash
# Start Vite dev server with hot-reload
npm run dev
# Frontend available at http://localhost:5173
```

### Verify Frontend Configuration

```bash
# Check vite.config.ts for proxy settings
cat vite.config.ts

# Ensure VITE_BACKEND_URL is set before building
echo $VITE_BACKEND_URL
# Should be: https://api.yourdomain.com (for production build)
```

---

## Step 4 — Environment Configuration

### Create Production Environment File

```bash
# Copy template
cp .env.example .env.production

# Edit with production values
nano .env.production
```

### .env.production Template

```bash
# ──────────────────────────────────────────
# JourneyIQ Production Environment
# ──────────────────────────────────────────

# Application
PORT=8000
ENVIRONMENT=production
LOG_LEVEL=info

# URLs
BACKEND_URL=https://api.journeyiq.com
FRONTEND_URL=https://www.journeyiq.com

# PostgreSQL Database
DATABASE_URL=postgresql+asyncpg://journeyiq_user:STRONG_PASSWORD_HERE@db:5432/journeyiq_prod
POSTGRES_USER=journeyiq_user
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
POSTGRES_DB=journeyiq_prod

# Security (GENERATE UNIQUE VALUES)
SECRET_KEY=GENERATE_WITH_python_-c_"import_secrets;print(secrets.token_urlsafe(64))"
JWT_SECRET=GENERATE_WITH_python_-c_"import_secrets;print(secrets.token_urlsafe(64))"

# Redis Caching
REDIS_URL=redis://redis:6379/0
```

### Generate Secrets

```bash
# Generate SECRET_KEY
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"

# Generate JWT_SECRET
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(64))"

# Generate POSTGRES_PASSWORD
python -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(32))"
```

> [!CAUTION]
> - Never use the default/example secret values in production
> - Never commit `.env.production` to version control
> - Rotate secrets quarterly (update JWT_SECRET during a maintenance window)

### Verify Environment Configuration

```bash
# Check all required variables are set
python -c "
required = ['DATABASE_URL', 'SECRET_KEY', 'JWT_SECRET', 'ENVIRONMENT', 'FRONTEND_URL', 'BACKEND_URL']
import os
from dotenv import load_dotenv
load_dotenv('.env.production')
for var in required:
    val = os.getenv(var)
    if val:
        print(f'  ✅ {var} = {val[:20]}...' if len(val) > 20 else f'  ✅ {var} = {val}')
    else:
        print(f'  ❌ {var} is NOT SET')
"
```

---

## Step 5 — Docker Deployment

### Build and Start All Services

```bash
# Ensure you're in the project root
cd JourneyIQ

# Copy production env file
cp .env.production .env

# Build and start all services
docker compose -f docker-compose.prod.yml up --build -d

# Wait for health checks to pass (30-60 seconds)
sleep 30

# Verify all containers are running
docker compose -f docker-compose.prod.yml ps
```

### Expected Container Status

```
NAME                          STATUS                    PORTS
journeyiq_db_prod             Up (healthy)              0.0.0.0:5432->5432/tcp
journeyiq_redis_prod          Up (healthy)              0.0.0.0:6379->6379/tcp
journeyiq_backend_prod        Up (healthy)              8000/tcp
journeyiq_ml_service_prod     Up (healthy)              8001/tcp
journeyiq_frontend_prod       Up                        0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### Run Database Migrations

```bash
# Run migrations inside the backend container
docker exec journeyiq_backend_prod alembic upgrade head

# Verify migration status
docker exec journeyiq_backend_prod alembic current
```

### Verify Deployment

```bash
# Basic health check
curl -s http://localhost/api/v1/health | jq '.'

# System health
curl -s http://localhost/api/v1/system/health | jq '.'

# Frontend
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost/
```

---

## Step 6 — Kubernetes Deployment

For teams using Kubernetes, manifests are provided in the `k8s/` directory.

### Prerequisites

```bash
# Verify kubectl is configured
kubectl cluster-info
kubectl get nodes
```

### Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Or apply everything at once with kustomize (if kustomization.yaml exists)
kubectl apply -k k8s/
```

### Configure Secrets

Before deploying, update `k8s/secret.yaml` with base64-encoded production values:

```bash
# Encode secrets
echo -n "your-database-url" | base64
echo -n "your-secret-key" | base64
echo -n "your-jwt-secret" | base64
```

> [!WARNING]
> Do not commit `k8s/secret.yaml` with real values to version control. Use a secrets management solution (Kubernetes External Secrets, HashiCorp Vault, AWS Secrets Manager) in production.

### Verify Kubernetes Deployment

```bash
# Check pod status
kubectl get pods -n journeyiq

# Check services
kubectl get svc -n journeyiq

# Check ingress
kubectl get ingress -n journeyiq

# View pod logs
kubectl logs -n journeyiq -l app=journeyiq-backend --tail=50

# Port-forward for local testing
kubectl port-forward -n journeyiq svc/journeyiq-backend 8000:8000
curl http://localhost:8000/api/v1/health
```

### Rolling Updates

```bash
# Update backend image
kubectl set image -n journeyiq \
  deployment/journeyiq-backend \
  backend=ghcr.io/your-org/journeyiq-backend:v1.1.0

# Watch rollout status
kubectl rollout status -n journeyiq deployment/journeyiq-backend

# Rollback if needed
kubectl rollout undo -n journeyiq deployment/journeyiq-backend
```

---

## Step 7 — SSL/TLS Certificate Setup

### Option A — Let's Encrypt (Self-Hosted)

```bash
# Install Certbot
sudo apt update && sudo apt install -y certbot

# Stop NGINX temporarily (port 80 must be free)
docker compose -f docker-compose.prod.yml stop frontend

# Obtain certificate
sudo certbot certonly --standalone \
  -d api.journeyiq.com \
  -d www.journeyiq.com \
  --agree-tos \
  --email admin@journeyiq.com

# Certificate files location:
# /etc/letsencrypt/live/api.journeyiq.com/fullchain.pem
# /etc/letsencrypt/live/api.journeyiq.com/privkey.pem

# Restart frontend with SSL
docker compose -f docker-compose.prod.yml up -d frontend
```

### Option B — Kubernetes cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@journeyiq.com
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
      - http01:
          ingress:
            class: nginx
EOF
```

Then add the annotation to your Ingress:

```yaml
metadata:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
```

### Option C — Cloud Provider SSL

| Provider | SSL Solution |
|---|---|
| AWS | ACM (AWS Certificate Manager) — free, auto-renewing |
| Azure | Azure-managed certificates on App Service |
| Render | Automatic SSL on all custom domains |
| Railway | Automatic SSL on all custom domains |
| Vercel/Netlify | Automatic SSL on all domains |

### Verify SSL

```bash
# Check certificate validity
openssl s_client -connect api.journeyiq.com:443 -servername api.journeyiq.com \
  2>/dev/null | openssl x509 -noout -dates

# Test HTTPS connectivity
curl -vI https://api.journeyiq.com/api/v1/health 2>&1 | grep -E "SSL|subject|expire"

# Check SSL grade
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=api.journeyiq.com
```

---

## Step 8 — DNS Configuration

### Required DNS Records

| Record Type | Name | Value | TTL | Purpose |
|---|---|---|---|---|
| `A` | `api.journeyiq.com` | `<server-ip>` | 300 | Backend API |
| `A` | `www.journeyiq.com` | `<server-ip>` | 300 | Frontend SPA |
| `CNAME` | `journeyiq.com` | `www.journeyiq.com` | 300 | Root domain redirect |

### Cloud-Specific DNS

| Provider | DNS Record |
|---|---|
| **Render** | CNAME → `your-app.onrender.com` |
| **Railway** | CNAME → `your-app.up.railway.app` |
| **Vercel** | CNAME → `cname.vercel-dns.com` |
| **Netlify** | CNAME → `your-app.netlify.app` |
| **Azure Static Web Apps** | CNAME → auto-generated Azure hostname |

### Verify DNS

```bash
# Check A record resolution
dig api.journeyiq.com +short

# Check from multiple locations
nslookup api.journeyiq.com 8.8.8.8
nslookup api.journeyiq.com 1.1.1.1

# Full DNS propagation check
# Visit: https://www.whatsmydns.net/#A/api.journeyiq.com
```

> [!NOTE]
> DNS propagation can take up to 48 hours, but typically completes within 1–4 hours. Set TTL to 300 (5 minutes) for faster updates during initial setup.

---

## Step 9 — Post-Deployment Verification

### Automated Verification Script

```bash
#!/bin/bash
BASE_URL="${1:-http://localhost}"
BACKEND="${BASE_URL}"
PASS=0
FAIL=0

check() {
  local name="$1"
  local url="$2"
  local expected="${3:-200}"

  status=$(curl -s -o /dev/null -w "%{http_code}" "${url}" 2>/dev/null)
  if [ "$status" -eq "$expected" ]; then
    echo "  ✅ ${name} (HTTP ${status})"
    PASS=$((PASS + 1))
  else
    echo "  ❌ ${name} (HTTP ${status}, expected ${expected})"
    FAIL=$((FAIL + 1))
  fi
}

echo "╔══════════════════════════════════════════╗"
echo "║   JourneyIQ Post-Deployment Verification ║"
echo "╚══════════════════════════════════════════╝"
echo ""

echo "── Core Health ──"
check "Basic Health"        "${BACKEND}/api/v1/health"
check "System Health"       "${BACKEND}/api/v1/system/health"
check "Liveness Probe"      "${BACKEND}/api/v1/system/live"
check "Readiness Probe"     "${BACKEND}/api/v1/system/ready"

echo ""
echo "── Infrastructure ──"
check "Database Metrics"    "${BACKEND}/api/v1/system/database"
check "Cache Metrics"       "${BACKEND}/api/v1/system/cache"
check "Runtime Info"        "${BACKEND}/api/v1/system/runtime"

echo ""
echo "── Monitoring ──"
check "System Metrics"      "${BACKEND}/api/v1/system/metrics"
check "Log Telemetry"       "${BACKEND}/api/v1/system/logs"
check "Prometheus"          "${BACKEND}/api/v1/system/prometheus"
check "Version Info"        "${BACKEND}/api/v1/system/version"

echo ""
echo "── ML/AI ──"
check "Model Registry"      "${BACKEND}/api/v1/system/models"

echo ""
echo "── Frontend ──"
check "Frontend SPA"        "${BASE_URL}/"
check "NGINX Health"        "${BASE_URL}/healthz"

echo ""
echo "── API Documentation ──"
check "Swagger UI"          "${BACKEND}/docs"
check "ReDoc"               "${BACKEND}/redoc"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

### Manual Verification Checklist

- [ ] All Docker containers showing `Up (healthy)` status
- [ ] `/api/v1/health` returns `{"status": "healthy", "database": "connected"}`
- [ ] `/api/v1/system/ready` returns `200` (not `503`)
- [ ] `/api/v1/system/deployment` shows `ENVIRONMENT=production`
- [ ] Frontend loads at root URL without errors
- [ ] API docs accessible at `/docs` (Swagger) and `/redoc`
- [ ] Database ping < 50ms (check `/api/v1/system/metrics`)
- [ ] CORS configured for production frontend URL
- [ ] Security headers present (`X-Frame-Options`, `CSP`, etc.)
- [ ] SSL certificate valid and not expiring within 30 days
- [ ] DNS resolving correctly for all configured domains
- [ ] Log file being written to `logs/app.log`
- [ ] Prometheus endpoint returning metrics
- [ ] Scheduler status showing `healthy`

> [!TIP]
> Bookmark the Swagger UI (`/docs`) — it serves as a live API reference and interactive testing tool for all endpoints.

---

*For deployment verification checklist, see [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md). For DevOps operations, see [DEVOPS.md](DEVOPS.md).*
