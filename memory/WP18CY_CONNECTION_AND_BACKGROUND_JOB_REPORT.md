# WP18CY Connection and Background Job Report

## Email / Background Dispatch
- Daily Report submit path now keeps OPPC eventing intact while repairing only the recipient-facing email transport branch.
- Preview trust result remained `captured_preview`, not silently suppressed.

## Scheduler / Backup Runtime Evidence
- `scheduler_locks` had fresh lock rows at capture time, proving some scheduler activity exists.
- Recent `backup_jobs` showed `complete-r2` jobs starting, heartbeating, then being marked `stale` and ownership-revoked.
- Latest stale jobs all stopped in `stage=archive_construction`.

## Drift / Risk
- This suggests scheduler liveness alone is insufficient; long-running complete-r2 execution is the unstable segment.
- No direct production worker/process inspection was available.
