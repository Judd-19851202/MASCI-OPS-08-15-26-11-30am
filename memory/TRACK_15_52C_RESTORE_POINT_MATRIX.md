# TRACK 15.52C · Restore Point Matrix

**Status:** Read-only · captured 2026-06-19 21:30 UTC.

## Required Question-5 table

| Restore Point | Available | Source |
|---|:---:|---|
| 1 hour | ✅ YES | R2 Archive |
| 24 hours | ✅ YES | R2 Archive |
| 7 days | ✅ YES | R2 Archive (Tier 1 hourly) |
| 30 days | ✅ YES | R2 Archive (Tier 2 daily) |
| 90 days | ❌ NO | Not Available (bucket is only 39 days old; would be UNVERIFIED via Atlas PITR even after bucket reaches 90d) |
| 180 days | ❌ NO | Not Available (Atlas PITR UNVERIFIED) |
| 365 days | ❌ NO | Not Available (Atlas PITR UNVERIFIED) |

## Same matrix with all four columns explicitly per the spec

| Restore Point | Atlas PITR | Atlas Snapshot | R2 Archive | Legacy ZIP | Not Available |
|---|:---:|:---:|:---:|:---:|:---:|
| 1 hour | UNVERIFIED | UNVERIFIED | ✅ | n/a | |
| 24 hours | UNVERIFIED | UNVERIFIED | ✅ | n/a | |
| 7 days | UNVERIFIED | UNVERIFIED | ✅ | n/a | |
| 30 days | UNVERIFIED | UNVERIFIED | ✅ | n/a | |
| 90 days | UNVERIFIED | UNVERIFIED | ❌ | ❌ | ⚠ Pending Atlas verification |
| 180 days | UNVERIFIED | UNVERIFIED | ❌ | ❌ | ⚠ Pending Atlas verification |
| 365 days | UNVERIFIED | UNVERIFIED | ❌ | ❌ | ⚠ Pending Atlas verification |

## Forward-projected matrix at Day 90 (≈ 2026-08-09)

Once the bucket reaches steady state and the R2 lifecycle has been running for ≥ 1 month, the matrix changes as follows:

| Restore Point | Atlas PITR | Atlas Snapshot | R2 Archive | Legacy ZIP | Effective |
|---|:---:|:---:|:---:|:---:|:---:|
| 1 hour | UNVERIFIED | UNVERIFIED | ✅ | n/a | ✅ R2 |
| 24 hours | UNVERIFIED | UNVERIFIED | ✅ | n/a | ✅ R2 |
| 7 days | UNVERIFIED | UNVERIFIED | ✅ | n/a | ✅ R2 |
| 30 days | UNVERIFIED | UNVERIFIED | ✅ | n/a | ✅ R2 |
| 89 days | UNVERIFIED | UNVERIFIED | ✅ (Tier 2 daily survivor) | n/a | ✅ R2 |
| 91 days | UNVERIFIED | UNVERIFIED | ❌ (deleted by R2 lifecycle) | n/a | ⚠ Atlas-only |
| 180 days | UNVERIFIED | UNVERIFIED | ❌ | n/a | ⚠ Atlas-only |
| 365 days | UNVERIFIED | UNVERIFIED | ❌ | n/a | ⚠ Atlas-only |

## Forensic notes

- "✅ R2" cells include all rows where the bucket holds an actual recoverable archive at that age. Restore drill in Track 15.37 proved end-to-end recovery in 17.7 s for 138k records.
- "❌ Not Available" cells are exactly the rows the operator should be most concerned about.
- "UNVERIFIED" cells are blockers — the operator must verify Atlas state before relying on those rows for go-live or for any operational claim.
- The matrix is **structurally consistent** with the lifecycle conflict documented in `TRACK_15_52C_RETENTION_TRUTH_AUDIT.md` and `TRACK_15_52C_R2_LIFECYCLE_FORENSICS.md`.

## Question 5 — direct answer

**MASCI can currently restore everything between 1 hour ago and 39 days ago from R2 with full confidence.** Anything older is not in R2 today (bucket-age limited), will not be in R2 at steady state (lifecycle-limited), and the only candidate fallback (Atlas PITR / Atlas Snapshot) is **UNVERIFIED**.
