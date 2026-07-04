# Delete / Retire / Merge Candidates

## DELETE NOW (safe · zero user impact) — 0 items
Nothing meets the "dead AND harmful" bar at the deploy gate. Class-A doctrine.

## RETIRE POST-DEPLOY (safe cleanup, not release-critical) — 37 items

### 25 stale root `.md` audit docs (Track 21.z scope · move to `/app/memory/_archived/`)
- LEGACY_RECORDS_ARCHITECTURE_iter248.md
- test_result.md
- FLEET_SEVERITY_REVIEW_PACKAGE_iter251.md
- HARD_USE_READINESS_AUDIT_iter240.md
- FLEET_OPS_FOUNDATION_iter251_ARCHITECTURE.md
- PORTAL_PARITY_AUDIT_iter244.md
- PRODUCTION_R2_CUTOVER.md
- LIVE_PRODUCTION_AUDIT_iter247.md
- QA_PERF_AUDIT.md
- QA_PERF_AUDIT_LIVE.md
- QA_REPORT_PHASE1.md
- FINAL_DEPLOYMENT_READINESS_LOCK.md
- DEPLOY.md
- ATLAS_MIGRATION.md
- READINESS_AUDIT_iter256.md
- image_testing.md
- SEVERITY_RULINGS_iter251.md
- auth_testing.md
- HARD_USE_READINESS_AUDIT_iter246.md
- QA_REPORT_MASTER_SOT.md
- MASCI_IT_INTEGRATION_BRIEF.md
- QA_PLATFORM_AUDIT.md
- DEPLOYMENT_CHECKLIST.md
- POST_DEPLOY_PRODUCTION_OBSERVATION.md
- FINAL_PLATFORM_STABILIZATION_REPORT.md

### 12 legacy frontend pages (Track 21.y scope · gated by `/legacy/*` router — no primary-nav link)
Sample: `pages/legacy/*`, `pages/transportation/_orientation.jsx` (unstable-nested-components warned by lint).

### ~5 legacy Mongo collections (Track 19.62 Phase B scope)
`db.legacy_*` / `db.deprecated_*` collections — no active writes, historical reads only.

### ~40 iter### test files (Track 21.x scope)
Pre-15.30 tests still using retired shared-password admin auth. Non-critical (excluded from Track-20.8 envelope).

## MERGE (future) — 2 items
- `db.fire_extinguishers` → `db.equipment_master` (Track 19.62 Phase B).
- `backend/server.py` line 13610 `_dispatch_auto_email` → `backend/trust_spine/dispatch.py` (Track 21.x extraction).

## Zero-drift enforcement
Every candidate above is documented in `TECHNICAL_DEBT_REGISTER.md` (Class-C entries or explicit Phase-2 plans).
