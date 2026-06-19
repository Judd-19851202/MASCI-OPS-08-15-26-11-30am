# TRACK 15.52C · Retention Truth Audit

**Status:** Read-only · evidence captured 2026-06-19 21:30 UTC against live `s3://masci-hub`.

## Question 1 — What retention model was originally designed?

| Source | Statement |
|---|---|
| `backend/lib/r2_retention.py` (docstring) | "Tier 1 · keep ALL hourly zips for the last 14 days. Tier 2 · 14-90 days · keep ONLY the newest zip per calendar day (UTC). Tier 3 · 90-365 days · keep ONLY the newest zip per calendar month (UTC). Tier 4 · > 365 days · DELETE." |
| Same file (env defaults) | `TIER1_DAYS=14 · TIER2_DAYS=90 · TIER3_DAYS=365` (overridable via env, but defaults are "the canonical TRACK 15.28A retention contract — do not change unless operator approves") |
| Track 15.28A changelog entry | Documented the introduction of this exact 14/90/365 tiered policy as the response to "the R2-side bucket has been growing without bound at ~14.47 GiB / day" |
| Track 15.37 documentation | Documented the policy as a YELLOW posture pending operator confirmation of Atlas PITR + R2 versioning |
| `_run_r2_tiered_retention_async()` at `backend/server.py:6953` | The async wrapper that calls `enforce_r2_retention(prefix="backups/auto-90d/", dry_run=False)` after every successful R2 upload |

**Intended retention architecture (designed):**

```
Hourly retention      ✅ keep all          0 -   14 d   (≤336 objects at 1/hr)
Daily retention       ✅ keep newest per day 14 -  90 d   (≤76 objects)
Weekly retention      ❌ not designed
Monthly retention     ✅ keep newest per month 90 - 365 d  (≤9 objects)
Yearly retention      ❌ not designed (Tier 4 deletes at 365 d)
Permanent archive     ❌ not designed
```

The retention design was **synchronously authored, intentional, and shipped** in Track 15.28A. The 14/90/365 numbers are the canonical contract.

## Question 2 — What retention model is operating today?

### R2 bucket lifecycle (live, queried via `s3.get_bucket_lifecycle_configuration`)

```
Rule 1: id="Default Multipart Abort Rule"            status=Enabled
        (Cloudflare default; not retention-related.)

Rule 2: id="masci-backups-auto-90d"                   status=Enabled
        filter={'Prefix': 'backups/auto-90d/'}
        expiration={'Days': 90}    ← deletes EVERYTHING at 90 days
```

The bucket lifecycle is the **operational truth**: any object under `backups/auto-90d/` is deleted at age 90 days, regardless of which Tier the app's code believes it belongs to.

### App-side retention (live, in `lib/r2_retention.py` and called from `server.py:6953-6991`)

Active and firing after every successful R2 upload. Verified synthetically (`plan_retention()` against 365-day synthetic dataset yields 15 hourly + 76 daily + 10 monthly = 101 survivors). But Tier 3 survivors are **deleted by the R2 lifecycle 90-day rule before they reach the monthly tier window in production**.

### Live object cohort (every object in `backups/`, 2026-06-19 21:30 UTC)

| Age Bucket | Object Count |
|---|---:|
| 0 – 30 days | 762 |
| 31 – 60 days | 92 |
| 61 – 90 days | 0 |
| 91 – 180 days | 0 |
| 181 – 365 days | 0 |
| 365+ days | 0 |
| **TOTAL** | **854** |

(Combined view of both `backups/auto-90d/` = 354 objects and legacy root `backups/*.zip` = 500 objects, since they share the bucket-creation date floor.)

### Critical context — the R2 BUCKET itself is 39 days old

```
$ s3.list_buckets() → masci-hub  created=2026-05-11 10:28:41 UTC
```

The bucket was created on **2026-05-11**, which is **39.5 days before this audit (2026-06-19 21:30 UTC)**. No object in the bucket can be older than the bucket itself. The "zero objects > 60 days" observation is **a true statement about today's evidence, but it does not yet test the Tier 3 / R2-lifecycle conflict** — that conflict will first fire on **2026-08-09 ± 1 day** (Day 90 from bucket creation), when R2 begins deleting the oldest objects regardless of what the app's monthly-survivor planner intended.

## Lifecycle map · live MASCI values

```
DAY 0 ──────► DAY 14 :  337 hourly archives · 168 GB · TIER 1 active
DAY 14 ─────► DAY 30 :   14 daily-survivor archives ·   3.1 GB · TIER 2 active (early window)
DAY 30 ─────► DAY 40 :    3 daily-survivor archives ·   3 MB · TIER 2 active
DAY 40 ─────► DAY 90 :    0 archives · BUCKET-AGE LIMITED — no objects this old yet
DAY 90 ─────► DAY 365:    0 archives · DESTINED TO BE EMPTY — R2 lifecycle will delete monthlies before they arrive
DAY 365+    :             0 archives · NEVER REACHABLE
```

## Question 1+2 summary

- **Intended retention:** 14d hourly · 90d daily · 365d monthly · then delete.
- **Operating retention:** 14d hourly · ~75d daily (truncated by 90-d R2 lifecycle) · NO monthly tier (R2 lifecycle deletes before app logic can preserve) · NO yearly tier.
- **Effective retention ceiling:** 90 days (R2 side wins).
- **Currently observable retention ceiling:** 39 days (bucket age — not a defect, will reach steady state at day 90).
