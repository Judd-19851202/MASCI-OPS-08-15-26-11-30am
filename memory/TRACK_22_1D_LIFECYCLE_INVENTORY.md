# TRACK 22.1D · Lifecycle Inventory

## Machine-readable sources
- `memory/track_22_1d/STARTUP_ORDER_before.json` — 51 startup handlers (Track 22.1C baseline).
- `memory/track_22_1d/STARTUP_ORDER_after.json` — 51 startup handlers (Track 22.1D close).
- `memory/track_22_1d/SHUTDOWN_ORDER_before.json` — 1 shutdown handler.
- `memory/track_22_1d/LIFECYCLE_INVENTORY_before.json` / `after.json` — scheduler-side-effect subset.

## Counts (unchanged)

| Category | Before | After |
|---|---|---|
| Startup handlers | **51** | **51** |
| Shutdown handlers | **1** | **1** |
| Scheduler-capable | 16 | 16 |
| Email-capable | 4 | 4 |
| Backup | 3 | 3 |
| Digest | 2 | 2 |
| Index creation | 11 | 11 |
| Mongo write | 2 | 2 |
| R2 storage | 2 | 2 |

Full ordered handler-by-handler list in `TRACK_22_1C_SCHEDULER_INVENTORY.md` (still authoritative — Track 22.1D changed 0 handlers).

## Delta between before and after

The only observed field-level diff between the two snapshots is `lineno` — every handler shifted by +11 because the `FastAPI(..., lifespan=...)` argument added 11 lines above them. All other fields (`qualname`, `name`, `module`, `sourcefile`, `is_coroutine`, `arg_count`, `bytecode_sha256`, `side_effects`, `docstring_first_line`) are byte-identical.

The Track 22.1D lock test `test_startup_handler_count_preserved` explicitly asserts equality of qualname / name / module / bytecode_sha256 while permitting the lineno shift.
