# WP-18DA Observability Report

## Existing observability retained

- runtime reliability hooks in `backend/lib/runtime_reliability.py`
- performance snapshot endpoint in `backend/routes/perf_snapshot.py`
- production health probe route in `backend/routes/admin_production_health.py`
- release identity stamping for frontend + backend

## Hardening added in this pass

- public probe fast-path middleware for `/api/health`, `/api/healthz`, `/api/ready`
- startup index bootstrap as an explicit lifecycle step
- scheduler proxy handling to preserve stable runtime observability across reloads

## Live evidence

- Preview browser verified:
  - public health
  - version
  - public grouped JHA path
- Production browser verified:
  - public health
  - version
  - public grouped JHA path
- Deployment scan: `PASS`
