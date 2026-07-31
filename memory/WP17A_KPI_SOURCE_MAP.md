# WP-17A KPI Source Map

Date opened: 2026-07-31
Status: ACTIVE

## Initial source map

| KPI / Surface | Primary UI Consumer | Endpoint / Service | Primary Source of Truth | Initial Truth Risk |
|---|---|---|---|---|
| Daily Report Draft Health | `DraftHealthTile.jsx` / OCC | `/api/admin/draft-health` | `draft_telemetry` | telemetry events may be presented as draft entities |
| Backup Health Check | OCC | `services.operations_control.backups` | local `BACKUP_DIR` only | non-canonical signal in production |
| Deploy Recovery Playbook | OCC | `services.operations_control.deploy` | local `BACKUP_DIR` + static playbook | non-canonical backup truth |
| Recovery Snapshot | Admin Recovery | `/api/admin/recovery/snapshot` | canonical archive lineage + backup truth services | reconcile with OCC cards |
| Security & Deployment Posture | OCC | `services.operations_control.security` | env snapshot only | may not reflect effective runtime CORS policy |
| Governance Summary | Governance pages | `/api/admin/governance/summary` | `compliance_findings`, `compliance_scans` | stale-scan disclosure missing |
| R2 Lifecycle Health | Storage & Recovery | `/api/admin/r2/lifecycle/health` | `r2_inventory`, `r2_classifications`, `r2_lifecycle_runs`, `backup_health` | stale freshness and ownership blended |
| Production Certification | trust / certification pages | `/api/admin/production-certification` | `trust_spine_events` | freshness policy may be too universal |
| Deploy Readiness Binding Coverage | Deploy readiness pages | `/api/admin/deploy-readiness` | master/trust helpers | formula + historical remediation audit needed |
| Master Binding Audit | Admin deploy readiness / audit tools | `/api/master-lookup/audit` | collection-level canonical binding coverage helper | denominator semantics previously weak |
| Employee Link Review Queue | Governance remediation | `/api/admin/compliance/employee-link-review-queue` | employee-linkage detector findings | ambiguous findings previously not materialized |
| Storage Audit / Safe Cleanup | OCC maintenance / storage recovery | `storage.audit`, `storage.safe_cleanup` | local filesystem + cleanup history | lacked thresholds / retention classes / cleanup evidence |
| Production Certification Policy | Diagnostics / AI Ops / Trust surfaces | `/api/admin/production-certification` | `trust_spine_events` + workflow policy catalog | one-size-fits-all freshness obscured workflow reality |
| Executive Overview | `ExecutiveOverview.jsx` | `/api/admin/executive/overview` | executive aggregator over `daily_reports`, `incidents`, `corrective_actions`, `project_team_assignments`, `fleet_status`, `asset_holds` | incident / corrective-action semantics needed canonical alignment + metadata |
| Project Health | `ProjectHealth.jsx` | `/api/project-health` | `jobs_master`, `tasks`, `po_requests`, `document_expirations`, `incidents`, `corrective_actions` | summary ladder and indicator columns needed explicit provenance |
| HR Queue / Roster strip | `HrHubV2.jsx`, `HrKpiStrip.jsx` | `/api/hr/employee-roster`, `/api/hr/employee-requests`, `/api/field-leadership/time-off/stats`, `/api/operations/expirations/summary` | canonical HR roster, employee request queue, FL time-off records, expiration summaries | old UI consumed wrong endpoints / wrong response shape causing fake-green zeros |
| Safety Company Posture | `SafetyOperationalKpisCard.jsx` | `/api/safety/company/safety-kpis` | shared operational KPI spine `aggregate_project_kpis()` + active project rollup | grouped cards lacked clear provenance and band logic visibility |
