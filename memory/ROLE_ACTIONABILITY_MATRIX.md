# Role Actionability Matrix · OMEGA Completeness Audit

**Batch:** OMEGA · Operational Completeness Audit · Phase 5
**Mode:** READ-ONLY
**Companion:** `OPERATIONAL_LIFECYCLE_MATRIX.md`
**Date:** 2026-06-01

---

## 1 · Legend

| Symbol | Meaning |
|---|---|
| ✅ | Role can perform the action via UI **and** API |
| 🟦 | API-only (no UI; role has the auth token to call directly) |
| 🟧 | UI-only (UI shows the button but API blocks · or UI exists but the route is missing) |
| ❌ | Action not available to this role |
| n/a | Action does not apply |

Roles: **SA** = Super-Admin · **A** = Admin · **S** = Safety · **HR** = HR · **PM** = PM · **D** = Dispatch · **Sh** = Shop · **FL** = Field-Leadership · **E** = Employee (no portal · publicly submits from QR)

---

## 2 · Selected high-value workflows · per-role actionability

### 2.1 · Incident Report

| Action | SA | A | S | HR | PM | D | Sh | FL | E |
|---|---|---|---|---|---|---|---|---|---|
| Create | ✅ | ✅ | ✅ | ❌ (HR cross-portal read-only) | ✅ | ❌ | ❌ | ✅ | ✅ (public form) |
| View | ✅ | ✅ | ✅ | ✅ | ✅ (scoped) | ❌ | ❌ | ✅ (scoped) | ❌ |
| Mark Under Investigation | ❌ | ❌ | ❌ | ❌ | ❌ | n/a | n/a | n/a | n/a |
| Mark Corrective Action Required | ❌ | ❌ | ❌ | ❌ | ❌ | n/a | n/a | n/a | n/a |
| Mark Pending Closure | ❌ | ❌ | ❌ | ❌ | ❌ | n/a | n/a | n/a | n/a |
| Mark Closed | ❌ | ❌ | ❌ | ❌ | ❌ | n/a | n/a | n/a | n/a |
| Delete | ✅ | ✅ | ❌ (Safety blocked) | ❌ | ❌ | n/a | n/a | n/a | n/a |

**Even Super-Admin cannot close an incident.** Not a permission issue · the endpoint does not exist.

### 2.2 · CAPA (Corrective Action)

| Action | SA | A | S | HR | PM | D | Sh | FL | E |
|---|---|---|---|---|---|---|---|---|---|
| Create | ✅ | ✅ | ✅ | ❌ | ❌ | n/a | n/a | n/a | n/a |
| View | ✅ | ✅ | ✅ | ✅ (read-only mirror) | ✅ (scoped read) | n/a | n/a | n/a | n/a |
| Edit | ✅ | ✅ | ✅ | ❌ | ❌ | n/a | n/a | n/a | n/a |
| Status change | ✅ | ✅ | ✅ | ❌ | ❌ | n/a | n/a | n/a | n/a |
| Link to incident | ✅ | ✅ | ✅ | ❌ | ❌ | n/a | n/a | n/a | n/a |
| Delete | ✅ | ✅ | ✅ | ❌ | ❌ | n/a | n/a | n/a | n/a |

🟢 Aligned — UI + API consistent.

### 2.3 · PO Request

| Action | SA | A | S | HR | PM | D | Sh | FL | E |
|---|---|---|---|---|---|---|---|---|---|
| Submit | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| View | ✅ | ✅ | ❌ | ✅ | ✅ (scoped) | ❌ | ❌ | ✅ (scoped) | ❌ |
| Approve | ✅ | ✅ | ❌ | ✅ | ✅ (own jobs) | ❌ | ❌ | ❌ | ❌ |
| Request clarification | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Respond to clarification | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Upload receipt | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Close | ✅ | ✅ | ❌ | ✅ | ✅ (own jobs) | ❌ | ❌ | ❌ | ❌ |
| Cancel | ✅ | ✅ | ❌ | ✅ | ✅ (own jobs) | ❌ | ❌ | ❌ | ❌ |

🟢 Fully actionable across PM/HR/Admin (the relevant roles).

### 2.4 · Asset Transfers

| Action | SA | A | S | HR | PM | D | Sh | FL | E |
|---|---|---|---|---|---|---|---|---|---|
| Create | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ (iter445) | ❌ |
| View | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ (iter445) | ❌ |
| Approve | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Reject | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Mark In-Transit | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Receive | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ (iter445 visibility) | ❌ |
| Cancel | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Close | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |

🟢 Fully actionable.

### 2.5 · Daily Report

| Action | SA | A | S | HR | PM | D | Sh | FL | E |
|---|---|---|---|---|---|---|---|---|---|
| Create | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ (public) |
| View | ✅ | ✅ | ✅ | ✅ | ✅ (scoped) | ❌ | ❌ | ✅ (scoped) | ❌ |
| Edit (post-submit) | ❌ | ❌ | ❌ | ❌ | ❌ | n/a | n/a | ❌ | ❌ |
| Sign-off / Approve | ❌ | ❌ | ❌ | ❌ | ❌ | n/a | n/a | ❌ | ❌ |
| Delete | ✅ | ✅ | ❌ | ❌ | ❌ | n/a | n/a | ❌ | ❌ |

**No role can edit or approve a Daily Report after submission.** Operationally significant.

### 2.6 · QA/QC Inspection

| Action | SA | A | S | HR | PM | D | Sh | FL | E |
|---|---|---|---|---|---|---|---|---|---|
| Create | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ (public) |
| View | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Mark deficiency resolved | ❌ | ❌ | ❌ | ❌ | ❌ | n/a | n/a | ❌ | ❌ |
| Sign-off | ❌ | ❌ | ❌ | ❌ | ❌ | n/a | n/a | ❌ | ❌ |
| Delete | ✅ | ✅ | ❌ | ❌ | ❌ | n/a | n/a | ❌ | ❌ |

🔴 No follow-up surface for any role.

### 2.7 · Site Safety Inspection

Same pattern as QA/QC — no follow-up surface; Safety / Admin can only create + view + delete.

### 2.8 · Fleet Defects

| Action | SA | A | S | HR | PM | D | Sh | FL | E |
|---|---|---|---|---|---|---|---|---|---|
| Create (from Pre-Op FAIL) | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| Acknowledge | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Mark repaired | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Clear (cleared to operate) | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Mark OOS | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |

🟢 Cross-role state machine well-distributed (Dispatch clears · Shop repairs).

### 2.9 · Tasks

| Action | SA | A | S | HR | PM | D | Sh | FL | E |
|---|---|---|---|---|---|---|---|---|---|
| Create | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | n/a |
| View | ✅ | ✅ | ✅ | ✅ | ✅ (scoped) | ✅ | ✅ | ✅ | n/a |
| Edit | ✅ | ✅ | ✅ | ✅ | ✅ (own) | ✅ | ✅ | ✅ | n/a |
| Status change | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | n/a |
| Reassign | ❌ (no dedicated route — patch only) | same | same | same | same | same | same | same | n/a |
| Close | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | n/a |
| Comment | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | n/a |
| Delete | ❌ (no delete route) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | n/a |

🟡 Cross-role available; reassign via patch only; no delete.

---

## 3 · Cross-cutting role observations

### 3.1 · HR is read-only across safety domain (by intent · documented in prior audits)

* HR cannot edit incidents, CAPAs, JHAs, meetings, FL forms.
* HR can edit employees, time-off, payroll-variance decisions, training records.
* This split is intentional ("HR owns OSHA recordkeeping — Safety closes incidents") but combined with the absence of an incident close action, **no role can close an incident.**

### 3.2 · Field Leadership has the narrowest surface

* FL can create FL Forms, view scoped records, view JHA (iter445), view Asset Transfers (iter445).
* FL cannot transition anything they themselves filed.
* FL forms are operationally one-way.

### 3.3 · Dispatch has dual surfaces

* `/dispatch-portal` (per-user) and `/admin/dispatch` (admin-impersonate-or-master) both exist.
* Dispatchers see "which one should I use?" friction (documented in `REAL_USER_DISCOVERABILITY_AUDIT.md`).
* Both surfaces call the same API.

### 3.4 · Shop has full Pre-Op signoff authority but cannot close incidents that reference its equipment

* Shop signoff closes the equipment defect.
* If the same Pre-Op generated an incident, the incident remains "open" forever.

### 3.5 · Public submitters (Employee / QR users) have no auth

* They can submit Daily Reports, Incident Reports, Inspections, Meetings, JHAs, Equipment Inspections.
* They cannot view their own submissions afterward.
* There is no "submission receipt" UI tied to a verifiable identifier.

---

## 4 · 🟧 UI-visible buttons that should be hidden (or backend should be added)

| Page | Visible button | Backend reality |
|---|---|---|
| `SafetyIncidents.jsx` (HR view) | Delete row (🗑️) | Backend returns 403 for HR token (`safety.py:822`) · UI does not pre-check role |
| `ViewIncident.jsx` lifecycle block | "Reported → Linked CAPA(s) → Verified → Closed. Closing without a verified CAPA is blocked." | Pure copy · no closure button anywhere |
| Admin `AdminEmployees` | "Email Welcome" on Field-Leadership Users panel | Backend route exists; UI sometimes hides under role mismatch |

(Other UI-vs-backend gaps documented per-workflow in `OPERATIONAL_LIFECYCLE_MATRIX.md`.)

---

## 5 · 🟦 API-only actions (no UI)

| Action | Endpoint | Role | Why API-only |
|---|---|---|---|
| Re-key admin token (epoch bump) | env var change + supervisor restart | Admin | Not a runtime action |
| Force-reseed crews | `POST /admin/crew-recovery/force-reseed` | Admin | Disaster recovery; intentionally hidden |
| Restore from backup | `POST /admin/recovery/restore` | Admin | Behind confirmation dialogs; multi-step |
| `POST /admin/job-photos/reindex` | rare maintenance | Admin | Not a recurring action |
| `POST /admin/job-photos/warm-cache` | preview tool | Admin | Not surfaced |
| `POST /admin/po-digest/scan-missing-receipts` | scheduler-only | Admin | No UI button |
| Operator digest manual fire | (config-driven only) | Admin | No UI |

These are intentional (low-frequency operations) — not gaps.

---

## 6 · 🟧 UI-says-allowed but API blocks

| Surface | UI promise | API reality |
|---|---|---|
| `SafetyIncidents.jsx` status filter | Filter by Open/Investigating/Closed | API list strips status; every row reads as "Open" |
| `HrIncidents.jsx` row actions | Some legacy delete UI | Backend returns 403 for HR |
| `ProjectHealth.jsx` "Unresolved high/critical" count | Number reflects "resolution_status != Closed" | DB has no producer for "Closed" → number includes every incident in production |

---

## 7 · Action-availability summary per role

| Role | Workflows where they can create | …can transition | …can close | …can audit |
|---|---|---|---|---|
| Super-Admin | all | most (limited by what exists) | most (limited by what exists) | most |
| Admin | all in admin scope | most | most | most |
| Safety | safety domain | CAPA + Fire Ext + Docs + Training Records | CAPA + Docs + Training | few |
| HR | employee + payroll + training (read) + time-off + FL forms (read) | employee + time-off + payroll-variance decisions | none in safety | few |
| PM | PO + Job + DR + QA/QC + Asset Transfers + scoped | PO + Asset Transfers + Job · scoped | PO + Asset Transfers | few |
| Dispatch | dispatch board + fleet defects clear + asset transfers + ops events | dispatch assignments + fleet defects + ops events | dispatch + ops holds release | few |
| Shop | Pre-Op signoff + fleet defects repair | fleet defects + equipment inspections | equipment inspections (signoff) | few |
| Field Leadership | FL forms + scoped DR + Pre-Op + safety forms + PO request | none (one-way submission) | none | none |
| Employee | public submits only | none | none | none |

---

## 8 · OMEGA discipline

🟢 Read-only · per-role permission inventory cross-referenced with route guards. No new actions proposed.

🛑 Continue to `CLOSURE_PATH_AUDIT.md`.
