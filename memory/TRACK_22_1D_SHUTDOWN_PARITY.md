# TRACK 22.1D · Shutdown Parity Report

## Method

- **`memory/track_22_1d/SHUTDOWN_ORDER_before.json`** — 1 shutdown handler captured at Track 22.1C close.
- Runtime enumeration `shutdown_handlers` field in both before and after snapshots.

## Result

| Field | Before | After | Delta |
|---|---|---|---|
| Shutdown handler count | 1 | 1 | **0** |
| Handler `qualname` | (unchanged) | (unchanged) | **byte-equal** |
| Handler `name` | (unchanged) | (unchanged) | **byte-equal** |
| Handler `module` | `server` | `server` | **byte-equal** |
| Handler `bytecode_sha256` | (unchanged) | (unchanged) | **byte-equal** |

## Semantics

The single `@app.on_event("shutdown")` handler is called by `lib.lifespan_bootstrap.orchestrated_lifespan` after the `yield` boundary, wrapped in a `try/finally` so it always runs even if the application code raised. Exceptions in the shutdown handler are logged (with qualname) and swallowed — identical to Starlette's default behavior, but with explicit logging so ops can trace shutdown issues.

## Cleanup ordering

Only 1 shutdown handler is registered, so ordering questions are trivial. If future tracks add more shutdown handlers, they will run in registration order (matching startup order semantics).

## Verdict

🟢 **SHUTDOWN PARITY CERTIFIED.** 1 → 1, byte-equal.
