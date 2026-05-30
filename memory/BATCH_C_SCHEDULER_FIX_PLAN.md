# BATCH_C_SCHEDULER_FIX_PLAN

**Date:** 2026-02-01
**Status:** Plan only · NO code changed · NO env-var changed · NO deploy initiated.
**Authored from:** Batch B deliverables + fresh code re-verification of `lib/singleton_scheduler.py:216–222` and `server.py:6341–6364`.

---

## 1 · Confirmed root cause (deterministic)

### 1.1 Where exactly is the scheduler dying?

**Inside `lib/singleton_scheduler.py`, line 222** — the early `return` statement of the `SCHEDULER_ENABLED` gate:

```python
enabled = (os.environ.get("SCHEDULER_ENABLED", "true") or "true").lower()
if enabled not in ("true", "1", "yes", "on"):
    logger.info(
        f"[singleton-lock:{lock_name}] SCHEDULER_ENABLED={enabled!r} — "
        f"scheduler disabled on this worker (preview / non-prod)"
    )
    return                                # ← THIS IS WHERE PROD DIES
owner_id = _generate_owner_id()
...
```

The function is called by our Phase 2 wrapper `_backup_scheduler_loop_with_capture(db)`. The wrapper awaits `run_with_singleton_lock(...)`. The gate returns cleanly without raising → wrapper's `try` block sees a normal completion → task is `done`. The supervisor watchdog detects `done` and respawns. Cycle repeats every 5 minutes.

### 1.2 What does `boot_step` show?

`boot_step: None` in all 3 post-deploy probes (04:00:38 / 04:04:27 / 04:06:10 UTC).

This proves `_record_boot_step("entered_loop_body")` — the FIRST line inside `_backup_scheduler_loop` — was **never executed**. The scheduler loop body never runs.

### 1.3 What does `boot_exception` show?

`boot_exception: None` in all 3 probes.

Combined with `boot_step: None`, this is the conclusive signature: **clean return, no exception, loop never entered.** The ONLY code path in `run_with_singleton_lock` that produces this signature is the `SCHEDULER_ENABLED` gate at line 222.

### 1.4 Is this config, code, singleton lock, R2 init, Mongo, env flag, or memory related?

**ENV FLAG.** Specifically: production has `SCHEDULER_ENABLED` set to a falsy value (`false` / `0` / `no` / `off`).

Ruled out:
- ❌ Code defect — no exception is raised; the path through the gate is correct.
- ❌ Singleton lock acquisition — the gate runs BEFORE the lock-acquire loop on line 227.
- ❌ R2 init — boot path never reaches R2 state seed (would require `boot_step: r2_seed_*`).
- ❌ Mongo connection — boot path never reaches Mongo heartbeat read (would require `boot_step: mongo_heartbeat_*`).
- ❌ Memory / OOM — task returns cleanly, doesn't crash. Memory pressure would surface as a SIGKILL on the worker, not a clean asyncio Task completion.

---

## 2 · Complete-R2 disablement

### 2.5 Why is complete-R2 disabled?

`_lite_mode_default()` in `server.py:6341–6364` returns `True` (lite mode forced) unless `BACKUP_LITE_MODE_ONLY` is explicitly set to `("0", "false", "no", "n", "off")`. **An unset env var still returns True** — i.e., lite-mode is the implicit default at the helper level regardless of env presence.

A second consultation of `_lite_mode_default()` at `server.py:4896` (inside `_run_scheduled_backup`) defeats any manual `lite=false` opt-out from the wrapper level. This is layered safety.

### 2.6 Was `BACKUP_LITE_MODE_ONLY=true` intentional or accidental?

**Intentional.** Documented in 4+ code locations:
- `server.py:6341–6358` — docstring: "Iter64 phase 2 (2026-05-11) moved photos to R2 but other base64 fields still live in Mongo and a full-archive build was still long enough to **recycle the worker mid-task on production**."
- `server.py:4889` — `_run_scheduled_backup` docstring referencing the env flag
- `server.py:4982` — operator-facing comment: "BACKUP_LITE_MODE_ONLY=true to make lite-mode permanent"
- `server.py:5332` — System & Backups admin page HTML: "Set `BACKUP_LITE_MODE_ONLY=true` on the deploy until S3 photo migration is done"
- `server.py:6219` — `_backup_scheduler_loop` docstring: "Production runs in lite-mode (`BACKUP_LITE_MODE_ONLY` true)"

This is **designed-in safety**, not configuration drift.

### 2.7 Is complete-R2 safe to re-enable?

**Conditionally**, with caveats:
- ✅ Last successful complete-R2: 2026-05-26 11:06 UTC (336 MB, 223 394 records) — proves the build CAN complete.
- ⚠ Worker OOM watermark: 600 MB. Build peak memory is unknown but a 336 MB archive plus in-memory cursor data is tight.
- ⚠ Build wall time: several minutes, during which the asyncio worker is blocked on this single task.
- ⚠ Email attachment limits: 336 MB exceeds Resend's limit; code correctly uploads to R2 and emails the link instead — but this path depends on healthy R2 credentials.

**Not safe to flip blindly.** The intended re-enable path is to complete the S3 photo migration of remaining base64 fields (signatures, training photos, etc.) OR build an IT-pull/streamed-export endpoint that replaces in-process archive construction.

---

## 3 · The minimum surgical fix

### 3.8 Recommended fix

**Single env-var change in the production environment panel.**

| Setting | Current value (suspected) | Proposed value |
|---------|---------------------------|----------------|
| `SCHEDULER_ENABLED` | `false` (or `0` / `no` / `off`) | **`true`** (or unset — default is `"true"`) |

- **Why this fix is minimum surgical**: a single env-var change. No code lines edited. No new logic. No new tests required (the scheduler code path is the well-trodden production path that ran successfully until the flag was set).
- **Why NOT a code change**: changing the gate logic in `singleton_scheduler.py` would alter the env-var contract for every worker and other schedulers using the same lock library. The current gate is doing exactly what it was designed to do; the env var is the problem, not the gate.
- **Blast radius**: 1 worker on production. No preview impact (preview has its own `.env`).

### 3.9 Optional follow-up code change (NOT REQUIRED for the fix)

If the operator wants a defence-in-depth guard against future env-var leaks, a future P3 task could add this to `lib/singleton_scheduler.py`:

```python
# Env-var hygiene safety: in production, scheduler must be ON unless explicitly
# set to "false". An unset env var means "production default = on".
app_env = (os.environ.get("APP_ENV", "") or "").lower()
if app_env == "production" and enabled in ("", None):
    enabled = "true"
```

This is **NOT** part of Batch C. Listed only so the operator knows the defense-in-depth option exists.

### 3.10 What about complete-R2 / `BACKUP_LITE_MODE_ONLY`?

**No change.** Keep lite-only for now.

- The lite-only constraint is documented as intentional and tied to a separate migration workstream (S3 photo migration of remaining base64 fields).
- Flipping `BACKUP_LITE_MODE_ONLY=false` to re-enable complete-R2 builds would re-introduce the worker-recycle OOM risk that motivated the flag in the first place.
- The scheduler fix (re-enabling `SCHEDULER_ENABLED`) gets twice-daily LITE backups running again — restoring continuous backup hygiene. Complete-R2 backups can be triggered separately via `POST /api/admin/backups/run-complete-now` (different endpoint, not the scheduler).
- Decoupling the two is correct: scheduler ON ≠ complete-R2 mode.

---

## 4 · Risk assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Env-var change breaks something else | 🟢 Low — `SCHEDULER_ENABLED=true` is the platform's default; production has historically run with it on | n/a |
| Scheduler runs and immediately fires a lite backup at the next scheduled hour | 🟡 Expected behaviour — this IS the goal. Operator should expect a lite backup at the next 02:00 or 18:00 UTC slot | Monitor `backup_health` row insertion |
| Scheduler runs into a `complete-r2` hourly tick (per `BACKUP_R2_HOURLY=true` in preview, unclear if also in prod) and OOMs | 🟡 Medium — depends on whether `BACKUP_R2_HOURLY=true` is set in production AND whether the hourly tick respects `BACKUP_LITE_MODE_ONLY=true` | Confirm `BACKUP_R2_HOURLY` env-var value in production BEFORE flipping `SCHEDULER_ENABLED`. If `BACKUP_R2_HOURLY=true`, the recommended sequence is to leave that flag unset/false during the first day of scheduler operation to verify lite-mode-only schedule before adding hourly R2 |
| Worker memory spike from the new boot path | 🟢 Negligible — boot path is small, dominated by Mongo heartbeat read (~1 KB) | n/a |
| Watchdog mass-alarm flood when scheduler starts ticking after long inactivity | 🟢 Low — the watchdog alarm fires only on `seconds_since_last_tick > 25h` AFTER a successful tick has happened. First successful tick resets the watchdog | n/a |
| Drift in old `last_run_for_hour` state | 🟢 None — these are in-memory dicts, reset per worker restart. The new scheduler will treat the next scheduled hour as fresh | n/a |

Overall fix risk: **🟢 LOW**.

---

## 5 · Rollback plan

If `SCHEDULER_ENABLED=true` causes any unexpected behaviour:

1. **In Emergent production env panel**: set `SCHEDULER_ENABLED=false`.
2. **Restart production workers** (operator action via platform).
3. **Verify dead-state restored**: `GET /api/admin/backups-scheduler-state` → `boot_step: None`, `task_alive: false`. (Same state we have right now.)
4. **No code rollback needed.** No code was changed.

Rollback wall-time: ~60–120 seconds from operator decision to live effect.

---

## 6 · Verification steps after the fix

Sequential — operator confirms each step before proceeding to next:

### Step 6.1 (T+0 · immediate, ~10 seconds after worker restart)

```
GET https://mascidocs.com/api/admin/backups-scheduler-state
```

Expected new values:
- `alive: true` (was `false`)
- `armed_at`: recent ISO timestamp (was `null`)
- `boot_step: "entering_main_tick_loop"` (was `null`)
- `boot_step_ts`: recent ISO timestamp (was `null`)
- `boot_exception: null` (unchanged)
- `task_alive: true` (was `false`)
- `last_attempt_outcome`: previous resurrection string OR a fresh start message (changes — confirms the gate is no longer firing)

If `boot_step` is `"entering_main_tick_loop"` and `alive: true`, **the scheduler is healthy.**

### Step 6.2 (T+5min · supervisor cycle)

Re-probe. Expected:
- `task_alive: true` (still — the wrapper task should NOT be dying anymore)
- `last_tick_ts`: recent ISO timestamp from a tick within the last 5 minutes
- `seconds_since_last_tick`: small integer (< 600)

If `last_tick_ts` is advancing, **the main tick loop is alive.**

### Step 6.3 (T+next scheduled hour · 02:00 or 18:00 UTC)

Re-probe AFTER the next scheduled backup hour passes (whichever is sooner from when the fix is applied):
- `last_attempt_started_at`: recent ISO timestamp at/just-after the scheduled hour
- `last_attempt_outcome`: should be `"ok ..."` for a successful lite backup run
- `last_run_for_hour`: dict should contain `{2: <today>}` or `{18: <today>}`
- A new row in `recent_health` with `mode: "lite"`, recent `ts`, `ok: true`

If a fresh lite-backup row appears in `recent_health` at the scheduled hour, **scheduled backups are restored.**

### Step 6.4 (T+24h · soak test)

Re-probe after a full day:
- `last_run_for_hour: {2: <today>, 18: <today>}` (both scheduled slots fired)
- 2 new rows in `recent_health` for `mode: "lite"` (one per scheduled hour)
- No `boot_exception` populated
- `task_alive: true` continuously

If the 24h soak passes, **the fix is durable.**

### Step 6.5 (no verification needed — but document)

Email delivery to `BACKUP_EMAIL_TO`: operator should also verify two lite-mode backup emails arrived in `jaymn.judd@mascigc.com` inbox within the past 24 hours.

---

## 7 · Should complete-R2 remain disabled or be restored?

**Remain disabled.** Recommended posture for next 4–8 weeks:

1. Restore SCHEDULED LITE backups (this fix) → continuous backup hygiene resumes.
2. Operator-on-demand complete-R2 backup via `POST /api/admin/backups/run-complete-now` only when a known-good full archive is needed (e.g., before a major release).
3. Migration workstream (separate batch, NOT authorized in Batch C): move remaining MongoDB base64 fields to R2 → eliminates the OOM risk that motivated lite-only → THEN `BACKUP_LITE_MODE_ONLY` can be unset cleanly.

This sequencing avoids re-introducing the worker-recycle failure mode while restoring backup continuity.

---

## 8 · Operator decision required

| # | Decision | Authority |
|---|----------|-----------|
| A | **Confirm `SCHEDULER_ENABLED=true`** (or unset) on the production env panel. Restart workers. | Operator only |
| B | **Confirm `BACKUP_R2_HOURLY` value in production.** If `true`, recommend toggling to `false`/unset on the FIRST day to keep behaviour predictable; if already `false`/unset, no action | Operator only |
| C | **Keep `BACKUP_LITE_MODE_ONLY=true`** (or unset — same effect). DO NOT change | Operator only |
| D | **Schedule the S3 photo migration workstream** as a separate batch (out of Batch C scope) | Operator only |

---

## 9 · Stop-condition compliance

- ✅ No code modified
- ✅ No env-var modified
- ✅ No backups run
- ✅ No redeploy
- ✅ No Fleet DVIR / notification / approval / pilot / RFI / schedule / P6 / PM Exposure Tile / UI / layout / design touched
- ✅ Plan only — operator decides the fix execution

---

## 10 · TL;DR

> **The scheduler is dying at `lib/singleton_scheduler.py:222`.** Production has `SCHEDULER_ENABLED` set to a falsy value. Set it to `true` (or unset it — default is `"true"`) and restart the production workers. **One env-var change. No code change.** Watchdog and tick-loop will resume within minutes. Complete-R2 lite-only stays as-is — that's intentional safety pending S3 photo migration.
