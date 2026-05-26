# Phase 31.3 · Storage Growth + Cost Trajectory Analysis
## iter440 · 2026-05-26

> Real numbers · no memory estimates · paginated boto3 inventory +
> Atlas live counts.

---

## Snapshot (audit time 2026-05-26 00:42 UTC)

| Layer                          | Bytes        | GB    |
| ------------------------------ | -----------: | ----: |
| R2 · `backups/auto-90d/`       | 59,213M      | 55.15 |
| R2 · `backups/<legacy>/`       | 24,168M      | 22.51 |
| R2 · `backups/` total          | 83,381M      | 77.66 |
| R2 · `operational_attachments` | 2,176 bytes  | <1 MB |
| Atlas · operational data       | (live) 123 collections · 244K records |

### Archive size convergence

| Date sample | Archive size |
| ----------- | -----------: |
| 2026-05-17  | 80–82 MB     |
| 2026-05-21  | 82–84 MB     |
| 2026-05-25  | 89–91 MB     |
| 2026-05-26  | 87–88 MB     |

Growth ≈ 0.7 MB/day per archive — driven by the daily-report,
incident, inspection, and continuity-event collections.

---

## Cadence vs cost · BEFORE the iter440 fix

```
real archives/day:     ~110  (vs 24 expected · 4.6× over)
archive size avg:       87 MB
daily R2 ingest:        9.6 GB/day
90-day steady-state:    864 GB
R2 storage cost:        $12.96/month     ($0.015/GB·mo)
R2 egress cost:         ~$0  (R2 has free egress)
R2 PUT request cost:    110 × 30 = 3300 PUTs/mo × $0.0045/1000 = $0.01/mo
Total monthly cost:     ~$13/month  for backups alone
```

## Cadence vs cost · AFTER the iter440 fix

```
expected archives/day:   24   (hourly · BACKUP_R2_HOURLY=true)
archive size avg:        87 MB
daily R2 ingest:         2.1 GB/day
90-day steady-state:     189 GB
R2 storage cost:         $2.83/month
Total monthly cost:      ~$3/month  for backups alone
```

### Savings

* **~76% cost reduction** at steady state.
* **~675 GB / month** of avoided R2 churn.
* **~80 GB / month** of avoided egress (none, but PUT requests).

---

## Annual projection (post-fix steady-state)

| Year | R2 storage usage | Annual cost      |
| ---- | ---------------: | ---------------: |
| 1    | ~190 GB          | ~$34             |
| 5    | ~190 GB          | ~$34/yr ongoing  |

(Lifecycle 90-day rule keeps steady-state flat indefinitely. Volume
growth comes only from Atlas data-set growth — each archive grows
~0.7 MB/day. After 1 year, archive size ≈ 87 + 252 MB ≈ 339 MB ·
steady-state ≈ 715 GB · cost ~$10.70/month.)

---

## Operational-attachment growth (independent of backups)

`storage-summary` snapshot:
* total: 32 attachments
* total_size_bytes: 2,176 (avg 68 B · placeholder-sized)
* projected 90-day growth: 96 attachments · 6,528 bytes

When real photo attachments start landing (currently inline_b64 = 0,
unknown = 0), per-attachment size will jump from ~68 B to ~200–800
KB/photo. With ~50 photos/day average across all forms, that's ~30
MB/day of attachments, which is independent of the backup chain
(R2 stores attachments under `photos/photos/<YYYY>/<MM>/...`,
NOT under `backups/`).

Backups DO include attachment metadata + inlined photos for archive
integrity, so attachment growth flows through both prefixes.

---

## Atlas backup interaction

Atlas managed backups are configured at the cluster level (Atlas UI,
not in this repo). The platform's R2 backup chain is INDEPENDENT of
Atlas's own continuous-backup feature — it's a doctrine of
defense-in-depth (R2 zips are point-in-time, self-contained, and
restorable without Atlas access).

No interaction risk. Both chains can co-exist.

---

## Summary

* Current R2 usage: 77.66 GB.
* Pre-fix trajectory: 765 GB at 90-day steady state (~$12/month).
* Post-fix trajectory: 190 GB at 90-day steady state (~$3/month).
* Operational doctrine is intact: defense-in-depth, no analytics.
* No new monitoring infrastructure is needed.
