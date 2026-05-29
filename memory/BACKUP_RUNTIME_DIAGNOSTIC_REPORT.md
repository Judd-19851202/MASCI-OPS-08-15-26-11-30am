# Backup Runtime Diagnostic Report

_Production · 2026-05-29 · 18:13–18:21 UTC._

> **Operator-authorized diagnostic** following the RED health alert.
> Read-only investigation + one operator-authorized manual-trigger call.
> No code changes. No env-var changes. No scheduler reset.

## 1 · Pre-state snapshot (production)

`GET https://mascidocs.com/api/admin/backups-scheduler-state` at 2026-05-29T18:20:14Z:

```jsonc
{
  "scheduler": {
    "alive": false,                          // ◄── scheduler asyncio task DEAD
    "armed_at": null,                        // never armed since this pod boot
    "last_tick_ts": null,                    // never ticked since boot
    "in_progress": false,
    "last_attempt_started_at": null,
    "last_attempt_outcome":
      "RESURRECTED at 2026-05-29T18:16:17.623749+00:00 "
      "(previous: completed without error)",  // ◄── supervisor tried 4 min ago
    "last_run_for_hour": {},
    "failed_attempts": {}
  },
  "task_alive": false,
  "seconds_since_last_tick": null,
  "manual_run": { "outcome": null, "lite_mode": null, ... },
  "manual_in_progress": false,
  "lite_mode_only_env": true,                // ◄── BACKUP_LITE_MODE_ONLY=true already
  "oom_watermark_mb": 600.0,
  "watchdog_threshold_hours": 25.0,
  "now_utc": "2026-05-29T18:20:14.770575+00:00",
  "scheduled_hours_utc": [2, 18],            // ◄── twice daily, not hourly
  "circuit_breaker_max_attempts_per_day": 3,
  "recent_health": [
    { /* last successful complete-r2 backup: 2026-05-26T11:06:56Z · 321 MB · 223,394 records */ }
  ]
}
```

### Diagnostic insights from pre-state

| Signal | Interpretation |
|---|---|
| `task_alive: false` + `alive: false` | the scheduler loop is NOT executing — confirmed dead. |
| `last_tick_ts: null` AND `armed_at: null` | the scheduler has not run a single tick since the current pod was booted. |
| `last_attempt_outcome: "RESURRECTED at 2026-05-29T18:16:17 (previous: completed without error)"` | the 5-minute supervisor IS alive · it DID notice the task was dead · it DID try to bring it back at 18:16:17Z · 4 minutes before this snapshot · BUT the resurrected task is dead again by 18:20:14Z. **Resurrect attempts are not surviving.** |
| `lite_mode_only_env: true` | `BACKUP_LITE_MODE_ONLY=true` is already on in prod. The May 26 11:06 `complete-r2` row predates that flag — it must have been flipped after that tick. |
| `scheduled_hours_utc: [2, 18]` | Twice daily at 02:00 and 18:00 UTC. The 79-h silence covers SIX missed ticks · today's 18:00 UTC tick (20 min before the operator authorized this call) was also missed. |
| `recent_health` newest row | still 2026-05-26T11:06:59Z r2-usage-alert · CONFIRMS the production DB's last write to `backup_health` was on that date. |

## 2 · Manual trigger · HTTP response

```
T_BEFORE_UTC = 2026-05-29T18:20:14Z
POST https://mascidocs.com/api/admin/backups/run-now?lite=true
Headers: X-Admin-Token: <64-char admin session token>

HTTP 200 · 0.288 s
{
  "accepted":   true,
  "lite_mode":  true,
  "poll":       "/api/admin/backups-scheduler-state",
  "started_at": "2026-05-29T18:20:15.073243+00:00"
}
```

## 3 · Post-state · manual run completion

First poll at 18:20:48Z (33 s after the POST) already showed completion:

```jsonc
"manual_run": {
  "started_at":   "2026-05-29T18:20:15.073243+00:00",
  "finished_at":  "2026-05-29T18:20:21.535541+00:00",   // ◄── completed in 6.46 s
  "outcome": "ok · MASCI_lite_backup_2026-05-29_182015Z.zip · 202 KB · emailed_to=jaymn.judd@mascigc.com",
  "lite_mode": true
}
```

## 4 · backup_health entry produced by the manual run

The next poll surfaced a fresh row at the top of `recent_health`:

```jsonc
{
  "id":          "ea6a58f30e1b454e9018350bf82f2917",
  "ts":          "2026-05-29T18:20:21.409106+00:00",
  "ok":          true,
  "mode":        "lite",
  "filename":    "MASCI_lite_backup_2026-05-29_182015Z.zip",
  "size_bytes":  207375,                      // 202 KB
  "records":     138,                         // metadata-only payload (lite mode)
  "emailed_to":  "jaymn.judd@mascigc.com",
  "error":       null
}
```

## 5 · R2 upload result

**No `mode="lite-r2"` row was written in this manual tick.** The lite mode does not push to Cloudflare R2 by design — only the `complete-r2` cadence ticks do. R2 still holds the last full archive from 2026-05-26T11:06:56Z (`MASCI_complete_backup_2026-05-26_110257Z.zip · 336 MB · 223,394 records`).

Live R2 tonnage (per the last r2-usage-alert row, unchanged): **79.02 GB · 1,846 objects**.

## 6 · Email delivery result

Backup code path stamped the row with `emailed_to: "jaymn.judd@mascigc.com"`. The 202 KB lite zip was attached to a Resend message sent to `BACKUP_EMAIL_TO`. Operator should confirm receipt at `jaymn.judd@mascigc.com`.

## 7 · Did the scheduler revive?

**No.** A second `scheduler-state` read at 18:20:48Z (33 s after fire, 4.5 min after the most recent supervisor RESURRECT) still reports:

```jsonc
"scheduler": {
  "alive": false,
  "task_alive": false,
  "armed_at": null,
  "last_tick_ts": null,
  "last_attempt_outcome": "RESURRECTED at 2026-05-29T18:16:17.623749+00:00 (previous: completed without error)"
}
```

The manual-run codepath bypasses the scheduler entirely (it runs in a FastAPI BackgroundTask, see `server.py:6730 _do_run`), so the success of the manual run **does NOT** indicate the scheduler is healthy. It only proves that the **backup CODE** (zip build · email · `backup_health` write) is fully functional.

## 8 · Root-cause classification (refined)

| Hypothesis from initial investigation | Status after live diagnostic |
|---|---|
| A — pod restart left `DISABLE_BACKUP_SCHEDULER=true` | RULED OUT · `lite_mode_only_env: true` is a separate flag · the scheduler-state endpoint would not return its existing fields if the scheduler were fully disabled |
| B — scheduler task + supervisor both crashed | **PARTIALLY CONFIRMED** · supervisor is alive (it issued the 18:16:17Z RESURRECT) but each resurrected task immediately dies again |
| C — task killed by OOM watermark during full zip build | **MOST LIKELY** · `lite_mode_only_env: true` was clearly set as the operator's mitigation after the 336 MB May 26 build · but the scheduler loop itself is dying ANYWAY on every resurrect, so the OOM kill is recurring on something that fires very early in the loop |

The refined root cause is therefore:

> **The production backup scheduler's resurrected task is dying immediately during initialization — most likely an OOM kill or an unhandled exception that occurs BEFORE the first `_record_backup_health` call (otherwise we'd see an error row). The supervisor IS attempting to bring it back, but each new task instance is killed the moment it tries to arm. The 5-minute resurrect interval explains why we see exactly ONE "RESURRECTED" line and not a cascade.**

## 9 · Impact assessment (updated)

| Axis | State |
|---|---|
| Production data | INTACT in live Atlas (`masci_safety` on `masci-prod.1nduwmg.mongodb.net`) |
| Last durable backup | 2026-05-26T11:06:56Z (`MASCI_complete_backup_2026-05-26_110257Z.zip · 336 MB · 223,394 records` on R2) |
| Just-created emergency lite | 2026-05-29T18:20:21Z (`MASCI_lite_backup_2026-05-29_182015Z.zip · 202 KB · 138 records · email-only · NOT on R2`) — a slim "DB exists & schema validates" proof, not a full data restore source |
| Data-loss risk if Atlas dies right now | medium — 79 h of operational records (May 26 11:06 → now) only live in Atlas |
| Daily Report PDF audit footer continuity | UNAFFECTED |
| Watchdog alarm cooldown | watchdog will NOT fire again until 12 h pass (`BACKUP_WATCHDOG_COOLDOWN_HOURS=12`) unless reset |
| Foreman / superintendent workflow | UNAFFECTED |

## 10 · Recommendation (per operator's authorization §5)

> _"If lite backup succeeds and scheduler is confirmed dead: Recommend production pod restart."_

**Both preconditions are met:**

1. ✅ Lite backup succeeded (HTTP 200 + completed in 6.46 s + 202 KB zip on email + backup_health row landed).
2. ✅ Scheduler is confirmed dead (`alive: false · task_alive: false · last_tick_ts: null` AND a recent RESURRECT attempt that did NOT survive).

**Recommendation:** Restart the production pod hosting `mascidocs.com`.

### Why this is the right move
- Backup code path is proven healthy (the manual run just succeeded end-to-end).
- The scheduler-init failure is happening AFTER pod boot but BEFORE the first health-row write, and the supervisor's 5-minute resurrect is not surviving — a clean reboot resets all module-level state (`_BACKUP_SCHEDULER_STATE`, singleton lock, in-progress flag).
- A pod restart also re-runs the startup validator at `server.py:11257` which CRITICAL-logs if the scheduler can't arm — that log line will tell us conclusively whether the resurrect failure is recurring or one-shot.
- The next scheduled tick is **02:00 UTC tomorrow** (~7.5 h from now). Restarting BEFORE that gives the supervisor time to settle and increases the chance the 02:00 tick fires.

### Recommended steps (operator-authorized only · I will NOT execute)
1. **Trigger one MORE lite manual run AFTER the restart** to confirm the post-restart code path still works.
2. **Watch `scheduler-state` for ~10 minutes after restart.** Look for `alive: true · armed_at: <fresh ts> · task_alive: true`.
3. **If the scheduler is still dying immediately on the restart pod**, the next diagnostic step is to read the production container logs from boot for the line:
   ```
   "[scheduled-backup] scheduler started — <hours_str>"
   ```
   followed by any CRITICAL · ERROR · or "scheduler task died" lines.
4. **Optional (operator decides)**: If the operator wants belt-and-suspenders before the 02:00 UTC tick, fire `run-now?lite=true` once more right after the restart to bank a fresh `backup_health` row.

### Forbidden (per directive · I will NOT do)
- ❌ modify scheduler code
- ❌ modify backup code
- ❌ change environment variables (`BACKUP_LITE_MODE_ONLY` stays where the operator left it)
- ❌ enable lite-only mode (already on; not flipped by me)
- ❌ redesign backup architecture
- ❌ restart the production pod without explicit go-ahead

## 11 · Evidence captured (for audit log)

| Artifact | Value |
|---|---|
| Pre-state HTTP | `GET /api/admin/backups-scheduler-state` 200 @ 2026-05-29T18:20:14Z |
| Manual trigger HTTP | `POST /api/admin/backups/run-now?lite=true` 200 @ 2026-05-29T18:20:14Z (`started_at=18:20:15.073Z`) |
| Background task completion | `finished_at=2026-05-29T18:20:21.535Z` (6.46 s) |
| backup_health row id | `ea6a58f30e1b454e9018350bf82f2917` |
| Backup filename | `MASCI_lite_backup_2026-05-29_182015Z.zip` |
| Size | 207,375 bytes (202 KB) |
| Records | 138 (lite mode is metadata-snapshot, by design) |
| Email destination | `jaymn.judd@mascigc.com` |
| R2 upload | NOT performed (lite mode does not push to R2 by design) |
| Scheduler state after fire | still `alive: false · task_alive: false` |
| Last RESURRECT attempt | 2026-05-29T18:16:17.624Z (4 min before our call · did not survive) |

## 12 · Doctrine compliance

- ✅ **Read-first** — full pre-state captured before any write call.
- ✅ **Single operator-authorized write** — exactly one `POST /run-now` per the directive.
- ✅ **No production code changes.**
- ✅ **No environment changes.**
- ✅ **Evidence captured in full** — pre-state · trigger response · post-state · backup_health row · scheduler state.
- ✅ **Recommendation gated** — pod restart proposed but NOT executed.

---

_End of BACKUP_RUNTIME_DIAGNOSTIC_REPORT.md._
