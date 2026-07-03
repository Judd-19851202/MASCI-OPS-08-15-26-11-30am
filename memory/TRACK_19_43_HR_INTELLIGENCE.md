# TRACK 19.43 · HR Intelligence Digest

**Status:** 🟢 IMPLEMENTED (from CONTRACT_REGISTERED).
**Product ID:** `hr_intelligence`.
**Aggregator:** `/app/backend/operational_intelligence/products.py::_agg_hr_intelligence`.

## Contract

| Field | Value |
|---|---|
| `product_id` | `hr_intelligence` |
| `display_name` | HR Intelligence Digest |
| `permission_role` | `admin_only` |
| `schedule_freq` | `weekly` (Mon 13:00 UTC) |
| `status` | IMPLEMENTED |

## 14 sections rendered

1. Executive Summary — active employees · new hires (7d) · exits (7d) · expired quals · expiring (30d) · orientations active.
2. Operational Intelligence Score.
3. Trend Direction — expired-qualifications headline metric.
4. Top Wins — all quals current · training activity · net-positive workforce.
5. Needs Immediate Attention — expired quals · expiring 30d · in-progress orientations.
6. Top 5 · Expired Qualifications (employee · cert type · expired on).
7. Core Metrics — active employees · training activities · orientations.
8. Trend Table — not-applicable this run.
9. Recommendations — renew · schedule · follow up on orientations.
10. Upcoming Risks — 30-day expiring quals.
11. Recent Changes — new hires · exits · training activity.
12. Deep Links — `/hr/employees`, `/hr/training-records`, `/hr/lifecycle`, `/hr/orientation`.
13. No-Auto-Decision Notice — verbatim.
14. Audit Footer.

## Insufficient-data guard

`insufficient_data_score()` when zero HR signals populated.

## Non-goals

- HR performance ratings (owned by HR).
- Termination cause / eligibility for rehire (never determined by platform).
- Discipline actions (owned by HR).
