# TRACK 22.1K · Shutdown Architecture

## Registries
Two parallel append-only lists in `backend/lib/lifespan_bootstrap.py`:
```python
LIFECYCLE_STEPS: List[LifecycleStep]     # startup, appended by @register_lifecycle_step(group)
SHUTDOWN_STEPS:  List[LifecycleStep]     # shutdown, appended by @register_shutdown_step(group)
```
Both share the `LifecycleStep` dataclass (group, name, fn, source_module).

## Public API
```python
from lib.lifespan_bootstrap import (
    LIFECYCLE_STEPS,        # startup registry (50 pre-22.1K, 51 post-)
    SHUTDOWN_STEPS,         # shutdown registry (0 pre-22.1K, 1 post-)
    register_lifecycle_step,# decorator for startup handlers
    register_shutdown_step, # decorator for shutdown handlers (new in 22.1K)
    orchestrated_lifespan,  # unified 4-phase lifespan
    create_lifespan,        # factory
)
```

## Shutdown execution
```
▼ yield finishes (application about to exit)

for i, step in enumerate(SHUTDOWN_STEPS):      # phase-4a
    try:
        await _run_callable(step.fn)
    except Exception:
        logger.exception(...)                  # SWALLOW — allow full shutdown
        # continue to next step

for i, fn in enumerate(app.router.on_shutdown):# phase-4b (empty post-22.1K)
    try:
        await _run_callable(fn)
    except Exception:
        logger.exception(...)                  # SWALLOW
```

## Semantic differences vs pre-22.1K
| Aspect | Pre-22.1K | Post-22.1K |
|---|---|---|
| Where handlers live | `app.router.on_shutdown` (Starlette default) | `SHUTDOWN_STEPS` registry |
| Iteration order | Source registration order | Source registration order (unchanged) |
| Exception handling | Logged + swallowed | Logged + swallowed (unchanged) |
| Await semantics | Awaited via Starlette | Awaited via `_run_callable` (same) |
| Observability | Two-line log envelope | Two-line log envelope + explicit `[track-22.1k]` marker |

**Result:** semantic behavior is IDENTICAL. Only the storage location and log-marker text changed.

## Migrated handlers (1)
```
SHUTDOWN_STEPS = [
    LifecycleStep(
        group="shutdown",
        name="shutdown_db_client",
        fn=<async fn>,          # SHA-256 a7db2b01... (byte-identical to pre-22.1K)
        source_module="server",
    ),
]
```
Body (unchanged from pre-migration):
```python
try:
    if _backup_task is not None:
        _backup_task.cancel()
except Exception:
    pass
client.close()
```

## Graceful termination properties
- **Deterministic**: strict source-registration order.
- **Timeout-safe**: no per-step timeout added because the migrated handler is fast (< 100 ms — task cancel + client close). Additional handlers added in future should individually manage their own timeouts if slow.
- **Restart-safe**: `client.close()` is idempotent; `_backup_task.cancel()` is idempotent.
- **Never hangs forever**: uvicorn's own SIGTERM handling still applies; the orchestrator does not add blocking waits beyond `await _run_callable(step.fn)`.
- **Exception-transparent**: exceptions are logged with full stack trace but swallowed, matching Starlette's default `on_shutdown` semantics.

## Future extensibility
New shutdown work goes into `@register_shutdown_step("<group>")` handlers in `server.py` (or any imported module). Ordering: append order. To insert a step earlier, register it earlier in module import order.
