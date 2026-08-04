# WP18CY Backup Root Cause Report

## Contract
- Freshness target: latest recoverable point no older than **60 minutes**.

## Preview Evidence Captured
- `SCHEDULER_ENABLED=true`
- `DISABLE_BACKUP_SCHEDULER=false`
- `BACKUP_R2_FULL_HOUR_UTC=23`
- Latest `backup_health` row at capture: `2026-08-04T02:04:07.837337+00:00`, mode `lite`, ok `true`, age `~797.7 min`.
- Latest successful `complete-r2` row: `2026-07-31T03:12:41.305671+00:00`.
- Recent `complete-r2` backup jobs for `2026-08-01`, `2026-08-02`, `2026-08-03` were `state=stale` at `stage=archive_construction` after heartbeat activity.
- Earlier `complete-r2-deferred` rows recorded `deferred_by_resource_guard:app_disk_pressure:*`.

## Root-Cause Ladder
1. **Earlier deferrals were explicit and truthful**: resource guard blocked some complete-r2 attempts for disk pressure.
2. **Later scheduled complete-r2 runs did start** but failed to complete and were recovered as stale jobs.
3. **No newer successful complete-r2 artifact replaced the Jul-31 restore point**, so the freshness contract is presently not met in preview.

## What Was Repaired in This WP
- Recovery dashboard certification reads were hardened with bounded indexes so diagnosis is now cheaper and more reliable.

## What Was Not Repaired
- The underlying runtime condition causing recent `scheduler_nightly` `complete-r2` jobs to stall in `archive_construction` was **not safely remediated in this preview-only workspace**.
- No direct production backup run, production restore drill, or production scheduler probe was available.

## Current Disposition
- **Preview backup reliability remains an open blocker.**
