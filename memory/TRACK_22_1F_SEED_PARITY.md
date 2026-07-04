# TRACK 22.1F · Seed Parity Report

## Result

| Measurement | Before | After | Delta |
|---|---|---|---|
| Runtime routes | 1,440 | **1,441** | **+1** (intentional: `GET /api/admin/platform/status`) ✅ |
| Method count | 1,444 | 1,445 | +1 (same route) ✅ |
| OpenAPI paths | 1,263 | 1,264 | +1 (same route) ✅ |
| Middleware | 7 | 7 | 0 ✅ (byte-equal chain) |
| `app.router.on_startup` | **40** | **33** | **−7** (migrated to LIFECYCLE_STEPS.seed) |
| `LIFECYCLE_STEPS` entries | 11 | **18** | **+7** |
| `LIFECYCLE_STEPS` groups | 1 (`index-ensure`) | 2 (`index-ensure`, `seed`) | +1 |
| **Total lifecycle-executing handlers** | 51 | **51** (18 + 33) | **0** — every handler still fires exactly once |
| Shutdown handlers (qualname + bytecode) | 1 | 1 | byte-equal (lineno shifts by +Platform-Status route; bytecode unchanged) ✅ |
| Endpoint `qualname` drift on shared 1,440 routes | 0 | 0 | 0 ✅ |
| Endpoint `dependency_chain` drift on shared 1,440 routes | 0 | 0 | 0 ✅ |
| 5 locked bytecode fingerprints | match | match | 0 ✅ |
| 7 seed bytecode fingerprints | preserved | preserved | 0 ✅ |

## Execution order (post-22.1F)

```
uvicorn imports server
    ├── Startup consistency guard  (module import · L44–65 · sys.exit(98) on env mismatch)
    ├── Mongo client bound         (module import · L69–71)
    ├── FastAPI(lifespan=...)      (module import · L73–84)
    ├── Resend SDK safety patch    (module import · L116–152)
    ├── _verify_env_db_alignment() (module import · L1214)
    ├── 18 @register_lifecycle_step(...) decorators fire → LIFECYCLE_STEPS[0..17]
    │       · [0..10]  group="index-ensure"  (Track 22.1E)
    │       · [11..17] group="seed"          (Track 22.1F)
    ├── 33 @app.on_event("startup")  decorators fire → app.router.on_startup[0..32]
    └── 1  @app.on_event("shutdown") decorator fires → app.router.on_shutdown[0]

uvicorn invokes orchestrated_lifespan(app)
    ↓
[track-22.1e] lifespan.startup: executing 18 LIFECYCLE_STEPS
[track-22.1e] lifespan.startup: LIFECYCLE_STEPS complete
    ↓
[track-22.1d] lifespan.startup: executing 33 handlers
[iter453.6] startup-readiness gate FLIPPED
[track-22.1d] lifespan.startup: complete
    ↓
yield (application serves requests)
```

## Duplicate / missing execution proof

- **No duplicate execution:** each of the 7 migrated seeds appears in `LIFECYCLE_STEPS` exactly once and is NOT present in `app.router.on_startup`. Verified by `test_on_startup_no_longer_contains_migrated_seeds` + `test_lifecycle_steps_contains_7_seed_handlers` (exact-order assertion).
- **No missing execution:** total lifecycle callables remain **51** (18 + 33). Boot log confirms the count in both stages.
- **Order preserved:** the 7 seeds are registered in source order (the same order they had inside the pre-22.1F on_startup list). They now execute after the 11 index-ensure handlers — see `TRACK_22_1F_SEED_DEPENDENCY_PROOF.md` for why this is a strict improvement.

## Boot log evidence (2026-07-04 18:11 UTC)

```
[Track 21.2] EMAIL_SAFETY_MODE=strict — Resend SDK patched. No live email can leave this pod.
lib.lifespan_bootstrap - INFO - [track-22.1e] lifespan.startup: executing 18 LIFECYCLE_STEPS
lib.lifespan_bootstrap - INFO - [track-22.1e] lifespan.startup: LIFECYCLE_STEPS complete
lib.lifespan_bootstrap - INFO - [track-22.1d] lifespan.startup: executing 33 handlers
server            - INFO - [iter453.6] startup-readiness gate FLIPPED · public writes now accepted
lib.lifespan_bootstrap - INFO - [track-22.1d] lifespan.startup: complete
INFO:     Application startup complete.
```

## Verdict

🟢 **SEED PARITY CERTIFIED.** All 7 seeds migrated cleanly; every function body byte-identical; execution order preserved-or-strengthened.
