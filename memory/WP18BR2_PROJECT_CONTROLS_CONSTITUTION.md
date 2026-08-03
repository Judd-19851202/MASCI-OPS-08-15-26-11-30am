# WP18BR2 Project Controls Constitution

Date: 2026-08-03

## Constitutional position

Project Controls should be built on the existing platform, but only on the **corrected and enterprise-bounded** constitutional model.

That means:

- reuse existing engines where authority is real,
- extend or consolidate where truth already exists but enterprise semantics are incomplete,
- and authorize `Build New` only where no constitutional owner was evidenced.

## Project Controls constitutional matrix

| Capability | Current architecture assessment | Enterprise scalability assessment | Long-term technical debt risk | Recommended disposition | Avoids future rewrite? |
|---|---|---|---|---|---|
| Cost Codes | Real, reusable split between global definitions and project planning. | Strong base for multi-project use, but enterprise estimating/ERP hierarchy was not proven. | Medium | Reuse | Yes |
| Project Cost-Code Planning | Existing owner is clear on `jobs_master.assigned_cost_codes`. | Scales only if revision/lock/approval governance is made explicit before growth. | High | Extend | Yes, if amended before WP-18C |
| Schedule | Deterministic and explainable engine already exists. | Strong per-project, not yet proven as enterprise master-schedule authority. | High | Extend | Yes, if kept project-scoped until enterprise layer is defined |
| Lookahead | Existing lifecycle exists on `jobs_master.oppc_planning_lifecycle`. | Reusable, but not yet an explicit enterprise planning standard. | Medium | Extend | Yes |
| Forecasting | Forecast snapshots and overrides are already on the canonical schedule path. | Project-safe today; portfolio-scale synchronous refresh is already bounded. | High | Extend | Yes, if rollup posture changes before scale growth |
| Monday Review / Briefing | Real existing operational-control chain. | Useful at scale, but release hierarchy and portfolio semantics are still bounded. | Medium | Extend | Yes |
| Production | Real existing field actuals path, but not a single-owner domain once fact families are acknowledged. | Needs decomposition before enterprise reporting becomes trustworthy. | High | Extend | Yes, if fact families are formalized now |
| Constraints | Real standing workflow plus field-fact lane. | Enterprise-safe only if dual-lane ownership is explicit. | High | Extend | Yes |
| Crews / Labor | Existing planned roster, field hours, and weekly reconciliation all exist. | Strong ingredients, but one enterprise labor hierarchy was not proven. | High | Extend | Yes, if explicitly separated by role and purpose |
| Resources | Demand, roster, and deployment owners already exist. | Enterprise-safe only if the federation is narrated and governed as one model. | High | Consolidate | Yes |
| Equipment | Asset Spine is the strongest identity core. | Multi-provider/acquisition scale is possible only if registry and mappings stay explicitly subordinate. | High | Consolidate | Yes |
| Executive KPI / Reporting | Useful derived surfaces already exist. | Enterprise semantics remain overlapping and latency-bounded. | Very high | Consolidate | Yes, if done before more executive features are added |
| Budget Hierarchy | No owner evidenced. | Cannot scale because it does not constitutionally exist yet. | Very high | Build New | Yes |
| Earned Value | No owner evidenced. | Cannot scale because it does not constitutionally exist yet. | Very high | Build New | Yes |

## What survives unchanged

The following constitutional answers remain strong:

1. `cost_code_registry` should stay the reusable definition owner.
2. `jobs_master.assigned_cost_codes` should stay the project planning owner.
3. `schedule_engine.py` should stay the schedule computation path.
4. `daily_reports` should stay the primary field actuals spine.
5. `project_team_assignments` should stay the roster-planning owner.
6. Asset Spine should remain the permanent registry core for equipment identity.

## What changes under this final challenge

### 1. Project Controls is not just a project-scale question anymore

Every recommendation here is challenged against the user’s enterprise question:

- 5x–10x larger contractor
- multiple companies/divisions/business units
- multiple regions/states/DOTs
- acquisition integration
- new service lines without parallel systems

On that stricter basis, reuse still survives — but several enterprise contracts do not.

### 2. Enterprise operating hierarchy becomes a prerequisite

Project Controls cannot remain only `project_number`-centric while executive readers and AI/ODS layers still hardcode MASCI tenant assumptions. The platform now requires an explicit enterprise operating hierarchy as a constitutional prerequisite to scale-safe controls.

### 3. Finance-side controls remain blocked

PO workflow evidence, approved amounts, and project friction indicators do **not** add up to a budget constitution. Budget and Earned Value remain the two clearest absent controls domains.

## Constitutional rules for any future implementation

1. **Do not rebuild the existing cost/schedule/production spine.**
2. **Do not create a second owner for project planning, field actuals, roster planning, or asset identity.**
3. **Do not treat derived executive readers as canonical truth owners.**
4. **Do not start finance-side controls until Budget Hierarchy exists as a first-class owner.**
5. **Do not start Earned Value until Budget Hierarchy is constitutionally locked.**
6. **Do not scale the surface area faster than the enterprise hierarchy and operator navigation can absorb.**

## Constitutional determination

Project Controls is **architecturally viable on this platform**, but **not yet implementation-authorized** under the stricter WP-18BR2 standard. The platform is strongest when read as:

- a reusable project-controls foundation,
- with bounded but real enterprise ingredients,
- still requiring explicit enterprise and finance constitutions before WP-18C.