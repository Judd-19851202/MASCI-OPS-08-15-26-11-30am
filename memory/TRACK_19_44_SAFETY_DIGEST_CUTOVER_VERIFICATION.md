# TRACK 19.44 · Safety Digest Cutover Verification

Track 19.43 shipped the operator-controlled `OI_ENGINE_SAFETY_MORNING_LIVE`
gate. Track 19.44 confirms it still functions correctly and documents the
operator cutover procedure.

## Gate verified

- File: `/app/backend/safety_digest.py::_enabled()`.
- Env flag: `OI_ENGINE_SAFETY_MORNING_LIVE`.
- Behaviour: `true` short-circuits legacy `_enabled()` to False regardless of `SAFETY_DIGEST_ENABLED`.
- Test coverage: `test_track_19_43_fleet_hr_intelligence.py::test_cutover_gate_disables_legacy_safety_digest` — 🟢 still GREEN.

## Operator cutover procedure (documented — not executed by this track)

1. **Dry-run comparison** — POST `/api/operational-intelligence/safety_morning_digest/dispatch?dry_run=true`. Verify audience + subject + section content match the legacy Track 19.39 output.
2. **Recipient reconciliation** — confirm all current `SAFETY_DIGEST_TO_EMAIL` addressees are present as active rows in `morning_digest_recipients` with `digest_type=safety_morning_digest`. Add any missing.
3. **Notify stakeholders** — internal note to Safety leadership that Monday's email will come from the OI engine.
4. **Flip the gate** — production env: `OI_ENGINE_SAFETY_MORNING_LIVE=true`. Restart affected worker if applicable.
5. **First Monday** — trigger `POST /api/operational-intelligence/safety_morning_digest/dispatch?dry_run=false` manually (or wait for scheduler once wired).
6. **Verify** — confirm ONE recipient email delivered · legacy `scheduler_runs.safety_digest` shows no new rows after gate flip.
7. **Two-week soak** — leave gate ON for two weeks. Monitor complaints / delivery issues.
8. **Cleanup** — after successful soak, follow-up track archives `safety_digest.py` (still preserved for rollback).

## Rollback

Set `OI_ENGINE_SAFETY_MORNING_LIVE=false` (or delete the env var). Legacy cron resumes on next iteration. HIGH confidence.

## Status

- Preview env: gate not required (scheduler globally disabled).
- Production env: **awaiting operator confirmation** — no automatic cutover from this track.
