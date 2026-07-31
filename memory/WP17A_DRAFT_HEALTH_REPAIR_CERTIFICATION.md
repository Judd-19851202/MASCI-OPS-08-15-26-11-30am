# WP-17A Draft Health Repair Certification

Date opened: 2026-07-31
Status: ACTIVE

## Repair statement
- Replaced raw event-count semantics with distinct draft-entity / draft-slot aggregation in `/api/admin/draft-health`.
- Added stable `actorIdentity` emission in frontend telemetry for forward-correct grouping.
- Exposed confidence + limitations when historical telemetry rows lack actor identity.

## Verified behavior
- repeated saves on one draft entity no longer inflate the entity count in the repaired summarizer
- failed, stale, abandoned, committed, and restored dimensions are now explicit

## Remaining
- portal-by-portal wording audit to ensure no UI still implies raw telemetry equals unique draft count where that is not true
