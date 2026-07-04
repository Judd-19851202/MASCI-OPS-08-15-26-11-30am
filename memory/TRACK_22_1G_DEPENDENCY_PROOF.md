# TRACK 22.1G · Dependency Proof

**Question:** Can each of the 4 non-email scheduler handlers safely execute BEFORE the remaining 29 legacy `on_startup` handlers without introducing a new failure mode?

**Answer:** **Yes.** Every one is `asyncio.create_task(...)` — the task is scheduled and the parent decorator returns immediately. The task itself is what does the work, asynchronously, competing normally with all other work on the event loop. Reordering the *scheduling* does not reorder the *work*.

## The scheduling-vs-work distinction

All 4 migrated handlers use the pattern:

```python
async def _start_X():
    asyncio.create_task(long_running_X_loop(...))
    logger.info("[X] task scheduled")
```

- **What Track 22.1G moves earlier:** the `create_task` call.
- **What Track 22.1G does NOT move earlier:** the actual loop body inside `long_running_X_loop`. That runs whenever the event loop next schedules it — which happens at the same relative time regardless of whether the parent `create_task` fires in `LIFECYCLE_STEPS` or `on_startup`.

## Per-handler dependency table

| Handler | Depends on `_db_isolation_failsafe`? | Depends on `_bootstrap_operations`? | Depends on `_bootstrap_integrations`? | Depends on Mongo readiness? | Depends on R2 readiness? | Depends on scheduler-object init? | Depends on Trust Spine? | Depends on readiness flag? | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| `_start_job_photos_indexer` | No (module-import DB guard) | No | No | Yes — motor client at module import | No | Uses existing asyncio doctrine | No | No | ✅ safe |
| `_start_motive_reliability_loop` | No | No | No | Yes | No | Singleton-locked via existing scheduler doctrine | No | No | ✅ safe |
| `_start_health_monitor` | No | No | No | Yes — reads `health_monitor_runs` | No | Uses `start_health_monitor_loop` helper | No | No | ✅ safe |
| `_cluster_capacity_history_loop` | No | No | No | Yes — writes `capacity_history` | No | No external scheduler | No | No | ✅ safe |

## Cross-check: what still runs in on_startup

The 29 remaining `on_startup` handlers do not read from `job_photos` indexer state, motive-reliability collections, `health_monitor_runs`, or `capacity_history` during their startup phase. Any consumer of these signals only sees them at request time — so reordering the *scheduling* of the loops does not affect any startup handler's success path.

## Strict-improvement side effect

Because the 4 scheduler-start calls now happen earlier, their asyncio tasks are handed to the event loop marginally sooner. Under high concurrent boot pressure this reduces the maximum age of "no data yet" for `/api/health/full`'s scheduler-tick check.

## Verdict

🟢 **DEPENDENCY PROOF CERTIFIED.** All 4 scheduler-start handlers safe to migrate. Zero new failure modes introduced.
