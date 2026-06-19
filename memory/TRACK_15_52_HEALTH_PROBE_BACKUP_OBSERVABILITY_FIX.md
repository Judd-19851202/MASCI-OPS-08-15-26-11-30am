# TRACK 15.52 · Health Probe Backup-Observability Fix

**Status:** ✅ FIXED · `/api/health/full` now reports the real R2 backup state.
**Date:** 2026-06-19.
**Files touched:** `backend/server.py` only · ~70 lines net · no schema changes · no new collections · no new scheduler.

## Problem statement (verbatim from operator)

> Production-health-probe was failing intermittently and GitHub Actions was sending failure-notification emails — but R2 backups were demonstrably healthy (the latest snapshot was 17 minutes old at the time of certification). The false-red came from `/api/health/full` reporting `backup_recent=false` even when R2 had a fresh upload.

## Root cause

`/api/health/full` derives `backup_recent` by querying the in-DB audit collection:

```python
db.backup_health.find_one({"ok": True}, sort=[("ts", -1)])
```

But the in-DB audit row can drift stale even when R2 backups succeed, for at least three reasons we observed today:

1. **Multi-environment R2 sharing.** The R2 bucket (`masci-hub`) is shared across `APP_ENV=preview` and `APP_ENV=production`. The preview pod's hourly loop fired only 9 `complete-r2` audit rows in its lifetime, while the same bucket holds 855 backups (the rest from the production worker). Preview's `backup_health.find_one({ok:true})` returned 2026-06-16, even though R2 itself had a backup at 2026-06-19 20:04 UTC (~17 min old).
2. **Worker restart between audit + upload.** If the worker is recycled (rolling deploy, supervisor restart, scheduler watchdog respawn) between `_run_complete_archive_to_r2` finishing the upload and `_record_backup_health(mode="complete-r2", ok=True)` writing the audit row, the audit silently never lands.
3. **Audit-write transient failure.** `_record_backup_health` swallows exceptions by design (it's best-effort), so a transient Atlas write timeout drops the audit row without surfacing.

Meanwhile UptimeRobot and `scripts/predeploy_certify.sh` both treat `/api/health/full` as the truth source. A 503 from this endpoint is what triggered the alert email + blocked the predeploy gate.

## Canonical truth source

`/api/admin/backups-list-r2` (line 8096) lists R2 directly via `photo_storage._client` paginator. It is the source of truth ALL other paths agree on — the admin UI, the operator console, and (now) the health probe.

## The fix

Add `_r2_backup_age_seconds_cached()` that:
- Uses the same paginator pattern as `/api/admin/backups-list-r2` against the `backups/` prefix.
- Computes age of newest object via `LastModified`.
- Caches the result in-process for 5 minutes (`_R2_BACKUP_AGE_CACHE`) so the anonymous probe stays cheap.
- Returns `None` only on infrastructure failure (R2 unreachable, no creds) — a real outage with no recent backup returns a large number that still trips the 26h staleness check.

`/api/health/full` now consults R2 first via the helper, and falls back to `db.backup_health` only when R2 itself can't be reached. The 26-hour staleness window and the boolean contract are unchanged.

```python
backup_age_s = await _r2_backup_age_seconds_cached()
if backup_age_s is not None:
    out["backup_recent"] = backup_age_s < (26 * 3600)
else:
    # Fallback to DB audit row (existing logic).
    ...
```

## Hard-rule compliance

- ✅ **No new backup system.** Reads the existing R2 bucket via the existing `photo_storage` client.
- ✅ **No new scheduler.** Cache is lazy; first call after TTL expires triggers a single bucket-list.
- ✅ **No new collections.** Cache is process-local `dict`.
- ✅ **Did not weaken health checks.** Stale R2 (no backup in 26h) still returns `backup_recent=false` → 503. Fallback to DB audit row preserves prior behavior when R2 is unreachable. Both paths apply the same 26h SLO.
- ✅ **Did not hide real backup failures.** Verified by the stale-bucket simulation (see PRODUCTION_HEALTH_PROBE_CERTIFICATION.md §4).
- ✅ **Fixed the false-negative only.** Schema unchanged. Contract test (`test_iter183_health_full_endpoint.py`) still passes 3/3.

## Files changed

`/app/backend/server.py`:
- Inserted `_r2_backup_age_seconds_cached()` helper above `/api/health/full` route.
- Modified the `backup_recent` branch in `api_health_full` to consult R2 first.
- Added a header comment explaining the precedence rule and the fallback.

No other files touched. No env vars added. No supervisor changes.

## Verification (captured 2026-06-19 20:39 – 20:40 UTC after backend restart)

| Test | Before fix | After fix |
|---|---|---|
| `GET /api/health/full` HTTP code | 503 | **200** |
| `backup_recent` boolean | `false` | **`true`** |
| `ok` boolean | `false` | **`true`** |
| Stale-R2 simulation (age = 27 h) | n/a | `ok:false · backup_recent:false · 503` ✅ |
| Fresh-R2 simulation (age = 30 min) | n/a | `ok:true · backup_recent:true · 200` ✅ |
| Contract test `test_iter183_health_full_endpoint.py` | n/a (pre-fix endpoint failed contract) | **3/3 PASS** |
| Latency cold / warm | n/a | 0.142 s / 0.156 – 0.163 s |

## Production-health-probe workflow

`/.github/workflows/production-health-probe.yml` and `tools/verify-production.sh` were inspected — neither probes `/api/health/full` directly (they probe `/api/health` and `/api/admin-strict/diag/persistence-health`). The false-alert path is via:
- **UptimeRobot** → `/api/health/full` → email on 503
- **`scripts/predeploy_certify.sh` Phase 1** → `/api/health/full` → blocks deploy on non-200

Both paths see the same 200 now and both stop alerting.

## What was deliberately NOT done

- Did **not** rewrite the hourly R2 upload path. The fix is observability-side only; the underlying backup engine works (855 zips in bucket, hourly cadence proven).
- Did **not** plumb every audit-row write through retry/transactional logic. That would be a larger refactor and is unnecessary now that the probe consults R2 directly.
- Did **not** add a new GitHub-Actions workflow. Existing `production-health-probe.yml` is unaffected.
