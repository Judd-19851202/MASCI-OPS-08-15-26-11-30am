# Track 19.05 · Daily Report Redesign Protection Matrix

Classification for the future redesign. Audit only — no changes made.

## Legend

| Level | Meaning |
| --- | --- |
| **MUST PRESERVE** | Critical operational/legal/PM/safety/payroll/compliance surface. Redesign must not remove or rename. |
| **CAN SIMPLIFY** | Retain but improve UX (grouping, helper text, progressive disclosure). |
| **CAN MERGE** | Duplicate/overlap with another; can be combined at UI level (persisted schema stays). |
| **CAN HIDE BEHIND YES/NO** | Only relevant when event occurred; hide until trigger fires. |
| **CAN REMOVE** | Low/no value, not routed, not used, confusing, or dead. |
| **NEEDS DECISION** | Business decision required (operator + PM + safety leader) before redesign. |

## Matrix

| Field / section / control | Classification | Notes |
| --- | --- | --- |
| `id`, `doc_id`, `created_at`, `audit_envelope_sha256` | MUST PRESERVE | System-generated audit backbone |
| `report_number` (`DR-YYYYMMDD-NNN`) | MUST PRESERVE | Prefix index; PDF filename |
| `report_date`, `project_name`, `project_number`, `location`, `prepared_by`, `superintendent` | MUST PRESERVE | Every downstream surface reads these |
| `weather_summary`, `weather_snapshots[]` | MUST PRESERVE | Legal record of conditions |
| `weather_impact` + notes | CAN MERGE | With `constraints[]` weather type (UI-merge only) |
| `schedule_delays` + notes | CAN MERGE | With `constraints[]` (UI-merge only) |
| `safety_incidents_today` + `injuries_reported` | MUST PRESERVE | Distinct legal/insurance signals |
| Incident escalation cascade (safety_notified, contact_person, contact_time, incident_report_filled, incident_report_time) | MUST PRESERVE | Regulatory reporting |
| `general_notes` | CAN HIDE BEHIND YES/NO | Show "Additional notes?" toggle |
| `masci_crews[]` | MUST PRESERVE | Payroll + HR + accountability |
| `subcontractors[]` | MUST PRESERVE | Billing + coverage |
| `visitors[]` | CAN HIDE BEHIND YES/NO | 20% usage — trigger "Did visitors come today?" |
| `equipment[]` | MUST PRESERVE | Equipment cost + shop maintenance signal |
| `materials[]` (inbound) | MUST PRESERVE | Compliance + accounting |
| `outbound_materials[]` | MUST PRESERVE | Environmental + accounting |
| `activities[]` (legacy) | CAN REMOVE (from UI; keep schema) | 3% adoption; superseded by production[] |
| `production[]` (Wave-1A) | MUST PRESERVE — needs BETTER UX | 0% adoption is a UX failure, not a schema failure |
| `constraints[]` (Wave-1A) | MUST PRESERVE — needs BETTER UX | 0% adoption; drives advisory RFI + schedule signals |
| `narrative_sections{}` | CAN SIMPLIFY | 10% adoption; consider surfacing one prompt at a time |
| `photos[]` + min 6 gate | MUST PRESERVE (min may be renegotiated) | 43% meet the current gate; NEEDS DECISION on min count |
| `photo_captions[]` | CAN SIMPLIFY | Optional; inline caption UI is inconsistent |
| `attachments[]` (Track 19.04) | MUST PRESERVE | New, deliberate |
| `distribution_list[]` | MUST PRESERVE | Email routing |
| `prepared_by_signature` | MUST PRESERVE | Legal artifact |
| `superintendent_signature` | CAN REMOVE (schema too — coordinated) | Already removed from UI (DR-FIX-3 R13); keep schema for legacy render only |
| `team_snapshot`, `prepared_by_identity`, `prepared_by_bound` | MUST PRESERVE | Audit backbone |
| `excavation_activity_today` + `linked_excavation_ids[]` | MUST PRESERVE | HARD server gate |
| `submitter_employee_id`, `submitter_email_at_submit`, `submitter_consent_at` | MUST PRESERVE | FSI Tier-1 identity |
| Smart Prefill offer chip | MUST PRESERVE | Track 19.04 P0 fix |
| DraftRestorePrompt / DraftRecoveryNotice / CrewSetupRestorePrompt | MUST PRESERVE | Track 19.04 doctrine |
| Autosave hook `useFormDraft` | MUST PRESERVE | Whole platform depends on it |
| Photo/attachment R2 storage | MUST PRESERVE | Immutable historical evidence |
| 6-photo submit gate | NEEDS DECISION | 43% comply; consider lowering to 3 or enforcing server-side |
| Section collapse state (CollapseCard) | CAN SIMPLIFY | Currently per-section; consider a smart-default expansion pattern based on project type |

## High-level guidance

* **Never remove a persisted schema key.** Every field above marked non-MUST is a UI-layer decision only.
* **The redesign should invest in adoption of production[] and constraints[]** — the two structured fields with 0% adoption represent the biggest untapped operational value.
* **Yes/No progressive disclosure** should replace collapsed-by-default sections for visitors, subcontractors, outbound_materials, and delays — surface a single Yes/No at the top of each and reveal detail only when Yes.
* **Photo minimum needs a business decision** — data shows 57% of reports don't meet 6.
