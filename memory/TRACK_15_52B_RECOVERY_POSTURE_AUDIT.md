# TRACK 15.52B · Recovery Posture Audit

**Status:** Evidence-based · assumes Atlas PITR status is **UNVERIFIED** per `TRACK_15_52B_ATLAS_PROTECTION_AUDIT.md`. Each scenario shows the posture under the two possible Atlas states.

## Definitions

- **RPO (Recovery Point Objective):** Maximum data loss tolerated in a worst-case disaster — i.e. the time gap between the last good backup point and the moment of disaster.
- **RTO (Recovery Time Objective):** Time from disaster declaration to a working, verified, point-in-time-consistent application.

## Current state · HOURLY cadence

| Scenario | Best-case restore point | Worst-case restore point | Effective RPO | RTO |
|---|---|---|---|---|
| **Atlas PITR enabled** (M10+ tier with continuous backup) | T − 1 minute (PITR oplog) | T − 1 minute (PITR oplog) | **~1 minute** | ~30 min (Atlas restore button → DNS cutover) |
| **Atlas PITR DISABLED** (free tier / not configured) | T − 5 minutes (last R2 upload finished) | T − 60 minutes (just before next hourly upload starts) | **60 minutes** | ~30 min (R2 download → `restore_drill.py` → DNS cutover; proven 17.7 s for 138k records in Track 15.37 drill) |
| **R2 unreachable AND Atlas PITR off** | last Atlas scheduled snapshot (~24 h) | last Atlas scheduled snapshot (~24 h) | **up to 24 h** | ~30 min |

## Proposed state · 6-HOURLY cadence

| Scenario | Best-case restore point | Worst-case restore point | Effective RPO | RTO |
|---|---|---|---|---|
| **Atlas PITR enabled** | T − 1 minute (PITR oplog) | T − 1 minute (PITR oplog) | **~1 minute** | ~30 min |
| **Atlas PITR DISABLED** | T − 5 minutes (last R2 upload finished) | T − 360 minutes (just before next 6h upload starts) | **360 minutes** | ~30 min |
| **R2 unreachable AND Atlas PITR off** | last Atlas scheduled snapshot (~24 h) | last Atlas scheduled snapshot (~24 h) | **up to 24 h** | ~30 min |

## Side-by-side delta

| State of Atlas PITR | Hourly worst-case RPO | 6-hourly worst-case RPO | Δ |
|---|---:|---:|---:|
| **ENABLED** | 1 min | 1 min | **0 min** — no change |
| **DISABLED** | 60 min | 360 min | **+300 min worse** — 6× degradation |

## Operational impact analysis

### If Atlas PITR is verified ON
- R2 hourly is **redundant** for RPO purposes — Atlas PITR provides sub-minute RPO independent of R2 cadence.
- R2's value is for **disaster recovery** (Atlas-region outage) and **cold restore drills**, both of which work fine on 6-hourly cadence.
- The cost saving ($17/year) is the only meaningful benefit; risk delta is zero.
- **Decision: switch to 6-hourly is SAFE.**

### If Atlas PITR is verified OFF or DOWNGRADED
- R2 hourly is **the only sub-hour RPO mechanism**. Switching to 6-hourly degrades the RPO from 60 min → 360 min in the worst case.
- For a safety-critical platform supporting workplace-violence-incident defensibility, witness statements, and OSHA-recordable training records, a **6-hour data-loss window** is materially worse than a 1-hour window.
- **Decision: switch to 6-hourly is UNSAFE without Atlas PITR first being confirmed.**

## Practical recovery-time evidence

Track 15.37 (2026-02) ran a live restore drill from R2 zip into the preview pod's isolated drill DB:
- 138,464 records / 160 collections / 632.7 MB archive.
- Drill restore completed in **17.7 seconds** with zero errors.
- Cross-env guard correctly rejected production→preview attempts.

So R2-based RTO is in the seconds-to-minutes range for the restore itself; the dominant RTO is DNS cutover and verification, not the restore. Cadence does not affect RTO.

## What 6-hourly DOES preserve

| Property | Hourly | 6-hourly |
|---|:---:|:---:|
| Tier 1 hourly preservation (0-14 d) | 336 archives | 56 archives |
| Tier 2 daily survivors (14-90 d) | 76 archives | 76 archives |
| Daily granularity for forensics | ✅ | ✅ |
| Cross-environment restore drill | ✅ | ✅ |
| Audit-trail completeness | ✅ | ✅ |
| Forensic ability to identify "what existed at hour H of day D" within last 14 days | ✅ (24 fixed points/day) | ⚠ (4 fixed points/day · 6 h between snapshots) |

## SECTION F summary

The 6-hourly cadence change is **safe if and only if Atlas PITR is verified ON**.

If Atlas PITR is ON, R2 cadence is a redundant safety net and reducing it to 6 h costs $17/year less for zero RPO impact.

If Atlas PITR is OFF, R2 hourly is the only sub-hour-RPO mechanism, and degrading it to 6 h means the platform's worst-case data loss for a safety-critical system grows from 60 min to 360 min — a **6× regression** that should not be approved on cost grounds alone.

The bottleneck for this decision is therefore **Section C's UNVERIFIED Atlas PITR status**, not Section E's cost numbers.
