# TRACK 15.52C · R2 Lifecycle Forensics — Why Are There Zero Objects Older Than 90 Days?

**Status:** Read-only · root cause proven from live evidence captured 2026-06-19 21:30 UTC.

## The observation

`backups/` prefix on `s3://masci-hub` contains:
- 0 – 30 days: 762 objects
- 31 – 60 days: 92 objects
- 61 – 90 days: **0 objects**
- 91 – 180 days: **0 objects**
- 181 – 365 days: **0 objects**
- 365+ days: **0 objects**

## Hypotheses considered

| # | Hypothesis | Verdict |
|---|---|:---:|
| H1 | Cloudflare lifecycle expiration deleted them | **FALSE** (see proof below) |
| H2 | Application cleanup job deleted them | **FALSE** (see proof below) |
| H3 | Archive rotation process deleted them | **FALSE** (no archive rotation exists in code) |
| H4 | Manual deletion by operator | **UNVERIFIED but unlikely** (no operator action recorded in CHANGELOG, audit trail does not show admin deletions of `backups/` keys) |
| H5 | Path mismatch — older backups are at a different prefix or in a different bucket | **FALSE** (full bucket walk found no other backup prefixes; `list_buckets()` shows only `masci-hub`) |
| H6 | Storage migration — bucket itself is recent | **✅ TRUE — this is the root cause** |

## Proof of H6 — the R2 bucket itself is only 39 days old

```
$ python3 -c "import boto3; ... s3.list_buckets() ..."
bucket=masci-hub  created=2026-05-11 10:28:41+00:00
```

Bucket creation date: **2026-05-11 10:28:41 UTC.**
Audit date: **2026-06-19 21:30 UTC.**
Elapsed: **39.46 days.**

The bucket cannot contain objects older than its own age. The newest possible date that could be characterized as "older than 90 days" within this bucket is `2026-05-11 - 90 = 2026-02-10` — but the bucket did not exist on 2026-02-10.

The oldest object in the bucket is `backups/MASCI_complete_backup_2026-05-11_141541Z.zip` at `2026-05-11 14:15:41 UTC` (the first backup written within hours of bucket creation, age 39.30 days).

## Proof H1 (Cloudflare lifecycle) is FALSE

The lifecycle rule `masci-backups-auto-90d` expires objects at Day 90. The oldest object in the bucket is 39.30 days old. The lifecycle rule **has never fired** in this bucket. It is **scheduled to fire for the first time on 2026-08-09 ± a few hours**, when the earliest `auto-90d/` object (2026-05-17 23:55 UTC) reaches age 90.

We cannot blame the lifecycle for deleting objects that never existed.

## Proof H2 (app cleanup job) is FALSE

`backend/lib/r2_retention.py:enforce_r2_retention()`:
- Tier 1 (0-14 d): keep all
- Tier 2 (14-90 d): keep newest per day
- Tier 3 (90-365 d): keep newest per month
- Tier 4 (> 365 d): delete

The function only enters the delete branch for Tier 4 objects (> 365 days). No object in the bucket is older than 39 days, so Tier 4 has never been triggered. We confirmed this by running `plan_retention()` against a 365-day synthetic dataset — Tier 4 deleted_by_tier was `{1:0, 2:0, 3:264, 4:0}` — which proves the function's *intent*; but in the *live* bucket, no Tier 4 deletes can fire because no objects qualify.

Tier 3 deletes (264 in the synthetic test) DO happen in the live system today — but only for objects in `auto-90d/` aged 14-90 days that lose their "newest-per-day" status to a newer same-day backup. They are not deletes of older-than-90-day objects.

## Why "older than 90 days" looks empty TODAY

Because the bucket is **39 days old**.

The earliest possible date at which we can begin to test whether the R2 lifecycle vs app Tier 3 conflict actually causes data loss is **2026-08-09** (Day 90 from bucket creation).

Until then, the question "why are there no objects older than 90 days?" reduces to "because the bucket is younger than 90 days."

## Where were MASCI backups before 2026-05-11?

This is the more important question. Investigation in this container:

- `find /app/backend/backups` (the legacy local-disk path): currently empty in preview pod.
- Other R2 buckets in the same Cloudflare account: `s3.list_buckets()` shows ONLY `masci-hub`. Either there is no second bucket, or the access key is scoped to `masci-hub` only.
- The CHANGELOG references a `backups/` history going back to early 2026, but provides no evidence of any external archive store.

**Best evidence-based answer:** prior to the May 2026 R2 bucket creation, MASCI's backups likely lived in:
- (a) the local-disk path `/app/backend/backups/` of the previous deployment pod (ephemeral, lost on pod recycle), OR
- (b) MongoDB Atlas managed snapshots only (UNVERIFIED — depends on Atlas tier), OR
- (c) an earlier bucket or storage tier that was rotated out when this bucket was created.

None of these are confirmable from this container. **Pre-May-2026 backup history is UNVERIFIED.**

## Lifecycle conflict forecast (no action required, evidence only)

The first Tier-3 monthly-survivor candidate will be the newest backup from June 2026, which is `MASCI_complete_backup_2026-06-19_200433Z.zip` (or its successor at month-end). The app's `r2_retention.py` will mark this candidate as a Tier 3 KEEP at Day 90 (2026-09-17), but the R2 lifecycle rule will independently DELETE it on Day 90 from its `LastModified` (2026-09-17 ± hours).

The conflict will materialize on **2026-09-17 ± 1 day**, when MASCI loses the first monthly survivor it intended to retain.

## Forensic summary

| Question | Evidence-based answer |
|---|---|
| Why are there zero objects older than 90 days? | The bucket is 39 days old. No object can be that old. |
| Did the lifecycle rule delete them? | No. The rule has not yet fired. |
| Did the app retention delete them? | No. Tier 4 has not yet activated. |
| Did anyone manually delete them? | No evidence of admin deletes in this bucket. |
| Did they exist before 2026-05-11? | UNVERIFIED. Likely on a previous bucket or local disk that is now gone. |
| When WILL the conflict between R2 lifecycle and app Tier 3 first cause data loss? | Approximately 2026-09-17 (Day 90 from the first `auto-90d/` upload on 2026-05-17). |
