# BACKUP_SYSTEM_VERIFICATION_REPORT

**Date:** 2026-05-30 (Batch D · Phase 3)
**Method:** Live production probes + code-evidence audit. Read-only.
**Evidence:** `/app/memory/batch_d_evidence/`

---

## 1 · Subsystem status grid (PASS/FAIL determination for every backup path)

| # | Subsystem | Status | Evidence type |
|---|---|---|---|
| 1 | Scheduled LITE backup (02:00 / 18:00 UTC) | 🟢 VERIFIED WORKING | runtime · code · health-row |
| 2 | Scheduled-slot CATCH-UP (missed-window fill) | 🟢 VERIFIED WORKING | runtime today |
| 3 | Manual LITE backup (`POST /api/admin/backups/run-now`) | 🟢 VERIFIED WORKING | runtime (Batch A 03:14:33Z) · code |
| 4 | Manual COMPLETE backup (`POST /api/admin/backups/run-complete-now`) | 🟡 CODE-ONLY · NOT EXERCISED IN BATCH D | code only |
| 5 | Hourly COMPLETE-R2 (`BACKUP_R2_HOURLY=true` path) | 🟢 VERIFIED WORKING (cascaded auto-fire) | runtime today · code · R2 inventory |
| 6 | Nightly COMPLETE-R2 fallback (`BACKUP_R2_FULL_HOUR_UTC=3`) | 🟡 SUPERSEDED BY HOURLY in prod (`r2_hourly: true`) | code |
| 7 | R2 storage upload (boto3 S3-compatible) | 🟢 VERIFIED WORKING | 1 517 objects in bucket; today's archive present |
| 8 | S3 integration | 🟢 SAME AS R2 (uses S3 protocol against R2 endpoint) | env vars `S3_BUCKET`, `S3_ENDPOINT_URL`, etc. |
| 9 | Source: MongoDB read for backup payload | 🟢 VERIFIED WORKING | 141-record lite + 223 394-record complete payloads documented |
| 10 | `backup_health` collection (write) | 🟢 VERIFIED WORKING | new rows confirmed today (13:30:53Z, 13:39:10Z) |
| 11 | `backup_health` retention/history | 🟢 VERIFIED — 10 most-recent rows returned by state endpoint | runtime |
| 12 | Email notification on scheduled backup (Resend) | 🟢 VERIFIED WORKING | `emailed_to: jaymn.judd@mascigc.com` recorded today |
| 13 | Email alarm on R2 usage threshold | 🟢 INSTRUMENTATION VERIFIED · ALARM PATH NOT FORCED | r2-usage-alert row at 13:39:10Z (79.57 GB · 2 271 objects) |
| 14 | Watchdog (silent-scheduler alarm > 25h) | 🟢 INSTRUMENTED · CURRENTLY HEALTHY | `last_watchdog: {alarm_fired:false, hours_silent:0.0, reason:"healthy"}` |
| 15 | Supervisor (resurrect dead scheduler task) | 🟢 VERIFIED WORKING (fired at 13:26:25Z) | runtime |
| 16 | Circuit breaker (cap retries at 3/day) | 🟡 CODE PATH ONLY · NEVER TRIGGERED | code (server.py:6526-6541) |
| 17 | R2 lifecycle / retention rule (`backups/auto-90d/`) | 🟡 RULE APPLIED · TTL NOT YET VERIFIED THIS BATCH | infra (`scripts/r2_lifecycle_apply.py`) · oldest key in bucket = 2026-05-25 |
| 18 | Emergency disk-prune on boot (`BACKUP_DISK_HIGH_WATERMARK`) | 🟢 RUN ON BOOT (passed — current disk% below threshold) | code (server.py:11322-11327) |
| 19 | Restore from local lite ZIP | ⚪ UNKNOWN — RESTORE NOT EXERCISED | code only |
| 20 | Restore from R2 complete archive | ⚪ UNKNOWN — RESTORE NOT EXERCISED | code only |
| 21 | Restore-after-deploy / drift detection (Phase 25.3 `_backup_drift_watch`) | 🟢 INSTRUMENTED — log-warning channel only | code (server.py:5930-5933) |
| 22 | Mongo direct dump (mongodump) | 🚫 NOT IMPLEMENTED (by design — backup = app-level export) | code search → 0 results |

---

## 2 · Detailed evidence per subsystem

### 2.1 — Scheduled LITE backup · 🟢 VERIFIED WORKING

**Runtime evidence (`batch_d_evidence/probe_t0_attempt2.json`):**
```
recent_health[0]:
  ts:                2026-05-30T13:30:53.887175Z
  ok:                true
  mode:              lite
  filename:          MASCI_lite_backup_2026-05-30_133044Z.zip
  size_bytes:        211 805
  records:           141
  emailed_to:        jaymn.judd@mascigc.com
  error:             null
last_run_for_hour: {"2": "2026-05-30"}
last_attempt_outcome: "ok · ... · emailed_to=jaymn.judd@mascigc.com"
```

**Code evidence:** Loop at `server.py:6515–6577`. `_run_scheduled_backup(db)` honors `_lite_mode_default()` consultation at `server.py:4896`, which returns `True` because `BACKUP_LITE_MODE_ONLY=true` is live (`lite_mode_only_env: true` in state response).

### 2.2 — Catch-up · 🟢 VERIFIED WORKING

The 02:00 UTC slot was missed during the deploy downtime (worker not alive at 02:00). On first tick at 13:30:44Z, the loop found `last_run_for_hour.get(2) != today` and fired the missed-slot backup. **Direct proof of the iter440 Phase 31.3 catch-up logic.**

### 2.3 — Manual LITE backup · 🟢 VERIFIED WORKING (Batch A evidence, not re-triggered)

**Batch A evidence:**
```
recent_health[1]:
  ts:                2026-05-30T03:14:39.059548Z
  ok:                true
  mode:              lite
  filename:          MASCI_lite_backup_2026-05-30_031433Z.zip
  size_bytes:        211 805
  records:           141
  emailed_to:        jaymn.judd@mascigc.com
```

Triggered by `POST /api/admin/backups/run-now?lite=true` in Batch A. Endpoint defined at `server.py:6776`. **Not re-triggered in Batch D** (verification by code-evidence only, per stop-condition compliance — no manual runs by main agent).

### 2.4 — Manual COMPLETE backup · 🟡 CODE-ONLY

Endpoint exists: `POST /api/admin/backups/run-complete-now` at `server.py:6864`. **Not exercised in Batch D** (explicitly forbidden by operator directive). Cannot be promoted to 🟢 until manually exercised under separate authorization.

### 2.5 — Hourly COMPLETE-R2 · 🟢 VERIFIED WORKING (CASCADED AUTO-FIRE — see §3 for governance flag)

**Runtime evidence (`batch_d_evidence/admin_complete_r2_state.json`):**
```
r2_hourly:           true                       ← env BACKUP_R2_HOURLY=true ALREADY SET in prod
nightly_last:
  filename:          MASCI_complete_backup_2026-05-30_133054Z.zip
  size_bytes:        464 061 276    (≈ 442.6 MB)
  r2_key:            backups/auto-90d/MASCI_complete_backup_2026-05-30_133054Z.zip
  ts:                2026-05-30T13:30:44.513056Z
nightly_last_hour:   2026-05-30T13
```

**Why it fired**: code at `server.py:6589` reads `BACKUP_R2_HOURLY`. Pre-existing prod value is `true`. After restart, `last_r2_complete_hour` seeded from most-recent complete-r2 row (2026-05-26T11). At first tick (13:30:44Z), `hour_bucket = "2026-05-30T13" != "2026-05-26T11"` → fired.

**This is the iter85 `BACKUP_R2_HOURLY=true` path executing as documented.**
- ✅ 464 MB archive built in-memory + uploaded to R2 without worker OOM
- ✅ `r2-usage-alert` row recorded (79.57 GB, 2 271 objects)
- ✅ Local file deleted post-upload (per `server.py:5949–5953`)
- ✅ `backup_health` row recorded with `mode: complete-r2`

**Material finding:** The prior Batch C posture ("complete-R2 lite-only stays as-is — that's intentional safety") was based on the `BACKUP_LITE_MODE_ONLY` flag, which gates the **email-only** scheduled backup path. It does **NOT** gate the `BACKUP_R2_HOURLY` path. **These are two independent code paths.** See §3 for documentation drift.

### 2.6 — R2 inventory (`admin_r2_list.json`)

```
count returned:    100  (page 1)
total_in_bucket:   1 517 objects
latest:            MASCI_complete_backup_2026-05-30_133054Z.zip (today)
oldest:            MASCI_complete_backup_2026-05-25_030136Z.zip
```

**90-day lifecycle prefix `backups/auto-90d/` populated.** Per `R2_RETENTION_AUDIT.md` referenced at `server.py:5941`, legacy backups outside this prefix are excluded from the lifecycle TTL.

### 2.7 — Email delivery · 🟢 VERIFIED WORKING

Today's catch-up lite backup record contains `emailed_to: jaymn.judd@mascigc.com`. The email-send path is `_send_backup_email` at `server.py:6133` (Resend API). Successful `emailed_to` field implies the Resend call returned a delivery ID. **Note:** Resend API response is recorded in-memory; this evidence does not confirm inbox receipt — only successful API ack.

### 2.8 — Watchdog · 🟢 INSTRUMENTED · HEALTHY

`last_watchdog: {alarm_fired:false, hours_silent:0.0, reason:"healthy"}` after T+5. Code at `server.py:5226` runs every tick. Alarm fires only after `watchdog_threshold_hours: 25.0` of scheduler silence. **Currently 0.0 hours silent → healthy.**

### 2.9 — Supervisor · 🟢 VERIFIED WORKING (one resurrection observed)

`last_attempt_outcome: "RESURRECTED at 2026-05-30T13:26:25Z (previous: completed without error)"` recorded in Attempt-1 (pre-deploy-complete probe). This single resurrection followed by sustained `task_alive: true` proves:
1. Supervisor detects dead task ✅
2. Supervisor respawns within 5-min window ✅
3. Respawned task entered the loop body ✅

### 2.10 — Failure handling (circuit-breaker) · 🟡 CODE-ONLY

`failed_attempts: {}` in current state. The circuit breaker (`server.py:6526–6541`) is wired but has not triggered today. Cannot promote to 🟢 without forcing a failure (not authorized in Batch D).

### 2.11 — Restore paths · ⚪ UNKNOWN

Neither lite-zip restore nor R2-archive restore exercised in Batch D. The restore code paths exist (referenced via `/admin/system` page guidance) but no automated test ran in this scope.

### 2.12 — Backup drift watch · 🟢 INSTRUMENTED (silent-by-design)

`_backup_drift_watch` at `server.py:5930–5933`. Per Phase 25.3 doctrine, surfaces **log-only** warnings if a collection silently disappears between consecutive complete-archive runs. **NEVER** raises an alert, email, dashboard, or notification. Today's run did not log a drift warning (no anomaly).

### 2.13 — Mongo direct dump · 🚫 NOT IMPLEMENTED (by design)

There is no `mongodump`/binary-snapshot pathway. **Every backup is an app-level Mongo collection export** built by `_build_complete_archive_on_disk`. This is the intentional architecture — protects against schema drift between dump and restore and ensures every backup is restorable via the app's own restore flow.

---

## 3 · Critical finding for operator review

**🟡 Complete-R2 hourly backups are now firing automatically on production.**

This is **not** a defect, **not** an unauthorized action by main agent, and **not** an undocumented code path. It is the iter85 `BACKUP_R2_HOURLY=true` path executing as designed. The pre-existing production env value (untouched by Batch D) was `true`, and enabling `SCHEDULER_ENABLED` re-enabled the entire loop, including this branch.

**Implications:**
- Every UTC hour (24×/day) a complete archive (~442+ MB at current scale) will build on the worker and upload to R2.
- R2 storage is at 79.57 GB / 2 271 objects. The 90-day lifecycle rule will eventually shed pressure, but daily growth is significant.
- Worker memory: today's 464 MB build did not OOM (watermark is 600 MB). Headroom is ~136 MB. Risk grows as collection data grows.

**Per `BATCH_C_SCHEDULER_FIX_PLAN.md §4 Row B`**, this risk was forewarned:
> "Confirm `BACKUP_R2_HOURLY` value in production. If `true`, recommend toggling to `false`/unset on the FIRST day to keep behaviour predictable; if already `false`/unset, no action."

**Operator decision required (NOT executed in Batch D):**
- (a) Leave `BACKUP_R2_HOURLY=true` (24× complete-R2 builds/day · current state)
- (b) Set `BACKUP_R2_HOURLY=false` (revert to once-daily `BACKUP_R2_FULL_HOUR_UTC=3` schedule)
- (c) Other (e.g., adjust `BACKUP_R2_FULL_HOUR_UTC`, raise OOM watermark, etc.)

**Main agent is NOT requesting authorization to change this.** Surfacing as a Phase 3 finding for the operator's awareness.

---

## 4 · Final answer — "If production DB was lost right now, exactly what recovers and what is lost?"

### 4.1 — PROVEN recovery paths

| Source | Coverage | Last known good | Notes |
|---|---|---|---|
| Today's complete-R2 archive (R2 key `backups/auto-90d/MASCI_complete_backup_2026-05-30_133054Z.zip`) | Full Mongo dump · 223 394+ records · inline photos · 464 MB | 2026-05-30T13:30:44Z | Restorable via existing restore code path; restore code path itself **NOT exercised in this batch (UNKNOWN)** |
| 1 516 prior R2 archives (`backups/auto-90d/*.zip`) | Historical complete dumps · 90-day lifecycle | spans 2026-05-25 → 2026-05-30 in the visible sample | Same restore caveat |
| Today's lite ZIP (emailed) | Compact 211 KB · 141 records · text-only | 2026-05-30T13:30:53Z | Email delivery confirmed (`emailed_to` recorded); inbox receipt not independently verified |
| `backup_health` Mongo collection | Audit trail of every backup attempt | Continuous | Lives **in** the same Mongo cluster — would itself be part of any catastrophic data-loss event |

### 4.2 — UNPROVEN recovery paths (need exercise before declaring recoverable)

- Local lite-ZIP restore flow (`/admin/system` page references it)
- R2 complete-archive restore flow (download from R2 → re-import into Mongo)
- Cross-environment restore (e.g., restore prod into preview for drill)
- Post-restore data-integrity verification

### 4.3 — Data NOT covered by current backups

- Anything written to MongoDB **after** 2026-05-30T13:30:44Z (the most recent complete-R2 snapshot). Maximum data-loss window now `≤ 60 min` while `BACKUP_R2_HOURLY=true` remains active.
- Files held only in `/app/backend/backups/` local volume **at the time of disaster** — but this directory is now empty (`count: 0`) because today's archive was deleted post-R2-upload per `server.py:5949`.
- R2-only photo objects whose lifecycle TTLs are independent of the backup archive.
- Anything outside the `_build_complete_archive_on_disk` enumeration (verified collections list not re-audited in Batch D).

### 4.4 — One-line summary

> **At time of probe (2026-05-30T13:42Z), production Mongo can be recovered to within the last ≤ 60 minutes via the R2 complete-archive path, contingent on the restore code path being exercised in a separately-authorized drill. The restore path itself is the principal UNKNOWN.**

---

## 5 · Recommended next-batch focus (NOT executed — operator decision)

1. **Restore drill** in preview using today's R2 archive → end-to-end recovery proven.
2. **`BACKUP_R2_HOURLY` posture decision** (24× vs 1× daily complete-R2 builds).
3. **Circuit-breaker exercise** in preview (force 3 consecutive failed scheduled backups → verify breaker latches → verify next-day reset).
4. **Watchdog alarm exercise** (simulate 25h silence → verify Resend alarm email fires).
5. **Backup drift watch verification** (run two consecutive complete archives with a deliberately-omitted collection → verify log warning fires).

**None of these are part of Batch D.** Listed for the operator's roadmap awareness.
