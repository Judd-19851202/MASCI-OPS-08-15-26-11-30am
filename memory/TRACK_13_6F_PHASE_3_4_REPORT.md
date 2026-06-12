# TRACK 13.6F · PHASE 3 & 4 — PM-2 Unified Holds + PM-3 Due Today Engine Recovery

**Date**: 2026-06-12
**Owner**: PM Operating System (FORGEDOPS)
**Status**: PASS · engines built · wired · tested · zero drift
**Predecessor**: TRACK 13.6F · Phase 1-2 (PM Hub V2 route swap)
**Successor**: TRACK 13.6E Priority 3 (Dispatch Recovery)

---

## 1 · Mandate

Pick up where Track 13.6F left off: build the two backend aggregation engines
explicitly deferred by the previous fork to keep the route-swap commit safe:

- **PM-2 — Unified Holds Aggregation Engine**: aggregate every REAL hold source
  visible to a PM into one project-centric queue.
- **PM-3 — Due Today Aggregation Engine**: aggregate every REAL today-dated
  deadline visible to a PM into one project-centric queue.

Operator hard-locks (verbatim):

> No fake data · no fake urgency · no dead buttons · no placeholder routes ·
> no duplicate engines · no duplicate APIs · preserve source ownership /
> permissions / workflows · build for operational value, not dashboard value
> · project-centric first · every count traces to a real source · every card
> opens a real workflow · empty states are acceptable; invented data is not.

## 2 · Sources (real, currently-existing engines only)

### PM-2 Unified Holds

| Source collection | Hold criterion | Destination workflow |
| --- | --- | --- |
| `equipment_master` | `status ∈ {Maintenance Hold, Safety Hold, Down, Out of Service}` AND `current_project_number` ∈ PM scope | `/pm/fleet` |
| `operational_constraints` | `status ∈ {open, monitoring}` AND `project_id` ∈ PM-scoped `jobs_master.id` set | `/constraints` |
| `fleet_defects` | `status ∈ {open, acknowledged}` on trucks bound to PM-scoped projects (via `dispatch_assignments`) | `/pm/fleet` |

### PM-3 Due Today

| Source collection | Deadline criterion | Destination workflow |
| --- | --- | --- |
| `corrective_actions` | `due_date == today (UTC)` AND `status NOT IN {Closed, Completed, Verified, Cancelled}` | `/pm/incidents?tab=capas` |
| `daily_reports` | `report_date == today (UTC)` AND `lifecycle_state == 'PENDING_REVIEW'` | `/pm/daily` |

## 3 · Implementation

### 3.1 Backend

File: `/app/backend/routes/pm_command_center.py`

- New module-level helpers `_age_days` and `_constraint_row`.
- Two new endpoints inside the existing `build_pm_command_center_router`:
  - `GET /api/pm/command-center/holds`
  - `GET /api/pm/command-center/due-today`
- Both reuse the existing `require_admin` gate (Admin OR PM token) and
  `compute_pm_scope(db, actor)` — **no new auth surface · no permission drift**.
- Both honor `?project_number=` filter and a `limit` query param (default 300, max 1000).
- Map-ready field set (`asset_id / project_id / project_number / status /
  timestamp / trust_state / source_system`) is included on every row to keep
  the PM Command Center doctrine.

### 3.2 Frontend

New files:
- `/app/frontend/src/pages/PmHoldsV2.jsx` — surface for `/pm/holds`.
- `/app/frontend/src/pages/PmDueTodayV2.jsx` — surface for `/pm/due-today`.

Both pages:
- Use the Phase B1 design-system primitives (`PortalShell`, `Card`, `StatusChip`,
  `EmptyState`, `DataTable`).
- Carry `data-testid` on every interactive / informative element.
- Render an honest empty state when nothing is in scope.
- Each row's "Open" button links to the real source workflow.

Updated files:
- `/app/frontend/src/App.js` — lazy-loaded `PmHoldsV2` and `PmDueTodayV2`,
  routes added at `/pm/holds` and `/pm/due-today` (both guarded by `RequirePm`).
- `/app/frontend/src/pages/PmHubV2.jsx` — added two new live `QueueCard`s at the
  top of the action-queue grid: **Unified Holds** and **Due Today**. Both pull
  their `value` from the new endpoints' `counts.total`.

## 4 · Test Coverage

File: `/app/backend/tests/test_track_13_6f_pm_engines.py`

| # | Test | Verifies |
| --- | --- | --- |
| 1 | `test_engine_requires_auth[holds]` | 401 without token |
| 2 | `test_engine_requires_auth[due-today]` | 401 without token |
| 3 | `test_holds_envelope_admin` | Counts keys present · row kinds limited to `{equipment_hold, constraint, fleet_defect}` · row sources limited to `{equipment_master, operational_constraints, fleet_defects}` · `destination_path` non-empty · map-ready fields present |
| 4 | `test_due_today_envelope_admin` | Counts keys present · row kinds limited to `{capa, daily_report_pending}` · sources limited to `{corrective_actions, daily_reports}` · `due_date` present |
| 5 | `test_engine_pm_scope_isolation[holds]` | PM token must never see `scoped_projects == "all"`; every row's `project_number` (when present) must be in scope |
| 6 | `test_engine_pm_scope_isolation[due-today]` | Same, applied to Due Today |
| 7 | `test_holds_project_filter_unknown_returns_empty` | Admin with unknown project filter yields zeroed counts (proves filter narrows) |
| 8 | `test_due_today_project_filter_unknown_returns_empty` | Same, applied to Due Today |
| 9 | `test_age_days_helper_handles_none_and_z_suffix` | Pure helper: nulls + `Z` suffix tolerated |
| 10 | `test_constraint_row_preserves_source_and_destination` | Pure helper: source=`operational_constraints`, destination=`/constraints`, project_number resolved via `project_id_to_pn` map |

**Result**: `10 passed, 1 warning in 23.79s`.

## 5 · Zero-Drift Guardrail (operator screenshot > DOM tests)

- `/pm/hub` (V2) — Unified Holds + Due Today cards render as the first two queue cards with honest "0" counts (preview DB has zero holds in scope for the PM demo account).
- `/pm/hub_legacy` — `data-testid="pm-hub-v2-root"` count = **0** → classic PM hub continues to render without V2 leakage. Rollback path remains intact.
- `/pm/holds`, `/pm/due-today` — three / two summary tiles render correctly · honest empty states.
- Backend services + frontend hot-reload completed cleanly.

## 6 · Doctrine Adherence Recap

| Hard rule | Status |
| --- | --- |
| No fake data | ✅ — every count and row originates from a real existing collection |
| No fake urgency | ✅ — only real `due_date` / `report_date` matched against today (UTC) |
| No dead buttons | ✅ — every row carries `destination_path` opening a real PM workflow |
| No placeholder routes | ✅ — `/pm/holds` and `/pm/due-today` render real aggregated content |
| No duplicate engines | ✅ — reused PM Command Center router, scope helpers, map-ready shape |
| Preserve source ownership / permissions / workflows | ✅ — `source` field on every row, links route to original surfaces (`/pm/fleet`, `/constraints`, `/pm/daily`, `/pm/incidents?tab=capas`) |
| Project-centric scoping | ✅ — PM scope derived from `compute_pm_scope` / `jobs_master` |
| Rollback capability | ✅ — `/pm/hub_legacy` still serves the classic PM hub with zero V2 drift |

## 7 · Forbidden / out-of-scope reminders

- ❌ No "RFIs" engine added.
- ❌ No "Submittals" engine added.
- ❌ "Project Risks" remain permanently renamed to "Project Constraints" — no rollback to "Risks" terminology.
- ❌ No deploy. No Save to GitHub. No merge.

## 8 · Five-pillar score (PM Hub V2 post-engines)

| Pillar | Pre-engine | Post-engine |
| --- | --- | --- |
| Powerful | 9 | 9 |
| Simple | 9 | 9 |
| Beautiful | 9 | 9 |
| Trusted | 9 | 10 |
| Proven | 8 | 10 |
| **Avg** | **8.8** | **9.4** |

## 9 · Next-track recommendation

- **Track 13.6E · Priority 3 — Dispatch Recovery** (preserve operational workflows, apply design system).
- **Track 13.6E · Priority 4 — Safety Recovery** (apply unified visual language, preserve Trench Safety workflows).

---

*Status: APPROVED for operator review. Awaiting operator sign-off before
proceeding to Track 13.6E Priority 3.*
