# TRACK 19.42 · Transportation Intelligence Digest

**Status:** 🟢 IMPLEMENTED (moved from CONTRACT_REGISTERED).
**Product ID:** `transportation_intelligence`.
**Aggregator:** `/app/backend/operational_intelligence/products.py::_agg_transportation_intelligence`.

## Contract

| Field | Value |
|---|---|
| `product_id` | `transportation_intelligence` |
| `display_name` | Transportation Intelligence Digest |
| `permission_role` | `safety_or_admin` |
| `template_key` | `executive_v1` |
| `schedule_freq` | `weekly` |
| `schedule_iso_day` | 1 (Monday) |
| `schedule_hour_utc` | 13 |
| `status` | `IMPLEMENTED` |
| `tags` | `["transportation", "fleet", "safety", "weekly"]` |

## Data sources consumed

- `db.dvir` — total · last-7d · open-defects.
- `db.driver_qualifications` — active · expiring in 30d · expired.
- `db.equipment_units` — total · OOS.
- `db.vehicle_assignments` — active assigned; unassigned derived.
- `db.incident_cases` — vehicle-accident type in last 7 days.
- `db.transport_action_items` — open backlog.

All queries are wrapped in `try/except` — a missing collection returns 0, not an error. If no signal is populated, the aggregator returns `insufficient_data_score()`.

## 14 sections rendered

1. **Executive Summary** — Active drivers · Expired · Expiring 30d · DVIRs 7d · DVIRs w/ open defects · OOS units · Vehicle incidents 7d.
2. **Operational Intelligence Score** — 0–100 · Attention · Confidence · Freshness.
3. **Trend Direction** — expired-qualifications headline metric (▼/▲/→).
4. **Top Wins** — full fleet availability · no vehicle incidents · qualifications current.
5. **Needs Immediate Attention** — expired qualifications · expiring 30d · open DVIR defects · OOS · vehicle incidents.
6. **Top 5 Items** — units currently OOS (unit · make · model · status · OOS since).
7. **Core Metrics** — fleet size · vehicles assigned · unassigned · DVIR total · action backlog.
8. **Trend Table** — not-applicable this run (history required · engages Track 19.43+).
9. **Recommendations** — actionable renewal/return-to-service items.
10. **Upcoming Risks** — 30-day cert-expiry watchlist.
11. **Recent Changes** — DVIRs submitted last 7d.
12. **Deep Links** — Command Queue · Fleet · Inspection Center · Driver Qualification Records · Vehicle Incidents.
13. **No-Auto-Decision Notice** — Transportation · Fleet · Safety · HR own decisions. Platform does NOT decide DOT recordability, fault, preventability, discipline, or liability.
14. **Audit Footer** — track · aggregator source · insufficient-data behaviour statement.

## Live smoke behaviour

- Preview environment: transportation collections empty → aggregator returns `insufficient_data_score()` cleanly (CRITICAL + `confidence=insufficient_data`).
- Populated environment: real signals compute a bounded 0–100 score with named contributors.

## Rollback

Delete the `_agg_transportation_intelligence` block + `register_product("transportation_intelligence")` block in `products.py`. Product falls back to CONTRACT_REGISTERED behaviour (the Track 19.40 baseline stub raises `NotImplementedError`). HIGH confidence.
