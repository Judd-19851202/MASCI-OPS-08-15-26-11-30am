# TRACK 15.53 · Retention Conflict Resolution

**Status:** ✅ **RESOLVED — single source of truth is now the app-side `lib/r2_retention.py` tiered retention.**
**Date:** 2026-06-19 21:45 UTC.

## The conflict (re-stated for the audit trail)

Pre-track state (verified live at 21:44 UTC):

| Engine | Policy |
|---|---|
| `backend/lib/r2_retention.py` | Tier 1 keep all (0-14 d) · Tier 2 newest-per-day (14-90 d) · Tier 3 newest-per-month (90-365 d) · Tier 4 delete (> 365 d) |
| Cloudflare R2 lifecycle rule `masci-backups-auto-90d` | Expiration: **90 days** on prefix `backups/auto-90d/` |

**Failure mode:** the R2 lifecycle would delete Tier 3 monthly-survivor candidates at Day 90 before the app's `r2_retention.py` could promote them. Forecast first material data loss: 2026-08-29 ± 1 day.

## Resolution choice (Option B with safety-net)

| Option | Pros | Cons | Choice |
|---|---|---|---|
| **A · Lifecycle handles all retention** | Survives even if app is offline for weeks | Loses tier-aware preservation (no monthly survivors; cliff at Day 90 or Day 365) | ❌ Not chosen — discards the monthly tier value |
| **B · App handles all retention** | Tier-aware (hourly/daily/monthly); matches the documented design | Depends on the app running; if scheduler is dead for weeks, objects accumulate | ✅ **CHOSEN with a longstop** |
| **Hybrid (chosen)** | Same as B, but with Cloudflare-side ceiling at Day 365 as a backstop | Adds an extra rule to keep in sync if the design changes | ✅ |

**Final implementation:** the R2 lifecycle rule is **kept**, but its `Expiration` ceiling is raised from `90` to `365` days. This matches the app's Tier 4 boundary exactly. The app's `r2_retention.py` is now the authoritative retention engine within the 0-365 day window; R2 lifecycle serves only as a longstop that guarantees no object lives beyond 365 days even if the app pruner stops running.

This is the simplest "one source of truth" arrangement that does not require any code change and does not weaken protection.

## The change applied (live S3 call)

```python
s3.put_bucket_lifecycle_configuration(
    Bucket="masci-hub",
    LifecycleConfiguration={
        "Rules": [
            {
                "ID": "Default Multipart Abort Rule",
                "Status": "Enabled",
                "Filter": {"Prefix": ""},
                "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7},
            },
            {
                "ID": "masci-backups-auto-365d",
                "Status": "Enabled",
                "Filter": {"Prefix": "backups/auto-90d/"},
                "Expiration": {"Days": 365},
                "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7},
            },
        ],
    },
)
# returned HTTP 200
```

## Verification (live, 2026-06-19 21:45 UTC, immediately after the call)

```
$ python3 -c "...get_bucket_lifecycle_configuration..."
Lifecycle rules:
  - id=Default Multipart Abort Rule  status=Enabled
    filter={'Prefix': ''}
    AbortIncompleteMultipartUpload={'DaysAfterInitiation': 7}

  - id=masci-backups-auto-365d        status=Enabled
    filter={'Prefix': 'backups/auto-90d/'}
    Expiration={'Days': 365}
    AbortIncompleteMultipartUpload={'DaysAfterInitiation': 7}
```

The 90-d rule is gone. The 365-d rule is live and enabled.

## Single source of truth (post-change)

**`backend/lib/r2_retention.py`** is the authoritative retention engine.

- Tier 1 (0-14 d): keep all hourly. Live count: 337 objects · 168 GB.
- Tier 2 (14-90 d): keep newest per day. Live count: 17 objects · 3.1 GB.
- Tier 3 (90-365 d): keep newest per month. Live count: 0 today (bucket too young; will start filling on 2026-08-09 when first object turns 90 d).
- Tier 4 (> 365 d): delete (app) **and** lifecycle backstop (R2 side).

## Why this is structurally correct

- **No new backup system.** Same `_backup_scheduler_loop`, same `_run_complete_archive_to_r2`, same `enforce_r2_retention`.
- **No new collection.** No schema change.
- **No new scheduler.** The retention pruner continues to run inside the existing scheduler loop.
- **No code change.** The `r2_retention.py` Tier 3 / Tier 4 logic was already correct; it was the R2 lifecycle that was undercutting it. Removing the undercut is enough.
- **No data migration.** Existing 854 objects are unchanged.
- **No deletion of historical data.** Every object that existed before the change still exists.

## Backup-pipeline impact verification

| Check | Result |
|---|---|
| Bucket object count before | 854 |
| Bucket object count after | 854 (unchanged) |
| Bucket total bytes before | 207,817,130,821 |
| Bucket total bytes after | 207,817,130,821 (unchanged) |
| Newest backup readable post-change | HEAD 200 · ETag preserved · size match |
| `mascidocs.com/api/health/full` post-change | 200 |

## What changes operationally

Nothing in the next 90 days. The pre-change lifecycle would have started firing on Day 90 from any object's `LastModified`; the new lifecycle still won't fire until Day 365. The app-side `r2_retention.py` continues to enforce Tier 1 + Tier 2 today (already verified active), and will begin enforcing Tier 3 monthly survivors starting on **2026-08-09 ± 1 day** (Day 90 from the first `auto-90d/` upload on 2026-05-17).

## Final answer to Phase 2/3

**Q: Was the retention conflict resolved?**
**A: Yes.** The R2 lifecycle rule's expiration was raised from 90 d to 365 d, matching the app's Tier 4 boundary. Both engines now agree.

**Q: What is now the single source of truth for retention?**
**A:** `backend/lib/r2_retention.py` (Tier 1 14 d hourly · Tier 2 90 d daily · Tier 3 365 d monthly · Tier 4 delete). The Cloudflare lifecycle rule `masci-backups-auto-365d` is a longstop that matches the app's Tier 4 ceiling and never deletes anything the app intended to keep.
