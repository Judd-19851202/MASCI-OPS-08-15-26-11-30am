# TRACK 19.43 · Fleet Intelligence Digest

**Status:** 🟢 IMPLEMENTED (from CONTRACT_REGISTERED).
**Product ID:** `fleet_intelligence`.
**Aggregator:** `/app/backend/operational_intelligence/products.py::_agg_fleet_intelligence`.

## Contract

| Field | Value |
|---|---|
| `product_id` | `fleet_intelligence` |
| `display_name` | Fleet Intelligence Digest |
| `permission_role` | `safety_or_admin` |
| `schedule_freq` | `weekly` (Mon 13:00 UTC) |
| `status` | IMPLEMENTED |

## 14 sections rendered

1. Executive Summary — total units · OOS · safety holds · maint holds · open defects · critical defects · overdue inspections.
2. Operational Intelligence Score.
3. Trend Direction — OOS headline metric.
4. Top Wins — full availability · clean inspections · zero equipment incidents.
5. Needs Immediate Attention — CRITICAL defects · safety holds · OOS · overdue inspections · equipment incidents.
6. Top 5 · Fleet Attention (safety-hold rows preferred; falls back to OOS units).
7. Core Metrics — inspections/transfers last 7d · equipment incidents.
8. Trend Table — not-applicable this run.
9. Recommendations — resolve critical defects · return OOS · close inspections · investigate holds.
10. Upcoming Risks — reserved.
11. Recent Changes — inspections + transfers volume.
12. Deep Links — `/fleet`, `/fleet/holds`, `/fleet/defects`, `/fleet/inspections`, `/safety/cases?type=equipment_damage`.
13. No-Auto-Decision Notice — verbatim.
14. Audit Footer.

## Insufficient-data guard

Returns `insufficient_data_score()` when zero fleet signals are populated. Score → CRITICAL, confidence → `insufficient_data`.

## Rollback

Delete the `_agg_fleet_intelligence` block + `register_product("fleet_intelligence")` block. Product falls back to CONTRACT_REGISTERED behaviour. HIGH confidence.
