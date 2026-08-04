# WP-18C5 Material Transaction Model

## Constitutional rule preserved

Material **delivery** must remain distinct from material **installation / consumption**.

## Implemented model

- Delivered material facts come from `daily_reports.materials` and are preserved as `material_flow.delivered`.
- Explicit installed / consumed material rows only populate `material_flow.installed` when the source record explicitly says so.
- Outbound material rows are preserved separately as `material_flow.outbound_unclassified` until PM review classifies the movement safely.

## Evidence

- `backend/services/project_schedule_actuals_spine.py::_material_flow`
  - defaults Daily Report material rows to delivery evidence
  - does not guess installation / return / waste when the source is ambiguous
- `frontend/src/pages/ViewDailyReport.jsx`
  - surfaces delivered / installed / outbound review counts on the Daily Report detail route
- `frontend/src/components/pm/schedule/ScheduleActualsWorkspace.jsx`
  - surfaces delivery / installation / outbound review counts for PM review

## Review behavior

- If a report contains ambiguous outbound material rows, the candidate remains review-governed.
- C5 records provenance and confidence instead of normalizing or guessing.

## Governing decision

**PASS** — material delivery and installation remain distinct, and ambiguous outbound movements remain under review instead of being silently normalized.
