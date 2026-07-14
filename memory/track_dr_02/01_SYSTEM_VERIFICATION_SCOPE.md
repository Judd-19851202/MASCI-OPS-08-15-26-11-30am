# System Verification Scope

Date: 2026-07-14
Track: DR-02
Mode: Read-only architecture lock

## Verified Daily Report surfaces in repository

### Active field entry
- `frontend/src/pages/DailyReportRouter.jsx`
- `frontend/src/pages/NewDailyReport.jsx`
- `frontend/src/pages/NewDailyReportV3.jsx`
- `frontend/src/components/daily-report-v3/sections.jsx`

### Draft / restore / queue / device continuity
- `frontend/src/lib/resiliency/useFormDraft.js`
- `frontend/src/lib/resiliency/draftStore.js`
- `frontend/src/lib/resiliency/draftTelemetry.js`
- `frontend/src/lib/resiliency/resiliencyQueue.js`
- `frontend/src/lib/resiliency/dailyReportScope.js`
- `frontend/src/lib/crewMemory.js`
- `frontend/src/lib/resiliency/photoDraftStore.js`
- `frontend/src/lib/resiliency/DraftRestorePrompt.jsx`

### Canonical Daily Report submit/read stack
- `backend/routes/daily_reports.py`
- `backend/routes/daily_report_lifecycle.py`
- `backend/routes/daily_summary.py`
- `backend/server.py` (attachment upload, recent-context, route mounts)

### Legacy / parallel Daily Report stack
- `backend/routes/dr_v2.py`
- `backend/routes/dr_v2_pdf.py`
- `backend/routes/dr_v2_canonicalize.py`
- `backend/routes/dr_v2_photos.py`
- `backend/lib/daily_report_collections.py`
- `frontend/src/pages/daily-report-v2/DailyReportV2.jsx`

### Downstream integrations verified
- Trust Spine: `backend/lib/trust_spine.py`
- Email / notifications dispatch: `backend/lib/email_dispatch.py`, `backend/routes/daily_report_lifecycle.py`
- ODS ingest: `backend/services/ods_spine/ingest.py`
- ODS intelligence / PM brief / executive brief: `backend/routes/ods_intelligence.py`
- Search: `backend/routes/global_search.py`, `backend/doc_ids.py`
- Admin roll-up / Daily Report health: `backend/lib/daily_report_rollup.py`, `backend/routes/dr_admin_intel.py`
- PDF/export: `backend/pdf_render.py`, `backend/routes/dr_v2_pdf.py`, `backend/routes/daily_reports.py`
- HR / PM / Safety / Field Leadership read surfaces:
  - `backend/routes/hr_portal.py`
  - `backend/routes/pm_command_center.py`
  - `backend/routes/safety_portal/daily_reports.py`
  - `backend/routes/field_leadership_portal.py`

### Suggestion / assistive integrations verified
- Equipment suggestion API: `backend/routes/equipment_detection.py`
- Daily summary UI: `frontend/src/components/daily-report/DailySummaryAssist.jsx`

## Items requested by DR-02 that are not fully proven in repo

The following are only partially provable or not provable from repository code alone and must be marked **UNKNOWN** if a runtime/business decision is needed:
- exact production feature-flag distribution between routed shells
- actual field-device browser mix and dominant failure modes
- whether “Weekly Reconciliation integration” has one dedicated Daily Report-owned module; only indirect HR/payroll and evidence reconciliation links are verifiable
- whether an “Executive Brief” refers strictly to ODS brief endpoints, broader operational intelligence products, or both in business language

## Pillar check baseline

Every architecture decision in DR-02 is judged against:
- Powerful
- Simple
- Beautiful
- Trusted
- Proven
- Deployable
- Durable
- Relentless Ownership

## Scope conclusion

The repository is rich enough to lock the canonical architecture, but some runtime roll-out facts remain UNKNOWN. Those unknowns do not prevent the platform architecture from being specified if the final lock explicitly chooses one permanent system and classifies all retained legacy pieces.
