# BACKUP_SCHEDULER_READINESS_REPORT

**Date:** 2026-02-01 · Phase 2A-4
**Mission:** Verify current scheduler status, failure mode, operational risk, manual capability, and readiness for future hardening. **No modifications. No deployment. No env-var changes. No scheduler reset.**

---

## 1 · Current status (read-only)

### Preview (this pod)
- **State**: scheduler intentionally disabled by env flag `SCHEDULER_ENABLED=false`.
- **Evidence**: `/var/log/supervisor/backend.err.log` shows the recurring pattern every 5 minutes:
  ```
  2026-05-30 02:33:36 server CRITICAL [scheduled-backup] scheduler task is DEAD — respawning.
    Last state: completed without error
  2026-05-30 02:33:36 lib.singleton_scheduler INFO [singleton-lock:backup_scheduler]
    SCHEDULER_ENABLED='false' — scheduler disabled on this worker (preview / non-prod)
  ```
- **Interpretation**: The "DEAD — respawning" message is **misleading wording** in preview. It reflects an asyncio Task that returned normally after the lock acquirer detected `SCHEDULER_ENABLED=false`. The supervisor watchdog respawns the task; it immediately exits again. This is **harmless** but generates ~288 noisy log entries per day in preview.
- **Severity in preview**: 🟢 Not an issue — preview is not supposed to run the scheduler.

### Production (prior diagnostic 2026-05-29 18:13–18:21 UTC)
- **Per `BACKUP_RUNTIME_DIAGNOSTIC_REPORT.md` §1 pre-state snapshot**:
  - `alive: false` · `armed_at: null` · `last_tick_ts: null`
  - `last_attempt_outcome: "RESURRECTED at 2026-05-29T18:16:17 (previous: completed without error)"`
  - `lite_mode_only_env: true` (production has `BACKUP_LITE_MODE_ONLY=true`)
  - `scheduled_hours_utc: [2, 18]` (twice daily)
  - **Last successful complete-r2 backup: 2026-05-26 11:06 UTC** (3 days before diagnostic)
- **Interpretation in production**: Scheduler task is genuinely dead — different mechanism than preview's intentional shutdown. The asyncio Task returns immediately ("completed without error") even though `SCHEDULER_ENABLED=true`. The supervisor resurrects every 5 min; resurrection lasts < 5 min and dies again.
- **Severity in production**: 🔴 P0 — scheduler is not ticking on its own.

### What we DO NOT have
- Live access to production logs since 2026-05-29.
- Confirmation that the lite-mode emergency fallback ran in the 2026-05-29 → 2026-02-01 window.
- Atlas backup row count for the production `backup_health` collection since the diagnostic.

---

## 2 · Current failure mode

From `_backup_scheduler_loop` code review (`server.py:6293`) and `run_with_singleton_lock` (`lib/singleton_scheduler.py:185`):

**Hypothesis (most likely)** — the lock acquisition path returns successfully (lock held by some prior owner whose heartbeat expired naturally), the scheduler immediately enters its main loop, and **dies silently within the first tick** due to one of:

- Mongo connection blip during the boot heartbeat read (`server.py:6342 await db.backup_health.find_one(...)`)
- Exception during the boot disk safety check (`server.py:11235 _disk_pct_used()`)
- Unhandled exception during the first slot-collapse calculation

The supervisor's 5-minute watchdog correctly detects "task done" but the resurrection inherits the same failure mode and dies the same way.

**This is consistent with**:
- `last_state: "completed without error"` (returned normally without raising)
- `armed_at: null` (never reached the `_BACKUP_SCHEDULER_STATE["armed_at"] = now.isoformat()` line at 6329)
- `last_tick_ts: null` (never reached the first tick)

The task is **exiting between the lock-acquisition success and the first state-write**.

---

## 3 · Current operational risk

| Risk | Level | Mitigation status |
|------|-------|-------------------|
| Backup drift in production | 🔴 P0 | Manual `POST /api/admin/backups/run-now?lite=true` confirmed working (2026-05-29) |
| Complete-r2 backups stale > 3 days | 🟡 | Last verified 2026-05-26 11:06 UTC; production trend since then unknown without live log access |
| Backup health endpoint failure | 🟢 Low | `GET /api/admin/backups-scheduler-state` returned valid JSON during 2026-05-29 probe |
| Restore drill freshness | 🟡 | Atlas point-in-time recovery is independent of MASCI scheduler; PIT remains available regardless |
| Watchdog alarm fatigue | 🟡 | Watchdog is firing in preview every 5 min (harmless) — production watchdog correctly logging CRITICAL on every resurrection |

---

## 4 · Current manual backup capability — VERIFIED WORKING

From `BACKUP_RUNTIME_DIAGNOSTIC_REPORT.md` §11:

```
POST /api/admin/backups/run-now?lite=true
  Response: 200 @ 2026-05-29T18:20:14Z (started_at=18:20:15.073Z)
  Background completion: 18:20:21.535Z (6.46 s)
  backup_health row id: ea6a58f30e1b454e9018350bf82f2917
  Filename: MASCI_lite_backup_2026-05-29_182015Z.zip
  Size: 207,375 bytes (202 KB)
  Records: 138 (lite mode = metadata-snapshot)
  Email destination: jaymn.judd@mascigc.com (delivered)
  R2 upload: NOT performed (lite mode is by-design metadata-only)
```

**Result**: Manual lite backup works in production. Manual complete-r2 backup has **not been re-verified in the current pod** (last successful: 2026-05-26). Operator authorization required before attempting a manual complete-r2 to verify.

---

## 5 · Readiness for future P0 hardening

When the operator authorizes hardening, the following 5-phase plan (held from prior session) becomes actionable:

### Phase 1 — Diagnostic instrumentation
- Add structured logging at every step of `_backup_scheduler_loop` boot (between lock-acquired and first state-write).
- Surface `boot_step` field in `_BACKUP_SCHEDULER_STATE` so the dead-state diagnostic shows WHERE the task died.

### Phase 2 — Defensive wrapping
- Wrap the boot heartbeat read (`server.py:6342`) in try/except + retry.
- Wrap the disk safety check (`server.py:11235`) in try/except.
- Any boot exception flips to `last_attempt_outcome: "BOOT EXCEPTION: {e!r}"` instead of silent task death.

### Phase 3 — Watchdog email
- Currently logs CRITICAL only. Add Resend email to `BACKUP_EMAIL_TO` after N consecutive resurrections (e.g. N=3).

### Phase 4 — Pod-restart safety
- If 5 consecutive resurrections fail within 30 minutes, mark `recovery_needed: true` in scheduler state and email operator.
- DO NOT auto-restart pod (operator wants manual control).

### Phase 5 — Verification
- Confirm at least one full complete-r2 backup cycle completes in production after hardening.
- Confirm `last_tick_ts` advances every 5–10 minutes.
- Confirm Atlas backup_health row count grows daily.

### Estimated effort
- Phases 1+2: ~2 hours surgical (single-file edit on `server.py`)
- Phase 3: ~1 hour
- Phase 4: ~1 hour
- Phase 5: production-only verification window, operator-authorized

### Risk during hardening
- 🟡 The fix touches the same code path that is currently dead. Any new bug could prevent the surgical fix from improving the situation.
- ✅ Mitigation: deploy hardening BEHIND `BACKUP_DIAGNOSTIC_VERBOSE=true` env flag so verbose logging activates without changing core flow.
- ✅ Lite-mode manual backups remain available throughout the hardening window.

---

## 6 · Stop-condition compliance

| Rule | Compliance |
|------|-----------|
| Do not modify scheduler | ✅ — no edits to `server.py` or `lib/singleton_scheduler.py` |
| Do not harden scheduler | ✅ — readiness plan documented, not executed |
| Do not deploy any fix | ✅ — no deploy actions taken |
| Read-only verification only | ✅ — used existing logs + existing diagnostic report |

---

## 7 · Operator-facing summary

- **Preview**: scheduler intentionally OFF (`SCHEDULER_ENABLED=false`); noisy log entries every 5 min are harmless.
- **Production**: scheduler is **dead** (verified 2026-05-29; current status unknown without live log access). Last confirmed complete-r2 backup 2026-05-26.
- **Manual fallback**: lite-mode manual backup works; complete-r2 manual backup has not been re-verified since the dead-state began.
- **Operator decisions needed**:
  1. Authorize a fresh runtime probe of `/api/admin/backups-scheduler-state` and `/api/admin/backups-health` in production (single read-only call).
  2. Authorize a single manual `POST /api/admin/backups/run-now?lite=false` (complete-r2 path) to verify the manual backup pipeline survives the dead-scheduler state.
  3. Authorize Phase 1+2 of the hardening plan (diagnostic instrumentation + defensive wrapping). This is the lowest-risk, highest-value next step.

**No action will be taken on any of these until the operator individually authorizes them.**
