# WAVE 5 — CANONICAL % COMPLETE CONTRACT (KPI-PERCENT-COMPLETE)

Owner rule: same concept + same scope => one calculator. Different business KPIs that
merely share the label "% Complete" MUST be explicitly separated and governed — never
forced through one formula because they share a variable name.

Shared implementation: `backend/lib/kpi_percent_complete.py`.
Guards: `test_gd0017_percent_complete_contract.py` (20/20) + `test_wave5_pc_checklist_contract.py` (17/17, live preview).

## STATUS (updated this checkpoint)
- PC-CHECKLIST: **RECONCILED + MIGRATED + LIVE-VERIFIED** (preview).
- PC-SCHEDULE: **AUDITED + GOVERNED** (explicit modes) + 1 genuine mean-rollup migrated.
- PC-STORED: **AUDITED — TRUTHFUL AS-IS** (unknown≠0 honored; other `||0` over always-numeric backends).
- PC-COST: **RECONCILED** (quantity-only concept; canonical `quantity_progress_percent`; 3 cores migrated).
- **KPI-PERCENT-COMPLETE = FULLY RECONCILED — 84/84 final disposition, Pending 0.**

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

## PC-COST — RECONCILED (QUANTITY-only; no $-burn / EV / billing concept exists here)
Canonical calculator `quantity_progress_percent()` (overrun >100 allowed; zero/neg/missing denom -> governed empty).
KEY AUDIT TRUTH: every PC-COST site in this codebase is QUANTITY-based. There is NO actual-cost/budget burn,
committed-cost, earned-value-ratio, or billed/contract-value % Complete among the 84 sites. (`crew_productivity_percent`,
`labor_efficiency_percent`, `production_efficiency_percent`, `variance_percent` in oppc_execution are efficiency/variance
KPIs, NOT % complete, and were not flagged.) So PC-COST reduces to ONE governed concept with two governed scopes:

| KPI ID | Formula | Scope | Site(s) migrated |
|---|---|---|---|
| PC-COST-QUANTITY | installed_qty / authorized_qty * 100 (overrun allowed) | ENTERPRISE per-project, CURRENT cumulative | `foundation.py` per-code `progress_pct` (:628) + `overall_percent` (:670) |
| PC-COST-QUANTITY-WINDOWED | actual_qty / planned_qty * 100 | TIME_WINDOWED (Monday review week) | `oppc_execution.py:641` production_summary.percent_complete |

- `authorized_quantity` already reflects approved change orders (original + approved COs); calculator consumes the
  governed denominator (does not re-derive CO math).
- Consumer lineage: `foundation.overall_percent_complete` (:674) -> `foundation` job dict `cost_code_progress_percent`
  (:994) -> `pm_routes.py:303` -> frontend `PmJobsRead.jsx:202`, `PmCostCodeAssignmentCard.jsx:99`,
  `daily-report-v3/sections.jsx:1113` (all render the backend value; `|| 0` harmless — backend always numeric).
  `oppc_confidence_data.py:105` reads `overall_percent_complete` (consumer, no re-derivation).
- Guards: GD-0017 adds PC-COST-QUANTITY cases (0/100/overrun-not-clamped/zero-neg-missing-denom/change-order-denom/
  distinct-from-checklist-and-schedule/same-scope equality). GD-0017 = 26/26.

## ===== KPI-PERCENT-COMPLETE — FINAL DISPOSITION OF ALL 84 SITES (Pending = 0) =====
Every site has a final governed disposition (migrated / governed-owner / truthful-as-is / non-formula):

- MIGRATED to canonical calculator (8 compute sites): checklist -> asset_spine:427, employee_lifecycle:1377 (+3 per-field),
  HrCompletenessTile.jsx:169; schedule mean -> actuals_spine:570; cost -> foundation:628, foundation:670, oppc_execution:641.
- GOVERNED DISTINCT OWNER (documented, correct as-is): SCHEDULE_MAX_READING -> actuals_spine:619, earned_value:479;
  SCHEDULE_WEIGHTED_ROLLUP (EVM) -> earned_value:809/811 (`_weighted_average`); oppc_execution:641 downstream slots
  333/497/536/682 (derived from the migrated weekly percent); oppc_briefings:142 (reads monday completion_percent).
- PC-STORED (parse/clamp of an entered/imported value; unknown!=0 honored where nullable): authority:412/909/1053
  (import/entry clamp), foundation:194/484/516 (imported cost-line stored %), daily_reports:293 (Optional[float]=None),
  actuals_spine:603/634/681/707/761/797/846 (approved stored value clamp/round), schedule_engine:260/327/329/458 &
  foundation:390/393/397/423 (schedule-task stored progress), operational_kpis/aggregator:346-384 (stored snapshot
  passthrough), daily_summary:186/427/774 & pdf_render:1386 (render/export of stored daily % ), enterprise_governance:
  387/416 (Pydantic model default fields).
- TRUTHFUL-AS-IS FRONTEND (evidence: unknown!=0 where contract permits; else backend always numeric): ViewDailyReport.jsx:752
  (renders blank for null — reference pattern), sections.jsx:1113/1212 & PmJobsRead:202 & PmCostCodeAssignmentCard:99
  (backend always numeric -> `|| 0` never a lie), PmMondayReviewWorkspace:343 (absent readiness = 0% legit default),
  dailyReportSummaryPayload.js:70/193 (internal summary-math input, not a truth display), edit inputs
  PmProjectSchedule:117/140/203/815, sections.jsx:1381/1389, ScheduleActualsWorkspace:89 (form defaults).
- NON-FORMULA (headers / alias maps / comments): authority:134/1683/1703/1782/1800/1816/1838/1858/1135, pdf_render:1368/1372,
  dailyReportSchema.js:107, dailyReportSummaryPayload.test.js:44/68 (test fixtures).

### CLOSURE
KPI-PERCENT-COMPLETE = **FULLY RECONCILED**. Sites classified 84/84 · final disposition 84/84 · Pending 0 ·
unexplained formula differences 0 · duplicate local formula owners 0 (all same-concept/same-scope routed to one
calculator; distinct concepts explicitly separated) · unknown-as-0 defects 0 · same-concept/same-scope disagreements 0.

