# WP15 Governance Coverage Matrix

Last updated: 2026-07-29
Status: Final evidence snapshot for WP-15 determination

| Domain | Backend enforcement | Request lifecycle | Negative-path evidence | Live / independent verification | Residual position |
|---|---|---|---|---|---|
| Governance admin | Verified | Verified | Verified | Verified (`pytest` + independent backend QA) | No lifecycle blocker |
| Daily Reports | Partial / governed read adapter | Verified shared lifecycle | Verified | Verified in certification suite | No manual builder blocker; broader repo auth still partial |
| Equipment | Partial / governed scope adapter | N/A | Partial | Verified in certification suite | No manual builder blocker |
| Job Photos | Partial / governed scope adapter | N/A | Partial | Verified in certification suite | No manual builder blocker |
| PM Command Center | Partial / governed scope adapter | Verified | Verified | Verified (frontend QA + backend QA) | Residual read-scope inline logic in operations center |
| Safety portal surfaces | Partial | Verified | Partial | Verified (frontend QA + backend QA) | No manual builder blocker |
| Dispatch portal surfaces | Partial | Verified | Partial | Verified (frontend QA + backend QA) | No manual builder blocker |
| HR portal surfaces | Partial | Verified via shared client | Partial | Verified in certification suite | Residual route-local auth remains in employee domains |
| Shop / Asset Care reads | Partial | Verified via shared client | Partial | Verified in focused recovery suite | Residual asset-admin auth not fully governance-backed |
| Field Leadership | Partial | Verified | Partial | Verified in certification suite | Unreachable PM legacy branch removed |
| Trust Spine | Verified | N/A | N/A | Verified (`test_track_15_76_trust_spine.py`) | Breadth sampling still expandable |
| Emergency overrides | Verified | Verified | Partial | Verified (`test_wp15_enterprise_governance.py` + backend QA) | Revocation breadth still expandable |

## Note
This matrix reflects only exercised evidence from the current run. “Partial” means incomplete constitutional migration breadth, not an observed runtime outage.