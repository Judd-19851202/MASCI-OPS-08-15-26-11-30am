# WP18C3 Permission and Approval Evidence

Date: 2026-08-03

## Route-level permission model

### PM-scoped routes
- `/api/pm/project-controls/projects/{project_number}/budget/overview`
- `/api/pm/project-controls/projects/{project_number}/budget/versions`
- `/api/pm/project-controls/projects/{project_number}/budget/imports`
- `/api/pm/project-controls/projects/{project_number}/budget/imports/{import_id}/rows/{row_id}/review`
- `/api/pm/project-controls/projects/{project_number}/budget/imports/{import_id}/activate`
- `/api/pm/project-controls/projects/{project_number}/budget/export/*`

These routes pass through `_require_project_scope(...)`, preserving the accepted C2 PM scope model.

### Admin governance routes
- `/api/admin/governance/project-controls/budget/overview`
- `/api/admin/governance/project-controls/budget/review-queue`
- `/api/admin/governance/project-controls/budget/versions`
- `/api/admin/governance/project-controls/budget/imports`
- `/api/admin/governance/project-controls/budget/backfill/run`
- `/api/admin/governance/project-controls/budget/export/*`

These routes require `require_admin` and resolve the authenticated actor for audit / distribution entries.

## Approval gates in code

### Row review gate
`review_budget_import_row(...)` enforces:
- `customer_pay_item_number` required for approval
- `description` required for approval
- `enterprise_work_type_id` required for approval

### Activation gate
`activate_budget_import_session(...)` hard-stops when:
- no rows exist
- no rows are approved
- any row remains pending / review-required
- an immutable original budget already exists and a second original is attempted

## Audit evidence

The implementation writes audit events for:
- `budget_import_staged`
- `budget_import_row_reviewed`
- `budget_version_activated`

Export actions additionally write governed distribution audit rows into `project_budget_distribution_audit`.

## Runtime evidence

- PM live API flow passed for import → row approval → activation.
- Admin governance page and review queue loaded successfully.
- Existing `/pm/project-controls` and `/admin/governance/project-controls` routes remained functional after C3 was added.

Source: `/app/test_reports/iteration_112.json`
