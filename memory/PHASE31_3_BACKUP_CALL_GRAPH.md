# Phase 31.3 · Backup Call Graph
## iter440 · 2026-05-26

> Every code path capable of producing a `MASCI_complete_backup_*.zip`
> in R2. Mapped from `backend/server.py` source.

---

## Producers

### 1 · Scheduled (the production path)
```
@app.on_event("startup")  ─ runs ONCE per worker boot
└── _backup_scheduler_loop(db)                                  server.py:6328
    ├── (at startup) read backup_health for staleness · log
    ├── (iter440 fix) seed _BACKUP_SCHEDULER_STATE from backup_health
    ├── await asyncio.sleep(30)                                 (startup grace)
    └── while True:                                             (tick every 5 min)
        ├── if BACKUP_R2_HOURLY=true:
        │     hour_bucket = now.strftime("%Y-%m-%dT%H")
        │     should_fire_r2 = state.last_r2_complete_hour != hour_bucket
        │     if should_fire_r2:
        │         await _run_complete_archive_to_r2(db)         server.py:5923
        │         state.last_r2_complete_hour = hour_bucket
        ├── else (legacy daily mode):
        │     should_fire_r2 = (now.hour >= BACKUP_R2_FULL_HOUR_UTC
        │                       AND state.last_r2_complete_date != today)
        │     [same _run_complete_archive_to_r2 call]
        ├── await _backup_watchdog_check(db)                    (logs only)
        ├── await _maybe_send_weekly_variance_email()           (independent)
        └── await asyncio.sleep(300)                            (5 min)
```

### 2 · Manual admin trigger
```
POST /api/admin/backups-complete-r2-trigger                     server.py:6759
└── require_admin_strict  (admin token gate)
    └── _run_complete_archive_to_r2(db)
```

### 3 · Watchdog (read-only, NEVER produces archives)
```
_backup_watchdog_check(db)                                      server.py:5292
└── reads backup_health
└── (rate-limited) sends an alarm email IF backups silent past threshold
└── NEVER calls _run_complete_archive_to_r2
```

---

## Single archive producer — `_run_complete_archive_to_r2(db)`
```
server.py:5923
├── (skip if R2 not configured)
├── BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
├── filename = f"MASCI_complete_backup_{stamp}.zip"
├── tmp = out.with_suffix(f".zip.tmp.{uuid.uuid4().hex[:8]}")
├── stats = asyncio.to_thread(_build_complete_archive_on_disk, db, tmp)
│   (synchronous · streams Mongo collections to zip · inlines photos · applies redactions)
├── tmp.replace(out)                            (atomic rename)
├── try: _backup_drift_watch(db, stats)         (writes backup_drift_history snapshot)
│   except: log warning, continue
├── r2_key = "backups/auto-90d/" + filename
├── await upload_local_file(out, key=r2_key, content_type="application/zip")
├── presigned_get_url_for_key(r2_key, ttl=7 days)
├── out.unlink()                                (delete local copy)
├── _record_backup_health(db, ok=True, mode="complete-r2", filename, size_bytes, records)
└── asyncio.create_task(_log_r2_usage_warning())  (background usage probe)

EXCEPTION PATH (any uncaught error above):
├── tmp.unlink() if exists
├── _record_backup_health(db, ok=False, mode="complete-r2-error", error=repr(e))
└── return None
```

---

## Health/status surfaces (READ-only · NEVER produce archives)

| Endpoint                                                       | Reads          | Function                |
| -------------------------------------------------------------- | -------------- | ----------------------- |
| `GET /api/admin-strict/diag/persistence-health`                | `backup_health` + `backup_drift_history`  | Atlas + backup status snapshot |
| `GET /api/admin-strict/diag/production-health`                 | (HTTP probes only) | Production smoke vs preview |
| `GET /api/admin/system-health`                                 | `backup_health` | Banner card on `/admin/system` |
| `GET /api/admin/digest/weekly?format={text\|json}`             | `backup_health` + `backup_drift_history` | Weekly operator digest |
| `GET /api/admin/backups-list-r2`                               | R2 list_objects_v2 (paginated · iter440 fix) | Backup archive inventory |
| `GET /api/admin/backups`                                       | local disk     | List local zips |
| `GET /api/admin/deploy-recovery`                               | `backup_health` | Recent successful backups |

None of these can produce a new archive.

---

## State storage

### In-memory (process-local, wiped on every reload)
```
_BACKUP_SCHEDULER_STATE: dict  (server.py:6281)
  ├── last_r2_complete_hour   : "YYYY-MM-DDTHH"
  ├── last_r2_complete_date   : "YYYY-MM-DD"
  ├── last_r2_complete        : { filename, size_bytes, r2_key, ts }
  ├── last_tick_ts            : ISO timestamp
  └── last_watchdog           : { status, ts, ... }
```

iter440 · Phase 31.3 · After startup, this dict is **seeded from
Mongo** so a reload doesn't wipe the hour-bucket bookkeeping.

### Mongo-persistent
```
backup_health           · every run logs a row (200 max, FIFO)
backup_drift_history    · every successful complete-r2 logs a snapshot (30 max)
```

---

## Conclusion

* Single producer code path: `_run_complete_archive_to_r2` (server.py:5923).
* Single trigger code path: `_backup_scheduler_loop` (server.py:6328).
* Pre-fix state-volatility caused multi-fire-per-hour on every reload.
* Post-fix state-seed prevents this regression.
* No recursive triggers, no retry loops, no orphan callsites.
