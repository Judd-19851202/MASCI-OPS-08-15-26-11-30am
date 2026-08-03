# WP-18 Executive Constitutional Amendment Packet — Executive Decision Book

Date: 2026-08-03  
Packet: WP-18 ECAP  
Scope rule: documentation and implementation-contract work only. No application code, UI, API, database, permissions, configuration, runtime behavior, or integration changes were made.

## Executive answer

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

The exact architecture ForgedOps should implement next is:

1. **preserve the validated operational platform exactly where authority is already correct**
2. **preserve and govern the bounded read-side and operator surfaces that already work**
3. **extend the existing enterprise-governance, project-controls, cost-code, schedule, production, and equipment architecture**
4. **consolidate only the clearly duplicated federations**
5. **refactor executive reporting in place** so one hierarchy explains every visible executive number
6. **retire only the legacy reporting lane that duplicates newer executive surfaces**
7. **build new only two net-new subsystems:** Budget Hierarchy and Earned Value

## Primary executive question

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_AND_RUNTIME_VERIFIED`

**What exact architecture should ForgedOps implement next so MASCI gains enterprise-grade Project Controls, financial trust, executive intelligence, earned value, scalability, and operational integration while preserving the maximum amount of the validated platform already built?**

### Final answer

- Preserve the current project identity, roster, permissions/governance, cost-code definition library, planning spine, schedule engine, daily-report field capture, Asset Spine registry, portal structure, safety/dispatch/shop/HR/operator domains, PDF/email/report infrastructure, backup/recovery discipline, and validated workflow APIs.
- Govern and tighten the existing read-side surfaces so every executive and project-control number has one owner, one formula, one drill-down path, and one explanation.
- Extend the enterprise hierarchy already present in governance into downstream readers, reporting, and configuration inheritance.
- Build Budget Hierarchy as the financial-control layer **on top of** current project/cost/schedule/production/procurement truth.
- Build Earned Value as a derived layer **after** Budget Hierarchy is active.

## Final disposition law

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

All ECAP capability decisions use exactly one of:

- `PRESERVE_EXACTLY`
- `PRESERVE_AND_GOVERN`
- `EXTEND`
- `CONSOLIDATE`
- `REFACTOR_IN_PLACE`
- `RETIRE`
- `BUILD_NEW`
- `DEFER`
- `BLOCKED_PENDING_DECISION`

Authoritative source: `WP18_ECAP_CAPABILITY_DISPOSITION_MATRIX.csv`

## Final enterprise hierarchy

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `INFERENCE`

Authoritative source: `WP18_ECAP_ENTERPRISE_HIERARCHY_CONSTITUTION.md`

### Included levels for WP-18C

1. Company root (`MASCI` today; additive for future operating companies)
2. Division
3. Department
4. Region
5. Facility subtype nodes (`plant`, `yard`, `shop`) where operationally required
6. Project
7. Contract / project commercial container
8. Phase
9. Work package
10. Cost code
11. Schedule activity
12. Resource assignment layer (`employee`, `crew`, `equipment`, `vendor/subcontract`, `material line`)

### Explicitly not first-class in WP-18C unless later evidenced

- Holding company
- District
- Area
- Branch
- Office
- Cost center as a standalone operational owner

These remain `DEFER` or attributes, not independent WP-18C hierarchy objects.

## Final executive reporting hierarchy

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

Authoritative source: `WP18_ECAP_EXECUTIVE_REPORTING_HIERARCHY.md`

### Final rule

Every executive number rolls through one chain only:

- field / transaction / event fact
- canonical owner collection
- governed derived model
- role-appropriate reader
- drill-down path back to the canonical record

ODS, Project Health, KPI rollups, executive overview, and finance rollups may all continue to exist, but only under one explicit reporting hierarchy and KPI dictionary.

## Final Budget Hierarchy

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `PARTIAL_EVIDENCE` + `INFERENCE`

Authoritative source: `WP18_ECAP_BUDGET_HIERARCHY_CONSTITUTION.md`

### Final rule

The Budget Hierarchy is a **net-new subsystem** built over preserved upstream truth. It must separate:

- estimate
- awarded contract value
- original budget
- approved/current/revised budget
- contingency and reserve
- commitments
- actuals
- forecast to complete / estimate at completion
- revenue / billing / collections
- margin

## Final Earned Value architecture

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `PARTIAL_EVIDENCE` + `INFERENCE`

Authoritative source: `WP18_ECAP_EARNED_VALUE_ENGINE_BLUEPRINT.md`

### Final rule

Earned Value is the second and last justified `BUILD_NEW` subsystem. It is derived from:

- Budget Hierarchy
- cost-code activation and mapping
- approved schedule activities
- approved production / quantity truth
- governed actual-cost inputs

## Final source-of-truth law

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

Authoritative sources:

- `WP18_ECAP_AUTHORITY_AND_SOURCE_OF_TRUTH_MAP.md`
- `WP18_ECAP_DATA_OWNERSHIP_AND_STEWARDSHIP_MATRIX.csv`

### Core truth owners

- project identity → `jobs_master`
- roster and project staffing assignment → `project_team_assignments`
- cost-code library → `cost_code_registry`
- project planning → `jobs_master.assigned_cost_codes`
- daily field actuals → `daily_reports`
- payroll reconciliation → `payroll_variance`
- equipment registry → Asset Spine / `equipment_master` authoritative core
- procurement commitment workflow input → `po_requests`
- governance / permissions / approvals / audit → enterprise governance registry and ledgers
- Budget Hierarchy → new WP-18C budget subsystem
- Earned Value → new WP-18C derived subsystem

## Final Project Controls law

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

Authoritative sources:

- `WP18_ECAP_PROJECT_CONTROLS_OPERATING_MODEL.md`
- `WP18_ECAP_SCHEDULE_LOOKAHEAD_ACTUALS_ARCHITECTURE.md`
- `WP18_ECAP_PRODUCTION_QUANTITY_PRODUCTIVITY_MODEL.md`
- `WP18_ECAP_FORECASTING_COMMITMENT_ACTUALS_MODEL.md`

Project Controls is defined as one operating model joining estimate, budget, cost codes, schedule, lookahead, Daily Reports, quantities, resources, commitments, forecast, earned value, and executive reporting.

## What happens before WP-18C

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

Before WP-18C begins, this ECAP packet must be the accepted contract for:

1. enterprise hierarchy
2. reporting hierarchy
3. Budget Hierarchy
4. Earned Value
5. source-of-truth boundaries
6. preservation rules
7. implementation sequence
8. WP-18C package boundaries
9. acceptance and certification evidence

## What happens during WP-18C

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

WP-18C executes only through the sub-packages defined in `WP18_ECAP_WP18C_WORK_PACKAGE_MAP.md`, in the sequence defined by `WP18_ECAP_IMPLEMENTATION_SEQUENCE.md`, under the stop conditions defined by this ECAP.

## What is explicitly excluded from WP-18C

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

- broad rebuild of protected subsystems
- hidden net-new subsystems beyond Budget Hierarchy and Earned Value
- replacing the validated portal structure without evidence
- turning ForgedOps into the accounting general ledger without explicit authorization
- destructive migrations without recovery and reconciliation proof

## Final authorization gate

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

Authoritative source: `WP18_ECAP_FINAL_EXECUTIVE_AUTHORIZATION.md`

### Final result

**`AUTHORIZED_FOR_WP18C_WITH_ACCEPTED_CONDITIONS`**

WP-18C is authorized because this packet accepts and resolves the BR3 blocking amendments as a complete pre-implementation constitution.