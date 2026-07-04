# TRACK 22.1 · Runtime Enumeration Snapshot

## Snapshot files

| Stage | Path | Size (bytes) |
|---|---|---|
| Baseline (before extraction) | `memory/track_22_1/RUNTIME_ENUMERATION_before.json` | see filesystem |
| Post-extraction | `memory/track_22_1/RUNTIME_ENUMERATION_after.json` | see filesystem |

Both are produced by `backend/tests/track_22_1/enumerate_runtime.py`, deterministically sorted, and safe to `diff`.

## Counts (matches Endpoint Parity Report)

| Object | Count |
|---|---|
| Routes | **1,440** |
| Method entries | **1,444** |
| OpenAPI paths | **1,263** |
| Middleware | **7** |
| Startup handlers | **51** |
| Shutdown handlers | **1** |
| Exception handlers | **3** |

## Middleware chain (in order)

Captured via `app.user_middleware`. Both before and after snapshots list the same 7 middleware classes with the same option keys, in the same order. Order is critical: session-timeout is installed early, CORS is installed after routers register but before rate-limit dependencies wire, exception handlers apply globally. **No changes this track.**

## Startup handlers (in registration order)

51 handlers registered via `@app.on_event("startup")`. All 51 qualnames are byte-identical between the two snapshots. This includes:

- Scheduler bootstrap chain (backup, digest, verification, health, Trust Spine)
- Sentry init hook (defers until startup so the `_SOURCE_HASH` release identifier is available)
- Session timeout index bootstrap
- Admin hardening index bootstrap
- Application readiness flag flip (`app.state.ready = True`)

**Zero re-ordering.** The extraction touches no startup handler.

## Shutdown handlers

1 handler in both snapshots. Identical.

## Exception handlers

3 handlers in both snapshots. Identical.

## Dependency-chain totals

Every route's `Depends(...)` closure was walked to a full list of callable qualnames and sorted. Across 1,440 routes:

- **0 dependency-chain diffs** between before and after.

This is the strongest single parity signal: it proves that not only did the same handlers register, but every `Depends(rate_limit_public_post)`, `Depends(require_admin_dep)`, and `Depends(_actor_dep)` resolves to the same callable object identity as before. The re-import of `rate_limit_public_post` from `lib.rate_limiting` into `server` under an identical binding name is what preserves this equality.

## Portal-token / auth-gate parity

Every endpoint that carries a portal-token gate (`X-Admin-Token`, `X-Portal-Token`, JWT bearer) is present with the same `dependency_chain` before and after. Full detail in `TRACK_22_1_AUTH_PARITY.md`.

## Route class distribution

All routes are `APIRoute` / `Route` instances as before. No `Mount`, `WebSocketRoute`, or other class was added or removed. Confirmed via the `type` field in both snapshots.

## Reproducibility

The enumeration script is deterministic given the same env vars and same code base. Re-running it on any commit reproduces the corresponding snapshot byte-for-byte (modulo Python object hash randomization for `set()` types, which is why the script sorts everything before serializing).
