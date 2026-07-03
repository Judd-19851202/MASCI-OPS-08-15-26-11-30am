# TRACK 19.51 · Operational Intelligence Integration Map

Which OI product feeds which portal Attention Strip.

| Portal | Best-fit OI product | Consumed via | Score model? |
|---|---|---|:-:|
| Executive / Admin | `corporate_intelligence` + `weekly_operations_digest` + `executive_operations_brief` | `GET /summary` filtered to those product_ids | reuse |
| Safety | `safety_morning_digest` | `GET /summary` filtered · `top_attention_label` per product row | reuse |
| HR | `hr_intelligence` + `training_intelligence` | `GET /summary` filtered | reuse |
| PM | `project_intelligence` | `GET /summary` filtered | reuse |
| Shop | `shop_intelligence` | `GET /summary` filtered | reuse |
| Transportation | `transportation_intelligence` | `GET /summary` filtered | reuse |
| Fleet | `fleet_intelligence` | `GET /summary` filtered | reuse |
| Dispatch | `transportation_intelligence` (for driver quals) | `GET /summary` filtered | reuse |
| Field | none (task-launcher, not intelligence-driven) | N/A | N/A |
| Guidance | none | N/A | N/A |
| Asset Administrator | `fleet_intelligence` (asset-hold view) | `GET /summary` filtered | reuse |

## Reuse contract
Every portal Attention Strip must fetch from `GET /api/operational-intelligence/summary` and filter client-side. **Do not** re-query domain collections. **Do not** re-derive scores. If a portal needs a signal the summary endpoint does not expose, propose it as a summary-endpoint additive extension in a follow-up track — never a duplicate scoring path.

## Zero-drift guarantee
- 1 engine.
- 1 score model.
- 1 layout standard.
- N portal Attention Strips, all sourced from that engine.
