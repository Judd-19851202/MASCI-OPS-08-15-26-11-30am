# Backup Scheduler Restart Verification Report

_Production · `mascidocs.com` · 2026-05-29 19:06–19:12 UTC._

> Post-redeploy verification per operator's POST-REDEPLOY PRODUCTION
> BACKUP VERIFICATION directive.
> Read-only verification. No code changes. No env changes. One
> operator-pre-authorized `POST /api/admin/backups/run-now?lite=true`
> at 19:09:06Z (part of Step 4).

## Final answer

> **Did the redeploy restore the backup scheduler?  →  NO.**

The fresh pod (uptime 11 min at end of probe) reproduces the same
**RESURRECT-and-die** pattern observed pre-redeploy. The supervisor is
alive and trying; each arm attempt of `_backup_scheduler_loop()` dies
before it can record a single tick or arm event. Backup CODE path
remains fully functional (manual lite backup succeeded in 10.6 s).

This satisfies the operator's stop clause:
> "If scheduler does not revive after restart, then recommend
> code-level hardening as a separate P0."

I am **STOPPING** here per directive. No code, env, or scheduler
changes have been made.

## Incident classification

> **B — PARTIALLY RESOLVED**
>
> - Manual backup works (fresh `backup_health` row written + emailed)
> - Scheduler still unhealthy
> - Auto-scheduled hourly/daily backups remain offline
> - Operational impact identical to pre-redeploy state

## STEP 1 · Production health

| Check | Result |
|---|---|
| `/api/health` | HTTP 200 · `{ok:true, service:masci-hub}` @ 19:06:50Z |
| `/api/version` | HTTP 200 · `service:masci-hub` · `started_at: 2026-05-29T19:00:46.062Z` · `uptime_s: 364` (≈6 min at first probe) |
| `/api/auth/multi-login` (admin) | HTTP 200 · `ok:true` · `portal_tokens:[admin, pm, shop, hr, safety, dispatch, field_leadership]` |
| `/api/admin/backups-scheduler-state` | HTTP 200 · 0.23 s — token works, endpoint healthy |
| DB connectivity | Implicit ✅ — login + scheduler-state both read from Mongo without errors |

**Fresh pod confirmed**. The redeploy successfully created a new
container — `started_at` is 19:00:46Z and `uptime_s` was 364 at first
probe, both consistent with a redeploy started ~6 min before
verification began.

## STEP 2 · Scheduler state — BEFORE state (T0)

`GET /api/admin/backups-scheduler-state` at **2026-05-29T19:07:16Z**
(uptime ≈ 6.5 min):

```jsonc
{
  "scheduler": {
    "alive": false,
    "armed_at": null,
    "last_tick_ts": null,
    "in_progress": false,
    "last_attempt_started_at": null,
    "last_attempt_outcome": null,        // ◄── cold — supervisor hadn't acted yet
    "last_run_for_hour": {},
    "failed_attempts": {}
  },
  "task_alive": false,
  "seconds_since_last_tick": null,
  "manual_run": { "outcome": null, "lite_mode": null, ... },
  "lite_mode_only_env": true,
  "oom_watermark_mb": 600.0,
  "watchdog_threshold_hours": 25.0,
  "circuit_breaker_max_attempts_per_day": 3,
  "scheduled_hours_utc": [2, 18],
  "now_utc": "2026-05-29T19:07:16.963921+00:00",
  "recent_health": [
    { "ts": "2026-05-29T18:20:21.409Z",     // manual lite backup from
      "mode": "lite",                        // pre-redeploy diagnostic
      "filename": "MASCI_lite_backup_2026-05-29_182015Z.zip" }
  ]
}
```

### Interpretation

| Signal | Meaning |
|---|---|
| `_BACKUP_SCHEDULER_STATE` reset to defaults (all nulls / empties) | ✅ Pod is genuinely fresh — no stale state carried over from the dying pod |
| `last_attempt_outcome: null` AND `armed_at: null` at uptime ≈ 6 min | At 6 min uptime, **no successful arm has happened AND no resurrect has been attempted yet** — the in-app 5-min supervisor was about to fire its first cycle |
| `lite_mode_only_env: true` | Operator's pre-existing mitigation still active (not changed by this session) |
| `recent_health` newest row | Still the manual lite backup from 18:20:21Z — production has not received a single durable backup tick since pod boot |

## STEP 3 · Tick observation — AFTER state (T1 · +91s)

`GET /api/admin/backups-scheduler-state` at **2026-05-29T19:08:47Z**
(uptime ≈ 8 min):

```jsonc
{
  "scheduler": {
    "alive": false,
    "armed_at": null,
    "last_tick_ts": null,
    "last_attempt_outcome":
      "RESURRECTED at 2026-05-29T19:07:30.421858+00:00 "
      "(previous: completed without error)"  // ◄── exact same RED FLAG
  },
  "task_alive": false,
  "now_utc": "2026-05-29T19:08:47.091645+00:00"
}
```

### Interpretation

- The in-app supervisor IS alive on the fresh pod — it issued a
  RESURRECT at **19:07:30Z**, ~6 min 44 s after pod boot.
- The resurrected task died **between 19:07:30Z and 19:08:47Z** without
  ever:
  - setting `alive: true`
  - writing `armed_at`
  - writing `last_tick_ts`
  - producing any `backup_health` row
- **`last_tick_ts` did NOT advance** between T0 and T1.
- **The pattern is byte-identical to the pre-redeploy diagnostic
  report §1**: `task_alive: false · alive: false · armed_at: null ·
  last_tick_ts: null · last_attempt_outcome: "RESURRECTED at ..."`.

## STEP 4 · Manual lite backup

```
T_BEFORE = 2026-05-29T19:09:06Z
POST https://mascidocs.com/api/admin/backups/run-now?lite=true
Headers: X-Admin-Token: <fresh admin token>

HTTP 200 · 0.27 s · accepted=true · lite_mode=true · started_at=19:09:06.503Z

Completion (polled at +12s):
  finished_at = 2026-05-29T19:09:17.116Z   (10.6 s elapsed)
  outcome     = ok · MASCI_lite_backup_2026-05-29_190906Z.zip ·
                203 KB · emailed_to=jaymn.judd@mascigc.com
  lite_mode   = true
```

**Result: ✅ SUCCESS.** Backup code path is fully functional on the
fresh pod. The `_do_run` BackgroundTask completed end-to-end (zip
build · email send · health row write).

## STEP 5 · Backup health row produced by manual run

```jsonc
{
  "id":         "9927a723fff84d498b6e09c47c32ba84",
  "ts":         "2026-05-29T19:09:16.991167+00:00",
  "ok":         true,
  "mode":       "lite",
  "filename":   "MASCI_lite_backup_2026-05-29_190906Z.zip",
  "size_bytes": 208739,                    // 203 KB
  "records":    139,                       // metadata-only payload (lite)
  "emailed_to": "jaymn.judd@mascigc.com",
  "error":      null
}
```

Fresh `backup_health` row landed in production Atlas. Three newest rows
chronologically:

```
2026-05-29T19:09:16Z · mode=lite        · MASCI_lite_backup_2026-05-29_190906Z.zip
2026-05-29T18:20:21Z · mode=lite        · MASCI_lite_backup_2026-05-29_182015Z.zip
2026-05-26T11:06:59Z · mode=r2-usage-alert
```

R2 upload: **not performed** (lite mode does not push to R2 by design,
same as the prior manual run). Live R2 archive remains the May 26
complete backup.

## STEP 6 · Supervisor health — Final state (T2 · +~4 min)

`GET /api/admin/backups-scheduler-state` at **2026-05-29T19:11:37Z**
(uptime ≈ 11 min):

```jsonc
{
  "scheduler": {
    "alive": false,
    "armed_at": null,
    "last_tick_ts": null,
    "last_attempt_outcome":
      "RESURRECTED at 2026-05-29T19:07:30.421858+00:00 (previous: completed without error)",
    "in_progress": false
  },
  "task_alive": false,
  "seconds_since_last_tick": null,
  "now_utc": "2026-05-29T19:11:37.108645+00:00"
}
```

### Interpretation

- ✅ **No crash loop**: Only **one** RESURRECT line in 4+ minutes —
  matches the supervisor's 5-min cycle. The pod is not thrashing.
- ❌ **No recovery either**: The single supervisor attempt at 19:07:30Z
  died and was never followed by `alive: true` / `armed_at`.
- ❌ **No tick advancement**: `last_tick_ts` remained `null` from T0 to
  T1 to T2.

## STEP 7 · Incident status comparison · pre-redeploy vs post-redeploy

| Signal | PRE-REDEPLOY (18:20:14Z) | POST-REDEPLOY (19:11:37Z) | Delta |
|---|---|---|---|
| Production pod | OLD (silent ≥ 79 h) | FRESH (`started_at=19:00:46Z`) | ✅ pod genuinely restarted |
| `_BACKUP_SCHEDULER_STATE` cleared | – (stale "RESURRECTED" from 18:16:17Z) | ✅ reset (null at T0) | ✅ clean cold start |
| `scheduler.alive` | false | false | ❌ unchanged |
| `task_alive` | false | false | ❌ unchanged |
| `armed_at` | null | null | ❌ unchanged |
| `last_tick_ts` | null | null | ❌ unchanged |
| Supervisor attempting resurrect | yes (18:16:17Z) | yes (19:07:30Z) | ✅ supervisor still alive |
| Resurrect succeeds | no | no | ❌ identical failure mode |
| Manual `run-now?lite=true` works | ✅ | ✅ | ✅ backup code is healthy |
| `lite_mode_only_env` | true | true | ✅ env unchanged (per directive) |
| `BACKUP_LITE_MODE_ONLY` source | operator-set | operator-set | ✅ env unchanged (per directive) |

## STEP 8 · Root-cause classification (refined)

The pre-redeploy diagnostic concluded:

> "The production backup scheduler's resurrected task is dying
> immediately during initialization — most likely an OOM kill or an
> unhandled exception that occurs BEFORE the first `_record_backup_health`
> call (otherwise we'd see an error row)."

**The post-redeploy evidence confirms this hypothesis.** A clean pod
restart cleared `_BACKUP_SCHEDULER_STATE` and the singleton lock, yet
the very FIRST arm attempt on the new pod (initiated by the supervisor
at 19:07:30Z, ≈6:44 after boot) **also died immediately** with no
state mutation. That rules out:

- ✗ "stale module-level state from previous pod" (cold pod, same failure)
- ✗ "stuck singleton-lock from previous worker" (singleton has 90 s TTL,
  far less than the 6.7 min from boot to the failed RESURRECT)
- ✗ "stale in-progress flag blocking arm" (also reset on boot)

What remains:

- ✓ **An exception or kill that fires during scheduler-task
  initialization itself** — happening between the supervisor's
  `asyncio.create_task(run_with_singleton_lock(...))` call and the
  scheduler's first state-write at
  `_BACKUP_SCHEDULER_STATE["alive"] = True` / `["armed_at"] = ...`
  (see `server.py:6328-6329`).
- Most likely candidates (in order of probability):
  1. **OOM kill during R2 client initialization** — even in lite-only
     env, the singleton-lock helper or scheduler-loop module imports
     may instantiate the R2 client at the top of the loop and crash
     the worker. The pod's container memory headroom under
     `lite_mode_only_env=true` should be re-examined.
  2. **Exception in `_ensure_scheduler_lock_indexes` or
     `run_with_singleton_lock`** before the scheduler loop is reached.
  3. **An unhandled exception in `_seed_state_from_health()` /
     `last_r2_complete_hour` seeding** at `server.py:6389–6411` — this
     code runs BEFORE any state-write.

## STEP 9 · Evidence captured for audit

| Artifact | Value |
|---|---|
| Pod started_at | `2026-05-29T19:00:46.062130Z` (`/api/version` uptime_s=364 at first probe) |
| Pre-state HTTP (T0) | `GET /api/admin/backups-scheduler-state` 200 @ 2026-05-29T19:07:16Z |
| Mid-state HTTP (T1) | `GET /api/admin/backups-scheduler-state` 200 @ 2026-05-29T19:08:47Z (RESURRECT line appeared) |
| Manual trigger HTTP | `POST /api/admin/backups/run-now?lite=true` 200 @ 2026-05-29T19:09:06Z (`started_at=19:09:06.503Z`) |
| Manual completion | `finished_at=2026-05-29T19:09:17.116Z` (10.6 s) |
| backup_health row id | `9927a723fff84d498b6e09c47c32ba84` |
| Backup filename | `MASCI_lite_backup_2026-05-29_190906Z.zip` |
| Size | 208,739 bytes (203 KB) |
| Records | 139 (lite-mode metadata) |
| Email destination | `jaymn.judd@mascigc.com` |
| Post-state HTTP (T2) | `GET /api/admin/backups-scheduler-state` 200 @ 2026-05-29T19:11:37Z |
| Supervisor RESURRECT attempts on fresh pod | 1 (at 19:07:30Z — died) |
| Crash-loop indicators | NONE — single RESURRECT per ~5 min cycle |

## STEP 10 · Recommended next action

> **PROMOTE TO P0 — SCHEDULER CODE-LEVEL HARDENING REQUIRED.**

Per the operator's pre-authorized fallback clause ("If scheduler does
not revive after restart, then recommend code-level hardening as a
separate P0"), this report formally promotes the issue.

### Recommended hardening work (NOT executed — awaiting authorization)

1. **Instrument the arm path** — add tightly-scoped exception
   capture + persistent log line ("scheduler-arm-failed: <repr>")
   inside `run_with_singleton_lock` or at the very top of
   `_backup_scheduler_loop` so the next failure is diagnosable from
   the live state endpoint instead of requiring container logs.
2. **Guard `_seed_state_from_health()`** against any exception so a
   bad row in `backup_health` cannot kill the entire scheduler loop.
3. **Defer R2 client instantiation** until the first
   `complete-r2` tick. While `lite_mode_only_env=true`, the loop
   should not touch boto3/R2 modules at all.
4. **Record `scheduler-arm-failed` rows in `backup_health`** with
   `mode="arm-failed"` so the diagnostic endpoint surfaces the actual
   cause to admins without operator console access.
5. **Add a 60-second "is-alive-by-now" assertion** in
   `@app.on_event("startup")` that logs CRITICAL if the scheduler
   hasn't armed within 60 s of pod boot — that line will appear in
   container logs and Emergent Support can pull it.

None of the above is in scope right now. **I will wait for explicit
authorization** to land any of these changes in preview before
operator-driven redeploy.

### Operational guidance while scheduler is broken

- **Manual lite backups every 12–24 h** via `POST /api/admin/backups/run-now?lite=true`
  remain the only auto-protection path. The watchdog cooldown
  (`BACKUP_WATCHDOG_COOLDOWN_HOURS=12`) will keep the noisy email
  from re-firing until the next cooldown expires.
- **R2 last full archive** is still 2026-05-26 (`MASCI_complete_backup_2026-05-26_110257Z.zip`).
  Any restoration would need to combine the May 26 archive with the
  current Atlas state — data-loss risk if Atlas dies remains MEDIUM.
- **Daily Report PDF audit footer**, foreman / superintendent /
  approval-routing workflows, and authentication flows are
  UNAFFECTED — those code paths do not depend on the backup
  scheduler.

## STEP 11 · Doctrine compliance

- ✅ Verification only — read-only HTTP probes + the one operator-pre-
  authorized `run-now?lite=true` call.
- ✅ Zero code changes.
- ✅ Zero env-var changes.
- ✅ No scheduler restart attempted beyond the redeploy itself.
- ✅ No Approval/Rejection, Pilot, RFI, Schedule, or P6 work touched.
- ✅ Evidence fully captured (pre-state · resurrect line · manual run
  HTTP + completion · fresh health row · post-state) with timestamps.
- ✅ Stop condition observed — this report is the deliverable; awaiting
  operator instruction.

---

_End of BACKUP_SCHEDULER_RESTART_VERIFICATION_REPORT.md._
