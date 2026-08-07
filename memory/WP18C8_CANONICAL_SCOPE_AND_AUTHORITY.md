# WP-18C8 Canonical Scope and Authority

Date: 2026-08-07
Final gate target: `WP-18C8 — GO — READY TO SAVE & DEPLOY`
Current factual result: `GO — READY TO SAVE & DEPLOY`

## Delivered canonical scope

WP-18C8 was implemented as one governed Earned Value Engine, not as a parallel dashboard.

Delivered runtime capabilities:
- Canonical backend authority: `backend/services/project_earned_value_engine.py`
- PM routes: `/api/pm/project-controls/projects/{project_number}/earned-value*`
- Executive/Admin routes: `/api/admin/governance/project-controls/projects/{project_number}/earned-value*`
- Version capture + CSV export
- Additive C8 snapshot/version persistence
- PM budget trust-line review activation for commitment and actual-cost candidate linkage
- PM route: `/pm/project-controls/earned-value`
- Executive/Admin route: `/admin/governance/project-controls/earned-value`
- Navigation discoverability in PM sidebar, Admin sidebar, and Executive Overview launch card

## Authorities reused

The C8 engine reuses, and does not replace, these existing authorities:

| Need | Authority reused | Evidence |
|---|---|---|
| BAC / budget line truth | `project_budget_authority` | `backend/services/project_budget_authority.py` |
| PV / baseline timing | `project_schedule_authority` | `backend/services/project_schedule_authority.py` |
| Quantity / approved progress | `project_schedule_actuals_spine` + `project_controls_work_ledger` | `backend/services/project_schedule_actuals_spine.py`, `backend/services/project_controls_authority.py` |
| AC trust line | `project_budget_authority` receipt/accounting candidate linkage | `project_budget_actual_cost_candidates`, `project_budget_lines` |
| ETC source | `project_forecasting_commitments` (C7) | `backend/services/project_forecasting_commitments.py` |
| Operator metric governance | `wp17a_kpi_governance` | `backend/lib/wp17a_kpi_governance.py` |
| PM / Executive route shells | Existing PM/Admin shells | `frontend/src/pages/*`, `frontend/src/components/*` |

## Explicit non-scope / blocked scope

The following were intentionally not built inside C8:
- No second forecasting engine
- No second KPI engine
- No new schedule authority
- No executive-only mathematical branch
- No portfolio or multi-project intelligence (`C9` remains blocked)
- No PDF/email/notification channel for C8 because no governed operator requirement or inherited runtime contract existed
- No VAC publication because VAC is not in the governed C8 roadmap contract recovered for this package

## Canonical metric contract published

Published in runtime:
- BAC
- PV
- EV
- AC
- CV
- SV
- CPI
- SPI
- ETC
- EAC
- TCPI

Not published as a governed C8 metric:
- VAC

## Truth behavior

- Missing or contradictory evidence never auto-promotes to green.
- PV blocks when baseline timing is absent.
- EV is quantity-first; schedule-based EV is an explicit fallback only when approved quantity is unavailable at the same grain.
- AC is recognized only from governed linkage; receipts do not silently become accounting truth.
- ETC is inherited from C7 remaining-work forecast, not re-forecasted in C8.
- EAC is computed from recognized AC plus governed ETC, while preserving commitment-floor safety.

## Seeded certification project used for runtime proof

Project: `ZZ-RUNTIME-CERT-2026`

Certified summary at closeout:
- BAC = `1200`
- PV = `0`
- EV = `1200`
- AC = `900`
- CV = `300`
- SV = `1200`
- CPI = `1.3333`
- SPI = `null` (PV denominator = `0`)
- ETC = `null` (no remaining governed remaining-work cost at the current line grain)
- EAC = `900`
- TCPI = `null` (no valid remaining denominator after full earned completion at the current line grain)

## Final constitutional decision

WP-18C8 is complete because the platform now has a single governed EV authority that consumes inherited truth lines, exposes operator evidence, resolves the legitimate C8-blocked linkage lane, and passes PM + Executive runtime proof without reopening C7 or leaking into C9.