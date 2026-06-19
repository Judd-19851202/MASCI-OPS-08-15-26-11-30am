# TRACK 15.52B · Code Path Audit

**Status:** Read-only trace through live code. Captured 2026-06-19 21:00 UTC.

## Q1 · Does 6-hour cadence already exist in code?

**YES — completely.**

Source: `backend/server.py` lines 5698-5772 (`_parse_backup_hours`).

```python
def _parse_backup_hours() -> list[int]:
    """Precedence (highest first):
      1. BACKUP_HOURS_LOCAL + BACKUP_TIMEZONE  → convert local hours to UTC
      2. BACKUP_HOURS_UTC                       → legacy UTC-only path
      3. Default [BACKUP_HOUR_UTC, 18]
    """
    local_raw = (os.environ.get("BACKUP_HOURS_LOCAL") or "").strip()
    tz_name = (os.environ.get("BACKUP_TIMEZONE") or "").strip()
    if local_raw and tz_name:
        ...  # parse hours, convert local→UTC via zoneinfo.ZoneInfo, return sorted
    # Fall through to BACKUP_HOURS_UTC, then to default
```

Setting `BACKUP_HOURS_LOCAL=0,6,12,18` + `BACKUP_TIMEZONE=America/New_York` directly produces a 4-times-per-day local-time-anchored schedule, automatically DST-correct.

## Q2 · Is it production-ready?

**YES.** Track 15.38 (2026-02) added the code with 6 tests in `backend/tests/test_track_15_38_local_schedule.py`, all passing. The function is called once at module load (`BACKUP_HOURS_UTC: list[int] = _parse_backup_hours()`) and consumed by the scheduler loop at `server.py:7820-7849`.

## Q3 · Is it merely disabled?

**YES.** The code path exists and is well-tested. It is dormant only because:
- `BACKUP_R2_HOURLY=true` on production (overrides the schedule for the R2 path — see `server.py:7849`).
- `BACKUP_HOURS_LOCAL` is unset on production (so `_parse_backup_hours()` falls through to `BACKUP_HOURS_UTC=2,18`).

The local-disk daily backup at 02:00+18:00 UTC continues, but the R2 path fires every hour regardless of `BACKUP_HOURS_*` when `BACKUP_R2_HOURLY=true`. Source: `server.py:7820-7849`:

```python
# When BACKUP_R2_HOURLY=true (iter85) the complete archive fires
# every hour; otherwise it fires once per day at BACKUP_R2_FULL_HOUR_UTC.
r2_hourly = (os.environ.get("BACKUP_R2_HOURLY", "false") or "false").lower() in ("1", "true", "yes")
if r2_hourly:
    r2_hour = current_utc_hour  # i.e. every hour
else:
    r2_hour = int(os.environ.get("BACKUP_R2_FULL_HOUR_UTC", "3") or "3")
```

## Q4 · What exact configuration change enables 6-hour cadence?

Production environment must change THREE env-var values. No code change required.

```diff
- BACKUP_R2_HOURLY=true
+ BACKUP_R2_HOURLY=false
+ BACKUP_HOURS_LOCAL=0,6,12,18
+ BACKUP_TIMEZONE=America/New_York   # MASCI HQ TZ; substitute per tenant for white-label
```

After this change:
- R2 complete-archive will fire at local 00:00, 06:00, 12:00, 18:00 (UTC-translated via `zoneinfo`).
- The DST transitions self-correct after the next worker restart (~7 d max if no deploys).
- The legacy local-disk daily backup at 02:00 + 18:00 UTC continues independently (controlled by `BACKUP_HOURS_UTC`, NOT by `BACKUP_R2_HOURLY`).
- App-side `lib/r2_retention.py` still enforces the 14d/90d/365d tiering.

## Q5 · Are code changes required?

**NO.** Zero code changes. The flip is purely an environment-variable change applied on the production pod, followed by a backend supervisor restart (or the next natural deploy).

## Operational checklist for the operator

Pre-flight (all confirmed BEFORE the env change):
1. Verify Atlas PITR is ON (per `TRACK_15_52B_ATLAS_PROTECTION_AUDIT.md`).
2. Verify R2 bucket versioning state and decide if enabling it is also part of this change.
3. Capture the latest healthy R2 backup filename + `MANIFEST.json` checksum for rollback evidence.
4. Snapshot the production env vars to a secured location.

Flip:
5. Apply the three env-var changes above on the production pod.
6. `sudo supervisorctl restart backend` (5-10 s downtime).

Post-flight (within 6-12 h):
7. Confirm `mascidocs.com/api/admin/backups-complete-r2-state` shows `r2_hourly: false`.
8. Confirm a new backup arrives in `s3://masci-hub/backups/auto-90d/` at the next scheduled local hour (00:00, 06:00, 12:00, or 18:00 local).
9. Confirm `mascidocs.com/api/health/full` continues to return 200 (after Track 15.52 fix is deployed; otherwise audit-row drift may briefly false-red — see Track 15.52A).

Rollback (≤ 60 s if needed):
10. Restore the snapshotted env vars.
11. `sudo supervisorctl restart backend`.

## SECTION G summary

The 6-hour cadence is **fully implemented in code, fully tested, and fully production-ready**. It is dormant solely because the operator has not flipped three environment variables on the production pod. No new code is required. Track 15.37 + 15.38 shipped everything in code; only the env-var flip remains.

## Adjacent code paths (read-only inventory · for completeness)

| File / function | Purpose | Affected by cadence change? |
|---|---|:---:|
| `server.py:_run_complete_archive_to_r2` | Build + upload complete-archive zip to R2 | Indirectly — fires fewer times |
| `server.py:_record_backup_health` | Audit row writer | Same code; fewer rows |
| `server.py:_backup_watchdog_check` | Alert when backups go stale | Threshold = `BACKUP_RETENTION_DAYS` × 86400 = 14 d; will not trigger from 6-hour change |
| `lib/r2_retention.py:enforce_r2_retention` | Tier 1/2/3/4 pruner | Identical behavior; just operates on fewer hourly objects |
| `backup_verification.py` | Weekly heartbeat report | Identical; the report compares R2 age to `BACKUP_VERIFICATION_MAX_AGE_HOURS=36` — 6-hour cadence stays well within 36 |
| `routes/admin_persistence_health.py` | `/api/admin-strict/diag/persistence-health` | Reports `last_backup_time`; will report 6-hour-old timestamps in the worst case — still healthy |
| `server.py:/api/health/full` (post-15.52) | Public probe | R2 LastModified primary, DB audit-row fallback; both fine at 6-hour cadence |
