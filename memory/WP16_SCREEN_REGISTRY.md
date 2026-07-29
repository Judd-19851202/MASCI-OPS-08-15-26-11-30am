# WP16 Screen Registry

Date: 2026-07-29

## Purpose
Master index of every discoverable user-facing screen/surface in the current restored baseline. This document is observational only and does not make design decisions.

## Status legend
- `EXERCISED` — route was opened in preview during this audit and has a screenshot reference.
- `BLOCKED` — route rendered, but live audit evidence showed blocking API errors affecting the screen during capture.
- `UNKNOWN` — reserved for routes whose current state cannot be determined from available evidence.
- `NOT YET EXERCISED` — discoverable in source inventory, but not opened in preview during this audit.

## Admin

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `/admin` | Admin | Admin | Admin Operating System landing | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-ADMIN-HOME.jpeg | EXERCISED |
| `/admin/ai` | AI | Admin > AI | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/ai-configuration` | AI Configuration | Admin > AI Configuration | AI Configuration | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/ai-operations` | AI Operations | Admin > AI Operations | AI Operations | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/analytics` | Analytics | Admin > Analytics | Analytics | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/asset-admin` | Asset Admin | Admin > Asset Admin | Asset Admin | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/asset-mapping` | Asset Mapping | Admin > Asset Mapping | Asset Mapping | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/asset-spine` | Asset Spine | Admin > Asset Spine | Asset Spine | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/assets/:assetId` | Assets | Admin > Assets > Assetid | Assetid | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/assets/:assetRef/thread` | Assets | Admin > Assets > Assetref | Thread | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/audit` | Audit | Admin > Audit | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/audit-log` | Audit LOG | Admin > Audit LOG | Audit LOG | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/command-center` | Command Center | Admin > Command Center | Command Center | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/communications` | Communications | Admin > Communications | Communications | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/compliance` | Compliance | Admin > Compliance | Compliance | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/compliance-findings` | Compliance Findings | Admin > Compliance Findings | Compliance Findings | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/cost-registry` | Cost Registry | Admin > Cost Registry | Cost Registry | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/daily` | Daily | Admin > Daily | Daily | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/daily-reports` | Daily Reports | Admin > Daily Reports | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/daily/:id` | Daily | Admin > Daily > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/database` | Database | Admin > Database | Database | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/deploy-readiness` | Deploy Readiness | Admin > Deploy Readiness | Deploy Readiness | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/deploy-recovery` | Deploy Recovery | Admin > Deploy Recovery | Deploy Recovery | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/diagnostics` | Diagnostics | Admin > Diagnostics | Diagnostics | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/digest-config` | Digest Config | Admin > Digest Config | Digest Config | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/dispatch` | Dispatch | Admin > Dispatch | Dispatch | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/dls/day-1-debrief` | DLS | Admin > DLS > DAY 1 Debrief | DAY 1 Debrief | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/dls/shift-qr` | DLS | Admin > DLS > Shift QR | Shift QR | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/dls/week-1-debrief` | DLS | Admin > DLS > Week 1 Debrief | Week 1 Debrief | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/driver-intel/:driverKey` | Driver Intel | Admin > Driver Intel > Driverkey | Driverkey | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/email` | Email | Admin > Email | Email | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/employees/:id/history` | Employees | Admin > Employees > ID | History | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/equipment` | Equipment | Admin > Equipment | Equipment | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/equipment-inspections` | Equipment Inspections | Admin > Equipment Inspections | Equipment Inspections | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/equipment/:id` | Equipment | Admin > Equipment > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/equipment/:id/history` | Equipment | Admin > Equipment > ID | History | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/executive` | Executive | Admin > Executive | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/executive-intelligence` | Executive Intelligence | Admin > Executive Intelligence | Executive Intelligence | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/executive-operational-intelligence` | Executive Operational Intelligence | Admin > Executive Operational Intelligence | Executive Operational Intelligence | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/executive-overview` | Executive Overview | Admin > Executive Overview | Executive Overview | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/geofence-reconciliation` | Geofence Reconciliation | Admin > Geofence Reconciliation | Geofence Reconciliation | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance` | Governance | Admin > Governance | Enterprise governance dashboard | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-ADMIN-GOVERNANCE.jpeg | EXERCISED |
| `/admin/governance-trust` | Governance Trust | Admin > Governance Trust | Governance Trust | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/approval-flows` | Governance | Admin > Governance > Approval Flows | Approval Flows | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/audit` | Governance | Admin > Governance > Audit | Governance Audit | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/authority` | Governance | Admin > Governance > Authority | Authority | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/decisions` | Governance | Admin > Governance > Decisions | Decisions | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/delegations` | Governance | Admin > Governance > Delegations | Delegations | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/emergency-overrides` | Governance | Admin > Governance > Emergency Overrides | Emergency Overrides | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/health` | Governance | Admin > Governance > Health | Governance Health | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/identities` | Governance | Admin > Governance > Identities | Identities | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/legacy-health` | Governance | Admin > Governance > Legacy Health | Legacy Health | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/organization` | Governance | Admin > Governance > Organization | Organization | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/overview` | Governance | Admin > Governance > Overview | Governance Overview | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/permissions` | Governance | Admin > Governance > Permissions | Permissions | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/policies` | Governance | Admin > Governance > Policies | Policies | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/registry` | Governance | Admin > Governance > Registry | Registry | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/roles` | Governance | Admin > Governance > Roles | Roles | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/self-protection` | Governance | Admin > Governance > Self Protection | Self Protection | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/separation-of-duties` | Governance | Admin > Governance > Separation OF Duties | Separation OF Duties | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/governance/versions` | Governance | Admin > Governance > Versions | Versions | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/guidance-coverage` | Guidance Coverage | Admin > Guidance Coverage | Guidance Coverage | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/guide` | Guide | Admin > Guide | Guide | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/health` | Health | Admin > Health | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/hub_v1` | HUB V1 | Admin > HUB V1 | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/hub_v2` | HUB V2 | Admin > HUB V2 | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/identity-security` | Identity Security | Admin > Identity Security | Identity Security | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/incidents` | Incidents | Admin > Incidents | Incidents | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/incidents/:id` | Incidents | Admin > Incidents > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/inspections` | Inspections | Admin > Inspections | Inspections | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/inspections/:id` | Inspections | Admin > Inspections > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/integration-truth` | Integration Truth | Admin > Integration Truth | Integration Truth | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/integrations` | Integrations | Admin > Integrations | Integrations | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/jha` | JHA | Admin > JHA | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/jha-acknowledgements` | JHA Acknowledgements | Admin > JHA Acknowledgements | JHA Acknowledgements | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/jha-plans` | JHA Plans | Admin > JHA Plans | JHA Plans | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/jha-plans/poster` | JHA Plans | Admin > JHA Plans > Poster | Poster | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/jha/:id` | JHA | Admin > JHA > ID | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/jobs` | Jobs | Admin > Jobs | Jobs | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/jobs/:projectNumber/team` | Jobs | Admin > Jobs > Projectnumber | Team | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/leadership-equipment` | Leadership Equipment | Admin > Leadership Equipment | Leadership Equipment | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/leadership/records/:id` | Leadership | Admin > Leadership > Records | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/legacy-imports` | Legacy Imports | Admin > Legacy Imports | Legacy Imports | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/login` | Login | Admin > Login | Admin sign-in shell | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-ADMIN-LOGIN.jpeg | EXERCISED |
| `/admin/maintenance` | Maintenance | Admin > Maintenance | Maintenance | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/material-ledger-quality` | Material Ledger Quality | Admin > Material Ledger Quality | Material Ledger Quality | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/meetings` | Meetings | Admin > Meetings | Meetings | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/meetings/:id` | Meetings | Admin > Meetings > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/mfa` | MFA | Admin > MFA | MFA | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/occ` | OCC | Admin > OCC | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/ods-intelligence` | ODS Intelligence | Admin > ODS Intelligence | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/operational-intelligence` | Operational Intelligence | Admin > Operational Intelligence | Operational Intelligence | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/operational-intelligence/recipients` | Operational Intelligence | Admin > Operational Intelligence > Recipients | Recipients | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/operational-inventory` | Operational Inventory | Admin > Operational Inventory | Operational Inventory | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/operational-language` | Operational Language | Admin > Operational Language | Operational Language | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/operations-control` | Operations Control | Admin > Operations Control | Operations Control | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/operations-control/cases/:caseId` | Operations Control | Admin > Operations Control > Cases | Caseid | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/operations-dashboard` | Operations Dashboard | Admin > Operations Dashboard | Operations Dashboard | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/operations-events` | Operations Events | Admin > Operations Events | Operations Events | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/people` | People | Admin > People | People | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/photos` | Photos | Admin > Photos | Photos | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/platform-configuration` | Platform Configuration | Admin > Platform Configuration | Platform Configuration | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/platform-overview` | Platform Overview | Admin > Platform Overview | Admin Platform Overview | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/pnl` | PNL | Admin > PNL | PNL | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/posters/print-all` | Posters | Admin > Posters > Print ALL | Print ALL | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/preview-validation-identities` | Preview Validation Identities | Admin > Preview Validation Identities | Preview Validation Identities | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/profile` | Profile | Admin > Profile | Profile | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/project-identity` | Project Identity | Admin > Project Identity | Project Identity | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/project-staffing` | Project Staffing | Admin > Project Staffing | Project Staffing | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/promo-assets` | Promo Assets | Admin > Promo Assets | Promo Assets | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/qaqc` | Qaqc | Admin > Qaqc | Qaqc | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/qaqc/:id` | Qaqc | Admin > Qaqc > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/recovery` | Recovery | Admin > Recovery | Recovery | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/recovery-stream` | Recovery Stream | Admin > Recovery Stream | Recovery Stream | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/safety/issuance/:id` | Safety | Admin > Safety > Issuance | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/safety/training/:id` | Safety | Admin > Safety > Training | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/scheduler-runs` | Scheduler Runs | Admin > Scheduler Runs | Scheduler Runs | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/sessions` | Sessions | Admin > Sessions | Sessions | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/storage` | Storage | Admin > Storage | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/storage-recovery` | Storage Recovery | Admin > Storage Recovery | Storage Recovery | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/system` | System | Admin > System | System | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/system-health` | System Health | Admin > System Health | System Health | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/terminations` | Terminations | Admin > Terminations | Terminations | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/training` | Training | Admin > Training | Training | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/training-videos` | Training Videos | Admin > Training Videos | Training Videos | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/transportation/*` | Transportation | Admin > Transportation > ALL | ALL | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/trench-boxes` | Trench Boxes | Admin > Trench Boxes | Trench Boxes | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/trench-boxes/poster` | Trench Boxes | Admin > Trench Boxes > Poster | Poster | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/trench-safety` | Trench Safety | Admin > Trench Safety | Trench Safety | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/trench-safety-assets` | Trench Safety Assets | Admin > Trench Safety Assets | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/trench-safety/assets` | Trench Safety | Admin > Trench Safety > Assets | Assets | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/trench-safety/assets/:assetId` | Trench Safety | Admin > Trench Safety > Assets | Assetid | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/trench-safety/excavations` | Trench Safety | Admin > Trench Safety > Excavations | Excavations | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/trench-safety/field-reports` | Trench Safety | Admin > Trench Safety > Field Reports | Field Reports | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/trench-safety/repair-review` | Trench Safety | Admin > Trench Safety > Repair Review | Repair Review | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/trench-safety/reports` | Trench Safety | Admin > Trench Safety > Reports | Trench Safety Reports | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/trench-safety/tabulated-data` | Trench Safety | Admin > Trench Safety > Tabulated Data | Tabulated Data | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/trust-spine` | Trust Spine | Admin > Trust Spine | Trust Spine | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/admin/vendors/:vendorId/thread` | Vendors | Admin > Vendors > Vendorid | Thread | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/operations-control/cases` | Cases | Operations Control > Cases | Cases | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/operations-control/cases/:caseId` | Cases | Operations Control > Cases > Caseid | Caseid | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |

## PM

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `/pm` | PM | PM | PM center / assigned-project dashboard | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-PM-HOME.jpeg | EXERCISED |
| `/pm/change-password` | Change Password | PM > Change Password | Change Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/command-center` | Command Center | PM > Command Center | Command Center | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/crew-compliance` | Crew Compliance | PM > Crew Compliance | Crew Compliance | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/daily` | Daily | PM > Daily | Daily | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/daily/:id` | Daily | PM > Daily > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/due-today` | DUE Today | PM > DUE Today | DUE Today | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/equipment` | Equipment | PM > Equipment | Equipment | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/equipment/:id` | Equipment | PM > Equipment > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/field-leadership` | Field Leadership | PM > Field Leadership | Field Leadership | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/fleet` | Fleet | PM > Fleet | Fleet | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/holds` | Holds | PM > Holds | Holds | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/hub` | HUB | PM > HUB | HUB | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/hub_legacy` | HUB Legacy | PM > HUB Legacy | HUB Legacy | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/hub_v2` | HUB V2 | PM > HUB V2 | HUB V2 | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/incidents` | Incidents | PM > Incidents | Incidents | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/incidents/:id` | Incidents | PM > Incidents > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/inspections` | Inspections | PM > Inspections | Inspections | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/inspections/:id` | Inspections | PM > Inspections > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/jha-plans` | JHA Plans | PM > JHA Plans | JHA Plans | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/job/:projectNumber/team` | JOB | PM > JOB > Projectnumber | Team | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/jobs` | Jobs | PM > Jobs | Jobs | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/login` | Login | PM > Login | PM sign-in shell | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-PM-LOGIN.jpeg | EXERCISED |
| `/pm/meetings` | Meetings | PM > Meetings | Meetings | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/meetings/:id` | Meetings | PM > Meetings > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/monday-review` | Monday Review | PM > Monday Review | Monday Review | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/odr` | ODR | PM > ODR | ODR | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/operational-intelligence` | Operational Intelligence | PM > Operational Intelligence | Pm Operational Intelligence | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/people` | People | PM > People | People | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/photos` | Photos | PM > Photos | Photos | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/posters` | Posters | PM > Posters | Posters | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/project-schedule` | Project Schedule | PM > Project Schedule | Project Schedule | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/project-staffing` | Project Staffing | PM > Project Staffing | Project Staffing | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/project/:projectNumber` | Project | PM > Project > Projectnumber | Projectnumber | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/project/:projectNumber/thread` | Project | PM > Project > Projectnumber | Thread | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/projects-legacy/:projectNumber` | Projects Legacy | PM > Projects Legacy > Projectnumber | Projectnumber | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/projects/:projectNumber` | Projects | PM > Projects > Projectnumber | Projectnumber | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/qaqc` | Qaqc | PM > Qaqc | Qaqc | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/reset/:token` | Reset | PM > Reset > Token | Pm Reset Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/suppliers` | Suppliers | PM > Suppliers | Suppliers | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/trench-boxes` | Trench Boxes | PM > Trench Boxes | Trench Boxes | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/trench-safety` | Trench Safety | PM > Trench Safety | Trench Safety | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/trench-safety/assets` | Trench Safety | PM > Trench Safety > Assets | Assets | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/trench-safety/assets/:assetId` | Trench Safety | PM > Trench Safety > Assets | Assetid | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/trench-safety/excavations` | Trench Safety | PM > Trench Safety > Excavations | Excavations | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/trench-safety/reports` | Trench Safety | PM > Trench Safety > Reports | Trench Safety Reports | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/pm/trench-safety/tabulated-data` | Trench Safety | PM > Trench Safety > Tabulated Data | Tabulated Data | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |

## HR

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `/hr` | HR | HR | HR overview / attention dashboard | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-HR-HOME.jpeg | BLOCKED |
| `/hr/change-password` | Change Password | HR > Change Password | Change Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/daily-reports` | Daily Reports | HR > Daily Reports | Daily Reports | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/daily-reports/:id` | Daily Reports | HR > Daily Reports > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/driver-qualification` | Driver Qualification | HR > Driver Qualification | Driver Qualification | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/driver-qualification/import` | Driver Qualification | HR > Driver Qualification > Import | Import | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/driver/:driverKey` | Driver | HR > Driver > Driverkey | Driverkey | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/employee-accountability` | Employee Accountability | HR > Employee Accountability | Employee Accountability | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/employee-requests` | Employee Requests | HR > Employee Requests | Employee Requests | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/employees` | Employees | HR > Employees | Employee lifecycle list + filters | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-HR-EMPLOYEES.jpeg | BLOCKED |
| `/hr/employees/:empId/profile` | Employees | HR > Employees > Empid | Profile | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/employees/:id/accountability` | Employees | HR > Employees > ID | Accountability | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/employees/:id/thread` | Employees | HR > Employees > ID | Thread | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/field-leadership` | Field Leadership | HR > Field Leadership | Field Leadership | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/field-leadership-users` | Field Leadership Users | HR > Field Leadership Users | Field Leadership Users | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/forgot` | Forgot | HR > Forgot | Hr Forgot Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/historical-records/batches` | Historical Records | HR > Historical Records > Batches | Batches | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/historical-records/batches/:batchId` | Historical Records | HR > Historical Records > Batches | Batchid | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/historical-records/intake` | Historical Records | HR > Historical Records > Intake | Intake | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/historical-records/queue` | Historical Records | HR > Historical Records > Queue | Queue | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/hub_legacy` | HUB Legacy | HR > HUB Legacy | HUB Legacy | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/hub_v2` | HUB V2 | HR > HUB V2 | HUB V2 | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/incidents` | Incidents | HR > Incidents | Incidents | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/login` | Login | HR > Login | HR sign-in shell | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-HR-LOGIN.jpeg | EXERCISED |
| `/hr/motive-drivers` | Motive Drivers | HR > Motive Drivers | Motive Drivers | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/payroll-variance` | Payroll Variance | HR > Payroll Variance | Payroll Variance | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/qualifications` | Qualifications | HR > Qualifications | Qualifications | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/reset/:token` | Reset | HR > Reset > Token | Hr Reset Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/safety-records` | Safety Records | HR > Safety Records | Safety Records | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/time-off` | Time OFF | HR > Time OFF | Time OFF | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/time-verification` | Time Verification | HR > Time Verification | Time Verification | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/hr/training-records` | Training Records | HR > Training Records | Training Records | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |

## Safety

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `/safety-portal` | Safety Portal | Safety Portal | Safety attention dashboard | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-SAFETY-HOME.jpeg | EXERCISED |
| `/safety-portal/audits` | Audits | Safety Portal > Audits | Audits | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/change-password` | Change Password | Safety Portal > Change Password | Change Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/corrective-actions` | Corrective Actions | Safety Portal > Corrective Actions | Corrective Actions | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/digest` | Digest | Safety Portal > Digest | Digest | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/documents` | Documents | Safety Portal > Documents | Documents | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/driver/:driverKey` | Driver | Safety Portal > Driver > Driverkey | Driverkey | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/employees` | Employees | Safety Portal > Employees | Employees | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/fire-extinguishers` | Fire Extinguishers | Safety Portal > Fire Extinguishers | Fire Extinguishers | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/fire-extinguishers/import` | Fire Extinguishers | Safety Portal > Fire Extinguishers > Import | Import | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/fleet` | Fleet | Safety Portal > Fleet | Fleet | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/forgot-password` | Forgot Password | Safety Portal > Forgot Password | Safety Forgot Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/forms-records` | Forms Records | Safety Portal > Forms Records | Forms Records | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/hub_legacy` | HUB Legacy | Safety Portal > HUB Legacy | HUB Legacy | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/hub_v2` | HUB V2 | Safety Portal > HUB V2 | HUB V2 | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/incidents` | Incidents | Safety Portal > Incidents | Incidents | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/incidents/:id` | Incidents | Safety Portal > Incidents > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/inspections` | Inspections | Safety Portal > Inspections | Inspections | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/inspections/:id` | Inspections | Safety Portal > Inspections > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/jha-plans` | JHA Plans | Safety Portal > JHA Plans | JHA Plans | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/library` | Library | Safety Portal > Library | Library | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/login` | Login | Safety Portal > Login | Safety sign-in shell | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-SAFETY-LOGIN.jpeg | EXERCISED |
| `/safety-portal/meetings` | Meetings | Safety Portal > Meetings | Meetings | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/meetings/:id` | Meetings | Safety Portal > Meetings > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/reports` | Reports | Safety Portal > Reports | Safety Portal Reports | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/reset/:token` | Reset | Safety Portal > Reset > Token | Safety Reset Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/training` | Training | Safety Portal > Training | Training | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/trench-safety` | Trench Safety | Safety Portal > Trench Safety | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/trench-safety/assets` | Trench Safety | Safety Portal > Trench Safety > Assets | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety-portal/trench-safety/tabulated-data` | Trench Safety | Safety Portal > Trench Safety > Tabulated Data | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/cards` | Cards | Safety > Cards | Field Safety Cards | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/cases/:caseId` | Cases | Safety > Cases > Caseid | Safety Case Workspace | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/cases/:caseId/executive-report` | Cases | Safety > Cases > Caseid | Executive Case Report | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/cases/:caseId/reports/:reportType` | Cases | Safety > Cases > Caseid | Incident Report Viewer | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/executive-intelligence` | Executive Intelligence | Safety > Executive Intelligence | Executive Intelligence | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/forms` | Forms | Safety > Forms | Safety Forms Hub | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/forms/equipment-issuance/:id` | Forms | Safety > Forms > Equipment Issuance | View Safety Form | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/forms/equipment-issuance/:id/return` | Forms | Safety > Forms > Equipment Issuance | Return Equipment | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/forms/equipment-issuance/new` | Forms | Safety > Forms > Equipment Issuance | New Safety Equipment Issuance | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/forms/equipment-training/:id` | Forms | Safety > Forms > Equipment Training | View Safety Form | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/forms/equipment-training/new` | Forms | Safety > Forms > Equipment Training | New Safety Equipment Training | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/forms/login` | Forms | Safety > Forms > Login | Safety Forms Login | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/incidents/:caseId/thread` | Incidents | Safety > Incidents > Caseid | Safety Incident Thread | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/inspections/new` | Inspections | Safety > Inspections > NEW | Inspections NEW | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/jha` | JHA | Safety > JHA | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/trench-boxes` | Trench Boxes | Safety > Trench Boxes | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/trench-safety` | Trench Safety | Safety > Trench Safety | Trench Safety | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/trench-safety/assets` | Trench Safety | Safety > Trench Safety > Assets | Assets | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/trench-safety/assets/:assetId` | Trench Safety | Safety > Trench Safety > Assets | Assetid | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/trench-safety/excavations` | Trench Safety | Safety > Trench Safety > Excavations | Excavations | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/trench-safety/field-reports` | Trench Safety | Safety > Trench Safety > Field Reports | Field Reports | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/trench-safety/repair-review` | Trench Safety | Safety > Trench Safety > Repair Review | Repair Review | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/trench-safety/reports` | Trench Safety | Safety > Trench Safety > Reports | Trench Safety Reports | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety/trench-safety/tabulated-data` | Trench Safety | Safety > Trench Safety > Tabulated Data | Tabulated Data | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |

## Dispatch

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `/dispatch-portal` | Dispatch Portal | Dispatch Portal | Transportation mission control / live map | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-DISPATCH-HOME.jpeg | EXERCISED |
| `/dispatch-portal/board` | Board | Dispatch Portal > Board | Board | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/dispatch-portal/change-password` | Change Password | Dispatch Portal > Change Password | Change Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/dispatch-portal/command` | Command | Dispatch Portal > Command | Command | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/dispatch-portal/driver-qualification` | Driver Qualification | Dispatch Portal > Driver Qualification | Driver Qualification | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/dispatch-portal/driver/:driverKey` | Driver | Dispatch Portal > Driver > Driverkey | Driverkey | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/dispatch-portal/fleet` | Fleet | Dispatch Portal > Fleet | Fleet | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/dispatch-portal/forgot-password` | Forgot Password | Dispatch Portal > Forgot Password | Dispatch Forgot Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/dispatch-portal/haul-ledger` | Haul Ledger | Dispatch Portal > Haul Ledger | Haul Ledger | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/dispatch-portal/hub_legacy` | HUB Legacy | Dispatch Portal > HUB Legacy | HUB Legacy | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/dispatch-portal/hub_v2` | HUB V2 | Dispatch Portal > HUB V2 | HUB V2 | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/dispatch-portal/login` | Login | Dispatch Portal > Login | Dispatch sign-in shell | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-DISPATCH-LOGIN.jpeg | EXERCISED |
| `/dispatch-portal/map` | MAP | Dispatch Portal > MAP | MAP | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/dispatch-portal/reset/:token` | Reset | Dispatch Portal > Reset > Token | Dispatch Reset Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |

## Shop

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `/shop` | Shop | Shop | Shop command center | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-SHOP-HOME.jpeg | EXERCISED |
| `/shop/asset-care` | Asset Care | Shop > Asset Care | Asset Care | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/change-password` | Change Password | Shop > Change Password | Change Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/equipment` | Equipment | Shop > Equipment | Equipment | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/equipment/:id` | Equipment | Shop > Equipment > ID | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/fleet` | Fleet | Shop > Fleet | Fleet | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/fuel-lube` | Fuel Lube | Shop > Fuel Lube | Fuel Lube | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/fuel-lube/:visitId` | Fuel Lube | Shop > Fuel Lube > Visitid | Visitid | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/fuel-lube/new` | Fuel Lube | Shop > Fuel Lube > NEW | Fuel Lube NEW | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/hub_legacy` | HUB Legacy | Shop > HUB Legacy | HUB Legacy | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/hub_v2` | HUB V2 | Shop > HUB V2 | HUB V2 | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/login` | Login | Shop > Login | Shop sign-in shell | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-SHOP-LOGIN.jpeg | EXERCISED |
| `/shop/manager/queue` | Manager | Shop > Manager > Queue | Queue | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/me` | ME | Shop > ME | ME | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/pm` | PM | Shop > PM | PM | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/pm/schedules` | PM | Shop > PM > Schedules | Schedules | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/pm/templates` | PM | Shop > PM > Templates | Templates | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/pm/work-orders` | PM | Shop > PM > Work Orders | Work Orders | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/pm/work-orders/:id` | PM | Shop > PM > Work Orders | ID | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/reset/:token` | Reset | Shop > Reset > Token | Shop Reset Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/service-truck-reconciliation` | Service Truck Reconciliation | Shop > Service Truck Reconciliation | Service Truck Reconciliation | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/service-truck-reconciliation/:recId` | Service Truck Reconciliation | Shop > Service Truck Reconciliation > Recid | Recid | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/service-truck-reconciliation/new` | Service Truck Reconciliation | Shop > Service Truck Reconciliation > NEW | Service Truck Reconciliation NEW | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/trench-safety-repairs` | Trench Safety Repairs | Shop > Trench Safety Repairs | Trench Safety Repairs | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/units/:unitNumber/history` | Units | Shop > Units > Unitnumber | History | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shop/units/history` | Units | Shop > Units > History | History | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |

## Field Leadership

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `/field-leadership` | Field Leadership | Field Leadership | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/field-leadership/portal` | Portal | Field Leadership > Portal | Portal | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/field-leadership/portal/change-password` | Portal | Field Leadership > Portal > Change Password | Change Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/field-leadership/portal/dashboard` | Portal | Field Leadership > Portal > Dashboard | Portal Dashboard | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/field-leadership/portal/driver-qualification` | Portal | Field Leadership > Portal > Driver Qualification | Driver Qualification | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/field-leadership/portal/login` | Portal | Field Leadership > Portal > Login | Field Leadership Portal Login | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/leadership` | Leadership | Leadership | Field Leadership Hub | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/leadership/:kind/new` | Kind | Leadership > Kind > NEW | Field Leadership Form Page | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/leadership/hub_v2` | HUB V2 | Leadership > HUB V2 | Leadership Hub V2 | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/leadership/login` | Login | Leadership > Login | Field Leadership Portal Login | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/leadership/records` | Records | Leadership > Records | Field Leadership Records | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/leadership/records/:id` | Records | Leadership > Records > ID | Field Leadership View | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |

## Training / Guidance

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `/guidance` | Guidance | Guidance | Operational Guidance Center | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/guidance/:articleId` | Articleid | Guidance > Articleid | Operational Guidance Center | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/guidance/section/:sectionId` | Section | Guidance > Section > Sectionid | Operational Guidance Center | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/training` | Training | Training | Training Hub | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/training-hub` | Training HUB | Training HUB | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/training/:track` | Track | Training > Track | Training Track | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/training/:track/packet` | Track | Training > Track > Packet | Training Packet Download | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/training/:track/poster` | Track | Training > Track > Poster | Training Qr Poster | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |

## Transportation Ops wrapper

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `/transport-invite/:token` | Token | Transport Invite > Token | External Carrier Invite | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/transport-verify/:cnum` | Cnum | Transport Verify > Cnum | Certificate Verify | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/transportation-operations/*` | ALL | Transportation Operations > ALL | ALL | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |

## Transportation Ops child

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `academy (mounted under /admin/transportation/* and /transportation-operations/*)` | Academy | Transportation Ops > Academy | Transportation Academy | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `academy/:moduleKey (mounted under /admin/transportation/* and /transportation-operations/*)` | Academy | Transportation Ops > Academy | Transportation Academy Module | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `administration/audit (mounted under /admin/transportation/* and /transportation-operations/*)` | Administration | Transportation Ops > Administration | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `assignments (mounted under /admin/transportation/* and /transportation-operations/*)` | Assignments | Transportation Ops > Assignments | Assignments View | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `audit (mounted under /admin/transportation/* and /transportation-operations/*)` | Audit | Transportation Ops > Audit | Audit Timeline | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `carriers (mounted under /admin/transportation/* and /transportation-operations/*)` | Carriers | Transportation Ops > Carriers | Carriers List | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `carriers/:id (mounted under /admin/transportation/* and /transportation-operations/*)` | Carriers | Transportation Ops > Carriers | Carrier Workspace | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `certificates (mounted under /admin/transportation/* and /transportation-operations/*)` | Certificates | Transportation Ops > Certificates | Certificates View | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `cleanup (mounted under /admin/transportation/* and /transportation-operations/*)` | Cleanup | Transportation Ops > Cleanup | Cleanup Companion Panel | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `command-queue/* (mounted under /admin/transportation/* and /transportation-operations/*)` | Command Queue | Transportation Ops > Command Queue | Command Queue Center | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `compliance (mounted under /admin/transportation/* and /transportation-operations/*)` | Compliance | Transportation Ops > Compliance | Compliance Dashboard | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `compliance/documents (mounted under /admin/transportation/* and /transportation-operations/*)` | Compliance | Transportation Ops > Compliance | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `compliance/rate-schedules (mounted under /admin/transportation/* and /transportation-operations/*)` | Compliance | Transportation Ops > Compliance | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `dispatch (mounted under /admin/transportation/* and /transportation-operations/*)` | Dispatch | Transportation Ops > Dispatch | Dispatch Bridge Workspace | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `documents (mounted under /admin/transportation/* and /transportation-operations/*)` | Documents | Transportation Ops > Documents | Document Center | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `drivers (mounted under /admin/transportation/* and /transportation-operations/*)` | Drivers | Transportation Ops > Drivers | Drivers List | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `drivers/:id (mounted under /admin/transportation/* and /transportation-operations/*)` | Drivers | Transportation Ops > Drivers | Driver Workspace | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `emails (mounted under /admin/transportation/* and /transportation-operations/*)` | Emails | Transportation Ops > Emails | Email Routes Panel | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `fleet (mounted under /admin/transportation/* and /transportation-operations/*)` | Fleet | Transportation Ops > Fleet | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `fleet/inspections (mounted under /admin/transportation/* and /transportation-operations/*)` | Fleet | Transportation Ops > Fleet | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `fleet/trucks (mounted under /admin/transportation/* and /transportation-operations/*)` | Fleet | Transportation Ops > Fleet | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `forecast (mounted under /admin/transportation/* and /transportation-operations/*)` | Forecast | Transportation Ops > Forecast | Compliance Forecast | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `health (mounted under /admin/transportation/* and /transportation-operations/*)` | Health | Transportation Ops > Health | Automation Health | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `inspections (mounted under /admin/transportation/* and /transportation-operations/*)` | Inspections | Transportation Ops > Inspections | Inspection Center | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `intelligence/* (mounted under /admin/transportation/* and /transportation-operations/*)` | Intelligence | Transportation Ops > Intelligence | Intelligence Center | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `learning (mounted under /admin/transportation/* and /transportation-operations/*)` | Learning | Transportation Ops > Learning | Learning Loop Panel | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `live-operations (mounted under /admin/transportation/* and /transportation-operations/*)` | Live Operations | Transportation Ops > Live Operations | Live Operations Workspace | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `modules (mounted under /admin/transportation/* and /transportation-operations/*)` | Modules | Transportation Ops > Modules | Module Manager | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `modules/:mid (mounted under /admin/transportation/* and /transportation-operations/*)` | Modules | Transportation Ops > Modules | Module Detail | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `orientation/* (mounted under /admin/transportation/* and /transportation-operations/*)` | Orientation | Transportation Ops > Orientation | Orientation Center | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `predictions (mounted under /admin/transportation/* and /transportation-operations/*)` | Predictions | Transportation Ops > Predictions | Predictions Panel | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `rate-schedules (mounted under /admin/transportation/* and /transportation-operations/*)` | Rate Schedules | Transportation Ops > Rate Schedules | Rate Schedule Center | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `recommendations (mounted under /admin/transportation/* and /transportation-operations/*)` | Recommendations | Transportation Ops > Recommendations | Recommendations Panel | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `reports (mounted under /admin/transportation/* and /transportation-operations/*)` | Reports | Transportation Ops > Reports | Reports View | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `trucks (mounted under /admin/transportation/* and /transportation-operations/*)` | Trucks | Transportation Ops > Trucks | Trucks List | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `trucks/:id (mounted under /admin/transportation/* and /transportation-operations/*)` | Trucks | Transportation Ops > Trucks | Truck Workspace | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |

## Driver

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `/d/:token` | Token | D > Token | Driver Magic Landing | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/driver` | Driver | Driver | Driver Shift | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/shift` | Shift | Shift | Shift Start | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |

## Executive

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `/executive` | Executive | Executive | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/executive-dashboard` | Executive Dashboard | Executive Dashboard | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/executive/ods-intelligence` | ODS Intelligence | Executive > ODS Intelligence | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |

## Dev

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `/dev` | DEV | DEV | DEV | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/dev/login` | Login | DEV > Login | Dev Login | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |

## Public / Shared

| Route / URL | Module | Parent navigation | Primary purpose | Mobile/Desktop availability | Screenshot reference | Audit status |
| --- | --- | --- | --- | --- | --- | --- |
| `*` | fallback | Root > Fallback | Catch-all / not found fallback | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/` | Hub | Root > Hub | Platform public hub / launch surface | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-PUBLIC-HUB.jpeg | EXERCISED |
| `/_internal/design-system` | Design System | Internal > Design System | Design System | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/_internal/hr-v2-preview` | HR V2 Preview | Internal > HR V2 Preview | HR V2 Preview | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/_internal/pm-v2-preview` | PM V2 Preview | Internal > PM V2 Preview | PM V2 Preview | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/_internal/v2-compare/:portal` | V2 Compare | Internal > V2 Compare > Portal | Portal | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/_internal/v2-index` | V2 Index | Internal > V2 Index | V2 Index | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/access-denied` | Access Denied | Access Denied | Access Denied | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/app/*` | ALL | APP > ALL | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/asset-transfers` | Asset Transfers | Asset Transfers | Asset Transfers | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/change-password` | Change Password | Change Password | Directory Change Password | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/cheat-sheet` | Cheat Sheet | Cheat Sheet | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/cheatsheet` | Cheatsheet | Cheatsheet | Poster Error Boundary | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/constraints` | Constraints | Constraints | Constraints | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/constraints/:id` | ID | Constraints > ID | Constraint Detail | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/constraints/new` | NEW | Constraints > NEW | New Constraint | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/daily` | Daily | Daily | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/daily-report/v1` | V1 | Daily Report > V1 | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/daily-report/v2` | V2 | Daily Report > V2 | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/daily-report/v3` | V3 | Daily Report > V3 | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/daily-reports` | Daily Reports | Daily Reports | Daily Reports | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/daily-reports/:id` | ID | Daily Reports > ID | Redirect With Id | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/daily-reports/new` | NEW | Daily Reports > NEW | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/daily/:id` | ID | Daily > ID | Redirect With Id | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/daily/new` | NEW | Daily > NEW | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/daily/submit` | Submit | Daily > Submit | Public daily report authoring flow | Desktop exercised · Mobile not yet exercised | /app/memory/wp16_evidence/WP16-EVID-PUBLIC-DAILY-FORM.jpeg | EXERCISED |
| `/daily/v1` | V1 | Daily > V1 | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/daily/v2` | V2 | Daily > V2 | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/daily/v3` | V3 | Daily > V3 | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/document-expirations` | Document Expirations | Document Expirations | Document Expirations | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/equipment/:id` | ID | Equipment > ID | Redirect With Id | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/equipment/new` | NEW | Equipment > NEW | New Equipment Inspection | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/equipment/submit` | Submit | Equipment > Submit | New Equipment Inspection | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/field` | Field | Field | Field Section | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/field/calculators` | Calculators | Field > Calculators | Material Calculators | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/fl` | FL | FL | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/fleet` | Fleet | Fleet | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/fleet/dvir/new` | Dvir | Fleet > Dvir > NEW | New Fleet DVIR | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/fleet/dvir/submit` | Dvir | Fleet > Dvir > Submit | New Fleet DVIR | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/fleet/dvir/submitted/:id` | Dvir | Fleet > Dvir > Submitted | Fleet DVIRConfirmation | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/fleet/unit/:unit_number` | Unit | Fleet > Unit > Unit Number | Unit Number | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/fleet/weekly-emergency/new` | Weekly Emergency | Fleet > Weekly Emergency > NEW | New Fleet DVIR | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/fleet/weekly-lead/new` | Weekly Lead | Fleet > Weekly Lead > NEW | New Fleet DVIR | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/incidents` | Incidents | Incidents | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/incidents/:id` | ID | Incidents > ID | Redirect With Id | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/incidents/new` | NEW | Incidents > NEW | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/incidents/report` | Report | Incidents > Report | Incident Report | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/incidents/submit` | Submit | Incidents > Submit | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/inspect/:id` | ID | Inspect > ID | Redirect With Id | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/inspect/new` | NEW | Inspect > NEW | Inspection Legacy Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/inspections` | Inspections | Inspections | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/inspections/:id` | ID | Inspections > ID | Redirect With Id | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/inspections/new` | NEW | Inspections > NEW | Inspection Legacy Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/inspections/submit` | Submit | Inspections > Submit | Inspection Legacy Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/jha` | JHA | JHA | Jha Plans Hub | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/jha/new` | NEW | JHA > NEW | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/jha/submit` | Submit | JHA > Submit | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/legal/privacy` | Privacy | Legal > Privacy | Privacy Policy | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/legal/terms` | Terms | Legal > Terms | Terms Of Service | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/meetings` | Meetings | Meetings | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/meetings/:id` | ID | Meetings > ID | Redirect With Id | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/meetings/new` | NEW | Meetings > NEW | New Meeting | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/meetings/submit` | Submit | Meetings > Submit | New Meeting | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/near-miss` | Near Miss | Near Miss | Near Miss Kiosk | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/notifications` | Notifications | Notifications | Notifications Digest | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/odr/:id` | ID | ODR > ID | Odr Detail | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/odr/:id/done` | ID | ODR > ID > Done | Odr Done | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/odr/center` | Center | ODR > Center | Odr Center | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/odr/new` | NEW | ODR > NEW | Odr New | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/odr/public/:doc_id` | Public | ODR > Public > DOC ID | Odr Public Viewer | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/operational-records` | Operational Records | Operational Records | Operational Records | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/operations-actions` | Operations Actions | Operations Actions | Operations Actions | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/operations-actions/:id` | ID | Operations Actions > ID | Operations Action Detail | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/operations-actions/new` | NEW | Operations Actions > NEW | Operations Action New | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/operations-center` | Operations Center | Operations Center | Operations Center | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/operations-map` | Operations MAP | Operations MAP | Operations MAP | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/ops-training` | OPS Training | OPS Training | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/ops-training/:slug` | Slug | OPS Training > Slug | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/po-requests` | PO Requests | PO Requests | Po Requests | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/project-health` | Project Health | Project Health | Project Health | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/qa-qc` | QA QC | QA QC | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/qaqc` | Qaqc | Qaqc | Qaqc Section | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/qaqc/:id` | ID | Qaqc > ID | View Qaqc Inspection | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/qaqc/:slug/new` | Slug | Qaqc > Slug > NEW | New Qaqc Inspection | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/reports/daily/new` | Daily | Reports > Daily > NEW | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/revise/:token` | Token | Revise > Token | Revise | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/safety` | Safety | Safety | Safety Section | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/sign-in` | Sign IN | Sign IN | Sign In | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/submit` | Submit | Submit | Inspection Legacy Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/tasks` | Tasks | Tasks | Tasks | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/thank-you` | Thank YOU | Thank YOU | Thank You | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/time-off/public/:token` | Public | Time OFF > Public > Token | Public Time Off | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/trench-boxes` | Trench Boxes | Trench Boxes | Redirect | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/trench-safety` | Trench Safety | Trench Safety | Public Trench Safety Dashboard | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/trench-safety/assets/:assetId` | Assets | Trench Safety > Assets > Assetid | Trench Safety Qr Landing | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/trench-safety/excavation/new` | Excavation | Trench Safety > Excavation > NEW | Public Excavation Form | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/trench-safety/references` | References | Trench Safety > References | Public Trench Safety References | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/trench-safety/report` | Report | Trench Safety > Report | Public Trench Safety Report | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |
| `/trench-safety/tabulated-data` | Tabulated Data | Trench Safety > Tabulated Data | Public Trench Safety Tabulated Data | Desktop not yet exercised · Mobile not yet exercised | — | NOT YET EXERCISED |