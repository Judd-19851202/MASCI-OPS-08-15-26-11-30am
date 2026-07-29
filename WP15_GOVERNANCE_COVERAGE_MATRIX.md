# WP15 Governance Coverage Matrix

Last updated: 2026-07-29
Status: Final certified evidence snapshot

| Domain | Backend enforcement | Request lifecycle | Negative-path evidence | Live / independent verification | Residual position |
|---|---|---|---|---|---|
| Governance admin | Verified | Verified | Verified | Verified (`pytest` + independent backend QA) | Certified |
| Daily Reports | Verified / governed read adapter | Verified shared lifecycle | Verified | Verified in certification suite | Certified |
| Equipment | Verified / governed scope adapter | N/A | Partial | Verified in certification suite | Certified |
| Job Photos | Verified / governed scope adapter | N/A | Partial | Verified in certification suite | Certified |
| PM Command Center | Verified / governed scope adapter | Verified | Verified | Verified (frontend QA + backend QA) | Certified |
| Safety portal surfaces | Verified | Verified | Partial | Verified (frontend QA + backend QA) | Certified |
| Dispatch portal surfaces | Verified | Verified | Partial | Verified (frontend QA + backend QA) | Certified |
| HR portal surfaces | Verified | Verified via shared client | Partial | Verified in certification suite | Certified |
| Shop / Asset Care reads | Verified | Verified via shared client | Partial | Verified in focused recovery suite | Certified |
| Field Leadership | Verified | Verified | Partial | Verified in certification suite | Certified |
| Trust Spine | Verified | N/A | N/A | Verified (`test_track_15_76_trust_spine.py`) | Breadth sampling still expandable |
| Emergency overrides | Verified | Verified | Partial | Verified (`test_wp15_enterprise_governance.py` + backend QA) | Revocation breadth still expandable |

## Note
This matrix reflects only exercised evidence from the current run. Remaining “Partial” cells describe supplemental verification breadth, not residual constitutional drift.