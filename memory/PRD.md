# FORGEDOPS Daily Report Recovery PRD

## Original Problem Statement
FORGEDOPS LIVE PRODUCTION DAILY REPORT AI — FULL NON-SUBMIT FORENSIC DRY RUN.

Goal: fix the Daily Report so field crews can complete it top-to-bottom reliably, including AI summary generation and photo grounding, without losing data. The Daily Report creation flow is a **public field workflow** and must not require sign-in. Protected portals (admin, HR, PM, field leadership, transportation/dispatch, shop, safety) must remain authenticated.

## Product Boundary
- **Public / anonymous:** `/daily/submit` Daily Report creation workflow.
- **Authenticated only:** admin portal, HR portal, PM portal, field leadership, transportation/dispatch, shop, safety, and internal views of submitted reports.
- Public Daily Report drafts must restore by **device ID + report scope**, not by authenticated user identity.

## Current Architecture
- Frontend: React SPA
- Backend: FastAPI
- Database: MongoDB
- Async AI jobs: polling flow backed by MongoDB persistence
- Local resiliency: IndexedDB/local draft storage + local crew memory

## Key Files
- `/app/frontend/src/pages/NewDailyReportV3.jsx`
- `/app/frontend/src/components/daily-report/DailySummaryAssist.jsx`
- `/app/frontend/src/components/daily-report-v3/sections.jsx`
- `/app/frontend/src/components/daily-report-v3/SectionProjectConditions.jsx`
- `/app/frontend/src/lib/resiliency/useFormDraft.js`
- `/app/frontend/src/lib/resiliency/dailyReportScope.js`
- `/app/frontend/src/lib/crewMemory.js`
- `/app/backend/lib/async_jobs.py`

## What Was Already Completed Before This Fork
- Fixed Daily Report AI infinite spinner.
- Added Mongo-backed cross-pod persistence for async jobs.
- Repaired custom job manual entry controls.
- Fixed cited photo status incorrectly showing unavailable.
- Reduced false public session-expired interference on Daily Report-related endpoints.

## 2026-07-23 — Scope Correction + Public Workflow Hardening

### Implemented
- Removed authenticated actor coupling from the public Daily Report draft scope.
- Updated Daily Report scoped keys to use **project + report date + report instance** rather than auth actor identity.
- Updated `useFormDraft` with a `publicAnonymous` mode so public Daily Report drafts save and restore against the **device-scoped draft identity**, not logged-in portal identity.
- Removed public Daily Report summary-assist reliance on stable auth actor identity; summary-side draft persistence now uses device-scoped identity only.
- Removed `draftActorId` prop plumbing from Daily Report AI section usage.
- Reworked crew/setup memory to be **device + project + operator-context scoped** rather than auth-actor scoped, preventing shared-device contamination while keeping the flow public.
- Updated/extended related tests for the new public scope behavior.

### Verified Behavior
- `/daily/submit` loads anonymously with no login gate.
- Employees load from public roster endpoint.
- Equipment loads from public equipment endpoint.
- Suppliers/vendors load from public supplier endpoint.
- Anonymous autosave works.
- Anonymous restore after refresh works.
- Device-scoped draft identity is visible and active.
- Public AI summary draft endpoint works anonymously.
- Anonymous summary job polling reaches completed state.
- Protected portals were not modified as part of this scope correction.

## Public Daily Report PASS/FAIL Matrix

### P0
- **Public anonymous access to Daily Report:** PASS
- **Auth/login/session coupling removed from Daily Report draft flow:** PASS
- **Protected portals remain authenticated and out of scope:** PASS

### P1
- **Anonymous draft autosave:** PASS
- **Anonymous refresh restore:** PASS
- **Employees dropdown population:** PASS
- **Equipment dropdown population:** PASS
- **Subcontractor/vendor dropdown population:** PASS
- **AI summary section visible/reactive:** PASS
- **Anonymous summary generation backend contract:** PASS
- **Anonymous photo intelligence backend contract:** PASS

### Still Needing Dedicated Broader Certification
- **Tab close + full browser close/reopen restore proof:** PARTIAL / not fully re-certified in this pass
- **Wrong-draft precedence matrix across multiple same-device scenarios:** PARTIAL / core scope fixed, full scenario matrix still recommended
- **Regeneration after meaningful edits with stale-job overwrite proof:** PARTIAL / backend/job path healthy, targeted browser proof still recommended
- **Photo-analysis/citation invariant full parity audit:** PARTIAL / prior fixes exist, full matrix still recommended
- **Full end-to-end submit with signature from public flow:** PENDING final dedicated certification pass
- **Equipment rows/time UX canonical validation:** PENDING targeted UX verification

## Latest Test Evidence
- `/app/test_reports/iteration_25.json`
- `/app/daily_report_anonymous_public_api_test.py`
- `/app/daily_report_anonymous_public_api_test_results.json`

### Test Outcomes Recorded on 2026-07-23
- Frontend anonymous Daily Report QA: PASS
- Additional frontend public flow QA: PASS
- Backend anonymous public API contract QA: PASS

## 2026-07-23 — Release Closure Follow-up

### Narrow Scope Completed
- Fixed canonical submitted-report photo intelligence sync so the saved Daily Report record now reflects the submitted report's actual photo-intelligence outcome instead of stale draft-era status.
- Fixed evidence manifest photo status mapping so manifest `photos[].analysis_status` now matches the canonical photo-intelligence store for submitted records.
- Verified canonical Summary B persistence after regeneration using two distinct draft summary generations (A and B), then submitting B and confirming the saved record preserved B rather than A.

### Exact Commit
- `75f97eb4` — `daily report: sync canonical photo intel and certify summary B persistence`

### Certification Evidence
- Canonical photo-analysis/citation parity: PASS
  - Submitted record `DR-2026-03536` now shows:
    - `daily_reports.photo_intelligence_status = unavailable`
    - `/api/daily-reports/DR-2026-03536/photo-intelligence -> status=unavailable`
    - `/api/daily-reports/DR-2026-03536/evidence-manifest -> photos[].analysis_status=unavailable`
- Canonical Summary B persistence after regeneration: PASS
  - Generated distinct Summary A and Summary B for the same public Daily Report draft context.
  - Submitted Summary B.
  - Canonical saved record `DR-2026-03536` contains Summary B, not Summary A.
  - Saved `ai_accepted_summary_meta.report_state_signature = SUMMARY-B-CERT-SIGNATURE`.

### Final Verification State For This Narrow Follow-up
- Working tree clean after commit: YES
- Targeted backend tests from final commit: PASS

## Prioritized Backlog

### P0
- Complete final public Daily Report certification for signature + submit path in anonymous mode.

### P1
- Run explicit tab-close/browser-close reopen proof with device restore.
- Run stale/wrong-draft precedence matrix across project/date/operator combinations on shared device.
- Run regeneration-after-edits proof that stale summary jobs cannot overwrite newer intent.
- Run photo citation/analysis invariant reconciliation.
- Verify all dropdown-driven fields are represented correctly in the accepted AI summary.

### P2
- Add async job safety guards for oversized payloads, duplicate completions, and terminal-state overwrite protection in `/app/backend/lib/async_jobs.py`.

## Notes
- Daily Report work must stay **public and anonymous**.
- Do not use admin/test credentials for Daily Report creation testing.
- Use the marker `LIVE-AI-DRY-RUN-NO-SUBMIT` for dry-run scenarios and avoid unintended submission during non-submit verification.

## 2026-07-23 — MASCI OPS 8 C2 Deployment Identity & Automatic Governance Closure

### What changed
- Verified Preview frontend serve path: `craco start` compiles the actual browser-served bundle, so frontend release identity is now stamped before that compile path and exposed through `/release-identity.json`.
- Backend `/api/version` now compares backend runtime identity against the served frontend artifact identity (`served:http://127.0.0.1:3000/release-identity.json`) instead of relying only on a source file.
- Protected governance verification now follows the proven dual-token contract from `/api/auth/multi-login`: `X-Admin-Token` + `X-Directory-Token`.
- `/api/health/full` now evaluates backup freshness against the configured scheduler mode honestly: Preview `lite` backup mode uses recent successful backup evidence instead of a stale R2-only signal.
- Added automatic startup deployment verification that writes canonical idempotent ledger rows to `deployment_decisions` and canonical deployment audit/trust outcomes to `admin_audit` / OCC trust events.
- Hardened `scripts/post_deploy_verify.sh` to verify `/api/version`, `/api/health/full`, readiness, ledger read-back, and trust-event read-back against Preview.
- Added/updated focused regression tests for release identity, health contract, trust events, and deployment ledger idempotency.

### Canonical ownership after repair
- Release identity input: `backend/lib/release_identity.py`
- Frontend artifact identity: `frontend/scripts/stamp-build-version.js` + `frontend/public/release-identity.json`
- Backend runtime identity: `/api/version` in `backend/server.py`
- Parity decision: `/api/version` in `backend/server.py`
- Automatic deployment verification: startup background task in `backend/server.py`
- Canonical deployment ledger: `backend/routes/admin_deployment_ledger.py` -> `deployment_decisions`
- Canonical Trust/C2 deployment outcome: `admin_audit` rows classified by `backend/routes/occ_trust_events.py`

### Latest live Preview proof
- Current backend/runtime commit: see latest `/api/version` evidence for the committed Preview candidate.
- Current served frontend commit: see latest `/release-identity.json` and `/api/version` evidence for the committed Preview candidate.
- Frontend/backend parity: `true`
- Health full: `200 OK` with `mongo=true`, `scheduler=true`, `backup_recent=true`
- Latest automatic deployment ledger decision: `pass / GO`
- Latest automatic deployment trust outcome: `deployment_verification` audit row with `outcome=pass`
- Focused pytest on new/updated governance tests: `12 passed`

### Remaining backlog
- P0: None for this bounded repair track.
- P1: If the platform later introduces a clean immutable deploy-commit injection variable for Preview, point `intended_release_commit` at that canonical value instead of the current governed `PRE_SAVE_CANDIDATE:<HEAD>:<source_hash_prefix>` representation.
- P2: None.

## 2026-07-24 — MASCI OPS 8 Auth/Session Consistency Bounded Repair
- Accepted forensic finding: backend dual-token contract remains canonical; repair scope limited to frontend request/header consistency, 401 handling, and reachable-session messaging.
- Implemented scoped auth propagation across shared clients and verified blast-radius pages so multi-login requests consistently send the correct portal token plus `X-Directory-Token`.
- Repaired session-clearing behavior to avoid wiping valid portal/directory state on localized 401s unless the canonical session is actually invalid/expired.
- Aligned portal reachability messaging (`AccessDenied`, `PortalSwitcher`, permissions helpers) so assigned access is distinguished from currently reachable session state.
- Preview verification passed for Super Admin across Admin, HR, Safety, PM, Dispatch, Shop, and Field Leadership, including refresh/new-tab continuity; public root remained public and protected HR review remained protected.
- Remaining gap: disabled-user and genuine expired-session preview verification remain unproven because no seeded credential/session fixture was provided and identity data mutation was intentionally avoided.

## 2026-07-24 — MASCI OPS 8 Remaining Verification Completion
- Added isolated Preview-only fixtures for the remaining bounded checks: one explicit admin-only identity and one disabled HR identity.
- Disabled-user verification passed: authentication denied, no directory session created, no portal tokens issued, no protected portal access granted, and the browser stayed on explicit sign-in instead of showing a false empty state.
- Genuine expired-session verification passed using a Preview-only harness that expired a real directory session in `directory_sessions`: protected APIs rejected the stale session, stale browser tokens were cleared, the user was redirected to sign-in, and a normal re-login created a fresh valid session.
- Preview identity-preservation diff passed for all pre-existing non-fixture accounts: no deletions, no disablement changes, no portal-array changes, no super-admin flag changes, and no password-hash presence changes.
- Admin-only verification partially passed and exposed an existing policy mismatch relative to the requested acceptance criteria: the current canonical frontend/backend contract still allows admin users into PM and Shop routes by design, while HR, Safety, Dispatch, and Field Leadership stayed blocked.
- Because that PM/Shop admin reach is pre-existing canonical behavior and changing it would exceed the authorized bounded repair scope, this track remains blocked from redeployment approval until that policy expectation is resolved explicitly.

## 2026-07-24 — PM/Shop Authorization Policy Repair (Resolved)
- Canonical policy clarified: Super Admin retains universal access; ordinary Admin is not Super Admin and may reach PM/Shop only through explicit PM/Shop assignment.
- Implemented bounded PM/Shop repair only: PM portal routes now require PM token (or true Super Admin fallback), Shop portal routes now require Shop token (or true Super Admin fallback), and portal-specific PM/Shop login fallbacks no longer let ordinary Admin inherit access.
- Added Preview-only explicit-grant fixtures for verification: `ops8-admin-pm-preview@example.com`, `ops8-admin-shop-preview@example.com`, `ops8-pm-shop-preview@example.com`.
- Full policy matrix passed in Preview: Super Admin full access; Admin-only denied PM/Shop; Admin+PM allowed only Admin+PM; Admin+Shop allowed only Admin+Shop; PM+Shop allowed PM+Shop only; PM-only and Shop-only remained correctly scoped.
- Existing pre-fixture Preview identities remained unchanged after the repair and fixture creation (`existing_accounts_changed_count = 0`, `new_nonfixture_accounts_after_count = 0`).
- Core regressions still passed: `/api/version`, `/api/health/full`, deployment readiness, OCC trust events, public/protected Daily Report boundary, and the previously completed dual-token session repair.

## 2026-07-24 — Independent Re-Verification of PM/Shop Authorization Policy Repair
- Authorized scope remained verification-only. No application code, identities, passwords, or portal assignments were changed in this checkpoint.
- Independent browser verification passed against `https://backup-forensics.preview.emergentagent.com` for Super Admin, Admin-only, Admin+PM, Admin+Shop, PM+Shop, PM-only, HR-only, Safety-only, Shop-only, Dispatch-only, and Field Leadership-only personas.
- Independent backend/API regression verification passed: 57/57 checks, including canonical `POST /api/auth/multi-login`, exact `portal_tokens` issuance, direct protected API requests with `X-Directory-Token` + scoped portal token, disabled-user rejection, anonymous protected-route blocking, and health/version probes.
- Identity preservation re-check passed with zero non-fixture drift (`before_nonfixture_count = 184`, `after_nonfixture_count = 184`, `nonfixture_differences_count = 0`) using `/app/test_reports/ops8_reverify_identity_before.json`, `/app/test_reports/ops8_reverify_identity_after.json`, and `/app/test_reports/ops8_reverify_identity_diff.json`.
- Evidence artifacts created/confirmed: `/app/ops8_auth_policy_verification_report.md`, `/app/ops8_auth_policy_backend_regression_report.md`, `/app/ops8_auth_policy_backend_regression_results.json`, `/app/pm_shop_authorization_policy_backend_results.json`.
- Stable redeploy anchor remains runtime commit `c77ef2847bb16fea901f6e5a2bc6b218878e3221`; PM/Shop repair code in the current branch is represented by commit `e92d880bf9fc8c0555df1ff7fdf0f9862f504834`, with later commit `3afa5f7f73b564b9f17e68eb594fc577fb5c1ebc` adding verification artifacts only.

## 2026-07-24 — Dispatch Portal Runtime Crash + Stale Change-Password Route Fix
- User-reported Transportation sign-in crash reproduced from the Dispatch portal: `Cannot access 'DRAFT_TTL_MS' before initialization` inside `AssignmentCreateDrawer`.
- Fixed frontend-only root causes: removed the premature dependency reference in `frontend/src/components/dispatch/AssignmentCreateDrawer.jsx`, corrected the Dispatch change-password route mapping in `frontend/src/lib/mustChangePassword.js`, and corrected stale Dispatch login paths in `frontend/src/components/SessionStatusOverlay.jsx`.
- Verified with real Dispatch credentials (`cert.dispatch@example.com`) that sign-in no longer throws the runtime overlay, the app now routes to `/dispatch-portal/change-password` instead of stale `/dispatch/change-password`, and the change-password page loads normally.
- Focused verification evidence: `/root/.emergent/automation_output/20260724_022046/console_20260724_022046.log`, screenshot artifact from the same run, plus passing focused frontend/backend regression checks from `auto_frontend_testing_agent` and `deep_testing_backend_v2`.

## 2026-07-24 — Full-Certification Batch 1 (Bounded Repair Only)
- Scope approved by user: repair only D-001 (Incidents authorization contract on canonical review pages) and D-002 (shared auth inference for canonical non-prefixed routes), with no feature work, no auth model weakening, and no backend contract changes unless unavoidable.
- Added shared auth inference helper `frontend/src/lib/portalAuthScope.js` and wired it into `frontend/src/lib/api.js`, `frontend/src/lib/axiosPortalAuth.js`, `frontend/src/lib/fetchPortalAuth.js`, and `frontend/src/lib/xhrPortalAuth.js` so canonical non-prefixed route APIs now inherit the correct portal token plus `X-Directory-Token` using existing shared utilities.
- Repaired canonical incidents review pages by switching `frontend/src/pages/SafetyIncidents.jsx` to the shared `api` client and by correcting `/admin/incidents` to the admin guard in `frontend/src/app/routing/AppRoutes.jsx`. Final prefix fix added `/safety-portal` and `/dispatch-portal` handling in `portalAuthScope` so safety/dispatch portal continuity remains consistent.
- Verified fixed routes: `/admin/incidents`, `/pm/incidents`, `/safety-portal/incidents`, `/project-health`, `/asset-transfers`, `/odr/center`, `/operational-records`, `/operations-actions`, `/admin/operational-intelligence/recipients`.
- Final regression status: frontend PASS `22/22`, backend PASS `20/20`. Evidence: `/root/.emergent/automation_output/20260724_094043/console_20260724_094043.log`, `/root/.emergent/automation_output/20260724_093046/console_20260724_093046.log`, `/root/.emergent/automation_output/20260724_093017/console_20260724_093017.log`, plus Batch 1 verification summaries from `auto_frontend_testing_agent` and `deep_testing_backend_v2`.
- Batch 1 verdict reached: `VERIFIED — READY FOR FULL CERTIFICATION CONTINUATION`.

## 2026-07-24 — MASCI OPS 8 bounded repairs and certification checkpoint
- **Repair B verified**: retired legacy Field Leadership shared-secret auth, removed the canonical UI entry to the legacy gate, enforced canonical FL auth on `/api/field-leadership/*`, denied unassigned users, and restored per-user audit identity on created FL records.
- **Repair A verified**: converted `/api/admin/backups/integrity-check` from a blocking browser request into an async persisted workflow (`start/status/latest`) with duplicate-run guard, audit/trust events, and honest operator-facing state. External `502` timeout is resolved.
- **Combined checkpoint**: code checkpoint `4306bde8`; combined regression checkpoint `439f2adf`. Regression evidence: `/app/test_reports/iteration_31.json`, `/app/test_reports/iteration_32.json`.
- **Current certification verdict**: `VERIFIED WITH DOCUMENTED PRODUCTION-ONLY CHECKS`.

### Remaining documented production-only checks
- Idle and absolute session expiry with timeout-enabled environment
- Safe portal-grant removal / downgrade exercise on dedicated Preview fixtures
- Real-recipient notification delivery outside SAFE_CAPTURE
- Physical-device coverage: iPad Safari, iPhone Safari, Android Chrome, Windows Edge, Mac Safari/Chrome
- Actual restore drill / recoverability evidence separate from manifest integrity

### Evidence artifacts added
- `/app/consolidated_final_ledger.json`
- `/app/consolidated_final_ledger.md`
- `/app/certification_surface_matrix.json`
- `/app/certification_surface_matrix.md`
- `/app/final_coverage_report.json`
- `/app/final_coverage_report.md`
- `/app/final_verdict.md`
