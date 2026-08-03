# WP18 ECAP Enterprise Hierarchy Constitution

Date: 2026-08-03

## Final hierarchy decision

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `INFERENCE`

The final WP-18C hierarchy is intentionally smaller than a generic enterprise ERP hierarchy.

It includes only the levels that solve a real operational, reporting, financial, or scaling need for MASCI and near-term enterprise growth.

## Included hierarchy levels

| Level | Proof label | Purpose | Owner | Identifier | Parent | Children | Data scope | Permissions / rollup | Archive behavior | Acquisition / migration behavior |
|---|---|---|---|---|---|---|---|---|---|---|
| Company | `SOURCE_VERIFIED` | top operating-company boundary | executive / enterprise governance | `company_id` | none | division, department, region, facility, project | enterprise-wide | company-level visibility and rollups | preserved permanently | additive for future companies; do not fork architecture |
| Division | `SOURCE_VERIFIED` + `INFERENCE` | business-line or operating division boundary | executive + operations leadership | `division_id` | company | department, region, project, facility | division-wide | divisional reporting and financial rollup | archived with hierarchy history | acquisition can map legacy units into divisions first |
| Department | `SOURCE_VERIFIED` | functional authority boundary | department leader | `department_id` | company or division | teams, roles, facilities | departmental | role and approval scoping | archived with personnel history | legacy departments map here without schema rewrite |
| Region | `SOURCE_VERIFIED` + `INFERENCE` | geographic operating boundary | regional operations leader | `region_id` | division or company | facilities, projects | regional | regional operational and financial rollup | historical snapshots retained | acquisitions may land into region before finer segmentation |
| Facility subtype (`plant` / `yard` / `shop`) | `INFERENCE` | physical operating base for fleet, materials, or maintenance | operations / shop leadership | `facility_id` + `facility_type` | region or division | equipment, stock, work orders | facility | facility-level operational rollup | retained historically even if closed | acquired facilities migrate here without new hierarchy class |
| Project | `SOURCE_VERIFIED` | primary execution and controls boundary | project manager | `project_number` | company / division / region | contract, phase, work package, cost code activity | project | project-level permissions, controls, reporting | preserved permanently | legacy projects map directly with no duplicate project root |
| Contract | `INFERENCE` | commercial container when project commercial scope needs separate tracking | PM + finance owner | `contract_id` | project | phase, change, budget lines | project-commercial | budget/revenue/billing rollup | preserved with commercial history | optional where one project has multiple contracts |
| Phase | `INFERENCE` | major project work partition | PM / superintendent | `phase_id` | contract or project | work packages, cost codes, activities | execution segment | schedule/budget/quantity rollup | retained in project history | used where bid and operations align on phases |
| Work package | `INFERENCE` | near-term execution bundle tying schedule, cost, and production together | PM / superintendent | `work_package_id` | phase | cost codes, activities, assignments | tactical execution | lookahead and field accountability | retained with planning history | additive; no project rewrite required |
| Cost code | `SOURCE_VERIFIED` | cost / quantity / production accounting key | project controls + finance | `cost_code` | work package or phase | activities, quantities, budget lines, actuals | cost-performance | financial and production rollup | preserved with full transaction history | aliases map to canonical enterprise library |
| Schedule activity | `SOURCE_VERIFIED` | schedule and lookahead execution key | PM / controls | `activity_id` / `cpm_activity_id` | work package / cost code | daily progress and forecasts | schedule-performance | schedule and EV rollup | preserved with revisions | imported/native activities must resolve to one canonical ID |
| Resource assignment layer | `SOURCE_VERIFIED` + `INFERENCE` | execution actors/resources: employee, crew, equipment, vendor, material | domain owner by type | typed assignment IDs | work package / activity / project | none | lowest execution grain | role-scoped | retained with event history | acquisitions map resources without changing project hierarchy |

## Explicitly excluded or deferred levels

| Candidate level | Final decision | Why |
|---|---|---|
| Holding company | `DEFER` | not required to solve MASCI’s current validated operating problem |
| Legal entity as a standalone hierarchy level | `DEFER` | can remain an attribute on company/contract until accounting integration demands more |
| District | `DEFER` | no evidence that MASCI currently needs it as an independent rollup level |
| Area | `DEFER` | same reason as district |
| Branch | `DEFER` | not evidenced as a meaningful current operating boundary |
| Office | `DEFER` | physical location can live as facility metadata until needed |
| Functional group | `DEFER` | can remain under department/team rather than a new hierarchy layer |
| Cost center as a standalone operational hierarchy level | `DEFER` | should arrive only if Budget Hierarchy or ERP integration proves it necessary |

## Final hierarchy law

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

WP-18C must implement only the included hierarchy levels above.  
Deferred levels may not be introduced casually during implementation.