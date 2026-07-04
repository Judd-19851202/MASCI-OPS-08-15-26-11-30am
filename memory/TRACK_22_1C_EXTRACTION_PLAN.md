# TRACK 22.1C · Extraction Plan

## Executive summary

Track 22.1C is an **inventory + bytecode-lock** track. No `@app.on_event` handler was physically relocated. This document captures the honest architectural analysis of why physical relocation is unsafe within the current paradigm, and lists the candidates deferred to future tracks with their required parity gates.

## Why physical relocation of startup handlers was rejected

Every one of the 51 `@app.on_event("startup")` handlers in server.py:

1. Is registered via the `@app.on_event("startup")` decorator at its physical source line.
2. Closes over `app` + arbitrary module-locals from server.py.
3. Executes in FastAPI-registration order, which is source-file top-to-bottom order.

**Consequence:** moving any handler physically to another module either:
- **(a)** Changes registration order — forbidden by the Track 22.1C mandate.
- **(b)** Requires a wrapper `register_startup_handlers(app)` in the extracted module that re-decorates each handler at the same relative position — cosmetically identical but adds indirection with zero user-facing benefit and non-zero risk.
- **(c)** Requires converting to FastAPI lifespan events — explicitly out of scope for Track 22.1C ("Do not migrate to FastAPI lifespan in this track").

Given all three paths are either forbidden or add risk without benefit, **the correct architectural answer is to leave startup handlers where they are and add safety layers around them.** Track 22.1C does exactly that via the SHA-256 fingerprint lock + inventory JSON.

## What Track 22.1C DID move (nothing removed, only additions)

Additions only — zero relocation:

| Item | Location | Purpose |
|---|---|---|
| `backend/lib/scheduler_bootstrap.py` | New module | Houses `verify_locked_bytecode(app)` utility for ops audit |
| `memory/BYTECODE_FINGERPRINTS/INDEX.json` + 5 `.sha256.txt` files | New evidence | Cryptographic locks on 5 email-capable functions |
| `memory/track_22_1c/STARTUP_ORDER_before.json` | New inventory | 51-handler enumeration with side-effect classification |
| `memory/track_22_1c/SCHEDULER_INVENTORY_before.json` | New inventory | Filtered scheduler-side-effect subset |
| `memory/track_22_1c/RUNTIME_ENUMERATION_baseline.json` | New evidence | Byte-equal to Track 22.1B close |
| `backend/tests/track_22_1c/enumerate_lifecycle.py` | Reproducible harness | Anyone can regenerate the inventory |
| `backend/tests/test_track_22_1c_scheduler_bootstrap.py` | Lock test | 17 assertions |

## Deferred candidates (with parity gates)

### Track 22.1c-2 · FastAPI lifespan migration

- **Scope:** Convert all 51 `@app.on_event("startup")` decorators + 1 `@app.on_event("shutdown")` to a single FastAPI `lifespan` context manager.
- **Why deferred:** Explicitly out of scope per user directive ("Do not migrate to FastAPI lifespan in this track").
- **Parity gate:** startup handler count parity + observable behavior parity (`app.state.ready` still flips only after all init runs) + 3-layer email safety envelope survives + full 195/195 lock envelope green post-migration.
- **Risk:** MEDIUM — lifespan semantics differ from decorators in exception handling; requires per-handler review.

### Track 22.1c-3 · Extract self-contained scheduler helpers

- **Scope:** Move helpers like `_backup_scheduler_loop_with_capture`, `_lite_mode_default`, `_record_boot_step` to `lib/scheduler_bootstrap.py` (or a domain-appropriate module).
- **Why deferred:** Each closes over 2-4 module-locals (`_BACKUP_SCHEDULER_STATE`, `logger`, `_backup_scheduler_loop`). Extraction requires either lazy back-imports or dependency injection — both add complexity for ~40 lines of code moved.
- **Parity gate:** JSON runtime enum + backup smoke test in a sandbox.
- **Risk:** LOW-MEDIUM.

### Track 22.1c-4 · Extract seed-user startup handlers

- **Scope:** `_seed_shop_users`, `_seed_hr_users`, `_seed_field_leadership_users`, `_seed_field_leadership_equipment_catalog` are pure Mongo idempotent seeds. Could move to `lib/startup_seeds.py`.
- **Why deferred:** Even though they're side-effect-classified as "index" only (no email), they still close over `db` and their positions matter (early boot). Moving requires a `register_seeds(app, db)` wrapper.
- **Parity gate:** Full startup handler qualname parity except whitelisted moves.
- **Risk:** LOW.

## Deferred candidates NOT to pursue

- **Handler re-ordering to optimize boot latency:** Forbidden by the Zero-Drift mandate. Current order is production-certified.
- **Removing "obsolete" handlers:** Track 21.0 census + Track 22.0 audit already confirmed every startup handler is in use.
- **Consolidating multiple `_ensure_*_indexes` handlers into one:** Each closes over its own domain — merging risks binding a schema change to a wrong domain restart.

## Rollback plan for Track 22.1C

Delete:
- `backend/lib/scheduler_bootstrap.py`
- `memory/BYTECODE_FINGERPRINTS/` (whole directory)
- `memory/track_22_1c/` (whole directory)
- `backend/tests/track_22_1c/`
- `backend/tests/test_track_22_1c_scheduler_bootstrap.py`
- 10 memory MDs
- 3 ledger blocks

**No runtime code was modified this track.** Rollback is a pure delete.

## Zero-Drift verdict

🟢 **CERTIFIED.** Only additive artifacts. Zero handler touched. Zero timing altered.
