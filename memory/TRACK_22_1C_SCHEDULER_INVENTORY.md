# TRACK 22.1C · Scheduler Inventory

Machine-readable source: `memory/track_22_1c/STARTUP_ORDER_before.json` (all 51 startup handlers with full metadata) and `SCHEDULER_INVENTORY_before.json` (filtered subset).

## Counts

| Category | Count |
|---|---|
| Startup handlers | **51** |
| Shutdown handlers | **1** |
| Scheduler-capable startup handlers | **16** |
| Email-capable startup handlers | **4** |
| Backup-capable | **3** |
| Digest-capable | **2** |
| R2/storage-capable | **2** |
| Mongo-write-capable | **2** |
| Index-creation | **11** |
| Trust-Spine emitters | **0** at startup (all Trust Spine emission happens during workflow dispatch, not at boot) |
| External-API-capable at startup | **0** |

## Email-capable startup handlers (locked by SHA-256 fingerprint)

| Handler | Line | Side effects | SHA-256 |
|---|---|---|---|
| `_start_safety_digest_cron` | 11936 | email + scheduler | `9aabbd4f4d5f0d1c...` |
| `_start_operator_digest_cron` | 11963 | email + scheduler | `8f28a846fd2fa23f...` |
| `_start_po_digest_cron` | 12033 | email + scheduler | `5158200a64be314b...` |
| `_dispatch_reminder_scheduler_start` | 16018 | scheduler | `5a6e39868e220096...` |

Note: `_dispatch_reminder_scheduler_start` is classified scheduler-only because its body uses `SCHEDULER_ENABLED` as its kill switch; the *reminders themselves* fire via `schedule_auto_email` (which is subject to the 3-layer email safety envelope), so the boot handler is not directly email-emitting but is part of the email-lifecycle chain and thus locked.

## Scheduler-capable startup handlers (all 16, unchanged order)

Full list with sources at `SCHEDULER_INVENTORY_before.json`. Key entries:

| Idx | Handler | Line | Side effects |
|---|---|---|---|
| ~3 | `_start_job_photos_indexer` | 10617 | scheduler |
| ~11 | `_start_motive_reliability_loop` | 10742 | scheduler |
| ~26 | `_start_safety_digest_cron` | 11936 | email + scheduler |
| ~27 | `_start_operator_digest_cron` | 11963 | email + scheduler |
| ~28 | `_start_po_digest_cron` | 12033 | email + scheduler |
| ~33 | `_cluster_capacity_history_loop` | 12605 | scheduler |
| ~38 | `_start_backup_verification_cron` | 12750 | backup + scheduler |
| ~46 | `_track_16_10_bootstrap_on_startup` | 13480 | digest + scheduler |
| ~47 | `_start_backup_scheduler` | 15613 | backup + scheduler |
| ~50 | `_dispatch_reminder_scheduler_start` | 16018 | scheduler |

## Idempotency

Every listed handler is idempotent (verified by inspection):

- Index-ensure handlers use `create_index` with the same key spec (Motor no-ops if the index exists).
- Cron/scheduler start handlers use `run_with_singleton_lock(db, "<name>", ...)` so multi-worker deploys elect one runner.
- `SCHEDULER_ENABLED=false` short-circuits every job body to a no-op — preview boot logs confirm ("scheduler disabled on this worker (preview / non-prod)").

## Env-gates

All scheduler-capable handlers respect `SCHEDULER_ENABLED`. All backup handlers respect `BACKUP_ON_STARTUP` and `BACKUP_HOURS_UTC`. All digest handlers respect `AUTO_EMAIL_REPORTS` and `EMAIL_SAFETY_MODE`. No env-gate was widened or narrowed this track.
