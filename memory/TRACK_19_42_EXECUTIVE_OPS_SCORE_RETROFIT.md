# TRACK 19.42 · Executive Ops Brief · Score + 14-Section Layout Retrofit

**Status:** 🟢 SHIPPED. `executive_operations_brief` returns the standard
14-section layout with an Operational Intelligence Score.

## What changed

- `/app/backend/operational_intelligence/products.py::_agg_executive_ops`
  composes via `build_standard_layout(...)`.
- Real portfolio aggregator over Track 19.38 data — no fake transportation/fleet/HR domain fields.
- Score contributors:
  - **Positive**: zero HIGH-attention cases · avg days-open < 30.
  - **Negative**: HIGH-attention count · CAPA backlog > 10 · avg days-open > 60.
- `insufficient_data_score()` when portfolio window is empty.
- Trend direction currently returns flat placeholder — history-driven trend engages Track 19.43+ once engine history rows accumulate.

## Not in scope

- Transportation · Fleet · HR data domains are NOT surfaced here. Their intelligence lands in their own products (`transportation_intelligence` shipped in Track 19.42; remaining seven land Track 19.43+).

## Zero-drift

- Track 19.36/19.38 executive routes unchanged.
- Track 19.36 executive PDF path unchanged.
- Track 19.40 registry entry unchanged (aggregator upgraded in place).

## Lock test coverage

- `test_executive_ops_uses_standard_layout` — asserts all 14 sections and HIGH case drags score below 100.
- `test_executive_ops_insufficient_data_when_empty` — asserts CRITICAL + `insufficient_data` confidence on empty portfolio.
