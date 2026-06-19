# TRACK 15.52B · Contradiction Analysis

**Status:** Read-only review of Tracks 15.37, 15.38, 15.52, 15.52A against today's live production evidence.

## Track 15.37 — re-read against live evidence

| Claim from Track 15.37 (2026-02) | Verdict |
|---|:---:|
| "Restore drill completed: 138,464 records · 17.7 s · zero errors" | ✅ **Accurate.** Cited as RTO evidence in `TRACK_15_52B_RECOVERY_POSTURE_AUDIT.md`. |
| "Cadence env var NOT flipped (`BACKUP_R2_HOURLY` still `true`)" | ✅ **Accurate.** Live `mascidocs.com/api/admin/backups-complete-r2-state` returns `r2_hourly: true`. |
| "Legacy backups frozen between 2026-05-15 22:30 and 2026-05-17 21:24 UTC — ~500 objects · ~12 GiB" | ⚠ **Partially accurate.** Count of 500 is correct. **Size estimate (~12 GiB) was low** — actual is 22.51 GB across the full 2026-05-11 → 2026-05-17 window. The doc's stated window (15-17 May) is also a subset of the actual span (11-17 May). |
| "Switch to every-6-hours: cost −66 % · $44 → $15/year" | ⚠ **Cost basis was off.** Live: hourly $34.90/yr → 6-hourly $17.83/yr = −49% (≈ −$17/year). The −66% figure presumed an active-prefix size that was higher than reality (rev. up since), and excluded the legacy-prefix carry-cost ($4/yr) which the cadence change does not affect. **Direction of the conclusion is correct; magnitude was overstated.** |
| "AFTER operator confirms (i) Atlas PITR, (ii) R2 versioning" | ✅ **Still accurate.** Both gates remain open per `TRACK_15_52B_ATLAS_PROTECTION_AUDIT.md` + `TRACK_15_52B_R2_PROTECTION_AUDIT.md` (live `Versioning Status=None`). |

## Track 15.38 — re-read against live evidence

| Claim | Verdict |
|---|:---:|
| "Restore endpoint dual-manifest fix" | ✅ Verified — `routes/exports.py` accepts both `backup_manifest.json` and `MANIFEST.json`. |
| "Production env vars NOT flipped" | ✅ Live confirms unchanged. |
| "OPERATOR REQUIRED · Atlas Continuous Backup / PITR" | ✅ Still open. |
| "OPERATOR REQUIRED · R2 bucket versioning" | ✅ Still open · live `Versioning Status=None`. |
| `_parse_backup_hours()` precedence order documented | ✅ Verified by reading current `server.py:5698-5772`. |

## Track 15.52 — re-read against live evidence

| Claim | Verdict |
|---|:---:|
| "R2 has 855 hourly backups, latest 17 min before measurement" | ✅ **Accurate at the time.** Today's count: 854 objects (855 was the count at audit-time; bucket drifts by ±1 per hour as retention runs). |
| "Mean inter-backup spacing 59.8 min" | ✅ **Accurate.** Re-measured today: 58-64 min deltas across 10 consecutive samples. |
| Track 15.52 fix: `_r2_backup_age_seconds_cached()` consulting R2 directly | ✅ **Verified.** Live preview `mascidocs.com/api/health/full` returns 200. The R2-direct path works as designed. |
| Track 15.52 fix description: "Audit row can drift stale" | ✅ **Accurate.** `backup_health` collection in preview holds only 9 `complete-r2` rows despite R2 having 354 active objects · drift is real. |

## Track 15.52A — re-read against live evidence

| Claim | Verdict |
|---|:---:|
| "ONE backup-creator path · ZERO duplicates" | ✅ **Accurate.** `_backup_scheduler_loop → _run_complete_archive_to_r2` is the sole writer; verified via grep + execution path inspection. |
| "INTENDED 6-h cadence still gated on operator gate" | ✅ Live state still shows the gate open. |
| "ACTUAL R2 cadence HOURLY · mean 59.8 min" | ✅ Re-verified today. |
| "GitHub production-health-probe is NOT failing right now" | ✅ Re-verified — same 5 endpoints PASS today. |
| "MATCHES INTENT: YES" | ✅ Still accurate. |

## NEW contradictions discovered in this audit (not previously documented)

### Contradiction #1 — R2 lifecycle silently overrides app retention Tier 3

| Source | Statement |
|---|---|
| `backend/lib/r2_retention.py` (code) | "Tier 3 · 90-365 days · keep ONLY the newest zip per calendar month" |
| Cloudflare R2 bucket policy (live) | Rule `masci-backups-auto-90d` · Prefix `backups/auto-90d/` · **`Expiration: 90 days`** |
| Live cohort histogram | Zero objects in 90-365 d range |

**The app code intends to preserve monthly survivors for 365 days. R2 deletes them at 90 days. The two engines disagree silently — the R2 lifecycle wins.**

This was **not documented in Track 15.37 / 15.38 / 15.52 / 15.52A**. It is a new finding.

### Contradiction #2 — Track 15.37 cost projection was low

The "−66% cost reduction" projection assumed a higher current cost base than reality. Today: actual current cost is $34.90/year (not $44), and the 6-hour cost is $17.83 (not $15). Direction is still correct; magnitude is **−49%**, not **−66%**.

### Contradiction #3 — Track 15.37 legacy-prefix size was understated

Track 15.37 said "~12 GiB". Live measurement: **22.51 GB**. The 30 corrupted stubs + 470 pre-15.28A archives the doc enumerated were correct in COUNT but not in TOTAL SIZE.

## Things that were correct in prior tracks

- The fundamental architectural model (single scheduler, single uploader, singleton-locked, app + R2 retention).
- The "operator gate" framing for the cadence change.
- The R2 hourly observation in Track 15.52A.
- The Track 15.52 R2-direct health-probe fix is correctly implemented and functions live.

## Things that were misleading

- The Track 15.37 cost numbers (off by ~30%).
- The Track 15.37 legacy-prefix size (off by ~85%).
- The implicit assumption (across multiple tracks) that the app-side tiered retention is the **only** retention engine — when in fact R2 has its own lifecycle rule that overrides it past day 90.

## Things that were missing

- No prior track documented the R2-side lifecycle rule and its conflict with the app-side Tier 3 policy.
- No prior track measured the actual cohort distribution past 14 days.
- No prior track verified R2 bucket versioning / object-lock / replication status from live boto3 calls.

## SECTION H summary

The earlier tracks were **directionally correct** but **understated** in three places:
1. Cost projection: −66% → actual −49%.
2. Legacy prefix size: 12 GiB → actual 22.5 GB.
3. Effective monthly-tier retention: app claimed 365 d → R2 deletes at 90 d.

None of these change the *recommendation framework*. They do change the *numbers* the operator should base the decision on. This document is the corrected baseline.
