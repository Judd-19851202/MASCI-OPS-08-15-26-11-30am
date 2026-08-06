# WP-18DB Performance Budget Gate Report

## Change completed in WP-18DB

- `memory/WP18DA_PERFORMANCE_BUDGET_REGISTER.csv` is now enforced by the permanent preview release gate.
- Missing required budget keys or any row not marked `PASS` now blocks certification.

## Required governed budget keys enforced

- `frontend_home_domcontentloaded_preview`
- `frontend_home_loadevent_preview`
- `frontend_home_domcontentloaded_production`
- `api_health_preview`
- `api_version_preview`
- `api_public_grouped_preview`
- `api_health_production`
- `api_version_production`
- `api_public_grouped_production`
- `mongo_safety_issuances_query`
- `mongo_safety_trainings_query`
- `mongo_field_leadership_query`
- `pdf_field_leadership_preview`
- `csv_export_po_preview`
- `build_duration_workspace`
- `backend_restart_warmup_preview`

## Current evidence state

- Release gate result: `PASS`
- Therefore the budget register exists, required keys are present, and the enforced rows are currently passing.

## Conclusion

WP-18DA performance budgets are no longer documentation-only; they are part of the permanent WP-18DB release-control surface.