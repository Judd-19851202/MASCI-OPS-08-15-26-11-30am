# TRACK 15.52A · Root Cause Analysis

**Status:** Evidence-only · cross-references TRACK_15_52A_BACKUP_TRUTH_AUDIT.md, TRACK_15_52A_HEALTH_PROBE_FORENSICS.md, TRACK_15_52A_BACKUP_ARCHITECTURE_MAP.md.
**Question:** Of the five candidates (A/B/C/D/E), which is the root cause?

## Candidate evaluation

### A · "Backup cadence change never happened"

Evidence:
- Track 15.37 explicitly stated `Cadence env var NOT flipped (BACKUP_R2_HOURLY still true)`.
- Track 15.38 explicitly stated `Production env vars NOT flipped (BACKUP_R2_HOURLY still true · BACKUP_HOURS_LOCAL not set on prod)`.
- Track 15.38 explicitly stated `Atlas + R2 verification status: ❓ OPERATOR REQUIRED — both gates`.
- Live prod env confirms `BACKUP_R2_HOURLY=true`, mean R2 backup spacing = **59.8 min** (HOURLY).

Verdict: **Partially true.** The cadence change was a documented PROPOSAL gated on operator verification (Atlas PITR + R2 versioning). The gate is still open. Production has continued hourly per the documented behavior. The "change" never deployed because it was never approved to deploy.

### B · "Backup cadence changed but health probe is wrong"

Evidence:
- Cadence did NOT change (see A).
- Health probe (`/api/health/full`) had a real defect — it queried `backup_health` audit row which can drift stale.
- Defect was identified and fixed in Track 15.52 (already applied to preview).

Verdict: **First half FALSE, second half TRUE.** Cadence is unchanged; the probe defect was real, was found, and was fixed.

### C · "Multiple backup systems exist"

Evidence:
- `TRACK_15_52A_BACKUP_ARCHITECTURE_MAP.md §5` audit:
  - One scheduler loop (`_backup_scheduler_loop`).
  - One R2 uploader (`_run_complete_archive_to_r2`).
  - Singleton-lock via `scheduler_locks` collection prevents multi-worker races.
  - No OS cron, no systemd timer, no Cloudflare Worker, no Atlas Trigger.
  - `backup_verification.py` is a weekly PROBE, not a backup creator.
  - `automated_drill.py` is a RESTORE drill, not a backup creator.

Verdict: **FALSE.** Single backup-creator path. No duplicates.

### D · "Documentation is wrong"

Evidence:
- Track 15.51 documents stated "855 hourly snapshots, hourly cadence" — this is FACTUALLY CORRECT (verified: 50 most-recent objects show 59.8-min mean spacing).
- Track 15.51 PHASE 8 doc flagged the YELLOW finding (`/api/health/full` audit-row drift) — accurate.
- Track 15.52 doc described the R2-direct fix — accurate.

Verdict: **FALSE.** Existing documentation is consistent with current architecture. The user's perceived contradiction stems from conflating an APPROVED-BUT-NOT-DEPLOYED proposal (Track 15.37/15.38) with deployed state.

### E · Combination of A + B (partial)

Evidence: A is partially true (cadence change was approved as proposal, never deployed) AND the health-probe defect identified in Track 15.52 was real.

Verdict: **TRUE root cause.**

## Root cause statement (evidence-anchored)

> The platform is correctly running the intended cadence (hourly · `BACKUP_R2_HOURLY=true`) because the approved 6-hour cadence change from Track 15.37 was a PROPOSAL **explicitly conditional** on an operator gate (Atlas PITR + R2 versioning) that has not been closed. The cadence has not regressed.
>
> A SEPARATE defect — `/api/health/full` deriving `backup_recent` from a single Mongo audit row that can drift stale even while R2 backups succeed — was identified and fixed in Track 15.52 (R2-direct truth source with 5-min in-process cache, falling back to the DB row only when R2 is unreachable). This fix is applied to preview; propagation to production will happen on the next deploy.
>
> No duplicate backup system exists. No orphan worker is creating extra archives. No documentation is incorrect. The operator's perceived contradiction is a misattribution: the "approved" cadence change was a CONDITIONAL approval, not a DEPLOYED change — exactly as Tracks 15.37 + 15.38 explicitly recorded.

## Required-output table

| Field | Value |
|---|---|
| **INTENDED BACKUP CADENCE** | 6-hour (`BACKUP_HOURS_LOCAL=0,6,12,18`), **conditional** on Atlas-PITR + R2-versioning operator gate · gate still open |
| **ACTUAL CONFIGURED CADENCE** | HOURLY (`BACKUP_R2_HOURLY=true` on production env) |
| **ACTUAL R2 CADENCE** | HOURLY (mean 59.8-min inter-backup delta across 50 most-recent objects · 855 total in bucket) |
| **ACTIVE BACKUP JOBS** | ONE: `_backup_scheduler_loop._run_complete_archive_to_r2` (server.py:7138) on production worker only · preview pod has `SCHEDULER_ENABLED=false` |
| **CANONICAL BACKUP SYSTEM** | `_backup_scheduler_loop` (single-worker via `scheduler_locks` singleton) writing to `s3://masci-hub/backups/auto-90d/` with tiered retention 14d/90d/365d |
| **HEALTH PROBE CHECKS** | Pre-Track-15.52: `db.backup_health.find_one({ok:true})` age < 26h. Post-Track-15.52 (preview): R2 `LastModified` of newest `backups/` object age < 26h, with DB fallback. |
| **GITHUB ALERT ROOT CAUSE** | **Unverified.** Live execution of `production-health-probe.yml` against `mascidocs.com` at 2026-06-19 20:50 UTC: ALL 5 probes PASS. The workflow does **not** consult `/api/health/full`. Most likely source of operator-visible alert emails: **UptimeRobot** (the documented external consumer of `/api/health/full`) intermittently 503-ing on the audit-row-drift defect that Track 15.52 already fixed. Without a failed workflow-run URL I cannot evidence GitHub-Actions failures. |
| **MATCHES INTENT** | **YES** — current state matches what Tracks 15.37 + 15.38 explicitly deployed (cadence flip deferred to operator gate; flip env vars left unchanged). |
| **DEPLOYMENT IMPACT** | **NONE** — backups are healthy, fresh, and on the documented cadence. Production health-probe targets ALL pass. No regression. |
| **REQUIRED FIXES** | See `TRACK_15_52A_FIX_RECOMMENDATIONS.md` · one optional (propagate Track 15.52 R2-direct fix to production at next deploy as defense-in-depth) · zero urgent. |
