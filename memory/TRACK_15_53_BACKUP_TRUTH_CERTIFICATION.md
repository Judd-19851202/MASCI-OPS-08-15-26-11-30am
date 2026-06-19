# TRACK 15.53 · Backup Truth Certification

**Status:** Post-change snapshot · captured 2026-06-19 21:45 UTC.

## Protection-layer matrix

| Protection Layer | Status | Evidence |
|---|:---:|---|
| **Hourly backup** | ✅ ACTIVE | Newest object 2026-06-19 21:06:37 UTC (38 min before audit) · `r2_hourly: true` on prod · scheduler firing on cadence |
| **R2 versioning** | ❌ **NOT ENABLED** | Cloudflare R2 does not implement `PutBucketVersioning` via the S3-compatible API. Operator must enable via dashboard. See `TRACK_15_53_R2_VERSIONING_IMPLEMENTATION.md`. |
| **Lifecycle** | ✅ **ALIGNED WITH APP RETENTION** | `masci-backups-auto-365d · Expiration: 365 days · Filter: backups/auto-90d/ · Enabled` (changed from 90 d in this track) |
| **App retention** | ✅ ACTIVE — now the single source of truth | `backend/lib/r2_retention.py` Tier 1 14 d hourly · Tier 2 90 d daily · Tier 3 365 d monthly · Tier 4 delete |
| **Monthly retention** | 🟡 PATH ENABLED, AWAITING BUCKET AGE | Tier 3 logic verified working via synthetic 365-d dataset; will begin producing monthly survivors at Day 90 (~2026-08-09) |
| **Long-term retention (> 365 d)** | 🔴 NOT IMPLEMENTED | App Tier 4 deletes at 365 d. R2 lifecycle backstops at 365 d. There is no preserved archive beyond 1 year unless Atlas snapshots cover it. |
| **PITR (Atlas)** | ⚠ UNVERIFIED | Operator dashboard task — see `TRACK_15_53_ATLAS_PROTECTION_AUDIT.md` |
| **Snapshot recovery (Atlas)** | ⚠ UNVERIFIED | Same |
| **Object lock (R2)** | ❌ NOT CONFIGURED | `ObjectLockConfigurationNotFoundError` on bucket — out of scope for this track |
| **Replication (R2)** | ❌ NOT CONFIGURED | `ReplicationConfigurationNotFoundError` on bucket — out of scope for this track |
| **Backup pipeline post-change** | ✅ UNAFFECTED | 854 objects · 207.8 GB · HEAD on newest backup returns 200 · `mascidocs.com/api/health/full` returns 200 |

## Headline changes in this track

| Before | After |
|---|---|
| R2 lifecycle rule `masci-backups-auto-90d` · Expiration 90 d · would have deleted Tier 3 monthly survivors on 2026-08-29 | R2 lifecycle rule `masci-backups-auto-365d` · Expiration 365 d · matches app Tier 4 boundary exactly |
| Two engines disagreeing (silent data loss forecast 2026-08-29) | One source of truth (app `lib/r2_retention.py`) · lifecycle is a longstop backstop |
| Retention ceiling at 90 d | Retention ceiling at 365 d (subject to bucket aging) |
| Versioning OFF, no path forward | Versioning OFF, operator path documented |

## Six-pillar pass-through

| Pillar | Status |
|---|:---:|
| Powerful (recovery posture improved?) | ✅ — the structural barrier to 90-d / 180-d / 365-d recovery has been removed |
| Simple (use existing systems?) | ✅ — no new code, no new collection, no new scheduler, no new bucket; one rule edited, app retention unchanged |
| Beautiful (auditable state?) | ✅ — both engines now agree at the 365-d boundary; rule names match policy ("auto-365d" vs old "auto-90d") |
| Trusted (verifiable?) | ✅ — every claim above has a `boto3` call, an HTTP response, or a code line |
| Proven (verified live?) | ✅ — backup pipeline unaffected (854 unchanged), production probe 200 |
| Fix-It (defects addressed?) | 🟡 — lifecycle conflict fixed; versioning gap documented + operator action assigned |

## What MASCI can claim with full evidence today

> "MASCI's R2 backup is on hourly cadence with tiered retention 14-d hourly + 90-d daily + 365-d monthly + 365-d longstop. App-side retention is the single source of truth. The retention path for 90 / 180 / 365-d recovery is enabled and will fill in as the bucket ages past Day 90 (~2026-08-09)."

## What MASCI cannot yet claim

- "R2 backups are protected against accidental delete." (Versioning off.)
- "MASCI has verified Atlas PITR coverage for restores older than the bucket age." (UNVERIFIED.)
- "MASCI has data older than 39 days in R2 today." (Bucket too young — but path is open.)

## Final certification

🟢 **GREEN with two carry-forward yellows:** R2 versioning (operator-fixable) and Atlas PITR verification (operator-fixable). Backup integrity is improved on the highest-priority axis (retention conflict eliminated · forecast 2026-08-29 data loss prevented). Production hourly cadence remains in place and is healthy.
