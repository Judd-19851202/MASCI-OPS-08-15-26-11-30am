# HR DAILY REPORT VISIBILITY AUDIT

**Track:** 15.9
**Date:** 2026-06-17
**Status:** ✅ COMPLETE
**Source of truth:** `db.daily_reports` (single canonical collection — no shadow HR-DR collection exists)

---

## Methodology

This document classifies every field that may appear in a Daily Report document against three confidentiality bands:

- **HR SAFE** — field is rendered or operationally appropriate for HR review. Visible to HR via `/api/hr/daily-reports/{id}`.
- **HR REVIEW REQUIRED** — field may contain context-sensitive content (free-text PM observations, signature image data). HR has legitimate need but PM/Counsel should be aware HR sees this surface.
- **HR EXCLUDE** — field has no HR rendering use case AND is not in HR's interest (e.g., PM's outbound email CC list). Stripped at the database projection boundary on the HR detail endpoint.

Field inventory was assembled from:
- `/app/backend/routes/daily_reports.py` (`DailyReportCreate`, `DailyReport` Pydantic models)
- `/app/frontend/src/pages/NewDailyReport.jsx` (full PM-side form)
- `/app/backend/routes/hr_portal.py` lines 340-412 (HR endpoints + projection)
- `/app/frontend/src/pages/HrDailyReports.jsx` (HR-side renderer)

---

## Field-by-field classification

### Header / Identity

| Field | Source | Classification | Rationale |
|---|---|---|---|
| `id` | server-generated UUID | HR SAFE | Required for navigation. |
| `doc_id` | server (DR-YYYY-NNNNN) | HR SAFE | Human report number. Rendered. |
| `report_number` | server | HR SAFE | Synonym used by some pipelines. Rendered. |
| `report_date` | user | HR SAFE | Required for date filtering. Rendered. |
| `created_at` | server | HR SAFE | Sort key. |
| `project_name` | user | HR SAFE | Required for project filter. Rendered. |
| `project_number` | user | HR SAFE | Rendered. |
| `location` | user | HR SAFE | Rendered (work site address). |
| `prepared_by` | user | HR SAFE | Author identity. Rendered. |
| `superintendent` | user | HR SAFE | Foreman / superintendent name. Used for workforce-intel cross-link. |
| `gps_lat`, `gps_lng`, `gps_accuracy` | mobile auto-capture | HR SAFE | Operational location metadata, no PII. |

### Crew / Subcontractor / Visitor

| Field | Source | Classification | Rationale |
|---|---|---|---|
| `masci_crews[]` | user | HR SAFE | Core payroll cross-check use case. Names, hours, foreman. |
| `masci_crews[].foreman` | user | HR SAFE | |
| `masci_crews[].members[].name` | user | HR SAFE | Employee name search hits here. |
| `masci_crews[].members[].hours` | user | HR SAFE | Hours worked. |
| `subcontractors[]` | user | HR SAFE | Sub company name, crew size, work performed. |
| `subcontractors[].name` | user | HR SAFE | Sub filter hits here. |
| `visitors[]` | user | HR SAFE | Vendor / visitor entries. |
| `visitors[].name`, `.company`, `.purpose` | user | HR SAFE | Rendered. |

### Production / Materials / Equipment

| Field | Source | Classification | Rationale |
|---|---|---|---|
| `production[]` | user | HR SAFE | Structured production rows (units, locations). No dollar amounts. |
| `materials[]` | user | HR SAFE | Inbound material entries (qty, unit, source). |
| `outbound_materials[]` | user | HR SAFE | Outbound material entries. |
| `equipment[]` | user | HR SAFE | On-site equipment list. |
| `activities[]` | user | HR SAFE | Activity descriptors. |
| `constraints[]` | user | HR SAFE | Constraint rows (with advisory RFI/schedule flags). |

### Weather / Safety / Notes

| Field | Source | Classification | Rationale |
|---|---|---|---|
| `weather_summary` | user / API | HR SAFE | Rendered. |
| `weather_snapshots[]` | API auto-fetch | HR SAFE | Per-time-period weather. |
| `weather_impact` | user | HR SAFE | Free-text. |
| `safety_incidents_today` | user (Yes/No) | HR SAFE | Yes/No flag. |
| `injuries_reported` | user (Yes/No) | HR SAFE | Yes/No flag. |
| `incident_notes` | user free-text | **HR REVIEW REQUIRED** | Free-text. PM may include employee names + injury context. HR has legitimate need (payroll / disability follow-up) but content is sensitive. Counsel should be aware HR sees this. |
| `safety_notified` | user | HR SAFE | Yes/No + name. |
| `safety_contact_person`, `safety_contact_time` | user | HR SAFE | |
| `incident_report_filled`, `incident_report_time` | user | HR SAFE | Operational metadata. |
| `delay_description` | user free-text | HR SAFE | Operational. |
| `schedule_delays` | user | HR SAFE | Operational. |
| `general_notes` | user free-text | **HR REVIEW REQUIRED** | PM scratch space. May include recognition, coaching observations, or operational notes that touch HR-relevant matters. HR's reading is legitimate; PMs should know HR reads this. |
| `attachment_note` | user | HR SAFE | Annotation on uploaded files. |
| `narrative` | user free-text | **HR REVIEW REQUIRED** | Long-form description of the workday. Same reasoning as general_notes. |
| `excavation_activity_today` | user | HR SAFE | Operational/safety. |
| `linked_excavation_ids[]` | server | HR SAFE | Cross-references to excavation records. |

### Photos / Attachments

| Field | Source | Classification | Rationale |
|---|---|---|---|
| `photos[]` | user upload | **HR REVIEW REQUIRED** | Job-site photos may incidentally capture employees in identifiable contexts. HR has legitimate need (claim corroboration, attendance dispute). PM/Counsel awareness. |
| `photo_min` | user (target count) | HR SAFE | Operational metadata. |

### Signatures / Identity Bind

| Field | Source | Classification | Rationale |
|---|---|---|---|
| `prepared_by_signature` | user (base64 PNG) | HR SAFE | Signed attestation of accuracy — appropriate for HR review. |
| `superintendent_signature` | user (base64 PNG) | HR SAFE | Same. |
| `prepared_by_identity` | server (from token) | HR SAFE | Structured identity dict — internal context. |
| `prepared_by_bound` | server | HR SAFE | Boolean flag. |

### Audit Envelope

| Field | Source | Classification | Rationale |
|---|---|---|---|
| `audit_envelope_sha256` | server (computed at insert) | HR SAFE | Tamper-evidence hash. Operational. |

### Distribution / Outbound Comms

| Field | Source | Classification | Rationale |
|---|---|---|---|
| `distribution_list` | user (email CC list, ≤20 entries) | **HR EXCLUDE** | The PM's outbound-comms tool — who they CC when the DR is emailed. Has zero HR rendering use case. May contain customer / external counsel emails. Stripped at the database projection boundary in `/api/hr/daily-reports/{id}` (Track 15.9 hardening). |

---

## Confidentiality summary

| Band | Field count | Examples |
|---|---|---|
| HR SAFE | ~45 | report_date, project_name, masci_crews[], subcontractors[], weather_summary, signatures, audit_envelope_sha256, etc. |
| HR REVIEW REQUIRED | 4 | `incident_notes`, `general_notes`, `narrative`, `photos[]` |
| HR EXCLUDE | 1 | `distribution_list` (stripped server-side) |

---

## Enforcement points

1. **HR list endpoint** (`GET /api/hr/daily-reports`) — explicit projection limits the wire payload to ~12 summary fields (no narrative, no notes, no photos, no signatures, no distribution_list). Source: `hr_portal.py` lines 391-399.
2. **HR detail endpoint** (`GET /api/hr/daily-reports/{id}`) — projects out `distribution_list` at the database boundary. Source: `hr_portal.py` lines 405-414 (Track 15.9 hardening).
3. **HR token gate** — both endpoints depend on `require_hr_user` which only inspects `X-HR-Token`. PM/Admin/Safety/Dispatch/FL tokens cannot enter. Source: `hr_portal_deps.py` lines 42-66.
4. **No HR write verbs** — `routes/hr_portal.py` contains zero `POST/PUT/PATCH/DELETE` decorators under `/hr/daily-reports`. Asserted by `test_no_hr_write_endpoints_on_daily_reports`.
5. **No PM workflow surface** — no `/route`, `/approve`, `/reopen`, `/pdf`, `/email` sub-paths under `/hr/daily-reports`. Asserted by `test_no_pm_workflow_endpoints_under_hr_namespace`.
6. **No HR UI affordances** — the HR page does not render Edit / Approve / Reject / Reopen / Submit / Email / Generate PDF / Export buttons. Asserted by `test_no_pdf_or_export_affordance_in_hr_dr_ui`.

---

## Operator review items (REVIEW band — informational, not a blocker)

PMs should be aware that HR can read the following free-text fields. This is not a defect — HR's review of payroll and personnel matters is legitimate — but PM training should mention:

- `narrative` — keep workday descriptions operational.
- `general_notes` — avoid writing disciplinary content into the DR notes box; use the Field Leadership coaching/writeup pipeline instead, which has its own access controls.
- `incident_notes` — same as above for injury or safety-incident content.
- `photos[]` — be intentional about employee-identifying photos.

If a PM has authored sensitive personnel content inside a historical DR notes field, the workflow change is to migrate it to the Field Leadership coaching record system (already gated more tightly) and clear the DR field. Not a Track 15.9 deliverable — flagged here for product / counsel decision.

---

**End of audit.**
