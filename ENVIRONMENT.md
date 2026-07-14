# Environment Variable Reference Directory — JourneyIQ v1.5.0

This document lists all environment variables recognized by JourneyIQ's backend and frontend applications.

---

## 1. Backend Environment Variables

These variables are loaded by the FastAPI service at startup from system environment vars or local `.env` / `.env.production` files.

| Variable Name | Value Type | Default / Fallback | Security Classification | Purpose & Usage |
|---|:---:|---|:---:|---|
| `ENVIRONMENT` | String | `development` | Public | Defines launch mode: `development`, `testing`, `staging`, or `production`. |
| `LOG_LEVEL` | String | `INFO` | Public | Enforces standard logging severity: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |
| `DATABASE_URL` | String | SQLite URL | **Secret** | Connection string for database. Enforced to use SSL in production mode. |
| `SECRET_KEY` | String | Mock key | **Secret** | Symmetric encryption signature key for cookies and telemetry. |
| `JWT_SECRET` | String | Mock key | **Secret** | Signature validation key for JSON Web Tokens. |
| `JWT_ALGORITHM` | String | `HS256` | Public | Cryptographic algorithm for JWT encoding. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | `1440` (24 hours) | Public | Duration until access token expires. |
| `FRONTEND_URL` | String | `http://localhost:5173` | Public | The client origin server domain. Used for CORS matching. |
| `BACKEND_URL` | String | `http://localhost:8000` | Public | Hostname URL of the backend API service. |
| `REDIS_URL` | String | `None` | **Secret** | Optional connection endpoint for Redis caching server. |
| `SUPABASE_URL` | String | `None` | Public | API entry hostname for your Supabase cloud project. |
| `SUPABASE_KEY` | String | `None` | **Secret** | Database service role token to authenticate storage uploads. |
| `NVIDIA_API_KEY` | String | `None` | **Secret** | API key for NVIDIA NIM LLM inference calls. |

---

## 2. Frontend Build-Time Variables

These variables are injected during the frontend build step (`npm run build`) and are bundled into the static React assets.

| Variable Name | Value Type | Default / Fallback | Purpose & Usage |
|---|:---:|---|---|
| `VITE_API_URL` | String | `http://localhost:8000` | Target URL pointing to the FastAPI backend API server. |
| `VITE_BACKEND_URL` | String | `http://localhost:8000` | Alternative parameter pointing to the backend API host. |
