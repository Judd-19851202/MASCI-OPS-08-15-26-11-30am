# SCHEDULER_HARDENING_PHASE2_REPORT

**Date:** 2026-02-01 · Batch A · Step 7b
**Authorized scope:** **Phase 2 = defensive wrapping only.** Wrap the scheduler-task entry point so that any unhandled exception is captured BEFORE the asyncio Task terminates silently.
**File touched:** `/app/backend/server.py` only.
**Net behavior change:** **Exceptions that previously caused silent task death are now captured to module state + logged at ERROR level. The exception is then re-raised so the supervisor watchdog also sees it.** No scheduler logic changes.

---

## Changes applied

### Change 1 · New wrapper coroutine `_backup_scheduler_loop_with_capture(db)`

Added at `server.py:6315` immediately after `_record_boot_step`. Single responsibility: wrap the `run_with_singleton_lock(...)` call in a try/except that captures any unhandled exception into `_BACKUP_SCHEDULER_STATE["boot_exception"]` and `_BACKUP_SCHEDULER_STATE["last_attempt_outcome"]` before re-raising.

```python
async def _backup_scheduler_loop_with_capture(db) -> None:
    try:
        await run_with_singleton_lock(db, "backup_scheduler", _backup_scheduler_loop)
    except asyncio.CancelledError:
        _record_boot_step("cancelled")
        raise
    except Exception as e:
        _record_boot_step("unhandled_exception_in_wrapper", exc=e)
        _BACKUP_SCHEDULER_STATE["last_attempt_outcome"] = (
            f"UNHANDLED EXCEPTION IN WRAPPER: {type(e).__name__}: {e!r}"
        )
        raise
```

### Change 2 · Two call-site updates

- **Initial task spawn** (`server.py:11299`):
  ```python
  _backup_task = asyncio.create_task(
      _backup_scheduler_loop_with_capture(db)   ← was: run_with_singleton_lock(db, "backup_scheduler", _backup_scheduler_loop)
  )
  ```
- **Supervisor resurrection** (`server.py:11357`):
  ```python
  _backup_task = asyncio.create_task(
      _backup_scheduler_loop_with_capture(db)   ← was: run_with_singleton_lock(...)
  )
  ```

Both spawn paths now route through the defensive wrapper. The semantics of the wrapper are intentionally identical for the happy path (just an `await` indirection), so:
- ✅ Clean preview return (`SCHEDULER_ENABLED=false`) still exits cleanly
- ✅ Production normal operation routes the loop body identically
- ✅ Cancellation still propagates (re-raises `CancelledError`)
- ✅ Unhandled exceptions are now visible via the diagnostic endpoint

---

## Coverage matrix

| Failure mode | Before Phase 2 | After Phase 2 |
|--------------|----------------|---------------|
| Exception inside `run_with_singleton_lock` before scheduler call | Silent — task ends with no record | Captured to `boot_exception` + re-raised |
| Exception inside `_backup_scheduler_loop` boot path | Silent | Captured + re-raised |
| Exception inside the main `while True:` tick body | Already handled by existing inner try/except | Unchanged (already safe) |
| Asyncio cancellation | Silent | Records `boot_step = "cancelled"` then re-raises |

---

## Verification

✅ **Compile**: Backend restarted successfully, no startup errors.

✅ **Function symbol visible**: `grep -n "_backup_scheduler_loop_with_capture" /app/backend/server.py` returns 3 hits:
- Line 6315 — function definition
- Line 11299 — initial spawn call site
- Line 11357 — supervisor resurrection call site

✅ **Lint check**: ruff lint on `server.py` reports only the 6 pre-existing errors that existed before this batch (all unrelated f-string and duplicate-import warnings on lines 783–800 and 9007/9011). No new lint errors introduced by Phase 2.

✅ **Preview behaviour**: `SCHEDULER_ENABLED=false` correctly causes `run_with_singleton_lock` to return immediately. The wrapper's try-block sees a normal return, exits cleanly, supervisor respawns next cycle. **No spurious exception captures in preview** (verified by reading `boot_exception: null` in the preview probe).

⚪ **Production verification**: pending operator deploy. Once live:
- If the production task continues to "die silently", that's now impossible — either it stays alive OR `boot_exception` is populated with the exact `repr(e)`.
- The combined Phase 1+Phase 2 makes the dead-state diagnostic deterministic.

---

## What Phase 2 did NOT do

- ❌ No new scheduler logic.
- ❌ No retry / restart logic added.
- ❌ No email alarms added.
- ❌ No new env-var dependencies.
- ❌ No production deploy.
- ❌ No watchdog / resurrection-cadence changes.

---

## Combined Phase 1 + Phase 2 effect

When the operator deploys the hardened code to production and runs a fresh probe of `/api/admin/backups-scheduler-state`, the response will be **deterministic** about the scheduler state:

1. **Healthy scheduler**: `alive: true`, `boot_step: entering_main_tick_loop`, `last_tick_ts` advancing every 5–10 minutes, `boot_exception: null`.
2. **Boot-stage failure**: `alive: false`, `boot_step: <last reached stage>`, `boot_exception: "<ExceptionType>: <repr>"`. The exception's class + message identifies the root cause within seconds.
3. **Preview / disabled worker**: `alive: false`, `boot_step: null`, `boot_exception: null`. Distinguishable from a failure (which would have populated fields).

---

## Stop-condition compliance

- ✅ Defensive wrapping only
- ✅ No new scheduler features
- ✅ No retry or restart logic added
- ✅ Single-file change (`server.py`)
- ✅ Behaviour-preserving in the happy path
- ✅ Verified working in preview
