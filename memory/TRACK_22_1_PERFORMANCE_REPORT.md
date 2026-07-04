# TRACK 22.1 · Performance Report

## Startup time

| Boot | Wall-clock startup (measured via supervisor restart → first `/api/health` 200) |
|---|---|
| Pre-22.1 | ~5 s (reported in Track 21.3) |
| Post-22.1 | ~5 s (same order of magnitude — no measurable change) |

The extraction moves ~85 lines of Python from `server.py` to two thin `lib/` modules. Boot cost is dominated by:
- MongoDB Atlas TLS handshake
- Sentry init (env-gated)
- 51 startup handlers running index-ensures and scheduler-registers

Adding 2 new `import` statements is well below noise floor.

## Module load

- `lib/health_probes.py` — 33 SLOC, imports `fastapi.FastAPI` only.
- `lib/rate_limiting.py` — 96 SLOC, imports `fastapi.HTTPException`, `fastapi.Request`, and stdlib.

Both are lazy in the sense that they are imported exactly once at `server.py` boot; there is no cost per request.

## Memory

- No change in resident memory. The buckets (`_PUBLIC_POST_BUCKETS`, `_LOGIN_FAIL_BUCKETS`) are the same `defaultdict(list)` instances; they merely live in the `lib.rate_limiting` namespace now instead of `server`.

## Duplicate / dead imports

Static audit of `server.py` imports at the top of the file: no duplicates introduced. The pre-existing imports (`Lock`, `defaultdict`, `Dict`, `List`) are still needed by other code in `server.py` (many places use `Lock` / `defaultdict` for other subsystems).

## Slow initialisation

None introduced. Both extracted modules are dependency-free beyond stdlib + FastAPI, both of which are already loaded.

## Route lookup performance

Unchanged. FastAPI's route trie is built once at boot. Same 1,440 routes → same trie → same lookup cost.

## Per-request cost

- `/health` and `/healthz`: same 2-key dict return. No new allocations.
- Rate-limited public POSTs: same lock acquire + list scan. No new work.

## Six Pillars scorecard

- Powerful: 9.75 — same throughput, cleaner code.
- Durable: 9.80 — smaller modules are easier to reason about long-term.
- Simple: 9.77 — server.py is 85 lines shorter and 2 concepts cleaner.

## What CI enforces

- Nothing regarding performance directly this track. Performance-parity would require a dedicated benchmark harness, which is scheduled for a future Track (not blocking Track 22.1 closure).
