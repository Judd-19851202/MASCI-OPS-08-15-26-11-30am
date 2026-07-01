# TRACK 19.08 · Master Field Dictionary

Every field on the top-8 form pages. Column semantics defined in `01_MASTER_FORM_INVENTORY.md`.

**Extraction methodology**: Static parse of the `New*.jsx` pages + Pydantic models under `backend/routes/*.py` + backend schemas in `server.py`. Line references included where nontrivial. Full dictionary is machine-regeneratable via the drift-lock test `test_track_19_08_forms_audit_snapshots.py`.

---

## 1 · Field-classification legend

| Classification | Meaning |
| --- | --- |
| REQUIRED | Server or client refuses submit if empty |
| CONDITIONAL | Only shown / validated when a sibling field has a specific value |
| AUTO | Auto-populated (GPS, Smart Prefill, HR roster, next-number) |
| CALC | Derived from other fields (hours from start/lunch/stop; count aggregates) |
| LEGACY | Kept for backward-compat; new records may leave blank |
| DERIVED | Computed at read-time (not stored) — e.g. `crew_count = $size masci_crews` |
| PDF | Rendered on WeasyPrint PDF |
| EMAIL | Included in email body |
| CSV | Included in CSV export |
| ADMIN-ONLY | Only visible to admin readers |

---

## 2 · Daily Report (audited in 19.05; canonical anchor)

Full field spec preserved in `TRACK_19_05_*.md` (previously produced). Anchor collections: `daily_reports`. Schema-key lock is enforced by 59 assertions in `test_track_19_05_daily_report_total_audit.py`.

Key fields (excerpt — full list in the 19.05 audit):
`project_number` REQUIRED · `project_name` REQUIRED · `report_date` REQUIRED · `prepared_by` REQUIRED · `superintendent` AUTO+editable · `location` REQUIRED · `gps_lat`/`gps_lng`/`gps_accuracy` AUTO · `masci_crews[]` (name·employee_id·trade·start_time·stop_time·lunch_minutes·hours CALC·work_performed) · `subcontractors[]` · `visitors[]` · `equipment[]` · `production[]` · `materials[]` (inbound) · `outbound_materials[]` · `constraints[]` · `schedule_delays` Yes/No · `weather_impact` Yes/No · `weather_conditions` · `safety_incidents_today` Yes/No · `injuries_reported` Yes/No · `injury_report_details` CONDITIONAL · `accident_report_details` CONDITIONAL · `narrative_sections` (collapsed post-19.07) · `operational_notes` optional · `tomorrow_plan` REQUIRED · `photos[]` REQUIRED (min 6) · `attachments[]` (PDF/XLSX/XLS/CSV) · `prepared_by_signature` REQUIRED · `linked_excavation_ids[]` CONDITIONAL · `excavation_activity_today` Yes/No.

---

## 3 · Equipment Pre-Op — `NewEquipmentInspection.jsx` · collection `equipment_inspections`

| Field | Type | Classification | UI section | Notes |
| --- | --- | --- | --- | --- |
| `unit_number` / `asset_id` | string | REQUIRED · AUTO (via `EquipmentCombo`) | Asset picker | Legacy: `unit_number` and `asset_id` were both stored; new records use `asset_id` canonical; compat read supports both. |
| `equipment_type` | string | REQUIRED · CONDITIONAL (drives template load) | Asset picker | Determines which inspection template section renders |
| `operator_name` | string | REQUIRED | Header | Free text (not linked to HR by default) |
| `operator_employee_id` | string | AUTO (HR roster pick) | Header | Populated via EmployeeCombo |
| `project_number` | string | REQUIRED · AUTO (via `JobPicker`) | Job | |
| `project_name` | string | REQUIRED · AUTO | Job | |
| `location` | string | REQUIRED | Job | Free text; no GPS auto-fill (see friction §3) |
| `inspection_date` | date | REQUIRED | Header | |
| `shift_start` / `shift_end` | time | Optional | Header | |
| `sections[]` | array | REQUIRED (template-driven) | Inspection body | Each section carries `title`, `items[]` where each item has `label`, `status` (`pass`/`fail`/`na`), `notes`, `photos[]`. See `06_INSPECTION_ENGINE_SPECIFICATION.md` for the template contract. |
| `overall_status` | enum | CALC | Footer | Derived from item statuses: any FAIL → OOS |
| `defects[]` | array | CALC | Footer | Snapshot of failed items with photos + notes |
| `photos[]` | array | Optional (but expected) | Attachments | |
| `attachments[]` | array | Optional | Attachments | |
| `operator_signature` | data-URL | REQUIRED | Sign-off | |
| `submitted_at` | ISO datetime | AUTO | System | |
| `pdf_url` | string | AUTO (post-render) | System | R2 key |
| `email_dispatched_at` | ISO datetime | AUTO | System | Set by `schedule_auto_email` |
| `defect_ticket_ids[]` | array | AUTO | System | IDs of `fleet_defects` created on FAIL |

**Legacy compat fields**: `unit_number` (kept for reads); pre-Track-15.x flat `checklist[]` array is read but no longer written.

---

## 4 · DVIR — `NewFleetDVIR.jsx` · collections `fleet_audit` · `fleet_defects` · `fleet_status`

| Field | Type | Classification | UI section | Notes |
| --- | --- | --- | --- | --- |
| `unit_number` | string | REQUIRED · AUTO (via `EquipmentCombo` filtered by vehicles) | Header | |
| `dvir_type` | enum | REQUIRED | Header | `pre_trip` / `post_trip` / `weekly_lead` / `weekly_emergency` |
| `driver_name` / `driver_employee_id` | string | REQUIRED · AUTO | Header | |
| `odometer` | integer | REQUIRED | Header | |
| `location` | string | REQUIRED | Header | |
| `inspection_date` / `inspection_time` | date / time | REQUIRED | Header | |
| `sections[]` (Engine · Steering · Brakes · Tires · Lights · Body · Emergency-Equipment · etc.) | array | REQUIRED | Body | Template loaded by `dvir_type` + `equipment_type` |
| `defects[]` | array | CALC | Body | Failed items → mirrored to `fleet_defects` collection at submit |
| `overall_status` | enum | CALC | Footer | `safe_to_operate` / `unsafe_out_of_service` |
| `next_action` | enum | CALC | Footer | derived from `overall_status` |
| `driver_signature` | data-URL | REQUIRED | Sign-off | |
| `mechanic_signature` | data-URL | CONDITIONAL | Sign-off | Required when defect is resolved by shop before return-to-service |
| `photos[]` · `attachments[]` | arrays | Optional | Attachments | |
| `submitted_at` · `pdf_url` · `email_dispatched_at` | AUTO fields | | System | |
| `oos_applied_at` | ISO datetime | AUTO on FAIL | System | Sets `fleet_status.status = out_of_service` |
| `oos_cleared_at` | ISO datetime | AUTO on cleared | System | Set by shop / dispatch action |

---

## 5 · Safety Meeting / Toolbox — `NewMeeting.jsx` · collection `meetings`

| Field | Type | Classification | UI section | Notes |
| --- | --- | --- | --- | --- |
| `meeting_type` | enum | REQUIRED | Header | `safety_meeting` / `toolbox_talk` / `pre_task_briefing` |
| `topic` | string | REQUIRED | Topic | Free text; suggested list from `safety_topics` collection |
| `topic_source_id` | string | AUTO (from library) | Topic | Optional linkage to Safety Topic Library entry |
| `project_number` / `project_name` | strings | REQUIRED · AUTO | Job | |
| `location` | string | REQUIRED | Job | |
| `meeting_date` / `meeting_time` / `meeting_duration_minutes` | date/time/int | REQUIRED | Header | |
| `presenter_name` / `presenter_employee_id` | string | REQUIRED | Header | |
| `attendees[]` | array of `{name, employee_id, signature}` | REQUIRED (min 1) | Attendance | HR roster picker |
| `topics_covered` | string (long) | REQUIRED | Body | Free text; sometimes auto-filled from library |
| `key_takeaways` | string | Optional | Body | |
| `photos[]` | array | Optional | Attachments | |
| `attachments[]` | array | Optional | Attachments | |
| `presenter_signature` | data-URL | REQUIRED | Sign-off | |
| `submitted_at` · `pdf_url` · `email_dispatched_at` | AUTO | | System | |

**Absence**: No knowledge-check / comprehension field. Rationale in `11_SAFETY_MEETING_FORENSICS.md`.

---

## 6 · Incident / Injury / Accident / Near-Miss — `NewIncident.jsx` · collection `incidents`

| Field | Type | Classification | UI section | Notes |
| --- | --- | --- | --- | --- |
| `incident_type` | enum | REQUIRED | Header | `incident` / `injury` / `accident` / `near_miss` / `property_damage` / `vehicle` |
| `severity` | enum | REQUIRED | Header | `low` / `medium` / `high` / `critical` |
| `incident_date` / `incident_time` | date/time | REQUIRED | Header | |
| `discovered_by` / `reported_by` | strings | REQUIRED · AUTO | Header | |
| `project_number` / `project_name` / `location` | strings | REQUIRED · AUTO | Job | |
| `gps_lat`/`gps_lng`/`gps_accuracy` | floats | AUTO | Job | |
| `people_involved[]` | array | CONDITIONAL (min 1 when injury/accident) | Body | |
| `injuries[]` | array of `{name, employee_id, body_part, treatment_level, medical_facility}` | CONDITIONAL (required when `incident_type=injury`) | Body | |
| `equipment_involved[]` | array | Optional | Body | |
| `witnesses[]` | array | Optional | Body | |
| `description` | long text | REQUIRED | Body | |
| `immediate_actions` | long text | REQUIRED | Body | |
| `root_cause_notes` | long text | Optional (encouraged) | Body | |
| `photos[]` · `attachments[]` | arrays | REQUIRED (min 1 photo when injury/accident) | Attachments | |
| `reporter_signature` · `supervisor_signature` | data-URLs | REQUIRED / REQUIRED-if-super-present | Sign-off | |
| `submitted_at` · `pdf_url` · `email_dispatched_at` | AUTO | | System | |
| `lifecycle_state` | enum | AUTO | System | `reported` → `in_investigation` → `closed` (via `/incidents/{id}/transition`) |
| `recovery_actions[]` | array | Appended via transitions | System | Emergent from state-event stream |
| `corrective_action_ids[]` | array | AUTO | System | IDs of `corrective_actions` records generated |
| `osha_recordable` | boolean | Optional (manual flag) | Footer | |
| `osha_form_300_number` | string | Optional | Footer | |

**Legacy compat**: `injury_reported` / `accident_reported` booleans — kept for pre-typed-schema records; new records rely on `incident_type` enum.

---

## 7 · JHA / Job Hazard Analysis — `NewInspection.jsx` (JHA subtype) · collection `jhas` + `jha_acknowledgements`

| Field | Type | Classification | UI section | Notes |
| --- | --- | --- | --- | --- |
| `jha_template_id` | string | REQUIRED | Header | Template published in `jhas` |
| `project_number` / `project_name` | REQUIRED · AUTO | Header | |
| `task_description` | string | REQUIRED | Header | |
| `crew_names[]` | array | REQUIRED (min 1) | Attendance | |
| `hazards[]` | array of `{hazard, mitigation, residual_risk}` | REQUIRED | Body | |
| `signatures[]` | array of `{name, employee_id, signature}` | REQUIRED (min 1) | Sign-off | |
| `photos[]` · `attachments[]` | arrays | Optional | Attachments | |
| `submitted_at` · `pdf_url` · `email_dispatched_at` | AUTO | | System | |

**Acknowledgement records** (`jha_acknowledgements`): tie each attendee to a specific published JHA revision so audits can prove *who saw which version*. Separate collection because JHA templates are amended; the acknowledgement is immutable.

---

## 8 · QA-QC Inspection — `NewQaqcInspection.jsx` · collection `inspections` (subtype `qaqc`)

| Field | Type | Classification | UI section | Notes |
| --- | --- | --- | --- | --- |
| `inspection_type` | enum | REQUIRED | Header | subtype constant `qaqc` |
| `qaqc_slug` | string | REQUIRED · AUTO (from route param) | Header | Selects template from `pm_templates` |
| `project_number` / `project_name` / `location` | REQUIRED · AUTO | Header | |
| `inspection_date` | REQUIRED | Header | |
| `inspector_name` / `inspector_employee_id` | REQUIRED · AUTO | Header | |
| `sections[]` | array | REQUIRED | Body | Same shape as Equipment sections |
| `defects[]` | array | CALC | Body | Failed items snapshot |
| `overall_status` | enum | CALC | Footer | `pass` / `fail` / `n_a` |
| `photos[]` · `attachments[]` | arrays | Optional | Attachments | |
| `inspector_signature` | REQUIRED | Sign-off | |
| `submitted_at` · `pdf_url` · `email_dispatched_at` | AUTO | | System | |

---

## 9 · Safety Equipment Issuance — `NewSafetyEquipmentIssuance.jsx` · collection `equipment_issuances`

| Field | Type | Classification | Notes |
| --- | --- | --- | --- |
| `employee_id` · `employee_name` | REQUIRED · AUTO | HR roster pick |
| `equipment_items[]` | array of `{item_type, size, serial, condition}` | REQUIRED (min 1) | |
| `issuance_date` | REQUIRED | |
| `issued_by` | REQUIRED · AUTO | |
| `employee_signature` · `issuer_signature` | REQUIRED | |
| `photos[]` · `attachments[]` | Optional | |
| `pdf_url` | AUTO | R2 |
| `returned_at` · `return_signature` | CONDITIONAL | Set only on Return action |

---

## 10 · Safety Equipment Training — `NewSafetyEquipmentTraining.jsx` · collection `equipment_trainings`

| Field | Type | Classification | Notes |
| --- | --- | --- | --- |
| `employee_id` · `employee_name` | REQUIRED · AUTO | |
| `equipment_type` | REQUIRED | |
| `training_date` | REQUIRED | |
| `trainer_name` / `trainer_employee_id` | REQUIRED · AUTO | |
| `topics_covered` | REQUIRED | |
| `competency_verified` | boolean | REQUIRED | |
| `employee_signature` · `trainer_signature` | REQUIRED | |
| `photos[]` · `attachments[]` | Optional | |
| `pdf_url` | AUTO | R2 |

---

## 11 · Corrective Action — `SafetyCorrectiveActions.jsx` · collection `corrective_actions`

| Field | Type | Classification | Notes |
| --- | --- | --- | --- |
| `source` | enum | REQUIRED | `incident` / `audit` / `inspection` / `manual` |
| `source_id` | string | CONDITIONAL | ID of triggering doc |
| `title` · `description` | REQUIRED | |
| `assigned_to_employee_id` | REQUIRED | |
| `due_date` | REQUIRED | |
| `status` | enum | REQUIRED | `open` / `in_progress` / `closed` / `verified` |
| `closure_notes` · `closure_photos[]` | CONDITIONAL | |
| `verified_by` / `verified_at` | CONDITIONAL | |
| `created_at` · `closed_at` | AUTO | |

---

## 12 · Excavation / Trench — collection `trench_excavations`

Anchored by Track 15.5x; consumers include Daily Report (via `linked_excavation_ids[]`).

Key fields: `excavation_id` · `project_number` · `depth_feet` · `width_feet` · `soil_type` · `protective_system` · `competent_person` (name + signature) · `photos[]` · `benching_required` · `sloping_required` · `shoring_required` · `access_egress` · `atmospheric_testing_required` · `daily_inspection_records[]` · `backfilled_at`.

---

## 13 · Fields shared across ALL New*.jsx forms

* `project_number` / `project_name` — HR canonical job source
* `submitted_at` — set server-side
* `pdf_url` — R2 key set post-render
* `email_dispatched_at` — set by `schedule_auto_email`
* `photos[]` (data URL → R2 key + thumb URL)
* `attachments[]` (unified envelope from Track 19.04 — PDF/XLSX/XLS/CSV)
* Signature data URL(s)
* `submit_language` (Track 19.07 — en/es submission trace)
* `idempotency_key` (Track 15.x — dedupe replayed submits)

---

## 14 · Field-value shape drift observed (not fixed — audit only)

| Form | Field | Observed values | Comment |
| --- | --- | --- | --- |
| DR crew rows | `lunch_minutes` | int (30) *and* string ("30") | Post-19.06-amendment tests already tolerate both |
| Equipment inspection | `overall_status` | `pass` / `fail` / `n_a` / `partial` / `pending_review` | `pending_review` is a legacy-only value; still readable |
| Incident | `incident_type` vs. `injury_reported` boolean | Newer records use enum; older records had both | Compat shim in read layer |
| Meeting | `meeting_type` | `safety_meeting` / `toolbox_talk` / `pre_task_briefing` / `tailgate` | `tailgate` is a legacy synonym for `toolbox_talk` |

Preserved in `14_REDESIGN_PROTECTION_MATRIX.md` as "MUST PRESERVE — read tolerance".
