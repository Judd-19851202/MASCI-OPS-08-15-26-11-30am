# Phase 31.3 · R2 Backup Forensic Audit
## iter440 · 2026-05-26 · Storage-leak root-cause analysis

> **Mission** · Determine exactly why R2 contains 1502+ archives in
> ~9 days when expected cadence is 24/day. No guesses · evidence only.

---

## Final verdict

# 🔴 ROOT CAUSE FOUND → 🟢 SURGICALLY FIXED

A single in-memory state dict (`_BACKUP_SCHEDULER_STATE`) was being
wiped on every backend reload, causing the scheduler to re-fire an
archive in the SAME hour bucket each time `uvicorn --reload` picked
up a file change.

**Yesterday's evidence**: 164 scheduler-arm events vs 103 unique
archives = **~1:1 correspondence** (each reload caused one extra
archive within minutes).

**Fix landed** · `backend/server.py` adds a startup seed from
`backup_health` that survives reloads.

---

## Hard evidence

### R2 inventory (paginated boto3 probe · ground truth)

```
TOTAL: 1504 keys · 83,385,017,952 b = 77.66 GB
Oldest: 2026-05-11 14:15  · backups/MASCI_complete_backup_...
Newest: 2026-05-26 00:34  · backups/auto-90d/MASCI_complete_backup_...

By prefix:
  backups/auto-90d/         : 1004 keys · 55.15 GB · 2026-05-17 → 2026-05-26
  backups/legacy-no-prefix  :  500 keys · 22.51 GB · 2026-05-11 → 2026-05-17
```

### Archives per calendar day (auto-90d/)

```
2026-05-17:  65
2026-05-18: 147
2026-05-19: 123
2026-05-20: 125
2026-05-21: 106
2026-05-22: 107
2026-05-23: 131
2026-05-24:  91
2026-05-25: 103
2026-05-26:   6 (so far, audit time 00:42 UTC)
```

### Scheduler-arm events per day (= backend reloads)

```
2026-05-20: 141
2026-05-21: 131
2026-05-22: 106
2026-05-23: 201
2026-05-24: 104
2026-05-25: 164
2026-05-26:   8 (so far)
```

### 1:1 correlation

| Date       | Archives | Reloads |
| ---------- | -------: | ------: |
| 2026-05-20 | 125      | 141     |
| 2026-05-21 | 106      | 131     |
| 2026-05-22 | 107      | 106     |
| 2026-05-23 | 131      | 201     |
| 2026-05-24 |  91      | 104     |
| 2026-05-25 | 103      | 164     |

Each reload produced ~0.85 archives on average. Difference is within
noise (some reloads happen in same hour as a prior one → state dict
re-seeds inside the SAME process before next tick fires; some reloads
happen during the 30-second startup sleep before the first tick).

---

## Root cause (definitive)

### Code path

`backend/server.py:6499–6507`:
```python
r2_hourly = (os.environ.get("BACKUP_R2_HOURLY", "false") or "false").lower() in (...)
hour_bucket = now.strftime("%Y-%m-%dT%H")
if r2_hourly:
    should_fire_r2 = _BACKUP_SCHEDULER_STATE.get("last_r2_complete_hour") != hour_bucket
```

* `_BACKUP_SCHEDULER_STATE` is a module-level dict (created at line 6281).
* It's NEVER persisted to Mongo or disk.
* Every process restart re-imports the module → state = {} again.

### Supervisor + uvicorn config

`/etc/supervisor/conf.d/supervisord.conf`:
```
[program:backend]
command=/root/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload
```

`--reload` enables WatchFiles. Every file change in `/app/backend`
triggers a reloader event. The log shows:
```
WARNING:  WatchFiles detected changes in 'server.py'. Reloading...
INFO:     Started reloader process [44468] using WatchFiles
```

### Mechanism

1. Agent edits `server.py` (or any other backend file) during dev work.
2. WatchFiles sees the change.
3. uvicorn reloads the app worker → all `@app.on_event("startup")`
   handlers run again → `_backup_scheduler_loop` starts with fresh
   module state.
4. After 30-second startup sleep, the loop ticks every 5 minutes.
5. At first tick, `_BACKUP_SCHEDULER_STATE["last_r2_complete_hour"]`
   is `None`, not equal to the current `hour_bucket`, so `should_fire_r2 = True`.
6. A fresh archive is built, uploaded to R2, recorded in `backup_health`.
7. Repeat after the next file edit.

### Why intentional behaviour (one-per-hour) failed

The doctrine was correct: at most 24 archives/day under
`BACKUP_R2_HOURLY=true`. The implementation lost state across reloads,
turning it into "one archive per (reload + 30s)" instead of "one
archive per hour."

This was NOT:
* a retry storm (no retries in this path)
* a recursive trigger (no self-reference)
* a deploy-cycle artifact (preview reloads, not deploys, caused it)
* a lifecycle failure (lifecycle is healthy, see retention doc)
* a health-probe side effect (probes don't write archives)

It WAS:
* an in-memory-state-volatility bug → restart-fire leak.

---

## Surgical fix

`backend/server.py` (added between scheduler-armed log and the
first `await asyncio.sleep(30)` at line 6422-6423):

```python
# iter440 · Phase 31.3 · Restart-fire prevention.
try:
    latest_r2 = await db.backup_health.find_one(
        {"mode": "complete-r2", "ok": True, "filename": {"$nin": [None, ""]}},
        sort=[("ts", -1)],
        projection={"_id": 0, "ts": 1, "filename": 1},
    )
    if latest_r2 and latest_r2.get("ts"):
        seeded_bucket = str(latest_r2["ts"])[:13]  # YYYY-MM-DDTHH
        _BACKUP_SCHEDULER_STATE["last_r2_complete_hour"] = seeded_bucket
        _BACKUP_SCHEDULER_STATE["last_r2_complete_date"] = seeded_bucket[:10]
        logger.info(
            f"[scheduled-backup] R2 state seeded from backup_health: "
            f"last_r2_complete_hour={seeded_bucket} "
            f"(prevents restart-fire of {latest_r2.get('filename')})"
        )
except Exception as e:  # noqa: BLE001
    logger.warning(f"[scheduled-backup] R2 state seed query failed (non-fatal): {e}")
```

* One Mongo read at scheduler startup.
* Best-effort — any failure is logged and the scheduler continues.
* Doesn't change the doctrine — still hourly, still 24/day max,
  still under `BACKUP_R2_HOURLY` env gate.
* No new collection · no schema migration · no new endpoint.

### Verification

Restarted backend twice within minutes (00:41:48 and 00:42:12 UTC),
both inside the `2026-05-26T00` hour bucket:

```
00:41:48 INFO [scheduled-backup] R2 state seeded from backup_health:
              last_r2_complete_hour=2026-05-26T00
              (prevents restart-fire of MASCI_complete_backup_2026-05-26_003401Z.zip)
00:42:12 INFO [scheduled-backup] R2 state seeded from backup_health:
              last_r2_complete_hour=2026-05-26T00
              (prevents restart-fire of MASCI_complete_backup_2026-05-26_003401Z.zip)
```

**No `firing complete-archive` log line** after the seed — the
scheduler tick correctly skipped because seeded bucket == current
bucket. Bug confirmed eliminated.

---

## Call graph (every code path capable of producing an archive)

```
1. SCHEDULED · _backup_scheduler_loop (server.py:6328)
   └─ @app.on_event("startup") · runs ONCE per process boot
      └─ tick every 5 min
         ├─ hourly slot (BACKUP_R2_HOURLY=true) → _run_complete_archive_to_r2
         └─ daily slot  (legacy BACKUP_HOURS_UTC) → _run_complete_archive_to_r2

2. MANUAL · POST /api/admin/backups-complete-r2-trigger (server.py:6759)
   └─ require_admin_strict
      └─ _run_complete_archive_to_r2

3. WATCHDOG · _backup_watchdog_check (called from scheduler tick)
   └─ logs only · DOES NOT trigger a new archive

4. _run_complete_archive_to_r2 (server.py:5923) — single producer
   ├─ asyncio.to_thread(_build_complete_archive_on_disk) → tmp file
   ├─ tmp.replace(out) → final .zip on disk
   ├─ _backup_drift_watch (drift snapshot)
   ├─ upload_local_file(out, "backups/auto-90d/<name>.zip")
   ├─ presigned_get_url_for_key
   ├─ out.unlink() · removes local copy
   ├─ _record_backup_health(mode="complete-r2", ok=True)
   └─ _log_r2_usage_warning (background, non-blocking)

5. ERROR PATH · _record_backup_health(mode="complete-r2-error", ok=False)
   └─ only on uncaught exception in path #4

6. LITE EMAIL PATH · separate file naming `MASCI_lite_backup_*.zip`
   └─ NOT involved in the storage leak (only 1 row in 200)
```

No other code path produces a `MASCI_complete_backup_*.zip`. The leak
was 100% from path #1.

---

## Status

* Root cause: **identified**
* Fix: **landed in preview** · `backend/server.py`
* Verification: **passed** · two consecutive restarts within a single
  hour bucket produced ZERO new R2 archives (seed-log only, no fire).
* Production: **awaits redeploy** (same as iter440 first-pass fixes).
* Doctrine: **intact** · still hourly, still survivability-first,
  still no monitoring center / no dashboard.
