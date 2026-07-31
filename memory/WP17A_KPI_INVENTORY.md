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
