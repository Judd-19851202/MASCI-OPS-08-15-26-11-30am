# TRACK 20.8 · Rollback Checklist

## Rollback triggers

Roll back production if ANY of the following occur within 24 hours of deploy:

- `/api/health/full` returns 503 for > 5 minutes.
- Trust-spine emits `status="failed"` at `STAGE_PROVIDER_ACCEPTED` for real records (Resend delivery failures) at rate > 5% of submits.
- Real users report camera capture failures on Daily Report (regression on Track 20.7 fix).
- Real users report unable-to-sign-in issues > 3 reports.
- Backend supervisor restarts > 3 times in an hour (crash loop).
- Any real record submit accidentally triggers a synthetic-test-record skip (would mean production data uses `TEST_` prefix — should never happen; would indicate a data-integrity issue).
- Any live email dispatch to an unintended recipient.
- MongoDB connection failures > 1% of requests.

## Rollback procedure

1. **User-facing**: use the Emergent platform's rollback / previous-checkpoint feature. This is the fastest and safest option — it takes the codebase back to the pre-deploy checkpoint (Track 20.7 · confirmed green).
2. **DO NOT** attempt manual `git reset` on production. The Emergent rollback flow preserves audit + backup state; git reset does not.
3. **After rollback**: verify `/api/health` and `/api/health/full` both return 200 against the rolled-back version.
4. **Post-mortem**: classify the failure per Track 20.6A doctrine (A/B/C/D). File a new Debt Register entry. Determine the fix scope in a follow-up track (20.9+ or a phased retry of 20.8).

## Rollback-safe changes made in Tracks 20.6B + 20.7 + 20.8

All changes in this release are **additive** and rollback-clean:

- **Track 20.7** — one surgical guardrail on `frontend/src/components/PhotoUpload.jsx`. Rollback removes the fallback → desktop users go back to the original silent-no-op (the pre-Track-20.7 status quo). No data loss.
- **Track 20.6B** — one surgical `if` clause at the top of `_dispatch_auto_email` in `backend/server.py`. Rollback removes the synthetic-test-record short-circuit → tests would resume triggering live emails, but real records would be unaffected. No data loss.
- **Track 20.8** — documentation only. No code diff. Rollback has no code impact.

## Data integrity on rollback

- **Zero data migration** was performed in Tracks 20.6B / 20.7 / 20.8. All Mongo collections and their schemas are identical before and after this release.
- **Zero collection deletion**. Rollback is safe on the data layer.
- **Zero schema evolution** on any existing collection. No backwards-incompatible field additions.

## Deployment-time snapshot / backup

Per the Emergent platform's standard practice, a pre-deploy backup is captured automatically. Restoration path is via the platform's checkpoint UI.

## Verdict

🟢 **Rollback path clean and low-risk.** Any rollback within the first 24h post-deploy will restore the current preview state exactly, with zero data loss.
