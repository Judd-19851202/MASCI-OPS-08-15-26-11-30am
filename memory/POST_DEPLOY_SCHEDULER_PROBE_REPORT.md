# POST_DEPLOY_SCHEDULER_PROBE_REPORT

**Date:** 2026-02-01 · Batch B · Step 2
**Action:** Post-deploy diagnostic probes of `GET /api/admin/backups-scheduler-state` against production. Captured 3 probes across the first 6 minutes of the new pod's lifetime.

---

## Probe timeline (all UTC)

| Probe | Wall-clock | Pod uptime | Source file |
|-------|-----------|-----------|-------------|
| 1 | 2026-05-30T04:00:38Z | ~29 s | `batch_b_evidence/probe1_scheduler_state.json` |
| 2 | 2026-05-30T04:04:27Z | ~258 s (4.3 min) | `batch_b_evidence/probe2_scheduler_state.json` |
| 3 | 2026-05-30T04:06:10Z | ~361 s (6.0 min) | `batch_b_evidence/probe3_scheduler_state.json` |

---

## Captured state (Probe 1 · canonical)

```
--- New Phase 1+2 hardening fields ---
boot_step                      : None
boot_step_ts                   : None
boot_exception                 : None

--- Lifecycle ---
alive                          : False
armed_at                       : None
last_tick_ts                   : None
last_attempt_outcome           : 'RESURRECTED at 2026-05-30T03:58:09.268897+00:00
                                  (previous: completed without error)'

--- Wrapper / Supervisor ---
task_alive                     : False
seconds_since_last_tick        : None
lite_mode_only_env             : True       ← see COMPLETE_R2_DISABLEMENT_INVESTIGATION.md
watchdog_threshold_hours       : 25.0
scheduled_hours_utc            : [2, 18]
now_utc                        : '2026-05-30T04:00:38.633421+00:00'

--- Manual run state ---
manual_run.outcome             : 'ok · MASCI_lite_backup_2026-05-30_031433Z.zip ·
                                  206 KB · emailed_to=jaymn.judd@mascigc.com'
manual_in_progress             : False
```

---

## Captured state (Probes 2 + 3 · new-pod state)

Probes 2 and 3 hit the freshly-deployed pod (started 2026-05-30T04:00:09Z) before the 5-minute supervisor cycle could update `last_attempt_outcome`. Both show:

```
boot_step                      : None
boot_step_ts                   : None
boot_exception                 : None
alive                          : False
armed_at                       : None
last_attempt_outcome           : None         ← initial state, supervisor not yet cycled
task_alive                     : False
```

---

## Root-cause analysis (DETERMINISTIC)

### Evidence chain

1. **`boot_step: None`** — the very first `_record_boot_step("entered_loop_body")` call inside `_backup_scheduler_loop` was never executed. The loop body never ran.
2. **`boot_exception: None`** — no unhandled exception was captured by the Phase 2 wrapper. The wrapper saw a clean return from `run_with_singleton_lock`.
3. **`task_alive: false`** — the asyncio Task is done.
4. **`last_attempt_outcome` in Probe 1: `"RESURRECTED at ... (previous: completed without error)"`** — supervisor watchdog respawned a task whose previous incarnation **returned cleanly without raising**.

### Tracing `run_with_singleton_lock` to find the clean-return path

`/app/backend/lib/singleton_scheduler.py:185–276` is the function called by our wrapper. **The only clean-return path** in this function is at lines 216–222:

```python
enabled = (os.environ.get("SCHEDULER_ENABLED", "true") or "true").lower()
if enabled not in ("true", "1", "yes", "on"):
    logger.info(
        f"[singleton-lock:{lock_name}] SCHEDULER_ENABLED={enabled!r} — "
        f"scheduler disabled on this worker (preview / non-prod)"
    )
    return                              # ← THE ONLY clean return path
```

All other paths in `run_with_singleton_lock` either:
- Loop forever in the lock-poll `while True:` (line 227),
- Raise `asyncio.CancelledError` (which our wrapper re-raises),
- Or raise an unhandled `Exception` (which our wrapper would capture as `boot_exception`).

Therefore: **production's `SCHEDULER_ENABLED` env var is set to a value NOT in `("true", "1", "yes", "on")`** — most likely set to `false` explicitly.

### Conclusive determination

**Production has `SCHEDULER_ENABLED=false` (or another falsy value like `0` / `no` / `off`).**

This was the cause of:
- 2026-05-29 dead-state diagnostic
- 2026-05-30 03:13:55Z probe (Batch A)
- 2026-05-30 04:00 — 04:06 UTC probes (Batch B post-deploy)

The scheduler has been **disabled by an env-var setting**, not by code failure. No exception is being thrown; the gate is being deliberately tripped.

---

## Why this wasn't found earlier (2026-05-29 diagnostic)

The 2026-05-29 diagnostic (`BACKUP_RUNTIME_DIAGNOSTIC_REPORT.md`) observed the same symptoms (`task_alive: false`, `armed_at: null`, `completed without error`) but lacked the boot-step instrumentation to distinguish "exception inside loop body" from "loop body never entered". Without that distinction, the report could only hypothesize. With Phase 1+2 instrumentation in place, the distinction is now **certain**.

---

## Operator decisions surfaced (NOT YET AUTHORIZED)

1. **Read the production env-var value** for `SCHEDULER_ENABLED`. Operator-side: Emergent platform → Production env panel → search `SCHEDULER_ENABLED`. Expected to find it set to `false`, `0`, or `off`.
2. **Confirm intent**: was `SCHEDULER_ENABLED=false` set deliberately (e.g., during a prior incident) or accidentally (e.g., copy-paste from preview's `.env`)?
3. **If accidental**: change to `true` or unset entirely (default is `"true"`). Requires production env update + worker restart.
4. **If deliberate**: document the reason in `/app/memory/`. The scheduler will remain off until reversed.

**No env-var changes will be made by the agent until operator authorizes.**

---

## Supplementary findings

### Production's last successful complete-r2 backup (unchanged from Batch A)
- 2026-05-26 11:06 UTC — drift now 4+ days.
- All visible `backup_health` rows in the diagnostic response are `mode: "lite"`.
- See `COMPLETE_R2_DISABLEMENT_INVESTIGATION.md` for why lite-mode-only is in effect.

### Watchdog alarm threshold
- `watchdog_threshold_hours: 25.0` — if `seconds_since_last_tick > 90 000`, the system should send an alarm email. Since `seconds_since_last_tick: null` (never had a tick), the threshold has never been triggered. **This is a watchdog blind spot**: the alarm doesn't fire when the scheduler has *never* run, only when a previously-running scheduler stops ticking. Operator may want this addressed in a future hardening phase (Phase 3 candidate).

---

## Stop-condition compliance

- ✅ Read-only probe (3 GET calls, no writes)
- ✅ No scheduler code modification post-deploy
- ✅ No env-var changes
- ✅ Raw responses persisted to `/app/memory/batch_b_evidence/`
- ✅ No remediation applied
