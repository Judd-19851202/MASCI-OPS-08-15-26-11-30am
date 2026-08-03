# WP18BR2 Cost Code Constitution

Date: 2026-08-03

## Constitutional answer

**Global cost-code definitions should be `Reuse`. Project-specific cost-code planning should be `Extend`.**

## Primary facts

1. The global registry is explicit and reusable.
   - `REGISTRY_COLLECTION = "cost_code_registry"`
   - Registry APIs already exist for list, upsert, and guarded bulk replace.
   - Evidence: `backend/routes/cost_codes.py:48,324-352`.

2. Project-specific planning already has a constitutional owner.
   - Assignments are loaded from and persisted back to `jobs_master.assigned_cost_codes`.
   - Planning readiness and lifecycle are persisted on the same project root.
   - Evidence: `backend/routes/cost_codes.py:363-466,760-920`; `backend/services/cost_codes/foundation.py:640-690,1018-1046`.

3. Cost-code truth already feeds schedule, progress, forecast, and ODS projections.
   - Evidence: `backend/services/cost_codes/foundation.py:658-675,949-1037`; `backend/services/cost_codes/schedule_engine.py:211-540`.

4. Financial-adjacent fields exist, but they do not prove a canonical budget hierarchy.
   - `FINANCIAL_FIELDS = {"bid_unit_price", "target_man_hours", "contract_value", "margin", "margin_percent"}`
   - Evidence: `backend/services/cost_codes/foundation.py:15`.

## Constitutional owner model

| Layer | Constitutional owner | Why |
|---|---|---|
| Reusable enterprise code definitions | `cost_code_registry` | It is the only explicit reusable registry evidenced in source. |
| Project-specific plan / assignment | `jobs_master.assigned_cost_codes` | It is the actual persisted planning owner consumed by schedule and progress logic. |
| Actual production by cost code | `daily_reports.cost_code_quantities` | It is the field actuals input consumed by progress/schedule recompute. |
| Executive/reporting consumers | Derived only | ODS, Project Health, and intelligence consumers do not own cost-code truth. |

## Enterprise-scale challenge

### What already scales well

- The split between global definitions and project-specific assignments is architecturally sound.
- Reusing the same planning owner for schedule, forecast, and progress is the correct anti-duplication pattern.

### What does not yet survive final enterprise challenge unchanged

1. **Revision governance is still too implicit.**  
   Publish and lifecycle actions exist, but a long-horizon assignment revision contract is not yet explicit enough for multi-company program governance.

2. **Enterprise hierarchy above project scope is not proven.**  
   The cost-code path is strongly project-centric; enterprise company/division/business-unit semantics are not constitutionally expressed here.

3. **Finance adjacency must stay bounded.**  
   Financial fields on assignments do not convert the cost-code owner into a budget hierarchy or controller-grade financial authority.

## What would create future rewrite risk?

1. Building a second project planning collection.
2. Letting budget work bypass `jobs_master.assigned_cost_codes`.
3. Treating ODS/read-model projections as editable truth.
4. Expanding enterprise rollups before revision/lock semantics are explicit.

## Alternatives considered

| Alternative | Result | Why rejected |
|---|---|---|
| Rebuild cost-code planning as a new project-controls engine | Rejected | Existing owner is already real and connected to schedule/forecast/progress. |
| Collapse registry and project planning into one table/owner | Rejected | Definition truth and execution-planning truth are intentionally different layers. |
| Upgrade PO/Project Health/ODS into cost-code planning authority | Rejected | Those are downstream consumers or adjacent workflows, not planning owners. |

## Final determination

- **Global Cost Code Registry:** `Reuse`
- **Project Cost-Code Planning:** `Extend`

This recommendation avoids future rewrite **only if** future work preserves the existing split between reusable definitions, project planning, and field actuals.