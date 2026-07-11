# Changelog

All notable changes to the JourneyIQ project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
