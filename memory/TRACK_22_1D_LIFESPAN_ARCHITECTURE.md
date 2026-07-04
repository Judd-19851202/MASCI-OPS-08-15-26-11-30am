# TRACK 22.1D · Lifespan Architecture

## Post-22.1D boot flow

```
uvicorn server:app
    ↓
import server                                        (module import)
    ├── SDK safety patch (server.py L~105-142)        ← unchanged, first Resend interaction
    ├── FastAPI(title=..., lifespan=orchestrated_lifespan)   ← Track 22.1D wiring
    ├── 51 @app.on_event("startup") decorators fire  ← register into app.router.on_startup
    ├── 1 @app.on_event("shutdown") decorator fires   ← register into app.router.on_shutdown
    └── includes all routers, middleware, CORS
    ↓
uvicorn invokes app.router.lifespan_context(app)
    ↓
lib.lifespan_bootstrap.orchestrated_lifespan(app):
    ├── STARTUP PHASE
    │     for i, fn in enumerate(app.router.on_startup):
    │         await fn()                              ← same handlers, same order
    │     log "[track-22.1d] lifespan.startup: complete"
    ↓
    yield                                             (application serves requests)
    ↓
    ├── SHUTDOWN PHASE
    │     for i, fn in enumerate(app.router.on_shutdown):
    │         await fn()                              ← same handlers, same order
    │     log "[track-22.1d] lifespan.shutdown: complete"
```

Byte-identical to Starlette's default lifespan dispatch, but now:

- The orchestration point is a single named module (`lib/lifespan_bootstrap.py`).
- Boot / shutdown emit structured log markers usable by ops runbooks.
- Individual handler exceptions are logged with their qualname before re-raising (preserving Uvicorn's boot-failure semantics).
- Future tracks can migrate individual handlers into an explicit `LIFECYCLE_STEPS` registry inside this module, one per track, with bytecode-fingerprint proof each time.

## Module boundaries

```
backend/
├── server.py                (16,039 lines · was 16,028 · +11 for lifespan= arg only)
│   ├── L73 FastAPI(..., lifespan=create_lifespan())    ← Track 22.1D
│   ├── L~105 Resend SDK patch                          ← unchanged
│   ├── 51 @app.on_event("startup") decorators          ← unchanged
│   └── 1 @app.on_event("shutdown") decorator           ← unchanged
│
└── lib/
    ├── lifespan_bootstrap.py    (**NEW · Track 22.1D**)
    │   ├── orchestrated_lifespan(app)  · asynccontextmanager
    │   └── create_lifespan()   · factory
    ├── scheduler_bootstrap.py   (Track 22.1C)
    ├── email_dispatch.py        (Track 22.1B)
    ├── health_probes.py         (Track 22.1)
    ├── rate_limiting.py         (Track 22.1)
    └── ...
```

## Six Pillars

- Durable 9.87 — foundation for all future backend modularization.
- Operational 9.86 — clean startup / shutdown log markers.
- Trusted 9.97 — bytecode fingerprints preserved on 5 safety-critical bodies.
