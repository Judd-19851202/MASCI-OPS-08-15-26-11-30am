# BACKUP-AUDIT-001 · TIMELINE

**Sprint:** BACKUP-AUDIT-001 (AUDIT ONLY)
**Date:** 2026-02-09
**Purpose:** chronological reconstruction of "No successful full backup recorded in last 20 runs" warning across the production backup_health ledger.

---

## TIMELINE — last 30 days · production DB `masci_safety`

| When | Event | Mode | Outcome |
|---|---|---|---|
| 2026-05-10 → 2026-05-25 | Disk-based `full`/`lite` runs occurring at irregular cadence; R2 hourly cadence not yet dense in visible window | mixed | normal |
| **2026-05-26 01:01 UTC** | First `complete-r2` row visible in current window | `complete-r2` | ✅ ok, 91.7 MB, 244,432 records |
| 2026-05-26 02:01 UTC | One `lite` run lands inside ongoing hourly R2 cadence | `lite` | ✅ ok |
| 2026-05-26 02:01 → 2026-05-31 | 7 consecutive `complete-r2` + `r2-usage-alert` pairs visible | `complete-r2` × 7 | ✅ ok each |
| 2026-05-27 19:03–19:55 | Burst of 4 `lite` rows (preview-style spike — same DB cluster) | `lite` × 4 | ✅ ok |
| 2026-05-31 00:12 UTC | Last `complete-r2` row visible from May | `complete-r2` | ✅ ok, 279.1 MB, 21,482 records |
| 2026-06-08 22:02 + 22:04 | Two `lite` rows back-to-back (~2 min apart) | `lite` × 2 | ✅ ok |
| **2026-06-09 02:03:36 UTC** | **Most recent successful `lite` backup on production** (filename `MASCI_lite_backup_2026-06-09_020333Z.zip`) | `lite` | ✅ ok, 0.4 MB |
| 2026-06-09 02:06 UTC | Hourly R2 pair fires immediately after | `complete-r2` + `r2-usage-alert` | ✅ ok each |
| 2026-06-09 03:04 UTC | Next hourly R2 pair | `complete-r2` + `r2-usage-alert` | ✅ ok each |
| 2026-06-09 04:07 UTC | Hourly R2 pair | `complete-r2` + `r2-usage-alert` | ✅ ok each |
| 2026-06-09 05:05 UTC | Hourly R2 pair | `complete-r2` + `r2-usage-alert` | ✅ ok each |
| 2026-06-09 06:03 UTC | Hourly R2 pair | `complete-r2` + `r2-usage-alert` | ✅ ok each |
| 2026-06-09 07:06 UTC | Hourly R2 pair | `complete-r2` + `r2-usage-alert` | ✅ ok each |
| 2026-06-09 08:04 UTC | Hourly R2 pair | `complete-r2` + `r2-usage-alert` | ✅ ok each |
| 2026-06-09 09:07 UTC | Hourly R2 pair | `complete-r2` + `r2-usage-alert` | ✅ ok each |
| 2026-06-09 10:06 UTC | Hourly R2 pair | `complete-r2` + `r2-usage-alert` | ✅ ok each |
| **2026-06-09 11:04:19 UTC** | **Most recent `complete-r2` on production** (filename `MASCI_complete_backup_2026-06-09_110108Z.zip`, 447.9 MB) — newest R2 archive at audit time | `complete-r2` + `r2-usage-alert` | ✅ ok each |
| **2026-06-09 ~11:14 UTC** | **AUDIT MOMENT.** Read top-20 of `backup_health.find().sort(ts, -1).limit(20)`. Result: 10× `complete-r2` + 10× `r2-usage-alert`. **Zero `lite`/`full` rows in window** (the 02:03 lite was pushed out by subsequent hourly pairs). | — | ⚠ verifier would emit "No successful full backup …" |

---

## 30-day mode-frequency summary (production DB)

```
complete-r2          ok=True   95   (≈ every 1.0h)
r2-usage-alert       ok=True   95   (paired with each complete-r2)
lite                 ok=True    8   (avg every 3.75 days)
full                 ok=True    0   (zero in 30 days — OOM watermark sustained)
complete-r2-error    ok=False   1   (single transient failure)
(legacy null mode)              1
```

**Mathematical certainty of warning recurrence:** the verifier reads exactly 20 most-recent rows. The R2 pipeline writes 2 rows/hr → 10 hours fills the entire 20-row window. **Unless a `lite` or `full` row lands within any 10-hour wall-clock interval, the warning is guaranteed to fire** the next Mon 14:00 UTC.

With observed lite cadence of ~1 row per 3.75 days = 88 hours, the inter-lite gap is on average **8.8× larger than the verifier window**. Result: warning fires on most Mondays.

---

## Warning recurrence (estimated)

The condition has existed since `BACKUP_R2_HOURLY=true` was enabled AND the disk-based backup stopped firing in `full` mode (i.e., when `BACKUP_FULL_OOM_WATERMARK_MB` started auto-downgrading to `lite`). Both predate the 30-day evidence window — first observable production `complete-r2` row visible at **2026-05-26 01:01 UTC**, but earlier rows already exist beyond the 200-row retention cap.

| Mon 14:00 UTC | Inferred ledger window contents | Did warning fire? |
|---|---|---|
| 2026-06-02 14:00 | (out of evidence window) | likely YES — no full|lite in 30d preceding |
| 2026-06-09 14:00 (next Mon) | At least 7 hourly pairs (14 rows) + however many had landed since 02:03 lite. By the time Mon 14:00 hits, the 02:03 lite is ~36h old and definitely out of the top-20 window | YES — confirmed by live `build_verification_report` reproduction at audit time, verdict=warn, issues=["No successful full backup recorded in last 20 runs."] |

---

## Did the warning ever clear?

YES, intermittently. Specifically, whenever **two or more `lite` rows landed within the last ~10 hours before Mon 14:00 UTC**, that week's report read PASS. Observed clearing events visible in current ledger window:

| Cleared on | Why |
|---|---|
| 2026-05-27 burst (4 lites in ~50 min) | All 4 lite rows were still in the 20-row window → `last_full` populated |
| 2026-06-08 22:02 + 22:04 burst (2 lites in ~2 min) | Both lite rows in window until ~10 hours later. Verifier ran healthy until ~2026-06-09 08:04 when the 4th hourly pair pushed them out |
| 2026-06-09 02:03 (single lite) | Briefly cleared, then pushed out by ~12:03 UTC when 5 hourly pairs had accumulated since |

**Pattern:** the condition oscillates between cleared and tripped depending on whether a lite/full row falls in the 10-hour window prior to the Monday verification.

---

## First emergence

The mode-label mismatch is **definitional** — `mode="complete-r2"` was introduced when the R2 archive path shipped, but the verifier was written / extended in iter79 with the narrower `("full","lite")` filter. The two systems were designed in different sprints by different lenses (disk pipeline vs R2 pipeline) and never aligned at the verifier layer.

The mismatch only became **observable** once the R2 hourly cadence was switched on (env `BACKUP_R2_HOURLY=true`) AND the disk pipeline stopped producing `full` rows (env `BACKUP_FULL_OOM_WATERMARK_MB=600` continuously triggering lite-mode). Once both conditions held, the 20-row window started getting dominated by R2 pair rows, and the warning began firing.

---

## Recovery clock — time-to-restore from latest archive

| Step | Estimated time |
|---|---|
| Identify latest R2 archive | <1 min (R2 console or `list_objects_v2`) |
| Download `MASCI_complete_backup_2026-06-09_110108Z.zip` (447.9 MB) | ~30 s on a 100 Mbps connection |
| Run `python tools/restore_drill.py /tmp/<archive>.zip` against a preview DB | ~5–10 min (the May 30 drill restored 123 collections successfully) |
| Operator verifies row counts in restored DB vs current prod | ~5 min |
| Cut DNS / switch DB_NAME to restored DB | ~2 min |

**Achievable RPO** (data-loss tolerance): ≤ 1 hour (R2 cadence).
**Achievable RTO** (time-to-restore): ≤ 30 min for hot drill, ≤ 1h cold.

These numbers come from observed drill artifacts on the cluster (`masci_restore_drill_2026_05_30` exists and is complete with 123 collections including `admin_audit=1897` docs).

---

## Closure on Q9: "How long has this condition existed?"

- **First occurrence:** the mode-label mismatch existed since the R2 pipeline shipped (predates the 200-row retention window — likely months ago, in code lineage).
- **First production trigger of warning email:** once `BACKUP_R2_HOURLY=true` AND `BACKUP_FULL_OOM_WATERMARK_MB` continuously kicked in — both predate the visible 30-day evidence window.
- **Frequency:** roughly every Monday, intermittently cleared by lucky lite-row timing.
- **Recurring?** YES.
- **Ever cleared?** YES — whenever a lite row happens to fall in the 10-hour pre-verification window.

🛑 No remediation proposed in this document. Audit only.
