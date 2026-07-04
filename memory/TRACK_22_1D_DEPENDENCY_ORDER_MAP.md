# TRACK 22.1D · Dependency + Order Map

## Ordering principles (all preserved this track — 0 handler moved)

1. **Config / env guard** — `_db_isolation_failsafe` (handler #1) verifies MongoDB Atlas connectivity before any DB-dependent work.
2. **SDK safety patch** — installs at server.py L~105-142 at *module import time*, BEFORE any `@app.on_event` handler is even registered. Guarantees Resend patch is in place before the lifespan `yield`.
3. **Mongo / client availability** — `_ensure_scheduler_lock_indexes_at_startup` (handler #0) runs first inside the lifespan.
4. **Index setup before dependent jobs** — all 11 `_ensure_*_indexes` / `_arm_*_indexes` handlers run in the first half of the 51-handler sequence.
5. **Scheduler creation before scheduler job registration** — handlers `#3, #11, #26-28, #30, #32, #34, #38, #47, #50` (all scheduler-related) run after their prerequisite index-ensure handlers.
6. **Email-capable schedulers stay behind safety gates** — 4 email-capable schedulers (`_start_safety_digest_cron` #26, `_start_operator_digest_cron` #28, `_start_po_digest_cron` #30, `_dispatch_reminder_scheduler_start` #50) still respect the 3-layer email safety envelope. Fingerprint-locked.
7. **Readiness gate** — `_iter453_6_flip_ready_flag` (handler **#49**, next-to-last) flips `app.state.ready = True` only after everything else. Position preserved.
8. **Final scheduler arming** — `_dispatch_reminder_scheduler_start` (handler #50, **last**) fires after the readiness flip — same semantics as before.
9. **Shutdown ordering** — 1 shutdown handler; no cleanup dependency exists; preserved.

## Cross-handler dependencies (survey)

| Handler | Depends-on | Depended-on-by |
|---|---|---|
| `_ensure_scheduler_lock_indexes_at_startup` (#0) | Mongo client | All scheduler-capable handlers (#3, #11, #26-28, #30, ...) |
| `_seed_shop_users` (#5) | Mongo client, `_ensure_project_team_assignments_indexes` (#6? actually #6) | Any handler consuming shop-users membership |
| Email-capable digest crons (#26-28, #30) | pm_routing, email_dispatch (Track 22.1B) | none directly (fire-and-forget schedulers) |
| Health monitor (#18) | Mongo indexes, session tracker | Readiness flip (#49) |
| `_iter453_6_flip_ready_flag` (#49) | ALL prior handlers | `_dispatch_reminder_scheduler_start` (#50) |

**No handler was reordered. Dependency map is documented as evidence, not as a change plan.**

## Track 22.1D safety-critical order guarantee

Because `lib.lifespan_bootstrap.orchestrated_lifespan` iterates `app.router.on_startup` in the same Python list order that FastAPI's decorators registered, and because the decorators register in source-file top-to-bottom order, and because Track 22.1D did not touch the decorators themselves, **the source-file order → the registration order → the lifespan execution order** — all three chains are byte-identical to Track 22.1C close.

## Future modularization (Track 22.1e+)

When a handler is migrated from decorator to explicit `LIFECYCLE_STEPS` entry (future tracks), the migration MUST:

1. Preserve the handler's position in the ordered execution sequence.
2. Preserve the handler's bytecode SHA-256 (or update the fingerprint file in the same commit).
3. Preserve the handler's env-gate semantics.
4. Preserve its side-effect classification.
5. Pass the Track 22.1D `test_startup_handler_count_preserved` assertion (or its evolution).

This dependency-order map is the authoritative reference for those future migrations.
