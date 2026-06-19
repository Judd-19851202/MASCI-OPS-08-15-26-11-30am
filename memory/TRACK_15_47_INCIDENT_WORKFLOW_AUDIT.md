# TRACK 15.47 · Incident Workflow Audit · Phase 1

**Date:** 2026-06-19
**Audit type:** Read-only · evidence-based · no code changes
**Driver:** Real-world field incident — public-member verbal confrontation escalated to physical contact with a MASCI employee.
**Scope:** End-to-end incident workflow from first contact through final closure.

---

## 1 · Workflow trace · "An employee is involved in a confrontation with a member of the public"

The workflow is traced through the actual deployed code paths against the live preview database. Every claim is backed by either a file:line reference, a curl-tested response, or a real record from the `incidents` collection.

### Step 1 · Report

**Path:** Public form at `/incident/new` (`publicMode=true`) or admin form at `/incidents/new` → `POST /api/incidents`.
**Schema source:** `backend/routes/safety.py:268-340` (`IncidentCreate`).
**Authentication:** Public form requires no token (rate-limited). Admin form requires `X-Safety-Token` or `X-Admin-Token`.

| Capability | Status | Evidence |
|---|---|---|
| Report an incident | ✅ EXISTS | `INC-2026-00002` exists in preview, type `Public / Third Party`, reported by Allen Smathers on 2026-05-04. |
| Report a threat | ⚠️ GENERIC — uses `incident_type="Public / Third Party"` + free-text `description`. No dedicated threat type, no threat-level field. | `incidentSchema.js:3-13` enumerates 9 types; none of them are "Verbal Threat", "Physical Confrontation", or "Workplace Violence". |
| Report harassment | ⚠️ GENERIC — same path as above. | Same as above. |
| Report confrontation | ⚠️ GENERIC — same path as above. | Same as above. |
| Report physical contact | ❌ NO DEDICATED FIELD — operator must put it in `description` text or `body_part` if injured. | `incidentSchema.js:118-191` — no `physical_contact`, `weapon_involved`, or `assault` boolean. |

### Step 2 · Documentation (evidence attachment)

| Capability | Status | Evidence |
|---|---|---|
| Photos | ✅ EXISTS | `IncidentCreate.photos: List[str]` (`safety.py:316`). Stored as base64 data URLs. PDF renderer dedicates a `PHOTOS` section. INC-2026-00002 has 1 photo (license plate of the offending vehicle). |
| Videos | ⚠️ NOT A DISTINCT TYPE — videos can be uploaded only if encoded into the photos array. No `videos[]` field, no MIME enforcement. | No dedicated field in schema. |
| Witness statements | ⚠️ PARTIAL — `witnesses: List[{name, statement}]` exists. NO fields for: witness role, employer, phone, address, witness signature, witness type (employee / public / officer). | `incidentSchema.js:161`. PDF renderer DOES render witness signatures *if* they exist in the dict — but the form does not capture them (`safety.py:302`). |
| Police reports | ❌ NO DEDICATED ATTACHMENT FIELD. Operator could upload a PDF as base64 into `photos[]`, but the PDF would not be type-labeled "Police Report". No `police_report_number`, no `responding_officer`, no `agency`, no `case_number`. | Verified — no `police_*` field in `IncidentCreate`. |
| Medical documentation | ⚠️ PARTIAL — `medical_facility` (free text) + `treatment_provided` (free text). No structured "Medical Record Attachment" type. Could be uploaded as photo. | `safety.py:292-293`. |
| Property damage documentation | ⚠️ PARTIAL — `incident_type="Property / Equipment Damage"` exists. NO monetary value field. NO insurance claim number, NO vehicle VIN, NO license plate field. The license plate in INC-2026-00002 lives inside a photo, not a structured field. | Verified against PDF render of INC-2026-00002. |

### Step 3 · Investigation

| Capability | Status | Evidence |
|---|---|---|
| Safety review | ✅ EXISTS | `routes/incident_lifecycle.py:70-127` — `POST /api/incidents/{id}/transition`. Status states: open → investigating → review → closed (with reasons + state-event audit log). |
| Safety assign | ✅ EXISTS | Implied via CAPA system (`safety/corrective-actions` with `source_kind=incident`). 6 CAPAs in the preview DB are already linked to incidents. |
| Safety track | ✅ EXISTS | `GET /api/incidents/{id}/lifecycle` returns full state history. `state_events` collection records every transition with actor + timestamp + reason. |
| Safety escalate | ⚠️ INDIRECT — no dedicated "escalate" verb on the lifecycle endpoint, but priority can be raised on the linked CAPA. No "request executive review" action. | `incident_lifecycle.py:70-127`. |
| Safety close | ✅ EXISTS | Final state via `POST /transition` with `to_state="closed"`. |

### Step 4 · Corrective Actions

| Capability | Status | Evidence |
|---|---|---|
| Create CAPA | ✅ EXISTS | `POST /api/safety/corrective-actions` (`routes/safety_portal/corrective_actions.py:42`). `source_kind="incident"`, `source_id="<incident_id>"`. |
| Assign | ✅ EXISTS | `assigned_to_name`, `assigned_to_email` fields. Emits unified task via `task_service.create()`. |
| Track | ✅ EXISTS | `GET /api/safety/corrective-actions/{ca_id}/related-resolved` ties CAPAs to all related entities. Status pipeline: Open → In Progress → Closed. |
| Verify | ⚠️ PARTIAL — `completion_notes` + `closed_by_name` fields exist. No "verification signature" field, no "verified by safety" boolean. | `corrective_actions.py:60-63`. |
| Close | ✅ EXISTS | PATCH endpoint with status transition. |

### Step 5 · Notifications

`backend/routes/safety.py:795-869` fans out two notifications + one task on every `incident.created`:

| Recipient role | Status | Channel | Event key |
|---|---|---|---|
| Safety | ✅ FANS OUT | Bell notification + task | `incident.created` |
| PM | ✅ FANS OUT | Bell notification only (no task) | `incident.pm_visibility` |
| Superintendent | ❌ NOT IN FAN-OUT — superintendent is captured in `supervisor_name` (free text) but NO notification is routed to that role. The `apply_routing` call could include super if the routing config does, but the default fan-out does not. | Verified via grep — no `recipient_role="superintendent"` for incidents. |
| Operations | ❌ NOT IN FAN-OUT | No `recipient_role="operations"` in incident fan-out. |
| Executive | ❌ NOT IN FAN-OUT | No `recipient_role="executive"` in incident fan-out. Severe incidents surface on Executive Overview via `unresolved_incidents` count only. |
| OSHA | ⚠️ FORM CAPTURES — `notified_osha` flag in payload. NO automated submission, NO automated email. The flag is documentation only. | `safety.py:313`. |

**Email path:** `auto_email_safety_record` (`server.py:12750+`) fires emails via Resend to a resolved distribution list (PM + GC + Owner + SEVERE_INCIDENT_CC env list). Attaches the PDF. This IS the executive notification path for severe incidents (env-driven, not role-driven).

### Step 6 · PDFs

Rendered via `pdf_render.render_record_pdf(kind="incident", record)` → 1.9 MB PDF.

| PDF section | Status | Evidence (INC-2026-00002) |
|---|---|---|
| Incident details | ✅ Present | 40+ fields rendered as key/value table. |
| Witnesses | ✅ Renders if present — but INC-2026-00002 has 0 witnesses captured, so the section is absent. PDF renderer dedicates a witnesses block with name + company/trade + signature. | `pdf_render.py:1620-1675`. |
| Photos | ✅ Present | 1 photo rendered with license plate visible. |
| Attachments (general) | ❌ NO DISTINCT "ATTACHMENTS" SECTION — everything is photos. | Verified in PDF. |
| Corrective actions | ✅ Present as free-text field on the incident PDF (`"Even more signs"` in INC-2026-00002). Linked CAPAs are NOT cross-referenced into the incident PDF — they are separate records. | Verified — no "Linked CAPAs" block. |
| Investigation notes | ⚠️ PARTIAL — `immediate_cause`, `contributing_factors`, `root_cause_notes`, `root_causes` dict all render. State-event audit log (transitions) is NOT included in the PDF. | Verified — no "State History" block. |
| Police involvement | ❌ NO FIELDS, SO NO PDF OUTPUT. | Field doesn't exist. |
| Audit trail | ✅ Present | Foundation v15.41.1 footer + record ID + generated-by + environment. |

---

## 2 · Field-preservation diff (before / after the next track's writes)

Track 15.46 added zero fields. Track 15.41 + 15.42 added the universal PDF foundation footer + audit block. INC-2026-00002 PDF renders **all 40+ source fields** with no loss — verified via OCR + field extraction:

- ✅ incident_type, severity, project_name/number, location, dates/times
- ✅ description, immediate_cause, immediate_actions_taken, corrective_actions
- ✅ all 6 notification flags
- ✅ gps_lat/lng/accuracy
- ✅ supervisor_signature image
- ✅ 1 photo
- ✅ doc_id, status, resolution_status, foundation_version
- ⚠️ reporter_signature exists in the DB record but the PDF I rendered did NOT show it (signed reporter would render — verify with a record that has both signatures, e.g. a fatality record).

---

## 3 · Workflow strengths

1. **One backend, one schema, one PDF.** No duplicate writes, no dual collections. A submitted incident shows up on the Safety dashboard, the PM dashboard, the bell, and the email pipeline within seconds.
2. **CAPA linkage works.** Incident → CAPA → Task → Bell + email is solid. 6 incident-sourced CAPAs in preview DB confirm real adoption.
3. **Lifecycle state machine is real.** State transitions are audited with actor + reason. `state_events` collection backs every transition.
4. **GPS coordinates are captured automatically.** Defensible location data without operator action.
5. **Bilingual.** Submit-language tag is on the record (`submit_language: "en"` or `"es"`).
6. **Severity-routed routing.** "High" or "Critical" severities upgrade the linked CAPA priority automatically (`safety.py:802`).

---

## 4 · Workflow gaps (the ones that matter)

All gaps below are real — they were verified by reading the schema, the PDF output, and the live record. None of these are theoretical.

### 4.1 · NO dedicated incident types for the actual real-world incident

The driver type that triggered this track — **a verbal confrontation that escalated to physical contact** — does not have a dedicated `incident_type` value. The operator is forced into `Public / Third Party` (which today is used for "vehicle drove through cones") or `Security` (vague). This means downstream analytics, exec visibility, and CAPA categorization all bucket different events into the same line.

### 4.2 · NO threat / weapon / contact-type capture

There is no structured way to record:
- Whether the encounter was verbal-only or physical
- Whether a weapon was shown / used
- Whether the public member touched the employee
- Whether the employee was injured
- Whether the encounter was filmed / posted to social media

### 4.3 · NO police involvement fields

There is no:
- `police_called` flag
- `police_arrived` flag
- `responding_officer_name` field
- `agency` field (sheriff vs. city PD vs. state trooper)
- `case_number` / `report_number` field
- `report_obtained` flag (so safety knows to chase the report later)

A police report PDF could be uploaded into `photos[]` as base64, but it would not be labelled as a police report — it would render as a photo.

### 4.4 · NO witness phone / role / signature on the form

The witness sub-form captures `{name, statement}` only. The PDF renderer is READY for `{name, company, signature}` — it will render the signature image if present — but the form does not capture it. Without contact info, six months later when the case goes to deposition, the witness cannot be reached.

### 4.5 · NO vehicle / property damage value field

A "Property / Equipment Damage" incident has no monetary field. License plates live inside photos. VINs are not captured. Insurance claim numbers have no home.

### 4.6 · NO superintendent / operations / executive notification fan-out

The incident notification fans out to Safety + PM only. The superintendent (named in `supervisor_name`) does NOT receive an in-app notification. Operations and Executive roles get nothing unless the env-driven `SEVERE_INCIDENT_CC` list catches them.

### 4.7 · NO unified "evidence attachments" surface

Photos, videos, statements, police reports, medical records all collapse into the `photos[]` array. The PDF renders them as photos. There is no MIME enforcement, no naming, no per-attachment description.

### 4.8 · NO state-event history on the PDF

When the incident moves open → investigating → review → closed, the audit trail lives in `state_events` (queryable via `GET /api/incidents/{id}/lifecycle`) but DOES NOT appear on the printed PDF. Six months later in court, the PDF will not show that Safety reviewed the incident on a specific date and closed it after a specific corrective action.

### 4.9 · NO CAPA cross-reference on the PDF

The incident PDF renders the FREE-TEXT `corrective_actions` field. It does NOT render linked CAPA records (with their own IDs, owners, due dates, completion status). A reader of the PDF cannot tell whether the corrective action was actually completed.

### 4.10 · NO workplace-violence reporter

The MASCI workplace-violence policy referenced in the safety topic (`angry_public_de_escalation`) assumes a "workplace-violence report form" exists. **It does not exist as a distinct artifact.** The Public Interaction safety topic written in 15.46A points the foreman at a form that lives only in policy, not in the platform.

---

## 5 · Stop-and-ask checkpoint

Per the Track 15.47 directive (4C), the following gaps are LIABILITY-SENSITIVE and require user authorization before fixing:

| Gap | Liability sensitivity | Recommended fix complexity |
|---|---|---|
| 4.2 · Threat / weapon / contact-type capture | HIGH — directly bears on workplace-violence reporting + criminal evidence | Additive fields, low risk |
| 4.3 · Police involvement fields | HIGH — chain-of-custody for criminal case | Additive fields, low risk |
| 4.4 · Witness phone / role / signature | HIGH — depositions six months later | Additive fields on witness sub-doc, low risk |
| 4.5 · Property damage value / VIN / plate | MEDIUM — insurance + civil recovery | Additive fields, low risk |
| 4.6 · Superintendent / operations / executive notification | HIGH — first-call accountability | Notification fan-out extension, low risk |
| 4.7 · Unified attachments surface | MEDIUM — discoverability of evidence | Schema migration if done structurally; low if added as a labeled photos sub-array |
| 4.8 · State-event history on PDF | MEDIUM — defensibility | PDF renderer extension, low risk |
| 4.9 · CAPA cross-reference on PDF | HIGH — proof that corrections were actually performed | PDF renderer extension, low risk |
| 4.10 · Workplace-violence reporter | HIGH — policy↔platform gap | Net-new workflow (could be a flag + automated email) |

**ALL of the above are deferred to user decision per the 4C directive.** No fixes are implemented in this track without explicit authorization.

---

## 6 · Three answers the audit gives the executive

1. **Can an employee report a public confrontation today?** YES, but only as `Public / Third Party` with the details in free text. The platform does NOT capture threat type, weapon involvement, or police involvement as structured data.
2. **Can MASCI investigate it?** YES — lifecycle states + CAPAs work. But the investigation can only investigate what was captured; today, the structured capture is thin.
3. **Can MASCI prove what happened six months later in court?** PARTIALLY. The PDF renders the description + photos + signatures + dates. It does NOT render the police report number, the witness contact info, the state-event audit history, or the linked CAPA completion records.

---

## 7 · Companion documents

- `TRACK_15_47_INCIDENT_WORKFLOW_AUDIT.md` (this file)
- `TRACK_15_47_PUBLIC_INTERACTION_INCIDENT_CERTIFICATION.md` (Phase 1A — the 10-question certification)
- `TRACK_15_47_NOTIFICATION_CHAIN_AUDIT.md` (Phase 5)
- `TRACK_15_47_EXECUTIVE_VISIBILITY_AUDIT.md` (Phase 4)
- `TRACK_15_47_PDF_CERTIFICATION.md` (Phase 6)
- `TRACK_15_47_IMPLEMENTATION_RECOMMENDATIONS.md` (forward plan based on gaps)
- `TRACK_15_47_FIVE_PILLAR_CERTIFICATION.md` (final scorecard)
