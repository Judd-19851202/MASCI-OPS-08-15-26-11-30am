# WP18B Master Executive Architecture Audit

Date: 2026-08-03  
Work Package: WP-18B — Executive Architecture Authority Audit  
Platform: MASCI Operations Platform / ForgedOps  
Scope rule: Documentation, evidence, and constitutional architecture only. No application code, UI, API, workflow, database, model, configuration, or data changes were made.

## Executive objective achieved

This package establishes the constitutional architecture required to answer future delivery questions with evidence instead of assumption.

## Direct answers to the executive questions

### What capabilities already exist?
- The platform already evidences reusable capabilities for:
  - project identity and roster authority
  - global cost-code definitions and project-specific cost-code assignments
  - deterministic schedule computation
  - rolling planning lifecycle / lookahead state
  - Daily Report production actuals
  - Monday review workspace and Monday briefing artifacts
  - operational constraints persistence
  - federated resource coordination
  - equipment identity and deployment context
  - ODS / Project Health / OPPC executive intelligence lanes
- **Evidence source:** `WP18A_PLATFORM_CAPABILITY_REGISTER.csv`, `WP18B_CAPABILITY_AND_ENGINE_MAP.csv`
- **Confidence level:** High
- **Architectural impact:** The platform is foundation-rich; future work should assume reuse first
- **Recommended disposition:** **REUSE / EXTEND**

### Which engines already exist?
- `cost_code_registry`
- `jobs_master.assigned_cost_codes`
- `backend/services/cost_codes/schedule_engine.py`
- `daily_reports`
- `jobs_master.oppc_planning_lifecycle`
- `jobs_master.oppc_forecast_history`
- `jobs_master.oppc_forecast_overrides`
- `jobs_master.oppc_monday_reviews`
- `oppc_monday_briefings`
- `project_team_assignments`
- `dispatch_assignments`
- `equipment_master`
- ODS intelligence, Project Health, KPI dictionary, and OPPC executive recap lanes
- **Evidence source:** `WP18B_AUTHORITY_MATRIX.csv`, `WP18B_CAPABILITY_AND_ENGINE_MAP.csv`
- **Confidence level:** High
- **Architectural impact:** Net-new work should be measured against these existing engines before authorization
- **Recommended disposition:** **REUSE**

### Which engines should never be rebuilt?
- Cost-code registry and project-specific assignment spine
- Schedule engine and forecast history path
- Daily Report actuals spine
- Monday review and briefing chain
- Team roster, dispatch assignment, and equipment registry owners
- ODS, Project Health, KPI dictionary, and OPPC executive recap as existing signal lanes
- **Evidence source:** `WP18B_PROJECT_CONTROLS_READINESS_AUDIT.md`, `WP18B_COST_CODE_AUTHORITY_AUDIT.md`, `WP18B_SCHEDULE_AUTHORITY_AUDIT.md`
- **Confidence level:** High
- **Architectural impact:** Rebuilding any of these would create avoidable duplication and trust drift
- **Recommended disposition:** **REUSE / CONSOLIDATE**

### Which systems are duplicated?
- Daily Report legacy shell versus canonical submit path
- Cost-code registry versus project-assignment truth (role split that must not be collapsed)
- ODS versus OPPC versus Project Health versus legacy operational-intelligence in the executive-signal layer
- Monday review workspace versus Monday briefing artifact (complementary, not duplicate)
- Manual import/export fallback versus future live connectors
- **Evidence source:** `WP18B_DUPLICATION_REGISTER.csv`
- **Confidence level:** High
- **Architectural impact:** Some overlaps are legitimate layer splits; some require consolidation of semantics, not removal of capability
- **Recommended disposition:** **CONNECT / CONSOLIDATE**

### Which systems are underutilized?
- `jobs_master.oppc_planning_lifecycle` (real lookahead capability, weakly named)
- `operational_constraints` (real authority, weak downstream binding)
- KPI dictionary governance (`/api/admin/wp17a/kpi-dictionary`) as a constitutional executive hierarchy anchor
- PM command resource/equipment aggregation as an operator-facing planning surface
- Manual CSV integration fallback as a resilient bridge
- **Evidence source:** `WP18A_LOOKAHEAD_AND_WEEKLY_RECONCILIATION_AUDIT.md`, `WP18B_TRUST_LINE_REGISTER.csv`, `WP18B_OPERATOR_EXPERIENCE_AUDIT.md`
- **Confidence level:** Medium-high
- **Architectural impact:** Reuse value is higher than current naming/discoverability suggests
- **Recommended disposition:** **EXTEND**

### Which systems are disconnected?
- Constraint truth is not yet constitutionally bound into schedule, lookahead, and executive KPI hierarchy
- Executive KPI semantics are split across ODS, Project Health, OPPC recap, KPI dictionary, and legacy intelligence lanes
- Resource and equipment planning are federated but not explicitly framed as one constitutional control stack
- Budget hierarchy and earned value are absent as evidenced architectural owners
- **Evidence source:** `WP18B_TRUST_LINE_REGISTER.csv`, `WP18B_RISK_AND_DEPENDENCY_REGISTER.csv`
- **Confidence level:** High
- **Architectural impact:** These are the highest-value connection points before any new build work
- **Recommended disposition:** **EXTEND / CONNECT / CONSOLIDATE / BUILD_NEW**

### Which trust lines are complete?
- Project identity → PM job scope
- Project identity → roster/staffing
- Cost-code registry → project assignment
- Project assignment → schedule
- Daily production → progress/schedule
- Daily production → Monday review
- Schedule → Monday review
- Monday review → Monday briefing
- **Evidence source:** `WP18B_TRUST_LINE_REGISTER.csv:TL01-TL08`
- **Confidence level:** High
- **Architectural impact:** These are the strongest foundations for WP-18C sequencing
- **Recommended disposition:** **REUSE / EXTEND**

### Which trust lines are weak or missing?
- Daily Reports → ODS facts/KPI snapshots (real but derived)
- Constraints → schedule hierarchy
- Constraints → executive KPI flow
- Planning lifecycle → operator/executive lookahead semantics
- Resource demand → resource coordination
- Equipment identity → equipment planning
- Executive KPI dictionary → all executive signal lanes
- Budget hierarchy → operator/executive consumers (missing)
- Earned value → operator/executive consumers (missing)
- **Evidence source:** `WP18B_TRUST_LINE_REGISTER.csv:TL09-TL18`
- **Confidence level:** High
- **Architectural impact:** These define the repair/connect backlog that should precede any broad feature expansion
- **Recommended disposition:** **EXTEND / CONNECT / CONSOLIDATE / BUILD_NEW**

### What is the Single Source of Truth for each operational domain?
- Project identity → `jobs_master`
- Team roster → `project_team_assignments`
- Cost-code definitions → `cost_code_registry`
- Project-specific cost-code plan → `jobs_master.assigned_cost_codes`
- Production actuals → `daily_reports`
- Schedule snapshot → `schedule_engine.py` derived output
- Forecast history → `jobs_master.oppc_forecast_history` + `jobs_master.oppc_forecast_overrides`
- Lookahead lifecycle → `jobs_master.oppc_planning_lifecycle`
- Monday review state → `jobs_master.oppc_monday_reviews`
- Monday briefing artifact → `oppc_monday_briefings`
- Constraints → `operational_constraints`
- Resource supply → `dispatch_assignments` (with labor supply on `project_team_assignments` and demand on `jobs_master.assigned_cost_codes`)
- Equipment identity → `equipment_master`
- Budget hierarchy → no evidenced owner yet
- Earned value → no evidenced owner yet
- **Evidence source:** `WP18B_SOURCE_OF_TRUTH_MATRIX.csv`
- **Confidence level:** High
- **Architectural impact:** The truth map is now explicit and can serve as the future constitutional baseline
- **Recommended disposition:** see matrix

### What implementation sequence minimizes technical debt while maximizing reuse?
- Freeze authority contracts already evidenced
- Lock cost-code planning ownership
- Formalize schedule / lookahead / forecast hierarchy already in place
- Repair weak trust lines (especially constraints and downstream normalization)
- Connect federated resource and equipment planning lanes
- Connect Monday review / briefing hierarchy end-to-end
- Consolidate executive KPI semantics across existing lanes
- Only then authorize Budget Hierarchy
- Only after Budget Hierarchy authorize Earned Value
- **Evidence source:** `WP18B_RECOMMENDED_IMPLEMENTATION_SEQUENCE.md`
- **Confidence level:** High
- **Architectural impact:** This is the lowest-risk route to WP-18C and beyond
- **Recommended disposition:** sequence accepted as constitutional order

## Constitutional Project Controls answer

Across the 12 required Project Controls domains:

- **10 / 12 already have reusable or extendable architecture**
- **2 / 12 require BUILD_NEW only because no reusable owner was evidenced**

| Domain | Disposition | Basis |
|---|---|---|
| Project-specific Cost Codes | EXTEND | Existing registry + assignment + actuals spine already exists |
| Schedule hierarchy | EXTEND | Deterministic schedule engine already exists |
| Budget hierarchy | BUILD_NEW | No canonical budget owner/engine evidenced |
| Rolling Two-Week Lookahead | EXTEND | Existing planning lifecycle is real but embedded |
| Monday Morning Review | EXTEND | Existing review and briefing chain is already implemented |
| Production Tracking | REUSE | Daily Reports already own field actuals |
| Resource Planning | EXTEND | Federated existing owners already exist |
| Equipment Planning | EXTEND | Equipment identity + dispatch context already exist |
| Constraint Management | EXTEND | Canonical constraint owner exists, downstream binding is weak |
| Forecasting | EXTEND | Existing forecast history and override classes already exist |
| Earned Value | BUILD_NEW | No engine/formula/store evidenced |
| Executive KPI flow | CONSOLIDATE | Existing lanes overlap and need one hierarchy |

## Package cross-reference map

- Authority ownership: `WP18B_AUTHORITY_MATRIX.csv`
- Single Source of Truth: `WP18B_SOURCE_OF_TRUTH_MATRIX.csv`
- Flow lineage: `WP18B_DATA_FLOW_REGISTER.csv`
- Trust strength: `WP18B_TRUST_LINE_REGISTER.csv`
- Overlap and duplication: `WP18B_DUPLICATION_REGISTER.csv`
- Domain/engine mapping: `WP18B_CAPABILITY_AND_ENGINE_MAP.csv`
- Project Controls constitutional audit: `WP18B_PROJECT_CONTROLS_READINESS_AUDIT.md`
- Cost-code authority deep dive: `WP18B_COST_CODE_AUTHORITY_AUDIT.md`
- Schedule authority deep dive: `WP18B_SCHEDULE_AUTHORITY_AUDIT.md`
- Operator wayfinding audit: `WP18B_OPERATOR_EXPERIENCE_AUDIT.md`
- Risks and dependencies: `WP18B_RISK_AND_DEPENDENCY_REGISTER.csv`
- Low-risk sequence: `WP18B_RECOMMENDED_IMPLEMENTATION_SEQUENCE.md`
- Executive closeout: `WP18B_FINAL_EXECUTIVE_REPORT.md`

## Integrity note

This WP-18B package remains a constitutional architecture and evidence package only. No implementation work was performed or authorized.