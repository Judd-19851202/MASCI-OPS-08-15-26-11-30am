# Daily Report Architecture

Date: 2026-07-14
Track: DR-01
Mode: Read-only forensic blueprint

## 1. Entry surfaces

### 1.1 Canonical operator routes
- `/daily/new`
- `/daily/submit`

Both routes mount `DailyReportRouter`, which decides whether the operator sees `NewDailyReport` or `NewDailyReportV3` based on `useDailyReportV3Flag()`.

Evidence:
- `frontend/src/app/routing/AppRoutes.jsx:596-600`
- `frontend/src/pages/DailyReportRouter.jsx:14-29`
- `frontend/src/lib/dailyReportV3Flag.js:14-70`

### 1.2 Legacy V2 route status
The older V2 field shell is no longer mounted as the active field route. `/daily-report/v2` redirects to `/daily/submit`.

Evidence:
- `frontend/src/app/routing/AppRoutes.jsx:1305-1306`

## 2. Active frontend implementations

### 2.1 V1 / current large-shell form
`frontend/src/pages/NewDailyReport.jsx`

Responsibilities observed in repo:
- builds canonical V1 Daily Report payload from `buildDailyReportDefaults()`
- uses `useFormDraft(...)` for autosave / restore
- uses `dailyReportScope.js` for scoped draft identity
- uses `/jobs/{project_number}/recent-context` for Smart Prefill
- uses `crewMemory.js` for device-local setup memory
- submits to `POST /api/daily-reports`
- uses queue/idempotency recovery on submit

Evidence:
- `frontend/src/pages/NewDailyReport.jsx:359-365`
- `frontend/src/pages/NewDailyReport.jsx:414-422`
- `frontend/src/pages/NewDailyReport.jsx:532-565`
- `frontend/src/pages/NewDailyReport.jsx:623-729`
- `frontend/src/pages/NewDailyReport.jsx:800-880`
- `frontend/src/pages/NewDailyReport.jsx:1120-1274`

### 2.2 V3 / flag-gated alternate shell
`frontend/src/pages/NewDailyReportV3.jsx`

Responsibilities observed in repo:
- builds a Daily Report payload from the same schema defaults
- uses `useFormDraft(...)`, but with its own base key and its own inline scope logic
- uses `crewMemory.js` for local “yesterday setup” recovery
- submits to the same `POST /api/daily-reports`
- does **not** contain the V1 Smart Prefill `/recent-context` flow

Evidence:
- `frontend/src/pages/NewDailyReportV3.jsx:127-160`
- `frontend/src/pages/NewDailyReportV3.jsx:178-210`
- `frontend/src/pages/NewDailyReportV3.jsx:563-619`

## 3. Shared client continuity subsystem

### 3.1 Draft autosave / restore
`frontend/src/lib/resiliency/useFormDraft.js`

Observed contract:
- scoped form key
- IndexedDB-backed draft writes via `draftStore.js`
- restore offer rather than silent overwrite
- debounced save + 10s forced flush + lifecycle-triggered flush
- telemetry emission to `/api/draft-telemetry`

Evidence:
- `frontend/src/lib/resiliency/useFormDraft.js:66-75`
- `frontend/src/lib/resiliency/useFormDraft.js:99-172`
- `frontend/src/lib/resiliency/useFormDraft.js:174-276`

### 3.2 IndexedDB draft persistence
`frontend/src/lib/resiliency/draftStore.js`

Observed contract:
- primary key: `masci.draft.<actorId>.<formKey>`
- archive key: `masci.draft-archive.<actorId>.<formKey>.<deletedAt>`
- idempotency key: `masci.draft-idempotency.<actorId>.<formKey>`
- `savedByActor` stamped on draft writes

Evidence:
- `frontend/src/lib/resiliency/draftStore.js:24-27`
- `frontend/src/lib/resiliency/draftStore.js:58-76`
- `frontend/src/lib/resiliency/draftStore.js:102-119`

### 3.3 Draft telemetry
`frontend/src/lib/resiliency/draftTelemetry.js` → `backend/routes/draft_telemetry.py`

Observed contract:
- client batches `draft.*` and `quota.warning`
- server persists append-only events in `draft_telemetry`
- admin health feed aggregates from that collection

Evidence:
- `frontend/src/lib/resiliency/draftTelemetry.js:91-166`
- `backend/routes/draft_telemetry.py:21-39`
- `backend/routes/daily_reports.py:1026-1106`

### 3.4 Device-local setup memory
`frontend/src/lib/crewMemory.js`

Observed contract:
- localStorage only
- explicit restore prompt only
- saves setup fields, not per-day operational detail
- actor-scoped key on shared devices

Evidence:
- `frontend/src/lib/crewMemory.js:7-22`
- `frontend/src/lib/crewMemory.js:32-43`
- `frontend/src/lib/crewMemory.js:179-243`

## 4. Backend daily-report core

### 4.1 Canonical submit endpoint
`POST /api/daily-reports`

Observed behavior:
- validates approved summary presence
- normalizes production/material/outbound/equipment payloads
- persists canonical record into `db.daily_reports`
- emits downstream side effects (ODS ingest, photo intelligence, trust spine, email scheduling)

Evidence:
- `backend/routes/daily_reports.py:591-882`

### 4.2 Recent-context Smart Prefill contract
`GET /api/jobs/{project_number}/recent-context`

Observed behavior:
- returns prior crew/equipment baseline for a project
- biases to actor-specific prior report when `foreman` or `superintendent` query params are supplied
- returns time-pattern fields (`start_time`, `stop_time`, `lunch_minutes`)
- excludes known inactive employees from prefill offer

Evidence:
- `backend/server.py:4078-4237`

### 4.3 Daily Report lifecycle layer
`backend/routes/daily_report_lifecycle.py`

Observed behavior:
- additive review-state transitions over canonical `daily_reports`
- separate from field entry but part of the broader Daily Report system

Evidence:
- `backend/routes/daily_report_lifecycle.py:62-254`

## 5. Legacy V2 subsystem still present in backend

Although V2 is not the active field route, a parallel V2 subsystem still exists:
- `/api/dr-v2/meta`
- `/api/dr-v2/drafts`
- `/api/dr-v2/ai/synthesize`
- `/api/dr-v2/ai/approve`
- `/api/dr-v2/ai/audit/{report_id}`
- `/api/dr-v2/reports/{report_id}/pdf`

It writes to `dr_v2_*` collections and is wrapped by `daily_report_*` compatibility helpers.

Evidence:
- `backend/routes/dr_v2.py:243-539`
- `backend/routes/dr_v2_pdf.py` (route inventory via grep)
- `backend/lib/daily_report_collections.py:1-93`

## 6. Architectural conclusion

The Daily Report system is not one implementation. It is a routed composite of:
1. V1 canonical submit shell
2. V3 flag-gated alternate submit shell
3. a retained V2 AI/approval/PDF subsystem and collection family
4. shared continuity primitives that are no longer consumed consistently across shells

That multi-version topology is the root architectural condition enabling today’s drift.
