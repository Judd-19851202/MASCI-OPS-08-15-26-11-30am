# TRACK 22.1I.1 · Dependency Proof

## Purpose
Prove that moving `_start_backup_scheduler` from `app.router.on_startup` into `LIFECYCLE_STEPS.backup-scheduler` (which runs BEFORE the remaining `on_startup` handlers) cannot violate any dependency.

## Dependencies checked
| Producer | Consumed by `_start_backup_scheduler`? | Notes |
|---|---|---|
| `index-ensure` handlers | ❌ No | Handler only touches `BACKUPS_DIR` (fs) and `db` (motor client — lazy connect). No Mongo query at boot depends on any specific index. Singleton-lock uses idempotent upsert. |
| `seed` handlers | ❌ No | No seed data required. |
| `scheduler-nonemail` handlers | ❌ No | Independent loops. |
| `email-scheduler` handlers | ❌ No | Failure-email path is in `_start_backup_verification_cron`, not here. |
| `misc-bootstrap` handlers | ❌ No | Handler does not depend on any bootstrap ordering. |
| Mongo readiness | ✅ Lazy | Motor client is import-time; first Mongo I/O happens inside the loop after `asyncio.sleep(...)` — plenty of time. |
| R2 readiness | ❌ | R2 not touched at startup. |
| Trust Spine collections | ❌ | Not written at startup. |
| Resend SDK patch order | ✅ Enforced | Patch is installed at `server.py` module-scope BEFORE any `LIFECYCLE_STEPS` fires (asserted by lock test). |
| Platform Ops API utilities | ❌ | Not called. |
| Readiness flag (`app.state.ready`) | ❌ | Not consumed. |
| Router-hosted `command_center._startup` | ❌ | Independent. |
| Shutdown handler | ❌ | Independent. |

## Ordering safety
The new execution position is BEFORE any legacy `on_startup` handler (readiness flip + command_center router startup) and AFTER all 47 pre-existing `LIFECYCLE_STEPS`. Two behavioral windows:

1. **Handler runs, task is created, then LIFECYCLE_STEPS finishes, then legacy on_startup runs, then readiness flips.** The 1.5-second settle-window sleep gives the loop 1.5s in which the two remaining on_startup handlers also complete. This mirrors the pre-migration behavior when `_start_backup_scheduler` was in position 22/24 of `on_startup`.
2. **The supervisor task and asset-spine task are fire-and-forget.** Both `await asyncio.sleep(...)` before doing meaningful work. Ordering is orthogonal.

## Readiness-last guarantee preserved
`_iter453_6_flip_ready_flag` remains at index `[-1]` of `app.router.on_startup`. Post-migration verification:
```
on_startup = ["_startup" (command_center), "_iter453_6_flip_ready_flag"]
```
The `LIFECYCLE_STEPS` phase completes before either legacy handler fires. Readiness flip still runs last.

## Verdict
🟢 **SAFE TO MIGRATE.** No dependency violation. No ordering regression. Strict subset of correct behavior.
