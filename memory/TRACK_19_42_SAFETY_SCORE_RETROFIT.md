# TRACK 19.42 · Safety Morning · Score + 14-Section Layout Retrofit

**Status:** 🟢 SHIPPED. `safety_morning_digest` aggregator now returns
the standard 14-section layout with an Operational Intelligence Score.

## What changed

- `/app/backend/operational_intelligence/products.py::_agg_safety_morning`
  now composes via `build_standard_layout(...)`.
- Score derived from real contributors:
  - **Positive**: closure pace ≥ open pace · avg readiness ≥ 80% · zero HIGH cases with open portfolio.
  - **Negative**: HIGH-attention cases · overdue CAPAs · evidence gaps.
- Trend direction uses `compute_trend(total_open, total_open - opened + closed)`.
- `insufficient_data_score()` when no cases exist and none opened/closed in the last 7 days.
- Legacy Track 19.39 `compose_digest` output preserved under `digest.legacy_v1_shape` for downstream consumers.
- Verbatim `NO_AUTO_DECISION_NOTICE` retained.

## 14 sections rendered

1. Executive Summary — open · high · opened/closed 7d · overdue CAPAs · readiness %
2. Operational Intelligence Score — 0–100 · attention · confidence · freshness
3. Trend Direction — open cases week-over-week
4. Top Wins — closures · readiness · zero-high
5. Needs Immediate Attention — evidence gaps · overdue CAPAs · delayed closeout · exec review
6. Top 5 Items — top attention cases (case · project · type · attention · days · CAPA)
7. Core Metrics — portfolio trend signal string
8. Trend Table — not-applicable this run (history required)
9. Recommendations — actionable next steps
10. Upcoming Risks — reserved for Track 19.43+
11. Recent Changes — opened/closed 7d
12. Deep Links — Safety Case Center · Case Workspace
13. No-Auto-Decision Notice — verbatim Track 19.39 doctrine
14. Audit Footer — product · period · generated_at · note

## Zero-drift

- Track 19.39 API surface unchanged (`compose_digest`, `send_digest`, notice constant, subject).
- Track 19.39 lock test still 🟢 (24/24 assertions).
- `legacy_v1_shape` preserved on every dispatch so any external consumer that reads the 19.39 shape keeps working.

## Lock test coverage

- `test_safety_morning_uses_standard_layout` — asserts all 14 section keys in order.
- `test_safety_morning_preserves_no_auto_decision_notice` — verbatim notice retained.
- Score field completeness inherited from Track 19.41 layout tests.
