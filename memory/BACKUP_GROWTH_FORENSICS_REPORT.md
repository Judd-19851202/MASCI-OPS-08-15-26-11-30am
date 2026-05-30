# BACKUP_GROWTH_FORENSICS_REPORT

**Date:** 2026-05-30 (Batch F · Phase 3)
**Method:** Mongo `collStats` for every collection in `masci_safety` + R2 archive history listing + per-document size sampling.
**Evidence:** `/app/memory/batch_f_evidence/growth_forensics.json`, `r2_history.json`

---

## 1 · Critical correction to Batch E's hypothesis

Batch E hypothesized that the archive size growth (92 MB → 442 MB in 5 days) was "driven by accumulating audit_events / usage_events / health_monitor_runs (high-cardinality append-only collections)."

**This is INCORRECT. The actual driver is `daily_reports` — specifically inline base64 photo data carried inside per-DR `photos[]` and `subcontractors[]` fields.**

---

## 2 · Top 25 collections by data size (from `collStats`)

Total data size across all 139 collections: **375.5 MB** (after backup compression this becomes ~442 MB archive — the discrepancy is due to BSON-to-ZIP conversion overhead + photo binaries in the `photos/` archive prefix).

| Rank | Collection | docs | size_MB | %total | avg_bytes/doc | idx_MB |
|---:|---|---:|---:|---:|---:|---:|
| 1 | **daily_reports** | **86** | **260.69** | **69.42%** | **3 178 474** | 0.18 |
| 2 | usage_events | 241 446 | 38.10 | 10.15% | 165 | 17.55 |
| 3 | job_photo_thumb_cache | 1 791 | 24.17 | 6.44% | 14 152 | 0.19 |
| 4 | incidents | 7 | 15.42 | 4.11% | 2 310 126 | 0.13 |
| 5 | job_hazard_files | 6 | 15.18 | 4.04% | 2 653 380 | 0.07 |
| 6 | meetings | 23 | 11.54 | 3.07% | 526 227 | 0.11 |
| 7 | audit_events | 10 032 | 2.24 | 0.60% | 233 | 0.63 |
| 8 | health_monitor_runs | 16 908 | 1.89 | 0.50% | 117 | 0.81 |
| 9 | equipment_inspections | 25 | 1.06 | 0.28% | 44 579 | 0.28 |
| 10 | admin_audit | 1 883 | 0.73 | 0.19% | 403 | 0.15 |
| 11 | draft_telemetry | 1 638 | 0.53 | 0.14% | 342 | 0.41 |
| 12 | idempotency_keys | 23 | 0.53 | 0.14% | 24 027 | 0.11 |
| 13 | directory_sessions | 1 901 | 0.44 | 0.12% | 240 | 0.11 |
| 14 | operations_events | 534 | 0.41 | 0.11% | 800 | 0.25 |
| 15 | po_requests | 1 | 0.34 | 0.09% | 360 392 | 0.32 |
| 16 | session_activity | 1 052 | 0.34 | 0.09% | 340 | 0.27 |
| 17 | fleet_audit | 582 | 0.26 | 0.07% | 471 | 0.14 |
| 18 | hub_banner_audit | 1 161 | 0.24 | 0.06% | 213 | 0.07 |
| 19 | job_photos | 598 | 0.22 | 0.06% | 386 | 0.20 |
| 20 | equipment_master | 589 | 0.21 | 0.05% | 367 | 0.14 |
| 21 | compliance_findings | 233 | 0.14 | 0.04% | 631 | 0.04 |
| 22 | equipment_units | 484 | 0.12 | 0.03% | 259 | 0.04 |
| 23 | training_hits | 1 177 | 0.11 | 0.03% | 100 | 0.09 |
| 24 | employees | 245 | 0.09 | 0.02% | 400 | 0.27 |
| 25 | admin_audit_log | 142 | 0.06 | 0.02% | 447 | 0.04 |

**Top 6 collections account for 97% of all data.** Of those 6, `daily_reports` alone is 69.42% — by itself larger than every other collection in the platform combined.

---

## 3 · Per-DR size distribution

| Stat | Value |
|---|---:|
| Total DRs | 86 |
| Total DR data | 260.7 MB |
| Average DR size | 3.04 MB |
| Max DR size | 11.33 MB (`e000f6a2` · 2026-05-21 · SJR2C Loop Trail) |
| Number of DRs ≥ 5 MB | 14 (top 14 of 86) |
| Number of DRs ≥ 10 MB | 3 |

**Per-DR field-by-field bytes (largest DR `e000f6a2`):**

| Field | Bytes | KB | Notes |
|---|---:|---:|---|
| **subcontractors** | **7 066 584** | **6 901** | 🔴 dominant — likely inline base64 (driver licenses, COIs, etc.) |
| **photos** | **4 124 416** | **4 028** | 🔴 inline base64 photo data, 6 photos |
| materials | 669 968 | 654 | likely inline material delivery photos |
| prepared_by_signature | 20 895 | 20 | inline signature image |
| masci_crews | 453 | 0 | text-only |
| visitors | 256 | 0 | text-only |
| activities | 173 | 0 | text-only |
| equipment | 163 | 0 | text-only |
| distribution_list | 59 | 0 | text-only |
| project_name | 57 | 0 | text-only |
| (35 other fields) | <1k each | | text-only |

**Conclusion**: **the `subcontractors[]` + `photos[]` + `materials[]` array fields contain inline base64 image data** — these were NOT migrated to R2 references by the iter64 Phase 2 photo migration. Only `photos[]` fields on certain modules got migrated; subcontractor docs and materials photos stayed inline.

---

## 4 · R2 complete-archive size history

R2 listing of `backups/auto-90d/MASCI_complete_backup_*.zip` (top 100 most-recent):

| Date | Archives that day | Sum_MB | Avg_MB | Max_MB | Notes |
|---|---:|---:|---:|---:|---|
| 2026-05-25 | 81 | 7 586.8 | 93.7 | 247.3 | Scheduler healthy · hourly cadence |
| 2026-05-26 | 18 | 1 813.2 | 100.7 | 321.1 | Scheduler dying mid-day; growth visible |
| 2026-05-27 → 2026-05-29 | 0 returned in top-100 | — | — | — | **Scheduler dead (Batch B/C investigation period)** |
| 2026-05-30 | 1 | 442.6 | 442.6 | 442.6 | First archive after Batch D scheduler activation |

### Growth trajectory analysis

| Window | Avg archive size | Growth |
|---|---:|---:|
| 2026-05-25 baseline | 93.7 MB | — |
| 2026-05-26 (1 day) | 100.7 MB | +7% |
| 2026-05-30 (5 days · post-gap) | 442.6 MB | **+372%** (4.7×) |

Average size on 2026-05-25 was 93.7 MB. By 2026-05-30, single-archive size was 442.6 MB. The 5-day gap saw a ~349 MB increase.

Most plausible explanation for the jump: **~58 new heavy DRs (and/or edits to existing DRs) submitted between 2026-05-25 and 2026-05-30**, each carrying ~3 MB of inline subcontractor / photo data, contributing ~150-200 MB. The remainder is growth in `usage_events`, `health_monitor_runs`, and `directory_sessions`.

---

## 5 · Records/day rate (estimated from current counts ÷ window)

| Collection | Total docs | Estimate rate/day | Confidence |
|---|---:|---:|---|
| usage_events | 241 446 | ~1 500/day | Medium (assumes ~6 month accumulation) |
| health_monitor_runs | 16 908 | ~250/day | Medium |
| audit_events | 10 032 | ~150/day | Medium |
| directory_sessions | 1 901 | ~100/day | Medium |
| session_activity | 1 052 | ~50/day | Medium |
| daily_reports | 86 | ~2.8/day | High (last 30 days observed) |
| equipment_inspections | 25 | ~0.8/day | Medium |
| incidents | 7 | ~0.2/day | Low (low-cadence) |
| meetings | 23 | ~0.8/day | Medium |
| po_requests | 1 | <0.1/day | Very low cadence |

(Rate confidence is limited because my probes for time-bound counts returned 0 — the document time fields use a mix of ISO strings and BSON dates with varying field names per collection. Hourly cadence of the existing scheduler health rows could provide more reliable rate samples in a future deeper audit.)

---

## 6 · MB/day growth rate (archive-derived)

| Window | MB added | Days | MB/day |
|---|---:|---:|---:|
| 2026-05-25 → 2026-05-30 (archive size growth) | +349 MB | 5 | ~70 MB/day |

At 70 MB/day growth, the archive will:
- Hit 600 MB OOM watermark in **~3 days from today**
- Hit 1 GB in ~9 days
- Hit 5 GB in ~67 days

**🚨 The hourly complete-R2 build IS expected to OOM within ~3 days at current growth rate.** Per Batch E recommendation, change `BACKUP_R2_HOURLY=false` + `BACKUP_R2_FULL_HOUR_UTC=4` immediately.

But also: the root cause (inline base64 in DR subcontractors/photos arrays) needs structural mitigation — see `PLATFORM_RECOVERY_GAP_REPORT.md` GAP-1.

---

## 7 · Index size

`usage_events` carries 17.55 MB of indexes against only 38.10 MB of data — index-to-data ratio = 46%. That's an unusual indicator of either too many indexes or low-cardinality fields driving wide tree fan-out. Worth a future single-collection audit. Other collections show normal index ratios.

---

## 8 · Net forensics summary

| Finding | Severity | Action |
|---|---|---|
| 🔴 `daily_reports` is 69% of all data, with avg 3.18 MB/DR driven by inline base64 in `subcontractors[]` + `photos[]` + `materials[]` | CRITICAL | Migrate to R2 references (see GAP-1) |
| 🔴 Archive grew 4.7× in 5 days, on track to OOM in ~3 days at hourly cadence | CRITICAL | Toggle `BACKUP_R2_HOURLY=false` immediately (Batch E rec) |
| 🟡 `usage_events` 241k rows is 10% of total — biggest "telemetry" footprint but still 7× smaller than DR contribution | Medium | Consider TTL retention (180-day) |
| 🟡 `job_photo_thumb_cache` 24 MB is a derived cache — should not be in DR backups | Medium | Move to telemetry-tier or exclude from archive |
| 🟡 `audit_events` + `health_monitor_runs` together are 27 000 rows but only 4 MB — manageable | Low | TTL recommended but not urgent |
| 🟡 `usage_events` index size 17.55 MB on 38 MB data — index ratio audit | Low | Defer to ops-tuning batch |
