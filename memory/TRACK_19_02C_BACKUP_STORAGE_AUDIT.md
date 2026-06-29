# Track 19.02C · Backup Storage Audit

## Local backup directory

Path: `/app/backend/backups`
Total size (before & after this track): **7.9 MB** (unchanged — no cleanup needed)

| Filename | Size | Date |
| --- | ---: | --- |
| MASCI_lite_backup_2026-06-16_024648Z.zip | 1.98 MB | 2026-06-16 02:46 UTC |
| MASCI_lite_backup_2026-06-16_024749Z.zip | 1.98 MB | 2026-06-16 02:47 UTC |
| MASCI_lite_backup_2026-06-16_104632Z.zip | 2.11 MB | 2026-06-16 10:46 UTC |
| MASCI_lite_backup_2026-06-16_104735Z.zip | 2.13 MB | 2026-06-16 10:47 UTC |

## Retention policy (from `/app/backend/server.py`)

```
BACKUP_KEEP_MAX     = 3   (default; env: BACKUP_KEEP_MAX)
BACKUP_RETENTION_DAYS = (also env-configurable)
```

The scheduled backup runner prunes to `BACKUP_KEEP_MAX - 1 = 2` newest
backups when triggered, leaving room for the next one to land within the
cap. The current state (4 files) is within the emergency-prune band but
not over it — these are all from a single capture session two weeks ago
and total under 8 MB. **No prune required.**

## Emergency prune behavior verified

The "emergency prune" code path (server.py line 5837) kicks in only
when a new backup write fails due to disk watermark. With /app now at
**57% utilization** post-cleanup, the watermark is far from triggering
emergency prune.

## R2 / Atlas integrity

* Atlas: production MongoDB lives off-platform; backups are managed by
  Atlas snapshot policy. Nothing on this filesystem references Atlas
  internals.
* R2 references: backend `services/` and `scripts/` were grepped for
  `R2_BUCKET` / `cloudflare` — no live R2 sync detected on this preview
  environment.

## Conclusions

* Backup directory is not the disk-pressure root cause.
* Retention policy already correct.
* No backup files were deleted by this track.
