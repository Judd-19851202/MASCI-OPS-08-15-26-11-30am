# Schedule Constraint Model
## Phase V.0 · Architecture & Governance · 2026-05-27

> Operational constraint model — the bridge between RFIs and schedule
> activities. Distinct from P6's native logic constraints.
> Doctrine-locked.

---

## 1 · What is a Constraint (in MASCI doctrine)

A **constraint** in MASCI Ops is an **operational reason** that
forward progress on a scheduled activity is at risk or blocked.

It is **not**:

- A P6 logical relationship (SS, FS, FF, SF). Those live in P6.
- A P6 date constraint ("Start no earlier than"). Those live in P6.
- A general "to-do". Tasks have their own home in `/tasks`.

It **is**:

- A first-class object that links a real-world condition (an RFI, a
  utility conflict, a survey error, a closure window) to one or more
  schedule activities.
- The operational unit of risk tracking.
- The bridge between RFI workflows and schedule intelligence.

---

## 2 · Constraint Types

| Type | When |
|---|---|
| `rfi_pending` | An RFI is open and its resolution is required before an activity can proceed |
| `cei_hold` | CEI placed a written hold on work |
| `engineer_response_pending` | Engineer of Record owes a response (different from a formal RFI) |
| `utility_conflict` | Field conflict with utility infrastructure |
| `survey_control` | Survey / control point issue blocking layout |
| `material_lead` | Material lead time slipped against need-by |
| `mot_restriction` | MOT phasing prevents work in this window |
| `faa_closure_window` | Required airfield closure window unavailable |
| `qc_test_failure` | Material or workmanship QC test failed; rework required |
| `weather_hold` | Weather event prevents work (with documented threshold) |
| `subcontractor_delay` | Subcontractor not on schedule |
| `owner_decision_pending` | Owner has not yet made a binding decision |
| `access_restriction` | Site access blocked (third party, easement, neighbor) |
| `safety_hold` | Safety placed an active stop-work |

This list is **doctrine-locked**. New types require a doctrine
revision and a corresponding terminology entry.

---

## 3 · Constraint Statuses

| Status | Meaning |
|---|---|
| `proposed` | Superintendent or PM raised it; not yet confirmed by PM |
| `active` | PM confirmed it; affecting schedule |
| `resolved` | Resolution captured; constraint closed |
| `voided` | Raised in error; preserved for audit |

A constraint can move `proposed → active → resolved` only forward.
`voided` is a terminal off-ramp from `proposed` or `active` with a
documented reason.

---

## 4 · Constraint Record (collection: `rfi_constraints`)

| Field | Type | Notes |
|---|---|---|
| `constraint_id` | uuid | |
| `project_number` | str | indexed |
| `type` | enum | one of § 2 |
| `status` | enum | one of § 3 |
| `linked_activity_ids` | list | references stable P6 `task_id` values |
| `linked_rfi_id` | uuid · nullable | when an RFI drives the constraint |
| `linked_daily_report_ids` | list | optional · evidence chain |
| `linked_photo_ids` | list | optional · evidence chain |
| `linked_inspection_ids` | list | optional · QC / safety evidence |
| `linked_incident_ids` | list | optional · safety evidence |
| `responsible_party` | enum | `pm`, `cei`, `engineer`, `owner`, `utility`, `dot`, `faa`, `safety`, `subcontractor`, `internal` |
| `needed_by_date` | date | when resolution is needed to avoid impact |
| `impact_type` | enum | `none`, `delay`, `cost`, `safety`, `compliance`, `multiple` |
| `impact_assessment` | str | operator-written |
| `resolution_summary` | str · nullable | filled when resolved |
| `resolved_at` | ts · nullable | |
| `resolved_by` | user_id · nullable | |
| `void_reason` | str · nullable | required when voided |
| `created_by` | user_id | |
| `created_at` | ts | |
| `last_updated_at` | ts | |
| `audit_log` | embedded · append-only | state-change history |

---

## 5 · Constraint × Activity Linkage Rules

- A constraint can be linked to **one or more activities** in the
  current active schedule revision.
- Links use **stable P6 `task_id`** values, not array positions.
- When a new schedule revision activates, the system attempts to
  rebind each link to the new revision's matching `task_id`. If the
  activity was removed, the constraint surfaces an **orphaned-link
  warning** in the operational-impact view.
- Orphaned links do not automatically resolve the constraint. The PM
  decides explicitly.

---

## 6 · Constraint × RFI Linkage Rules

When an RFI is created and PM (or Superintendent) marks **"impacts
schedule"**:

1. The system **proposes** a `rfi_pending` constraint draft.
2. PM confirms it (`proposed → active`) when submitting the RFI.
3. The constraint's `linked_rfi_id` is set.
4. The RFI's `linked_constraint_ids` carries the back-reference.
5. When the RFI moves to `accepted` or `closed`, the system **proposes
   resolution** of the linked constraint. PM confirms.

Note: not every RFI creates a constraint. Only RFIs the PM explicitly
flags as schedule-impacting do. This prevents alert fatigue.

---

## 7 · Visual Doctrine for Constraints

In the schedule UI, constraints render as:

- A **slate badge** with the type label next to the affected activity row.
- A **red dot** prefix on the badge **only** if the constraint impacts a
  critical-path activity AND is overdue against `needed_by_date`.
- A small popover on tap/click with: type · linked RFI (if any) ·
  needed-by · status · resolution path.

No persistent red banners. No flashing. No animation. The single red
dot is the entire visual escalation vocabulary for the schedule view.

---

## 8 · Reporting Surfaces

Constraints feed:

- The **Operational Impact View** in the schedule subsystem.
- The **PM Dashboard** chip (count of `active` constraints with
  critical-path linkage).
- The **Governance Health Chip** (constraint drift counts as
  operational signal).
- The **RFI Center** (RFIs with linked constraints flagged).
- The **Executive read-only view** (high-exposure aging constraints).

---

## 9 · Notification Discipline

| Constraint event | Notify |
|---|---|
| `proposed` | PM (in-app) |
| `active` (newly active) | PM (in-app · digest only) |
| `active + critical-path linked` | PM (in-app + email) · Executive (in-app · digest) |
| `overdue against needed_by_date` | PM (in-app + email) |
| `resolved` | Superintendent (in-app) |
| `voided` | Admin (in-app) |

No notifications for routine creation, attachment uploads, or
read-only opens.

---

## 10 · Constraint Sunset Rules

- Resolved constraints remain queryable indefinitely.
- Voided constraints remain queryable indefinitely.
- No automatic delete. Ever.
- Resolved constraints fall **out** of operational-impact views after
  30 days unless explicitly pinned (audit reasons).

---

## 11 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Constraint collection + indexes land in V.5 (RFI ↔ Schedule linkage phase).
