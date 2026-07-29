# WP15 Architecture Freeze

Date: 2026-07-29
Status: Constitutional Infrastructure — Frozen

## Enterprise Governance as Constitutional Authority
Enterprise Governance is the constitutional authority for business authorization decisions across the platform. Trust Spine remains the authoritative record for governed lifecycle evidence. The Operational Health Dashboard consumes these authorities and may summarize, downgrade, or surface UNKNOWN, but it may not replace source truth. Future work packages may integrate with or formally extend this authority, but they may not replace it.

## Frozen Runtime Boundaries
- Canonical governance authority: `/api/admin/governance/*` backed by `backend/services/enterprise_governance.py`
- Canonical lifecycle evidence: `/api/admin/trust-spine` and `/api/admin/occ/trust-events`
- Canonical certification evidence: `/api/admin/production-certification`
- Canonical operator route: `/admin/governance`
- Canonical drift scanner: `backend/tools/wp15_governance_convergence_scan.py`

## Approved Extension Points
- Add new operational-health modules through `/api/admin/operational-health/modules/{module_id}` using canonical upstream evidence.
- Add new KPI cards only when each card declares evidence source, producer, timestamps, affected assets, and remediation guidance.
- Add future constitutional systems to the shared module catalog without duplicating their status engines.
- Extend CI protection by running the WP15 scanner in additional release gates, never by weakening existing failure rules.

## Prohibited Patterns
- No alternate business-authorization path outside Enterprise Governance.
- No dashboard-owned policy evaluation or duplicated role/permission logic.
- No GREEN status without explicit evidence.
- No silent downgrade from failure to warning where policy requires a hard stop.
- No undocumented constitutional exemptions.

## Governance Change Process
1. Change the canonical source first.
2. Update the convergence scanner and its CI assertions.
3. Update dashboard documentation and drill-down evidence mappings.
4. Append certification history with the new verification event.
5. Re-certify before declaring the constitutional state healthy.

## Relationship to Future Work Packages
WP15 establishes the common dashboard framework, not a one-off governance page. Future work packages must plug into the same framework for Backup & Disaster Recovery, Trust Spine, Operational Awareness, Scheduling, Academy, and Operational Intelligence.