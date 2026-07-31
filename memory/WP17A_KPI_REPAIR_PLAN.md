# WP-17A KPI Repair Plan

Date opened: 2026-07-31
Status: ACTIVE

## Priority order
1. Draft Health semantics
2. Canonical Backup Truth unification
3. Backup coverage / TTL telemetry policy
4. Security posture / CORS truth
5. Governance freshness and confidence
6. R2 lifecycle freshness vs ownership separation
7. Cross-portal master bindings
8. Production certification freshness
9. Disk pressure / artifact retention
10. KPI metadata, reconciliation, automation, and remaining P2–P4 items

## Current preview-verified repairs
- Draft telemetry now emits stable `actorIdentity` metadata for future canonical entity grouping.
- `/api/admin/draft-health` now summarizes distinct draft entities / draft slots rather than raw event totals.
- Operations Control backup cards now consume canonical recovery truth and label local cache as secondary.
- Backup coverage exclusions are centralized in `lib/backup_coverage_policy.py` and now classify `motive_events` as non-blocking TTL telemetry.
- Security posture now evaluates effective runtime CORS policy instead of only raw `CORS_ORIGINS` env text.
- Governance freshness states (`CURRENT`, `AGING`, `STALE`, `UNKNOWN`, `SCAN_FAILED`) are exposed.
- R2 lifecycle health now separates inventory freshness from ownership / orphan risk details.
- Diagnostics now exposes certification freshness window context.

## Still open in this work package
- Workflow-specific certification freshness SLA review
- Disk pressure local trend / projected exhaustion recorder
- KPI metadata framework and drill-down transparency
- Multi-page reconciliation audit and automation
- Remaining portal-by-portal KPI inventory
