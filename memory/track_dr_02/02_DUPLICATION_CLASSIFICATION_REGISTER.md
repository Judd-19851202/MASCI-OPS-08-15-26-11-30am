# Duplication Classification Register

Date: 2026-07-14
Track: DR-02

Allowed classifications only: **Merge / Replace / Redirect / Deprecate / Remove**

| Duplicate area | Current duplicate state | Evidence | Classification | Canonical decision |
|---|---|---|---|---|
| Field shell | `NewDailyReport.jsx` and `NewDailyReportV3.jsx` both serve live Daily Report routes via `DailyReportRouter` | `frontend/src/pages/DailyReportRouter.jsx:14-29` | **Replace** | One permanent shell behavior contract only |
| Routing | Router fork chooses V1 or V3 for same operator route | `frontend/src/pages/DailyReportRouter.jsx:14-29` | **Remove** | Remove route-level shell competition |
| Draft key family | V1 uses `daily-report-new`; V3 uses `daily-report` | `frontend/src/lib/resiliency/dailyReportScope.js:3`; `frontend/src/pages/NewDailyReportV3.jsx:59-63` | **Merge** | One canonical draft family |
| Draft scope formula | V1 helper uses project+date+report_number; V3 uses project+date | `frontend/src/lib/resiliency/dailyReportScope.js:10-18`; `frontend/src/pages/NewDailyReportV3.jsx:152-154` | **Replace** | One stable identity formula |
| Restore systems | draft restore + archive recovery + crewMemory restore + smart-prefill prompt reuse | `NewDailyReport.jsx:1390-1544`; `NewDailyReportV3.jsx:178-210,710-757` | **Merge** | One layered recovery architecture |
| Smart Prefill UI paths | V1 has repurposed `CrewSetupRestorePrompt` plus dedicated smart-prefill card; V3 has none | `NewDailyReport.jsx:1403-1491` | **Replace** | One explicit Smart Prefill flow |
| Smart Prefill data sources | server `/recent-context` vs local `crewMemory` shown through overlapping UX | `backend/server.py:4078-4237`; `frontend/src/lib/crewMemory.js`; `NewDailyReport.jsx:1403-1506` | **Merge** | Keep both capabilities, but separate boundaries |
| Autosave engines | `useFormDraft` is canonical, but older `useDraft` and `useDraftSync` still exist in repo | `frontend/src/lib/resiliency/useFormDraft.js`; `useDraft.js`; `useDraftSync.js` | **Deprecate** | Daily Report must use one draft engine only |
| AI summary pipelines | `DailySummaryAssist` → `/dr-v2/ai/synthesize` and separate `daily_summary.py` deterministic summary endpoints | `frontend/src/components/daily-report/DailySummaryAssist.jsx:178-183`; `backend/routes/daily_summary.py:295-445` | **Replace** | One Daily Report AI/summary architecture |
| Submission API families | `/api/daily-reports` vs `/api/dr-v2/drafts` | `backend/routes/daily_reports.py:591-882`; `backend/routes/dr_v2.py:1-20` | **Redirect** | One canonical submission API |
| Approved list/PDF routes | `/api/daily-reports/*` aliases + `/api/dr-v2/reports/*` legacy routes | `backend/routes/dr_v2_pdf.py:443-475` | **Redirect** | Canonical aliases stay; legacy paths become internal legacy compatibility only |
| PDF source models | legacy `daily_reports` records and modern `dr_v2_drafts` approvals both render to one PDF route | `backend/routes/dr_v2_pdf.py:296-570` | **Merge** | One canonical PDF contract |
| ODS ingest sources | `daily_report_v1` and `daily_report_v2` source types both emit facts | `backend/services/ods_spine/ingest.py:64-260,322-816` | **Merge** | One Daily Report fact envelope, regardless of legacy origin |
| Notifications | submit-time email dispatch vs lifecycle review fan-out | `backend/routes/daily_reports.py:855-856`; `backend/routes/daily_report_lifecycle.py:131-155` | **Merge** | One event-driven notification architecture by stage |
| Lifecycle | submit path + separate office review lifecycle | `backend/routes/daily_reports.py`; `backend/routes/daily_report_lifecycle.py` | **Merge** | One lifecycle model with multiple stages |
| Search identities | doc-id search + global search + approved list search paths | `backend/doc_ids.py:220-243`; `backend/routes/global_search.py:711-742`; `dr_v2_pdf.py:292-441` | **Merge** | One canonical identity/read model |
| Legacy V2 frontend shell | dormant `DailyReportV2.jsx` still on disk | `frontend/src/app/routing/AppRoutes.jsx:1305-1306`; `frontend/src/pages/daily-report-v2/DailyReportV2.jsx` | **Deprecate** | Not part of permanent field architecture |
| Legacy V2 API surface | `dr_v2.py`, `dr_v2_pdf.py`, `dr_v2_photos.py`, `dr_v2_canonicalize.py` | route inventory + files | **Deprecate** | Explicit compatibility boundary only |

## Duplication verdict

The current system violates the **Simple**, **Trusted**, **Durable**, and **Relentless Ownership** pillars because the same user journey can traverse multiple shells, keys, APIs, and AI paths.
