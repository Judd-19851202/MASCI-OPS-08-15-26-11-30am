# Legacy Component Inventory

Date: 2026-07-14
Track: DR-01

## 1. Active field-entry surfaces

### A. V1 active shell
- `frontend/src/pages/NewDailyReport.jsx`
- role: canonical large-shell field form
- current status: ACTIVE

### B. V3 alternate shell
- `frontend/src/pages/NewDailyReportV3.jsx`
- role: flag-gated alternate field form on same routes
- current status: ACTIVE VIA FLAG

### C. Route selector
- `frontend/src/pages/DailyReportRouter.jsx`
- role: runtime fork selector between V1 and V3
- current status: ACTIVE

## 2. Retained V2 frontend artifacts

### D. Retired V2 shell still on disk
- `frontend/src/pages/daily-report-v2/DailyReportV2.jsx`
- current status: NOT ROUTED AS PRIMARY FIELD ENTRY

### E. V2 hook stack
- `frontend/src/pages/daily-report-v2/hooks/useDrV2.js`
- current status: LEGACY / PARALLEL SUBSYSTEM

### F. V2 sections/panels
- `frontend/src/pages/daily-report-v2/sections/*`
- `frontend/src/pages/daily-report-v2/panels/PhotoIntelligencePanel.jsx`
- current status: LEGACY UI ARTIFACTS

## 3. Shared continuity primitives

### G. Draft store
- `frontend/src/lib/resiliency/draftStore.js`
- status: ACTIVE SHARED PRIMITIVE

### H. Draft hook
- `frontend/src/lib/resiliency/useFormDraft.js`
- status: ACTIVE SHARED PRIMITIVE

### I. Draft telemetry
- `frontend/src/lib/resiliency/draftTelemetry.js`
- status: ACTIVE SHARED PRIMITIVE

### J. Photo draft store
- `frontend/src/lib/resiliency/photoDraftStore.js`
- status: ACTIVE SHARED PRIMITIVE

### K. Crew memory
- `frontend/src/lib/crewMemory.js`
- status: ACTIVE SHARED PRIMITIVE

## 4. Backend canonical Daily Report stack

### L. Canonical CRUD / submit
- `backend/routes/daily_reports.py`
- collection: `daily_reports`
- status: ACTIVE CANONICAL SUBMIT PATH

### M. Review lifecycle
- `backend/routes/daily_report_lifecycle.py`
- status: ACTIVE ADDITIVE WORKFLOW LAYER

### N. Smart Prefill backend contract
- `backend/server.py` → `/jobs/{project_number}/recent-context`
- status: ACTIVE

## 5. Backend legacy / parallel V2 stack

### O. V2 core routes
- `backend/routes/dr_v2.py`
- status: ACTIVE LEGACY/PARALLEL API SURFACE

### P. V2 PDF routes
- `backend/routes/dr_v2_pdf.py`
- status: ACTIVE LEGACY/PARALLEL API SURFACE

### Q. V2 canonicalize routes
- `backend/routes/dr_v2_canonicalize.py`
- status: ACTIVE LEGACY/PARALLEL API SURFACE

### R. V2 photo routes
- `backend/routes/dr_v2_photos.py`
- status: ACTIVE LEGACY/PARALLEL API SURFACE

### S. Collection compatibility layer
- `backend/lib/daily_report_collections.py`
- canonical: `daily_report_*`
- legacy: `dr_v2_*`
- status: ACTIVE COMPATIBILITY LAYER

## 6. Inventory conclusion

The Daily Report system still carries legacy runtime obligations in both frontend and backend. The most important cleanup principle is **not deleting blindly**, but first deciding which pieces remain supported capability surfaces versus migration baggage.
