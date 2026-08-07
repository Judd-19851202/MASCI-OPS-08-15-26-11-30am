# WP18C7 Executive Decision Book

## Decision
- **Package**: WP-18C7 — Forecasting & Commitments
- **Result**: Implemented as one governed workspace and one governed backend authority.
- **Constitutional order used**: Reuse → Extend → Connect.

## Reused authorities
- `services.cost_codes.schedule_engine` for schedule forecasting and scenario comparison.
- `services.project_operational_intelligence` for production, resource, cost, and lineage evidence.
- `services.project_budget_authority` for PO-derived commitment exposure and actual-cost candidates.
- `services.project_schedule_actuals_spine` for actuals/reconciliation context.

## Net-new additive scope
- `backend/services/project_forecasting_commitments.py`
- PM/Admin/FL read APIs and PM commitment mutation APIs.
- `project_forecast_commitments` and `project_forecasting_snapshots` additive Mongo collections.
- PM, Executive, and Field Leadership frontend routes using one shared React workspace.

## Explicit decisions
- Forecasts never auto-create commitments.
- Executive reuses the PM authority service; no executive-only calculation engine exists.
- Field Leadership receives a constrained read-only slice without full cost review controls.
- Legacy deferred release surfaces remain blocked unless they were truly C7-dependent.

## Runtime evidence
- PM workspace PASS: `/api/pm/project-controls/projects/ZZ-FOR-ASSIGN-01/forecasting/workspace`
- Admin workspace PASS: `/api/admin/governance/project-controls/projects/ZZ-RUNTIME-CERT-2026/forecasting/workspace`
- FL workspace PASS: `/api/field-leadership/portal/projects/ZZ-RUNTIME-CERT-2026/forecasting`
- Test report: `/app/test_reports/iteration_155.json`
- Backend cert: `/app/wp18c7_backend_test_results.json`

## Closeout note
- This decision book reflects the implemented C7 runtime delivered in this run and the evidence captured by live API and UI tests.
