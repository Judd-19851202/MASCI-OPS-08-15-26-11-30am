# Pillar 1 · Accountability Engine · Architecture Audit

**Batch:** Pillar 1 · Accountability Engine · Design only
**Date:** 2026-05-31
**Scope:** Inventory every workflow on the MASCI Hub that produces an actionable operational item, then map the *current* ownership and accountability fields per workflow. Identify ambiguity, inconsistency, and absence.
**Discipline:** OMEGA · evidence-only · no code change · no new collections proposed in this report.

---

## 1 · Executive summary

The platform already ships a **unified Task & Notification engine** (`/app/backend/routes/tasks_notifications.py`, iter150 Phase E) that defines the canonical accountability shape: `assignee_role · assignee_user_id · assignee_employee_id · priority · status · due_at · created_by · audit[]`. Seven workflows already emit tasks through `task_service.create()`. The remaining workflows surface in the Executive Command Center either by **borrowing the source record's native fields** (which are inconsistent across collections) or by **hardcoding the owner string** at read time (e.g. Command Center always labels Safety items "Safety", regardless of who actually owns the row).

This audit catalogs:

- 7 workflows that already participate in the unified engine (✅).
- 6 workflows that surface in the Command Center but do **not** participate (🟡).
- 4 workflows with their own private status-history / audit array that does not conform to the canonical `tasks.audit` shape (🟡).
- 3 collections that have **no assignee field at all** (🔴 — most critical: `incidents`, `fleet_defects.assignee_*`, `daily_reports` lifecycle).

The architecture deliverable that follows this audit (`ACCOUNTABILITY_ENGINE_ARCHITECTURE.md`) proposes a **superset model** that subsumes the unified engine as-is (zero break) and provides a uniform projection of ownership onto every workflow that surfaces in executive visibility.

---

## 2 · Inventory · workflows that produce actionable operational items

Each row below is anchored to live code. Line references are current as of source_hash `54b8a402de538a17579cabc2e6aaac38` (production-deployed Path B build).

| # | Workflow | Collection(s) | Native owner fields | Native lifecycle | Native timeline | Participates in unified engine? | Surfaces in Executive Command Center? |
|---|---|---|---|---|---|---|---|
| W-01 | **Unified Tasks** (system-of-record) | `db.tasks` (tasks_notifications.py:74-200) | `assignee_role`, `assignee_user_id`, `assignee_employee_id`, `created_by{role,name}` | `ALLOWED_STATUS = {Open, In Progress, Pending Review, Completed, Closed, Cancelled, Overdue}` (line 74) | `audit[]` push-only with `{at,by,action,changes}` (line 178-182, 235-240) | ✅ canonical | ✅ Accountability card |
| W-02 | **Notifications** (delivery feed) | `db.notifications` | `recipient_role`, `recipient_user_id` (line 298-299) | `read_at`, `acknowledged_at` (line 312) | per-record only | ✅ canonical | indirectly via tasks linkage |
| W-03 | **Safety Corrective Actions** | `db.corrective_actions` (safety_portal/corrective_actions.py:48-72) | `assigned_to_name`, `assigned_to_email`, `created_by_name`, `created_by_email` | `Open → In Progress → Pending Review → Verified → Closed` (line 128-136) | `status_history[]` push-only (line 209-221) | ✅ emits `task_service.create(source_module="safety.corrective_actions")` (line 88-103) | ✅ Safety card (SAF-CA-OVERDUE, SAF-CA-CHRONIC) + Jobs card (JOBS-ISSUE-NO-OWNER, JOBS-ISSUE-NO-PATH) |
| W-04 | **PO Requests** (approvals) | `db.po_requests` (po_requests.py:540-552, 590-629) | `requested_by_role`, `requested_by_user_id`, `requested_by_employee_id`, `requested_by_name`; approvers via `approved_by` / `rejected_by` audit entries | `Submitted → Pending Approval → (Clarification Needed)* → Approved/Rejected → Pending Receipt → Closed/Cancelled` (line 540, 599, 611, 706, 849, 879) | `audit[]` push-only via `_audit_push()` helper (line 175-185) | ✅ emits `task_service.create(source_module="po.requests")` (line 220-230) | ✅ Approvals card (APP-AMBER, APP-RED, APP-WEEK) |
| W-05 | **Document Expirations** | `db.document_expirations` (document_expirations.py:232) | inherited from underlying document; tasks bear the role | per-document | per-document | ✅ emits `task_service.create()` | not currently — domain-specific dashboard |
| W-06 | **Employee Lifecycle** | `db.employee_lifecycle` (employee_lifecycle.py:713, 898, 1098, 1192, 1793) | linked to `employee_id`; HR or Admin actors | `status_history[]` per-record (line 898) | `status_history[]` push-only — **own schema, not `audit`** | ✅ emits `task_service.create()` for onboarding/offboarding | not currently |
| W-07 | **Training Center** (Phase E) | indirect | tasks bear safety role | per-record | per-record | ✅ documented in training_center.py:340 | not currently |
| W-08 | **Safety Incidents** | `db.incidents` | 🔴 **NONE** — no `assignee_role`, no `assigned_to_*`. Owner is *implicit*: linked corrective_action assignee, or hardcoded "Safety" string in command_center.py:478,532 | `severity`, `osha_recordable`, `corrected_on_site`, plus optional `status` (free-form per data) | none on the incident row itself (the linked CA carries its own history) | 🟡 partial — only via linked CA (D1/D2 patch traces this) | ✅ Safety card (SAF-CRITICAL-UNRESOLVED, SAF-OSHA-OPEN); Jobs card (JOBS-ISSUE-NO-PATH) |
| W-09 | **Fleet Defects** (DVIR / Shop) | `db.fleet_defects` (fleet_ops.py:166-174, 810-895) | `acknowledged_by_name` (string only, no `role` / `user_id`); reporter name in `reported_by_name` | `open → acknowledged → repaired → cleared` (line 167, 810, 847, 895) | inline mutation + `acknowledged_at` / `repaired_at` timestamps | 🔴 **NO** — does not emit a unified task on creation | ✅ Equipment card (EQP-OOS-OLD, EQP-OOS-NEW, EQP-BACKLOG) |
| W-10 | **Jobs (Daily-Report missing)** | derived from `db.jobs_master` × `db.daily_reports` (command_center.py:300-346) | `primary_pm_email`, `primary_pm_name` from `jobs_master` row | not a lifecycle — it's an absence pattern | none | 🔴 **NO** — virtual signal; no row, no task | ✅ Jobs card (JOBS-DR-MISSING) |
| W-11 | **Daily Reports** | `db.daily_reports` | `created_by` (free-form), `submitted_by_name` | submission only — no review/approval lifecycle | none | 🔴 **NO** | not directly — surfaces by absence in Jobs card |
| W-12 | **Inspections / JHAs / Meetings** | `db.inspections`, `db.jhas`, `db.meetings` | `created_by_name`, `signatories[]` (per-record schemas vary) | none beyond signature capture | none beyond signature timestamps | 🔴 **NO** | not directly |
| W-13 | **Dispatch holds / Lifecycle** | `db.dispatch_holds`, `db.dispatch_lifecycle` (dispatch_lifecycle.py) | per-record dispatcher actor | own statuses (active/cleared) | inline | 🔴 **NO** | not currently in Command Center |
| W-14 | **Asset Transfers** | `db.asset_transfers` | per-transfer initiator + receiver | own statuses | own audit array | 🔴 **NO** | not currently in Command Center |
| W-15 | **Master Data Updates** (admin) | `db.admin_audit` (line 1019-1027 in command_center.py) | actor captured in audit entry | n/a | append-only `admin_audit` | 🔴 **NO** — pure audit log, not an action | n/a |

---

## 3 · Ownership ambiguity register

| ID | Where | Today's behavior | Operator-facing question that cannot be answered fast | Severity |
|---|---|---|---|---|
| A-01 | **`db.incidents` has no assignee** | command_center.py:478,532 hardcodes `owner="Safety"` for every SAF-* card item, regardless of who is actually accountable for *this* incident. | "Who owns incident DR-2026-0142?" → must open the incident, infer from project PM + safety lead + any linked CA. | 🔴 HIGH |
| A-02 | **`db.fleet_defects` has no `assignee_role`/`assignee_user_id`** | fleet_ops.py:166-174 records `acknowledged_by_name` (string); command_center.py:660 hardcodes `owner="Shop"`. | "Who is actually working on Unit 412 OOS?" → must open the row and read free-text. No system answer. | 🔴 HIGH |
| A-03 | **`db.jobs_master.primary_pm_*` is read-only** | command_center.py:328 reads `primary_pm_name` as the owner for JOBS-DR-MISSING. No lifecycle — PM is not "assigned" to the missing report; they own the *job*. | "Has PM Chris seen the JOBS-DR-MISSING alert for project 24-15?" → cannot answer; no read receipt. | 🟡 MEDIUM |
| A-04 | **CA `assigned_to_name` is a string, not a foreign key** | safety_portal/corrective_actions.py:55-56 stores name + email — no `user_id` / `employee_id`. | "Reassign every open CA owned by 'J. Smith' (now departed)" → free-text match, fragile. | 🟡 MEDIUM |
| A-05 | **PO approver identity computed per-request** | po_requests.py:590 — approver role only resolved at the moment of decision; the *current pending approver* of an aged PO is implicit. | "Which approver is sitting on PO 26-0042?" → must trace approval routing rules; not a single read. | 🟡 MEDIUM |
| A-06 | **`tasks.assignee_user_id` is optional** | tasks_notifications.py:167-169 — many tasks are role-only (e.g. `safety`). Two safety users get the bell; neither is *the* owner. | "Who is the *individual* owner of CA-2026-0042?" → role-only fan-out means the answer is "anyone with the role". | 🟡 MEDIUM |
| A-07 | **No standard "viewed" event** | tasks audit captures `created/updated` only; corrective_actions, po_requests don't capture viewer at all. | "Has the assignee opened this since assignment?" → cannot answer. | 🟡 MEDIUM |
| A-08 | **Closure attribution inconsistent** | tasks: `audit[]` last entry; CA: `closed_by_name` field; PO: `closed` action in `audit[]`; fleet_defects: `repaired_by` / `cleared_by` (when present). | "Who closed this and when?" → answer lives in 4 different shapes. | 🟡 MEDIUM |
| A-09 | **Status enums diverge** | tasks: `{Open, In Progress, Pending Review, Completed, Closed, Cancelled, Overdue}`; CA: `{Open, In Progress, Pending Review, Verified, Closed}`; fleet_defects: `{open, acknowledged, repaired, cleared}`; po_requests: `{Submitted, Pending Approval, Clarification Needed, Approved, Rejected, Pending Receipt, Closed, Cancelled, Overdue Receipt}`. | "Is this item 'in progress'?" → meaning differs per collection. | 🟡 MEDIUM (intentional · domain-correct · noted not fought) |
| A-10 | **`db.daily_reports.created_by` is free-form** | daily_reports.py — no role/user_id reference; submitter is "name plus optional title". | "Who is accountable for the missing DR?" → falls back to PM by job linkage. | 🟢 LOW (DRs are records, not actions — Jobs card handles the absence at the job level) |

---

## 4 · Timeline / history schema divergence register

| Where | Schema | Push pattern | Captures |
|---|---|---|---|
| `db.tasks.audit[]` | `{at, by:{role,name}, action, changes:{from,to}}` | `$push` on every update | Author, action, field-level diff |
| `db.corrective_actions.status_history[]` | `{at, by, from_status, to_status, note}` (line 209-221) | `$push` on status changes only | Status transition · note · actor |
| `db.po_requests.audit[]` | `{at, action, actor, note, fields?}` via `_audit_push` (line 175-185) | `$push` per action | Workflow events (approved/rejected/clarification/closed/cancelled) |
| `db.employee_lifecycle.status_history[]` (line 898) | own shape — per-record | `$push` on lifecycle events | Hire/terminate/reactivate events |
| `db.admin_audit` | one row per event | `insert` | Cross-system admin events (login, directory mutation, threshold update — including command_center.thresholds.update) |
| `db.fleet_defects` (inline fields) | `acknowledged_at`, `repaired_at`, `cleared_at` + `*_by_name` | inline `update_one` | Workflow state changes; no event log |

Five collection-local audit shapes today. The Architecture deliverable proposes how to project these into a single readable timeline without forcing a schema migration on existing rows.

---

## 5 · Executive Command Center · current owner column source map

The Command Center already presents an `owner` for every surfaced item. This audit traces where that string comes from:

| Card · Rule | Owner string source | Quality |
|---|---|---|
| Jobs · JOBS-DR-MISSING | `job.primary_pm_name` ∥ `job.primary_pm_email` ∥ "Unassigned PM" (command_center.py:328) | 🟡 derived from job, not assigned |
| Jobs · JOBS-ISSUE-NO-OWNER | hardcoded "UNASSIGNED" (line 371) | 🟢 truthful by definition |
| Jobs · JOBS-ISSUE-NO-PATH | hardcoded "Safety" (line 406) | 🔴 hardcoded |
| Safety · SAF-CRITICAL-UNRESOLVED | hardcoded "Safety" (line 478) | 🔴 hardcoded |
| Safety · SAF-OSHA-OPEN | hardcoded "Safety" (line 532) | 🔴 hardcoded |
| Safety · SAF-CA-OVERDUE | `ca.assigned_to_name` ∥ "Unassigned" (line 568) | 🟢 real per-row |
| Equipment · EQP-OOS-OLD | hardcoded "Shop" (line 660) | 🔴 hardcoded |
| Accountability · ACC-* | `task.assignee_role` capitalized (line 764) | 🟡 role-only |
| Approvals · APP-* | `po.requested_by_name` (line 874) — *requester, not approver* | 🔴 wrong attribute (operator may misread) |

5 of 9 owner strings are hardcoded or attribute-mismatched. This is the single largest gap between Pillar 2 (Executive Visibility) and Pillar 1 (Accountability).

---

## 6 · Risks of leaving the audit unaddressed

| # | Risk | Likelihood | Severity |
|---|---|---|---|
| R-1 | Executive sees "Safety" but no Safety user knows it is theirs personally → silent un-ownership | HIGH | HIGH |
| R-2 | Approvals card labels the *requester* as the owner; the actual approver is invisible | HIGH | HIGH |
| R-3 | A departed employee's name remains in `assigned_to_name` for months because there is no `user_id` foreign key to invalidate | MEDIUM | MEDIUM |
| R-4 | Multiple history shapes prevent a single "What's happened on this item?" view in the executive drilldown | HIGH | MEDIUM |
| R-5 | Re-assignment of an in-flight item is workflow-specific; some collections allow it, some don't | MEDIUM | MEDIUM |
| R-6 | "Has the owner seen it?" cannot be answered — no `viewed_at` or read-receipt anywhere outside `notifications` | HIGH | MEDIUM |

These risks are exactly the gap between **"the system can see the problem"** (Phase A, shipped) and **"the system can answer who owns the problem and what they have done"** (Pillar 1, this design batch).

---

## 7 · What the audit does NOT do

- ❌ Propose any new collection (architecture deliverable will).
- ❌ Propose any new endpoint (architecture deliverable will).
- ❌ Propose any UI change (dashboard deliverable will).
- ❌ Propose escalation rules — explicitly out of this batch per directive.
- ❌ Propose notifications, emails, SMS, or cron — explicitly out of this batch per directive.
- ❌ Touch backup, recovery, scheduler, storage, R2, drill framework, Command Center Phase A.

---

## 8 · Audit conclusion

The platform already has the structural seed of an Accountability Engine in `tasks_notifications.py`. The work is **not to invent a new model from scratch**; the work is to:

1. Promote that model to a first-class platform contract (Architecture deliverable).
2. Project every actionable item — incident, fleet defect, missing daily report, aged PO — through the same lens (Lifecycle + Timeline deliverables).
3. Fix the 5 of 9 hardcoded owner strings in Command Center so the executive answer to "Who owns this?" comes from data, not from a literal string in a Python file (Executive Integration deliverable).
4. Phase the work so it remains reversible, OMEGA-disciplined, and free of scope creep into Escalation / Notifications / Pillar 3 / Pillar 4 (Roadmap deliverable).

This is a SPECIFICATION batch only. No code follows.
