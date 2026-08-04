# WP18CY Executive Decision Book

Date: 2026-08-04

## Mission
Stabilize Release 1.0 communication, backup, and MongoDB certification surfaces without changing constitutional authority, source-of-truth ownership, or introducing new workflows.

## Binding Decisions
1. Truth classes are kept separate: `SOURCE`, `PREVIEW_RUNTIME`, `PREVIEW_DB`, `PRODUCTION_DIRECT`, `UNAVAILABLE`.
2. Daily Report regression was repaired only at the first proven divergence.
3. No production repair is claimed because no direct production runtime proof was available in this execution context.
4. Backup alert truth is preserved; thresholds were not loosened.
5. MongoDB changes were limited to bounded, evidence-backed index additions for proven scan-heavy recovery reads.

## Decisions Taken
| Decision | Evidence | Result |
|---|---|---|
| Preserve OPPC eventing, repair only email transport branch | `daily_reports.py` + `control_plane.py` + preview capture | Approved |
| Replace generic Daily Report recipient email body with canonical Daily Report subject/body/PDF package | Preview capture `DR-2026-03607` and `DR-2026-03608` | Approved |
| Preserve To/CC/BCC route truth through notification capture | `notification_delivery.py` + unit tests | Approved |
| Add only three recovery-query indexes | bounded explain before/after | Approved |
| Certify production | direct production evidence unavailable | Rejected |
| Authorize WP-18C7 | WP-18CY gate unresolved | Rejected |

## Final Decision
- **WP-18CY Gate:** `NO-GO`
- **Reason:** Daily Report preview regression was repaired and verified, but direct production proof is unavailable and preview backup freshness remains outside the 60-minute contract.
