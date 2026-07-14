# DR-03 Change and Mutation Accounting

## Frontend changed
- `frontend/src/pages/DailyReportRouter.jsx`
- `frontend/src/pages/NewDailyReportV3.jsx`
- `frontend/src/app/routing/AppRoutes.jsx`
- `frontend/src/pages/DailyReportsDashboard.jsx`
- `frontend/src/pages/FieldLeadershipPortalDashboard.jsx`
- `frontend/src/lib/resiliency/dailyReportScope.js`
- `frontend/src/lib/resiliency/draftStore.js`
- `frontend/src/lib/resiliency/resiliencyQueue.js`
- `frontend/src/lib/crewMemory.js`
- `frontend/src/lib/useRememberedFilter.js`
- `frontend/src/lib/dailyReportSchema.js`
- `frontend/src/lib/resiliency/index.js`
- `frontend/src/lib/resiliency/__tests__/dailyReportScope.test.js`
- `frontend/src/lib/resiliency/__tests__/dailyReportMigration.test.js`
- `frontend/src/lib/__tests__/track_26_08_daily_report_draft_continuity.test.jsx`
- `frontend/src/lib/resiliency/resiliencyQueue.test.js`

## Backend changed
- `backend/routes/daily_summary.py`
- `backend/services/ods_spine/model.py`
- `backend/services/ods_spine/ingest.py`
- `backend/tests/test_daily_report_draft_health_contract.py`
- `backend/tests/test_dr03_route_convergence.py`
- `backend/tests/test_dr03_summary_canonical_fields.py`
- `backend/tests/test_dr_cutover_001_v1_to_ods.py`
- `backend/tests/test_dr_cutover_002_daily_summary.py`
- `backend/tests/test_ods_001_spine.py`
- `backend/tests/test_rc2_route_inventory.py`
- `backend/tests/test_track_22_9c_fix_shell_and_route.py`
- `backend/tests/test_dr_unify_003_consolidation.py`

## Documentation changed
- `/app/memory/track_dr_03/*`
- `/app/memory/PRD.md`

## Not changed
- Database schema
- Production data
- GitHub / preview / production deployment state
