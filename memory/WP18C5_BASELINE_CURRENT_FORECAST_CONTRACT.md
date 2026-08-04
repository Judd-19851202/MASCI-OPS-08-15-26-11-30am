# WP-18C5 Baseline / Current / Forecast Contract

## Final constitutional rule

- **Baseline schedule** remains the approved original commitment identified by `baseline_version_id` on the active schedule version.
- **Current schedule** remains the active governed working version in `project_schedule_versions` plus its governed schedule activity rows.
- **Forecast schedule** is a **separate derived view** produced only from PM-approved actuals and remaining duration via `build_schedule_forecast_view`.
- No C5 route writes forecast rows back into the baseline or current schedule stores.

## Implemented evidence

1. `backend/services/project_schedule_actuals_spine.py::_forecast_row`
   - builds forecast rows from the current activity plus `actual_state`
   - preserves `baseline_*`, `current_*`, and `forecast_*` fields separately
2. `backend/services/project_schedule_actuals_spine.py::build_schedule_forecast_view`
   - resolves baseline rows from `baseline_version_id`
   - returns forecast rows and summary without mutating baseline/current history
3. `frontend/src/pages/PmProjectSchedule.jsx`
   - renders the explicit **Baseline · current · forecast** contract card set
   - exposes forecast rows in a dedicated section with `pm-project-schedule-forecast-section`
4. `backend/services/project_schedule_authority.py::export_schedule_view`
   - adds `forecast_schedule_csv`

## Runtime verification

- `/app/backend/tests/test_wp18c5_schedule_actuals_foundation.py`
  - `test_wp18c5_forecast_row_keeps_baseline_current_forecast_distinct`
- `/app/backend/tests/test_wp18c5_schedule_actuals_api.py`
  - approved actuals updated the forecast export without replacing baseline/current fields
- `/app/test_reports/iteration_115.json`
  - baseline/current/forecast separation verified on PM route `/pm/project-controls/schedule?project_number=ZZ-RUNTIME-CERT-2026`

## Governing decision

**PASS** — C5 preserves baseline, current, and forecast as three distinct schedule layers.
