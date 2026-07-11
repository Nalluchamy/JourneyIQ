# JourneyIQ — Personalized Retail & Customer Journey Intelligence Platform

JourneyIQ is a production-hardened, enterprise-grade retail SaaS platform built to optimize customer shopping journeys using real-time behavioral heuristics, cohort segmentation, and machine learning-driven recommendations.

This repository contains the complete **v1.0.0 Release Candidate** codebase, integrating a premium 3D-styled Customer Storefront with an internal Owner Analytics Dashboard, powered by an asynchronous FastAPI backend, a PyTorch Neural Collaborative Filtering (NCF) recommendation service, and a PostgreSQL (Supabase) database layer.

---

## 🌟 Platform Capabilities

- **Vibrant Customer Storefront**: High-performance responsive shopping experience featuring 3D tilt interaction depth cards, an interactive 360-degree product rotation viewer, sticky add-to-cart controls, and multi-step animated checkout checkouts.
- **Owner Analytics Dashboard**: Flat, high-readability operations telemetry panel displaying live revenue telemetry, RFM customer segments, active model registries, and system cache stats.
- **Deep Learning Recommendation Engine**: PyTorch-driven Neural Collaborative Filtering (NCF) processing customer-item embeddings, backed by a hybrid content-popularity filter to handle cold-start new sessions.
- **MLOps Model Registry**: Autonomous APScheduler training loop generating versioned model artifacts with metadata, validation loss monitoring, and one-click rollback endpoints.
- **Prometheus Telemetry Metrics**: Operational `/api/v1/system/prometheus` endpoint exposing CPU, memory, SQLAlchemy db pools, Redis cache hit ratios, and average inference latency gauges.
- **Hardened Security & Backups**: Dynamic rate-limiting, JWT-based security middleware, and automatic database/model checkpoint backups with SHA-256 validation.
- **PWA & Offline Recovery**: Full web app manifest caching (`manifest.json` & `sw.js` service worker) alongside an offline connection status detection screen.

---

## 🛠️ Technology Stack

### Frontend
- **React 18** (TypeScript, Vite 6)
- **Styling**: Vanilla CSS with custom HSL gradient tokens and animations
- **Routing**: React Router v6 (optimized with route-based lazy loading & Suspense)
- **State Management & Fetching**: TanStack React Query & Axios
- **PWA**: Custom Service Worker caching & Install prompts

### Backend
- **FastAPI** (Python 3.13+)
- **ORM & Database**: SQLAlchemy (fully asynchronous connection pools via `asyncpg`)
- **Validation**: Pydantic v2
- **Logging**: Structlog JSON logs

### ML & AI Services
- **PyTorch 2.0+** (NCF Embeddings & Collaborative Filtering)
- **Scheduler**: APScheduler (automated training pipelines)

### Infrastructure & Operations
- **Containerization**: Multi-environment Docker & Docker Compose configurations
- **Orchestration**: Kubernetes manifests (Deployment, Ingress, ConfigMaps, Secrets)
- **CI/CD & Security**: GitHub Actions (CodeQL, Dependabot, Secret scanning)
- **Monitoring**: Prometheus scraping target compatible

---

## 📂 Repository Layout

```text
JourneyIQ/
├── .github/workflows/         # CodeQL security scans, linting, and releases
├── backend/
│   ├── app/
│   │   ├── api/endpoints/    # REST routes (auth, products, system diagnostics)
│   │   ├── core/             # Config loaders and logger setups
│   │   ├── db/               # Async engine and session factories
│   │   ├── models/           # SQLAlchemy database entities (User, Product, Order)
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # NCF Model Registry, ML inference, and payments
│   │   └── main.py           # FastAPI gateway with rate-limiting & timeout middleware
│   ├── migrations/           # Alembic database migration scripts
│   ├── requirements.txt      # Python backend package list
│   └── Dockerfile            # Multi-stage python image definition
├── frontend/
│   ├── public/               # manifest.json, sw.js cache worker, SVG assets
│   ├── src/
│   │   ├── components/ui/    # Accessible design system components (Button, Input)
│   │   ├── context/          # Unified NotificationContext toast providers
│   │   ├── layouts/          # MainLayout responsive header & mobile navigation drawer
│   │   ├── pages/            # Lazy-loaded views (Catalog, Detail, Cart, Dashboard)
│   │   ├── services/api.ts   # Axios API client client mappings
│   │   └── App.tsx           # Router and Query provider bootstrap
│   ├── tests/e2e/            # Playwright E2E integration test suite
│   ├── playwright.config.ts  # Playwright browser parameters
│   └── package.json          # Node dependencies and build scripts
├── ml-service/               # Python ML models microservices definitions
├── nginx/                    # Reverse-proxy reverse configurations
├── scripts/                  # Backup/restore and database seeders scripts
├── k8s/                      # Kubernetes deployment & ingress manifests
├── docker-compose.yml        # Orchestration compose definition
└── README.md                 # This file
```

---

## 🚀 Getting Started

### Prerequisites
- [Docker & Docker Compose](https://www.docker.com/products/docker-desktop/)
- [Node.js v20+](https://nodejs.org/) & [Python 3.13+](https://www.python.org/) (if running locally outside containers)

### Setup Configurations
1. Copy the environment variables template:
   ```bash
   cp .env.example .env
   ```
2. Update `.env` with your JWT secrets and Postgres credentials.

### Run with Docker (Recommended)
Build and run the entire SaaS application stack (Postgres, Redis, Backend, ML, Frontend):
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```
Access points:
- **Customer Storefront**: `http://localhost:5173`
- **FastAPI Backend Gateway**: `http://localhost:8000`
- **Telemetry Swagger Documentation**: `http://localhost:8000/docs`
- **Prometheus Metrics Endpoints**: `http://localhost:8000/api/v1/system/prometheus`

---

## 🧪 Quality Assurance & Testing

Before completing release candidates, verify all test suites execute successfully:

### 1. Backend Pytest Suite
Run the 68 async API unit/integration tests:
```bash
cd backend
$env:PYTHONPATH="."  # PowerShell
pytest
```

### 2. Frontend Playwright E2E Tests
Run E2E storefront workflows (Auth, Catalog, Cart, Checkout, Dashboard tabs):
```bash
cd frontend
npx playwright test
```

### 3. Backend Python Linting
Ensure zero warnings from Ruff:
```bash
cd backend
ruff check .
```

### 4. Frontend Type Checking & Production Build
Validate typescript compiles with zero errors:
```bash
cd frontend
npm run build
```

---

## 🛡️ Security Audits

Validate package vulnerability dependencies are 100% clean:
- **Frontend Check**: `npm audit` (Vite 6 and overrides applied to guarantee 0 vulnerabilities)
- **Backend Check**: `pip-audit`
