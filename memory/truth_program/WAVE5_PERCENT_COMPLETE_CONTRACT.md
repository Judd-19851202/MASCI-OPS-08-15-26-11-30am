# WAVE 5 — CANONICAL % COMPLETE CONTRACT (KPI-PERCENT-COMPLETE)

Owner rule: same concept + same scope => one calculator. Different business KPIs that
merely share the label "% Complete" MUST be explicitly separated and governed — never
forced through one formula because they share a variable name.

Shared implementation: `backend/lib/kpi_percent_complete.py`.
Guards: `test_gd0017_percent_complete_contract.py` (20/20) + `test_wave5_pc_checklist_contract.py` (17/17, live preview).

## STATUS (updated this checkpoint)
- PC-CHECKLIST: **RECONCILED + MIGRATED + LIVE-VERIFIED** (preview).
- PC-SCHEDULE: **AUDITED + GOVERNED** (explicit modes) + 1 genuine mean-rollup migrated.
- PC-STORED: **AUDITED — TRUTHFUL AS-IS** (nullable-contract field already renders unknown≠0; other `||0` are over always-numeric backends).
- PC-COST: **AUDIT PENDING** (do NOT migrate until denominator concept proven per owner).

## GOVERNED CONCEPTS

| Concept | Numerator | Denominator | Empty-denom | Rounding | Missing input | Calculator |
|---|---|---|---|---|---|---|
| PC-STORED | n/a (stored value) | n/a | n/a | clamp only | None = UNKNOWN (never 0) | `clamp_stored_percent()` |
| PC-CHECKLIST | completed eligible | total eligible | **GOVERNED per caller** (0.0 / 100.0 / None) | 1 dp, clamp [0,100] | floored | `checklist_percent(empty=…)` |
| PC-SCHEDULE | approved_percent_complete rows | count of rows | 0.0 | 2 dp | 0 in rollup | `schedule_rollup_percent(agg=SCHEDULE_MODE_MAX|MEAN)` |
| PC-COST | (TBD per-site) | (TBD per-site) | — | — | — | per-site governed calc after audit |

### PC-CHECKLIST empty-denominator is now EXPLICIT (no hidden default lie)
`checklist_percent(completed, total, *, ndigits=1, empty=0.0)` — the caller MUST choose the
empty-denominator meaning for its scope: `0.0` (nothing-of-nothing), `100.0` (vacuously
complete — nothing outstanding, fleet-wide compliance scope), or `None` (UNKNOWN).

## MIGRATED CONSUMER LINEAGE (PC-CHECKLIST)

### 1. Employee Record Completeness — scope: ENTERPRISE / CURRENT
- source: `db.employees` (filter: deleted_at=None, active lifecycle statuses unless include_inactive, `apply_synthetic_hr_exclusion`) — SAME filter as HR roster & /api/employees (no drift).
- eligibility: active employees; each counted once (Mongo doc = one employee, no dedup needed); N/A not applicable.
- calculator: `checklist_percent(..., empty=100.0)` — empty population = vacuously 100% complete.
- API: `GET /api/hr/employee-completeness` -> `completion_percent`, `trade_role_complete_percent`, `crew_complete_percent`, `supervisor_complete_percent` (all canonical, 1 dp).
- frontend: `components/HrCompletenessTile.jsx` `<Metric>` — now renders ALL FOUR backend percents (removed the local `Math.round((value/total)*100)` re-derivation that diverged on rounding + empty→0).
- export: `GET /api/hr/employee-completeness.csv`.
- human labels: "Fully complete X%", "Trade / Role X%", "Crew X%", "Supervisor X%".

### 2. Asset Onboarding % Complete — scope: WORKSPACE_SCOPED (per asset) / CURRENT
- source: `equipment_master.onboarding.{step}` booleans over fixed `AssetSpine.ONBOARDING_STEPS` (12 steps).
- calculator: `checklist_percent(completed_steps, 12, empty=0.0)` (denominator fixed, never empty).
- API: `GET /api/asset-spine/assets/{asset_id}/onboarding` -> `pct_complete`.
- BUG FIXED this checkpoint: handler used `if not doc` on a projected `find_one`, which returned `{}` (falsy) for assets with no `onboarding` field and 404'd EVERY asset -> `pct_complete` was unreachable. Now `if doc is None` (+ project `id`) so existing assets return 200 with `pct_complete` (0.0 when no steps done). Live-verified.

## PC-SCHEDULE — AUDIT RESULT (governed modes, NOT interchangeable)
Explicit governed modes in `kpi_percent_complete.py`: `SCHEDULE_MODE_MAX`, `SCHEDULE_MODE_MEAN`
(caller MUST pass an explicit `agg`; no anonymous default — ValueError otherwise).
- **SCHEDULE_MODE_MEAN** (unweighted work-package average) — `project_schedule_actuals_spine.py:570`
  `approved_percent_complete_average` MIGRATED to `schedule_rollup_percent(agg=SCHEDULE_MODE_MEAN)`.
  scope: WORKSPACE_SCOPED (work package) / CURRENT.
- **SCHEDULE_MODE_MAX** ("current approved reading" = highest approved candidate for ONE activity/line;
  this is NOT a portfolio rollup) — `actuals_spine.py:619` (activity), `project_earned_value_engine.py:479`
  (budget-line bucket). Documented as governed single-value derivation; left in place (correct, single-owner).
- **SCHEDULE_WEIGHTED_ROLLUP** (EVM physical %, weighted by `_activity_weight`) — owned by
  `project_earned_value_engine._weighted_average` (`:802/:813`). A DIFFERENT concept; intentionally NOT
  collapsed into the shared lib (tightly coupled to EVM weighting). Documented as its canonical owner.
- NON-FORMULA (excluded): `project_schedule_authority.py` 1782/1800/1816/1838/1858 = CSV export column
  headers + reads of already-stored `approved_percent_complete`; 134/1683/1703 = alias maps; 412/909/1053/681/707
  = PC-STORED clamps of an entered/approved value (max(0,min(100,…))).

## PC-STORED — AUDIT RESULT (UNKNOWN ≠ 0)
- Only field whose contract genuinely permits unknown: daily-report activity `percent_complete: Optional[float]=None`
  (`daily_reports.py:293`). Its PRIMARY human surface `ViewDailyReport.jsx:752` ALREADY renders blank (not "0%")
  for null/"" — the correct reference pattern. No change needed there.
- `sections.jsx:1113` (`overall_percent_complete`) / `1212` (`progress_percent`), `PmJobsRead.jsx:202`,
  `PmCostCodeAssignmentCard.jsx:99`: backend always returns a NUMBER (foundation/schedule_engine default 0.0),
  so `|| 0` never triggers -> no unknown state -> no lie. (These are PC-COST/PC-SCHEDULE, 0 is a legitimate default.)
- `dailyReportSummaryPayload.js:70`, form drafts (`PmProjectSchedule.jsx`, `sections.jsx:1381`,
  `ScheduleActualsWorkspace.jsx:89`): coercion/`?? 0` are EDIT-input defaults / internal summary-math inputs, not
  truth displays. Left as-is (changing would risk summary/submission regressions for no human-visible truth gain).
- `PmMondayReviewWorkspace.jsx:343` (`readiness.completion_percent || 0`): PC-SCHEDULE/monday concept; absent
  readiness -> 0% is a legitimate business default (no readiness computed). Documented; not a PC-STORED lie.
- CONCLUSION: PC-STORED is already truthful; no unsafe change manufactured.

## PC-COST — DEFERRED AUDIT (do not migrate until denominator proven)
Distinct denominators identified (NOT interchangeable — will become explicit KPI IDs at migration):
- `foundation.py:674 overall_percent_complete` = weighted_installed_qty / authorized_qty (QUANTITY-BASED).
- `oppc_execution.py:641 percent_complete` = total_actual_qty / total_planned_qty (QUANTITY-BASED).
- `pm_routes.py:303 cost_code_progress_percent` = downstream of overall_percent_complete.
- EVM (`project_earned_value_engine`) = earned value / budget (COST/EV-BASED) — different concept again.
=> PC-COST must be split into `PC-COST-QUANTITY` (installed/estimated qty) vs `PC-COST-EARNED` (EV/budget)
   before any migration; do NOT let cost completion inherit schedule semantics.
