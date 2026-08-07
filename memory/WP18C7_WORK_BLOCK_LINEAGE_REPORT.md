# WP18C7 Work Block Lineage Report

## C7 lineage chain
`Project → Schedule/Assignment Truth → Work Block / Quantity Evidence → Forecast/Commitment Workspace`

## Runtime implementation
- `project_operational_intelligence` supplies quantity, timeline, cost, resource, and lineage coverage evidence.
- `project_schedule_actuals_spine` supplies actuals/reconciliation context.
- The C7 service embeds `work_block_lineage.summary` and `source_review_queue` directly in the workspace payload.

## Confidence rule
- Lineage confidence is carried into the C7 `confidence` payload.
- Orphan events reduce confidence and are surfaced instead of silently ignored.

## Evidence
- Verified in PM/Admin runtime payloads by `iteration_155.json`.
