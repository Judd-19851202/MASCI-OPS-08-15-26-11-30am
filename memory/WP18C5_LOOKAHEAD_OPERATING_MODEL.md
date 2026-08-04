# WP-18C5 Lookahead Operating Model

## Preserved operating principle

Rolling lookahead remains an **overlay**, not a duplicate schedule and not a rewrite of baseline/current truth.

## Implemented operating chain

`Master Schedule -> Rolling Lookahead -> Daily Work Plan -> Daily Report Work Blocks -> PM Review -> Approved Actuals -> Forecast / Schedule Status`

## Reused authority

- Lookahead persistence remains in the existing project-controls lane:
  - `backend/services/project_controls_authority.py::get_project_lookahead`
  - `backend/services/project_schedule_authority.py::save_schedule_lookahead`
- PM routes remain under the governed enterprise governance surface:
  - `GET/PUT /api/pm/project-controls/projects/{project_number}/schedule/lookahead`

## C5 extension

- Daily work plans are derived from the active schedule version plus the saved lookahead.
- The lookahead stays short-horizon and editable by the PM.
- Saving lookahead does **not** activate a new schedule version and does **not** rewrite baseline history.

## UI evidence

- `frontend/src/pages/PmProjectSchedule.jsx`
  - lookahead tab remains intact
  - new daily work plan panel appears below the lookahead editor
- `frontend/src/components/pm/schedule/ScheduleDailyWorkPlanPanel.jsx`

## Verification

- Testing agent iteration `115` verified:
  - `pm-project-schedule-lookahead-tab`
  - `pm-project-schedule-daily-plan-section`
  - responsive + Spanish behavior pass

## Governing decision

**PASS** — lookahead remains governed overlay authority and now feeds the C5 daily work plan without duplicating schedule truth.
