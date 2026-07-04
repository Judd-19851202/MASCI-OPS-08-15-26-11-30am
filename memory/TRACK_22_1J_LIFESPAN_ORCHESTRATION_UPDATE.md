# TRACK 22.1J · Lifespan Orchestration Update

## Why the orchestrator was updated
Pre-22.1J execution order in `orchestrated_lifespan`:
```
1. LIFECYCLE_STEPS  (all groups, source order)
2. app.router.on_startup  (remaining legacy decorators)
3. yield
4. app.router.on_shutdown
```
Naively adding `@register_lifecycle_step("readiness")` to `_iter453_6_flip_ready_flag` would have placed readiness inside step 1 — **before** the still-legacy `command_center._startup`. That violates the readiness-last invariant.

## Post-22.1J execution order
```
phase-1  ▼  LIFECYCLE_STEPS where group != "readiness"        (48 handlers)
phase-2  ▼  app.router.on_startup                              (1 legacy handler)
phase-3  ▼  LIFECYCLE_STEPS where group == "readiness"         (1 handler)  ← LAST
yield
phase-5  ▼  app.router.on_shutdown                             (1 handler)
```

## Code change
`backend/lib/lifespan_bootstrap.py::orchestrated_lifespan` extended with:
```python
non_readiness_steps = [s for s in LIFECYCLE_STEPS if s.group != "readiness"]
readiness_steps     = [s for s in LIFECYCLE_STEPS if s.group == "readiness"]
# phase-1: iterate non_readiness_steps
# phase-2: iterate app.router.on_startup (unchanged)
# phase-3: iterate readiness_steps  ← new
```
Exception handling in phase-3 uses the same re-raise semantics as phase-1 and phase-2, preserving Uvicorn boot-failure semantics.

## Boot-log delta
| Log line | Emitted where |
|---|---|
| `[track-22.1e] lifespan.startup: executing 48 LIFECYCLE_STEPS (non-readiness)` | before phase-1 |
| `[track-22.1e] lifespan.startup: LIFECYCLE_STEPS (non-readiness) complete` | after phase-1 |
| `[track-22.1d] lifespan.startup: executing 1 handlers` | before phase-2 |
| `[track-22.1d] lifespan.startup: complete` | after phase-2 |
| `[track-22.1j] lifespan.startup: executing 1 readiness LIFECYCLE_STEPS (final phase)` | before phase-3 |
| `[iter453.6] startup-readiness gate FLIPPED · public writes now accepted` | during phase-3 (handler body) |
| `[track-22.1j] lifespan.startup: readiness phase complete` | after phase-3 |

## Guarantees
- 🟢 No handler is executed twice.
- 🟢 No handler is skipped.
- 🟢 `_iter453_6_flip_ready_flag` runs LAST.
- 🟢 If phase-1 or phase-2 raises, phase-3 does NOT run — readiness stays False and Uvicorn treats it as a boot failure (identical semantics to pre-22.1J behavior when the readiness handler followed a raising legacy handler in source order).
- 🟢 Shutdown handlers still run on shutdown.

## Rollback (single-file, 4-line)
Revert `orchestrated_lifespan` to iterate `LIFECYCLE_STEPS` in full source-order, then legacy `on_startup`. Flip decorator on `_iter453_6_flip_ready_flag` back to `@app.on_event("startup")`. Total diff ≈ 40 lines.
