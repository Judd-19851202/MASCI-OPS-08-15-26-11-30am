# TRACK 22.1I · Exclusion Matrix

## Handlers explicitly EXCLUDED from Track 22.1I

| # | Handler | Module | Why excluded | Target track | Risk if migrated now |
|---|---|---|---|---|---|
| 1 | `_startup` | `routes.command_center` | Handler is registered via `app.include_router()` on a sub-router — its `@router.on_event("startup")` decorator lives in `backend/routes/command_center.py`, NOT in `server.py`. Migrating requires editing the router module, not `server.py`. Out of scope for this track. | **Track 22.1L** (router-hosted startup handlers) | Editing an included-router module in this track exceeds the "server.py surgical" scope. |
| 2 | `_start_backup_scheduler` | `server` | Starts the nightly full-backup asyncio loop. The loop calls `_backup_scheduler_loop_with_capture(...)`, whose failure paths can invoke `_safety_send_email` → `_dispatch_auto_email`. In strict mode the SDK patch blocks live emails, BUT a backup-safety audit hasn't been performed yet to prove idempotency + safe reorder under the lifespan model. | **Track 22.1I.1** (dedicated backup safety audit) | Backup scheduler semantics can hold R2 tokens, DB audit rows, and reference to file operations — moving without an audit invites subtle regressions. |
| 3 | `_iter453_6_flip_ready_flag` | `server` | **The final readiness-flip handler.** Must remain LAST in on_startup ordering so `app.state.ready = True` is set only after every other bootstrap completes. If migrated to `LIFECYCLE_STEPS`, it would fire BEFORE the remaining on_startup handlers, causing public writes to be accepted prematurely. | **Track 22.1J** (readiness-last · dedicated migration with ordering-preservation harness) | Reordering breaks the ready-flag semantic. |

## Post-22.1I quarantine assertion

Track 22.1I lock test enforces (`test_excluded_handlers_remain_in_on_startup` + `test_readiness_flip_is_last`):
- All 3 excluded handlers remain in `app.router.on_startup`.
- `_iter453_6_flip_ready_flag` is the LAST entry (`on_startup[-1]`).

The assertion will fail LOUDLY if a future track violates the quarantine before proper closure.

## Verdict

🟢 **EXCLUSIONS CERTIFIED.** All 3 excluded handlers documented with owner + target track + reason. Quarantine guaranteed by lock test.
