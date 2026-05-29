# Workflow Ownership Matrix

_Phase V.5 · P0 Platform Trust Restoration · 2026-05-29 20:38 UTC._

> For every workflow: creator · owner · viewers · editors · delete authority ·
> next-step authority. Read-only audit, no fixes.

## 1 · Schema

| Column | Meaning |
|---|---|
| **Creator** | Persona that initiates the record (often anonymous / public submit) |
| **Owner** | Persona accountable for the workflow ("buck stops here") |
| **Viewers** | Personas that can read the record |
| **Editors** | Personas that can modify the record |
| **Delete authority** | Who can hard-delete or transition to "frozen" state |
| **Closer** | Persona that closes the workflow loop |
| **No-response path** | What happens if Owner never responds |

## 2 · Matrix

| Workflow | Creator | Owner | Viewers | Editors | Delete | Closer | No-response path |
|---|---|---|---|---|---|---|---|
| **Daily Report** | anonymous (foreman field submit) | Assigned PM (from `project_number`) | PM · Admin · HR · Safety · Shop (signoff card) | Admin only (post-submit) | **frozen — DELETE returns 410 by doctrine** | PM (review) | none defined — PM bell only |
| **DR · Production rows** | (sub-record of DR) | PM | inherits | (read-only post-submit) | inherits | inherits | n/a |
| **DR · Delays/Extra Work rows** | (sub-record) | PM | inherits | inherits | inherits | inherits | n/a |
| **DR · Weather Impact** | (sub-record) | PM | inherits | inherits | inherits | inherits | **none — operator confirmed schedule-integration on stop-list** |
| **Equipment Pre-Op (PASS)** | anonymous (operator) | Shop Manager | Admin · Shop · PM (scope) | Admin only | Admin only | Shop Manager (review email) | none — pass records are reference-only |
| **Equipment Pre-Op (FAIL)** | anonymous (operator) | Shop (task assigned) | Admin · Shop · PM (scope) | Admin only · Shop (signoff) | Admin only | Shop (signoff signs-off + sets out-of-service back to in-service) | task expires after configurable interval; future P1 — escalate to admin if no signoff |
| **Shop Recovery / asset-transfer** | Shop · Dispatch · Admin | Shop | Admin · Dispatch · Shop | originator · admin | Admin | Shop | task remains open · admin dashboard surfaces unsigned items |
| **PO Request** | any portal user | approval queue (leadership / admin / hr per PO routing) | requester · admin · approval queue | requester (pre-approval) · approval queue (approve/reject/clarify) | Admin only | approver | nightly cron raises "approval_needed" task; missing-receipt cron raises follow-up task |
| **PO Response** | approver | requester · admin | requester · admin · approval queue (audit) | (no edit after decision) | Admin only | requester (uploads receipt → status advances) | none defined for "no receipt uploaded for 30 days" beyond the existing receipt-missing watchdog |
| **PO Receipt upload** | any portal user (typically requester) | Admin · PM (financial reconciliation) | Admin · PM · HR | requester (until close) | Admin only | Admin (closes PO) | manual close · no escalation path |
| **PO Invoice upload** | (no separate invoice model — receipts only) | n/a | n/a | n/a | n/a | n/a | n/a — invoice = receipt in current data model |
| **Incident Report** | anonymous (foreman / safety) | Safety + Admin | Safety · Admin · PM (scope) · HR (if injury) | Admin only | Admin only | Safety (closes investigation) | none defined for severe-incident no-response (P1) |
| **Safety Meeting** | any portal user · Safety | Safety | Safety · Admin · PM | Admin only | Admin only | Safety | none |
| **JHA** | any portal user | Safety | Safety · Admin · PM | Admin only | Admin only | Safety | **GAP-3 — no task to safety supervisor** |
| **JHP (Job Hazard Planning)** | Safety | Safety | Safety · Admin · PM | Admin only | Admin only | Safety | n/a (consolidated with safety_forms) |
| **QA/QC Concrete/Rebar/Subwork** | any portal user | Safety (compliance owner per V.5 ownership decision) · PM (project view) | Safety · Admin · PM | Admin only | Admin only | Safety | none |
| **QA/QC Material Testing** | Safety | Safety | Safety · Admin · PM | Admin only | Admin only | Safety | none |
| **Asphalt Inspection** | (sub-type of QA/QC) | Safety | inherits | inherits | inherits | inherits | n/a |
| **Dispatch Request** | Dispatch · any field requester | Dispatch lead | Dispatch · Admin · Shop · PM | Dispatch · Admin | Admin only | Dispatch (closes when crew/asset deployed) | task surfaces in Dispatch hub; admin observes |
| **Equipment Request** | (subset of dispatch) | Dispatch | inherits | inherits | inherits | inherits | inherits |
| **HR Request (general)** | HR | HR | HR · Admin | HR · Admin | Admin only | HR | none |
| **Time Verification batch** | HR Manager | HR | HR · Admin | (read-only ledger; HR cannot edit Foreman timesheets directly) | n/a | (read-only) | n/a (read-only verification surface — no action expected) |
| **Payroll Variance manual** | HR Manager | HR | HR · Admin | HR | Admin only | HR | none for manual batches |
| **Payroll Variance weekly cron** | system | HR + Admin | HR · Admin | (system) | n/a | (operator-archive) | weekly email · admin reviews |
| **Training Record assigned** | Safety / HR | Employee | Safety · HR · Admin · linked supervisor (if found) | Safety · HR | Admin only | Employee (completes) | **GAP-4 — supervisor not always notified** |
| **Training Record completed** | Employee | Employee | inherits | inherits | inherits | (closes) | n/a |
| **Visitor Log** | (sub-record of DR) | PM (via DR ownership) | inherits | inherits | inherits | inherits | n/a |
| **Fleet DVIR** | Driver / Operator | Dispatch + Shop | Admin · Dispatch · Shop | Admin only | Admin only | Shop (resolves any defects flagged) | **GAP-6 — no notification path confirmed** |
| **Safety Equipment Issuance** | Safety / HR | Safety | Safety · Admin · HR | Safety · Admin | Admin only | Safety (tracks return) | **GAP-2 — bell-feed missing** |
| **Safety Equipment Training** | Safety | Employee + Safety | Safety · Admin | Safety · Admin | Admin only | Safety | **GAP-2 — bell-feed missing** |
| **Attachments / Public Links** | requester | requester | (anyone with link · rate-limited) | (read-only) | Admin only | (autoexpires per policy) | n/a |
| **PDF Downloads** | (transient HTTP) | n/a | (gated by parent record permissions) | n/a | n/a | n/a | n/a |
| **Backup Alerts** | scheduler | Admin (sole) | Admin | (system) | n/a | (admin acknowledges) | **GAP-7 — currently broken, scheduler dead** |
| **System Health Alerts** | health monitor cron | Admin | Admin | (system) | n/a | (admin acknowledges) | works (BUT subject to scheduler revival) |

## 3 · Ownership-field schema (canonical fields)

| Field | Set by | Used by |
|---|---|---|
| `created_at` | `datetime.now(timezone.utc)` on insert | every record |
| `created_by` | submit context (logged-in user · "Foreman" · "Anonymous Field Submit") | every record |
| `assigned_to` | task service (`task_service.create`) | tasks only |
| `requested_by` | PO requests, dispatch requests | PO, Dispatch |
| `submitted_by` | DR field; `prepared_by` field | DR |
| `superintendent` | DR section 03 (canonical FL role picker) | DR |
| `project_manager` | derived from `project_number` lookup | DR · Equipment · Safety · QA/QC · PO |
| `pm_decision`, `hr_decision` | nested objects on FL forms | FL forms |
| `_canonical_role` | `field_leadership_users` collection | FL portal |
| `email_to` | from `email_routing_config` | auto-email pipeline |

## 4 · Gaps consolidated by ownership lens

| Gap | Workflow | Ownership weakness |
|---|---|---|
| GAP-2 | Safety Equipment Issuance/Training | record exists with email-only fan-out; no bell-feed/task means **no operational dashboard owner sees it**. Safety hub does not surface these records. |
| GAP-3 | JHA submit | no task → safety supervisor never gets it in their action queue |
| GAP-4 | Training Record assigned | employee sees; their supervisor doesn't (unless `linked_employee_id`'s manager is back-resolved, which is intermittent) |
| GAP-6 | Fleet DVIR | unconfirmed owner; no notification, no task |
| GAP-7 | Backup alerts | watchdog cron depends on the dead scheduler; effectively silent failure |

---

_End of WORKFLOW_OWNERSHIP_MATRIX.md._
