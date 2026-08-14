# WAVE 5 — CANONICAL % COMPLETE CONTRACT (KPI-PERCENT-COMPLETE)

Owner rule: same concept + same scope => one calculator. Different business KPIs that
merely share the label "% Complete" MUST be explicitly separated and governed — never
forced through one formula because they share a variable name.

Shared implementation: `backend/lib/kpi_percent_complete.py`. Guard: `test_gd0017_percent_complete_contract.py` (PASS 4/4).
Status: CONTRACT BUILT. Consumer migration NOT yet performed (owner: build contract before modifying consumers).

## GOVERNED CONCEPTS (the 84 "% complete" sites decompose into these — NOT one KPI)

| Concept | What is completed | Numerator | Denominator | Empty-denom | Rounding | Missing input | Calculator |
|---|---|---|---|---|---|---|---|
| PC-STORED | User/import-entered progress on a schedule activity / daily-report row | n/a (stored) | n/a | n/a | none (clamp only) | None = UNKNOWN (never 0) | `clamp_stored_percent()` |
| PC-CHECKLIST | Completed eligible items over total eligible items (onboarding steps, lifecycle tasks) | completed eligible | total eligible | 0.0 (no ZeroDiv) | 1 dp, clamp [0,100] | 0 | `checklist_percent()` / `_from_flags()` |
| PC-SCHEDULE | Approved schedule progress rollup for a scope | approved_percent_complete rows | count/aggregation of rows | 0.0 | 2 dp | 0 in rollup | `schedule_rollup_percent(agg=max|mean)` |
| PC-COST | Cost-code progress percent (pm_routes) | earned/actual | budget/planned | (audit at migration) | TBD at migration | 0 | route to PC-SCHEDULE or its own governed calc after per-site audit |
| NON-FORMULA | Pydantic field defaults, column-alias maps, PDF column labels, comments | — | — | — | — | — | not a KPI compute site (exclude) |

## SITE MAP (backend, from WAVE5_KPI_CONCEPTS.json)
- PC-STORED (clamp/parse only): daily_summary.py (186,427,774), daily_reports.py model field,
  project_schedule_authority.py (412,909,1053,1135 + alias maps 134,1683,1703,1858), pdf_render.py (1386 read),
  enterprise_governance.py field defaults (387,416). => migrate to `clamp_stored_percent` (missing -> None).
- PC-CHECKLIST (true ratio): asset_spine.py:427 (steps completed/len(steps)), employee_lifecycle.py:1377
  (completion_percent). => migrate to `checklist_percent`.
- PC-SCHEDULE (rollup): project_schedule_actuals_spine.py (570 avg, 619 max, 634/681/707/761/797),
  project_schedule_authority.py approved_* (1782,1800,1816,1838). => migrate to `schedule_rollup_percent`.
- PC-COST: pm_routes.py:303 (cost_code_progress_percent) — audit numerator/denominator at migration.
- NON-FORMULA noise excluded: pdf_render comments (1368,1372), alias-map declarations, Pydantic defaults.
- Frontend (20 sites): display-only formatting of a backend-provided value in most cases; audit at consumer-migration
  to ensure they never RE-derive a divergent percent (must render the canonical backend value).

## KEY TRUTH DISTINCTIONS PINNED BY GD-0017
- Stored 0 (known 0%) != empty/missing (UNKNOWN). PC-STORED returns None for missing, never silent 0.
- Empty checklist (0/0) = 0.0 by contract (no ZeroDivisionError), distinct from "unknown".
- Divide-by-zero guarded everywhere; all results clamped [0,100].

## NEXT (consumer migration, after this checkpoint)
1. Migrate PC-CHECKLIST sites (asset_spine, employee_lifecycle) to `checklist_percent` — smallest, highest-divergence-risk.
2. Migrate PC-SCHEDULE rollups to `schedule_rollup_percent` (preserve max vs mean per governed scope).
3. Migrate PC-STORED clamps to `clamp_stored_percent` (fix any silent 0-for-missing).
4. Audit PC-COST + the 20 frontend sites to ensure they render (not re-derive) the canonical value.
5. Then KPI-EXPIRING-RATE (50) and KPI-UTILIZATION (45).
