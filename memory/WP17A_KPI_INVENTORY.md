# WP-17A KPI Inventory

Date opened: 2026-07-31
Status: ACTIVE

This inventory enumerates KPI / trust / observability surfaces being audited under WP-17A.

## Initial portal / page inventory

### Admin / Executive truth surfaces
- Admin OS
- Operations Control Center
- Operations Trust Center
- Deploy Readiness
- Production Certification
- Storage & Recovery
- Recovery Dashboard
- System Health
- Diagnostics
- Governance / Compliance
- Identity & Security
- Integration Center
- Platform Configuration

### Workflow / operational surfaces with KPI implications
- Daily Reports
- Equipment
- Dispatch
- Transportation
- Fleet
- Safety
- HR
- Training
- Qualifications
- Asset Administration / Asset Mapping
- Email / Notifications
- AI Operations

### Initial backend truth endpoints under active source tracing
- `/api/admin/occ/health`
- `/api/admin/operations-control/overview`
- `/api/admin/draft-health`
- `/api/admin/recovery/snapshot`
- `/api/admin/r2/lifecycle/health`
- `/api/admin/governance/summary`
- `/api/admin/production-certification`
- `/api/admin/deploy-readiness`
- `/api/admin/deployment-readiness`
- `/api/admin/integrations/health`
- `/api/health`
- `/api/ready`
- `/api/health/full`
- `/api/platform/data-truth`

## Initial frontend truth consumers under active audit
- `frontend/src/pages/admin/AdminOS.jsx`
- `frontend/src/pages/admin/AdminRecovery.jsx`
- `frontend/src/pages/AdminDeployReadiness.jsx`
- `frontend/src/components/admin/DraftHealthTile.jsx`
- `frontend/src/components/admin/ProductionHealthLine.jsx`
- `frontend/src/components/GovernanceHealthChip.jsx`
- `frontend/src/components/SystemHealthBadge.jsx`
- `frontend/src/components/IntegrationHealthCard.jsx`

## Expansion rule
This file will expand continuously until every KPI / score / badge / trust signal / health card / readiness state is captured.

## 2026-07-31 verified portal completion batch

### Executive — COMPLETE FOR CURRENT SWEEP
- `/admin/executive-overview`
- KPI surfaces: verdict, jobs attention, overdue operational items, staffing issues, equipment issues, safety attention items, activity snapshot
- Evidence captured: authenticated preview API verification + iteration 87 frontend verification

### Project — COMPLETE FOR CURRENT SWEEP
- `/project-health`
- KPI surfaces: red / amber / green / total / avg confidence summary cards, indicator columns, role-scoped status ladder
- Evidence captured: auth-aware backend regression suite + iteration 87 frontend verification

### HR — COMPLETE FOR CURRENT SWEEP
- `/hr` (HrHubV2)
- shared `HrKpiStrip`
- KPI surfaces: active employees, pending employee requests, time-off pending, training due soon, docs expired
- Evidence captured: representative queue / roster / expiration API reconciliation + iteration 87 frontend verification

### Safety — COMPLETE FOR CURRENT SWEEP
- company safety operational KPI card
- KPI surfaces: company band, safety events, injuries/accidents, near-miss/open incidents, meetings/JHAs/inspections, source-status strip
- Evidence captured: company safety band metadata verification + iteration 87 frontend verification
