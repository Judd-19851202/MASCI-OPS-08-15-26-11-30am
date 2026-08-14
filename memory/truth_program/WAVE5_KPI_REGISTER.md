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
