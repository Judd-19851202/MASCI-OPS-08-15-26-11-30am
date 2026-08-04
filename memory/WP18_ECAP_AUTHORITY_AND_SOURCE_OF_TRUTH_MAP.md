# WP18 ECAP Authority and Source of Truth Map

Date: 2026-08-03

## Core authority rules

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

1. Derived readers never become source-of-truth owners.
2. Entry systems, approval systems, and executive reporting systems may differ, but their boundaries must be explicit.
3. No financial concept may have duplicate authority.
4. Every operational fact has one authoritative owner.
5. Capture once, reuse everywhere, is the standing default.

## Source-of-truth map

| Domain | Truth owner | Proof label | Entry system | Reconciliation system | Executive reporting system |
|---|---|---|---|---|---|
| Project identity | `jobs_master` | `SOURCE_VERIFIED` | jobs/admin/project setup | governance + project admin | ODS / executive readers |
| Organization / authority | enterprise governance registry and ledgers | `SOURCE_VERIFIED` | auth directory / admin governance | governance ledgers | executive/admin governance views |
| Project roster | `project_team_assignments` | `SOURCE_VERIFIED` | PM / HR / admin | governance + HR | PM / executive consumers |
| Cost-code library | `cost_code_registry` | `SOURCE_VERIFIED` | admin/project controls | project controls + finance | PM / executive consumers |
| Project cost-code planning | `jobs_master.assigned_cost_codes` | `SOURCE_VERIFIED` | PM / project controls | planning review + audit | schedule / ODS / PM readers |
| Daily field actuals | `daily_reports` | `SOURCE_VERIFIED` | field / foreman / PM | PM + payroll + controls review | PM / executive consumers |
| Payroll reconciliation | `payroll_variance` | `SOURCE_VERIFIED` | HR/payroll review | HR/payroll | HR / executive consumers |
| Equipment registry | Asset Spine / `equipment_master` authoritative core | `SOURCE_VERIFIED` | shop / asset admin / imports | asset admin + dispatch/shop | fleet / executive readers |
| Procurement requests and approvals | `po_requests` | `SOURCE_VERIFIED` | field/PM/shop/safety submitters | approvers + future budget line binding | Project Health / finance readers |
| Constraints | `daily_reports.constraints` + `operational_constraints` dual-lane model | `SOURCE_VERIFIED` | field + PM/safety | PM / superintendent / controls | schedule / KPI / executive readers |
| Budget Hierarchy | new budget subsystem | `APPROVED_CONSTITUTIONAL_DECISION` | controlled budget operators | finance/project controls | executive finance rollups |
| Earned Value | new EV subsystem | `APPROVED_CONSTITUTIONAL_DECISION` | derived only; no direct operator entry | project controls / finance | executive and PM EV readers |

## Explicit non-owners

| Surface | Why it is not a truth owner | Proof label |
|---|---|---|
| Project Health | derived friction/attention reader only | `SOURCE_VERIFIED` |
| ODS intelligence | additive read model only | `SOURCE_VERIFIED` |
| operational KPI routes | explicitly non-budget / non-cost reporting | `SOURCE_VERIFIED` |
| AI outputs | assistive only; no silent authority | `SOURCE_VERIFIED` + `DOCUMENTED_ONLY` |
| Project P&L snapshot | derived live field-cost view, not budget authority | `SOURCE_VERIFIED` |

## Final source-of-truth determination

WP-18C must implement only on top of this authority map.  
Any contradiction during implementation is an executive stop condition.

Any later package that duplicates an existing truth owner fails the Operational Intelligence Constitution.