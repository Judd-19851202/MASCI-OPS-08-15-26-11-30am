# WP-18C5 Permission and Role Evidence

## PM authority

- PM scope-protected routes:
  - actuals overview
  - actual candidate list
  - actual candidate review
  - daily work plan read/save
- route guard reused:
  - `_require_project_scope(...)` in `backend/routes/enterprise_governance.py`

## Admin posture

- Admin route added for read-only governance oversight:
  - `GET /api/admin/governance/project-controls/schedule/actuals/overview`
- No admin route was added to approve schedule actuals or publish daily work plans.

## Daily Report detail

- PM read access remains project-scoped through the existing Daily Report permission flow.

## Verification

- `/app/test_reports/iteration_115.json`
  - `pm_project_scope`: **PASS**
  - `admin_read_only_governance`: **PASS**
- `/app/backend/tests/test_wp18c5_schedule_actuals_api.py`
  - PM route chain verified end-to-end

## Governing decision

**PASS** — PM remains the project authority gate; admin remains read-only governance for C5.
