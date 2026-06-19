# TRACK 15.52C · Long-Term Recovery Certification

**Status:** Read-only · evidence captured 2026-06-19 21:30 UTC.

## Question 5 — Can MASCI currently restore to specific points in time?

| Restore Point | Available? | Source | Evidence |
|---|:---:|---|---|
| **1 hour ago** | ✅ YES | R2 Archive | `backups/auto-90d/` newest object is 21 min old (`MASCI_complete_backup_2026-06-19_210637Z.zip` at 2026-06-19 21:06 UTC); restore drill proven at 17.7 s for 138k records in Track 15.37. |
| **24 hours ago** | ✅ YES | R2 Archive | 23 hourly archives between now and 24 h ago; mean delta 59.8 min. |
| **7 days ago** | ✅ YES | R2 Archive (Tier 1 hourly preservation active for 0-14 d) | ~168 hourly objects within last 7 d. |
| **30 days ago** | ✅ YES | R2 Archive (Tier 2 daily survivors 14-90 d) | 14 daily-survivor archives in 14-30 d cohort + 3 in 30-60 d cohort. |
| **90 days ago** | ❌ NO | Not available in R2 | Bucket is only 39 days old (created 2026-05-11). Oldest object is 39.30 d old. |
| **180 days ago** | ❌ NO | Not available in R2 | Bucket pre-dates this audit window by far less than 180 days. |
| **365 days ago** | ❌ NO | Not available in R2 | Bucket pre-dates this audit window by far less than 365 days. |

For 90+ days ago, the only theoretically possible source is **Atlas Continuous Backup / PITR** or **Atlas scheduled snapshots** — both of which are UNVERIFIED per `TRACK_15_52C_ATLAS_PROTECTION_AUDIT.md`.

## Comprehensive restore matrix

| Restore Point | R2 Archive | Atlas PITR | Atlas Snapshot | Legacy ZIP | Effective Best |
|---|:---:|:---:|:---:|:---:|:---:|
| 1 hour ago | ✅ | UNVERIFIED | UNVERIFIED | n/a | ✅ R2 |
| 24 hours ago | ✅ | UNVERIFIED | UNVERIFIED | n/a | ✅ R2 |
| 7 days ago | ✅ | UNVERIFIED | UNVERIFIED | n/a | ✅ R2 |
| 30 days ago | ✅ (Tier 2 daily) | UNVERIFIED | UNVERIFIED | n/a | ✅ R2 |
| 39 days ago (= bucket age) | ✅ (oldest legacy file 2026-05-11) | UNVERIFIED | UNVERIFIED | n/a | ✅ R2 |
| 40 – 90 days ago | ❌ (bucket too young) | UNVERIFIED | UNVERIFIED | ❌ (legacy ZIP frozen at 2026-05-17) | ⚠ UNVERIFIED |
| 90 days ago | ❌ | UNVERIFIED | UNVERIFIED | ❌ | ⚠ UNVERIFIED |
| 180 days ago | ❌ | UNVERIFIED | UNVERIFIED | ❌ | ⚠ UNVERIFIED |
| 365 days ago | ❌ | UNVERIFIED | UNVERIFIED | ❌ | ⚠ UNVERIFIED |

## Forward-looking restore-point degradation

The R2 retention ceiling will move:
- **Today (Day 39)**: max restorable from R2 = 39 days ago.
- **Day 90 (~2026-08-09)**: max restorable from R2 = 90 days ago. First Tier 4-equivalent deletion (R2 lifecycle fires) hits the oldest legacy zip.
- **Steady state**: max restorable from R2 = 90 days ago. App-side intent to keep monthlies 90-365 d is overridden by R2 lifecycle.

In other words, R2 will **never** be able to satisfy "restore 6 months ago" in the current configuration. Long-term recovery depends entirely on Atlas, whose protection level is **UNVERIFIED** today.

## Honest assessment

Today (2026-06-19), MASCI's verified recovery posture is:

- **0 – 39 days ago:** strong (R2 holds proof-of-day for every hour of the last 14 d, daily survivors for older).
- **40 – 90 days ago:** weak (R2 will eventually fill this gap as the bucket ages, but is empty today).
- **90 days – 1 year ago:** absent from R2 (forecast to remain absent due to lifecycle conflict).
- **1 year+ ago:** absent everywhere unless Atlas-managed snapshots are configured.

This is **not** the recovery posture the design implied. The design said 365-day archive coverage. The truth is ≤ 90 days.

## What MUST be true for MASCI to have genuine long-term recovery

One of:
1. **Atlas PITR is ON, configured for ≥ 7 days, with scheduled-snapshot retention extending to ≥ 365 days.** (UNVERIFIED.)
2. **R2 retains data ≥ 365 days.** Requires removing the 90-day lifecycle rule or routing monthly survivors to a non-lifecycle-managed prefix. Neither is in place.
3. **A separate immutable archive (Glacier-equivalent, write-locked, or off-Cloudflare) holds older snapshots.** Does not exist.

None of these are currently confirmed. The platform's *genuine* long-term recovery capability is therefore **NOT YET ESTABLISHED** as of 2026-06-19.

## Sign-off

R2 recovery is **healthy within the bucket-age window** (currently 39 days, ceiling 90 days at steady state). Long-term recovery (> 90 days) is **NOT ESTABLISHED** and depends entirely on Atlas, whose configuration is **UNVERIFIED**.
