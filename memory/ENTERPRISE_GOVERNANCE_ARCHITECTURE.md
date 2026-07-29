# Enterprise Governance Architecture

## Purpose

WP-15 establishes the canonical Enterprise Governance Engine for MASCI OPS.

It centralizes:

- governance identity projection
- roles and permissions
- policies
- approval flows
- delegation
- separation of duties
- emergency overrides
- governance decisions and audit history

## Canonical Owners

- Existing authentication remains canonical for login and credentials:
  - `/app/backend/routes/auth_directory_routes.py`
  - `/app/backend/auth.py`
  - `/app/backend/pm_auth.py`
- Enterprise Governance authorization owner:
  - `/app/backend/services/enterprise_governance.py`
- Enterprise Governance admin APIs:
  - `/app/backend/routes/enterprise_governance.py`
- Enterprise Governance admin UI:
  - `/app/frontend/src/pages/admin/AdminGovernanceOperatingSystem.jsx`

## Architectural Model

1. Authentication resolves identity through existing platform owners.
2. Governance derives a policy-ready identity projection from those owners.
3. Routes request governance decisions through a shared backend enforcement helper.
4. Governance decisions produce allow / deny outcomes as governed results.
5. Approval requests and overrides integrate with the Operations Control Plane communication path.
6. Trust Spine captures governance outcomes through enterprise-governance records and stages.

## Initial Enforced Scope

- Operational Case transitions / closure / export / baseline inclusion
- OCP certification execution
- Monday Briefing approval/freeze actions
- task assignment / task completion updates
- notification feed access / acknowledgement
- governance administration routes under `/admin/governance/*`

## Key Constraints

- no second authentication system
- backend enforcement is authoritative
- denials are governed outcomes, not generic app errors
- no direct email logic for approvals or overrides
- no emergency override is silent, permanent by default, self-approved, or unaudited
