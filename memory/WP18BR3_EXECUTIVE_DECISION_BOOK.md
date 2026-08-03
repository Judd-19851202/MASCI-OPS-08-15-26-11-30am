# WP-18BR3 Executive Constitutional Decision Book

Date: 2026-08-03  
Work Package: WP-18BR3 — Constitutional Architecture Review  
Scope rule: documentation only. No application code, UI, API, workflow, database schema, or runtime changes were performed.

## Executive purpose

WP-18BR3 answers one question:

**If the platform were rebuilt today using everything we have learned, what would remain exactly the same, what would change, and why?**

This is not a review of WP-18BR2 alone.  
`WP17_*`, `WP18A_*`, `WP18B_*`, `WP18BR_*`, `WP18BR2_*`, `PRD.md`, `ROADMAP.md`, `CHANGELOG.md`, and the actual platform architecture were treated as independent evidence.

## Primary answer

If rebuilt today, the platform should **not** be rebuilt from scratch.

The highest long-term value with the least technical debt comes from:

1. **keeping the current operational spine**
2. **extending the enterprise governance and project-controls layers already present**
3. **consolidating and simplifying overlapping executive/read-side surfaces**
4. **building only the genuinely missing finance-control layers**

## BR3 constitutional conclusion in one sentence

**The platform is more preservable than WP-18BR2 concluded.**  
The strongest BR3 answer is not `NO-GO`; it is **GO WITH REQUIRED AMENDMENTS**.

## Why BR3 changes the constitutional reading

### 1. The enterprise hierarchy is not absent; it is under-propagated

WP-18BR2 treated enterprise hierarchy as a likely `Build New` domain. BR3 challenge found stronger existing architecture than that conclusion allowed:

- identity snapshots already carry `tenant_id`, `company_id`, `division_id`, `department_id`, and `region_id`  
  `backend/services/enterprise_governance.py:202-233`
- role registry already defines authority levels and managed scope  
  `backend/services/enterprise_governance.py:760-805`
- governance defaults already map actors into tenant/company/division/department/region scope  
  `backend/services/enterprise_governance.py:858-905`
- governance already seeds an organization tree rooted at `MASCI` with company → division → department nodes  
  `backend/services/enterprise_governance.py:1536-1551`

**BR3 finding:** the deficiency is **propagation**, not architectural absence.  
That changes the recommendation from `Build New` to **`Extend`**.

### 2. Finance architecture is weak, but not blank

WP-18BR2 correctly found no full Budget Hierarchy or Earned Value owner. BR3 challenge agrees those two layers still do not exist. But BR3 also found more reusable financial groundwork than BR2 emphasized:

- project P&L snapshot exists and is sourced directly from `daily_reports`  
  `backend/server.py:6553-6754`; `frontend/src/pages/ProjectPnlPage.jsx:28-339`
- PO workflow already tracks estimated and approved amounts with approval and receipt stages  
  `backend/routes/po_requests.py:586-772`
- cost-code planning already carries `contract_value`, `margin`, `margin_percent`, and `target_man_hours` fields  
  `backend/services/cost_codes/foundation.py:15`
- OPPC execution already computes budget production rates and labor-efficiency-style metrics  
  `backend/services/cost_codes/oppc_execution.py:309-329,486-587`

**BR3 finding:** Budget Hierarchy and Earned Value still require new constitutional owners, but **upstream architecture should be preserved, not reworked**.

### 3. Executive reporting is the real redesign zone

WP-18BR2 was directionally correct that ODS, Project Health, KPI rollups, and legacy operational intelligence overlap. BR3 challenge agrees with the overlap, but reframes the action:

- ODS is explicitly additive/read-side  
  `backend/routes/ods_intelligence.py:71-123`
- Project Health is explicitly non-source-of-truth  
  `backend/routes/project_health.py:4-7`
- operational KPI routes explicitly exclude budget/cost truth  
  `backend/routes/operational_kpis.py:16-18,138-152`
- legacy operational intelligence still exists as a parallel digest/admin lane  
  `backend/operational_intelligence/routes.py:16-76`; `backend/operational_intelligence/engine.py:17-24,122-129`

**BR3 finding:** this is not a reason to withhold all implementation. It is a reason to **redesign the reporting hierarchy and retire the redundant legacy lane**.

## Preservation Report

Detailed preservation ledger: `WP18BR3_PRESERVATION_REPORT.csv`

### Preservation summary

| Category | BR3 count | Executive interpretation |
|---|---:|---|
| KEEP EXACTLY AS IS | 5 | These are already the right owners and should not be rebuilt. |
| KEEP WITH MINOR REFINEMENT | 6 | Valuable and usable now; only bounded clarification/tightening is needed. |
| EXTEND | 9 | Strong architecture exists and should remain the foundation for future work. |
| CONSOLIDATE | 1 | Real value exists, but duplicated seams should be merged. |
| REDESIGN | 1 | One area needs structural simplification to avoid future confusion. |
| RETIRE | 1 | Legacy overlap should be retired to protect clarity. |
| BUILD NEW | 2 | Only the genuinely missing finance-control layers justify a new subsystem. |

## What remains exactly the same

These should **not** be rebuilt:

1. `jobs_master` as the core project identity spine  
   `backend/server.py:6568-6576`
2. `project_team_assignments` as the roster/assignment authority  
   `backend/routes/project_team_assignments.py:824-847,878-1160`
3. `cost_code_registry` as the reusable cost-code definition master  
   `backend/routes/cost_codes.py:324-352`
4. weekly payroll variance as a distinct labor reconciliation lane  
   `backend/routes/payroll_variance.py:1-22,193-280`
5. governance/audit backbone as the authority guardrail  
   `backend/services/enterprise_governance.py:760-805`

## What changes

### Extend

- enterprise governance hierarchy propagation into read/reporting systems
- project cost-code planning
- schedule engine
- lookahead / planning lifecycle
- forecast history / overrides
- constraints architecture
- Asset Spine as the permanent equipment registry
- operator routing / portal hierarchy
- operational KPI rollups and project-controls reporting consumers

### Consolidate

- resource federation across cost-code demand, project-team roster, and dispatch deployment

### Redesign

- executive reporting hierarchy across ODS, Project Health, KPI rollups, and executive intelligence

### Retire

- legacy operational intelligence digest as a parallel executive lane

### Build New

- Budget Hierarchy
- Earned Value

## Investment protection answer

See: `WP18BR3_INVESTMENT_PROTECTION_ANALYSIS.md`

Short answer:

- **84% of the current architecture is preservable as foundation**
- **only 8% clearly requires net-new subsystem work**
- **the biggest risk is not under-building the platform; it is overreacting and rebuilding value that already exists**

## Enterprise readiness answer

The platform is **closer to enterprise-ready than BR2 concluded**, but not enterprise-complete.

### It already supports

- multi-role operations across admin, PM, shop, HR, safety, dispatch, field leadership, and executive portals  
  `frontend/src/app/routing/AppRoutes.jsx:698-1380`
- governance-aware authority levels and organizational metadata  
  `backend/services/enterprise_governance.py:202-233,760-805,858-905`
- equipment/company/region attributes in Asset Spine  
  `backend/services/asset_spine.py:161-177,457-472`

### It does not yet fully support without amendment

- clean propagation of enterprise scope through ODS/KPI/AI readers still defaulting to `masci`  
  `backend/routes/ods_intelligence.py:29,75-83`; `backend/routes/operational_kpis.py:173-187`; `backend/routes/ai_admin_config.py:47-52`
- controller-grade budget governance
- earned-value-based enterprise reporting
- one simplified executive reporting hierarchy

## Cross-system architecture answer

Detailed register: `WP18BR3_CROSS_SYSTEM_ARCHITECTURE_REGISTER.csv`

BR3 answer:

- **Most core systems do connect correctly.**
- **Very little of the operational platform is isolated.**
- **The main violations are overlap and missing finance authority, not disconnected modules.**

## Financial constitutional answer

Detailed review: `WP18BR3_FINANCIAL_CONSTITUTIONAL_REVIEW.md`

BR3 answer:

- enterprise financial management is **not ready as-is**
- but it **does not require rebuilding current project-controls work**
- the correct move is to build Budget Hierarchy and Earned Value **on top of** existing cost codes, daily reports, PO workflow, OPPC execution, and P&L reporting

## Operational constitutional answer

Detailed review: `WP18BR3_OPERATIONAL_CONSTITUTIONAL_REVIEW.md`

BR3 answer:

- scheduling, production, dispatch, equipment, safety, HR, shop, and PM flows already form one broad operational model
- the weak spots are **resource federation clarity**, **constraint dual-lane clarity**, and **executive reporting overlap**
- those are amendment problems, not rebuild problems

## Executive operator answer

Detailed review: `WP18BR3_EXECUTIVE_OPERATOR_REVIEW.md`

BR3 answer:

- PM, dispatch, shop, safety, HR, and field roles already have substantial value
- executive and accounting/finance roles are the least constitutionally complete because the reporting and financial model are still bounded

## Five-year review

Detailed review: `WP18BR3_FIVE_YEAR_REVIEW.md`

BR3 answer:

We will regret:

1. rebuilding the project-controls spine that already exists
2. leaving executive reporting overlap unresolved
3. pretending live P&L and PO amounts equal a full budget model
4. letting enterprise hierarchy stay present in governance but absent in downstream readers

## Rebuild test

Detailed matrix: `WP18BR3_REBUILD_TEST_AND_ROI_MATRIX.csv`

If the platform disappeared tomorrow:

- we would rebuild **project identity, cost-code registry, project cost-code planning, schedule, daily-report field capture, roster planning, Asset Spine, and governance** in nearly the same shape
- we would **not** rebuild the legacy operational intelligence digest
- we would **not** leave executive reporting as four overlapping read-side stories
- we would **not** pretend budget and EV already exist

## Final executive questions

### What should NEVER be rebuilt?
- `jobs_master` project identity spine
- cost-code registry
- project-team assignment authority
- daily-report field capture spine
- deterministic schedule engine foundation
- Asset Spine registry core
- governance/audit backbone

### What should NEVER be touched?
- the constitutional rule that derived read surfaces cannot become truth owners
- the split between reusable global cost-code definitions and project-specific planning truth
- the separation between governance enforcement and portal UX

### What absolutely MUST change?
1. enterprise hierarchy propagation into read/reporting layers
2. executive reporting hierarchy simplification
3. canonical Budget Hierarchy
4. canonical Earned Value derived layer

### What can wait?
- portal polish that does not alter data authority
- additional AI surfaces beyond bounded assistive use
- further executive dashboard proliferation

### What creates the highest ROI?
- extending the existing project-controls spine instead of rebuilding it
- adding Budget Hierarchy on the current cost-code / PO / P&L / production foundation
- simplifying executive reporting instead of growing more dashboards

### What creates the highest long-term risk?
- leaving finance authority undefined
- leaving enterprise scope propagation partial
- preserving overlapping executive readers without hierarchy

### What is overbuilt?
- overlapping executive read surfaces relative to the current decision needs

### What is underbuilt?
- finance authority: budget, actual-cost lineage, earned value

### What is duplicated?
- executive visibility lanes
- parts of resource planning semantics across demand, roster, and deployment

### What is missing?
- Budget Hierarchy owner
- Earned Value owner
- one authoritative executive reporting hierarchy

### What would be built differently from scratch?
- enterprise scope metadata would be propagated from governance into every reader from day one
- executive reporting would be one hierarchy, not several parallel read models
- the financial model would have been layered on earlier

### What should remain exactly as it exists today?
- project identity
- cost-code registry
- roster authority
- payroll variance lane
- governance/audit backbone

## Final gate

**GO WITH REQUIRED AMENDMENTS**

## Why the gate improved from BR2

BR2 was right about the missing finance layers and executive overlap.  
BR2 was too severe about how much existing architecture must change.

BR3 finds that:

- enterprise hierarchy already exists in governance form
- project-controls foundations are stronger than a NO-GO implied
- financial architecture is incomplete, but the missing layers sit on top of reusable upstream truth
- the remaining blockers are real but bounded enough to allow an implementation gate **with required amendments** rather than total withholding

## Blocking amendments before WP-18C

See: `WP18BR3_BLOCKING_AMENDMENTS.md`

The platform should move forward only if those amendments are accepted as governing architecture.