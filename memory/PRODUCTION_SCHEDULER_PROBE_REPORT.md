# PRODUCTION_SCHEDULER_PROBE_REPORT

**Date:** 2026-02-01 · Batch A · Step 5
**Authorized action:** Read-only probe of production `/api/admin/backups-scheduler-state`.

**Probe URL:** `https://mascidocs.com/api/admin/backups-scheduler-state`
**Probe time (UTC):** 2026-05-30T03:13:55Z
**Auth method:** `X-Admin-Token` header (multi-login portal_tokens.admin)
**Raw response:** `/app/memory/batch_a_evidence/scheduler_state_pretrigger.json`

---

## Probe result — verbatim

```json
{
  "scheduler": {
    "alive": false,
    "armed_at": null,
    "last_tick_ts": null,
    "in_progress": false,
    "last_attempt_started_at": null,
    "last_attempt_outcome": "RESURRECTED at 2026-05-30T03:13:09.102183+00:00 (previous: completed without error)",
    "last_run_for_hour": {},
    "failed_attempts": {}
  },
  "task_alive": false,
  "seconds_since_last_tick": null,
  "manual_run": {"started_at": null, "finished_at": null, "outcome": null, "lite_mode": null},
  "manual_in_progress": false,
  "lite_mode_only_env": true,
  "oom_watermark_mb": 600.0,
  "watchdog_threshold_hours": 25.0,
  "now_utc": "2026-05-30T03:13:55.881567+00:00",
  "scheduled_hours_utc": [2, 18],
  "circuit_breaker_max_attempts_per_day": 3,
  "recent_health": [
    {"ts": "2026-05-29T19:09:16Z", "ok": true, "mode": "lite", "size_bytes": 208739, "records": 139},
    {"ts": "2026-05-29T18:20:21Z", "ok": true, "mode": "lite", "size_bytes": 207375, "records": 138}
  ]
}
```

---

## Findings

| Finding | Detail |
|---------|--------|
| **Scheduler is DEAD in production** | `alive: false`, `armed_at: null`, `last_tick_ts: null` — **identical state to the 2026-05-29 diagnostic**. No recovery occurred in the 8-day window between the prior diagnostic and this probe. |
| **Resurrection cycle is active** | `last_attempt_outcome` shows a fresh resurrection at 2026-05-30T03:13:09Z (46 seconds before the probe). The supervisor watchdog is correctly detecting and respawning, but each respawn dies immediately. |
| **Lite-mode-only env flag is set** | `lite_mode_only_env: true` confirms `BACKUP_LITE_MODE_ONLY=true` on the production worker. This forces ALL scheduled and manual backups into lite mode regardless of `lite=false` query parameter. |
| **Last successful backups** | Only **lite-mode** backups in the visible 10-row window: 2026-05-29 19:09 and 18:20 UTC (both manually triggered per the prior diagnostic). **No complete-r2 row is in the recent_health window.** |
| **Schedule** | `[2, 18]` hours UTC (twice daily — 02:00 and 18:00). No tick has fired since the dead state began. |
| **Watchdog threshold** | 25h. Once `seconds_since_last_tick > 25 * 3600`, an alarm email should fire to `BACKUP_EMAIL_TO`. |
| **Manual backup state** | `manual_run.outcome: null`, `manual_in_progress: false` — no manual run was active at probe time. |

---

## Interpretation

- The scheduler has been continuously dead since the 2026-05-29 diagnostic identified the issue.
- The "completed without error" wording in `last_attempt_outcome` means the asyncio Task is returning cleanly **without entering** the `_backup_scheduler_loop` body (or it's entering and exiting before `armed_at` is written). The previous Phase 2A investigation hypothesized this is happening inside `run_with_singleton_lock(...)` before `scheduler_fn` is awaited.
- **Phase 1 + Phase 2 hardening (Step 7 of this batch)** will surface the exact boot stage where the task is dying — once the hardened code is deployed to production, the next probe will show `boot_step` and `boot_exception` fields populated.

---

## Risk assessment

| Risk | Severity |
|------|----------|
| **Drift in complete-r2 backups** since 2026-05-26 11:06 UTC (last verified) | 🔴 P0 — 4 days of growth without an R2 archive |
| **Lite mode covers metadata snapshot only** | 🔴 P0 — lite mode does NOT capture full collection contents; manual lite backups (the only working path) provide ~138 records per snapshot, NOT the full 200K+ record production dataset |
| **Atlas point-in-time recovery still available** | 🟢 — independent of MASCI scheduler; restore is possible if absolutely needed |
| **Watchdog alarm functional** | 🟡 — should be firing daily-plus given the dead state; operator should confirm receipt of alarm emails |

---

## Stop-condition compliance

- ✅ Read-only probe (single `GET` call)
- ✅ No scheduler modification
- ✅ No restart attempted
- ✅ No env-var changes
- ✅ Raw response persisted to `/app/memory/batch_a_evidence/scheduler_state_pretrigger.json`
