# JourneyIQ — SaaS Cloud Deployment Guide

> **Version:** 1.0.0 | **Last Updated:** 2026-07-11

This guide covers deploying JourneyIQ across multiple cloud platforms. The backend (FastAPI + PyTorch NCF) and frontend (React + Vite) can be deployed independently to different providers for maximum flexibility.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Environment Variable Reference](#environment-variable-reference)
- [Backend Deployment](#backend-deployment)
  - [Render](#render-backend)
  - [Railway](#railway-backend)
  - [AWS EC2 (Docker)](#aws-ec2-docker)
  - [Azure App Service](#azure-app-service)
- [Frontend Deployment](#frontend-deployment)
  - [Vercel](#vercel-frontend)
  - [Netlify](#netlify-frontend)
  - [Azure Static Web Apps](#azure-static-web-apps)
- [Docker Compose Production](#docker-compose-production)
- [Post-Deployment Verification](#post-deployment-verification)

---

## Architecture Overview

```
┌─────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   Frontend      │──────▶│   NGINX Reverse  │──────▶│   FastAPI        │
│   React + Vite  │       │   Proxy          │       │   Backend        │
│   (Static SPA)  │       │   nginx/nginx.conf│      │   app.main:app   │
└─────────────────┘       └──────────────────┘       └───────┬──────────┘
                                                             │
                                              ┌──────────────┼──────────────┐
                                              │              │              │
                                        ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
                                        │ PostgreSQL │ │   Redis   │ │  PyTorch  │
                                        │ (Supabase) │ │   Cache   │ │  NCF ML   │
                                        └───────────┘ └───────────┘ └───────────┘
```

---

## Environment Variable Reference

> [!IMPORTANT]
> All secrets (`SECRET_KEY`, `JWT_SECRET`, `POSTGRES_PASSWORD`) **must** be unique, cryptographically random values in production. Never reuse development defaults.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://postgres:postgres@db:5432/journeyiq` | Async PostgreSQL connection string (must use `asyncpg` driver) |
| `SECRET_KEY` | ✅ | — | Application-wide secret for signing tokens and sessions |
| `JWT_SECRET` | ✅ | — | Dedicated secret for JWT access/refresh token signing (HS256) |
| `ENVIRONMENT` | ✅ | `development` | Runtime mode: `development`, `staging`, or `production` |
| `REDIS_URL` | ⬚ | `None` | Redis connection string (e.g., `redis://redis:6379/0`). Falls back to in-memory cache if not set |
| `FRONTEND_URL` | ✅ | `http://localhost:5173` | Frontend origin URL for CORS allowlist and email links |
| `BACKEND_URL` | ✅ | `http://localhost:8000` | Backend public URL used in generated links and CORS |
| `POSTGRES_USER` | ✅ | `postgres` | PostgreSQL superuser name |
| `POSTGRES_PASSWORD` | ✅ | — | PostgreSQL password |
| `POSTGRES_DB` | ✅ | `postgres` | PostgreSQL database name |
| `PORT` | ⬚ | `8000` | Backend HTTP listen port |
| `LOG_LEVEL` | ⬚ | `info` | Logging verbosity: `debug`, `info`, `warning`, `error` |
| `VITE_BACKEND_URL` | ✅ (frontend) | `http://localhost:8000` | Frontend build-time variable pointing to the backend API |

> [!TIP]
> Generate secure secrets with:
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(64))"
> ```

---

## Backend Deployment

### Render (Backend)

[Render](https://render.com) provides managed hosting for Python web services with automatic deploys from GitHub.

#### Step 1 — Create a New Web Service

1. Navigate to **Render Dashboard → New → Web Service**
2. Connect your GitHub repository (`JourneyIQ`)
3. Set the **Root Directory** to `backend`

#### Step 2 — Configure Build & Start Commands

| Setting | Value |
|---|---|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000` |

#### Step 3 — Set Environment Variables

In the Render dashboard under **Environment**, add each variable from the [reference table](#environment-variable-reference):

```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/journeyiq
SECRET_KEY=<your-production-secret>
JWT_SECRET=<your-production-jwt-secret>
ENVIRONMENT=production
FRONTEND_URL=https://your-frontend-domain.vercel.app
BACKEND_URL=https://your-backend.onrender.com
REDIS_URL=redis://your-redis-host:6379/0
```

#### Step 4 — Database

- Use Render's managed PostgreSQL or connect to an external Supabase instance.
- Ensure the connection string uses the `asyncpg` driver prefix: `postgresql+asyncpg://`.

> [!WARNING]
> Render's free-tier PostgreSQL instances spin down after 15 minutes of inactivity. Use a paid plan for production workloads.

#### Step 5 — Deploy

Render auto-deploys on push to `main`. Monitor logs in the Render dashboard.

---

### Railway (Backend)

[Railway](https://railway.app) offers a similar PaaS experience with GitHub integration.

#### Step 1 — Create Project

1. Go to **Railway Dashboard → New Project → Deploy from GitHub Repo**
2. Select the `JourneyIQ` repository
3. Set the **Root Directory** to `backend`

#### Step 2 — Configure Service

```bash
# Build Command
pip install -r requirements.txt

# Start Command
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
```

> [!NOTE]
> Railway injects a `$PORT` environment variable automatically. Use `0.0.0.0:$PORT` in the start command so the platform can route traffic correctly.

#### Step 3 — Add PostgreSQL Plugin

1. Click **New → Database → PostgreSQL** in your Railway project
2. Railway automatically provisions the database and sets `DATABASE_URL`
3. Override with the asyncpg driver variant:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
```

#### Step 4 — Add Redis Plugin (Optional)

1. Click **New → Database → Redis**
2. Copy the `REDIS_URL` into your service variables

#### Step 5 — Set Remaining Environment Variables

Add `SECRET_KEY`, `JWT_SECRET`, `ENVIRONMENT=production`, `FRONTEND_URL`, and `BACKEND_URL` in the Railway variables panel.

---

### AWS EC2 (Docker)

For teams needing full infrastructure control, deploy using Docker on an EC2 instance.

#### Step 1 — Launch EC2 Instance

- **AMI:** Ubuntu 22.04 LTS or Amazon Linux 2023
- **Instance Type:** `t3.medium` (minimum for PyTorch NCF training)
- **Storage:** 30 GB gp3
- **Security Group:** Open ports `80`, `443`, `22`

#### Step 2 — Install Docker

```bash
# SSH into your instance
ssh -i your-key.pem ubuntu@<ec2-public-ip>

# Install Docker
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker
```

#### Step 3 — Clone Repository

```bash
git clone https://github.com/your-org/JourneyIQ.git
cd JourneyIQ
```

#### Step 4 — Configure Environment

```bash
cp .env.example .env
nano .env
# Set all production values (DATABASE_URL, SECRET_KEY, JWT_SECRET, etc.)
```

#### Step 5 — Deploy with Docker Compose

```bash
docker compose -f docker-compose.prod.yml up -d
```

This starts four services:
- `journeyiq_db_prod` — PostgreSQL 16 Alpine
- `journeyiq_redis_prod` — Redis 7 Alpine
- `journeyiq_backend_prod` — FastAPI backend with PyTorch
- `journeyiq_frontend_prod` — NGINX serving React SPA (ports `80`/`443`)

#### Step 6 — Verify Deployment

```bash
# Check all containers are running
docker ps

# Test health endpoint
curl http://localhost/api/v1/health

# Check logs
docker logs journeyiq_backend_prod --tail 50
```

#### Step 7 — Configure SSL with Certbot

```bash
sudo apt install certbot
sudo certbot certonly --standalone -d api.yourdomain.com
# Mount certificates into the NGINX container via docker-compose override
```

---

### Azure App Service

Deploy the backend as a Docker container on Azure App Service.

#### Step 1 — Create Azure Resources

```bash
# Login to Azure CLI
az login

# Create Resource Group
az group create --name journeyiq-rg --location eastus

# Create App Service Plan (Linux, B2 tier minimum for ML workloads)
az appservice plan create \
  --name journeyiq-plan \
  --resource-group journeyiq-rg \
  --is-linux \
  --sku B2

# Create Web App with Docker
az webapp create \
  --resource-group journeyiq-rg \
  --plan journeyiq-plan \
  --name journeyiq-backend \
  --deployment-container-image-name ghcr.io/your-org/journeyiq-backend:latest
```

#### Step 2 — Configure Environment Variables

```bash
az webapp config appsettings set \
  --resource-group journeyiq-rg \
  --name journeyiq-backend \
  --settings \
    DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/journeyiq" \
    SECRET_KEY="<your-secret>" \
    JWT_SECRET="<your-jwt-secret>" \
    ENVIRONMENT="production" \
    FRONTEND_URL="https://your-frontend.azurestaticapps.net" \
    BACKEND_URL="https://journeyiq-backend.azurewebsites.net" \
    REDIS_URL="redis://your-redis:6379/0"
```

#### Step 3 — Enable Continuous Deployment

```bash
# Connect to GitHub Container Registry or ACR
az webapp deployment container config \
  --resource-group journeyiq-rg \
  --name journeyiq-backend \
  --enable-cd true
```

> [!NOTE]
> For managed PostgreSQL, use Azure Database for PostgreSQL Flexible Server. For Redis, use Azure Cache for Redis.

---

## Frontend Deployment

The JourneyIQ frontend is a React + Vite SPA that compiles to static files in the `dist/` directory.

### Vercel (Frontend)

#### Step 1 — Connect Repository

1. Go to [vercel.com](https://vercel.com) → **New Project**
2. Import your GitHub repository
3. Set the **Root Directory** to `frontend`

#### Step 2 — Configure Build Settings

| Setting | Value |
|---|---|
| **Framework Preset** | Vite |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |
| **Install Command** | `npm ci` |

#### Step 3 — Set Environment Variables

```
VITE_BACKEND_URL=https://your-backend-url.onrender.com
```

> [!IMPORTANT]
> Vite environment variables **must** be prefixed with `VITE_` to be exposed to the client bundle. Set them **before** building.

#### Step 4 — Deploy

Push to `main` and Vercel auto-deploys. Preview deployments are created for every pull request.

---

### Netlify (Frontend)

#### Step 1 — Connect Repository

1. Go to [netlify.com](https://www.netlify.com) → **New site from Git**
2. Select your GitHub repository
3. Set **Base directory** to `frontend`

#### Step 2 — Configure Build Settings

| Setting | Value |
|---|---|
| **Build Command** | `npm run build` |
| **Publish Directory** | `frontend/dist` |

#### Step 3 — SPA Redirect Rule

Create `frontend/public/_redirects`:

```
/*    /index.html   200
```

This ensures client-side routing works correctly for the React SPA.

#### Step 4 — Set Environment Variables

In **Site settings → Build & deploy → Environment**:

```
VITE_BACKEND_URL=https://your-backend-url.onrender.com
```

#### Step 5 — Deploy

Netlify auto-deploys on push to `main`.

---

### Azure Static Web Apps

#### Step 1 — Create Static Web App

```bash
az staticwebapp create \
  --name journeyiq-frontend \
  --resource-group journeyiq-rg \
  --source https://github.com/your-org/JourneyIQ \
  --location eastus2 \
  --branch main \
  --app-location "/frontend" \
  --output-location "dist" \
  --login-with-github
```

#### Step 2 — Configure Navigation Fallback

Create `frontend/staticwebapp.config.json`:

```json
{
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/assets/*", "/favicon.svg", "/icons.svg"]
  },
  "globalHeaders": {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block"
  }
}
```

#### Step 3 — Set Environment Variables

```bash
az staticwebapp appsettings set \
  --name journeyiq-frontend \
  --setting-names VITE_BACKEND_URL=https://journeyiq-backend.azurewebsites.net
```

---

## Docker Compose Production

For self-hosted deployments, use the production compose file directly:

```bash
# Build and start all services
docker compose -f docker-compose.prod.yml up --build -d

# View running containers
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f backend

# Stop all services
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes (CAUTION: destroys data)
docker compose -f docker-compose.prod.yml down -v
```

### Production Services

| Service | Container | Ports | Health Check |
|---|---|---|---|
| PostgreSQL 16 | `journeyiq_db_prod` | `5432` | `pg_isready` |
| Redis 7 | `journeyiq_redis_prod` | `6379` | `redis-cli ping` |
| FastAPI Backend | `journeyiq_backend_prod` | Internal `8000` | `curl /api/v1/health` |
| ML Service | `journeyiq_ml_service_prod` | Internal `8001` | `curl /health` |
| Frontend (NGINX) | `journeyiq_frontend_prod` | `80`, `443` | — |

---

## Post-Deployment Verification

After deploying to any platform, run through these checks:

```bash
# 1. Health check
curl -s https://your-backend/api/v1/health | jq .

# 2. Readiness probe
curl -s https://your-backend/api/v1/system/ready | jq .

# 3. Version info
curl -s https://your-backend/api/v1/system/version | jq .

# 4. Database connectivity
curl -s https://your-backend/api/v1/system/database | jq .

# 5. Model registry status
curl -s https://your-backend/api/v1/system/models | jq .

# 6. Frontend loads
curl -s -o /dev/null -w "%{http_code}" https://your-frontend/
# Expected: 200
```

> [!CAUTION]
> Always test the complete authentication flow (register → verify email → login → refresh token) after deployment. JWT secrets that don't match between deployments will cause silent token validation failures.

---

*For DevOps operations and CI/CD details, see [DEVOPS.md](DEVOPS.md). For production setup walkthrough, see [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md).*
