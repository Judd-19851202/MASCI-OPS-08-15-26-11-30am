# EMPLOYEE ACCOUNTABILITY CONTINUITY MAP
**Audit date:** 2026-05-23
**Purpose:** Trace a single employee's record across every collection that touches them, and verify continuity at each step.

---

## Collections that hold employee-linked data
Sourced from `grep -rEho 'db\.[a-z_]+'` and verified against iter353c aggregation behavior.

| Collection | Linkage method | Aggregated by timeline? |
|---|---|---|
| `employees` | source of truth · `id` | ✅ (header + current_state) |
| `safety_training_records` | `employee_id` OR normalized name+email (iter350 hardened) | ✅ |
| `training_track_records` | `employee_id` | ✅ |
| `safety_documents` | `employee_id` | ⚠️ (linked but UI not surfacing in timeline events — verify) |
| `safety_equipment_issuances` | `employee_id` OR name | ✅ |
| `safety_equipment_trainings` | `employee_id` OR name | ✅ |
| `incidents` | `person_name` (string only — NO `employee_id`) | ⚠️ (timeline aggregates by name match — fragile) |
| `field_leadership_records` | `employee_id` OR name | ✅ |
| `daily_reports` | crew member names embedded | 🔴 NOT aggregated to timeline |
| `equipment_inspections` | `operator_name` string only | 🔴 NOT linked to employees |
| `qaqc_inspections` | typically project-scoped, not employee-scoped | n/a |
| `corrective_actions` | linked via `incident_id` or `linked_employee_id` | ⚠️ |
| `document_expirations` | document-scoped, `linked_employee_id` optional | ⚠️ |
| `notifications` | `linked_employee_id` available but observed empty on QA/QC records | 🔴 |

---

## Continuity findings

### ✅ STRONG continuity (iter353c verified)
- Training → timeline: employee creates training record via Safety OR HR (iter353a); timeline surfaces it with `category="Training"`, role pill on creator, `archived` flag preserved.
- PPE → timeline: every PPE issuance surfaces with `category="PPE & Equipment"`.
- FL records → timeline: write-ups, recognitions, evaluations all surface with role-pill attribution.
- CDL/medical → timeline: virtual events synthesized from `employees.cdl_expiration_date` and `employees.medical_card_expiration_date`. `current_state` tile shows current readiness.
- Lifecycle history → timeline: `employees.status_history[]` surfaces as `HR Lifecycle` events.

### ⚠️ FRAGILE continuity
- **Incidents → employee:** Incidents store `person_name` as a free-text string. NO `employee_id`. Timeline aggregation matches by name. Name typos / nickname variants / married-name changes break the link silently.
- **Documents → timeline:** `safety_documents` are linked by `employee_id` but this audit could not visually confirm they SURFACE on the timeline as discrete events. Verify with a live document upload + timeline read.
- **Document expirations → timeline:** `document_expirations` collection exists but is NOT aggregated into the timeline. An employee with a forklift cert expiring in 14 days does not get a `category="Driver Qualification"` event on their timeline.
- **CAPA → employee:** `corrective_actions.linked_employee_id` is optional and not enforced. Many CAPAs in production likely lack the link.

### 🔴 BROKEN continuity
- **Daily Reports → timeline:** A crew member's name appears on hundreds of daily reports per year. None of this propagates to the accountability timeline. The most data-rich employee-linked surface is invisible to HR's compliance brief.
- **Equipment Inspections → operator employee:** Pre-Op forms capture operator as a string. There is no enforced linkage to the employee master. Equipment failures cannot be aggregated against an operator's accountability record.
- **Notifications → employee:** `linked_employee_id` is a schema field but is NULL on observed QA/QC notifications. Employee-targeted notifications (training expiring, PPE recall) cannot be filtered to "show me everything sent about this employee".

---

## "Where did this go wrong?" trace examples

### Example A — Operator commits a Pre-Op failure
1. Mechanic submits failed Pre-Op → `equipment_inspections` row · `operator_name="Joe Smith"`
2. Shop fan-out email fires → all shop users + SHOP_MANAGER_EMAIL
3. PM scoped list shows the failure → ✅
4. HR accountability timeline for Joe Smith does NOT show this event → 🔴 (no `operator_employee_id` linkage)
5. Compliance brief PDF for Joe Smith would NOT include this → 🔴
6. If Joe Smith later submits 3 more failed Pre-Ops, HR has no aggregate visibility → 🔴

### Example B — Incident on a job
1. Field foreman files incident → `incidents` row · `person_name="Maria Lopez"`
2. Safety reviews, marks severity
3. CAPA created → `corrective_actions` row · `linked_employee_id=NULL` (not enforced)
4. iter353c timeline for Maria Lopez sees the incident (name match) → ✅
5. Timeline does NOT see the CAPA (CAPA→employee link broken) → 🔴
6. PDF Compliance Brief does NOT reference the corrective action follow-through → 🔴

### Example C — Training cert expires
1. Cron job (verify live) detects training expiring 30d → creates `notifications` row?
2. `recipient_role="safety"` → Safety inbox sees it · `recipient_role="pm"` for PM
3. HR inbox: 🔴 (no fan-out)
4. FL inbox: 🔴
5. Employee accountability timeline: ⚠️ — expiration is on the cert record itself, surfaces if Safety/HR re-look at the record
6. Compliance Brief PDF: ✅ Expiration Watch section catches it on read

### Example D — Employee terminated
1. HR updates `lifecycle_status="Terminated"` → `employees` PATCH · `status_history[]` appended
2. iter353b availability tile correctly EXCLUDES the employee (✓)
3. HR Accountability Timeline still lists every past event (✓ — archived/closed state preserved)
4. Daily Report submission tries to add their name → likely silently accepted (no enforcement) → ⚠️
5. PM list: terminated employee shouldn't appear in PM's crew → not verified this audit

---

## Linkage Standard compliance
The `lib/employee_linkage.py` utility (iter350-era) does the heavy lifting for `employee_id` → normalized name + email matching. iter353c demonstrated it works well for the timeline aggregation.

**Where the linkage standard is NOT applied:**
- Pre-Op operator name
- Daily Report crew member names (could enforce employee_id lookup at submit)
- Incident person_name
- CAPA linked_employee_id (optional, not enforced)
- Notification linked_employee_id (optional, not enforced)

Each of these is a place where a real employee's accountability trail goes silent. Fix is consistent: at write time, run `lib.employee_linkage` against the name string, store the resolved `employee_id` alongside the legacy string.
