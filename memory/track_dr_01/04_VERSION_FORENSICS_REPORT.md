# Version Forensics Report

Date: 2026-07-14
Track: DR-01

## Executive finding

The repository contains **three materially different Daily Report versions**:
- **V1** = active large-shell canonical submit experience
- **V3** = flag-gated alternate field shell on the same routes
- **V2** = retained legacy AI/approval/PDF subsystem and dormant field shell

These are not cosmetic variants. They differ in draft identity, Smart Prefill behavior, recovery affordances, and persistence topology.

## 1. V1 forensic profile

Primary file:
- `frontend/src/pages/NewDailyReport.jsx`

What V1 owns today:
- `useFormDraft()` wiring with scoped draft key
- explicit draft restore prompt
- archived-draft recovery
- prior-usage banner
- quota-pressure chip
- Smart Prefill via `/jobs/{project_number}/recent-context`
- device-local `crewMemory.js`
- offline queue + scoped idempotency
- canonical submit to `POST /api/daily-reports`

Evidence:
- `frontend/src/pages/NewDailyReport.jsx:414-486`
- `frontend/src/pages/NewDailyReport.jsx:532-565`
- `frontend/src/pages/NewDailyReport.jsx:1120-1274`

Assessment:
- V1 is the most behaviorally complete field implementation.
- V1 also contains internal drift of its own, especially around Smart Prefill duplication and moving scope identity.

## 2. V3 forensic profile

Primary file:
- `frontend/src/pages/NewDailyReportV3.jsx`

What V3 owns today:
- alternate field UX shell
- `useFormDraft()` integration, but with a different base key and different scope logic
- local “restore yesterday setup” via `crewMemory.js`
- canonical submit to `POST /api/daily-reports`

What V3 does **not** own:
- no `/recent-context` Smart Prefill consumption
- no legacy draft recovery affordance
- no archived-draft recovery affordance
- no prior-usage banner
- no quota-pressure surface
- no parity with V1 queue repair keying

Evidence:
- `frontend/src/pages/NewDailyReportV3.jsx:59-63`
- `frontend/src/pages/NewDailyReportV3.jsx:145-160`
- `frontend/src/pages/NewDailyReportV3.jsx:178-210`
- absence of any `/recent-context` call in `NewDailyReportV3.jsx`

Assessment:
- V3 is not a parity implementation of V1.
- It is a forked shell that reuses submit infrastructure but not the full continuity/prefill contract.

## 3. V2 forensic profile

Primary files:
- `frontend/src/pages/daily-report-v2/DailyReportV2.jsx`
- `frontend/src/pages/daily-report-v2/hooks/useDrV2.js`
- `backend/routes/dr_v2.py`
- `backend/routes/dr_v2_pdf.py`
- `backend/routes/dr_v2_canonicalize.py`
- `backend/routes/dr_v2_photos.py`

Observed behavior:
- V2 has its own draft save endpoint family: `/api/dr-v2/drafts`
- its own AI synthesis / approval pipeline
- its own collection family: `dr_v2_*`
- its own PDF / canonicalization / photo-intelligence flows
- its frontend shell remains on disk but is no longer mounted as the canonical route

Evidence:
- `frontend/src/pages/daily-report-v2/DailyReportV2.jsx:32-145`
- `frontend/src/pages/daily-report-v2/hooks/useDrV2.js:34-154`
- `backend/routes/dr_v2.py:243-539`
- `frontend/src/app/routing/AppRoutes.jsx:1305-1306`

Assessment:
- V2 is functionally alive in backend/runtime even though it is retired as the main field route.
- This is a major source of architectural drift because the platform still carries two Daily Report persistence families: `daily_reports` and `dr_v2_*`/`daily_report_*` compatibility collections.

## 4. Drift table

| Concern | V1 | V3 | V2 |
|---|---|---|---|
| Active routed shell | Yes | Yes, via flag | No |
| Canonical submit endpoint | `/api/daily-reports` | `/api/daily-reports` | `/api/dr-v2/drafts` + AI/PDF stack |
| Smart Prefill `/recent-context` | Yes | No | No evidence of current use |
| `crewMemory.js` | Yes | Yes | No evidence in routed shell |
| Draft base key | `daily-report-new` | `daily-report` | separate V2 autosave path |
| Draft scope logic | helper: project+date+report_number | inline: project+date | own draft store endpoint |
| Queue repair compatibility | Yes | No | N/A |
| Archived draft recovery | Yes | No | N/A |
| Legacy collections | No | No | Yes |

## 5. Forensic conclusion

The Daily Report system is currently a **multi-version live composite**, not a unified product. The most critical breakages are not caused by one missing line; they are caused by version divergence across the same operator journey.
