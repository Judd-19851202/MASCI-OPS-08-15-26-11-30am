# Enterprise Governance Health

Date: 2026-07-29

## Purpose
This document defines the evidence sources used by the Operational Health Dashboard for the Enterprise Governance module.

## Evidence Sources
- Governance authority: `/api/admin/governance/registry`, `/api/admin/governance/versions`
- Drift detection: `backend/tools/wp15_governance_convergence_scan.py`
- Lifecycle integrity: `/api/admin/trust-spine`, `/api/admin/occ/trust-events`
- Certification posture: `/api/admin/production-certification`
- Identity and session health: `/api/admin/governance/identities`, `/api/admin/sessions/recent`
- CI/CD protection: `.github/workflows/ci.yml`, `.github/workflows/sigma3-deploy-gate.yml`, `scripts/assert_wp15_governance_convergence.py`
- Constitutional closeout artifacts: `WP15_ARCHITECTURE_FREEZE.md`, `WP15_CONTINUOUS_CERTIFICATION.md`, `WP15_GOVERNANCE_DASHBOARD.md`, `WP15_CONSTITUTIONAL_GOVERNANCE_STANDARD.md`

## Status Rules
- GREEN: evidence explicitly proves the KPI is healthy.
- AMBER: evidence proves partial degradation or non-blocking concern.
- RED: evidence proves a constitutional or operational failure.
- UNKNOWN: evidence is missing, stale, or unreachable.

## Dashboard Contract
Every KPI card must expose current state, evidence timestamp, evidence source, last successful refresh, producer, affected assets, and remediation guidance when applicable.