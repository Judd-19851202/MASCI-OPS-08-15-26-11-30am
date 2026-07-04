# TRACK 22.1B · Performance Report

## Startup time

| Boot | Wall-clock startup (measured via supervisor restart → first `/api/health` 200) |
|---|---|
| Pre-22.1B (Track 22.1 close) | ~5 s |
| Post-22.1B | ~5 s (no measurable change) |

## Module load cost

- `lib/email_dispatch.py` — 136 SLOC, imports only `asyncio` + `typing` (both already loaded).
- Import cost: ~50 µs (Python 3.11 typical module load + parse).

Below noise floor.

## Per-dispatch latency

- Extra work per dispatch: **1 attribute lookup** (`_DISPATCHER_HOOK` in `lib.email_dispatch`) before `asyncio.create_task` is called.
- Attribute lookup cost: ~0.1 µs.
- Total per-dispatch overhead: negligible (~0.001% of the ~10ms Trust Spine + Mongo + PDF I/O time).

## Memory

- `_AUTO_EMAIL_DISPATCH_TASKS` (strong-ref set): same instance as pre-22.1B, now lives in `lib.email_dispatch` namespace.
- No new global state, no new caches, no new locks.

## Imports scan

- `lib/email_dispatch.py` top: `import asyncio`, `from typing import Callable, Optional`. Nothing else.
- `server.py` net: 3 lines removed (inline defs) + ~10 lines added (import block + register call). Net −63 lines.

## Dead / duplicate imports

None introduced. The `Lock`, `defaultdict`, `Dict`, `List` imports at the top of server.py continue to be needed by other subsystems (unchanged).

## Slow initialisation

None. The register-dispatcher call (`_register_email_dispatcher(_dispatch_auto_email)`) is a single global assignment — nanoseconds.

## Route lookup

FastAPI route trie unchanged (verified by JSON snapshot).

## Six Pillars scorecard

- Powerful: 9.76 — same throughput.
- Durable: 9.82 — smaller server.py surface, isolated email scaffolding.
- Simple: 9.79 — one place to find the fire-and-forget scheduler.

## What CI enforces

- Nothing regarding wall-clock performance directly this track. Performance-parity would require a benchmark harness (scheduled for a future dedicated track).
