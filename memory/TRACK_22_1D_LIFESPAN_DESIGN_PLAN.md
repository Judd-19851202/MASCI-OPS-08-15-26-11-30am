# TRACK 22.1D · Lifespan Design Plan

## Design decision

**Preserve all 51 `@app.on_event("startup")` decorators + 1 `@app.on_event("shutdown")` decorator exactly where they are.** Do NOT rewrite them as explicit `LIFECYCLE_STEPS` entries in this track.

Add a **single custom lifespan callable** to `FastAPI(lifespan=...)` that iterates the existing `app.router.on_startup` / `on_shutdown` lists at boot / shutdown boundaries in preserved registration order.

## Rationale

Rewriting 51 individual handlers into an explicit registry in one track would be a **51-way behavior-change risk**. Each handler closes over server.py module-locals (`db`, `app`, various flags); moving each to a registry entry would require either lazy back-imports (import cycle) or wide dependency-injection factories.

By keeping the decorators in place and adding a lifespan wrapper that calls them in registration order, we achieve:

- **Zero decorator behavior change** — the decorators still register their handlers into `app.router.on_startup` at module import time, in source-file top-to-bottom order.
- **Zero call-site behavior change** — the lifespan callable iterates the exact same list Starlette's default lifespan would have iterated.
- **Zero exception-handling behavior change** — startup exceptions still re-raise (killing Uvicorn boot); shutdown exceptions still log-and-continue.
- **Unblock future modularization** — the lifespan module is now the natural home for a `LIFECYCLE_STEPS` registry that future tracks (22.1e/f/g/...) will populate handler-by-handler.

## Migration table (this track)

| Handler | Current location | New location | Migration | Parity proof |
|---|---|---|---|---|
| All 51 startup handlers | `server.py` `@app.on_event("startup")` | Same physical location | **NONE — still decorators** | JSON snapshot of `app.router.on_startup` byte-equal (qualname/name/module/bytecode_sha256) |
| 1 shutdown handler | `server.py` `@app.on_event("shutdown")` | Same physical location | **NONE — still decorator** | JSON snapshot of `app.router.on_shutdown` byte-equal |
| `FastAPI(...)` constructor | `server.py` L73 | `server.py` L73 (+lifespan= kwarg) | Add 11 lines: `lifespan=create_lifespan()` argument | server.py line diff limited to constructor block |

## Migration table (future tracks — informational only)

| Track | Scope | Migration pattern |
|---|---|---|
| 22.1e | Migrate 10 index-ensure handlers | Move each `_ensure_*_indexes` body into a `LIFECYCLE_STEPS` list; update fingerprints |
| 22.1f | Migrate 4 email-capable digest crons | Preserve safety envelope + bytecode fingerprints |
| 22.1g | Migrate remaining scheduler handlers | Preserve `SCHEDULER_ENABLED` gates |
| 22.1h | Migrate seed handlers (idempotent) | Simpler — no gating |

Each future migration is a **single-handler, single-fingerprint update**. Because the lifespan orchestration layer already exists, no additional infrastructure is required — only per-handler evidence.

## Rollback plan for this track

Delete the `lifespan=` kwarg from `FastAPI(...)` and delete `backend/lib/lifespan_bootstrap.py`. The remaining 51 `@app.on_event` decorators revert to Starlette's default dispatch (identical behavior). No handler was touched — nothing else changes.
