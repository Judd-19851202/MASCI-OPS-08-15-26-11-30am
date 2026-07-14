# MASCI Operational Execution Role and Ownership Matrix

## 1. Role Authority

This matrix defines explicit role/object/action authority for the MASCI Operational Execution system.

No shorthand letters are authoritative.
Only the permission values defined below are authoritative.

## 2. Permission Value Set

- **ALLOWED** — actor may perform the action directly within governed scope
- **READ_ONLY** — actor may view, but may not mutate or approve
- **PROPOSE_ONLY** — actor may initiate a proposal/request, but another governed role must approve or complete
- **APPROVAL_REQUIRED** — actor may perform the action only after required approval is attached or while acting in an approval lane explicitly granted elsewhere
- **SYSTEM_DERIVED** — action may be executed only by deterministic preapproved automation
- **PROHIBITED** — actor may not perform the action
- **NOT_APPLICABLE** — action does not apply to this role/object combination

## 3. Governed Roles

- Platform Admin
- Company Admin
- Owner/President
- Executive
- Operations Leadership
- PM
- Co-PM
- Project Engineer
- Superintendent
- Foreman
- Field Leadership
- Dispatch
- Transportation
- Driver
- Shop
- Equipment/Fleet
- Safety
- HR
- QA/QC
- Survey
- Accounting
- Qualifications/Training Manager
- Read-Only Leadership
- System Automation
- AI Assistant

## 4. Governed Objects

- Organization/Tenant
- Person/Professional Identity
- Employee/Company Membership
- Project
- Project Team Assignment
- Company Cost Code
- Project Cost Code
- Cost-Code Alias
- Work Area
- Operational Work
- Schedule Activity
- Schedule Window
- Published Schedule
- Schedule Revision
- Resource Demand
- Resource Conflict
- Constraint
- Readiness
- Daily Report
- Daily Report Work Item
- Production Actual
- Labor Actual
- Equipment Actual
- Material Actual
- Trucking Actual
- Reconciliation
- Carry-Forward
- Executive Attention Item
- KPI
- Dashboard Projection
- Daily Company Operations Brief
- Brief Revision
- Notification
- Evidence/Attachment Reference
- Audit Record
- Trust Event
- ODS Projection
- Certification Artifact

## 5. Canonical Owner Matrix

| Object | Canonical Owner | Operational Contributor | Consumer | Escalation Owner | Backup Owner | SLA Note |
|---|---|---|---|---|---|---|
| Organization/Tenant | Company Admin / Platform authority | Company Admin | all scoped roles | Owner/President | Platform Admin | governance-critical |
| Person/Professional Identity | identity authority | HR | all scoped domains | HR | Company Admin | identity-critical |
| Employee/Company Membership | HR | Qualifications/Training Manager | PM, Safety, Dispatch, Operations | HR | Company Admin | workforce-critical |
| Project | `jobs_master` | PM / Operations | all scoped domains | Operations Leadership | Company Admin | operational-critical |
| Project Team Assignment | `project_team_assignments` | PM / Company Admin | PM, Executive, Operations, dashboards | Operations Leadership | Company Admin | staffing-critical |
| Company Cost Code | company cost-code authority | Company Admin | PM, Operations, Daily Reports, Reconciliation | Operations Leadership | Accounting | financial classification |
| Project Cost Code | project cost-code authority | PM | work, schedule, Daily Reports | Operations Leadership | Company Admin | project coding |
| Cost-Code Alias | cost-code alias authority | PM / Company Admin | search, mapping, history | Operations Leadership | Company Admin | compatibility-only |
| Work Area | work-area authority | Survey / PM | work, schedule, Daily Reports | Operations Leadership | Project Engineer | field-critical |
| Operational Work | Operational Work authority | PM / Superintendent / Foreman / Field Leadership | schedule, reconciliation, brief | Operations Leadership | PM | core work truth |
| Schedule Activity | schedule authority | PM / Superintendent / Field Leadership | dashboards, reconciliation, brief | Operations Leadership | Co-PM | commitment-critical |
| Schedule Window | schedule authority | PM / Operations | schedule consumers | Operations Leadership | Co-PM | publication-critical |
| Published Schedule | schedule authority | PM / Operations | Daily Execution, reconciliation, brief | Operations Leadership | Company Admin | publication-critical |
| Schedule Revision | schedule authority | PM / Operations | schedule consumers | Operations Leadership | Company Admin | version-critical |
| Resource Demand | source domain owner | PM / Superintendent / Dispatch / Shop | readiness/schedule/reconciliation | Operations Leadership | source domain backup owner | planning-critical |
| Resource Conflict | conflict evaluation authority | Operations / PM / Dispatch / Shop | schedule/readiness/dashboards | Operations Leadership | source domain owner | action-critical |
| Constraint | constraint authority | source domain + PM | schedule/readiness/reconciliation/brief | Operations Leadership or Safety when safety-bound | source domain backup owner | blocker-critical |
| Readiness | readiness authority | PM / Dispatch / Shop / Safety / QA/QC | schedule/executive surfaces | Operations Leadership | PM | go/no-go critical |
| Daily Report | `daily_reports` | Foreman / Superintendent / Field Leadership | PM, HR, Safety, ODS, reconciliation | PM for workflow, not source rewrite | Superintendent | field actual truth |
| Daily Report Work Item | Daily Report authority | Foreman / Superintendent | ODS, work linkage, reconciliation | PM for workflow only | Superintendent | item-level actual truth |
| Production Actual | Daily Report authority / governed projection | Foreman / Superintendent | ODS, KPI, reconciliation | PM / Operations | ODS projection authority | actuals-critical |
| Labor Actual | Daily Report / HR as governed source split | Foreman / Superintendent / HR | payroll checks, KPI, reconciliation | HR | PM | labor-critical |
| Equipment Actual | Daily Report / Equipment authority by concept | Foreman / Equipment/Fleet | KPI, reconciliation | Equipment/Fleet | Shop | asset-use critical |
| Material Actual | Daily Report / source material domain | Foreman / PM | KPI, reconciliation, brief | PM | Operations | material-critical |
| Trucking Actual | Transportation / Dispatch / Daily Report linkage | Dispatch / Transportation | KPI, reconciliation, brief | Operations Leadership | Dispatch | transport-critical |
| Reconciliation | reconciliation authority | PM / Operations / Safety / QA/QC | brief, dashboards | Operations Leadership | PM | close-the-loop critical |
| Carry-Forward | schedule/reconciliation authority | PM / Operations | schedule/reconciliation | Operations Leadership | PM | lineage-critical |
| Executive Attention Item | executive attention authority | Executive / Operations | Executive / PM / Safety / HR as scoped | Owner/President | Executive | intervention-critical |
| KPI | KPI owner per contract | source domain owners | dashboards, brief | Operations Leadership | Company Admin | decision-critical |
| Dashboard Projection | governed dashboard authority | System Automation / source domains | role-specific users | owning role lane | source domain owner | read-only projection |
| Daily Company Operations Brief | brief authority / Operational Intelligence | Executive / Operations reviewers | leadership consumers | Owner/President / Executive | Operations Leadership | publication-critical |
| Brief Revision | brief authority | Executive / Operations | leadership consumers | Executive | Operations Leadership | version-critical |
| Notification | notification authority over existing ecosystem | source workflow owner | targeted recipients | Operations Leadership / domain owner | Company Admin | delivery-only |
| Evidence/Attachment Reference | source-record authority | source workflow roles | scoped viewers | source domain escalation owner | Company Admin | evidence-critical |
| Audit Record | audit authority | System Automation | admins / scoped auditors | Platform Admin | Company Admin | append-only |
| Trust Event | Trust Spine authority | System Automation | certification / operations | Platform Admin | Company Admin | append-only proof |
| ODS Projection | ODS authority | System Automation | dashboards, brief, analytics | Operations Leadership | Platform Admin | derived-only |
| Certification Artifact | certification authority | engineers / operators / executives per lane | approvers, auditors | Operations Leadership / Executive / Jaymn by milestone | Platform Admin | release-critical |

## 6. Action Matrix by Role Family

### 6.1 Source Record Protection Rules

| Role | Daily Report | Daily Report Work Item | Production/Labor/Equipment/Material/Trucking Actuals | Published Schedule | Reconciliation | Brief | Notification | Certification Artifact |
|---|---|---|---|---|---|---|---|---|
| Executive | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | APPROVAL_REQUIRED | READ_ONLY | READ_ONLY |
| Operations Leadership | READ_ONLY | READ_ONLY | READ_ONLY | APPROVAL_REQUIRED | ALLOWED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED |
| PM | READ_ONLY | READ_ONLY | READ_ONLY | APPROVAL_REQUIRED | APPROVAL_REQUIRED | READ_ONLY | READ_ONLY | READ_ONLY |
| Superintendent | APPROVAL_REQUIRED | APPROVAL_REQUIRED | READ_ONLY | PROPOSE_ONLY | PROPOSE_ONLY | READ_ONLY | READ_ONLY | ALLOWED |
| Foreman | ALLOWED | ALLOWED | PROPOSE_ONLY | PROHIBITED | PROHIBITED | PROHIBITED | READ_ONLY | ALLOWED |
| Field Leadership | ALLOWED | ALLOWED | PROPOSE_ONLY | PROPOSE_ONLY | PROHIBITED | PROHIBITED | READ_ONLY | ALLOWED |
| Dispatch | READ_ONLY | READ_ONLY | PROPOSE_ONLY | PROHIBITED | READ_ONLY | READ_ONLY | ALLOWED | READ_ONLY |
| Transportation | READ_ONLY | READ_ONLY | PROPOSE_ONLY | PROHIBITED | READ_ONLY | READ_ONLY | ALLOWED | READ_ONLY |
| Shop | READ_ONLY | READ_ONLY | PROPOSE_ONLY | PROHIBITED | READ_ONLY | READ_ONLY | ALLOWED | READ_ONLY |
| Equipment/Fleet | READ_ONLY | READ_ONLY | APPROVAL_REQUIRED | PROHIBITED | READ_ONLY | READ_ONLY | ALLOWED | READ_ONLY |
| Safety | READ_ONLY | READ_ONLY | READ_ONLY | ALLOWED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | ALLOWED | READ_ONLY |
| HR | READ_ONLY | READ_ONLY | READ_ONLY | PROHIBITED | READ_ONLY | READ_ONLY | ALLOWED | READ_ONLY |
| QA/QC | READ_ONLY | READ_ONLY | READ_ONLY | ALLOWED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | ALLOWED | READ_ONLY |
| System Automation | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED |
| AI Assistant | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROPOSE_ONLY | PROHIBITED | PROHIBITED |

### 6.2 Core Planning and Commitment Actions

| Role | Operational Work Create/Edit | Schedule Activity Create/Edit | Schedule Window Manage | Commit | Publish | Revise | Supersede | Cancel | Reopen | Reconcile |
|---|---|---|---|---|---|---|---|---|---|---|
| Platform Admin | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED |
| Company Admin | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED |
| Owner/President | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY |
| Executive | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY |
| Operations Leadership | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED |
| PM | ALLOWED | ALLOWED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | ALLOWED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED | APPROVAL_REQUIRED |
| Co-PM | ALLOWED | ALLOWED | PROPOSE_ONLY | PROPOSE_ONLY | PROHIBITED | PROPOSE_ONLY | PROHIBITED | PROPOSE_ONLY | PROHIBITED | PROPOSE_ONLY |
| Project Engineer | PROPOSE_ONLY | PROPOSE_ONLY | PROPOSE_ONLY | PROHIBITED | PROHIBITED | PROPOSE_ONLY | PROHIBITED | PROPOSE_ONLY | PROHIBITED | PROPOSE_ONLY |
| Superintendent | PROPOSE_ONLY | PROPOSE_ONLY | PROPOSE_ONLY | PROHIBITED | PROHIBITED | PROPOSE_ONLY | PROHIBITED | PROPOSE_ONLY | APPROVAL_REQUIRED | PROPOSE_ONLY |
| Foreman | PROPOSE_ONLY | PROPOSE_ONLY | PROHIBITED | PROHIBITED | PROHIBITED | PROPOSE_ONLY | PROHIBITED | PROPOSE_ONLY | PROHIBITED | PROHIBITED |
| Field Leadership | PROPOSE_ONLY | PROPOSE_ONLY | PROHIBITED | PROHIBITED | PROHIBITED | PROPOSE_ONLY | PROHIBITED | PROPOSE_ONLY | PROHIBITED | PROPOSE_ONLY |
| Dispatch | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | READ_ONLY |
| Transportation | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | READ_ONLY |
| Shop | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | READ_ONLY |
| Equipment/Fleet | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | READ_ONLY |
| Safety | PROHIBITED | READ_ONLY | READ_ONLY | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | APPROVAL_REQUIRED |
| HR | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | READ_ONLY |
| QA/QC | PROHIBITED | READ_ONLY | READ_ONLY | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | APPROVAL_REQUIRED |
| Survey | PROPOSE_ONLY | READ_ONLY | READ_ONLY | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | READ_ONLY |
| Accounting | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY |
| Qualifications/Training Manager | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY |
| Read-Only Leadership | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY | READ_ONLY |
| System Automation | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED |
| AI Assistant | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED |

## 7. Notification and Brief Receipt Authority

| Role | Receive Notification | Receive Brief | Export | Certify | Provide Field Acceptance | Administer |
|---|---|---|---|---|---|---|
| Platform Admin | ALLOWED | READ_ONLY | ALLOWED | APPROVAL_REQUIRED | NOT_APPLICABLE | ALLOWED |
| Company Admin | ALLOWED | READ_ONLY | ALLOWED | APPROVAL_REQUIRED | NOT_APPLICABLE | ALLOWED |
| Owner/President | ALLOWED | ALLOWED | READ_ONLY | READ_ONLY | NOT_APPLICABLE | PROHIBITED |
| Executive | ALLOWED | ALLOWED | READ_ONLY | APPROVAL_REQUIRED | NOT_APPLICABLE | PROHIBITED |
| Operations Leadership | ALLOWED | ALLOWED | READ_ONLY | APPROVAL_REQUIRED | NOT_APPLICABLE | PROHIBITED |
| PM | ALLOWED | APPROVAL_REQUIRED | READ_ONLY | READ_ONLY | NOT_APPLICABLE | PROHIBITED |
| Co-PM | ALLOWED | READ_ONLY | READ_ONLY | PROHIBITED | NOT_APPLICABLE | PROHIBITED |
| Project Engineer | ALLOWED | READ_ONLY | READ_ONLY | PROHIBITED | NOT_APPLICABLE | PROHIBITED |
| Superintendent | ALLOWED | READ_ONLY | READ_ONLY | PROHIBITED | ALLOWED | PROHIBITED |
| Foreman | ALLOWED | READ_ONLY | READ_ONLY | PROHIBITED | ALLOWED | PROHIBITED |
| Field Leadership | ALLOWED | READ_ONLY | READ_ONLY | PROHIBITED | ALLOWED | PROHIBITED |
| Dispatch | ALLOWED | READ_ONLY | READ_ONLY | PROHIBITED | NOT_APPLICABLE | PROHIBITED |
| Transportation | ALLOWED | READ_ONLY | READ_ONLY | PROHIBITED | NOT_APPLICABLE | PROHIBITED |
| Driver | ALLOWED where scoped | NOT_APPLICABLE | PROHIBITED | PROHIBITED | NOT_APPLICABLE | PROHIBITED |
| Shop | ALLOWED | READ_ONLY | READ_ONLY | PROHIBITED | NOT_APPLICABLE | PROHIBITED |
| Equipment/Fleet | ALLOWED | READ_ONLY | READ_ONLY | PROHIBITED | NOT_APPLICABLE | PROHIBITED |
| Safety | ALLOWED | APPROVAL_REQUIRED | READ_ONLY | APPROVAL_REQUIRED | NOT_APPLICABLE | PROHIBITED |
| HR | ALLOWED | READ_ONLY | READ_ONLY | APPROVAL_REQUIRED | NOT_APPLICABLE | PROHIBITED |
| QA/QC | ALLOWED | APPROVAL_REQUIRED | READ_ONLY | APPROVAL_REQUIRED | NOT_APPLICABLE | PROHIBITED |
| Survey | ALLOWED | READ_ONLY | READ_ONLY | PROHIBITED | NOT_APPLICABLE | PROHIBITED |
| Accounting | ALLOWED | READ_ONLY | READ_ONLY | PROHIBITED | NOT_APPLICABLE | PROHIBITED |
| Qualifications/Training Manager | ALLOWED | READ_ONLY | READ_ONLY | APPROVAL_REQUIRED | NOT_APPLICABLE | PROHIBITED |
| Read-Only Leadership | READ_ONLY | READ_ONLY | READ_ONLY | PROHIBITED | NOT_APPLICABLE | PROHIBITED |
| System Automation | SYSTEM_DERIVED | SYSTEM_DERIVED | SYSTEM_DERIVED | PROHIBITED | NOT_APPLICABLE | SYSTEM_DERIVED |
| AI Assistant | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED | PROHIBITED |

## 8. Permanent Boundary Rules

- AI never approves, commits, publishes, reconciles, closes, certifies, or owns.
- Executives never rewrite field actuals.
- PMs never rewrite submitted Daily Report actuals.
- Foremen do not publish company schedule commitments unless explicitly delegated and approved.
- Shop controls repair/recovery state, not schedule truth.
- Dispatch controls assignments and movement, not work completion.
- Safety may block work through safety authority but cannot rewrite production truth.
- System Automation executes only deterministic, preapproved transitions.

## 9. Manual GitHub and Deployment Boundary

ONLY JAYMN MAY PHYSICALLY SAVE OR PUBLISH CHANGES TO GITHUB.
ONLY JAYMN MAY PHYSICALLY DEPLOY PREVIEW OR PRODUCTION.

Emergent roles, automation, or AI may not claim those manual actions occurred.

## 10. Certification and Traceability Cross-Reference

This role matrix is normatively linked to:
- stable identifiers in the Appendix §2
- lifecycle rules in the Appendix §3
- event envelope in the Appendix §4
- KPI/dashboard contracts in the Appendix §5
- notification contract in the Appendix §6
- brief contract in the Appendix §7
- security contract in the Appendix §8
- product identity contract in the Appendix §9
- manual deployment boundary in the Appendix §10