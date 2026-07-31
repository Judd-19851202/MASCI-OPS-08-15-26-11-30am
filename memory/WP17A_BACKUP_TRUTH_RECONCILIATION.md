# WP-17A Backup Truth Reconciliation

Date opened: 2026-07-31
Status: ACTIVE

## Canonical truth direction
- canonical production backup truth = recovery snapshot / archive lineage / scheduler / integrity evidence
- local backup filesystem = secondary local cache / staging context only

## Preview repairs implemented
- OCC backup surfaces now prefer canonical recovery truth
- local backup cache is labeled informational rather than canonical
- backup coverage exclusions are centralized in code policy

## Remaining
- reconcile any remaining backup-facing pages against the same canonical service
- document policy classes for every collection family
