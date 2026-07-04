# TRACK 22.1E · Lifecycle Step Pattern

## The pattern

```python
# backend/lib/lifespan_bootstrap.py
@dataclass
class LifecycleStep:
    group: str           # e.g. "index-ensure", "seed", "scheduler", "readiness"
    name: str            # canonical handler name
    fn: Callable         # async or sync callable
    source_module: str

LIFECYCLE_STEPS: List[LifecycleStep] = []

def register_lifecycle_step(group: str, name: str | None = None):
    def _wrap(fn):
        LIFECYCLE_STEPS.append(LifecycleStep(group, name or fn.__name__, fn, fn.__module__))
        return fn
    return _wrap
```

## Migration signature (before/after)

**Before (legacy):**
```python
@app.on_event("startup")
async def _fleet_ensure_indexes():
    # ... body ...
```

**After (Track 22.1E pattern):**
```python
@register_lifecycle_step("index-ensure")
async def _fleet_ensure_indexes():
    # ... byte-identical body ...
```

**Diff:** one decorator line. Function body byte-identical. Bytecode SHA-256 unchanged.

## Execution semantics

The lifespan orchestrator (`orchestrated_lifespan` in `lib/lifespan_bootstrap.py`) runs:

1. **LIFECYCLE_STEPS first** — in registration (source) order, with per-step exception logging.
2. **`app.router.on_startup` second** — remaining legacy decorators, in registration order.
3. **yield** (application serves requests).
4. **`app.router.on_shutdown`** — legacy shutdown decorators.

## Future migration cost

For each handler migrated by a future track (22.1F-K):
- 1 line diff in `server.py` (`@app.on_event("startup")` → `@register_lifecycle_step(...)`).
- 1 lock-test assertion (handler is in LIFECYCLE_STEPS, not on_startup).
- 1 line in the executive summary migration table.

**Total per-handler migration cost: ~3 lines.** Fully rollback-safe.

## Extensibility

Future groups are ready to use:
- `"seed"` — Track 22.1F
- `"scheduler"` — Track 22.1G
- `"email-scheduler"` — Track 22.1H (fingerprint-locked)
- `"bootstrap"` — Track 22.1I
- `"readiness"` — Track 22.1J
- `"shutdown"` — Track 22.1K

No infrastructure changes needed. The `group` field is a free-form string tag for observability.
