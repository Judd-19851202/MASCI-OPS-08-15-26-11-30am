# TRACK 18.00 · Phase F · Portal-Aware Data Layer + Dispatch Surface Polish

**Status:** ✅ GO
**Date:** 2026-02-10
**Type:** Correction + completion · zero-drift · no migrations · no new collections

---

## Defects corrected

1. **Mission Control summary tiles required admin access.** The `/api/admin/transportation/dashboard` endpoint (the data feed behind Mission Control's tiles) was gated by `require_admin_strict`. A dispatcher landing on `/transportation-operations` after the 18.00E-FIX rehome saw a 403 on the primary data source. Phase F makes this single endpoint portal-aware while keeping every record-detail endpoint (`/documents/queue`, `/inspections/queue`, `/carriers/{id}`, `/drivers/{id}`, `/trucks/{id}`) admin-strict.
2. **TopBar brand was missing on dispatch work surfaces other than the hub.** A dispatcher inside `/board`, `/command`, `/map`, `/haul-ledger`, or `/driver-qualification` still saw the legacy dispatch chrome with no Transportation Operations top strip. Phase F mounts the TopBar on every major dispatch surface.
3. **No formal Transportation-scoped restricted-state component.** Restricted screens still inherited Admin Console wording when accessed by a dispatcher. Phase F introduces `TxOpsRestricted` and `TxOpsRestrictedData` with the required wording per the prompt.
4. **TopBar Administration group was visible to every role.** Dispatch users saw clickable dead ends for Audit / Reports. Phase F makes the Administration group `adminOnly: true` and filters by `isAdmin()`.
5. **No mobile/iPad usable navigation.** Below the `md` breakpoint the grouped nav collapsed silently. Phase F adds an explicit hamburger toggle with a collapsible drawer.

---

## Surfaces touched
| File | Change |
|---|---|
| `backend/routes/transportation_experience.py` | `register_transportation_experience_routes` now accepts an optional `require_portal_dep`. Only the `dashboard` endpoint uses it; all other endpoints in the router keep `require_admin_dep`. |
| `backend/server.py` (line ~12846) | Passes `_require_any_portal_token` (the already-bound `make_require_any_portal_token`) as `require_portal_dep`. |
| `frontend/src/components/transportation/TransportationOpsTopBar.jsx` | Administration group flagged `adminOnly: true` · `visibleNavGroups()` filters by `isAdmin()` · mobile hamburger (`txops-portal-topbar-mobile-toggle` / `txops-portal-topbar-mobile-nav`). |
| `frontend/src/components/transportation/TxOpsRestricted.jsx` (NEW) | `TxOpsRestricted` + `TxOpsRestrictedData` components — Transportation-branded restricted states with the required wording. |
| `frontend/src/pages/DispatchBoard.jsx` | TopBar mounted at top of the return tree. |
| `frontend/src/pages/DispatchOperationsMapPage.jsx` | TopBar mounted above the sticky dispatch breadcrumb. |
| `frontend/src/pages/DispatchHaulLedger.jsx` | TopBar mounted above the existing header. |
| `frontend/src/pages/DispatchCommandCenter.jsx` | TopBar mounted above the always-on command strip. |
| `frontend/src/pages/DispatchDriverQualification.jsx` | TopBar mounted above the read-only view. |
| `frontend/src/pages/DispatchHub.jsx` | (unchanged — Phase E already mounted the TopBar here) |

## Endpoints reviewed
| Endpoint | Phase F decision | Reasoning |
|---|---|---|
| `GET /api/admin/transportation/dashboard` | **Portal-aware** | Returns summary counts only — eligible drivers/trucks/carriers, pending queue counts, expiring docs counts. No record details. Safe operational signals for every portal role. |
| `GET /api/admin/transportation/documents/queue` | **Remains admin-strict** | Returns individual document rows with PII, file URLs, status notes. Not dispatch-safe. |
| `GET /api/admin/transportation/inspections/queue` | **Remains admin-strict** | Returns individual inspection records with detailed findings. Not dispatch-safe. |
| `GET /api/admin/transportation/trucks/{id}` | **Remains admin-strict** | Truck details include carrier/driver/document linkage. Drilldown is via Phase D right rail (RBAC-filtered). |
| `GET /api/admin/transportation/carriers/{id}` | **Remains admin-strict** | Carrier workspace exposes packets/insurance/HR. Drilldown via Phase D right rail. |
| `GET /api/admin/transportation/drivers/{id}` | **Remains admin-strict** | Driver workspace exposes HR-sensitive fields. Drilldown via Phase D right rail. |
| `GET /api/admin/transportation/related/{type}/{id}` | **Already portal-aware** (Phase D) | Composer with RBAC matrix on `_actor`. Unauthorized relations OMITTED. |
| `GET /api/admin/transportation/search` | **Already portal-aware** (Phase C) | RBAC matrix; dispatch token sees dispatch-safe results only. |
| `GET /api/operations/transportation/readiness` | **Already portal-aware** (Track 16.16) | Mission Control's primary readiness source. |

Net: **one endpoint** opened up (summary tiles only) — surgical, audit-friendly, no record-detail leakage.

---

## RBAC behavior
* Mission Control dashboard endpoint accepts admin · dispatch · leadership · safety · pm · hr · shop · fl tokens.
* TopBar Administration group hidden from non-admin sessions.
* `RequireTransportationPortal` continues to gate the `/transportation-operations/*` route at the page level.
* Phase D RBAC matrix UNCHANGED — admin sees all, dispatch sees dispatch-safe, HR never sees trucks/dispatch_assignment, etc. Unauthorized relations OMITTED entirely (locked by tests 22 + Phase D regression).
* No new role. No new token. No new permission predicate.

---

## Dispatch preservation proof
| Surface | Status |
|---|---|
| `/dispatch-portal/login` | Preserved · auth unchanged |
| `/dispatch-portal` (hub) | Preserved · TopBar already present from Phase E |
| `/dispatch-portal/board` | Preserved · TopBar added in Phase F |
| `/dispatch-portal/command` | Preserved · TopBar added in Phase F |
| `/dispatch-portal/map` | Preserved · TopBar added in Phase F |
| `/dispatch-portal/haul-ledger` | Preserved · TopBar added in Phase F |
| `/dispatch-portal/driver-qualification` | Preserved · TopBar added in Phase F |
| `/dispatch-portal/fleet` | Preserved · TopBar deferred (shared with admin Fleet route — Phase G candidate) |
| `/dispatch-portal/driver/:driverKey` (driver acknowledgement) | Preserved · TopBar intentionally absent (driver-facing) |
| `X-Dispatch-Token` token verb | Preserved |
| `clearDispatchToken` / `getDispatchToken` / `getDispatchUser` | Preserved |
| `RequireDispatch` guard | Preserved |
| Twilio callbacks / magic links / dispatch lifecycle | Preserved (no backend changes to those paths) |

---

## Admin oversight proof
* `/admin/transportation/*` alias still mounted under `A()` (`RequireAdmin`).
* `AdminSideNavV2` visible for admin on both `/admin/transportation` AND `/transportation-operations` (same shell, RBAC drives sidebar).
* Administration group visible only for admin sessions in TopBar.
* All record-detail endpoints (docs queue, inspections, drivers, carriers, trucks) STILL admin-strict — no leakage.

---

## Tests
**40 / 40 PASS** — `backend/tests/test_track_18_00_phase_f_portal_aware_data_layer.py`.

| Range | Coverage |
|---|---|
| 01–08 | All 8 dispatch routes preserved |
| 09 | TopBar mounted on 6 dispatch surfaces (Hub · Board · Command · Map · Haul Ledger · Driver Q) |
| 10 | Mission Control CTA → `/transportation-operations` |
| 11 | `/transportation-operations/*` mounted with dispatch-safe `TX()` gate |
| 12 | TopBar has zero "Admin Console" / "Admin Portal" copy |
| 13 | Guard has zero "Admin Console" copy |
| 14 | `TxOpsRestricted` reads as Transportation Operations · uses required wording |
| 15 | Administration group is `adminOnly: true` and filtered by `isAdmin()` |
| 16 | `TransportationApp` conditionally mounts `AdminSideNavV2` only when admin |
| 17 | `/admin/transportation/*` alias preserved with `A()` wrapper |
| 18 | Phase C Universal Search endpoint still registered |
| 19 | Search RBAC keys on `_actor` |
| 20 | Phase D composer deep-links to `/transportation-operations/*` |
| 21 | Phase D envelope unchanged · `schema_version=18.00D` · 5 section names |
| 22 | Phase D RBAC: HR token never sees trucks/dispatch |
| 23 | Dashboard endpoint is portal-aware (`require_portal_dep` parameter) |
| 24 | server.py wires `_require_any_portal_token` into the dashboard |
| 25 | Documents queue + inspections queue REMAIN admin-strict |
| 26 | No new collection name introduced |
| 27 | No source-record mutation in the composer |
| 28 | No dispatch route removed |
| 29 | Dispatch auth helpers preserved |
| 30 | Single TopBar module — no duplicate forks |
| 31 | Mobile hamburger testids exist |
| 32–37 | Phase A · B · C · D · E · 18.00E-FIX preserved |
| 38 | Phase F wired into deployment gate |
| 39 | This doc exists |
| 40 | Admin nav (Audit / Reports) not dead-end for admin |

**Cross-track regression** — 161 prior + 40 new = **201 Track-18 tests** now under the gate.

---

## Live smoke
* **Dispatch token now loads Mission Control dashboard endpoint**:
  ```
  POST /api/dispatch/login (dispatch@mascigc.com) → token len 101
  GET  /api/admin/transportation/dashboard + X-Dispatch-Token → HTTP 200
  → {"compliance_score":41,"tiles":{eligible_drivers,eligible_trucks,eligible_carriers,…},…}
  ```
* Anonymous on the same endpoint → HTTP 401 (correctly blocked).
* `/api/healthz` 200 · backend booted cleanly · zero supervisor errors after restart.

---

## Risks / deferrals (P-Phase G candidates)
* **Some Transportation shell sub-routes still call admin-strict endpoints.** For dispatch users hitting those, the existing page renders the existing empty/error state with Transportation Operations chrome (TopBar at top, no "Admin Console" wording). `TxOpsRestricted` is now available for those screens to adopt explicitly — Phase G can replace inline 403 handlers with `<TxOpsRestricted workspace="Documents" />` etc.
* **`/dispatch-portal/fleet` does not yet show the TopBar.** That route uses the shared `FleetVisibility` component (also used at admin/fleet); mounting the bar there changes admin chrome too — deferred to Phase G with a portal-context prop.
* **Driver acknowledgement pages** (`/dispatch-portal/driver/:driverKey`) intentionally do NOT get the TopBar — those are driver-facing magic-link pages and should stay calm/minimal.

## Hard guarantees
* No new collection. No new auth verb. No new token. No new permission predicate.
* Backend API prefix `/api/admin/transportation/*` UNCHANGED.
* Phase D `schema_version=18.00D` UNCHANGED.
* `RequireAdmin` · `RequireDispatch` · multi-login portal tokens UNCHANGED.
* Dispatch board · command · map · haul ledger · driver qualification · driver acknowledgement · Twilio callbacks · assignment lifecycle UNCHANGED.

---

## Files touched
* **NEW** `/app/frontend/src/components/transportation/TxOpsRestricted.jsx`
* **NEW** `/app/backend/tests/test_track_18_00_phase_f_portal_aware_data_layer.py`
* **NEW** `/app/memory/TRACK_18_00_PHASE_F_PORTAL_AWARE_DATA_LAYER.md`
* `/app/backend/routes/transportation_experience.py` — optional `require_portal_dep` parameter added
* `/app/backend/server.py` — wires `_require_any_portal_token` into the dashboard
* `/app/frontend/src/components/transportation/TransportationOpsTopBar.jsx` — role-aware nav + mobile hamburger
* `/app/frontend/src/pages/DispatchBoard.jsx` — TopBar mounted
* `/app/frontend/src/pages/DispatchOperationsMapPage.jsx` — TopBar mounted
* `/app/frontend/src/pages/DispatchHaulLedger.jsx` — TopBar mounted
* `/app/frontend/src/pages/DispatchCommandCenter.jsx` — TopBar mounted
* `/app/frontend/src/pages/DispatchDriverQualification.jsx` — TopBar mounted
* `/app/scripts/deployment_gate.py` — Phase F test path appended
