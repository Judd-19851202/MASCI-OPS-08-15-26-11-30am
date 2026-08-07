# WP18C7 Forecast Versioning Report

## Storage
- Collection: `project_forecasting_snapshots`

## Versioning behavior
- Workspace payload is fingerprinted.
- New version persists only when governed workspace content changes or a snapshot note is supplied.
- `recent_versions` and `change_detection` are returned in every workspace response.

## Runtime proof
- PM snapshot capture PASS in `iteration_155.json`
- Backend validation PASS reported version persistence (example: version 29) in `/app/wp18c7_backend_test_results.json`
