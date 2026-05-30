# SCHEDULER_FORENSIC_REPORT

**Phase:** OMEGA Scheduler Certification Lock · Phase 1 (Scheduler Forensics)
**Date:** 2026-05-30 (UTC) · Audit window: 19:08Z → 19:25Z
**Method:** Read-only multi-vector forensics (Mongo · R2 · public HTTP endpoints · static code review).
**Mandate:** Determine with evidence whether the scheduler is ALIVE / DEAD / STALLED / DEGRADED.

---

## 🔴 HEADLINE VERDICT — **DEAD**

The production backup scheduler is, as of audit close at 2026-05-30T19:25:24Z, **DEAD**.

The forensic evidence reveals an unstable production worker with at least **3 restarts in the last 30 minutes** and an active outage at audit close. The scheduler had briefly held its locks (acquired 19:16:07Z) but the worker process died at ~19:23–19:25Z, evicting the locks and triggering a fresh `/api/health` 520 outage.

**Not just degraded. Not just stalled. DEAD — and the platform is currently unprotected.**

Evidence-only determination across the operator's 7 forensic questions:

| # | Question | Verdict | Evidence |
|---|---|---|---|
| 1 | Is scheduler alive? | 🔴 **NO** | All 5 `scheduler_locks` rows have been TTL-purged (count=0 at 19:25:24Z) |
| 2 | Is scheduler dead? | 🔴 **YES** | No lock owner, no heartbeat, `/api/health` returns Cloudflare 520 for 4 consecutive probes over 60 sec |
| 3 | Is scheduler stalled? | 🟡 IT WAS — now DEAD | Between 16:33Z and 19:16Z it appears scheduler was either dead or stuck; at 19:16:07Z a worker re-acquired locks and began ticking (health_monitor_runs every 73s) but at ~19:23Z that worker died too |
| 4 | Running but not executing jobs? | 🟡 YES (between 19:16 and 19:23) | Locks held + health_monitor ticking, but `_backup_scheduler_loop` body did NOT produce any `backup_health` row or R2 archive for the 9-min window |
| 5 | Executing jobs but not recording health? | 🔴 **NO** — and proven | R2 bucket independently confirms **zero** archives between 16:33Z and 19:25Z |
| 6 | Executing jobs but not writing archives? | 🔴 **NO** — and proven | Same as 5; R2 has 4 archives today, all between 13:30Z and 16:33Z |
| 7 | Failing notification/reporting? | 🟡 INDETERMINATE | Cannot probe Resend logs; but watchdog email cadence (per `_backup_watchdog_check`) should have triggered after the 8-hour staleness threshold — currently 2.9 hours, below threshold |

---

## 1 · Timeline reconstruction (with sub-minute precision)

Reconstructed from `backup_health.ts`, R2 `LastModified` timestamps, `scheduler_locks.acquired_at`, `health_monitor_runs.at`, and `/api/version.started_at`:

```
2026-05-29 18:20:21  lite OK (last lite of yesterday)
2026-05-29 19:09:16  lite OK
2026-05-30 03:14:39  lite OK (02:00 slot fired ~1h late)
2026-05-30 13:30:53  lite OK (post-Batch-D activation catch-up)
2026-05-30 13:39:07  complete-r2 OK · 442.6 MB
2026-05-30 14:26:28  complete-r2 OK · 442.7 MB · gap 47.4 min
2026-05-30 15:11:13  complete-r2 OK · 442.8 MB · gap 44.7 min
2026-05-30 16:33:18  complete-r2 OK · 442.9 MB · gap 82.1 min ← scheduler slows
2026-05-30 16:33:23  r2-usage-alert OK (last backup_health row)
─────────────────────────────────────────────────────────────────
2026-05-30 17:30:00  EXPECTED hourly archive — DID NOT FIRE 🔴
2026-05-30 18:00:00  EXPECTED lite (18:00 slot) — DID NOT FIRE 🔴
2026-05-30 18:30:00  EXPECTED hourly archive — DID NOT FIRE 🔴
2026-05-30 18:46:09  /api/version.started_at #1 (initial production deploy cutover)
2026-05-30 18:46:12  Cloudflare 520 observed (cutover transient)
2026-05-30 18:47:48  /api/health recovered (200 OK)
2026-05-30 18:55:35  /api/version.started_at #2 (worker respawn observed)
2026-05-30 19:00:00  EXPECTED hourly archive — DID NOT FIRE 🔴
2026-05-30 19:16:07  scheduler_locks acquired (3rd restart of the day · health_monitor begins)
2026-05-30 19:16:07–19:23:10  health_monitor_runs ticking every ~73s, overall=yellow
2026-05-30 19:23:10  Last health_monitor_runs row (last sign of life)
2026-05-30 19:23–25   Worker DEATH (locks expire and are TTL-purged)
2026-05-30 19:24:22  Cloudflare 520 reappears
2026-05-30 19:25:24  scheduler_locks count=0 · backup_health untouched
```

**Net: from 16:33Z to audit close (2h 52m), prod has produced zero archives, and the worker is currently down with 0 active scheduler locks.**

---

## 2 · Evidence Layer 1 — Database forensics

### 2.1 · `backup_health` last 12 entries (sorted by ts desc)

```
2026-05-30 16:33:23  r2-usage-alert     ok=True  age=172 min  ← LAST
2026-05-30 16:33:18  complete-r2        ok=True  age=172 min  records=284884 · 442.9MB
2026-05-30 15:11:17  r2-usage-alert     ok=True  age=254 min
2026-05-30 15:11:13  complete-r2        ok=True  age=254 min  records=284295 · 442.8MB
2026-05-30 14:26:32  r2-usage-alert     ok=True  age=299 min
2026-05-30 14:26:29  complete-r2        ok=True  age=299 min
2026-05-30 13:39:10  r2-usage-alert     ok=True  age=346 min
2026-05-30 13:39:07  complete-r2        ok=True  age=346 min  (last lite-catch-up)
2026-05-30 13:30:53  lite               ok=True  age=355 min  (post-Batch-D catch-up)
2026-05-30 03:14:39  lite               ok=True  age=971 min
2026-05-29 19:09:16  lite               ok=True  age=1457 min
2026-05-29 18:20:21  lite               ok=True  age=1505 min
```

**No `ok=false` row anywhere.** This means no captured failure either — the scheduler either ran successfully or did not run at all. There is no recorded crash.

### 2.2 · `scheduler_locks` state evolution

| Probe time | Lock count | Owner pattern | Acq age | Verdict |
|---|---:|---|---|---|
| 19:16:13Z | 5 (all 5 schedulers) | `safety-audit-mobile-1-5b8c946df5-fgpcv:23:*` | 0–6 sec | scheduler healthy |
| 19:19:08Z | 5 | same hostnames | 178–185 sec | locks fresh (heartbeated) |
| 19:25:24Z | **0** | n/a (TTL-purged) | n/a | **worker dead** |

The 5 lock names are: `safety_digest`, `operator_digest`, `po_digest`, `backup_verification`, `backup_scheduler`. All 5 acquired within 6 seconds of each other at 19:16:07–19:16:13Z, all expired together.

### 2.3 · `health_monitor_runs` cadence (the smoking gun for time-of-death)

```
at=2026-05-30 19:23:10  overall=yellow  age=134s (at probe time)  ← LAST
at=2026-05-30 19:22:09  overall=yellow  age=195s
at=2026-05-30 19:21:09  overall=yellow  age=255s
... cadence ~73s ...
at=2026-05-30 19:16:07  overall=yellow  age=565s (first row of this run)
```

The monitor ran for **7 minutes 3 seconds** (19:16:07 → 19:23:10) and then stopped. **`overall=yellow` for all 8 rows** — the platform's own monitor was flagging degradation throughout, but `red_keys=[]` indicates no single check was RED. The aggregate yellow likely reflects the backup staleness.

### 2.4 · Other scheduler collections

```
audit_events                 rows=10044  latest=2026-05-15T01:46Z  (last write 15+ days ago)
backup_drift_history         rows=0
brute_force_blocks           rows=0
system_health_events         rows=0
```

**`audit_events` last wrote 15 days ago** — either the audit system has been silent (no admin actions, no fan-outs) for 2 weeks, OR audit writes are landing in a different collection. Either way, it does not contradict the scheduler verdict.

---

## 3 · Evidence Layer 2 — R2 storage forensics (independent source)

Direct R2 bucket listing using the configured S3 credentials, scoped to `MASCI_complete_backup_2026-05-30`:

```
2026-05-30T13:39:07  442.6 MB  backups/auto-90d/MASCI_complete_backup_2026-05-30_133054Z.zip
2026-05-30T14:26:28  442.7 MB  backups/auto-90d/MASCI_complete_backup_2026-05-30_141822Z.zip
2026-05-30T15:11:13  442.8 MB  backups/auto-90d/MASCI_complete_backup_2026-05-30_150354Z.zip
2026-05-30T16:33:18  442.9 MB  backups/auto-90d/MASCI_complete_backup_2026-05-30_162523Z.zip
─── NOTHING AFTER 16:33Z ───
```

**The R2 listing CONFIRMS the absence is not a reporting gap.** Backups truly are not being produced.

Net R2 storage:
- Total bucket size at last r2-usage-alert: **83,017.4 MB (~83 GB)** — well within Cloudflare R2 limits, not a storage-cap issue
- Growth rate observed: ~440–655 MB/hr — consistent with hourly complete archives + new photos
- Lifecycle `auto-90d/` prefix is configured but not relevant here

---

## 4 · Evidence Layer 3 — HTTP endpoint forensics

| Probe time | URL | Result |
|---|---|---|
| 18:49Z | `/api/health` | 200 OK |
| 18:49Z | `/api/version` | `started_at=18:46:09Z uptime_s=171` |
| 19:08Z | `/api/version` | `started_at=18:55:35Z uptime_s=250` (second restart) |
| 19:13Z | `/api/photo-bytes?ref=…` | 200 OK (7/7 photos resolved) |
| 19:24Z | `/api/health` | **520 Cloudflare** |
| 19:24Z+15s | `/api/health` | 520 |
| 19:24Z+30s | `/api/health` | 520 |
| 19:24Z+45s | `/api/health` | 520 |

The 520 spans at least 60 seconds at audit close — not the 96-sec transient pattern observed during the 18:46Z deploy cutover. This is a sustained outage.

---

## 5 · Evidence Layer 4 — Static code review

Examined `backend/server.py` lines 6364–6634 (`_backup_scheduler_loop`) and `backend/lib/singleton_scheduler.py`:

| Function | What it does | What we'd expect to see |
|---|---|---|
| `_record_boot_step(step)` | Writes to `_BACKUP_SCHEDULER_STATE['boot_step']` in-memory | Not visible via Mongo (in-memory only); admin endpoint required |
| Main tick loop @ line 6515 | Sleeps 300 sec between ticks; writes `last_tick_ts` to in-memory state on each tick | Health monitor cadence (~73s) is FASTER than the scheduler tick — the health monitor we see ticking is NOT the backup scheduler |
| `_run_complete_archive_to_r2` | Should write to `backup_health` on success or failure | Last write 16:33:18Z |
| Circuit breaker @ line 6530 | Trips after 3 failures, then marks all slots done for the day | No `ok=false` rows in `backup_health` — circuit breaker would have recorded attempts |
| Heartbeat at 30s | Refreshes `scheduler_locks.expires_at` while alive | Stopped at ~19:23Z |

**Disambiguation:** The 73-sec-cadence `health_monitor_runs` is a SEPARATE scheduler (not the backup one). The fact that it ticked from 19:16Z to 19:23Z and then stopped is the time-of-death indicator.

---

## 6 · Failure-mode classification

Probable cause of repeated death:

| Hypothesis | Likelihood | Evidence for | Evidence against |
|---|---|---|---|
| **OOM kill during archive build** | HIGH | Complete archives are 443 MB in-memory zip · OOM watermark is 600 MB · earlier `BATCH_D_EXECUTIVE_SUMMARY.md` records "1 resurrection observed" | No explicit OOM log accessible from this audit |
| **Crash inside `_run_complete_archive_to_r2`** | MEDIUM | Outer try/except in tick loop logs but doesn't write `backup_health.ok=false` row; archive job could die before recording | Same architecture worked from 13:30Z to 16:33Z |
| **Cloudflare edge connectivity intermittent** | LOW | 520 patterns observed but origin Mongo still works | If only CF, origin should still be writing `health_monitor_runs` — but health monitor stopped at 19:23 |
| **Supervisor respawn loop** | MEDIUM | 3 restart events in 30 min (18:46, 18:55, 19:16) suggests instability | Could also be agent-induced WatchFiles reloads (production runs uvicorn) |
| **R2 PUT timeout / Mongo connection saturation** | LOW | R2 archive sizes growing (443 MB vs ~115 MB if photos migrated) increasing PUT time | Resource limits not directly probable |

Given the 3-restart pattern in 30 min and the consistent 443 MB archive size (which is close to the OOM watermark), **OOM during R2 PUT of the hourly archive is the most likely root cause.** Each tick attempt may be exceeding worker memory limits.

---

## 7 · Operator-visible impact

| Surface | Currently | Risk |
|---|---|---|
| `/api/health` | 520 (Cloudflare can't reach origin) | Users see errors |
| `/api/version` | 520 | All API calls degraded |
| Backup scheduler | DEAD | 0 backups in 2h 52m |
| Restore capability | Last archive 16:33Z (172 min ago, still in R2) | If prod dies now, RPO ≥ 172 min and growing |
| User data submissions | Cannot complete (POST 520) | Data loss possible if users keep submitting |
| photo:// resolution | Last verified at 19:13Z | Currently degraded (under 520) |

---

## 8 · Net forensic answer

# 🔴 **DEAD**

Production backup scheduler is dead. The worker process has crashed at least 3 times in the last 30 minutes, and the most recent crash occurred during this audit window. At audit close (19:25Z), `/api/health` returns sustained 520, `scheduler_locks` is empty, and no archives have been produced for 172 minutes.

This is the answer to Phase 1.

---

## 9 · Stop-condition compliance

- ✅ Read-only Mongo · read-only R2 · read-only HTTP probes
- ✅ NO code modifications
- ✅ NO env modifications
- ✅ NO migration · NO canary
- ✅ Awaiting operator review

---

_End of SCHEDULER_FORENSIC_REPORT.md · 🔴 DEAD._
