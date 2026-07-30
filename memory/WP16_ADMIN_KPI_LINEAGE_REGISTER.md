# WP16 Admin KPI Lineage Register

Date: 2026-07-30

| KPI ID | Route | Visible KPI name | Frontend component | API endpoint | Backend handler | Data source / collection | Filters / formula | Authoritative system of record | Refresh / cache behavior | Reconciled value | Truth status | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KPI-0001 | `/admin` | HEALTHY | AdminOS | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminOS.jsx | — |
| KPI-0002 | `/admin` | Storage & Recovery | AdminOS | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminOS.jsx | — |
| KPI-0003 | `/admin/executive-overview` | HEALTHY | ExecutiveOverview | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from ExecutiveOverview.jsx | — |
| KPI-0004 | `/admin/mfa` | Super-admin MFA enrollment and recovery. | AdminMfa | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminMfa.jsx | — |
| KPI-0005 | `/admin/geofence-reconciliation` | Total | AdminGeofenceReconciliation | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminGeofenceReconciliation.jsx | — |
| KPI-0006 | `/admin/operations-control/cases/:caseId` | Variance / recovery | OperationsControlCaseDetail | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from OperationsControlCaseDetail.jsx | — |
| KPI-0007 | `/admin/asset-spine` | Total Assets | AdminAssetSpineHealth | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminAssetSpineHealth.jsx | — |
| KPI-0008 | `/admin/asset-spine` | Motive Coverage | AdminAssetSpineHealth | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminAssetSpineHealth.jsx | — |
| KPI-0009 | `/admin/compliance` | Compliance & Audits | AdminCompliance | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminCompliance.jsx | — |
| KPI-0010 | `/admin/system` | System & Backups | AdminSystem | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminSystem.jsx | — |
| KPI-0011 | `/admin/ai-configuration` | AI Health (Live Ping) | AdminAIConfiguration | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminAIConfiguration.jsx | — |
| KPI-0012 | `/admin/recovery` | Storage & Recovery | AdminRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminRecovery.jsx | — |
| KPI-0013 | `/admin/recovery` | Recovery Posture | AdminRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminRecovery.jsx | — |
| KPI-0014 | `/admin/recovery` | Read-only recovery dashboard · polls every 30s. | AdminRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminRecovery.jsx | — |
| KPI-0015 | `/admin/recovery` | Backup Trust Score | AdminRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminRecovery.jsx | — |
| KPI-0016 | `/admin/recovery` | Archive count | AdminRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminRecovery.jsx | — |
| KPI-0017 | `/admin/recovery` | Bucket usage | AdminRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminRecovery.jsx | — |
| KPI-0018 | `/admin/storage-recovery` | Disk Health | AdminStorageRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminStorageRecovery.jsx | — |
| KPI-0019 | `/admin/storage-recovery` | Cloudflare R2 Health | AdminStorageRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminStorageRecovery.jsx | — |
| KPI-0020 | `/admin/storage-recovery` | Backup Health | AdminStorageRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminStorageRecovery.jsx | — |
| KPI-0021 | `/admin/storage-recovery` | Recovery Readiness | AdminStorageRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminStorageRecovery.jsx | — |
| KPI-0022 | `/admin/storage-recovery` | Storage & Recovery | AdminStorageRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminStorageRecovery.jsx | — |
| KPI-0023 | `/admin/storage-recovery` | R2 Bucket Health | AdminStorageRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminStorageRecovery.jsx | — |
| KPI-0024 | `/admin/storage-recovery` | R2 Health Refresh | AdminStorageRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminStorageRecovery.jsx | — |
| KPI-0025 | `/admin/storage-recovery` | Backup Health Refresh | AdminStorageRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminStorageRecovery.jsx | — |
| KPI-0026 | `/admin/storage-recovery` | R2 latency histogram surfaced in OCC | AdminStorageRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminStorageRecovery.jsx | — |
| KPI-0027 | `/admin/storage-recovery` | Composite storage health score | AdminStorageRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminStorageRecovery.jsx | — |
| KPI-0028 | `/admin/storage-recovery` | Disk · R2 · backups · recovery drills. One evidence-first surface. | AdminStorageRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminStorageRecovery.jsx | — |
| KPI-0029 | `/admin/ai-operations` | AI gateway · providers · modules · Daily Report AI health. | AdminAiOperations | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminAiOperations.jsx | — |
| KPI-0030 | `/admin/ai-operations` | AI call latency histogram | AdminAiOperations | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminAiOperations.jsx | — |
| KPI-0031 | `/admin/communications` | Delivery Health | AdminCommunications | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminCommunications.jsx | — |
| KPI-0032 | `/admin/communications` | Delivery latency percentiles | AdminCommunications | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminCommunications.jsx | — |
| KPI-0033 | `/admin/communications` | In-app notification queue health surface | AdminCommunications | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminCommunications.jsx | — |
| KPI-0034 | `/admin/governance-trust` | Deploy Recovery Playbook | AdminGovernanceTrust | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminGovernanceTrust.jsx | — |
| KPI-0035 | `/admin/diagnostics` | Runtime health · system probes · OCC snapshot · scheduler · certification. | AdminDiagnostics | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminDiagnostics.jsx | — |
| KPI-0036 | `/admin/diagnostics` | API Health | AdminDiagnostics | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminDiagnostics.jsx | — |
| KPI-0037 | `/admin/diagnostics` | System Health Cards | AdminDiagnostics | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminDiagnostics.jsx | — |
| KPI-0038 | `/admin/diagnostics` | System Health Detail | AdminDiagnostics | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminDiagnostics.jsx | — |
| KPI-0039 | `/admin/diagnostics` | Endpoint latency percentiles | AdminDiagnostics | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminDiagnostics.jsx | — |
| KPI-0040 | `/admin/diagnostics` | Mongo cluster capacity & connection pool surface | AdminDiagnostics | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminDiagnostics.jsx | — |
| KPI-0041 | `/admin/maintenance` | Storage · Backups · R2 | AdminMaintenance | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminMaintenance.jsx | — |
| KPI-0042 | `/admin/maintenance` | Security · Deployment · Health | AdminMaintenance | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminMaintenance.jsx | — |
| KPI-0043 | `/admin/maintenance` | Health / Diagnostics Maintenance | AdminMaintenance | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminMaintenance.jsx | — |
| KPI-0044 | `/admin/maintenance` | Refresh Backup Health | AdminMaintenance | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminMaintenance.jsx | — |
| KPI-0045 | `/admin/maintenance` | Refresh R2 Health | AdminMaintenance | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminMaintenance.jsx | — |
| KPI-0046 | `/admin/database` | Database Capacity | AdminDatabase | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminDatabase.jsx | — |
| KPI-0047 | `/admin/database` | Storage trend and capacity forecast. | AdminDatabase | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminDatabase.jsx | — |
| KPI-0048 | `/admin/dispatch` | Total Active Assets | AdminDispatch | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminDispatch.jsx | — |
| KPI-0049 | `/admin/operational-intelligence` | Score | AdminOperationalIntelligence | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminOperationalIntelligence.jsx | — |
| KPI-0050 | `/admin/operational-intelligence/recipients` | Total recipients | AdminOperationalIntelligenceRecipients | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminOperationalIntelligenceRecipients.jsx | — |
| KPI-0051 | `/admin/system-health` | System Health | SystemHealth | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from SystemHealth.jsx | — |
| KPI-0052 | `/admin/guidance-coverage` | Articles total | AdminGuidanceCoverage | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminGuidanceCoverage.jsx | — |
| KPI-0053 | `/admin/guidance-coverage` | Operational Guidance Coverage | AdminGuidanceCoverage | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminGuidanceCoverage.jsx | — |
| KPI-0054 | `/admin/operational-inventory` | Drift | AdminOperationalInventory | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminOperationalInventory.jsx | — |
| KPI-0055 | `/admin/operational-inventory` | Drift · P0 | AdminOperationalInventory | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminOperationalInventory.jsx | — |
| KPI-0056 | `/admin/operational-inventory` | Drift · P1 | AdminOperationalInventory | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminOperationalInventory.jsx | — |
| KPI-0057 | `/admin/operational-inventory` | Drift · P2 | AdminOperationalInventory | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminOperationalInventory.jsx | — |
| KPI-0058 | `/admin/operational-inventory` | Total articles | AdminOperationalInventory | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminOperationalInventory.jsx | — |
| KPI-0059 | `/admin/governance/legacy-health` | Healthy | AdminGovernance | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminGovernance.jsx | — |
| KPI-0060 | `/admin/governance/legacy-health` | Governance Health | AdminGovernance | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminGovernance.jsx | — |
| KPI-0061 | `/admin/project-identity` | Healthy | AdminProjectIdentityGovernance | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminProjectIdentityGovernance.jsx | — |
| KPI-0062 | `/admin/project-identity` | Identity Health Score | AdminProjectIdentityGovernance | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminProjectIdentityGovernance.jsx | — |
| KPI-0063 | `/admin/governance/self-protection` | Total open gaps | SelfProtection | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from SelfProtection.jsx | — |
| KPI-0064 | `/admin/compliance-findings` | Compliance Findings | AdminComplianceFindings | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminComplianceFindings.jsx | — |
| KPI-0065 | `/admin/deploy-recovery` | Deployment Recovery | DeployRecovery | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from DeployRecovery.jsx | — |
| KPI-0066 | `/admin/analytics` | Usage Analytics | AdminAnalytics | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminAnalytics.jsx | — |
| KPI-0067 | `/admin/analytics` | Top route count | AdminAnalytics | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminAnalytics.jsx | — |
| KPI-0068 | `/admin/analytics` | Top routes by call count | AdminAnalytics | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminAnalytics.jsx | — |
| KPI-0069 | `/admin/guide` | Backups — how to never lose data | AdminGuide | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from AdminGuide.jsx | — |
| KPI-0070 | `/admin/inspections` | Total Reports | Dashboard | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from Dashboard.jsx | — |
| KPI-0071 | `/admin/inspections` | Avg Score | Dashboard | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from Dashboard.jsx | — |
| KPI-0072 | `/admin/trench-boxes` | Trench shield tabulated data · OSHA compliance ready | TrenchBoxesAdmin | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from TrenchBoxesAdmin.jsx | — |
| KPI-0073 | `/admin/trench-safety/reports` | Executive Asset Health | TrenchSafetyReports | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from TrenchSafetyReports.jsx | — |
| KPI-0074 | `/admin/trench-safety/reports` | Inspection Compliance | TrenchSafetyReports | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from TrenchSafetyReports.jsx | — |
| KPI-0075 | `/admin/incidents` | Incidents | IncidentsDashboard | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from IncidentsDashboard.jsx | — |
| KPI-0076 | `/admin/incidents` | Field-reported incidents · escalation tracking | IncidentsDashboard | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from IncidentsDashboard.jsx | — |
| KPI-0077 | `/admin/incidents/:id` | Incidents | ViewIncident | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from ViewIncident.jsx | — |
| KPI-0078 | `/admin/executive-operational-intelligence` | Total labor hours | ExecutiveOperationalIntelligence | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from ExecutiveOperationalIntelligence.jsx | — |
| KPI-0079 | `/admin/executive-operational-intelligence` | Total equipment hours | ExecutiveOperationalIntelligence | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from ExecutiveOperationalIntelligence.jsx | — |
| KPI-0080 | `/admin/executive-operational-intelligence` | No at-risk projects in this range. | ExecutiveOperationalIntelligence | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from ExecutiveOperationalIntelligence.jsx | — |
| KPI-0081 | `/admin/executive-operational-intelligence` | Portfolio totals in range | ExecutiveOperationalIntelligence | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from ExecutiveOperationalIntelligence.jsx | — |
| KPI-0082 | `/admin/executive-operational-intelligence` | Top-at-risk projects by delay + safety | ExecutiveOperationalIntelligence | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from ExecutiveOperationalIntelligence.jsx | — |
| KPI-0083 | `/admin/executive-operational-intelligence` | Canonical variance, recovery, and resource coordination | ExecutiveOperationalIntelligence | — | — | — | — | — | — | — | NOT_YET_TRACED | Static seed from ExecutiveOperationalIntelligence.jsx | — |