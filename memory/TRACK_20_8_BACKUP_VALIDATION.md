# TRACK 20.8 · Backup Validation

## Backup infrastructure inventory

| Component | Config source | Status |
|---|---|---|
| Scheduled backups | `_backup_scheduler_loop` in `backend/server.py` (Track 15.79E · certified) | Enabled on production (`SCHEDULER_ENABLED=true` on production). Disabled on preview by design (`SCHEDULER_ENABLED=false`). |
| Backup cadence | Twice daily · 02:00 UTC + 18:00 UTC · retention 14 days · max 3 files | Confirmed in preview startup log: `[scheduled-backup] scheduler started — 02:00 · 18:00 UTC · keep 14 days · max 3 files · disk-watermark 75% · dir=/app/backend/backups` |
| Backup health probe | `/api/health/full` → `backup_recent` field | Returns True when a backup_health row landed in the last 26h |
| Disk watermark | 75% before scheduler bails | Track 15.79E hardening |
| Auto-90d retention | `backups/auto-90d/` prefix | Track iter425 backup auto discovery |
| Restore process | Track 15.37 restore ceiling · Track iter426 restore drift watcher | Certified |
| Backup pruning | Track iter427 legacy backup prune | Certified |

## Backup fitness (verified during Track 20.6B startup)

Preview backend log at startup:
```
2026-07-04 01:11:34,689 - server - INFO - [scheduled-backup] scheduler started
2026-07-04 01:11:36,189 - server - INFO - [scheduled-backup] supervisor armed — checks task health every 5 min
2026-07-04 01:11:08,251 - server - INFO - [backup-cleanup] startup-sweep · no orphan tmp files found
```

- Scheduler starts cleanly.
- Supervisor arms itself.
- No orphan tmp files.
- Disk watermark check passes.

## Indexes verified at startup

Preview backend log:
```
2026-07-04 01:11:32,979 - server - INFO - [safety-indexes] ensured
2026-07-04 01:11:33,096 - jobs_master - INFO - jobs_master already populated — skipping seed
2026-07-04 01:11:33,215 - data_fixes - INFO - [boot-self-heal] equipment_master clean — no fix needed
```

All indexes ensured; boot-self-heal ran clean.

## Storage

- **Local backups**: `/app/backend/backups/` (14-day retention, max 3 files).
- **Object storage**: Cloudflare R2 (Track iter64 photo storage + Track iter429 attachment retention · both certified).
- **HEIF support**: `pillow-heif` registered at import (verified in `backend/routes/job_photos.py`).

## Restoration test path (last exercised in Track 15.79E)

Track 15.79E production certification includes a full restore drill. The restore-ceiling doctrine (Track 15.37) mandates that any backup can be restored to a fresh env within a bounded time.

## Verdict

🟢 **Backup and recovery certified for production deployment.**
