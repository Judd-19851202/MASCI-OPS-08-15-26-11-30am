# WP18C9 Canonical Scope and Authority

Date: 2026-08-07  
Status: PASS  
Final Gate Intent: `WP-18C9 — GO — READY TO SAVE & DEPLOY`

## Canonical Scope
- Deliver one governed cross-project portfolio surface by upgrading `/admin/executive-overview` and adding scoped PM access at `/pm/portfolio-intelligence`.
- Reconcile, not duplicate, the adjacent executive surfaces by keeping `/admin/executive-operational-intelligence` and `/admin/command-center` as linked supporting views.
- Provide explainable portfolio attention, cost performance, schedule risk, commitments, constraints, production outlook, resource pressure, and drill-back.
- Persist a bounded portfolio cache in `portfolio_intelligence_snapshots` as a delivery/read surface only; it is not a new truth authority.

## Explicit Non-Scope
- No new forecast engine.
- No new earned-value engine.
- No new autonomous actioning or C10 behavior.
- No override of existing project truth from C1–C8.

## Upstream Truth Reused by C9
| Domain | Canonical upstream | C9 use |
|---|---|---|
| Project scope | `jobs_master` + enterprise governance scope helpers | Determine visible projects per actor |
| Project performance | `project_operational_intelligence_snapshots` | Production outlook, freshness, supporting context |
| Forecast and commitments | `project_forecasting_snapshots` and live refresh via existing forecasting service | Likely finish, commitments, constraints, resource pressure, forecast cost |
| Earned Value | `project_earned_value_snapshots` and live refresh via existing EV service | BAC/PV/EV/AC/ETC/EAC rollups and project EV readiness |
| Project health | Existing `/api/project-health` surface | Supporting operator context on the frontend |

## Authority Rules Enforced
1. Portfolio CPI and SPI are derived from aggregate EV/AC and EV/PV totals only.
2. Project CPI/SPI values are never averaged.
3. Production quantities are rolled up only inside the same unit bucket.
4. Missing or older evidence is surfaced as insufficient evidence, not green.
5. PM users only receive their governed project scope.
6. C9 refreshes missing/older upstream project updates through existing C6/C7/C8 services; it does not create new math.

## Implemented Surfaces
- Admin API: `/api/admin/governance/project-controls/portfolio-intelligence`
- Admin refresh: `/api/admin/governance/project-controls/portfolio-intelligence/refresh`
- Admin export: `/api/admin/governance/project-controls/portfolio-intelligence/export`
- PM API: `/api/pm/project-controls/portfolio-intelligence`
- PM refresh: `/api/pm/project-controls/portfolio-intelligence/refresh`
- PM export: `/api/pm/project-controls/portfolio-intelligence/export`
- Admin UI: `/admin/executive-overview`
- PM UI: `/pm/portfolio-intelligence`

## Final Scope Verdict
C9 was delivered as an additive portfolio layer over existing governed project truth. No duplicate KPI, forecast, or EV truth engine was introduced.
