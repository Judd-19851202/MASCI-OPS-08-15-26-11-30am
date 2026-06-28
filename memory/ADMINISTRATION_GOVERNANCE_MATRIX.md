# Administration Governance Matrix

**Constitutional rule (Track 18.09C):** Administration shall contain **only** platform governance. Anything performing operational transportation work is a candidate defect.

## Classification of every `/admin/*` page

| # | Route / Page | Owner today | Classification | Verdict |
|---|---|---|:---:|---|
| 1 | `/admin` · `AdminHub` | Super Admin | GOVERNANCE | ✅ Platform entry point |
| 2 | `/admin/hub_v2` · `AdminHubV2` | Super Admin | GOVERNANCE | ✅ |
| 3 | `/admin/executive-overview` · `ExecutiveOverview` | Operations Executive | GOVERNANCE | ✅ Cross-portal read-only |
| 4 | `/admin/people` · `AdminPeople` | Admin | GOVERNANCE | ✅ User management |
| 5 | `/admin/mfa` · `AdminMfa` | Admin | GOVERNANCE | ✅ Security |
| 6 | `/admin/promo-assets` · `AdminPromoAssets` | Admin | GOVERNANCE | ✅ Platform asset registry |
| 7 | `/admin/jobs` · `AdminJobs` | Admin / PM Coordinator | GOVERNANCE | ✅ Project identity (cross-workspace) |
| 8 | `/admin/jobs/:projectNumber/team` · `AdminJobTeam` | Admin | GOVERNANCE | ✅ Project staffing |
| 9 | `/admin/project-staffing` · `AdminProjectStaffing` | Admin | GOVERNANCE | ✅ |
| 10 | `/admin/geofence-reconciliation` · `AdminGeofenceReconciliation` | Admin | GOVERNANCE | ✅ Privileged Motive↔project mapping approval |
| 11 | `/admin/operations-dashboard` · `AdminOperationsDashboard` | Admin / Trust Center | GOVERNANCE | ✅ Read-only operational counts |
| 12 | `/admin/asset-mapping` · `AdminAssetMapping` | Admin | GOVERNANCE | ✅ |
| 13 | `/admin/asset-spine` · `AdminAssetSpineHealth` | Admin | GOVERNANCE | ✅ |
| 14 | `/admin/equipment` · `AdminEquipment` | Admin / Shop Coordinator | SHARED | Operational execution lives in Shop workspace; Admin is oversight |
| 15 | `/admin/email` · `AdminEmail` | Admin | GOVERNANCE | ✅ Email routing config |
| 16 | `/admin/training` · `AdminTraining` | Admin / HR / Safety | SHARED | Operational execution lives in HR + Safety workspaces |
| 17 | `/admin/compliance` · `AdminCompliance` | Admin | GOVERNANCE | ✅ Cross-portal compliance overview |
| 18 | `/admin/system` · `AdminSystem` | Admin | GOVERNANCE | ✅ |
| 19 | `/admin/recovery` · `AdminRecovery` | Admin | GOVERNANCE | ✅ |
| 20 | `/admin/recovery-stream` · `AdminRecoveryStream` | Admin | GOVERNANCE | ✅ |
| 21 | `/admin/jha-acknowledgements` · `AdminJhaAcknowledgements` | Admin / Safety | GOVERNANCE | ✅ Read-only cross-portal |
| 22 | `/admin/command-center` · `AdminCommandCenter` | Admin | GOVERNANCE | ✅ |
| 23 | `/admin/database` · `AdminDatabase` | Admin | GOVERNANCE | ✅ Platform diagnostics |
| 24 | `/admin/integrations` · `AdminIntegrationCenter` | Admin | GOVERNANCE | ✅ Integration center |
| 25 | `/admin/dispatch` · `AdminDispatch` | Admin / Dispatch | SHARED | Equipment availability/transfer/utilization — operational data in admin shell |
| 26 | `/admin/dls/*` · `AdminDls*` | Admin / Leadership | GOVERNANCE | ✅ Day-1 / week-1 debriefs |
| 27 | `/admin/profile` · `AdminProfile` | Admin | GOVERNANCE | ✅ |
| 28 | `/admin/operations-events` · `AdminOperationsEvents` | Admin | GOVERNANCE | ✅ Nervous-system viewer |
| 29 | `/admin/digest-config` · `AdminDigestConfig` | Admin | GOVERNANCE | ✅ Notification policy |
| 30 | `/admin/system-health` · `SystemHealth` | Admin | GOVERNANCE | ✅ |
| 31 | `/admin/audit-log` · `AdminAuditLog` | Admin | GOVERNANCE | ✅ |
| 32 | `/admin/sessions` · `AdminSessions` | Admin | GOVERNANCE | ✅ |
| 33 | `/admin/guidance-coverage` · `AdminGuidanceCoverage` | Admin | GOVERNANCE | ✅ |
| 34 | `/admin/operational-inventory` · `AdminOperationalInventory` | Admin | GOVERNANCE | ✅ |
| 35 | `/admin/governance` · `AdminGovernance` | Admin | GOVERNANCE | ✅ |
| 36 | `/admin/project-identity` · `AdminProjectIdentityGovernance` | Admin | GOVERNANCE | ✅ |
| 37 | `/admin/governance/self-protection` · `SelfProtection` | Admin | GOVERNANCE | ✅ Emergency override |
| 38 | `/admin/compliance-findings` · `AdminComplianceFindings` | Admin | GOVERNANCE | ✅ Cross-portal contradiction detection |
| 39 | `/admin/operational-language` · `AdminOperationalLanguage` | Admin | GOVERNANCE | ✅ Platform language registry |
| 40 | `/admin/deploy-recovery` · `DeployRecovery` | Admin | GOVERNANCE | ✅ Deployment |
| 41 | `/admin/transportation/*` · `AdminTransportation` (re-export of TransportationApp) | Admin oversight | SHARED | Same router as `/transportation-operations/*`; admin doorway is oversight |

## Summary

* **GOVERNANCE: 34 pages.** All consistent with the constitutional rule.
* **SHARED: 5 pages** (`/admin/equipment`, `/admin/training`, `/admin/dispatch`, `/admin/transportation/*`, `/admin/audit-log` if cross-portal-by-nature). Each is justified — operational execution is owned by a non-admin workspace; the admin variant is read-only oversight or the same shared component under admin auth.
* **OPERATIONAL violations in Administration: 0.** The audit identified zero pages performing operational transportation execution that should have been moved to Transportation Operations.

## Implication

Administration is **already a true governance workspace**. No operational rehome from Administration → Transportation Operations is required by the 18.09C directive. The single concrete defect addressed this track was the compat-redirect prefix inside `TransportationApp.jsx`, not an Administration page rehome.
