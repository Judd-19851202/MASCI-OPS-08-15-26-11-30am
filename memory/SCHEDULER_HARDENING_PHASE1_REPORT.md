# SCHEDULER_HARDENING_PHASE1_REPORT

**Date:** 2026-02-01 · Batch A · Step 7a
**Authorized scope:** **Phase 1 = instrumentation only.** Add boot-step tracing so the dead-state can be diagnosed without triggering a backup.
**File touched:** `/app/backend/server.py` only.
**Net behavior change:** **None.** Pure observability layer.

---

## Changes applied

### Change 1 · Extended `_BACKUP_SCHEDULER_STATE` dict

Added three new keys to the module-scope state dict at `server.py:6249`:

```python
"boot_step": None,
"boot_step_ts": None,
"boot_exception": None,
```

These appear automatically in the `GET /api/admin/backups-scheduler-state` response because the endpoint passes the whole dict through at line 7087 (`state = dict(_BACKUP_SCHEDULER_STATE)`).

### Change 2 · New helper `_record_boot_step(step, *, exc=None)`

Added at `server.py:6270`. Single responsibility: write the current boot stage + timestamp into module state AND emit a structured log line (INFO on normal step, ERROR on exception). No behaviour change; pure trace.

### Change 3 · Instrumented `_backup_scheduler_loop` boot path

Added `_record_boot_step(...)` calls at the following 7 stages inside `_backup_scheduler_loop`:

| Stage | When | Why it matters |
|-------|------|----------------|
| `entered_loop_body` | First line of the loop function body | Proves the lock-acquirer returned and the scheduler coroutine actually started |
| `armed` | After `_BACKUP_SCHEDULER_STATE["armed_at"] = now.isoformat()` | Confirms the module state is being written and visible |
| `disk_staleness_read` | After `hours_stale = _hours_since_last_backup()` | Confirms the local filesystem read succeeded |
| `mongo_heartbeat_started` | Inside the existing try-block, before `db.backup_health.find_one(...)` | Detects whether a Mongo connection blip during the boot heartbeat is the silent killer |
| `mongo_heartbeat_done` | After the heartbeat block completes successfully | Confirms the boot heartbeat finished |
| `mongo_heartbeat_exception` | In the `except` branch of the heartbeat block | Records the exception's `repr` for forensics |
| `r2_seed_started` / `r2_seed_done` / `r2_seed_exception` | Same pattern around the R2 state seed query | Same diagnostic value |
| `entering_main_tick_loop` | Just before `await asyncio.sleep(30)` precedes the `while True:` tick loop | Confirms boot completed and the main loop is about to start |

Once this lands in production, the next probe of `/api/admin/backups-scheduler-state` will show `boot_step` populated with the last-reached stage. The "silent task death" mystery becomes a 1-line diagnostic.

---

## Files diff summary

- `/app/backend/server.py` — three insertions:
  - Lines ~6249–6263: state dict extended with 3 new keys (4-line change)
  - Lines ~6266–6313: new `_record_boot_step` helper function (~45 lines)
  - Lines ~6362–6479 (approx): 8 `_record_boot_step(...)` call insertions threaded through the existing boot path

**Total addition:** ~60 lines of pure-observability code, no behaviour change to scheduler logic.

---

## Verification

✅ **Compile**: Backend restarted successfully (`sudo supervisorctl restart backend`), no startup errors.

✅ **Endpoint shape**: `GET /api/admin/backups-scheduler-state` against preview returns the new fields:
```json
{
  "scheduler": {
    "alive": false,
    "armed_at": null,
    "boot_step": null,             ← NEW (correctly null in preview — scheduler doesn't run here)
    "boot_step_ts": null,          ← NEW
    "boot_exception": null,        ← NEW
    ...
  }
}
```

✅ **Preview correctly skips the loop body**: `SCHEDULER_ENABLED=false` causes `run_with_singleton_lock` to return BEFORE `_backup_scheduler_loop` is called → `boot_step` remains `None`, which is the correct signal that "the scheduler is intentionally disabled here, no boot was attempted."

⚪ **Production verification**: pending operator authorization to deploy the new code to production. Once deployed:
- If the scheduler is healthy, `boot_step` will advance through all 7 stages and remain at `entering_main_tick_loop` (with `last_tick_ts` advancing on each tick).
- If the scheduler dies during boot, `boot_step` will lock at whichever stage was last reached → operator can read the exact failure point from a single API call.

---

## What Phase 1 did NOT do

- ❌ No defensive wrapping (that is Phase 2 — separate report).
- ❌ No scheduler logic changes.
- ❌ No env-var changes.
- ❌ No watchdog alarm changes.
- ❌ No production deploy.

---

## Stop-condition compliance

- ✅ Instrumentation only
- ✅ No scheduler hardening beyond observability
- ✅ No backup pipeline changes
- ✅ Single-file change (`server.py`)
- ✅ Read-only effect (state observability + log output)
- ✅ Verified working in preview
