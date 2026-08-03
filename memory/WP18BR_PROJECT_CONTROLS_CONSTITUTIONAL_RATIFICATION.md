# WP18BR Project Controls Constitutional Ratification

Date: 2026-08-03  
Purpose: Final executive challenge of the constitutional architecture for Project Controls before any future implementation authorization.

## Ratification table

| Capability | Should exist? | Constitutional owner after challenge | Who writes | Who approves | Who consumes | Who audits / certifies | Who reports | Who archives / restores | Conflict risk | WP-18BR status |
|---|---|---|---|---|---|---|---|---|---|---|
| Cost Codes | Yes | `cost_code_registry` for reusable definitions; `jobs_master.assigned_cost_codes` for per-project planning | Admin registry maintainers; PM/admin assignment managers | Publish / planning-lifecycle actions evidenced; full historical approval chain not fully proven | Schedule, forecast, OPPC, ODS, PM schedule | Trust Spine lifecycle on mutation path; OPPC owner audits | PM schedule, executive consumers | Mongo durability exists; explicit assignment revision restore model not fully proven | Medium | REVISED |
| Schedules | Yes | `schedule_engine.py` over assigned cost codes + Daily Report actuals | PM/admin schedule mutation through assignment rows / overrides | Forecast overrides and publish actions exist; enterprise master-schedule approval chain not fully proven | PM schedule, Monday review, briefings, executive summaries | Trust Spine planning lifecycle + OPPC review evidence | PM, OPPC, executive | Persisted source fields on `jobs_master`; derived schedule itself is recomputed | Medium-high | REVISED |
| Budgets | Yes | No current owner proven; requires new constitutional owner | Not evidenced | Not evidenced | PM financial adjacency, project health, future controller/CFO surfaces | Not evidenced | Not evidenced | Not evidenced | Very high | APPROVED as BUILD_NEW |
| Forecasting | Yes | `jobs_master.oppc_forecast_history` + `jobs_master.oppc_forecast_overrides` with `schedule_engine.py` | PM/admin snapshot + override actions | Snapshot/override governance exists; portfolio release hierarchy not fully proven | PM schedule, Monday briefing, confidence consumers | Trust Spine events on forecasting workflows | PM + executive recaps | Versioned/hashes for OPPC survivability are evidenced | Medium | REVISED |
| Production | Yes | Fact family, not one owner: `daily_reports`, `haul_cycles`, `payroll_variance_batches` by subtype | Field submitters; dispatch lifecycle; payroll variance workflow | Daily Report acceptance and payroll lifecycle exist; unified production approval hierarchy not singular | Schedule, OPPC, ODS, PM command, executive views | Trust Spine + workflow_state_events | PM, executive, safety, ops | Daily Reports and payroll batches durable; per-fact archival is proven unevenly | High | REVISED |
| Earned Value | Yes | No current owner proven; requires new derived owner after budget exists | Not evidenced | Not evidenced | Future executive / project-control consumers only | Not evidenced | Not evidenced | Not evidenced | Very high | APPROVED as BUILD_NEW |
| Resources | Yes | Federated: demand on `jobs_master.assigned_cost_codes`, roster on `project_team_assignments`, active dispatch on `dispatch_assignments` | PM/admin planning, staffing operators, dispatch | No single enterprise approval chain evidenced | PM staffing, command center, executive resource coordination | Existing workflow evidence is partial and federated | PM / executive consumers | Underlying stores durable; federation-level restore contract not explicitly proven | High | REVISED |
| Equipment | Yes | Asset Spine over `equipment_master` for identity; `dispatch_assignments` for deployment; `asset_mappings` remains provider-local mapping | Asset admins; dispatch operators; provider mapping operators | Asset mutation authority exists; external-ID ownership remains unresolved | PM command, fleet, executive resource coordination | Asset Spine and provider-local audit paths exist, but split remains | PM / fleet / executive consumers | Registry-side restore evidence exists; cross-provider identity restore is unresolved | High | REVISED |
| Crews | Yes | Planned crew/roster on `project_team_assignments`; field crew hours on `daily_reports.masci_crews`; weekly governed reconciliation on `payroll_variance_batches` | Staffing operators; field submitters; payroll variance workflow | Payroll variance lifecycle provides the strongest approval/finalization evidence | OPPC, HR, PM, executive labor views | `workflow_state_events` + Trust Spine | PM / HR / executive consumers | Batch durability and lifecycle evidence are proven; unified crew-planning archive policy not explicit | High | REVISED |
| Constraints | Yes | `daily_reports.constraints` for daily field facts; `operational_constraints` for standing blocker workflow | Field submitters; constraint operators | Standing workflow approvals partial; daily field facts ride Daily Report submission | PM command, OPPC, future schedule/KPI consumers | Daily Report lifecycle + partial constraint workflow evidence | PM / executive consumers | Durable storage exists; unified constraint restore/report hierarchy not explicit | High | REVISED |
| Lookahead | Yes | `jobs_master.oppc_planning_lifecycle` | PM/admin planning actions and weekly rollover | Publish/weekly rollover actions exist | PM schedule, Monday review, OPPC readiness | Trust Spine on publish/rollover workflow | PM / executive readiness consumers | Stored on `jobs_master`; explicit archive policy not separately proven | Medium | REVISED |
| Monday Review | Yes | `jobs_master.oppc_monday_reviews` | PM edits + OPPC workspace builder | Freeze/save actions exist | PM workspace, briefing builders | Trust Spine + upstream readiness evidence | PM and briefing consumers | Stored on `jobs_master`; briefing-side freeze/version history proven | Medium | APPROVED |
| Executive Reporting | Yes | Not singularly ratified yet; currently split across ODS, Project Health, OPPC recap, KPI dictionary, legacy intelligence | Multiple derived producers | No single constitutional approval owner proven | Executive, PM, admin, safety consumers | KPI dictionary governance exists but does not yet bind all lanes | Executive dashboards and briefings | Mixed; some cached/generated records exist, but singular executive restore contract is not proven | Very high | DEFERRED |

## Role-based constitutional challenges

### CFO / Controller challenge
- **What broke:** no budget owner, no earned-value owner, and PO approvals are not a budget hierarchy.
- **Evidence:** `po_requests.py`, `project_health.py`, `operational_kpis.py`
- **Outcome:** WP-18B financial conclusions are ratified only with the explicit admission that Budget and Earned Value are not yet architecturally present.

### COO / PMO / Superintendent challenge
- **What broke:** schedule and lookahead exist, but resource/crew/equipment/constraint bindings are not fully constitutionally explicit.
- **Evidence:** `OPPC_ENTERPRISE_RESOURCE_COORDINATION.md`, `OPPC_PAYROLL_RECONCILIATION_CERTIFICATION.md`, `OPPC_PERFORMANCE_SCALABILITY_VALIDATION.md`
- **Outcome:** reuse survives; completeness claims were revised downward.

### CIO / Chief Architect challenge
- **What broke:** Asset Spine was underrepresented, production/constraint truth was oversimplified, and executive KPI hierarchy is still overlapping.
- **Outcome:** WP-18B remains usable, but only with the amendments captured in WP-18BR.

## Cost code constitutional review

| Challenge area | Evidence-backed answer after challenge | Risk | Status |
|---|---|---|---|
| Global code definitions | `cost_code_registry` still survives as the reusable definition owner. No alternate ERP / estimating master was proven. | Medium | APPROVED |
| Project-specific planning | `jobs_master.assigned_cost_codes` survives as the project planning owner. | Medium | APPROVED |
| Imports / CSV / Excel | Bulk-replace and assignment update paths prove manual import-style governance exists, but not a fully ratified enterprise import contract. | High | REVISED |
| PDF / reporting | Schedule/PDF artifacts already consume the existing cost-code planning spine; they do not create a second owner. | Low | APPROVED |
| ERP / estimating sync | Not proven. The earlier audit explicitly did not prove external estimating/ERP synchronization into the registry. | High | DEFERRED |
| Versioning / locks / revisions | Publish/workflow events exist, but a full revision ledger, revision restore contract, and explicit lock hierarchy were not fully proven. | High | REVISED |
| Approvals | Publish actions and Trust Spine events exist, but complete long-horizon approval history is not yet strong enough for final constitutional lock. | High | REVISED |
| Cross-project reporting / executive rollups | Reusable as read-models only; they must remain derived consumers of the project assignment owner. | Medium | APPROVED |
| Daily reports / schedule / forecasting integration | Proven and strong: actuals flow from Daily Reports, schedules derive from the existing planning spine, and forecast history/overrides are already on the same path. | Low | APPROVED |
| Payroll / AI / KPI adjacency | These remain downstream consumers only. None of them proved a second cost-code truth owner. | Medium | APPROVED |

### Cost code constitutional determination

Cost-code architecture **survives**, but not as a casual “already solved” domain. It is ratified only as:

- reusable global definition truth on `cost_code_registry`
- reusable project planning truth on `jobs_master.assigned_cost_codes`
- reusable actuals truth on `daily_reports.cost_code_quantities`
- derived-only executive / AI / KPI consumers downstream

The missing piece is not a new engine. It is **revision, lock, approval, and import governance** around the existing owner.

## Schedule constitutional review

| Challenge area | Evidence-backed answer after challenge | Risk | Status |
|---|---|---|---|
| Project schedule | Proven. `schedule_engine.py` remains a real reusable engine over the cost-code planning spine plus Daily Report actuals. | Medium | APPROVED |
| Master / enterprise schedule | Not proven as a separately ratified constitutional layer. Project-level strength must not be overstated into enterprise master-schedule authority. | High | DEFERRED |
| Rolling lookahead / weekly plans | Proven as embedded lifecycle on `jobs_master.oppc_planning_lifecycle`, but still under-labeled and under-governed. | Medium | REVISED |
| Monday review | Proven and reusable on `jobs_master.oppc_monday_reviews`. | Low | APPROVED |
| Actual progress | Proven from Daily Reports into schedule progress. | Low | APPROVED |
| Forecasting | Proven on `jobs_master.oppc_forecast_history` and `jobs_master.oppc_forecast_overrides`, but executive refresh cost remains material. | Medium | REVISED |
| Constraints binding | Still weak. Automatic schedule propagation from `operational_constraints` was not proven. | High | REVISED |
| Resource / equipment / crew planning | Related, but not owned by the schedule stack itself. These remain federated adjacent domains. | Medium-high | REVISED |
| Executive reporting | Reusable only as derived read surfaces, with scale bounds recorded. | High | REVISED |

### Schedule constitutional determination

Schedule architecture is constitutionally reusable, but only as a **project-scoped deterministic stack**. The challenge does **not** support claiming that enterprise master-schedule hierarchy, constraint-aware schedule propagation, or decade-scale synchronous executive recompute are already finished.

## Executive operator review

| Role | Evidence-backed discoverability finding | Main strength | Main blind spot | Status |
|---|---|---|---|---|
| PM | Strongest operator evidence. `/pm/project-schedule` and `/pm/monday-review` are explicit, and PM intelligence/command surfaces already exist. | Schedule, Monday review, production visibility | Cost codes / lookahead / forecast are still embedded rather than named cleanly | REVISED |
| Foreman | Field Leadership + Daily Report + field forms prove strong field-entry discoverability. | Daily production, forms, field accountability | Budget / forecast / executive controls are not this role’s explicit constitutional lane | APPROVED |
| Superintendent | Role exists strongly in roster, routing, and field workflows, but discoverability remains spread across Field Leadership, PM, and Daily Report surfaces. | Field oversight, weekly readiness inputs | Resource / constraint / schedule consolidation is still distributed | REVISED |
| Dispatcher | Transportation / dispatch routes and haul-cycle throughput are strong. | Truck activity, dispatch supply, throughput | Cost/schedule/budget controls remain indirect consumers only | REVISED |
| Safety | Safety portal provides strong incidents / inspections / records discoverability. | Safety controls and compliance | Production/schedule/cost are adjacent rather than constitutional safety-owned lanes | APPROVED |
| HR | HR routes and payroll variance evidence provide a real labor-governance surface. | Labor records, payroll reconciliation | Cost-code / schedule / budget authority is not HR-owned | REVISED |
| Shop | Shop routes provide strong equipment/service discoverability. | Equipment care, fleet service operations | Project-controls planning authority remains indirect | REVISED |
| Executive | Executive overview, ODS, Project Health, and OPPC recap exist. | Portfolio visibility exists today | KPI overlap and scale-latency bounds prevent final lock | DEFERRED |
| Accounting | Only adjacency was proven: PO flows, approved amounts, and PM/admin financial surfaces. | PO workflow evidence exists | No canonical accounting / budget constitutional stack was proven | DEFERRED |
| Controller | Same conclusion as Accounting, but with stricter financial risk. | Some approval/amount signals exist | No budget hierarchy, no earned value, no ERP-facing authority lock | DEFERRED |
| Estimator | No explicit estimator-facing constitutional controls spine was proven. | Cost-code definitions may become future inputs | No estimating sync or estimator authority was evidenced | DEFERRED |

### Executive operator determination

The platform is **operator-rich but unevenly named**. PM, field, dispatch, safety, HR, and shop roles already have meaningful surfaces. Finance-facing roles do not yet have a ratified constitutional controls stack. Therefore, discoverability supports reuse — but not a blanket claim that every role already has a finished Project Controls operating system.

## Ten-year scalability review

### Ratified scale answer

The ratified answer is **bounded reuse, not unconditional scale approval**.

- Synthetic and preview evidence supports strong project-scoped operation.
- Forecast compute is acceptable per project, but full-portfolio recompute is materially expensive.
- Executive confidence / health / dashboard endpoints already show multi-second live preview latency at the audited scale.
- The evidence supports future national/multi-division use **only if** executive rollups are cached or background-materialized and the KPI hierarchy is consolidated first.

### Ten-year constitutional risks

1. portfolio-wide synchronous executive recompute
2. unresolved finance-side authority (budget / earned value / controller stack)
3. semantic KPI overlap across ODS / Project Health / OPPC / dictionary lanes
4. federated resource/equipment/crew planning without one explicit decomposition standard
5. unresolved external identifier split in equipment identity

## AI constitutional review

### What challenge proved

- AI configuration, provider routing, and ODS/brief surfaces already exist.
- AI can summarize current derived truths and produce briefings.
- AI does **not** solve missing authority. It inherits whatever truth conflicts already exist upstream.

### Current AI blockers to constitutional lock

1. Executive KPI hierarchy is still overlapping.
2. Budget hierarchy is absent.
3. Earned value is absent.
4. Production and constraint truth require decomposed constitutional ownership.
5. Enterprise-scale executive refresh is still latency-bounded.

### AI constitutional determination

AI is ratified as a **consumer/summarization layer**, not as a truth owner and not as proof that predictive Project Controls are already safe to expand.

## Executive cross-examination and five-year risks

### Likely CFO / Controller criticism
- “You do not yet have a canonical budget baseline, budget hierarchy, or earned-value engine.”
- Ratification response: **Correct. BUILD_NEW remains justified and unavoidable.**

### Likely COO / PMO criticism
- “The existing controls stack is strong, but crews, resources, equipment, constraints, and schedule interactions are still more federated than the original audit admitted.”
- Ratification response: **Correct. Those domains are ratified only with decomposition amendments.**

### Likely Chief Architect / CIO criticism
- “You cannot call dashboards or AI summaries the constitutional owner just because they aggregate facts.”
- Ratification response: **Correct. ODS, Project Health, OPPC recap, and AI remain derived lanes only.**

### Five-year debt if amendments are ignored
1. duplicate finance engines built on top of PO adjacency
2. executive KPI drift across overlapping rollups
3. silent equipment identity drift across Asset Spine and provider mappings
4. field-vs-standing constraint confusion in downstream controls
5. crew governance disputes between roster, field hours, and payroll reconciliation

## Constitutional answer

Project Controls should still be built on the existing platform. However, the final constitution is **more segmented and more precise** than WP-18B originally stated. The ratified architecture is:

- reuse-first
- evidence-backed
- explicit about multi-owner fact families where they already exist
- explicit about the two truly absent domains: **Budget Hierarchy** and **Earned Value**

No Project Controls implementation should begin until these ratified amendments are treated as governing architecture.