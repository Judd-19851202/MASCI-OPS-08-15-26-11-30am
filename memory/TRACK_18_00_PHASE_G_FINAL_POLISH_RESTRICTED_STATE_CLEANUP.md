# TRACK 18.00 · Phase G · Final Polish + Restricted-State Cleanup

**Status:** ✅ GO
**Date:** 2026-02-10
**Type:** Closing polish · zero-drift · no new features

---

## Mission
Close the final Track 18.00 polish gaps after Phase F's portal-aware data layer landed:
1. TopBar on `/dispatch-portal/fleet`.
2. Adopt `TxOpsRestrictedData` where the Transportation shell previously rendered legacy inline error copy.
3. Audit-lock the rule: zero "Admin Console" / "Admin Portal" wording anywhere inside the Transportation Operations shell or shared TopBar (covered by static scan in `test_14`).
4. Verify visible nav items load or restrict gracefully — no dead ends.
5. Preserve every preceding phase (A · B · C · D · E · 18.00E-FIX · F).

---

## Surfaces polished

### Workstream A — TopBar on dispatch fleet
* `/dispatch-portal/fleet` route in `App.js` now mounts the `TransportationOpsTopBar` inline above the shared `<FleetVisibility scope="dispatch" />` component — using a tiny JSX fragment wrapper directly in the `<Route element={…}>` expression. Zero changes to the `FleetVisibility` component itself; the admin/shop/safety Fleet routes are untouched.

### Workstream B — Restricted-state cleanup
* `_views.jsx` `TopCleanupOpportunityCard` previously rendered `"Cleanup signals unavailable."` as plain grey text when the admin-strict endpoint returned 401/403 for non-admin tokens. Replaced with `<TxOpsRestrictedData testid="tx-dashboard-top-cleanup-error" />` — same testid kept for backwards-compat with existing UI tests; new copy now reads:
  > "Transportation Operations · This Transportation data is not available for your role."
* `TxOpsRestricted` (full-card) and `TxOpsRestrictedData` (inline strip) components remain available for further screens to adopt as needed (Phase H candidate when they show up).

### Workstream C — Visible nav validation
Locked by `test_18` (every `NAV_GROUPS` item has an `href:`) and `test_19` (every nav target is either `/transportation-operations/*` or `/dispatch-portal/*` — never `/admin/transportation/*`). The Administration group is `adminOnly: true` so dispatch users never see Reports / Audit clickable dead ends (`test_16`, `test_17`).

### Workstream D — Access-state doctrine
* Every Transportation Operations page that calls an admin-strict endpoint should adopt either `TxOpsRestricted` (full restricted screen) or `TxOpsRestrictedData` (inline restricted strip) when the response is 401/403.
* Loading states stay calm and Transportation-themed (`"Loading top cleanup signal…"`, `"Loading HR sync health…"`).
* Empty states use the existing `EmptyState` primitive with descriptive titles.
* Error states (where they exist) must use `TxOpsRestrictedData` going forward — `_views.jsx` is the first adopter and serves as the pattern for Phase H.

### Workstream E — Data access not expanded
* The audit confirmed Phase F made the correct call: only the summary-count dashboard endpoint was opened up. Record-detail endpoints stay admin-strict. Phase G does NOT touch any backend RBAC.

---

## Dispatch surfaces (TopBar coverage)
| Surface | TopBar | Phase |
|---|---|---|
| `/dispatch-portal` (hub) | ✅ | E |
| `/dispatch-portal/board` | ✅ | F |
| `/dispatch-portal/command` | ✅ | F |
| `/dispatch-portal/map` | ✅ | F |
| `/dispatch-portal/haul-ledger` | ✅ | F |
| `/dispatch-portal/driver-qualification` | ✅ | F |
| `/dispatch-portal/fleet` | ✅ | **G** |
| `/dispatch-portal/driver/:driverKey` | ❌ (driver-facing magic-link surface, intentionally minimal) | — |
| `/dispatch-portal/login`, `/forgot-password`, `/reset/`, `/change-password` | ❌ (auth surfaces, intentionally minimal) | — |

---

## Routes preserved
* All `/dispatch-portal/*` routes — including the seven workspace surfaces above plus driver and auth surfaces — preserved exactly as Phase F left them.
* `/admin/transportation/*` admin alias preserved with `RequireAdmin` (`A()`).
* `/transportation-operations/*` canonical dispatch-safe route preserved with `RequireTransportationPortal` (`TX()`).
* Backend API prefixes UNCHANGED.

## Auth preserved
* `RequireAdmin` · `RequireDispatch` · `RequireTransportationPortal`.
* `X-Admin-Token` · `X-Dispatch-Token` · multi-login `portal_tokens.*`.
* No new permission predicate. No new token storage. No new auth verb.

## RBAC
* Phase D RBAC matrix unchanged.
* Phase F portal-aware dashboard endpoint unchanged.
* All record-detail endpoints (docs / inspections / drivers / carriers / trucks) **remain admin-strict** (locked by `test_24`).
* Anti-leak doctrine: unauthorized relations OMITTED entirely.

---

## Admin oversight proof
* `/admin/transportation/*` still mounted under `A()` (`RequireAdmin`).
* `AdminSideNavV2` visible for admin sessions.
* Administration TopBar group visible only for admin sessions.
* Admin Fleet routes (`/shop/fleet`, `/safety-portal/fleet`) **do not** get the TopBar (locked by `test_10`) — only `/dispatch-portal/fleet` does.

---

## Mobile / iPad
* Phase F hamburger toggle preserved (`txops-portal-topbar-mobile-toggle` / `-mobile-nav`).
* No new mobile work in Phase G.

---

## Tests
**40 / 40 PASS** — `/app/backend/tests/test_track_18_00_phase_g_final_polish.py`.

| Range | Coverage |
|---|---|
| 01–02 | `/dispatch-portal/fleet` route present + now mounts TopBar inline |
| 03–08 | TopBar on hub · board · command · map · haul-ledger · driver-qualification |
| 09 | TopBar NOT on driver magic-link surfaces |
| 10 | Admin Fleet (shop/safety) NOT decorated with TopBar |
| 11–12 | `TxOpsRestricted` and `TxOpsRestrictedData` components present |
| 13 | Transportation shell adopts `TxOpsRestrictedData` |
| 14 | **Static scan across the entire `/transportation/` page tree + `/components/transportation/` — zero "Admin Console" / "Admin Portal" copy in user-facing JSX** |
| 15 | Same lock on the TopBar source |
| 16 | Administration group `adminOnly: true` |
| 17 | `visibleNavGroups()` filters by `isAdmin()` |
| 18 | Every NAV_GROUPS item has an `href` (no clickable null) |
| 19 | Every nav target is `/transportation-operations/*` or `/dispatch-portal/*` (zero legacy admin) |
| 20–22 | Phase C search, Phase D relationships, Mission Control all still registered |
| 23 | Dashboard endpoint is portal-aware (Phase F lock) |
| 24 | Record-detail endpoints remain admin-strict (5 endpoints checked) |
| 25–27 | Dispatch / Admin / Driver auth all unchanged |
| 28 | No new collection introduced |
| 29 | No dispatch route removed |
| 30 | No mutation API added |
| 31–37 | Phase A · B · C · D · E · 18.00E-FIX · F all preserved |
| 38 | Phase G wired into deployment gate |
| 39 | This doc exists |
| 40 | `TxOpsRestricted` text contract preserved |

**Cross-track regression** — 201 prior + 40 new = **241 Track-18 tests** now under the gate.

---

## Live smoke
Will be verified by testing_agent_v3_fork:
* Dispatch login → all 7 dispatch surfaces (incl. `/dispatch-portal/fleet`) show TopBar.
* Driver magic-link routes never show TopBar.
* Mission Control CTA opens `/transportation-operations` without Admin Console wording.
* Cleanup signal data-restricted screens read as "Transportation Operations · This Transportation data is not available for your role."
* Admin Fleet routes still render without TopBar (no chrome drift).
* Mobile hamburger at 390 px works · iPad 1024 px works · desktop 1920 px works.

---

## Risks
* **None blocking.** Two minor follow-ups:
  1. Other admin-strict consumers in the shell (HR sync widget, document queue counts) still return `null` or grey text on 401/403. Adopting `TxOpsRestrictedData` everywhere is mechanical and can be done incrementally as those screens get touched (Phase H candidate).
  2. The cleanup signals route remains admin-strict at the backend — only the *frontend* error state was upgraded. Opening that endpoint to portal-aware reads would be a Phase H decision based on whether dispatch needs cleanup intelligence visibility.

## Deferrals (Phase H candidates)
* Adopt `TxOpsRestrictedData` on the HR sync, document queue, inspection queue, and rate schedule loading screens (mechanical · no API changes).
* If product wants dispatchers to see cleanup-signal counts, open the cleanup-signals endpoint to portal-aware reads (mirroring Phase F's dashboard fix).
* Cleanup-companion fleet workspace polish.
* Dispatcher-personalized "your queue" badge on Mission Control (carried from Phase F finish suggestion).
* Global command palette tying Search ↔ Relationships drawer.

---

## Files touched
* **NEW** `/app/backend/tests/test_track_18_00_phase_g_final_polish.py`
* **NEW** `/app/memory/TRACK_18_00_PHASE_G_FINAL_POLISH_RESTRICTED_STATE_CLEANUP.md`
* `/app/frontend/src/App.js` — `/dispatch-portal/fleet` route wraps `<FleetVisibility>` with TopBar inline
* `/app/frontend/src/pages/transportation/_views.jsx` — `TopCleanupOpportunityCard` error state now uses `TxOpsRestrictedData`
* `/app/scripts/deployment_gate.py` — Phase G test path appended
