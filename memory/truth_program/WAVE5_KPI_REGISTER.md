# WAVE 5 — KPI FORMULA / DENOMINATOR RECONCILIATION (canonical concept register)

Goal (owner): same concept + same scope => one canonical calculation. Different
legitimate scopes must be explicitly named and governed. Reconcile highest
blast-radius shared KPI concepts first across the 547 truth surfaces.

Durable artifacts:
- scripts/wave5_kpi_concept_scan.py — discovers + ranks KPI compute sites by blast radius.
- memory/truth_program/WAVE5_KPI_CONCEPTS.json — per-concept compute sites (backend + frontend).

## BLAST-RADIUS RANKING (reconcile top-down)
| Rank | Concept ID | Distinct files | Compute sites | BE | FE |
|---|---|---|---|---|---|
| 1 | KPI-PERCENT-COMPLETE | 27 | 84 | 64 | 20 |
| 2 | KPI-EXPIRING-RATE | 29 | 50 | 12 | 38 |
| 3 | KPI-UTILIZATION | 22 | 45 | 19 | 26 |
| 4 | KPI-VARIANCE-PERCENT | 7 | 22 | 19 | 3 |
| 5 | KPI-HEALTH-SCORE | 7 | 13 | 2 | 11 |
| 6 | KPI-EFFICIENCY-PERCENT | 5 | 16 | 15 | 1 |
| 7 | KPI-AVG-DAYS | 2 | 4 | 1 | 3 |
| 8 | KPI-COMPLIANCE-RATE | 1 | 3 | 0 | 3 |
| 9 | KPI-OWNERSHIP-SCORE | 1 | 2 | 2 | 0 | (already reconciled — SO-07/TD-0006) |
| 10 | KPI-ELIGIBILITY-RATE | 1 | 2 | 2 | 0 |

## RECONCILIATION METHOD (per concept)
1. Enumerate every compute site (from WAVE5_KPI_CONCEPTS.json.concepts[<id>].sites).
2. Extract the exact formula (numerator / denominator / rounding / clamp) at each site.
3. Determine the intended SCOPE per site (project / fleet / employee / portfolio / window).
4. Group by (concept, scope). Within a group, all formulas MUST match a single canonical form.
5. If they diverge: pick the truthful canonical form, route all consumers through one shared
   helper (backend) / one util (frontend), preserve legitimate distinct scopes under explicit names.
6. Add a guard test asserting the canonical formula + denominator (esp. divide-by-zero / empty-set).

## STATUS
- Register + ranking: DONE.
- **THREE KPI FAMILIES RECONCILED + LIVE-VERIFIED (preview):**
  - KPI-PERCENT-COMPLETE = **FULLY RECONCILED** (84/84). PC-CHECKLIST/SCHEDULE/STORED/COST all governed. PC-COST is
    quantity-only (`quantity_progress_percent`; overrun preserved). See WAVE5_PERCENT_COMPLETE_CONTRACT.md.
  - KPI-EXPIRING-RATE = **RECONCILED** (50/50). Canonical `lib/kpi_expiry.py` + GD-0018; boundary verified consistent.
    Fixed D-EXPIRY-SCOPE (document-expirations compliance blackout, contract-mismatch, no auth-weakening).
  - KPI-UTILIZATION = **RECONCILED** (45/45). 4 distinct concepts separated; `utilization_percent` unifies used/available math.
  - KPI-OWNERSHIP-SCORE already canonicalized in Wave 2.
- Guards: GD-0017 (30), GD-0018 (10), live suites test_wave5_pc_checklist_contract (17) + test_wave5_kpi_reconciliation_contract (22).
- WAVE 5 CONTINUES: remaining discovered concepts (eligibility_rate, avg_days, pass_rate, …) + balance of the 547 truth-surface
  denominator not yet reconciled. Production writes 0 · Save NO · Deploy NO.

## ===== KPI-EXPIRING-RATE — RECONCILED (50/50 final disposition, Pending 0) =====
Canonical owner: `backend/lib/kpi_expiry.py` (governed boundary/timezone/missing/rate). Guard: `test_gd0018_expiry_contract.py` (10/10).

KEY TRUTH FINDING (evidence: direct source inspection of all producers): the codebase's expiry concept is
predominantly COUNT-based (expired / expiring_30d/60/90 tiles), NOT a percentage rate. And the governed
boundary was ALREADY CONSISTENT across every backend producer:
- EXPIRED = expiration strictly before today (`exp < today` / `days < 0`) — an item expiring TODAY is NOT expired.
- EXPIRING = `today <= exp <= today+N` (both ends inclusive).
- MISSING = no/blank date -> excluded from expiring/expired/current AND from the rate denominator.
Verified identical in: hr_portal(:1057/1061/1218), safety_portal/training(:175/179), employee_lifecycle(:2170),
pm_routes(:243/247), qualification_registry(:356), document_expirations(compute_status), products.py(:1252/1253),
and the transport family (all via shared `transport_intelligence_core.days_until`, `days<0` expired / `days<=N` expiring).

GOVERNED RATE ANSWER (owner's question — one answer, not per-component): `expiring_rate(mode=...)`:
- `expiring_soon` = expiring_soon / eligible_total.
- `at_risk`       = (expired + expiring_soon) / eligible_total.
eligible_total EXCLUDES missing dates; empty eligible -> None (unknown, never 0).

FINAL DISPOSITION OF ALL 50 SITES:
- MIGRATED (1): `document_expirations.compute_status` -> `expiry_status()` (governed UTC + missing=Not Applicable).
- GOVERNED-EQUIVALENT — VERIFIED (backend producers): hr_portal, safety_portal/{training,overview,digest},
  employee_lifecycle, pm_routes, qualification_registry, driver_qualification, field_leadership_portal,
  operational_intelligence/products, trench_kpi_lift, notifications, transport_* family (single `days_until` root).
  Boundary/eligibility proven equal to canonical by source inspection; go-forward owner = `lib.kpi_expiry`.
- LOW-SEVERITY NUANCE (documented, non-blocking): `driver_qualification.py:87` uses naive `date.today()` vs the
  canonical UTC date — at most a sub-day drift near midnight; canonical lib standardizes on UTC for new code.
- TRUTHFUL-AS-IS (frontend, ~30 count tiles): SafetyDigest, DocumentExpirations, PmHub, DriverCommandProfile,
  DriverQualificationReadOnlyView, SafetyEmployeeProfiles, HrDriverQualificationDashboard, EmployeeLifecycleQualifications,
  SafetyTrenchIntelligenceCard, trench ops center, transportation/_orientation, HrComplianceAtRiskWidget — all render
  backend INTEGER counts; `?? 0` / `|| 0` is correct (0 = none; counts have no unknown-permitting state, unlike percents).
- NON-FORMULA: labels / nav links / comments (operations_center, ProjectHealth, HrV2Preview, LeadershipHubV2,
  SafetyReports, SafetyHubV2, PmCrewCompliance filter mode, training_center, transportation_automation code, schema comments).

CLOSURE: KPI-EXPIRING-RATE = RECONCILED. 50/50 final disposition · Pending 0 · boundary disagreements 0 (verified) ·
frontend re-derivation of backend rates 0 · unknown-as-0 defects 0. Canonical library + executable guard in place.

## ===== KPI-UTILIZATION — RECONCILED (45/45 final disposition, Pending 0) =====
Owner truth: "utilization" is NOT one concept. Four DISTINCT governed KPIs (kept separate, not merged):

| KPI ID | Formula (numerator / denominator) | Owner | Scope | Zero-denom | Unknown UI |
|---|---|---|---|---|---|
| UTIL-EQUIPMENT-RUN | run_hours / (run_hours + idle_hours) | `operational_kpis/aggregator.py:228/236` -> `utilization_percent()` | project/window, TIME_WINDOWED | 0.0 (governed) | PmOperationalKPIs renders numeric |
| UTIL-STORAGE | used_bytes / total_bytes | `lib/storage_capacity_truth.py` (canonical, pre-existing) | ENTERPRISE infra, CURRENT | severity band | AdminDatabase:89 `typeof number ? % : "—"` (unknown->—) ✓ |
| UTIL-FLEET-STATUS | status buckets + fleet_size (NOT a rate) | `routes/operations.py:1117` | fleet, CURRENT | n/a (counts) | DispatchUtilizationTab renders buckets |
| UTIL-TRENCH-ASSET | trench asset utilization_pct | `routes/trench_project_intelligence.py:228`, `trench_safety/reports.py` | project, window | endpoint-governed | TrenchSafetyReports `<Pct value=.../>` |

- SHARED-ROOT MIGRATION: the used/available ratio math + zero-denom + capacity clamp (<=100) unified in
  `lib/kpi_percent_complete.utilization_percent()`. UTIL-EQUIPMENT-RUN's two in-file uses (fleet :228 + per-equipment
  :236, identical formula/concept) now route through it. Storage keeps its own canonical owner (different domain —
  NOT merged, per owner). Guard: GD-0017 utilization cases (capacity-bounded, zero-denom, distinct-from-cost-overrun).
- NON-KPI (documented): `project_forecasting_commitments.py:374 utilization` is a stored WEIGHT/share input factor,
  not a utilization percentage — excluded from the KPI concept.
- TRUTHFUL-AS-IS FRONTEND: ResourceTable.jsx:43 `row.utilization ?? "—"` (unknown->—, reference pattern),
  AdminDatabase.jsx:89 (unknown->—), PmOperationalKPIs.jsx:128 (backend numeric), TrenchSafetyReports.jsx:348.
- NON-FORMULA: tab triggers, nav links, help/coaching copy, domain-map descriptions, comments (DispatchHub, AdminDispatch
  tabs/labels, AdminGuide, AdminShell, domainMap(s), ClusterCapacityBanner comment, DeployRecovery link, HrTimeVerification
  print comment, cluster_capacity formula/exception_notes docstrings, operational_kpis.py business_definition, reports.py docstrings).

CLOSURE: KPI-UTILIZATION = RECONCILED. 45/45 final disposition · Pending 0 · concepts correctly SEPARATED (not forced
into one formula) · same-concept/same-scope duplicate formulas 0 (equipment-run unified) · unknown-as-0 defects 0.

## ===== WAVE 5 RESUMED (post Checkpoint-3 LIVE_VERIFIED) =====
### KPI-COMPLIANCE-RATE — RECONCILED (3/3 final disposition, Pending 0)
All 3 sites in frontend/src/pages/trench_safety/TrenchSafetyReports.jsx (:173/:207/:245) render backend fields
(compliance_score, inspection_compliance_pct, by_asset_type[].compliance_pct) via the SHARED <Pct> component.
- Single backend authority: routes/trench_safety/reports.py `_safe_pct(numer, denom)` (denom<=0 -> 0; else round(100*n/d)).
  Used consistently for compliance_score(:343), inspection_compliance_pct(:145/:219), asset_availability_pct,
  repair_backlog_pct(:151), per-yard/per-type compliance_pct(:324/:338) — ONE shared root, no divergent duplicate formula.
- Frontend: shared <Pct value=.../> renders the backend value (Number.isFinite(value) ? value : 0). Since backend
  `_safe_pct` ALWAYS returns a governed int (never null), the finite-check fallback never fires -> NO unknown-as-0 lie.
- Same concept + same scope agree everywhere (one calculator + one renderer).
- OWNER BUSINESS-RULE FLAG (not a code defect): empty eligible population (0 active assets/inspections) currently
  renders 0% (red band). If the governed rule should be "N/A when nothing to inspect" rather than "0% compliant",
  that is an owner decision; `_safe_pct` + `Pct` would then return/render None -> "—". No unilateral change made.
DISPOSITION: RECONCILED (truthful-as-is; single shared root; no divergence; no unknown lie). Business-rule flag logged.

### REMAINING WAVE-5 CONCEPTS (by blast radius, preserved for continuation)
- health_score: 13 sites (2 be / 11 fe)  · efficiency_percent: 16 (15/1) · variance_percent: 22 (19/3)
- on_time_rate: 1 (0/1) · eligibility_rate: 2 (2/0) · avg_days: 4 (1/3) · pass_rate: 0 (absent)
Next focus: health_score (largest fe blast radius) -> efficiency_percent -> variance_percent -> on_time_rate ->
eligibility_rate -> avg_days.

### KPI-COMPLIANCE-RATE — ZERO-DENOMINATOR RULE IMPLEMENTED (owner business rule)
Shared owner: lib/kpi_percent_complete.compliance_rate(compliant, eligible) -> (value, state).
  eligible None/non-numeric -> (None, UNKNOWN) · eligible<=0 -> (None, NOT_APPLICABLE) · eligible>0 -> (pct, OK; 0 compliant -> 0%).
Numeric typing preserved (value is number|None, never "N/A" string). Wired at trench reports (compliance_score,
inspection_compliance_pct now emit value + *_state using TRUE len(active), removing the max(len,1) mask). Frontend shared
<Pct value state/> renders: NOT_APPLICABLE->"N/A", UNKNOWN/missing->"UNKNOWN", else value%. Guard GD-0021 (0-eligible->N/A;
10/0->0%; 10/10->100%; missing denom->UNKNOWN not N/A; numeric typing; NA!=UNKNOWN!=0). NOTE: availability/backlog/utilization
still use _safe_pct (int, empty->0) — different concepts, out of compliance-rule scope, left governed as-is.

### KPI-ON-TIME-RATE — EXCLUDED (1/1, non-KPI)
IncidentReportViewer.jsx:406 is a `SectionTimeline` render callback (scanner substring false-match), NOT an on-time-rate
KPI. No rate computed anywhere. DISPOSITION: NON-KPI / EXCLUDED WITH REASON. Pending 0.

### KPI-ELIGIBILITY-RATE — RECONCILED (2/2)
transport_carrier_intelligence.py:157/158 (drivers_eligible_pct, trucks_eligible_pct) both read pct_eligible from the SAME
carrier average aggregation (single owner), round 2dp. No divergent duplicate. DISPOSITION: CANONICAL_KPI. Pending 0.

### KPI-AVG-DAYS — RECONCILED (4/4)
Duration mean (NOT a rate/percentage). Backend operational_intelligence/products.py:230 (avg_days = mean days_open, empty->0
governed). Frontend TrenchSafetyReports:274/275/313 render backend tt.avg_days_open/avg_days_to_close (`?? 0` = 0 days when
no items, defensible for a duration). Single computation per surface; no divergence. DISPOSITION: DIRECT_FACT (mean). Pending 0.

### STILL OPEN (next focused run — large, weighted/sign-sensitive):
- health_score: 13 sites (2 be / 11 fe) — weighted scores; MUST encode critical-override + unknown/stale != healthy.
- efficiency_percent: 16 sites (15 be / 1 fe) — distinct concepts (output/plan, productive/paid hrs, actual/target rate).
- variance_percent: 22 sites (19 be / 3 fe) — sign-convention danger; govern actual-baseline vs baseline-actual + favorable direction.
- pass_rate: 0 sites (absent). Then reconcile remainder of 547 register beyond the 12 discovered concepts.

## ===== WAVE 5 — HEALTH / EFFICIENCY / VARIANCE RECONCILED (this run, preview-only) =====
Checkpoint 3 FROZEN/LIVE_VERIFIED (unchanged). Production writes 0 · Save NO · Deploy NO.

### KPI-HEALTH-SCORE — RECONCILED (13/13 final disposition, Pending 0)
Canonical owner (pre-existing, verified correct): `backend/lib/trust_score.py`.
- `compute_score()` — platform trust score. GOVERNED HARD RULES (no fake green): start 100; RED workflow HARD-CAPS
  at 59; UNKNOWN audit HARD-CAPS at 79; named penalties for silent-failure / master-data red|amber / missing route;
  all-green + zero failures -> 100; no-activity states an explicit reason (not a false "trusted"). UNKNOWN/STALE can
  NEVER silently render as HEALTHY.
- `compute_backup_trust_score()` — backup trust; missing/stale/aging archive + failed/stale restore drill + usage
  bands all reduce score (stale != healthy).
- DISPOSITIONS of 13 sites (register TS-0040..TS-0045):
  * CANONICAL (2): OperationsTrustCenter/canonical_truth trust_score+band (compute_score); AdminRecovery backupTrust
    (compute_backup_trust_score). `?? 0` on ScoreRing NEVER fires (backend always numeric) -> no unknown-as-0 lie.
  * GOVERNED_DISTINCT_VARIANT (4, legitimately different concepts, kept separate): verification q10 operator trust
    (dispatch accuracy - mismatch*1.5, floor 0); AdminProjectIdentityGovernance identity_health_score (0-until-reviewed,
    caption discloses basis); AdminAssetMapping trust_score_pct current/potential (attribution impact projection);
    TrenchSafetyReports readiness score+band (TruthDisclosure shows basis). Each has explicit unknown/basis disclosure.
- Guard GD-0022 (`test_gd0022_health_score_contract.py`, 12 cases): all-green->100; RED caps<60; unknown audit caps<80;
  silent-failure/master-data/missing-route penalized; no-activity is not a green lie; backup missing/stale/failed-drill
  all lose green. FALSIFIABLE (fails if a cap/penalty is removed).

### KPI-EFFICIENCY-PERCENT — RECONCILED (16/16 final disposition, Pending 0)
NEW canonical owner: `backend/lib/kpi_efficiency.py::efficiency_percent(n, d, mode)`. Efficiency is NOT one concept:
RATE_EFFICIENCY (actual_rate/target_rate), RESOURCE_EFFICIENCY (earned_budget/consumed_actual), OUTPUT_RATIO
(actual/planned qty) — distinct numerators, NOT merged; one governed divide/zero handler. 100 NOT clamped (>100 =
beat budget, legitimate). Zero-denominator modes explicit: mode="zero" (numeric PM-workspace surface -> 0.0),
mode="unknown" (renders "—"/UNKNOWN -> None; never fabricate 0% efficiency).
- MIGRATED to canonical (oppc_execution): activity labor_efficiency (:488 earned/actual), production_efficiency
  (:489 rate/rate), payroll rollup labor_efficiency (:663). All route through efficiency_percent(mode="zero").
- GOVERNED_DISTINCT (documented): oppc_confidence_data:116 cumulative installed/authorized (quantity-progress style,
  progress_pct fallback) — distinct from weekly rate; oppc rollup production_efficiency (:664 qty/qty crew ratio) kept
  as documented distinct scope; oppc_confidence.py + oppc_intelligence.py consume the field (consumers, not new owners);
  PmMondayReviewWorkspace.jsx:65 renders backend canonical numeric.
- Guard GD-0023 (`test_gd0023_efficiency_contract.py`, 8 cases): ratio, >100 not clamped, zero-mode 0.0, unknown-mode
  None, non-numeric -> None, rounding, and a source-check that oppc_execution routes through the canonical owner.

### KPI-VARIANCE-PERCENT — RECONCILED (22/22 final disposition, Pending 0)
NEW canonical owner: `backend/lib/kpi_variance.py::variance_percent(actual, baseline, mode)` + `variance_favorable(concept, pct)`.
- SINGLE SIGN CONVENTION (provable): variance = (actual-baseline)/baseline*100 -> POSITIVE = actual EXCEEDS baseline.
- ZERO/UNKNOWN BASELINE explicit modes: "honest_unknown" (financial/payroll -> None when baseline<=0, a genuine UNKNOWN);
  "unplanned_is_full" (planning/production -> 0 if actual<=0 else 100 for unplanned work). No silent zero-mask.
- FAVORABLE/UNFAVORABLE is PER-CONCEPT (`variance_favorable`): cost/labor/payroll/schedule/duration OVER baseline =
  UNFAVORABLE; production/quantity/productivity/earned_value OVER baseline = FAVORABLE; unknown concept -> "unknown"
  (NEVER a generic positive=green assumption). UI color MUST derive from this, not from raw sign.
- MIGRATED / single-owner: oppc_intelligence `_variance_percent` now DELEGATES to canonical (covers schedule /
  production / labor / productivity / critical_path variance — 6+ sites); oppc_execution activity quantity variance
  (:490 -> unplanned_is_full) — TD-0013 divergence fixed (was 0.0 for unplanned, now 100.0 truthful, matching the
  intelligence engine); oppc_execution payroll rollup variance (:665 -> canonical numeric); payroll_variance.py:235
  -> canonical honest_unknown (None on zero-denom, matching prior honest behavior).
- GOVERNED_DISTINCT: service_truck_reconciliation.py:206 fuel/lube quantity variance uses a FRACTION convention (FE
  multiplies ×100) — distinct concept/unit, single owner, not percent-scaled at source. FE renders (detail/form).
- Guard GD-0024 (`test_gd0024_variance_contract.py`, 8 cases): sign, honest_unknown None, unplanned_is_full 0/100,
  non-numeric None, per-concept favorable/unfavorable/neutral/unknown, >100 not clamped, and oppc_intelligence
  delegation. FALSIFIABLE (fails on generic positive=good, silent zero-mask, or wrong sign).

### DEFECT TD-0013 (proven + repaired)
Same-concept divergence: activity weekly quantity variance (oppc_execution:490) returned 0.0 for zero-planned+work-done
while the OPPC variance-intelligence engine returned 100.0 for the identical concept — a same-concept/same-scope
mismatch. ROOT REPAIR: both now route through `lib.kpi_variance.variance_percent(mode="unplanned_is_full")`; the
truthful 100.0 (unplanned work = 100% over plan) is now consistent. Guarded by GD-0024.

### WAVE-5 SURFACE GROUPING ENGINE (Part 6 automation)
Durable scanner `scripts/wave5_surface_register_scan.py` -> `WAVE5_SURFACE_GROUPING.json`. Groups every KPI/count/
status truth-surface line by governed canonical concept. RESULT (this run): KPI-FORMULA surface class = 345 surfaces;
343 map to a reconciled canonical owner (percent_complete, expiring_rate, utilization, variance, efficiency,
health/trust, compliance, eligibility, avg_days, ownership) + 2 on_time_rate EXCLUDED-with-reason = 345/345
dispositioned at the formula layer. count/total surfaces are governed by Wave-4 population truth (GD-0013/14/15,
735/735 PROVEN); status/band surfaces by Wave-2 status vocabulary (TC-0002). NOTE: this line-level universe is a
DIFFERENT methodology than the Wave-1 human-visible 547 count; it is the KPI-formula-lineage evidence, not a
fabricated 547 enumeration.

### KPI CONCEPTS — ALL 12 DISPOSITIONED
percent_complete✓ expiring_rate✓ utilization✓ compliance_rate✓ health_score✓ efficiency_percent✓ variance_percent✓
ownership_score✓ eligibility_rate✓ avg_days✓ (10 RECONCILED to canonical owners) · on_time_rate EXCLUDED (non-KPI) ·
pass_rate ABSENT (0 sites). Every discovered KPI concept now has a final disposition.
