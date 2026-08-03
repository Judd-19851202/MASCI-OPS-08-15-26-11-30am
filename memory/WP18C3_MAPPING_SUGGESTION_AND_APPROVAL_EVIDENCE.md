# WP18C3 Mapping Suggestion and Approval Evidence

Date: 2026-08-03

## Suggestion engine posture

WP-18C3 implements a governed suggestion stage in `backend/services/project_budget_authority.py`:
- existing customer pay-item reuse suggestions come from exact-number and description-overlap checks;
- enterprise work-type suggestions reuse `_suggest_work_type(...)` from the accepted C2 authority layer;
- suggestion output carries `confidence`, `reasons`, `matched_terms`, and `warnings`;
- rows with missing contractual/classification evidence move to review-required status.

This stage is **advisory only**. It is intentionally non-authoritative and cannot activate a budget version on its own.

## PM approval gate

PM row approval endpoint:
- `POST /api/pm/project-controls/projects/{project_number}/budget/imports/{import_id}/rows/{row_id}/review`

Activation endpoint:
- `POST /api/pm/project-controls/projects/{project_number}/budget/imports/{import_id}/activate`

Activation hard-stops if any row remains in `pending_review` or `review_required`.

## Runtime-certified approval evidence

### Row-review facts
- PM user: `cert.pm@example.com`
- Certified work type selected: `work-type:asphalt`
- Certified project: `ZZ-RUNTIME-CERT-2026`

### First governed activation
- import: `budget-import:ZZ-RUNTIME-CERT-2026:63f83cc774eb`
- row: `budget-import-row:budget-import:ZZ-RUNTIME-CERT-2026:63f83cc774eb:2`
- approved with:
  - `enterprise_work_type_id = work-type:asphalt`
  - `phase_id = PHASE-A`
  - `work_package_id = WP-C3`
  - `schedule_activity_id = ACT-C3-1`
  - `budget_amount = 1000.0`

### Second governed activation
- import: `budget-import:ZZ-RUNTIME-CERT-2026:25c8c28f1309`
- row: `budget-import-row:budget-import:ZZ-RUNTIME-CERT-2026:25c8c28f1309:2`
- approved with:
  - `enterprise_work_type_id = work-type:asphalt`
  - `phase_id = PHASE-A`
  - `work_package_id = WP-C3`
  - `schedule_activity_id = ACT-C3-2`
  - `budget_amount = 1200.0`

## Approval protections verified

1. PM review was required before activation.
2. Work-type approval was explicit.
3. Customer pay-item reuse stayed separate from work-type classification.
4. The later version superseded the prior active version without deleting it.
5. Export comparison was possible because parent/baseline references were preserved.

## Evidence sources

- `backend/services/project_budget_authority.py`
- `backend/routes/enterprise_governance.py`
- `frontend/src/pages/PmProjectBudgetAuthority.jsx`
- `/app/test_reports/iteration_112.json`
