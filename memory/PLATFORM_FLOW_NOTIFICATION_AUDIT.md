# Platform Flow & Notification Audit

_Phase V.5 · P0 Platform Trust Restoration · 2026-05-29 20:35 UTC._

> Every workflow's notification + task fan-out path traced through the
> codebase. Read-only audit, no fixes.

## 1 · Two notification pipelines coexist

### 1a · `schedule_auto_email` (PDF email pipeline)
- Triggers a Resend email with a generated PDF attachment
- Recipient list resolved via `recipients_for_record_async(db, record, kind)`
- Override-able via `email_routing_config` Mongo doc (admin-editable)
- Used by: Daily Report · Equipment Pre-Op · Safety Inspection · Safety Meeting · JHA · Incident · QA/QC
- Gated by `auto_email_enabled()` (`RESEND_API_KEY` present + `AUTO_EMAIL_REPORTS` not false)

### 1b · `emit_task_and_notification` / `emit_notification` (in-app bell + tasks)
- Creates a row in `db.tasks` (operational action item) AND/OR `db.notifications` (bell-feed entry)
- Routed to a role (admin, pm, shop, hr, safety, dispatch, fl)
- Listed via `GET /api/tasks` and `GET /api/notifications` (bell badge `unread-count`)
- Used by: Equipment Pre-Op (fails) · PO Requests · Safety (CA · fire-ext) · QA/QC · Asset Transfers · Employee Lifecycle · Document Expirations · Training Center · Safety Portal Corrective Actions · Safety Portal Fire Extinguishers

## 2 · Per-workflow notification matrix

| Workflow | Trigger | PDF email (auto-email) | Bell/Task | Recipients | Gap? |
|---|---|---|---|---|---|
| **Daily Report submit** | `POST /api/daily-reports` | ✅ `schedule_auto_email("daily-report", doc)` | ❌ | Assigned PM + always_cc | none (PM intentionally owns) |
| **Daily Report — Visitors sub-rows** | inside DR | inherits DR email | ❌ | inherits | none (sub-record) |
| **Daily Report — Production rows** | inside DR | inherits | ❌ | inherits | none |
| **Daily Report — Delays/Extra Work rows** | inside DR | inherits | ❌ | inherits | none |
| **Daily Report — Weather YES flag** | inside DR | inherits | ❌ | inherits | **P2 — no automatic schedule-impact task** |
| **Equipment Pre-Op submit (PASS)** | `POST /api/equipment-inspections` | ✅ `schedule_auto_email` → Shop Manager role only (iter238 override) | ❌ | Shop Manager(s) | none |
| **Equipment Pre-Op submit (FAIL)** | same endpoint, `fail_count > 0` | same email | ✅ `emit_task_and_notification` → assignee_role `shop` | Shop role + cc PM, Superintendent | none |
| **Equipment Pre-Op signoff (shop)** | `POST /api/equipment-inspections/{id}/signoff` | ❌ | ✅ `emit_notification` → PM | Assigned PM | none |
| **Shop Recovery / asset-transfer** | `POST /api/asset-transfers` | ❌ | ✅ `emit_task_and_notification` → shop | Shop + originating party | none |
| **PO Request submit** | `POST /api/po-requests` | ❌ | ✅ task → leadership/admin + cc PM/HR | Approval queue | none |
| **PO Response approve/reject/clarify** | `POST .../approve|reject|clarify` | ❌ | ✅ `emit_notification` → requester + admin | Requester | none |
| **PO Receipt upload** | `POST .../receipt` | ❌ | ✅ task closes receipt-missing task; bell to requester | Requester + admin | none |
| **PO Receipt-missing watchdog** | nightly cron (server.py) | ❌ | ✅ creates `po.receipts` task | Approval queue | none |
| **Incident Report submit** | `POST /api/safety/incidents` | ✅ `schedule_auto_email("incident", doc)` (with `severe_incident_cc` env CC for severe) | ✅ task → safety + PM project-health notification | safety, PM, plus configured CC | none |
| **Safety Meeting submit** | `POST /api/safety/meetings` | ✅ `schedule_auto_email("meeting")` | ✅ task → safety | safety + always_cc | none |
| **Safety Inspection submit** | `POST /api/safety/inspections` | ✅ `schedule_auto_email("inspection")` | ✅ task → safety + pm | safety + pm | none |
| **JHA submit** | `POST /api/safety/jha` | ✅ `schedule_auto_email("jha")` | ❌ | safety + always_cc | **P1 — no task to safety supervisor** |
| **JHP submit** | `POST /api/safety/jhp` (if exists) | (see safety_forms) | ❌ | safety_forms_to | (consolidated with safety forms — see below) |
| **Safety Forms (FL 10 forms)** | `POST /api/field-leadership/forms/...` | ✅ `send_email_async` → leadership_always_to | ❌ | safety + admin | **P1 — no bell/task** |
| **Safety Forms (Equipment Issuance/Training)** | `POST /api/safety-forms/*` | ✅ `_dispatch_email` → safety_forms_to | ❌ | safety + admin | **P1 — no bell/task** |
| **QA/QC submit (Concrete/Rebar/Subwork)** | `POST /api/qaqc/...` | ✅ `schedule_auto_email("qaqc")` | ✅ task → safety (compliance owner) | safety + always_cc | none |
| **Corrective Action open** | safety.corrective_actions | ❌ | ✅ task → safety + linked party | safety | none |
| **Fire Extinguisher inspection** | safety_portal.fire_extinguishers | ❌ | ✅ task → safety | safety | none |
| **Training Record assigned** | training_center | ❌ | ✅ task → employee | Employee | **P1 — supervisor not notified** |
| **Training Record completed** | training_center | ❌ | ✅ task closes | n/a | none |
| **Time Verification query** | `GET /api/hr/time-verification` (read-only) | n/a | n/a | n/a | n/a (no event to notify on) |
| **Payroll Variance batch** | `POST /api/hr/payroll-variance` | ✅ weekly cron emails to `PAYROLL_VARIANCE_EMAIL_TO` (Sunday 18:00 UTC) | ❌ | PAYROLL_VARIANCE_EMAIL_TO env | **P2 — manual triggers don't notify; only cron does** |
| **Dispatch Request** | dispatch_lifecycle | ❌ | ✅ task → dispatch | Dispatch lead | none |
| **HR Visitor Log** | embedded in DR | inherits DR email | ❌ | inherits | n/a (sub-record) |
| **Fleet DVIR submit** | (route in fleet_ops.py) | ❌ | ❌ | none confirmed | **P0/P1 — no notification path confirmed** |
| **Document Expiration warning** | nightly cron | ❌ | ✅ task → HR + admin | HR | none |
| **Backup success (hourly/daily)** | scheduler loop | ✅ Resend email to `BACKUP_EMAIL_TO` | ❌ | jaymn.judd@mascigc.com | none |
| **Backup failure / staleness** | watchdog cron | ✅ Resend alarm to `BACKUP_EMAIL_TO` (requires watchdog reachable) | ❌ | jaymn.judd@mascigc.com | **P0 — currently broken: scheduler is dead, watchdog never reads stale-zero state** (open since 79h-stale incident) |
| **System Health Outage** | `outage_alerts.send_outage_alert` from health monitoring loop | ✅ Resend to `OUTAGE_ALERT_TO` | ❌ | jaymn.judd@mascigc.com | none |

## 3 · Routing-config keys (admin-editable, DB-overrides env)

| Key | Default | Type | Audience |
|---|---|---|---|
| `always_cc` | `[jaymn.judd@mascigc.com, safety@mascigc.com]` | List | Office CC on compliance kinds (inspection / meeting / JHA / incident / qaqc) |
| `safety_forms_to` | `[safety@, jaymn@]` | List | Full To: for Safety Forms (issuance, training, return) |
| `leadership_always_to` | `[jaymn@, safety@]` | List | CC for the 10 FL forms |
| `shop_manager_fallback` | `shopmanager@mascigc.com` | str | Used when `shop_users` collection has no Shop Manager role |
| `severe_incident_cc` | `[]` | List | Extra CCs for severe incidents |
| `backup_email_to` | from env | List | Backup auto-email + manual backup-email-now |

## 4 · Resolution heuristic (per-record)

`recipients_for_record_async` resolves the recipient list using:
1. Assigned PM (from `project_number` → PM lookup in `pm_routing.py`)
2. Always-CC list (`always_cc` routing key)
3. Optional cc roles via the calling code (e.g. PO's `cc_roles=["hr"]`)
4. Severe-incident extras (`severe_incident_cc`)

## 5 · Gaps (consolidated)

| Gap ID | Workflow | Type | Severity |
|---|---|---|---|
| GAP-1 | FL 10 forms — no bell/task fan-out | bell-feed missing | P1 |
| GAP-2 | Safety Forms (equipment issuance / training / return) — no bell/task fan-out | bell-feed missing | P1 |
| GAP-3 | JHA submit — no task to safety supervisor | task missing | P1 |
| GAP-4 | Training Record assigned — supervisor not notified | recipient missing | P1 |
| GAP-5 | Payroll Variance — manual batch creates no notification (only weekly cron emails) | recipient missing | P2 |
| GAP-6 | Fleet DVIR — no notification path | full chain missing | P0 (suspected; needs operator confirmation that DVIR was intended to notify) |
| GAP-7 | Backup failure alert blocked by dead scheduler | known P0 (separately tracked) | P0 |
| GAP-8 | Daily Report Weather YES → no schedule-impact task | task missing | P2 (intentional per operator — schedule integration is on stop-list) |

---

_End of PLATFORM_FLOW_NOTIFICATION_AUDIT.md._
