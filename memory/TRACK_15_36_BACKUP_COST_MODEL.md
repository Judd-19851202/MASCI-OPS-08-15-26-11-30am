# TRACK 15.36 · Backup Cost Model

**Track:** 15.36 · READ-ONLY · no cadence change made
**Date:** 2026-02
**Pricing baseline:** Cloudflare R2 standard pricing (verified as of 2026-02):

| Line item | Rate |
|---|---|
| Storage | **$0.015 / GiB-month** (US-east class) |
| Class A operations (writes / lists) | $4.50 per million |
| Class B operations (reads / GETs) | $0.36 per million |
| Egress | **$0.00** (zero-egress is R2's flagship feature) |
| Atlas (M0-M10) | Inclusive of backup snapshots on M2+; Continuous Backup on M10+ |

All cost numbers below are R2-only. Atlas costs are not modelled here — Atlas Continuous Backup and snapshot retention are bundled into the cluster tier.

---

## Current state (live · 2026-06-19T10:06:16Z probe)

| Metric | Value |
|---|---|
| Total R2 bucket | 197.13 GiB · 8,517 objects |
| Backups prefix only (`backups/`) | 864 objects |
| Backups in `backups/auto-90d/` (governed by retention) | ~364 objects |
| Backups in legacy `backups/` (unpruned) | ~500 objects |
| Avg backup zip size (newest 500 sample) | 373 MB (range 0.1 MB – 632.6 MB) |
| Hourly backup avg (newest 24h sample) | ~600 MB |
| Records per backup | ~138,000 (auto-discovery covers all 163 collections) |
| Photos inlined per backup | varies; included in 600 MB total |
| New backup data per day at hourly cadence | 24 × 600 MB = 14.06 GiB/day |
| Current R2 monthly cost | **197 GiB × $0.015 = $2.96 / month** |

The cost is small in absolute terms — but the bucket is at **394 %** of the `R2_USAGE_ALERT_GB=50` threshold the platform itself defines as "alert".

---

## Steady-state backup growth (per cadence)

The R2 hourly archive is mostly composed of newly-uploaded photos + slightly-grown collections. Each archive is roughly the same size because all 163 collections are re-archived in full every tick (no incremental). For the cost model we use **600 MB per archive** as the working figure (matches the 24 newest archives).

| Cadence | Archives/day | New GiB/day | Tier-1 (14d hourly retention) survivors | Tier-1 size |
|---|---|---|---|---|
| Hourly | 24 | 14.06 | 336 archives | **197 GiB** |
| Every 4 h | 6 | 3.52 | 84 archives | **49 GiB** |
| Every 6 h | 4 | 2.34 | 56 archives | **33 GiB** |
| Every 12 h | 2 | 1.17 | 28 archives | **16 GiB** |
| Daily | 1 | 0.59 | 14 archives | **8 GiB** |

Tier-2 (14-90d, newest per day) adds 76 archives × 600 MB = **45 GiB** (cadence-independent).
Tier-3 (90-365d, newest per month) adds ~9 archives × 600 MB = **5 GiB** (cadence-independent).

So total steady-state R2 backup storage is approximately:

| Cadence | Tier-1 + Tier-2 + Tier-3 | Steady-state size |
|---|---|---|
| Hourly | 197 + 45 + 5 | **247 GiB** |
| Every 6 h | 33 + 45 + 5 | **83 GiB** |
| Daily | 8 + 45 + 5 | **58 GiB** |

---

## Cost projection (R2 storage only) — per cadence × horizon

| Horizon | Hourly | 4-hour | 6-hour | 12-hour | Daily |
|---|---|---|---|---|---|
| 30 days | $3.71 | $1.62 | $1.25 | $0.99 | $0.87 |
| 90 days | $11.12 | $4.85 | $3.74 | $2.96 | $2.61 |
| 1 year | $44.46 | $19.40 | $14.94 | $11.84 | $10.44 |
| 3 years | $133.38 | $58.20 | $44.82 | $35.52 | $31.32 |
| 5 years | $222.30 | $97.00 | $74.70 | $59.20 | $52.20 |

These are pure R2 storage costs at the **steady-state** size for each cadence (Tier-1 + Tier-2 + Tier-3 combined).

---

## Adoption-scaled projection (per cadence)

"Adoption" here means concurrent crew submitting incidents, photos, daily reports — which directly drives per-archive size growth via inlined photos.

Working multipliers:
* **Current adoption (≈25 %)** = 600 MB / archive
* **50 % adoption** = 1.2 GiB / archive
* **75 % adoption** = 1.8 GiB / archive
* **100 % adoption** = 2.4 GiB / archive

### Steady-state R2 storage (Tier-1 + Tier-2 + Tier-3) at each adoption × cadence

| Cadence | Current | 50 % | 75 % | 100 % |
|---|---|---|---|---|
| Hourly | 247 GiB | 494 GiB | 741 GiB | 988 GiB |
| 4-hour | 81 GiB | 162 GiB | 243 GiB | 324 GiB |
| 6-hour | 83 GiB | 166 GiB | 249 GiB | 332 GiB |
| 12-hour | 38 GiB | 76 GiB | 114 GiB | 152 GiB |
| Daily | 28 GiB | 56 GiB | 84 GiB | 112 GiB |

### Annual R2 storage cost at each adoption × cadence

| Cadence | Current | 50 % | 75 % | 100 % |
|---|---|---|---|---|
| Hourly | $44 | $89 | $133 | $178 |
| 4-hour | $15 | $29 | $44 | $58 |
| 6-hour | $15 | $30 | $45 | $60 |
| 12-hour | $7 | $14 | $21 | $27 |
| Daily | $5 | $10 | $15 | $20 |

### 5-year R2 storage cost at each adoption × cadence

| Cadence | Current | 50 % | 75 % | 100 % |
|---|---|---|---|---|
| Hourly | $222 | $445 | $667 | $890 |
| 4-hour | $73 | $146 | $219 | $292 |
| 6-hour | $75 | $149 | $224 | $299 |
| 12-hour | $34 | $68 | $103 | $137 |
| Daily | $25 | $50 | $76 | $101 |

---

## Class-A operation costs (writes/lists)

Each backup write is ~2-3 Class A ops (PutObject, multipart parts). The retention pruner does ~1 ListObjectsV2 page + 1 DeleteObjects per tick. Conservative estimate per cadence:

| Cadence | Class A ops/year | Annual cost |
|---|---|---|
| Hourly | ~50,000 | $0.23 |
| 6-hour | ~10,000 | $0.05 |
| Daily | ~2,000 | $0.01 |

**Class A operations cost is negligible at all cadences.**

---

## Bandwidth cost

R2 zero-egress = **$0.00** for download. Backup retrieval / restore costs nothing in bandwidth. This is the major economic advantage of R2 over S3 for backup workloads.

---

## Savings from switching to 6-hour cadence

| Metric | Hourly (current) | Every 6 hours | Saved |
|---|---|---|---|
| Archives/day | 24 | 4 | -83 % |
| Tier-1 (14d) size | 197 GiB | 33 GiB | -83 % |
| Steady-state size | 247 GiB | 83 GiB | -66 % |
| Annual cost | $44 | $15 | $29 (-66 %) |
| 5-year cost | $222 | $75 | $147 (-66 %) |
| 5-year cost @ 100 % adoption | $890 | $299 | $591 (-66 %) |

Even at 100 % adoption growth (4× current photo volume), switching from hourly → 6-hour saves ~$590 over 5 years and keeps the bucket comfortably under 350 GiB.

---

## The real cost driver is not cadence — it's the legacy unpruned `backups/` prefix

The legacy prefix holds ~500 objects (Track 15.28A explicitly excluded it). Those objects do not appear to be growing (writes go to `auto-90d/`), but they are also not shrinking. They contribute roughly:

* 500 objects × est. average 30 MB = **~15 GiB**
* Annual R2 cost: 15 × $0.015 × 12 = **$2.70 / year**

The cleanup opportunity is small in dollars ($2.70/yr) but real in object count (-500 objects from the bucket inventory). Operator should authorize a one-shot delete of the legacy prefix in a separate track — not in Track 15.36.

---

## Summary — what does cadence-change actually buy

| If we change | We save |
|---|---|
| Hourly → 6-hour | 164 GiB at steady state · $29/year · 5,000 fewer S3 ops/year |
| Hourly → daily | 189 GiB at steady state · $34/year · ~50,000 fewer S3 ops/year |
| Delete legacy `backups/` prefix | 15 GiB · $2.70/year |

**The dollar savings are small. The architectural savings — fewer alert-noise rows, faster bucket-list operations, lower restore-time confusion ("which of 24 today's backups do I use?") — are the bigger win.**
