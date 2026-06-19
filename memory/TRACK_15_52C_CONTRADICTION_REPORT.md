# TRACK 15.52C · Contradiction Report

**Status:** Read-only · ranked from most-impactful to least.

## Ranking criteria

1. Does the contradiction cause data loss?
2. Does the contradiction cause operator confusion that could lead to a wrong production decision?
3. Does the contradiction mislead a third party (auditor, insurance, OSHA reviewer) reading platform documentation?

## Ranked contradictions

### #1 (CRITICAL) — R2 lifecycle silently overrides app-side Tier 3 monthly retention

| Source | Statement |
|---|---|
| `backend/lib/r2_retention.py:plan_retention()` | "Tier 3 · 90-365 days · keep ONLY the newest zip per calendar month." |
| Cloudflare R2 bucket policy `masci-backups-auto-90d` | `Expiration: 90 days` (deletes everything in `backups/auto-90d/` at Day 90). |
| Synthetic test (this audit) | `r2_retention.plan_retention(365-day dataset)` correctly classified 10 objects as Tier 3 survivors. |
| Live R2 bucket (this audit) | Zero Tier 3 survivors exist · the bucket is 39 days old · the first Tier-3 promotion attempt will be deleted by the lifecycle rule before it can be preserved (forecast: ~2026-08-29 for the May-2026 candidate). |

**Operational consequence:** MASCI believes it has 365-day retention. It actually has ≤ 90-day retention at steady state. Any restore demand for data older than ~90 days will fail in production after Day 90 from bucket creation.

### #2 (HIGH) — Track 15.37 cost projection was overstated

| Source | Statement |
|---|---|
| Track 15.37 changelog | "Switch to every-6-hours: cost −66% · $44 → $15/year" |
| Live measurement (Track 15.52B) | $34.90/yr current · $17.83/yr at 6-hour → **−49%, not −66%** |

**Operational consequence:** Decision-makers comparing cost vs. risk may have weighted the cost-saving argument higher than the math supports.

### #3 (HIGH) — Track 15.37 legacy prefix size was understated

| Source | Statement |
|---|---|
| Track 15.37 changelog | "Legacy backups ~12 GiB · 500 objects (30 corrupted + 470 pre-15.28A)" |
| Live measurement (this audit + 15.52B) | **22.51 GB** · 500 objects, span 2026-05-11 → 2026-05-17 |

**Operational consequence:** Operator decisions about whether to sweep this prefix may have been informed by an understated cost-benefit (sweeping 22.5 GB recovers more value than 12 GiB).

### #4 (HIGH) — Implied 365-day retention vs. actual 39-day bucket age

| Source | Statement |
|---|---|
| `lib/r2_retention.py` docstring and Track 15.28A changelog | Implies a multi-month / yearly retention guarantee. |
| `s3.list_buckets()` (live) | Bucket created **2026-05-11 10:28 UTC** — only 39 days ago today. |

**Operational consequence:** The platform has not yet had time to accumulate the multi-month archives the docs imply. This is a *temporal* mismatch, not a defect, but it is invisible to anyone reading the docs without measuring the bucket.

### #5 (MEDIUM) — R2 versioning / object-lock / replication framed as part of the architecture, none enabled

| Source | Statement |
|---|---|
| Track 15.37/15.38/15.52 documentation | Treats R2 archive as the durability layer. |
| `s3.get_bucket_versioning` (live) | `Status=None` (disabled). |
| `s3.get_object_lock_configuration` (live) | Not configured. |
| `s3.get_bucket_replication` (live) | Not configured. |

**Operational consequence:** A delete of any backup object — accidental or malicious — is permanent. The architecture is durable against hardware loss but not against deletion.

### #6 (MEDIUM) — Pre-bucket-creation backup history is undocumented

| Source | Statement |
|---|---|
| CHANGELOG (multiple tracks throughout 2026-02 / 2026-03 / 2026-04) | References to backups as if they have been a long-standing capability. |
| `s3.list_buckets()` (live) | The R2 bucket was created **2026-05-11**. |

**Operational consequence:** Pre-May-2026 backups likely existed somewhere — local disk on a now-recycled pod, a different bucket, or Atlas snapshots only — but none of that is documented in PRD/CHANGELOG. Auditors asking "where was data backed up before May 2026?" have no on-platform answer.

### #7 (LOW) — Track 15.52A claimed 855 objects; today 854

This is not a real contradiction; the bucket fluctuates ±1 per hour as the retention pruner runs. Noted only for completeness.

## Summary

The platform's backup story has the right intent and the right code shape, but a series of small misalignments (R2 lifecycle vs app retention, cost projection, prefix size, bucket age, R2 hardening flags) cumulatively understate the real retention ceiling. The most impactful single contradiction is **#1** — and it is also the only contradiction that will measurably cause data loss in production (forecast Day 90, ~2026-08-09).

## Pillar-6 status

Per the audit's hard rules, no contradictions were *fixed* in this track. All seven are documented for the operator to address in the order they choose.
