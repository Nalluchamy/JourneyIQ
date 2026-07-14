# SaaS Cloud Deployment Guide — JourneyIQ v1.5.0

This guide provides step-by-step instructions for deploying the JourneyIQ platform to production-ready SaaS cloud infrastructures.

---

## 1. System Architecture

```mermaid
graph TD
    User([Customer]) -->|HTTPS| Vercel[Vercel Frontend CDN]
    Admin([Admin / Staff]) -->|HTTPS| Vercel
    Vercel -->|REST API Calls| Render[Render FastAPI Web Service]
    
    subgraph "SaaS Backend Services"
        Render -->|SQL Queries| SupabaseDB[(Supabase PostgreSQL)]
        Render -->|Asset URLs| SupabaseStorage[(Supabase Storage)]
        Render -->|Optional Caching| UpstashRedis[(Upstash Redis)]
        Render -->|NCF Model| PyTorch[PyTorch Inference Engine]
    end
    
    subgraph "External Integrations"
        Render -->|LLM Chat| NVIDIA[NVIDIA NIM Cloud API]
    end
```

---

## 2. Environment Configuration

The production environment requires the following variables. Configuration validation is executed automatically at backend startup to prevent launch with insecure defaults.

| Environment Variable | Required | Production Value / Pattern | Description |
|---|:---:|---|---|
| `ENVIRONMENT` | ✅ | `production` | Execution mode (enforces validation checks) |
| `LOG_LEVEL` | ⬚ | `INFO` | Logger level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://...pooler.supabase.com...` | Connection pooled PostgreSQL URL (with SSL required) |
| `SECRET_KEY` | ✅ | Cryptographically secure random string | App-wide hashing secret (e.g. `openssl rand -hex 32`) |
| `JWT_SECRET` | ✅ | Cryptographically secure random string | Signature secret key for JWT access & refresh tokens |
| `FRONTEND_URL` | ✅ | `https://journeyiq.vercel.app` | Frontend client origin (CORS allowed list) |
| `BACKEND_URL` | ✅ | `https://journeyiq-api.onrender.com` | FastAPI backend service hostname |
| `SUPABASE_URL` | ✅ | `https://your-ref.supabase.co` | Supabase API connection URL |
| `SUPABASE_KEY` | ✅ | `service_role` private token | Secret service key to bypass Storage RLS policies |
| `NVIDIA_API_KEY` | ⬚ | `nvapi-...` | Optional NVIDIA NIM API key for Shopping Assistant |
| `REDIS_URL` | ⬚ | `redis://...` | Optional Upstash Redis server endpoint |

---

## 3. Database Deployment (Supabase)

JourneyIQ uses Supabase PostgreSQL as its database backend.

1. **Create Project**: Sign in to [Supabase](https://supabase.com) and create a new project.
2. **Retrieve Connection String**:
   - Go to **Project Settings → Database → Connection Pooler**.
   - Copy the Transaction mode connection URI (port `6543`).
   - Change the prefix from `postgresql://` to `postgresql+asyncpg://`.
3. **Execute Database Migrations**:
   - Run Alembic migrations locally targeting the Supabase instance:
     ```bash
     cd backend
     DATABASE_URL="postgresql+asyncpg://postgres.ref:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require" alembic upgrade head
     ```
4. **Seed database**:
   - Run the seed script to populate premium categories, products, dummy users, orders, and reviews:
     ```bash
     DATABASE_URL="postgresql+asyncpg://postgres.ref:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require" python seed.py
     ```

---

## 4. File Storage Deployment (Supabase Storage)

JourneyIQ product catalog images are hosted on Supabase Storage for durability and CDN speed.

1. **Create Storage Bucket**:
   - In Supabase dashboard, go to **Storage → New Bucket**.
   - Set the bucket name to `products`.
   - Toggle **Public** to `ON` (allowing public URL reads).
2. **Upload Images**:
   - Upload the product images and SVGs from `frontend/public/images/products/*` into the root of the `products` bucket.
3. **URL Generation**:
   - The backend automatically resolves relative paths like `/images/products/macbook_pro.png` by formatting them against `SUPABASE_URL` into: `https://<ref>.supabase.co/storage/v1/object/public/products/images/products/macbook_pro.png` at serialization time.

---

## 5. Backend Deployment (Render)

Deploy the FastAPI service as a Python Web Service on Render.

1. **Create Web Service**:
   - Log in to [Render Dashboard](https://render.com) and click **New → Web Service**.
   - Connect your GitHub repository.
2. **Configure App Build settings**:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:10000`
3. **Set Environment Variables**:
   - Under **Environment**, add the keys from [Environment Configuration](#2-environment-configuration).
4. **Configure Health Probes**:
   - Set the health check path to `/api/v1/health`.

---

## 6. Frontend Deployment (Vercel)

Deploy the React SPA application on Vercel.

1. **Add Project**:
   - Go to [Vercel](https://vercel.com) and import the repository.
   - Set the **Root Directory** to `frontend`.
2. **Configure Build Settings**:
   - **Framework Preset**: `Vite`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm ci`
3. **Configure Environment Variables**:
   - Add `VITE_API_URL` set to the backend Render service URL (e.g. `https://journeyiq-api.onrender.com`).
4. **SPA Rewrites**:
   - The repository includes a `vercel.json` file inside the `frontend` directory which automatically handles rewrites so all routes fallback to `index.html` (resolving client-side router 404s).

---

## 7. Rollback & Disaster Recovery

### Rollback Procedure
If a deployment fails or degrades performance:

1. **FastAPI Web Service (Render)**:
   - Go to Render Dashboard.
   - Select the Web Service, navigate to **Activity**.
   - Click the options dots on the last stable commit build and click **Rollback to this deploy**.
2. **Frontend client (Vercel)**:
   - Go to Vercel project deployments.
   - Locate the previous successful deployment card, click the options menu, and click **Promote to Production**.
3. **ML Recommendation weights**:
   - Trigger a model rollback via the registry endpoints by sending a POST request to:
     `POST /api/v1/system/models/rollback/{version_id}`.

### Backup Strategy
- **Supabase Database**: Automatic backups are enabled by default on Supabase. Backups are stored in Supabase's secure object storage.
- **Manual Backups**: Run the backup script daily or before major migration operations:
  ```bash
  python backend/scripts/backup.py --db-url "$DATABASE_URL" --bucket "backups"
  ```
