# WP18C9 Authority and Lineage Map

Date: 2026-08-07  
Status: PASS

| Portfolio result | Upstream project truth | Delivery behavior | Drill-back |
|---|---|---|---|
| Portfolio cost performance | Project Earned Value snapshots | Aggregate EV/AC/PV/BAC/ETC/EAC totals, then derive CPI/SPI | Earned Value page |
| Projects needing attention | Deterministic rules over project EV, forecast, commitments, constraints, production freshness | No hidden score; reasons and next action stored per project | Project card + project pages |
| Schedule risk | Forecast schedule summary and commitment dates | Count slipped projects and days past commitment | Forecasting page |
| Commitments | Forecast commitment lifecycle counts | Count at-risk/missed/met and cost exposure | Forecasting page |
| Constraints | Forecast constraint register | Count open constraints and leading drivers | Forecasting page |
| Production outlook | Project performance + forecast unit buckets | Roll up only same-unit quantities | Project performance page |
| Resource pressure | Forecast resources families | Count shortage lanes only | Forecasting page |
| Project health context | Existing project health route | Frontend-supporting context only | Project Health page |

## Supporting Record Preservation
- Project performance timestamp preserved from the project performance snapshot.
- Forecast timestamp preserved from the latest forecast version.
- Earned Value timestamp preserved from the latest EV snapshot.
- Project-level drill-back remains explicit in every project card and export row.

## Final Lineage Verdict
C9 preserves traceability by pointing every portfolio conclusion back to the same project records already used by the individual project views.
