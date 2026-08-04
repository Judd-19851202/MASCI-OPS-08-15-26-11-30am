# WP-18C5 Resource Allocation Model

## Scope implemented in C5

Resource allocation in C5 is limited to the planned-vs-actual spine needed for schedule execution authority:

- planned crew / equipment / vendor / subcontractor references on schedule activity rows
- daily work-plan carry-through of planned resource references
- actual labor / equipment / subcontractor evidence preserved on Daily Report work blocks and surfaced on schedule actual candidates

## Reused authorities

- planned resources: `project_schedule_authority` planned assignment fields
- actual work-block resource facts: `project_controls_work_ledger` / Daily Report work blocks
- equipment identity: `equipment_master`
- supplier / subcontractor identity: `suppliers`

## C5 implementation details

- `backend/services/project_schedule_actuals_spine.py::_resolve_equipment_row`
  - resolves equipment references against `equipment_master`
- `backend/services/project_schedule_actuals_spine.py::_resolve_supplier_row`
  - resolves supplier/subcontractor references against `suppliers`
- unresolved identity links remain `review_required`

## Explicit non-goals preserved

- no crew productivity analytics
- no fleet optimization engine
- no labor forecasting engine
- no accounting actual-cost replacement

## Verification

- runtime API chain passed with equipment + supplier references in `/app/backend/tests/test_wp18c5_schedule_actuals_api.py`
- PM/admin UI verified in `/app/test_reports/iteration_115.json`

## Governing decision

**PASS** — C5 carries planned and actual resource evidence through the schedule spine while reusing governed equipment and supplier registries.
