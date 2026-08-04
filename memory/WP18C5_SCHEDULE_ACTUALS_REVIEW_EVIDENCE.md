# WP-18C5 Schedule Actuals Review Evidence

## Review lane implemented

- Route: `POST /api/pm/project-controls/projects/{project_number}/schedule/actuals/candidates/{candidate_id}/review`
- Allowed PM actions:
  - `approve`
  - `reject`
  - `defer`
  - `needs_review`

## Stored review evidence

- `review_status`
- `review_note`
- `review_history[]`
- `approved_actual`
  - `activity_id`
  - `actual_start_date`
  - `actual_finish_date`
  - `approved_percent_complete`
  - `approved_installed_quantity`
  - `schedule_progress_status`
  - `approved_at`
  - `approved_by`

## Derived schedule update after approval

- `schedule_activities.actual_state`
- `schedule_activities.actual_links`
- `work_packages.actual_totals`
- separate forecast row recomputation

## Runtime proof

- `/app/backend/tests/test_wp18c5_schedule_actuals_api.py`
  - created a candidate from a Daily Report
  - approved it through the PM review route
  - verified approved actual fields and downstream exports
- `/app/test_reports/iteration_115.json`
  - `counts`: `3` candidates, `3` approved
  - PM actuals tab verified as **PASS**

## Governing decision

**PASS** — PM review is the explicit authority gate between Daily Report facts and approved schedule actuals.
