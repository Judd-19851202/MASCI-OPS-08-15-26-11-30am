# WP18BR3 Financial Constitutional Review

Date: 2026-08-03

## Executive question

Does the current architecture support enterprise financial management **without redesign**?

## Executive answer

**Not fully. But it also does not justify rebuilding the current operational and project-controls foundation.**

The correct BR3 answer is:

- preserve the existing operational/controls sources already generating financial-adjacent signal
- add a real Budget Hierarchy layer
- add Earned Value only after budget exists
- do not mistake current derived financial views for the future canonical finance model

## What evidence supports preservation

### 1. Cost codes already carry financial-adjacent planning fields

`FINANCIAL_FIELDS = {"bid_unit_price", "target_man_hours", "contract_value", "margin", "margin_percent"}`  
`backend/services/cost_codes/foundation.py:15`

This is not a budget model by itself, but it is real reusable planning signal.

### 2. PO workflow already captures procurement-side money movement signal

- estimated amount on submission
- approved amount on approval
- issue/receipt lifecycle
- project linkage

Evidence: `backend/routes/po_requests.py:586-772`

This is not a budget baseline, but it is clearly worth preserving.

### 3. P&L snapshot already turns daily reports into cost signal

The existing `project_pnl` endpoint and `ProjectPnlPage` prove the platform can already derive:

- crew hours
- labor cost at operator-supplied rate
- subcontractor hours
- material delivery lines

Evidence: `backend/server.py:6619-6754`; `frontend/src/pages/ProjectPnlPage.jsx:60-339`

### 4. OPPC execution already computes budget-rate and efficiency style metrics

Evidence includes:

- `budget_production_rate`
- `budget_hours_per_installed_quantity`
- `labor_efficiency_percent`
- `production_efficiency_percent`
- `forecast_labor_remaining`

Evidence: `backend/services/cost_codes/oppc_execution.py:309-329,486-587`

This is not Earned Value, but it proves the architecture is capable of derived performance math.

## What evidence contradicts a “finance is already solved” claim

### 1. P&L snapshot is deliberately bounded

The backend P&L endpoint:

- derives labor cost from a supplied labor-rate parameter
- does not create a budget baseline
- does not store actual cost authority
- does not roll revenue, billing, cash flow, or margin as a canonical ledger

Evidence: `backend/server.py:6627-6754`

### 2. KPI architecture explicitly excludes money truth

Operational KPI routes say, in source, that they are **no money / no budget** surfaces.

Evidence: `backend/routes/operational_kpis.py:16-18,149-152`

### 3. Project Health is a derived attention model, not financial authority

Evidence: `backend/routes/project_health.py:4-7,167-186`

### 4. No canonical budget baseline or EV store was evidenced

BR3 challenge re-checked the architecture and still found no controller-grade owner for:

- budget baseline
- revised budget governance
- committed cost rollup
- actual cost rollup
- billing / revenue / cash flow hierarchy
- earned value formulas and rollup

## Financial constitutional decision by domain

| Domain | BR3 answer | Why |
|---|---|---|
| Estimate structure | Preserve upstream signals | Cost-code financial fields already exist and should remain foundational. |
| Budget structure | Build new constitutional owner | No true budget baseline authority exists today. |
| Forecasting | Extend | Forecast math already exists on schedule/OPPC lanes. |
| Committed cost | Extend from PO + future budget layer | PO flow is real but not sufficient alone. |
| Actual cost | Extend from current production/labor/procurement facts into a future cost model | Raw facts exist but no canonical actual-cost authority does. |
| Cost codes | Preserve and extend | Cost-code architecture is already one of the strongest reusable finance-adjacent spines. |
| Production | Preserve with minor refinement | Daily Reports should remain the field actuals origin. |
| Productivity | Extend | OPPC already produces useful derived productivity measures. |
| Earned Value | Build new derived layer | Upstream inputs exist, but EV itself does not. |
| Executive forecasting | Extend | Useful today, but not yet controller-grade enterprise forecasting. |
| Portfolio rollups | Redesign executive hierarchy, not the upstream truth | Reporting overlap is the real issue. |

## BR3 financial conclusion

The architecture **does not yet support enterprise financial management without amendment**.

But the architecture **does support building enterprise financial management without redesigning the current operational foundation**.

That is the critical BR3 difference from a more pessimistic reading.