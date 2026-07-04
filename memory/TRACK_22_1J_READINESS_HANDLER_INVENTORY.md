# TRACK 22.1J · Readiness Handler Inventory

## Handler identity
| Field | Value |
|---|---|
| Name | `_iter453_6_flip_ready_flag` |
| Module | `server` |
| File | `backend/server.py` |
| Source line (pre-migration) | 16038 |
| Prior decorator | `@app.on_event("startup")` |
| New decorator | `@register_lifecycle_step("readiness")` |
| Lifecycle group | `readiness` |
| Bytecode SHA-256 | `3ad0b42c02c53519565c03606ae0024b903a6db7c71c42578e406541e89a8fc4` |
| Body change | **None** — decorator swap only |

## Function body (verbatim)
```python
async def _iter453_6_flip_ready_flag():
    """Final startup hook — flip the readiness gate AFTER all other
    @app.on_event('startup') handlers have completed. FastAPI runs
    startup events in registration order, and this module-level
    registration is the LAST one in server.py, so by the time this
    runs every index/scheduler/router setup above is finished.
    """
    app.state.ready = True
    logging.getLogger(__name__).info(
        "[iter453.6] startup-readiness gate FLIPPED · public writes now accepted",
    )
```

## Side-effect inventory
| Aspect | Value |
|---|---|
| Mongo writes | ❌ |
| R2 writes | ❌ |
| Email dispatch | ❌ |
| Trust Spine writes | ❌ |
| External HTTP | ❌ |
| Scheduler task creation | ❌ |
| In-memory state mutation | `app.state.ready = True` |
| Log line | `[iter453.6] startup-readiness gate FLIPPED · public writes now accepted` |

## Health/readiness contract
- Readiness endpoints and health checks that consult `app.state.ready` continue to see identical semantics — flip happens once, at boot, in the final phase, and stays True for process lifetime.

## Ordering contract
| Constraint | Enforced by |
|---|---|
| Runs AFTER every LIFECYCLE_STEP with group≠readiness | `orchestrated_lifespan` phase-1 |
| Runs AFTER every `app.router.on_startup` handler (incl. `command_center._startup`) | `orchestrated_lifespan` phase-2 → phase-3 |
| Runs EXACTLY ONCE | Single registration in `LIFECYCLE_STEPS` + no legacy decorator |
| No future group may accidentally run after readiness | Any new group is non-readiness by default; only `group="readiness"` is placed in phase-3 |

## Idempotency
`app.state.ready = True` is trivially idempotent (identity op after first set).

## Safe-to-migrate = TRUE
1. Body byte-identical (decorator swap only).
2. Orchestrator extended in the same commit to preserve readiness-last.
3. Lock test explicitly asserts phase-3 position and the ordering invariant.
4. Boot log unchanged.
