# Changelog

All notable changes to the JourneyIQ project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.1] - 2026-07-13 — Production Validation & SaaS Polishing

### Added
- **System Validation Script** (`backend/scratch/validate_system.py`): Comprehensive 9-check platform health validator producing PASS/FAIL/WARN report with JSON and Markdown export. Checks: DB connection, Storefront data, Recommendation Engine, Deep Learning model (PyTorch NCF), NLP Sentiment, Agentic AI loop, Business Copilot, API health endpoints, and NVIDIA LLM config.
- **7-Stage CI/CD Pipeline**: Extended GitHub Actions workflow with stages: (1) pytest + coverage, (2) validate_system.py smoke test, (3) frontend build, (4) Playwright E2E, (5) Docker image builds, (6) CodeQL security scan, (7) automated release packaging.
- **Professional README**: Complete rewrite with system architecture diagram, all AI pipeline diagrams (NCF, NLP, Agentic AI, Business Copilot grounding), full API reference table, recommendation benchmarks, version roadmap, and deployment guide.

### Changed
- **`test_agent_endpoints`**: Seeded a low-stock product before the orchestrator `/run` API call so the Agentic AI analyzer detects a `LOW_STOCK` anomaly and generates planned actions — completing the assertion.
- **README.md**: Full rewrite from v1.0.0 template to enterprise-grade documentation covering all v1.1–v1.4.1 platform capabilities.

### Fixed
- **`response_builder.py`**: Regex f-string quantifier `{0,3}` changed to `{{0,3}}` to prevent Python f-string parsing the quantifier braces as a tuple expression.
- **Agent test isolation**: `test_agent_endpoints` now seeds its own test data rather than relying on pre-existing database state.

---

## [1.0.0] - 2026-07-11


### Added
- **Route-based Lazy Loading**: Optimized frontend bundle loading with `React.lazy` and `Suspense` inside `App.tsx` routes.
- **PWA Capabilities**: Service worker caching structure (`sw.js`) and application description manifest (`manifest.json`) in the public folder.
- **Global Notification Context**: Centralized toast context provider and custom `useNotification` hook to display error, success, and info toast banners.
- **Error Fallback Screen**: Standard React `ErrorBoundary` fallback catching rendering exceptions, alongside custom 500 `ServerError` and 404 `NotFound` layouts.
- **Network Status Listener**: Browser offline detection template (`OfflinePage.tsx`) which monitors network connectivity statuses.
- **Automated Documentation Portal**: MkDocs site initialization configuration (`mkdocs.yml`) with grouped markdown reference logs under `/docs`.
- **E2E Playwright Tests**: Complete E2E integration specs validating auth, catalogs, dashboard telemetry, and recommendations.

### Changed
- **Unified Storefront Notifications**: Refactored `Cart.tsx`, `Products.tsx`, `ProductDetails.tsx`, `Wishlist.tsx`, and `Profile.tsx` to consume the centralized `useNotification` context instead of local toast state.
- **Storefront Header Navigation**: Integrated `About` and `Contact` routes into the main responsive navigation header (`MainLayout.tsx`) for user accessibility.
- **About/Contact Pages**: Refactored static template placeholder pages into fully themed, functional brand specifications pages with contact forms and client-side validation.
- **Storefront & Dashboard Visual Style**: Completed storefront premium gradient layout revisions and simplified internal dashboard views.

### Fixed
- **Dependency Security Vulnerabilities**: Upgraded Vite to `6.4.3` and configured dependency overrides for `esbuild` in `package.json` to resolve security advisories, achieving a clean `0 vulnerabilities` npm audit report. Upgraded pip tools to secure versions.
- **Python Linting Cleanups**: Excluded styling/false-positive warning rules in `pyproject.toml` and autofixed unused imports/sorting to pass Ruff checks with zero errors.
- **PyTorch Model Inference Serialization**: Fixed backend Deep Learning model return payload serialization during FastAPI schemas envelope validation.
