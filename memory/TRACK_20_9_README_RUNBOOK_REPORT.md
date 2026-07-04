# TRACK 20.9 · README / Runbook Report

**File touched:** `/app/README.md`
**Prior state:** single line — `# Here are your Instructions` (Emergent scaffold boilerplate).
**New state:** full 11-section MASCI runbook (2026-08-04 · Track 20.9).

## Section coverage

| # | Section | Purpose |
|---|---|---|
| 1 | Architecture at a glance | Snapshot of stack: React SPA + FastAPI + Mongo + R2 + Resend + Universal Threads + Trust Spine. |
| 2 | Boot the platform locally | Supervisor-managed services; hot-reload rules; log tails. |
| 3 | Run the tests | Exact `pytest` invocation for the Track-20.8 regression envelope. |
| 4 | Frontend lint | Real ESLint 9 gate — `yarn lint` and `yarn lint:strict`. Documents the Track 20.9 fixes. |
| 5 | Deploy | Points at `DEPLOYMENT_CHECKLIST.md`; never `git push` — use Emergent Save-to-GitHub. |
| 6 | Rollback | Points at `memory/TRACK_20_8_ROLLBACK_CHECKLIST.md`; Emergent Builds → Rollback flow. |
| 7 | Environment variables | Backend .env + frontend .env, with production-only annotations. |
| 8 | Health checks | `/api/health`, `/api/health/full`, `/api/admin/deploy-readiness` — expected shapes + escalation rules. |
| 9 | **Email-safety rule** | **READ BEFORE TESTING** section — mandatory `TEST_` prefix on `project_name` when submitting to any workflow endpoint; Track 20.6B doctrine. |
| 10 | Track discipline | Feature vs audit vs cleanup vs release-gate tracks; classification A/B/C/D per Track 20.6A. |
| 11 | Common runbooks | Backend won't start · "Take Photo did not open the camera" · "Restore did nothing" · HMAC rotation. |

## Why the email-safety section is placed prominently

The single largest deployment risk on the MASCI platform is a well-meaning engineer running a workflow-submit test against the preview backend without knowing about the `TEST_` gate. Because `AUTO_EMAIL_REPORTS=true` and Resend is fully wired in preview, any such run would spam real inboxes. The runbook now leads with this rule in bold.

## Zero-drift

Doc-only change. No runtime touched.
