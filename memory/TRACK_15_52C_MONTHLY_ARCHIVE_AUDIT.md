# TRACK 15.52C · Monthly Archive Audit

**Status:** Read-only · captured 2026-06-19 21:30 UTC.

## Question 4 — Do monthly archives actually exist?

### Where would they be stored?

Per `backend/lib/r2_retention.py:_FILENAME_RE`, all backup archives share a single naming convention regardless of their tier:

```
MASCI_(complete|full|lite)_backup_YYYY-MM-DD_HHMMSSZ.zip
```

There is **no separate prefix, bucket, storage class, or filename convention** for "monthly" archives. The app's retention engine simply marks certain objects as "survivors" using in-memory bucketing during a Tier 2 / Tier 3 pass — but no Mongo collection, no manifest, no path-segment, and no metadata tag distinguishes them in R2.

A "monthly archive" in MASCI's design is therefore not a separate object — it is a **role** assigned at retention-time to whichever zip happened to be the newest one written in a given calendar month.

### Naming convention

Same as all backups. No `monthly/` prefix; no `MASCI_monthly_*` filename.

### Retention policy

App-side: Tier 3 keeps the newest zip per calendar month for 90-365 days.

R2-side: bucket lifecycle deletes every object in `backups/auto-90d/` at 90 days, regardless of monthly-survivor role.

### Oldest monthly archive in the live bucket

There is none. The bucket is 39 days old; no archive has yet been *promoted* to Tier 3 (which only happens at age 90+).

Looking forward, the candidate Tier 3 survivors would be:
- May 2026 newest: `MASCI_complete_backup_2026-05-31_*.zip` (live: there is a 2026-05-31 archive, last modified 2026-05-31; it will turn 90 d on **2026-08-29**).
- June 2026 newest: TBD until month-end.
- July 2026 newest: TBD.

At **2026-08-29 ± hours**, the R2 lifecycle rule will delete the May 2026 candidate before it can be promoted to monthly survivor. That is the first concrete event where monthly retention will measurably fail.

### Storage location

Same prefix (`backups/auto-90d/`) as hourly + daily. No segregation.

### Cross-checks

| Check | Result |
|---|---|
| Bucket walk for `monthly*` keys | 0 hits |
| Bucket walk for `archive*` keys | 0 hits |
| Codebase search for `monthly_archive | monthly_backup | long_term_archive | cold_storage` | 0 hits |
| Codebase search for separate monthly-write code path | None — Tier 3 is purely a *don't-delete* decision in `r2_retention.py:plan_retention()` |
| Cloudflare R2 storage classes (Standard / Infrequent Access) on the bucket | Standard only; no Glacier-equivalent tier configured |
| Atlas snapshot archive | UNVERIFIED — depends on cluster tier and snapshot retention settings the operator controls |

## Verdict

**"Monthly retention is documented but not implemented as a distinct archive."**

A more precise statement:

> Monthly retention is implemented **only as a deferred-deletion rule** within the same hourly archive store. The implementation depends entirely on R2 lifecycle NOT deleting the would-be survivors. Because R2 lifecycle DOES delete them at Day 90 regardless of role, monthly retention will not function in production once the bucket ages past 90 days. As of today (Day 39), no Tier 3 promotion has happened yet, so the failure is **forecast, not yet observable**.

## Implication for restore-point matrix

Any attempt to restore data older than ~90 days from R2 in production **will fail** starting 2026-08-09 ± 1 day. The only data-protection layer that can answer "restore 6 months ago" or "restore 1 year ago" is Atlas (PITR + scheduled snapshots), which is itself **UNVERIFIED** per `TRACK_15_52C_ATLAS_PROTECTION_AUDIT.md`.

## What would a TRUE monthly-archive look like (informational only — NO ACTION TAKEN)

For evidence-only documentation: a true monthly archive would require either:
- A separate R2 prefix (e.g. `backups/monthly-365d/`) NOT covered by the 90-day lifecycle rule, OR
- A separate bucket, OR
- A separate storage class (e.g. Cloudflare R2 Infrequent Access, when generally available), OR
- A cross-account copy to a write-locked bucket.

None of these exist today. This is documentation only; no implementation is recommended in this read-only forensic track.
