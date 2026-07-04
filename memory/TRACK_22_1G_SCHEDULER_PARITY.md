# TRACK 22.1G · Scheduler Parity Report

## Result

| Measurement | Before (22.1F close) | After (22.1G close) | Delta |
|---|---|---|---|
| Runtime routes | 1,441 | 1,441 | **0** ✅ |
| Method count | 1,445 | 1,445 | 0 ✅ |
| OpenAPI paths | 1,264 | 1,264 | 0 ✅ |
| Middleware | 7 | 7 | 0 ✅ (byte-equal chain) |
| `app.router.on_startup` | **33** | **29** | **−4** (migrated to LIFECYCLE_STEPS.scheduler-nonemail) |
| `LIFECYCLE_STEPS` entries | 18 | **22** | **+4** |
| `LIFECYCLE_STEPS` groups | 2 (index-ensure, seed) | 3 (index-ensure, seed, scheduler-nonemail) | +1 |
| **Total lifecycle-executing handlers** | 51 | **51** (22 + 29) | **0** — every handler still fires exactly once |
| Shutdown handlers (qualname + bytecode) | 1 | 1 | byte-equal ✅ |
| Endpoint `qualname` drift on 1,441 routes | 0 | 0 | 0 ✅ |
| Endpoint `dependency_chain` drift | 0 | 0 | 0 ✅ |
| 5 locked bytecode fingerprints | match | match | 0 ✅ |
| 5 email-capable schedulers in on_startup | 5 | 5 | **0 (untouched)** ✅ |

## Scheduler job identity + timing parity

| Handler | Job ID (unchanged) | Trigger type (unchanged) | Interval / cron (unchanged) | Env gate (unchanged) |
|---|---|---|---|---|
| `_start_job_photos_indexer` | `_job_photos_indexer_loop` (asyncio task) | fire-and-forget loop | loop-driven | none |
| `_start_motive_reliability_loop` | `motive_reliability_supervisor` (singleton-locked task) | 4 sub-cadences per `lib.motive_reliability` | as defined in module | none |
| `_start_health_monitor` | `start_health_monitor_loop` | 60-s poll | 60 s | none |
| `_cluster_capacity_history_loop` | `_loop` (asyncio task) | hourly cadence after initial record | 3600 s | none |

Zero changes to job IDs, trigger types, intervals, or env gates.

## Execution order (post-22.1G)

```
uvicorn imports server
    ├── (all module-import guards + Resend SDK patch — unchanged)
    ├── 22 @register_lifecycle_step(...) decorators fire → LIFECYCLE_STEPS[0..21]
    │       · [0..10]  group="index-ensure"        (Track 22.1E)
    │       · [11..17] group="seed"                 (Track 22.1F)
    │       · [18..21] group="scheduler-nonemail"   (Track 22.1G · NEW)
    ├── 29 @app.on_event("startup") decorators fire → app.router.on_startup[0..28]
    └── 1  @app.on_event("shutdown") decorator fires → app.router.on_shutdown[0]

uvicorn invokes orchestrated_lifespan(app)
    ↓
[track-22.1e] lifespan.startup: executing 22 LIFECYCLE_STEPS
[track-22.1e] lifespan.startup: LIFECYCLE_STEPS complete
    ↓
[track-22.1d] lifespan.startup: executing 29 handlers
[iter453.6] startup-readiness gate FLIPPED
[track-22.1d] lifespan.startup: complete
    ↓
yield (application serves requests)
```

## Duplicate / missing execution proof

- **No duplicate execution:** each of the 4 migrated scheduler handlers appears in `LIFECYCLE_STEPS` exactly once and is NOT present in `app.router.on_startup` (asserted).
- **No missing execution:** boot log confirms `LIFECYCLE_STEPS: 22 handlers` then `on_startup: 29 handlers` then readiness flip.
- **Total callables per boot = 51** (22 + 29), unchanged from Track 22.1F close.

## Boot log evidence (2026-07-04 18:37 UTC)

```
[Track 21.2] EMAIL_SAFETY_MODE=strict — Resend SDK patched. No live email can leave this pod.
lib.lifespan_bootstrap - INFO - [track-22.1e] lifespan.startup: executing 22 LIFECYCLE_STEPS
lib.lifespan_bootstrap - INFO - [track-22.1e] lifespan.startup: LIFECYCLE_STEPS complete
lib.lifespan_bootstrap - INFO - [track-22.1d] lifespan.startup: executing 29 handlers
server            - INFO - [iter453.6] startup-readiness gate FLIPPED · public writes now accepted
lib.lifespan_bootstrap - INFO - [track-22.1d] lifespan.startup: complete
INFO:     Application startup complete.
```

## Verdict

🟢 **SCHEDULER PARITY CERTIFIED.** All 4 non-email schedulers migrated cleanly; every function body byte-identical; every job ID / trigger / interval / env gate preserved; email-capable quarantine intact.
