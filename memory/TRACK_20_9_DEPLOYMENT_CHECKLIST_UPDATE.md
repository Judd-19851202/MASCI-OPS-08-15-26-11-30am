# TRACK 20.9 · Deployment Checklist Update Report

**File touched:** `/app/DEPLOYMENT_CHECKLIST.md`
**Prior version:** locked 2026-05-15 · iter142 · Phase-1 Iter D.
**New version:** locked 2026-08-04 · Track 20.9.

## What changed (structural)

| Section | Prior version | New version |
|---|---|---|
| Header locking date | 2026-05-15 (iter142) | 2026-08-04 (Track 20.9) — supersedes prior. |
| §0 Pre-flight | Deploy-readiness banner + qa_audit + integration probes. | Track 20.8 release-gate certification: full regression envelope · deployment-agent static scan · frontend build clean · lint gate · debt-register clean. |
| §1 Email-Safety Certification | **NOT PRESENT** in prior. | **NEW MANDATORY SECTION.** Source-level presence check on `_dispatch_auto_email` short-circuit · runtime evidence via backend logs · grep confirming no email transports in touched tests · `TEST_` prefix mandate. |
| §2 Photo Capture Smoke | **NOT PRESENT.** | **NEW.** Track 20.7 fallback verification on both desktop-no-webcam and mobile-with-camera devices. |
| §3 Operational Threads Smoke | **NOT PRESENT.** | **NEW.** All six Universal Threads (Employee · Project · Vendor · Asset · Incident · Fleet Unit) + Fire Protection linked-extinguisher check. Confirms canonical `/dispatch-portal` route. |
| §4 Env-var diff | Present, iter142 shape. | Present, updated with `SCHEDULER_ENABLED`, `REACT_APP_BACKEND_URL`, correct 20.6B email-safety commentary. |
| §5 Post-deploy smoke | Backend + frontend smoke sections. | Kept, expanded: `/api/health/full` · multi-login portal_tokens bundle · trust-spine lifecycle verification for one real submission. |
| §6 Post-deploy monitoring | Present. | Rewritten to include trust-spine `status="failed"` watch, `synthetic_test_record` audit watch (expected empty on prod), backup scheduler watch. |
| §7 Rollback | Present. | Now references `memory/TRACK_20_8_ROLLBACK_CHECKLIST.md` as authoritative playbook. |
| §8 Known-mocked integrations | Present. | Preserved verbatim (MaintainX + Motive both `disabled` — architectural guardrail locked 2026-05-14). |

## What was preserved verbatim

- Supervisor restart sequence (backend first, sleep, verify, frontend second).
- Known-mocked integrations doctrine.
- ADMIN_HMAC_SECRET rotation + ADMIN_SESSION_EPOCH bump rules.
- Deep-probe expectations (`overall_status in (ready, attention)`).

## Zero-drift

Doc-only change. No route, no permission, no runtime touched.
