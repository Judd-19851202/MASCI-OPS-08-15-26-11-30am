# Track 19.05 · Daily Report Data Model Map

Complete field-by-field map. Source: `/app/backend/routes/daily_reports.py::DailyReportCreate` + `DailyReport`. Audit only — no schema changes.

## Header / project identity

| Field | Type | Req | Source | PDF | Email | PM | Admin | Historical Snapshot | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | UUID str | system | server | ✓ | ✓ | ✓ | ✓ | ✓ | Persistent DR id |
| `doc_id` | `DR-YYYY-NNNNN` | system | `ensure_doc_id` | ✓ | ✓ | ✓ | ✓ | ✓ | Human-readable |
| `report_number` | `DR-YYYYMMDD-NNN` | auto-filled | `/next-number` | ✓ | ✓ | ✓ | ✓ | ✓ | Foreman may edit |
| `report_date` | `YYYY-MM-DD` | REQ | user | ✓ | ✓ | ✓ | ✓ | ✓ | Drives report_number date prefix |
| `project_name` | str | REQ | job pick / manual | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `project_number` | str | REQ-ish | job pick / manual | ✓ | ✓ | ✓ | ✓ | ✓ | Drives PM routing + recent-context |
| `location` | str | REQ | GPS button / manual | ✓ | — | ✓ | ✓ | ✓ | — |
| `prepared_by` | str | REQ | portal FL user OR manual | ✓ | ✓ | ✓ | ✓ | ✓ | Signature owner |
| `superintendent` | str | opt | jobs_master.superintendent OR recent DR | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `created_at` | ISO datetime | system | server | ✓ | ✓ | ✓ | ✓ | ✓ | UTC |

## Weather

| Field | Type | Notes |
| --- | --- | --- |
| `weather_summary` | str | Free text |
| `weather_snapshots[]` | list of dicts | `{time, temp_f, conditions, wind_mph, …}` from weather refresh |
| `weather_impact` | Yes/No | Triggers notes |
| `weather_impact_notes` | str | Conditional |

## Safety triggers (all Yes/No + conditional detail)

`schedule_delays`, `schedule_delays_notes`, `safety_incidents_today`, `injuries_reported`, `incident_notes`, `safety_notified`, `safety_contact_person`, `safety_contact_time`, `incident_report_filled`, `incident_report_time`.

## Row-based sections (all List[Dict])

| Array | Row shape (informal) | Purpose |
| --- | --- | --- |
| `masci_crews[]` | `{name, employee_id, trade, start_time, lunch_minutes, stop_time, hours, work_performed}` | MASCI crew (Section 04) |
| `subcontractors[]` | `{company, trade, foreman, count, hours, work_performed, attachment_note, photos[]}` | Section 05 |
| `visitors[]` | `{name, company, purpose, in_time, out_time}` | Section 06 |
| `equipment[]` | `{description, hours_used, time_delivered, time_removed, notes}` | Section 07 |
| `materials[]` | `{material, quantity, unit, supplier, ticket_number, notes, ticket_photos[]}` | Inbound Section 08 |
| `outbound_materials[]` | `{material, quantity, unit, hauler, destination, ticket_or_manifest, notes}` | Section 09 (MM-ENTRY-002 K-MM-1) |
| `activities[]` | `{description, notes}` (free text) | Section 10 legacy activity log |
| `production[]` | `ProductionRow` `{row_id, description, quantity, unit, custom_unit_label, station_from, station_to, location, notes}` | Section 10 structured (Wave-1A) |
| `constraints[]` | `ConstraintRow` `{row_id, constraint_type, hours_impact, notes, may_require_rfi, may_affect_schedule}` | Section 10 delays/constraints |

## Narrative + attachments

| Field | Notes |
| --- | --- |
| `narrative_sections{}` | Optional guided-prompt dict: `work_completed, delays, inspections, materials_received, follow_ups, tomorrow_plan` (Track 15.62 recovery) |
| `general_notes` | Free-text catch-all |
| `photos[]` | List of data URLs at submit → `_sanitize_inline_photos` converts to `photo://…` refs |
| `photo_captions[]` | Parallel to `photos[]` |
| `attachments[]` (Track 19.04) | `{attachment_ref, mime_type, extension, category, filename, file_size, uploaded_at}` |
| `distribution_list[]` | Up to 20 extra email recipients |
| `prepared_by_signature` | Base64 signature data URL |
| `superintendent_signature` | DR-FIX-3 R13 — removed from UI, retained in schema for legacy compat |

## System / audit fields

| Field | Notes |
| --- | --- |
| `audit_envelope_sha256` | SHA256 of the sanitized doc — tamper detection |
| `prepared_by_identity` | Structured directory identity when signed-in FL/portal token present |
| `prepared_by_bound` | True when identity resolved |
| `team_snapshot` | Job-ownership roster snapshot at submit (Phase 2B-2A) |
| `linked_excavation_ids[]` + `excavation_activity_today` | Two-way trench linkage (Phase 10A-B) |

## Field source-of-truth taxonomy

| Source | Fields |
| --- | --- |
| Foreman-typed | `general_notes`, all row `notes`, `weather_summary`, `activities[]`, `production[]`, most row data |
| Auto-filled (deferred to explicit apply) | `superintendent` from jobs_master; crew + equipment via v19.04 Smart Prefill offer |
| GPS | `gps_lat`, `gps_lng`, `gps_accuracy` |
| System | `id`, `doc_id`, `created_at`, `audit_envelope_sha256`, `team_snapshot`, `prepared_by_identity`, `prepared_by_bound` |
| Portal token | `submitter_employee_id`, `submitter_email_at_submit` |

## Redesign protection

* **MUST PRESERVE** every named field. The audit hash + PDF renderer + PM aggregator + trust-spine reader + advisory-flag deriver + team_snapshot embed all read from the persisted shape.
* Fields may be **renamed in UI**, but the schema key must not change without a coordinated backfill migration + PDF template update + audit hash migration.
