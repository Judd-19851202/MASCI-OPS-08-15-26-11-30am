# TRACK 22.1L · Command Center Startup Inventory

## Pre-migration state
| Field | Value |
|---|---|
| Location | `backend/routes/command_center.py` L966 |
| Registration | `@router.on_event("startup")` on the APIRouter returned by `build_command_center_router(db, require_admin_strict_dep)` |
| Discovery in app | FastAPI's `include_router(...)` moves router `on_startup` handlers into `app.router.on_startup` at include time (`server.py` L11089–11092) |
| Type | **Closure** — captures `db` (freevar) |
| Bytecode SHA-256 (pre) | `9e1a377eddcdb931171303be1d0eaaf22bfd92d788affa6a71e658733176ad4e` |
| Body | `try: await _seed_defaults(db) except Exception: pass` |

## Call graph
```
build_command_center_router._startup()
  ↓
_seed_defaults(db)     # backend/routes/command_center.py L948
  ├─ db.command_center_thresholds.find_one({"_id": ...})
  ├─ db.command_center_thresholds.insert_one(DEFAULT_THRESHOLDS)   # only if missing
  ├─ db.command_center_calendar.find_one({"_id": ...})
  └─ db.command_center_calendar.insert_one(DEFAULT_CALENDAR)        # only if missing
```

## Side-effect classification
| Aspect | Value |
|---|---|
| Mongo writes | 2 idempotent upserts (thresholds, calendar) guarded by `find_one({_id})` presence |
| R2 writes | ❌ |
| Email dispatch | ❌ |
| External HTTP | ❌ |
| Scheduler task creation | ❌ |
| Trust Spine writes | ❌ |
| Auth impact | ❌ (module-level function, no dep injection at seed time) |
| Websocket interaction | ❌ |

## Dependency graph
| Dependency | Required at boot? |
|---|---|
| Mongo connectivity | ✅ Lazy-satisfied by motor client (available at import time) |
| Index-ensure group | ❌ (uses simple `_id` PK lookups) |
| Seed group | ❌ |
| Scheduler groups | ❌ |
| Email-scheduler group | ❌ |
| Misc-bootstrap group | ❌ |
| Backup-scheduler group | ❌ |
| Readiness | ❌ (this must run BEFORE readiness) |
| Any legacy `app.router.on_startup` handler | ❌ (there were none other than readiness pre-22.1L) |

## Post-migration state
| Field | Value |
|---|---|
| Location | `backend/server.py` (immediately before `_iter453_6_flip_ready_flag`) |
| Registration | `@register_lifecycle_step("command-center")` |
| Type | Top-level async function; imports `_seed_defaults` lazily inside try-block for zero import-order risk |
| Bytecode SHA-256 (post) | `b2976f4460227c5402564de80fe32ee1d588f9f185ebd7ba97a39277989743cf` (locked in INDEX.json) |
| Body | Semantically identical — same try/except around `_seed_defaults(db)` with silent-on-error semantics |
| Router `_startup` decorator | **REMOVED** — factory now returns the router with no `on_startup` hooks |
| `app.router.on_startup` after include | Empty (100% migrated) |

## Ordering guarantee
Registration happens at `server.py` module import time, at a source line AFTER `_start_backup_scheduler` (L15652) and BEFORE `_iter453_6_flip_ready_flag` (readiness, phase-3). This places `_command_center_seed_defaults` at position 49 in `LIFECYCLE_STEPS` (0-indexed) — the LAST non-readiness step in registration order.

## Idempotency
- The pre-migration closure and the post-migration handler both call the same module-level `_seed_defaults(db)` helper.
- `_seed_defaults` is idempotent (presence-guarded inserts).
- Silent-on-error semantics preserved (`try/except Exception: pass`) — never blocks boot.

## Safe-to-migrate = TRUE
All conditions satisfied. Migration is a two-file surgical change with zero behavior drift.
