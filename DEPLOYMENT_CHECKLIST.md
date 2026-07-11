# Production Deployment Checklist - JourneyIQ

Follow this checklist to prepare and deploy JourneyIQ to staging and production containerized environments.

## 1. Environment Configurations
Verify the following variables are set in your production `.env` or system environment:
- [ ] `ENVIRONMENT=production`
- [ ] `DATABASE_URL` (Supabase PostgreSQL pooler string)
- [ ] `REDIS_URL` (Redis cloud server URL)
- [ ] `JWT_SECRET` (Strong 256-bit key)
- [ ] `JWT_REFRESH_SECRET` (Separate strong 256-bit key)
- [ ] `REQUIRE_EMAIL_VERIFICATION` (Set to `True`)

## 2. Database Migrations
Run Alembic migrations directly against the target database:
- [ ] `alembic upgrade head`

## 3. Local Verification Tests
- [ ] Verify linting: `ruff check backend`
- [ ] Verify typing: `mypy backend`
- [ ] Run backend unit and integration tests: `pytest backend/tests`
- [ ] Ensure HTML coverage is generated: `coverage html`

## 4. Load Testing Check
Run load tests using our test verification script (e.g. hitting dashboard / recs endpoints with simulated concurrent traffic) to verify memory and CPU metrics stability:
- [ ] Execute `python backend/tests/load_test_locust.py` (or HTTP script) simulating 100 concurrent requests.
- [ ] Monitor memory and response latency graphs.
