# ROLE_VISIBILITY_AUDIT.md
**Phase 17 · iter413 · 2026-05-24**

## Verdict
**PASS** — every role sees only what doctrine permits. No role-creep regressions introduced by iter392-iter412.

## Audit by role
| Role | Sees | Cannot see | Verified by |
|---|---|---|---|
| **Dispatch** | Operational command (iter411 hub), assignment issuance drawer, live operational board, governance findings, transfers + holds, fleet/utilization/idle (secondary), DLS health summary if also admin | Driver PII beyond name/CDL flag, PM project financials, Safety incident bodies, HR records | iter411 DispatchHub rewrite; iter408 lookups |
| **PM** | Production-awareness only: project-scoped `PmHaulActivityTile` (iter409) + `DispatchLifecycleTile` read-only filtered by `project_numbers` | Issue/cancel/reassign affordances. PM tile has ZERO write surface (testing-agent verified empirically iter409) | iter409 testing-agent verification |
| **Shop / Fleet** | iter396 `DispatchLifecycleTile` showing BREAKDOWN signals + truck/trailer master continuity | Assignment issuance, PM production data, Safety body content, HR records | iter396 visibility filter on scope="shop" |
| **Safety** | Restrained — Safety remains intentionally quiet on DLS. No DLS tiles surface in Safety pages | DLS internals — confirmed by inspection (no `DispatchLifecycleTile` imported in any `/safety/*` page) | Manual grep of `src/pages/safety/*` |
| **Field Leadership (FL)** | Operational continuity tile (existing iter319) + DLS read-only tile (iter396 with scope="fl") | Issuance, governance write actions | iter319 + iter396 |
| **HR** | Qualification continuity only (CDL / approved-driver / driver_status fields). Surfaced into iter408 driver dropdown via `driver_qualification` lib | DLS internals, dispatch assignment bodies, governance findings | `routes/hr_*` pages unchanged through Phase 12-17 |
| **Driver** (magic-link, no portal) | Their assigned truck + their lifecycle states + sign-out · `/shift` self-start entry | Other drivers, fleet master, financials | iter393 session scoping |

## Role-creep scan
- `grep -r "DispatchLifecycleTile" /app/frontend/src/pages/safety/`: **0 hits** ✅
- `grep -r "AssignmentCreateDrawer" /app/frontend/src/pages/pm/`: **0 hits** ✅
- `PmHaulActivityTile` has zero buttons / zero `onClick` write handlers — verified by iter409 testing agent ✅
- Driver session API requires per-shift `dispatch_driver_sessions.shift_id` — cross-driver access impossible by data model ✅

## Cross-role coexistence verified
- PmHub shows BOTH iter409 (PM Haul Activity) AND iter396 (DispatchLifecycleTile) — verified via testing agent in iter409 report
- DispatchHub.jsx imports `DispatchTransfersTab` + `DispatchHoldsTab` from `AdminDispatch.jsx` (shared component, role-gated at parent route)

## Non-blocking observations
- Older Safety/HR modules predate Phase 12 doctrine. They follow restraint already (no DLS leakage) but their internal visual styling will be picked up in a future "legacy alignment" iter (see `LEGACY_ALIGNMENT_AUDIT.md`).

## Verdict
**Role visibility doctrine intact.** No tile shows what its role should not own.
