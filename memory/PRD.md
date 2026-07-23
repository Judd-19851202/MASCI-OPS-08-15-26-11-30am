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