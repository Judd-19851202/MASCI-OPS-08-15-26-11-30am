# TRACK 22.1H · Scheduler Parity Report

## Result

| Measurement | Before (22.1G close · with pre-existing dupe) | After (22.1H close) | Delta |
|---|---|---|---|
| Runtime routes | 1,441 | 1,441 | **0** ✅ |
| Method count | 1,445 | 1,445 | 0 ✅ |
| OpenAPI paths | 1,264 | 1,264 | 0 ✅ |
| Middleware | 7 | 7 | 0 ✅ (byte-equal chain) |
| `app.router.on_startup` (list length) | **29** (includes 1 dupe of `_start_safety_digest_cron`) | **23** | **−6** (5 migrated + 1 defect-closure) |
| `LIFECYCLE_STEPS` entries | 22 | **27** | **+5** |
| `LIFECYCLE_STEPS` groups | 3 | **4** (`+email-scheduler`) | +1 |
| **Total callables fired per boot** | 51 (with dupe fire) | **50** | **−1** ✅ defect closed |
| Shutdown handlers (qualname + bytecode) | 1 | 1 | byte-equal ✅ |
| Endpoint `qualname` drift on 1,441 routes | 0 | 0 | 0 ✅ |
| Endpoint `dependency_chain` drift | 0 | 0 | 0 ✅ |
| 5 locked bytecode fingerprints | match | **match** | 0 ✅ |

## Scheduler job identity + timing parity

| Handler | Singleton-lock key (unchanged) | Cadence (unchanged) | Env gate (unchanged) |
|---|---|---|---|
| `_start_safety_digest_cron` | `"safety_digest"` | Weekly · Monday 14:00 UTC | `SAFETY_DIGEST_TO_EMAIL` |
| `_start_operator_digest_cron` | `"operator_digest"` | Weekly · Monday 14:00 UTC | `OPERATOR_DIGEST_RECIPIENTS` / fallback |
| `_start_po_digest_cron` | `"po_digest"` | Weekly · Monday 14:00 UTC | `PO_DIGEST_RECIPIENTS` / fallback |
| `_start_backup_verification_cron` | `"backup_verify"` | Weekly | backup-watchdog env gates |
| `_dispatch_reminder_scheduler_start` | APScheduler `dispatch_reminder_scheduler.start(app, db)` | scheduler cadence (env-driven) | `SCHEDULER_ENABLED` |

Zero changes to singleton-lock keys, cadences, env gates, timezone behavior, or recipient lookup order.

## Execution order (post-22.1H)

```
uvicorn imports server
    ├── Startup consistency guard  (module import · L44–65)
    ├── Mongo client bound         (module import · L69–71)
    ├── FastAPI(lifespan=...)      (module import · L73–84)
    ├── Resend SDK safety patch    (module import · L~116–152) ← BEFORE any lifespan step
    ├── 27 @register_lifecycle_step(...) decorators fire → LIFECYCLE_STEPS[0..26]
    │       · [0..10]  group="index-ensure"        (Track 22.1E)
    │       · [11..17] group="seed"                 (Track 22.1F)
    │       · [18..21] group="scheduler-nonemail"   (Track 22.1G)
    │       · [22..26] group="email-scheduler"      (Track 22.1H · NEW)
    ├── 23 @app.on_event("startup") decorators fire → app.router.on_startup[0..22]
    └── 1  @app.on_event("shutdown") decorator fires → app.router.on_shutdown[0]

uvicorn invokes orchestrated_lifespan(app)
    ↓
[track-22.1e] lifespan.startup: executing 27 LIFECYCLE_STEPS
[track-22.1e] lifespan.startup: LIFECYCLE_STEPS complete
    ↓
[track-22.1d] lifespan.startup: executing 23 handlers
[iter453.6] startup-readiness gate FLIPPED
[track-22.1d] lifespan.startup: complete
    ↓
yield (application serves requests)
```

## Duplicate / missing execution proof

- **No duplicate execution:** each of the 5 migrated schedulers appears in `LIFECYCLE_STEPS` exactly once and is NOT present in `app.router.on_startup`.
- **No missing execution:** boot log fires `LIFECYCLE_STEPS: 27 handlers` → `on_startup: 23 handlers` → readiness flip → `lifespan.startup: complete`.
- **1 defect fire retired:** `_start_safety_digest_cron` used to fire twice per boot (pre-existing double-registration); now fires exactly once via `LIFECYCLE_STEPS`.

## Boot log evidence (2026-07-04 19:23 UTC)

```
[Track 21.2] EMAIL_SAFETY_MODE=strict — Resend SDK patched. No live email can leave this pod.
lib.lifespan_bootstrap - INFO - [track-22.1e] lifespan.startup: executing 27 LIFECYCLE_STEPS
lib.lifespan_bootstrap - INFO - [track-22.1e] lifespan.startup: LIFECYCLE_STEPS complete
lib.lifespan_bootstrap - INFO - [track-22.1d] lifespan.startup: executing 23 handlers
server            - INFO - [iter453.6] startup-readiness gate FLIPPED · public writes now accepted
lib.lifespan_bootstrap - INFO - [track-22.1d] lifespan.startup: complete
INFO:     Application startup complete.
```

## Verdict

🟢 **SCHEDULER PARITY CERTIFIED.** All 5 email-capable schedulers migrated cleanly; every function body byte-identical; every singleton-lock key / cadence / env gate / recipient path preserved. Pre-existing double-registration defect closed. `_dispatch_auto_email` fingerprint remains locked at `ebf525...`.
