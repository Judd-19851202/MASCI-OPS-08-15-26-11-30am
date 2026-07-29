# WP15 Remaining Findings Register

Last updated: 2026-07-29
Status: Active working register

## Current Normalized Totals
- Legacy governance findings: **71**
- Manual governed builders: **29**
- Category F: **0**

## Pattern-Level Register
| Finding ID | Severity | Category | Description | Current Count | Canonical Replacement | Status |
|---|---:|---|---|---:|---|---|
| RG-001 | P0 | Request lifecycle | Manual governed header construction | 29 | `buildScopedPortalAuthHeaders` | In progress |
| RG-002 | P0 | Governance scope | Remaining module-local PM scope families | 2+ families | `governance_project_scope` / `governance_project_scope_filter` | In progress |
| RG-003 | P1 | Governance drift | Route-local authorization helpers | 4 | Enterprise Governance evaluation | In progress |
| RG-004 | P1 | Governance drift | Inline role branches / checks | residual | Enterprise Governance evaluation | In progress |
| RG-005 | P1 | Governance drift | Custom 403 auth gates | residual | Canonical deny path | In progress |
| RG-006 | P2 | Certification | Broader session-expiry / lockout / recovery evidence incomplete | 1 program area | Modernized certification suite + live checks | In progress |

## Reconciliation Note
This register tracks normalized constitutional findings rather than raw line matches. Raw implementation sites remain reproducible via `backend/tools/wp15_governance_convergence_scan.py`.