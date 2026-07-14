# Canonical Daily Report Recovery Architecture

Date: 2026-07-14
Track: DR-01

## Recovery target

Recover the Daily Report system to **one canonical operator flow** with:
- one routed field shell behavior contract
- one stable draft identity contract
- one Smart Prefill contract
- one canonical submit persistence path
- one explicitly isolated legacy V2 compatibility boundary

## 1. Canonical operator route contract

### Target
`/daily/new` and `/daily/submit` must behave as one product, not two partial implementations.

### Evidence basis
Today those routes are split by `DailyReportRouter` into V1 or V3.

Evidence:
- `frontend/src/pages/DailyReportRouter.jsx:14-29`

### Recovery rule
During recovery, there must be exactly one shell-level behavioral contract for:
- draft identity
- Smart Prefill
- queue/idempotency
- restore affordances
- operator review notices

## 2. Canonical draft identity contract

### Target
One draft key family shared by every active field shell and every continuity subsystem.

### Repository-backed target shape
Project + report date are the intended stable identity anchors.

Why this target is evidence-backed:
- `useFormDraft` comment explicitly describes scoping by `(project, report_date)`
- PRD records a recent repair as “project + report date” scoping
- V3 already scopes only by project + date

Evidence:
- `frontend/src/lib/resiliency/useFormDraft.js:67-72`
- `memory/PRD.md:9`
- `frontend/src/pages/NewDailyReportV3.jsx:146-154`

### Recovery rule
The draft identity contract should not depend on `report_number` because `report_number` is preview/generated after mount and is not the stable human work context.

## 3. Canonical Smart Prefill contract

### Target
Server-backed Smart Prefill should have exactly one source and one explicit apply path:
- source: `/jobs/{project_number}/recent-context`
- consumer: one explicit offer UI
- apply semantics: one mapping path only

### Evidence basis
The backend already provides a complete 19.06.1 contract including actor scope and time pattern fields.

Evidence:
- `backend/server.py:4078-4237`

### Recovery rule
`crewMemory.js` must remain a separate local-device continuity feature, not a substitute for Smart Prefill and not a UI alias for backend recent-context.

## 4. Canonical submission contract

### Target
Field entry continues to submit only through `POST /api/daily-reports`.

### Evidence basis
Both V1 and V3 already use that endpoint.

Evidence:
- `frontend/src/pages/NewDailyReport.jsx:1157-1164`
- `frontend/src/pages/NewDailyReportV3.jsx:566-568`
- `backend/routes/daily_reports.py:591-882`

## 5. Legacy V2 isolation boundary

### Target
The `dr_v2_*` subsystem should be treated as a legacy compatibility lane, not as a second field-entry architecture.

### Evidence basis
The route is retired for end users, but the backend V2 services remain active.

Evidence:
- `frontend/src/app/routing/AppRoutes.jsx:1305-1306`
- `backend/routes/dr_v2.py:243-539`
- `backend/lib/daily_report_collections.py:1-93`

### Recovery rule
V2 AI/PDF/approval services may remain temporarily, but they should not define field-entry state rules for active `/daily/new` traffic.

## 6. Recovery architecture summary

### Canonical stack
1. One routed shell behavior contract
2. One draft key family
3. One recent-context Smart Prefill path
4. One local setup-memory path (`crewMemory`) with explicit restore only
5. One submit endpoint (`/api/daily-reports`)
6. One legacy compatibility boundary for `dr_v2_*`

This architecture does **not** invent a new system. It reasserts the contract that the repo already partially describes but does not currently honor consistently.
