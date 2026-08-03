# WP18BR2 Budget Hierarchy Constitution

Date: 2026-08-03

## Constitutional answer

**Budget Hierarchy must be `Build New`.**

## What was challenged

The review intentionally tried to disprove `Build New` by looking for any hidden budget owner inside:

- PO request workflow
- Project Health
- PM financial navigation / financial-adjacent surfaces
- operational KPI lanes
- cost-code financial fields

## Primary facts

1. PO workflow exists, including submitted, approved, and receipt phases with approved amounts.
   - Evidence: `backend/routes/po_requests.py:580-760`.

2. Project Health consumes PO friction indicators such as pending approval, missing receipt, and overdue receipt.
   - Evidence: `backend/routes/project_health.py:167-186`.

3. Operational KPI routes explicitly forbid cost/budget truth.
   - Evidence: `backend/routes/operational_kpis.py:16-18,34-57`.

4. Cost-code planning includes financial-adjacent fields.
   - Evidence: `backend/services/cost_codes/foundation.py:15`.

## Why those facts do **not** add up to a budget constitution

None of the evidenced paths proved:

- a canonical budget baseline owner,
- original vs revised budget governance,
- cost-code budget allocation hierarchy,
- commitment vs actual vs forecast-at-completion layering,
- controller/CFO approval chain,
- change-order integration as budget authority,
- enterprise budget rollup semantics,
- or one budget API/store/ledger that other consumers must obey.

In other words: **adjacent money-like data exists, but budget authority does not.**

## Enterprise-scale challenge

At MASCI-today scale, adjacency may feel usable.  
At $500M+ contractor scale, it becomes dangerous.

Without a real budget hierarchy, the platform cannot credibly support:

- multi-company financial consolidation,
- acquisition onboarding,
- division-level budget governance,
- variance management by authoritative baseline,
- or controller-grade trust lines into executive reporting.

## Alternatives considered

| Alternative | Result | Why rejected |
|---|---|---|
| Treat PO approvals as the budget hierarchy | Rejected | PO flow is a procurement/request control, not a budget baseline owner. |
| Treat Project Health as budget authority | Rejected | It is an aggregate consumer and explicitly non-duplicative. |
| Treat cost-code financial fields as the budget hierarchy | Rejected | Fields alone do not create budget ownership, approvals, or rollup governance. |
| Pretend budget is already solved by “financial signals” | Rejected | That would create deceptive executive truth and future reconciliation debt. |

## Final determination

- **Budget Hierarchy:** `Build New`

This is one of the rare cases where `Build New` is constitutionally justified because no reusable budget owner was evidenced in the audited repository.