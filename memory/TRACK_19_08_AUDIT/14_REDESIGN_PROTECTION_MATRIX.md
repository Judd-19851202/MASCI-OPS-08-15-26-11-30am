# TRACK 19.08 · Redesign Protection Matrix

Every field / behaviour / surface classified. **Preserve, Can-Modify, or Needs-Decision.** Every classification carries its justification.

Legend:
* **P** — MUST PRESERVE (unchanged in redesign)
* **P-OP** — Operational Critical
* **P-LEGAL** — Legal Critical (OSHA · DOT · state)
* **P-PAYROLL** — Payroll Critical
* **P-FLEET** — Fleet-management critical
* **P-BE** — Backend Critical (schema / route / contract)
* **M** — Can Merge with sibling
* **S** — Can Simplify
* **H** — Can Hide (still readable, not surfaced by default)
* **R** — Can Reorder
* **D** — Needs Product Decision
* **?** — Unknown; audit further before redesign

---

## 1 · Daily Report (already redesigned in 19.06/19.07)

All fields locked by 59-assertion Track 19.05 audit + 44-assertion Track 19.06 test + 23-assertion Track 19.07 test + 21-assertion Track 19.06 Amendment test. **P-BE.**

---

## 2 · Equipment Pre-Op

| Field | Class | Justification |
| --- | --- | --- |
| `unit_number` / `asset_id` | P-OP + P-BE | Anchors the record to a specific asset; downstream fleet-status / defect linkage requires it |
| `equipment_type` | P-OP | Drives template load |
| `operator_name` / `operator_employee_id` | P-LEGAL | Accountability trail per shift |
| `project_number` / `project_name` | P-OP | Project scoping for reports/exports |
| `location` | P-LEGAL | Location of inspection is auditable |
| `inspection_date` / `shift_start` / `shift_end` | P-LEGAL | Time-in-service window |
| `sections[]` (each item's status / notes / photos) | P-OP + P-LEGAL | The inspection artifact itself — MUST PRESERVE |
| `overall_status` (derived) | P-OP | Server re-derives; client display is calc |
| `defects[]` (snapshot on submit) | P-OP + P-FLEET | Downstream fleet_defects records |
| `photos[]` | P-LEGAL | Evidence per item |
| `operator_signature` | P-LEGAL | Signer identity |
| `submitted_at` / `pdf_url` / `email_dispatched_at` | P-BE | Audit-trail primitives |
| **Coaching-panel stack (3 systems)** | S | Redundancy — can collapse into a single help drawer |
| **Flat section layout** | R (add progressive disclosure) | Reuse Track 19.06 `PresenceGate` pattern |
| **Manual asset selection** | D | QR-scan asset-binding is a P2 opportunity — product decision |

---

## 3 · DVIR

| Field | Class | Justification |
| --- | --- | --- |
| `unit_number` | P-OP + P-FLEET + P-DOT | Federal DVIR requirement |
| `dvir_type` | P-DOT | Distinguishes pre-trip / post-trip / weekly (DOT §396.11) |
| `driver_name` / `driver_employee_id` | P-DOT + P-LEGAL | Driver identity per DVIR |
| `odometer` | P-DOT | Federal requirement |
| `inspection_date` / `inspection_time` | P-DOT | Federal requirement |
| `sections[]` items | P-DOT + P-FLEET | DOT §392 & §393 checklist |
| `overall_status` (safe / unsafe) | P-DOT | Federal disposition |
| `defects[]` | P-FLEET + P-DOT | Federal requirement + downstream shop workflow |
| `driver_signature` | P-DOT + P-LEGAL | Federal requirement |
| `mechanic_signature` | P-DOT (when defects) | §396.11(a)(2) — required when repairs completed |
| `photos[]` | P-OP | Not federally required; retained for MASCI investigation quality |
| `oos_applied_at` / `oos_cleared_at` | P-FLEET | Shop-lifecycle timestamps |
| **Section layout (flat)** | R | Same as Equipment Pre-Op |
| **Photo required at defect** | D | Industry standard — recommend requiring; needs product decision |

---

## 4 · Safety Meeting

| Field | Class | Justification |
| --- | --- | --- |
| `meeting_type` enum | P-OP + P-BE | Downstream analytics depend on categorization |
| Legacy `tailgate` value | P (read tolerance) | Historical records use it |
| `topic` / `topics_covered` | P-LEGAL | OSHA §1926.20 training documentation |
| `attendees[]` (name + employee_id + signature) | P-LEGAL | OSHA §1926.21(b)(2) — training records |
| `presenter_name` / `presenter_employee_id` | P-LEGAL | Trainer identity |
| `meeting_date` / `meeting_duration_minutes` | P-LEGAL | Training duration for OSHA docs |
| `photos[]` | P-OP | Evidence |
| `presenter_signature` | P-LEGAL | Sign-off |
| **`topics_covered` + `key_takeaways`** | M | Merge into a single "discussed and decided" field (see 12_UX_FRICTION §B) |
| **Per-attendee knowledge-check** | D + (new field) | Product decision; would strengthen operational value |
| **Batch attendee sign** | S | UI simplification; no schema change |

---

## 5 · Incident

| Field | Class | Justification |
| --- | --- | --- |
| `incident_type` enum | P-LEGAL + P-BE | OSHA classification |
| `severity` enum | P-OP | Notification routing depends on this |
| `incident_date` / `incident_time` | P-LEGAL | Timeline evidence |
| `discovered_by` / `reported_by` | P-LEGAL | First-observer / reporter identity |
| `project_number` / `location` / GPS | P-LEGAL | Location evidence |
| `people_involved[]` / `injuries[]` | P-LEGAL + P-OSHA | Injured party details |
| `equipment_involved[]` | P-OP | Root-cause forensics |
| `witnesses[]` | P-LEGAL | Legal evidence |
| `description` / `immediate_actions` | P-LEGAL | OSHA §1904 recordkeeping |
| `root_cause_notes` | P-OP | Investigation quality |
| `photos[]` | P-LEGAL + P-OP | Evidence |
| `reporter_signature` / `supervisor_signature` | P-LEGAL | Sign-off |
| `lifecycle_state` | P-OP | Workflow |
| `corrective_action_ids[]` | P-OP + P-LEGAL | Closes the loop |
| `osha_recordable` / `osha_form_300_number` | P-OSHA | Federal recordkeeping |
| Legacy `injury_reported` / `accident_reported` booleans | P (read tolerance) | Historical records use them |
| **11 sections all always visible** | R + progressive disclosure | Redesign opportunity |

---

## 6 · JHA

| Field | Class | Justification |
| --- | --- | --- |
| `jha_template_id` | P-OP | Template identity |
| Template `hazards[]` / `mitigation` / `residual_risk` | P-LEGAL | Hazard analysis artifact |
| `signatures[]` per attendee | P-LEGAL | Training evidence |
| Acknowledgement records (separate collection) | P-LEGAL | Immutable per-revision proof-of-training |
| **`inspections.subtype=jha` legacy path** | P (read) + S (write) | New writes to `jhas`; legacy read tolerance |

---

## 7 · Shared primitives

| Primitive | Class | Justification |
| --- | --- | --- |
| Actor-scoped draft store (Track 19.04) | P-BE + P-OP | Prevents cross-crew draft bleed |
| Unified attachment pipeline (Track 19.04) | P-BE | Single R2 path for PDF/XLSX/XLS/CSV |
| HR canonical roster (`/hr/employee-roster`) (Track 19.03) | P-OP + P-HR | Single-source-of-truth for identity |
| Smart Prefill (Track 15.46 · 19.04 · 19.06 amendment) | P-OP | Productivity accelerator; hours-restore is amendment |
| PresenceGate progressive disclosure (Track 19.06) | R (extend) | Reuse across Equipment/DVIR/Incident |
| Trust-Spine correlation ids | P-BE + P-LEGAL | Auditor traceability |
| Excavation hard-gate | P-LEGAL | OSHA trench-safety requirement |

---

## 8 · Route protections

Backend routes and their status:
* All routes listed in `02_MASTER_ROUTE_INVENTORY.md` are **P-BE**.
* `DELETE /daily-reports/{id}` returns 410 — **P-BE** (historical immutability).
* Legacy `/api/admin/login` returns 410 — **P** (retired, must not return).
* Route aliases (submit / new) — **P** (live compat).

---

## 9 · Aggregate protection posture

| Category | Count | Class |
| --- | ---: | --- |
| Federal-DOT required fields | 12 | P-DOT |
| OSHA-required fields | 26 | P-LEGAL |
| Payroll-critical fields | 8 | P-PAYROLL |
| Fleet-management-critical | 15 | P-FLEET |
| Schema-lock fields (Track 19.05) | 47 | P-BE |
| Route-lock endpoints (Track 19.08) | 846 | P-BE |
| Total MUST-PRESERVE | **~154** | — |
| Total CAN-SIMPLIFY (UI-only) | ~22 | S |
| Total CAN-REORDER (add progressive disclosure) | ~10 | R |
| Needs product decision | ~8 | D |

**No schema change is permitted in any redesign track without explicitly bumping a lock test.**
