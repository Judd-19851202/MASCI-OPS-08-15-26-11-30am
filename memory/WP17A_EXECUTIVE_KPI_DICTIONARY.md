# WP-17A Executive KPI Dictionary Snapshot

Authoritative live source: `/api/admin/wp17a/kpi-dictionary`

Current snapshot count: **25** audited KPI surfaces.

## Dictionary scope

Each entry in the live dictionary includes:
- canonical name
- business description
- executive description
- formula
- raw inputs
- derived inputs
- source tables
- repository / route source
- refresh interval
- owner
- confidence
- certification status
- validation timestamp
- dependencies
- consumers
- related KPIs
- known limitations
- intentional exceptions
- version history
- last modified

## Snapshot inventory

| ID | Display Name | Category | Owner | Canonical Source |
| --- | --- | --- | --- | --- |
| WP17A-KPI-001 | Daily Report · Draft Health | Admin OS / Operations Control Center | daily-report-resiliency | `/api/admin/draft-health` |
| WP17A-KPI-002 | Backup Health Check | Operations Control Center | platform-trust-program | `/api/admin/recovery/snapshot` |
| WP17A-KPI-003 | Deploy Recovery Playbook | Operations Control Center | platform-trust-program | `/api/admin/deployment-readiness` |
| WP17A-KPI-004 | recovery snapshot backup posture | Admin Recovery / Recovery Dashboard | platform-trust-program | `/api/admin/recovery/snapshot` |
| WP17A-KPI-005 | CORS pinned=no | Operations Control / Security | platform-trust-program | runtime CORS policy |
| WP17A-KPI-006 | governance summary / convergence score | Governance / Trust | governance-trust | `/api/admin/governance/summary` |
| WP17A-KPI-007 | storage lifecycle health score | Storage & Recovery | storage-reliability | `/api/admin/r2/lifecycle/health` |
| WP17A-KPI-008 | master-binding coverage percentages | Deploy Readiness | deploy-readiness | deploy readiness surfaces |
| WP17A-KPI-009 | production certification | Production Certification | production-certification | `/api/admin/production-certification` |
| WP17A-KPI-010 | storage / system usage | Platform / Storage / System Health | platform-trust-program | `/api/cluster/capacity` + history |
| WP17A-KPI-011 | governance convergence metric | Admin OS | platform-trust-program | Admin OS governance probe |
| WP17A-KPI-012 | master-binding coverage percentages | Deploy Readiness / Master Lookup | master-data-integrity | `/api/master-lookup/audit` |
| WP17A-KPI-013 | review queue for ambiguous employee bindings | Governance / Data Integrity | platform-trust-program | `/api/admin/compliance/employee-link-review-queue` |
| WP17A-KPI-014 | storage audit / safe cleanup projection | Storage & Recovery / OCC Maintenance | platform-trust-program | OCC storage operations |
| WP17A-KPI-015 | production certification freshness / stale workflow status | Diagnostics / AI Ops / Governance Trust | production-certification | `/api/admin/production-certification` |
| WP17A-KPI-016 | Why this number? | Shared trust-shell KPI surfaces | platform-trust-program | shared metadata model |
| WP17A-KPI-017 | executive verdict and tile-level Why this number? | Executive | executive-truth | `/api/admin/executive/overview` |
| WP17A-KPI-018 | project-health summary cards and indicator headers | Project | project-health | `/api/project-health` |
| WP17A-KPI-019 | employee requests, time-off pending, training due soon, docs expired, active employees | HR | hr-operations | canonical HR endpoints |
| WP17A-KPI-020 | company safety posture, band, totals-card Why this number? | Safety | safety-truth | `/api/safety/company/safety-kpis` |
| WP17A-KPI-021 | Atlas Capacity Forecast | Storage & Recovery | storage-reliability | `/api/cluster/capacity/history` |
| WP17A-KPI-022 | OCC Health Snapshot | Operations | operations-control | `/api/admin/occ/health` |
| WP17A-KPI-023 | Environment / Data Source Truth | Trust Center | platform-attestation | `/api/platform/data-truth` |
| WP17A-KPI-024 | Trust Validator | Trust Center | platform-trust-program | `/api/admin/platform-trust/validate` |
| WP17A-KPI-025 | Enterprise Governance Health | Admin | governance-trust | `/api/admin/operational-health/modules/enterprise-governance` |