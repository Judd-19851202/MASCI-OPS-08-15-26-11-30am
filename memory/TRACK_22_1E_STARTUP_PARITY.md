# TRACK 22.1E · Startup Parity Report

## Result

| Measurement | Before | After | Delta |
|---|---|---|---|
| Runtime routes | 1,440 | 1,440 | 0 ✅ |
| Method count | 1,444 | 1,444 | 0 ✅ |
| OpenAPI paths | 1,263 | 1,263 | 0 ✅ |
| Middleware | 7 | 7 | 0 ✅ (byte-equal chain) |
| `app.router.on_startup` handlers | **51** | **40** | **−11 (migrated to LIFECYCLE_STEPS)** |
| `LIFECYCLE_STEPS` entries | 0 | **11** | +11 |
| **Total lifecycle-executing handlers** | 51 | **51** (11 LIFECYCLE_STEPS + 40 on_startup) | **0** — every handler still fires exactly once |
| Shutdown handlers | 1 | 1 | 0 ✅ |
| Endpoint `qualname` drift | 0 | 0 | 0 ✅ |
| Endpoint `dependency_chain` drift | 0 | 0 | 0 ✅ |
| 5 locked bytecode fingerprints | match | match | 0 ✅ |

## Execution order (post-22.1E)

```
uvicorn imports server
    ├── Resend SDK safety patch (server.py L~105-142)
    ├── FastAPI(lifespan=orchestrated_lifespan) at L73
    ├── 11 @register_lifecycle_step("index-ensure") decorators fire     → LIFECYCLE_STEPS[0..10]
    ├── 40 @app.on_event("startup") decorators fire                     → app.router.on_startup[0..39]
    └── 1  @app.on_event("shutdown") decorator fires                    → app.router.on_shutdown[0]
    ↓
uvicorn invokes orchestrated_lifespan(app)
    ↓
[track-22.1e] LIFECYCLE_STEPS: 11 index handlers run in source order    ← NEW
[track-22.1e] lifespan.startup: LIFECYCLE_STEPS complete
    ↓
[track-22.1d] on_startup: 40 remaining handlers run in registration order  ← unchanged behavior
[track-22.1d] lifespan.startup: complete
    ↓
yield (application serves requests)
```

## Duplicate / missing execution proof

- **No duplicate execution**: each of the 11 migrated handlers appears in `LIFECYCLE_STEPS` exactly once and is NOT present in `app.router.on_startup` (verified by `test_on_startup_no_longer_contains_migrated_handlers`).
- **No missing execution**: `LIFECYCLE_STEPS complete` log fires with 11 handlers; then `lifespan.startup: complete` fires with 40 handlers; then readiness gate flips as before.
- **Each of the 51 lifecycle callables still fires exactly once per boot**.

## Boot log evidence

```
2026-07-04 17:30:16 - [Track 21.2] EMAIL_SAFETY_MODE=strict — Resend SDK patched
2026-07-04 17:30:18 - lib.lifespan_bootstrap - INFO - [track-22.1e] lifespan.startup: executing 11 LIFECYCLE_STEPS
2026-07-04 17:30:18 - [scheduler-lock] indexes ensured
2026-07-04 17:30:18 - [trust-spine] indexes ensured
...
2026-07-04 17:30:19 - lib.lifespan_bootstrap - INFO - [track-22.1e] lifespan.startup: LIFECYCLE_STEPS complete
2026-07-04 17:30:19 - lib.lifespan_bootstrap - INFO - [track-22.1d] lifespan.startup: executing 40 handlers
2026-07-04 17:30:19 - [track-16-08-bootstrap] modules seeded=0
...
2026-07-04 17:30:25 - server - INFO - [iter453.6] startup-readiness gate FLIPPED
2026-07-04 17:30:25 - server - INFO - [dispatch-reminders] background task scheduled
2026-07-04 17:30:25 - lib.lifespan_bootstrap - INFO - [track-22.1d] lifespan.startup: complete
INFO:     Application startup complete.
```

## Verdict

🟢 **STARTUP PARITY CERTIFIED.** 51 handlers still execute; 11 now in the new lifespan-first LIFECYCLE_STEPS registry; 40 remain in legacy on_startup pending Tracks 22.1F-K.
