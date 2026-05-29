# Alerting & Destination Matrix

_Phase V.5 · P0 Platform Trust Restoration · 2026-05-29 20:40 UTC._

> For every workflow: where alerts go and which dashboards surface the
> record. Read-only audit, no fixes.

## 1 · Schema

| Column | Meaning |
|---|---|
| **Email recipients** | Resend email destinations |
| **Bell / Task** | In-app notifications + actionable tasks (visible via `/api/notifications` and `/api/tasks`) |
| **Dashboard surface** | Portal hub card / panel / table where the record appears |
| **Severity tier** | P0 = system-critical · P1 = operational · P2 = informational |

## 2 · Matrix

| Workflow | Email | Bell | Task | Dashboard surface |
|---|---|---|---|---|
| **Daily Report (any)** | PM + always_cc | ❌ | ❌ | Admin DR list · PM Hub project tile · HR Daily Reports filter |
| **Daily Report (Injury YES)** | PM + always_cc | ❌ | ❌ | (none specific — relies on Incident Report creation) |
| **Daily Report (Equipment Issue YES)** | PM + always_cc | ❌ | ❌ | (no auto-link to Equipment Pre-Op) **P2 gap** |
| **Equipment Pre-Op PASS** | Shop Manager (iter238 override) | ❌ | ❌ | Admin Equipment Dashboard · PM Equipment list · Shop Equipment list |
| **Equipment Pre-Op FAIL** | Shop Manager | Shop role bell | Shop task | Admin Equipment Dashboard "Open Items" panel · Shop "Equipment Needing Attention" tile · ShopHub Open Shop Items |
| **Shop Recovery / asset-transfer** | none | Shop role bell | Shop task | ShopHub Active Recovery section · Shop Asset Transfers list |
| **PO Request** | none | Approval queue bell | Approval task | PO Requests table · ApprovalCount card · PendingApprovalQueue widget · PM PO Requests · HR PO Requests · admin nightly cron |
| **PO Approve / Reject / Clarify** | none | Requester bell | (closes prior task) | requester sees status flip · audit log · admin dashboard |
| **PO Receipt upload** | none | Requester bell | (closes receipt-missing task) | PO Requests "Pending Receipt" → "Closed" status; admin dashboard |
| **Incident Report** | Safety · Admin · `severe_incident_cc` for severe | Safety bell | Safety task | Safety Operations Dashboard · Admin Incidents list · HR Safety Records (if injury) |
| **Safety Meeting** | Safety + always_cc | Safety bell | Safety task | Safety Operations Dashboard · Admin meetings list · HR Safety Records |
| **Safety Inspection** | Safety + always_cc | Safety bell | Safety + PM task | Safety Ops Dashboard · Admin Inspections list |
| **JHA** | Safety + always_cc | ❌ **GAP-3** | ❌ **GAP-3** | Admin JHA list (only) |
| **Safety Forms (Equipment Issuance/Training/Return)** | safety_forms_to | ❌ **GAP-2** | ❌ **GAP-2** | Admin Safety Forms list (only) |
| **Field Leadership 10 forms** | leadership_always_to (Safety + Admin) | ❌ **GAP-1** | ❌ **GAP-1** | FL Portal forms list · Admin FL forms list (read-only by default) |
| **QA/QC Concrete/Rebar/Subwork** | Safety + always_cc | Safety bell | Safety task | Safety Operations Dashboard · Admin QA/QC list · PM QA/QC list |
| **QA/QC Material Testing** | Safety + always_cc | Safety bell | Safety task | same |
| **Corrective Action** | none | Safety bell | Safety task | Safety CA list · Safety Hub Open CAs card |
| **Fire Extinguisher Inspection** | none | Safety bell | Safety task | Safety Fire Extinguishers list |
| **Dispatch Request** | none | Dispatch bell | Dispatch task | DispatchHub board |
| **HR Time Verification** | none (read-only) | n/a | n/a | HR Time Verification page |
| **HR Payroll Variance manual** | none | ❌ **GAP-5** | ❌ **GAP-5** | HR Payroll Variance page |
| **HR Payroll Variance weekly cron** | PAYROLL_VARIANCE_EMAIL_TO env | ❌ | ❌ | HR Payroll Variance page (next-batch surfaces it) |
| **Training Records (assigned)** | none | Employee bell | Employee task | Training Center · HR Training Records · Safety Training Records · supervisor (if linked) **GAP-4 if no supervisor link** |
| **Visitor Log (sub-record)** | inherits DR | ❌ | ❌ | DR detail (only) |
| **Fleet DVIR** | none | ❌ | ❌ | (no confirmed dashboard) **GAP-6** |
| **Document Expirations** | none | HR bell | HR task | Admin Document Expirations cron + HR Hub |
| **Backup success** | BACKUP_EMAIL_TO | ❌ | ❌ | Admin Backup Health panel |
| **Backup failure / staleness** | BACKUP_EMAIL_TO via watchdog | ❌ | ❌ | Admin Backup Health panel · email alarm |
| **System Health Outage** | OUTAGE_ALERT_TO via send_outage_alert | ❌ | ❌ | Admin Persistence/Health panels |

## 3 · Dashboard surfaces (where workflows land)

| Hub | Visible workflows |
|---|---|
| **Admin Console** | Backup Health · System Health · Approval Queue · everything mounted under admin namespace |
| **PM Hub** | Project tiles · DR submission stream · Equipment Pre-Op scope · PO Requests scope |
| **Shop Hub** | Equipment Needing Attention (failed pre-ops) · Active Recovery Work · Waiting/Delays · Returned to Service · Operational Continuity History · More footer (now-enabled: Recent Pre-Op Inspections / Fleet DVIR queue / Trends / Activity / Equipment / Parts / Integrations) |
| **HR Hub** | Docs Expired card · Overdue Tasks card · POs Missing Receipt card · Docs Expiring Soon card · Daily Reports filter · Time Verification · Payroll Variance · Training Records · Safety Records · Employee Accountability · PO Requests |
| **Safety Operations Dashboard** | 4 stats (Incidents Total · Incidents 7d · Meetings 7d · Inspections 30d) · 4 secondary stats (CA Open · CA Overdue · Training Deficiencies · PPE Issuances) · Primary Operations (Inspections · Meetings · Incidents · QA/QC · Corrective Actions · Fire Extinguishers · Training · Equipment Issuance) |
| **Dispatch Portal** | Operational Attention (Trucks in Breakdown · Stuck > 30 min · Extended Wait) · Issue Work tiles · Drivers · DVIR queue · Integrations |
| **Field Leadership Portal** | 10 forms list · 4 FL roles (sr_superintendent · superintendent · foreman · leadman) |

## 4 · Alert-staleness recovery

| Alert source | Cooldown | Reset trigger | Stale-suppression risk |
|---|---|---|---|
| Backup watchdog | `BACKUP_WATCHDOG_COOLDOWN_HOURS` (default 12 h) | Successful backup_health row appears (resets `_watchdog_last_alarm`) | Currently NONE firing because scheduler dead (P0 known) |
| System Health outage | `OUTAGE_ALERT_COOLDOWN_MIN` (default 60 min) | Endpoint returns 200 for 5 minutes | Healthy |
| PO Request approval-needed | nightly cron | new PO landing, or approval flipping status | Healthy |
| PO Receipt missing | nightly cron | receipt uploaded | Healthy |
| Document Expiration | nightly cron | document renewed | Healthy |

## 5 · Gaps consolidated by alert lens

| Gap | Manifestation |
|---|---|
| GAP-1 (FL 10 forms) | submission lands in admin list silently; no proactive surface for the assigned safety / leadership team. Email-only fan-out means the record exists but is unanchored to a "what do I do next" dashboard. |
| GAP-2 (Safety Forms) | same pattern as GAP-1 |
| GAP-3 (JHA) | safety email goes out but the safety team's task queue doesn't include the JHA |
| GAP-4 (Training assigned) | the assignee gets it; the assignee's supervisor doesn't, so the supervisor cannot see "my crew has training due" in their dashboard |
| GAP-5 (Payroll variance manual) | HR Manager triggers a batch but it doesn't notify a CC list or generate a task. The HR Manager themselves must close the loop. |
| GAP-6 (Fleet DVIR) | unconfirmed — needs operator clarification whether DVIR was ever wired into the notification pipeline. The fleet_ops.py route file appears present but no `schedule_auto_email` / `emit_*` calls were found. |
| GAP-7 (Backup) | currently broken P0 — separately tracked |

---

_End of ALERTING_AND_DESTINATION_MATRIX.md._
