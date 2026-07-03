# TRACK 19.36 · ZERO-DRIFT MATRIX

**Date:** 2026-07-03 · **Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md`

Proves Track 19.36 preserved every certified contract, permission, and workflow byte-for-byte.

---

## Zero-Drift Matrix

| Category | Status | Notes |
|---|---|---|
| Schemas (`incident_cases`, `incident_case_events`, `incident_case_evidence`, `corrective_actions`, `case_witnesses`, `case_medical`, `case_agency_contacts`, `case_communications`, `case_tasks`) | ✅ unchanged | No collection touched · no new indexes |
| Backend routes (existing) | ✅ unchanged | All Phase A / C / D / E routes preserved |
| Existing PDF endpoint (`/api/incident-cases/{id}/reports/{type}.pdf`) | ✅ unchanged | Phase E · byte-for-byte preserved |
| Existing dashboard endpoints (`/api/incident-intelligence/*`) | ✅ unchanged | Phase D preserved |
| Existing dashboard page (`/safety/executive-intelligence`) | ✅ unchanged | `ExecutiveIntelligence.jsx` not modified |
| Payloads | ✅ unchanged | Assembler is read-only |
| PDFs (existing) | ✅ unchanged | Not touched |
| Emails | ✅ unchanged | Not touched · no new dispatches |
| Notifications | ✅ unchanged | Not touched |
| Permissions | ✅ unchanged | New endpoints use existing Safety/Admin/PM read gate |
| Trust Spine (`incident_case.employee_ids` · `equipment_ids` · `project_id`) | ✅ unchanged | Read-only surface |
| Audit events (`incident_case_events`) | ✅ unchanged | Append-only invariant preserved · no new event types |
| HR Source-of-Truth | ✅ unchanged | Employee linkage untouched |
| Autosave / drafts | ✅ preserved | N/A · report is read-only |
| Historical records | ✅ preserved | Legacy case documents render identically |
| Bilingual engine (`useT()`) | ✅ preserved | New page uses same engine |
| Track 19.34 Field-vs-Safety grep invariant | ✅ preserved | No new field-facing surface introduced |
| Track 19.35 Field Facts immutability | ✅ preserved | Workspace panel unchanged; new link is header-level |
| CAPA state machine | ✅ unchanged | Read-only surface |
| Rollback paths | ✅ preserved | Additive-only · full runtime rollback documented |

## File-level change footprint

| Change | File | Type | Lines |
|---|---|---|---|
| Executive Intelligence assembler | `backend/incident_engine/executive_intelligence.py` | NEW | ~470 |
| Boardroom HTML renderer | `backend/incident_engine/executive_report_render.py` | NEW | ~280 |
| Additive route registration | `backend/incident_engine/executive_report_routes.py` | NEW | ~60 |
| Wire assembler + routes | `backend/server.py` | EDIT | +14 |
| Executive Case Report page | `frontend/src/pages/ExecutiveCaseReport.jsx` | NEW | ~300 |
| Route + import for report page | `frontend/src/App.js` | EDIT | +3 |
| Header link to report | `frontend/src/pages/SafetyCaseWorkspace.jsx` | EDIT | +8 |
| Icon import for link | `frontend/src/pages/SafetyCaseWorkspace.jsx` | EDIT | (existing `FileText` reused) |

**Total: 4 new files · 3 files edited (all additive edits) · 0 files deleted.**

## Backend footprint

**No collection is read-modify-written.** The assembler and both routes are pure reads over pre-existing certified collections. Verifiable via `git diff --stat backend/`.

## Payload-level drift check

- All existing request/response bodies: unchanged.
- New endpoints emit shapes that are **additive** to the API surface — no field renamed, no field removed anywhere.

## Permission drift check

- New endpoints use the same Safety/Admin/PM read gate as the entire `/api/incident-cases/*` surface (`make_require_safety_admin_or_pm`).
- Public routes unchanged (`/incidents/report`, `/near-miss`).
- Frontend page mounted under `/safety/*` — inherits the existing Safety-gated route boundary.

## Legacy route drift check

- `/incidents/new` → `/incidents/report` redirect: unchanged.
- `/incidents/submit` → `/incidents/report` redirect: unchanged.
- `/safety/cases/:caseId` → `SafetyCaseWorkspace`: unchanged.
- `/safety/executive-intelligence` → `ExecutiveIntelligence`: unchanged.
- `/safety/cases/:caseId/reports/:reportType` → `IncidentReportViewer`: unchanged.
- **NEW** `/safety/cases/:caseId/executive-report` → `ExecutiveCaseReport`: additive only.

## PDF drift check

- Phase E `render_pdf_route` (existing) still handles `/api/incident-cases/{id}/reports/{type}.pdf` byte-for-byte.
- New endpoint `/api/incident-cases/{id}/executive-report.pdf` **coexists** at a distinct path and uses a distinct renderer.
- Both use the same underlying `html_to_pdf_bytes` WeasyPrint helper; no shared state.

## Email / notification drift check

- No `fsi_send_email` calls added.
- No `email_routing_audit_v2` entries added.
- No notification/digest hook added.

## Audit event drift check

- `incident_case_events` append-only invariant preserved.
- No new event types emitted by the assembler (the assembler never writes).

## Rollback drift check

- Runtime rollback: comment out the `_register_ie_executive_report_routes` wiring block in `server.py` and the App.js route entry. Both changes are additive-only lines.
- File-level rollback: delete 3 backend files + 1 frontend file. No collection cleanup needed. Rollback confidence: HIGH.

## Verdict

🟢 **Zero drift.** Track 19.36 is strictly additive. Every certified contract, permission, and workflow is preserved.
