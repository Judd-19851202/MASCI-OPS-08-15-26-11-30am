# TRACK 20.8 · Deployment Checklist

## Pre-deploy verifications (all complete)

- [x] `deployment_agent` static scan: **PASS**.
- [x] Test envelope: **384/385 green** (1 legitimate design-branch skip).
- [x] Track 20.6B lock test: **18/18 green**.
- [x] Track 20.7 lock test: **24/24 green**.
- [x] All Universal Thread lock tests: **green**.
- [x] Live browser smoke on public Daily Report: **green** (Track 20.7 fallback proven).
- [x] Live curl on every certified endpoint category: **all expected status codes**.
- [x] Email safety structurally enforced: **verified via backend logs**.
- [x] Zero OPEN debt at deployment gate.
- [x] PRD.md + CHANGELOG.md + TECHNICAL_DEBT_REGISTER.md updated.
- [x] 15 Track 20.8 deliverable docs on disk.
- [x] Lock test `test_track_20_8_deployment_certification.py` on disk.

## Deployment day steps

1. **Merge** current state to production branch via the "Save to GitHub" flow (do NOT git push manually — direct users to the Emergent Save to GitHub feature).
2. **Trigger** production deploy via the Emergent deploy button.
3. **Verify** production `https://<app>.emergent.host/api/health` → 200.
4. **Verify** production `https://<app>.emergent.host/api/health/full` → 200 (deep probe: mongo · scheduler · backup_recent all healthy).
5. **Login smoke** — sign in as super-admin on production. Confirm all 7 portal tokens mint. Confirm redirect to `/admin`.
6. **Public smoke** — hit `/daily/submit` on production. Confirm form renders. Confirm photo upload works (via desktop file picker in the deploy environment).
7. **Real workflow smoke** — submit a real (non-`TEST_`) Daily Report. Confirm auto-email fires (production `AUTO_EMAIL_REPORTS=true`).
8. **Trust-spine smoke** — check `trust_spine_events` collection for the record. Expect `STAGE_ROUTING_RESOLVED → STAGE_RECIPIENTS_BUILT → STAGE_NOTIFICATION_QUEUED → STAGE_PROVIDER_ACCEPTED → STAGE_COMPLETED` all `status="ok"`.

## Post-deploy monitoring (first 24 hours)

- Watch `/api/health/full` for degradation (Uptime Robot / equivalent).
- Watch Resend delivery dashboard for bounces / delayed sends.
- Watch trust-spine events for any `status="failed"` on real submits.
- Watch backend supervisor logs for any startup or scheduled-task failure.
- Watch backup scheduler: expect a healthy backup within 26h (matches `/api/health/full` `backup_recent` probe).

## Post-deploy verification queries

Run on production DB after first real submit:

```javascript
// Verify real records dispatch (should return "ok")
db.trust_spine_events.find({
  workflow: "daily-report",
  stage: "notification_queued"
}).sort({ts: -1}).limit(5)

// Verify Track 20.6B skip audit fires for any accidental TEST_ record on prod
db.trust_spine_events.find({
  failure_reason: "synthetic_test_record"
}).sort({ts: -1}).limit(5)
```

Real production should show `status="ok"` on the first, and an empty result on the second (production data does not use TEST_ prefixes).

## Deployment call

🟢 **DEPLOY.**
