# WP15 Residual Risk Register

Last updated: 2026-07-29
Status: Final review state

## Residual Risks
| Risk ID | Severity | Description | Current state |
|---|---:|---|---|
| RR-001 | P0 | Manual governed request builders remained in frontend | Closed — manual builder count is now 0 |
| RR-002 | P0 | Repository still has legacy-migratable backend auth seams | Open — 9 findings remain and block sole-authority certification |
| RR-003 | P1 | Session-expiry / lockout / recovery evidence breadth | Partial — core evidence verified; live brute-force unlock and full reset-email redemption not exercised |
| RR-004 | P1 | Emergency override certification | Closed for core evidence |
| RR-005 | P1 | Trust Spine completeness breadth | Partial — integrity verified, breadth sampling not exhaustive |

## Acceptance Status
- RR-002 is **not accepted away**. It is the primary reason for final constitutional NO-GO.
- RR-003 and RR-005 are acceptable as follow-on completeness work once RR-002 is resolved.