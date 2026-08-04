# WP-18C5 Vendor / Subcontractor Execution Model

## Reuse-first decision

C5 reuses the existing supplier registry and does **not** create a second vendor truth.

## Implemented authority line

- canonical registry: `suppliers`
- runtime link resolution: `backend/services/project_schedule_actuals_spine.py::_resolve_supplier_row`
- daily-plan carry-through: planned vendor / subcontractor refs on day-plan items
- actual evidence: Daily Report subcontractor rows and material supplier names are linked into candidate review rows

## PM / admin behavior

- PM sees resolved or review-required supplier/subcontractor links in the actuals review tab.
- Admin gets read-only oversight in the governance page.
- No C5 surface permits direct supplier-master mutation.

## Runtime evidence

- `/app/backend/tests/test_wp18c5_schedule_actuals_api.py` submitted a Daily Report containing supplier/subcontractor evidence and passed the full chain.
- `/app/test_reports/iteration_115.json` verified PM and admin C5 surfaces as pass.

## Governing decision

**PASS** — vendor and subcontractor execution evidence flows through C5 using the governed supplier registry, without duplicate identity truth.