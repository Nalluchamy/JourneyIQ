# JourneyIQ – Personalized Customer Journey Optimization Platform

JourneyIQ is an enterprise-grade retail platform built to optimize customer shopping journeys using real-time behavioral heuristics, cohort segmentation, and machine learning-driven recommendations.

This represents **Phase 1 – Foundation & Project Architecture**, establishing a production-ready boilerplate with async databases, Docker orchestration, standardized API versioning, robust logging, error boundary handlers, and developer quality suites.

---

## Technology Stack

### Frontend
- **React 18** (TypeScript, Vite)
- **Styling**: TailwindCSS & shadcn/ui design tokens
- **Routing**: React Router v6
- **Data Fetching**: TanStack React Query & Axios
- **Localization**: react-i18next

### Backend
- **FastAPI** (Python 3.13+)
- **ORM & Database**: SQLAlchemy (using `asyncpg` driver for full async database operations)
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Logging**: Structlog (Structured JSON logs in production, colored console logs in development)

### ML Service
- **FastAPI** (Python 3.13+) skeleton prepared for recommendation engines, embedding pipelines, and CLV predictive scorers.

### Infrastructure & Tooling
- **Orchestration**: Docker & Docker Compose with container healthchecks
- **CI/CD**: GitHub Actions
- **Quality Tools**: Ruff, Black, isort, mypy (Backend) & ESLint, Prettier (Frontend)

---

## Repository Layout

```text
JourneyIQ/
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI configurations
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/
│   │   │   │   └── health.py  # Enhanced /health endpoint (checks DB connectivity)
│   │   │   └── api.py         # Consolidated API routers mapping /api/v1/...
│   │   ├── core/
│   │   │   ├── config.py      # Pydantic Settings configuration loader
│   │   │   └── logging_config.py # Structlog configurations
│   │   ├── db/
│   │   │   ├── base_class.py  # Declarative Base metadata setup
│   │   │   └── session.py     # Async engine and AsyncSessionLocal provider
│   │   ├── models/            # Empty placeholder for database models
│   │   ├── schemas/           # Empty placeholder for Pydantic schemas
│   │   ├── services/          # Empty placeholder for business logic services
│   │   ├── utils/             # Empty placeholder for auxiliary helper functions
│   │   └── main.py            # FastAPI main application with middleware
│   ├── migrations/            # Alembic migrations folder (async environment setup)
│   ├── alembic.ini            # Alembic CLI config
│   ├── pyproject.toml         # Ruff, Black, isort, and mypy parameters
│   ├── requirements.txt       # Python backend dependencies
│   └── Dockerfile             # Multi-stage python runner
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/        # Reusable presentation components
│   │   ├── i18n/
│   │   │   ├── en.json        # Central English translation copy
│   │   │   └── i18n.ts        # react-i18next bootsrapper
│   │   ├── layouts/
│   │   │   └── MainLayout.tsx # Responsive header, navigation links, and footer layout
│   │   ├── lib/               # Utility functions or integrations
│   │   ├── pages/
│   │   │   ├── Home.tsx       # Landing page (Hero and Features)
│   │   │   ├── Products.tsx   # Placeholder page
│   │   │   ├── About.tsx      # Placeholder page
│   │   │   └── Contact.tsx    # Placeholder page
│   │   ├── routes/            # Route configurations
│   │   ├── services/
│   │   │   └── api.ts         # Centralized Axios client (timeouts & interceptors)
│   │   ├── App.tsx            # Main router and query provider bootstrap
│   │   ├── index.css          # Design system stylesheet mapping HSL vars
│   │   └── main.tsx           # React app mount
│   ├── .eslintrc.json         # ESLint configurations
│   ├── .prettierrc            # Prettier configurations
│   ├── package.json           # Frontend dependencies and npm scripts
│   ├── tsconfig.json          # Root typescript reference configuration
│   ├── vite.config.ts         # Vite bundler parameters with path alias
│   └── Dockerfile             # Node-alpine dev server
├── ml-service/
│   ├── app/
│   │   └── main.py            # Skeleton FastAPI entrypoint
│   ├── Dockerfile             # Python runner for ML services (port 8001)
│   ├── requirements.txt       # Python ML service packages
│   └── README.md              # Machine learning onboarding instructions
├── docs/                      # General architectural guides
├── docker-compose.yml         # Dev environment container orchestrator
├── .env.example               # Environment variables template
├── .gitignore                 # System & environment exclusion rules
└── README.md                  # This file
```

---

## Getting Started

### Prerequisites
- Docker and Docker Compose installed.
- Node.js v20+ and Python 3.13+ (only if running locally without Docker).

### Configuration
Copy the environment variables template and customize as required:
```bash
cp .env.example .env
```

---

## Installation & Deployment

### Running with Docker (Recommended)
Launch all services (PostgreSQL, FastAPI Backend, ML Service, and React Frontend) with health checks:
```bash
docker-compose up --build
```

#### Services Available:
- **Frontend App**: `http://localhost:5173`
- **FastAPI Backend (API v1)**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ML Service**: `http://localhost:8001`
- **PostgreSQL Database**: `localhost:5432`

---

## Running Services Locally (Development mode)

### 1. Database (PostgreSQL)
Ensure you have a running PostgreSQL database and update the `DATABASE_URL` in your local `.env`.

### 2. Backend API
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI service:
   ```bash
   uvicorn app.main:app --reload
   ```

### 3. Frontend App
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install package dependencies:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```

---

## Quality Tooling & Verification

### Backend Quality Commands
Execute inside the `/backend` folder:
- **Ruff Lint Check**: `ruff check .`
- **Black Format Check**: `black --check .`
- **Isort Import Check**: `isort --check-only .`
- **Mypy Type Verification**: `mypy .`

### Frontend Quality Commands
Execute inside the `/frontend` folder:
- **ESLint Lint Check**: `npm run lint`
- **Prettier Format Check**: `npm run format:check`
- **Type Checking & Compilation**: `npm run build`

---

## Future Roadmap
- **Phase 2**: Implement JWT-based OAuth2 Authentication, Session Tracking hooks in the frontend, and User behavior database schema.
- **Phase 3**: Implement the ML recommendations API (linking `ml-service` to the main backend) and A/B Testing engines.
- **Phase 4**: Customer dashboard analytics and telemetry visualization.
