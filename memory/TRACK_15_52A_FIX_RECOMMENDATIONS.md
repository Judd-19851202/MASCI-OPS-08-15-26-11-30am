# TRACK 15.52A · Fix Recommendations

**Status:** Evidence-based · only safe fixes proposed · zero urgent.

## Summary

Based on the forensic audit, **no urgent code change is required**. The backup engine is healthy and on the documented cadence; the previously-flagged observability defect on `/api/health/full` is already fixed in Track 15.52 (applied to preview, awaiting production rollout via the standard deploy path).

The recommendations below are graded by safety + priority. Apply only what the operator chooses; none of them are deployment blockers.

## R1 · Propagate Track 15.52 R2-direct truth source to production (LOW-RISK · RECOMMENDED)

**What:** Deploy the current preview build to production. Track 15.52 added `_r2_backup_age_seconds_cached()` and modified `/api/health/full` to consult R2 directly with a fallback to the existing `backup_health` DB row.

**Why:** Production currently relies on the in-DB audit row alone. If a worker restarts between R2 upload + audit-row write (a rare but possible race), the row drifts stale and `/api/health/full` would return 503 for up to 26h. Track 15.52's R2-direct check eliminates that class of false-red.

**Risk:** Very low. Same code path as `/api/admin/backups-list-r2` (already proven in production). 5-min cache prevents R2-list amplification. Contract test `test_iter183_health_full_endpoint.py` still passes 3/3. Stale-R2 negative test still trips 503.

**How:** Normal deploy. No env var changes required. No new collections, no new scheduler.

## R2 · OPTIONAL · Close the Track 15.37/15.38 operator gate (BUSINESS DECISION)

**What:** Operator confirms (one-time, dashboard lookups documented in `TRACK_15_38_LEGACY_BACKUP_AUDIT.md`):
1. Atlas Continuous Backup / PITR enabled on `masci-prod.1nduwmg.mongodb.net`.
2. R2 bucket versioning enabled on `masci-hub`.

After confirmation, flip the cadence env vars on production:
- Unset `BACKUP_R2_HOURLY` (or set to `false`).
- Set `BACKUP_HOURS_LOCAL=0,6,12,18` + `BACKUP_TIMEZONE=America/New_York` (or tenant-appropriate TZ).

**Why:** The Track 15.37 cost analysis projected a **−66 % R2 storage cost** ($44 → $15/year per the original sizing) by dropping from 24/day → 4/day. With current 650 MB zips, that's ~21 GB/day → ~7 GB/day = ~14 GB/day less write traffic.

**Risk:** Documented as YELLOW in Track 15.37. Atlas PITR provides the sub-hour RPO independently; R2 versioning protects against accidental delete. Without those two safety nets the cadence cut would weaken posture.

**How:** Two-line env change in production. No code change required (the `_parse_backup_hours()` mechanism shipped in Track 15.38 supports this).

## R3 · DEFER · `backup_health` audit-row reliability cleanup (LOW-VALUE)

**What:** Track down why production's `backup_health` collection occasionally misses `mode=complete-r2` audit rows even when the upload succeeded. The row is best-effort (line 6246 comment: `Best-effort — a Mongo write failure must not break backups`); investigation would profile `_record_backup_health` for transient Atlas write timeouts.

**Why:** Now that `/api/health/full` (post-Track 15.52) no longer depends solely on `backup_health`, the operational impact of audit-row gaps is near-zero. They remain a minor data-quality nuisance for `/api/admin-strict/diag/persistence-health` (which still uses the DB row · `routes/admin_persistence_health.py:_last_backup_time`).

**Recommendation:** Defer to a calmer track. Not urgent.

## R4 · NOT RECOMMENDED · Add a new backup scheduler / replace existing one

**Explicitly out of scope per Track 15.52A hard rules:** no V2 backup systems, no new schedulers, no duplicate paths. The current single-path architecture (`_backup_scheduler_loop` → `_run_complete_archive_to_r2` → R2 → tiered retention) is correct.

## R5 · NOT RECOMMENDED · Modify `production-health-probe.yml`

**Why not:** The workflow is functioning as designed. All 5 probes pass against `mascidocs.com` as of 2026-06-19 20:50 UTC. Changing it would either weaken coverage or introduce new false-positives. If the operator can share a specific failed workflow run URL, we can revisit; without that, modification would be a guess.

## R6 · OPTIONAL · Operator runbook addendum (DOCUMENTATION)

**What:** Add one paragraph to the operator runbook clarifying:
> "GitHub Actions production-health-probe" (the cron-driven workflow) and "the production health probe" (UptimeRobot's external hit on `/api/health/full`) are TWO different probes. If the operator receives a GitHub-branded failure email, click through to the workflow run page to see which of the 5 endpoints failed — only those 5 are checked. UptimeRobot failures come via UptimeRobot's own dashboard and reference `/api/health/full`.

**Why:** This was the root of the apparent contradiction in the user prompt. A naming distinction eliminates future confusion.

**How:** Add to `/app/memory/OPS_RUNBOOK.md` (or wherever the operator playbook lives).

## Safe-fix application status

| Recommendation | Status | Files touched in this track |
|---|---|---|
| R1 · Propagate Track 15.52 to production | **Already in code** (preview build) · operator just needs to deploy | None new — fix already lives in `backend/server.py` |
| R2 · Close cadence operator gate | Operator decision pending | None — no code change |
| R3 · `backup_health` reliability | Deferred | None |
| R4 · New scheduler | Explicitly rejected | None |
| R5 · Workflow modification | Not warranted | None |
| R6 · Runbook clarity | Optional docs | None in this track |

**No files were modified during this audit.** This is a read-only forensic track per the user's hard rules ("VERIFY EVERYTHING FROM LIVE CODE, LIVE CONFIGURATION, LIVE R2 DATA").
