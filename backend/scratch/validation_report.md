# JourneyIQ v1.4.1 — Validation Report

> Generated: 2026-07-13 22:08:08  
> Elapsed: 24.4s

---

## Summary

| Metric | Value |
|--------|-------|
| **Overall Score** | **77%** |
| Checks Passed | 7 / 9 |
| Warnings | 2 |
| Errors | 0 |
| Elapsed | 24.4s |

---

## Check Results

| Status | Module | Detail |
|--------|--------|--------|
| ✅ PASS | Database Connection | — |
| ⚠️ WARN | Storefront Data | No products found — run: python seed.py |
| ✅ PASS | Recommendation Engine | RecommendationService imported successfully |
| ✅ PASS | Deep Learning Model (NCF) | Model loaded (7 KB), Precision@10=0.000, NDCG=0.000 |
| ✅ PASS | NLP Sentiment Engine | Sentiment accuracy: 100% (3/3 test cases) |
| ✅ PASS | Agentic AI Loop | Observer returned 11 telemetry sections, Analyzer found 0 issue(s) |
| ✅ PASS | Business Copilot | Query executed (3 data keys), 1 insight(s) generated |
| ⚠️ WARN | API Health Endpoints | Backend not running at http://localhost:8000 — start with: uvicorn app.main:app --reload |
| ✅ PASS | NVIDIA / LLM Chat Config | NVIDIA API key detected — LLM chat enabled |

---

## Warnings

- ⚠️ Storefront Data: No products found — run: python seed.py
- ⚠️ API Health Endpoints: Backend not running at http://localhost:8000 — start with: uvicorn app.main:app --reload

---

## Next Steps

- Fix any ❌ **FAIL** checks before deploying to production.
- Review ⚠️ **WARN** items — they indicate optional features not configured.
- Run `pytest` for full unit + integration test coverage.
- Run `npm run build` to verify frontend compilation.

*Produced by `backend/scratch/validate_system.py`*