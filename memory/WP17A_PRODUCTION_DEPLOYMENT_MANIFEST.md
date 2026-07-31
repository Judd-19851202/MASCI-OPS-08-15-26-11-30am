# WP17A Production Deployment Manifest

Date prepared: 2026-07-31
Manifest status: **READY TO DEPLOY · NOT YET EXECUTED**

## Deployment scope

Deploy the complete verified WP-17A package:
- canonical KPI dictionary and metadata governance
- runtime reconciliation and certification routes
- predictive capacity intelligence
- Executive / Project / HR / Safety KPI truth repairs
- standardized metadata on audited governance / trust / operational health surfaces

## Exact build identities

- Current production build identity:
  - commit: `fd89cfe673d61292075a4f6668a2d0e71dcdd5f4`
  - source hash: `ec85d311da889befeb222f6ee3bf1931`
  - built at: `2026-07-31T03:07:30+00:00`
- Proposed WP-17A production build identity:
  - commit: `bd9bdd2012c4f2e31b57d7390218b20c361c6dcc`
  - source hash: `665ea6071d75dd046905a35dfe8dcea4`
  - built at: `2026-07-31T19:25:22.462301+00:00`

## Backend changes

- `backend/lib/wp17a_kpi_governance.py`
- `backend/routes/wp17a_kpi_governance.py`
- `backend/routes/cluster_capacity.py`
- `backend/routes/executive_overview.py`
- `backend/routes/project_health.py`
- `backend/routes/operational_kpis.py`
- `backend/routes/employee_requests.py`
- `backend/routes/field_leadership.py`
- `backend/routes/sprint_a.py`
- `backend/routes/platform_data_truth.py`
- `backend/routes/admin_platform_trust.py`
- `backend/routes/occ_health_aggregator.py`
- `backend/routes/admin_operational_health.py`
- `backend/routes/daily_reports.py`
- `backend/routes/qaqc.py`
- `backend/routes/admin_persistence_health.py`
- `backend/lib/database_client_governance.py`
- `backend/server.py`

## Frontend changes

- `frontend/src/pages/ExecutiveOverview.jsx`
- `frontend/src/pages/ProjectHealth.jsx`
- `frontend/src/pages/HrHubV2.jsx`
- `frontend/src/components/HrKpiStrip.jsx`
- `frontend/src/components/SafetyOperationalKpisCard.jsx`
- `frontend/src/components/admin/StorageObservabilityCard.jsx`
- `frontend/src/pages/admin/AdminDatabase.jsx`
- `frontend/src/lib/kpiMetadata.js`
- `frontend/src/buildVersion.generated.js`

## Configuration changes

- No new required environment variables introduced for WP-17A.
- Existing protected variables remain authoritative:
  - `REACT_APP_BACKEND_URL`
  - `MONGO_URL`
  - `DB_NAME`

## Database / index changes

- No destructive migrations.
- No new mandatory production migrations.
- Existing collections and indexes remain authoritative.

## Data backfills / operational jobs

- No new production backfill was executed in this release attempt.
- No ambiguous data mutations authorized.
- Existing scheduled jobs remain in place; WP-17A adds no destructive cleanup job.

## Intentional limitations

- MaintainX is **MOCKED / DISCONNECTED / NOT_APPLICABLE** and excluded from certification.
- Visual / UX standardization remains out of scope until WP-17 approval.

## Pre-deployment evidence

- Preview reconciliation: PASS
- Preview blocking findings: 0
- Preview certification: EXECUTIVE_READY_FOR_APPROVAL
- Preview deployment package: READY
- Release gate decision: PASS (`scripts/release_gate.py --target production --json` with canonical clean-checkout proof)
- Backend tests: `22 passed, 1 skipped`
- Frontend build: PASS
- Python lint: PASS
- JS lint: PASS
- Production smoke on existing live site: PASS for baseline health endpoints only
- Production WP-17A governance routes: **NOT LIVE** (`404`)

## Rollback procedure

- Rollback target is the currently live production build:
  - commit `fd89cfe673d61292075a4f6668a2d0e71dcdd5f4`
  - source hash `ec85d311da889befeb222f6ee3bf1931`
- Use the platform rollback to the last good production checkpoint.
- Re-run `tools/verify-production.sh` after rollback.

## Post-deployment test matrix

- `tools/verify-production.sh https://mascidocs.com`
- live `/api/admin/wp17a/kpi-dictionary`
- live `/api/admin/wp17a/reconciliation`
- live `/api/admin/wp17a/certification`
- live `/api/admin/wp17a/deployment-package`
- representative portal UI validation across Executive / Admin / Project / HR / Safety / Storage

## Current blocker

- Native production deployment has not been executed from this agent environment; live production remains on the older build and therefore cannot be certified for WP-17A lock.