# WP-18C5 Daily Work Plan Model

## Implemented store

- Collection: `project_daily_work_plans`
- Service authority: `backend/services/project_schedule_actuals_spine.py`
  - `get_daily_work_plan`
  - `save_daily_work_plan`

## Model shape

- `plan_id`
- `project_number`
- `work_date`
- `status` (`draft | published | archived`)
- `version_id`
- `baseline_version_id`
- `lookahead_id`
- `items[]`
  - `activity_id`, `activity_name`
  - `work_package_id`, `budget_line_id`, `customer_pay_item_number`, `project_cost_code`
  - `planned_quantity`, `planned_hours`
  - `planned_crews`, `planned_equipment`, `planned_materials`, `planned_vendors`, `planned_subcontractors`, `planned_constraints`
  - `actual_status`, `approved_percent_complete`, `daily_goal_note`

## Authority line

- Default plan derivation comes from the active current schedule plus saved lookahead.
- PM may save/publish the day plan.
- The day plan remains an execution overlay and does not alter schedule-version history.

## Runtime evidence

- PM route:
  - `GET /api/pm/project-controls/projects/{project_number}/schedule/daily-work-plan`
  - `PUT /api/pm/project-controls/projects/{project_number}/schedule/daily-work-plan`
- Runtime certification:
  - `/app/backend/tests/test_wp18c5_schedule_actuals_api.py` published a daily work plan and verified status `published`
- QA report:
  - `/app/test_reports/iteration_115.json` marked `pm-project-schedule-daily-plan-section` and `pm-project-schedule-save-daily-plan-button` as **PASS**

## Governing decision

**PASS** — the daily work plan exists as a distinct day-of-execution model under PM control, derived from governed schedule + lookahead truth.