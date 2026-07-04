# TRACK 22.1C · Startup-Order Parity Report

## Method

Two JSON snapshots produced by `backend/tests/track_22_1/enumerate_runtime.py`:

- `memory/track_22_1b/RUNTIME_ENUMERATION_after.json` — Track 22.1B close (baseline for 22.1C).
- `memory/track_22_1c/RUNTIME_ENUMERATION_baseline.json` — captured after Track 22.1C additions (before writing any deliverable text; regenerated after the fingerprint/utility work).

Both files list `startup_handlers` and `shutdown_handlers` in registration order, by qualname.

## Result

| Metric | 22.1B after | 22.1C baseline | Delta |
|---|---|---|---|
| Startup handler count | 51 | 51 | **0** |
| Shutdown handler count | 1 | 1 | **0** |
| Startup handler qualname list | (full list) | (full list) | **byte-equal** |
| Shutdown handler qualname list | (full list) | (full list) | **byte-equal** |
| Middleware chain | 7 items | 7 items | **byte-equal (same order, same option keys)** |
| Route count | 1,440 | 1,440 | **0** |
| Method count | 1,444 | 1,444 | **0** |
| OpenAPI paths | 1,263 | 1,263 | **0** |
| `(path, methods)` tuple set | equal | equal | **0** |
| `endpoint_qualname` per route | equal for all 1,440 | equal | **0 moves** |
| `dependency_chain` per route | equal for all 1,440 | equal | **0 drift** |
| Exception handlers | 3 | 3 | **0** |

## Verdict

🟢 **ZERO STARTUP-ORDER DRIFT.** Every one of the 51 startup handlers registered by server.py is at the same registration index with the same qualname. No `@app.on_event` was touched.

## Enforcement

The Track 22.1C lock test `test_runtime_enum_matches_22_1b_close` performs a byte-equal comparison of the two runtime enumeration JSON snapshots. Any change that adds, removes, re-orders, or renames a startup handler fails this assertion.

## Enforcement complement — fingerprint lock

For the 4 email-capable + 1 dispatcher (5 total) locked handlers, the SHA-256 bytecode fingerprint provides a second layer of protection: even if a handler stays in the same registration position, an edit to its *body* changes its `co_code` hash and fails `test_all_locked_handlers_match_live_bytecode`.

Together the two enforcements guarantee: **no scheduler-safety-critical function can be renamed, re-ordered, or edited in body without a corresponding intentional lock-file update in the same commit.**
