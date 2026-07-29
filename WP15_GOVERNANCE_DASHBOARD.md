# WP15 Governance Dashboard

Date: 2026-07-29

## Shared Framework
The platform now uses one shared Operational Health Dashboard framework. Enterprise Governance is the first live module on that framework.

## Primary Route
- Admin route: `/admin/governance`
- Backend module endpoint: `/api/admin/operational-health/modules/enterprise-governance`

## Mandatory KPI Sections
1. Constitutional Status
2. Governance Drift
3. Certification Health
4. Trust Spine Integrity
5. Identity Health
6. Authorization Health
7. Operator Experience
8. Constitutional Exemptions

## Drill-Down Contract
Every KPI opens a drill-down explaining:
- why the state is GREEN / AMBER / RED / UNKNOWN
- which evidence supports it
- which scanner or certification produced it
- when it was last verified
- which files, modules, or workflows are affected
- what remediation is recommended

## Future Modules
Planned modules on this framework: Backup & Disaster Recovery, Trust Spine, Operational Awareness, Scheduling, Academy, and Operational Intelligence.