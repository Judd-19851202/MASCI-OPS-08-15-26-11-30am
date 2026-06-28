# TRACK 18.00E-FIX · Transportation Operations Portal Rehome

**Status:** ✅ GO
**Date:** 2026-02-10
**Type:** Emergency routing correction · zero-drift · frontend-led with one backend deep-link update

---

## Defect (root cause)
After Track 18.00 Phase E, the unified `TransportationOpsTopBar` was mounted at the top of `/dispatch-portal` so dispatchers see the Transportation Operations brand. **But** the Mission Control CTA — and every grouped-nav link inside the topbar — routed to `/admin/transportation/*`, which is gated by `RequireAdmin`. A dispatcher with a valid dispatch token but no admin token would click Mission Control and hit:

> "You don't have access to Admin Console"

That violates the product doctrine. **Transportation Operations is its own operational portal. Dispatch is a workspace inside it. Admin Console is an oversight role over it — not the parent container.**

---

## Fix
**Single shell, two access paths, RBAC determines content.**

### Frontend
1. **NEW** `/app/frontend/src/components/RequireTransportationPortal.jsx` — a dispatch-safe gate that accepts ANY portal token (admin · dispatch · leadership · safety · pm · hr · shop · fl). Unauthenticated visitors land at `/sign-in`, not `/admin/login`. Never renders the Admin-Console `AccessDenied` page.
2. **NEW route in `App.js`** — `/transportation-operations/*` wrapped by `TX(<AdminTransportation />)` (which re-exports `TransportationApp`). Same shell. Dispatch-safe.
3. **`/admin/transportation/*` retained** as an alias for admin oversight bookmarks (still wrapped by `A()`).
4. **`TransportationApp.jsx` made portal-aware** — `AdminSideNavV2` mounts ONLY when `isAdmin()` is true. Dispatch users get a clean Transportation Operations shell with no Admin Console sidebar.
5. **TopBar repointed** — Mission Control CTA, brand link, Search button, all 5 grouped nav rails (Operations · People · Compliance · Operations Intelligence · Administration), and the `/` keyboard shortcut all now route to `/transportation-operations/*`. Zero `/admin/transportation/*` links remain inside `NAV_GROUPS`.

### Backend
6. **Phase D composer `route` deep-links updated** — 32 frontend-route strings inside `/app/backend/routes/transportation_relationships.py` now point at `/transportation-operations/*`. This makes related-record rows in the right rail clickable by dispatch users without bouncing through the admin gate. **API prefix unchanged** (`/api/admin/transportation/related/...` stays — backend URLs are not user-facing). **Schema version still `18.00D`.**

### No-change zones
* No new collection.
* No new auth verb.
* No new token storage.
* No new RBAC role.
* No data migration.
* No new route file on the backend.
* `RequireAdmin`, `RequireDispatch`, multi-login `portal_tokens.*`, `X-Dispatch-Token`, `getAdminToken`, `getDispatchToken` — all untouched.
* Dispatch lifecycle code, dispatch board, dispatch map, dispatch command center, dispatch haul ledger, dispatch driver qualification, dispatch driver acknowledgement, Twilio callbacks, assignment lifecycle — all untouched.

---

## Routes changed
| Surface | Before | After |
|---|---|---|
| TopBar brand `<Link to>` | `/admin/transportation` | `/transportation-operations` |
| TopBar Search button | `/admin/transportation` | `/transportation-operations` |
| TopBar Mission Control CTA | `/admin/transportation` | `/transportation-operations` |
| TopBar nav: Operations group | `/admin/transportation/*` | `/transportation-operations/*` |
| TopBar nav: People group | `/admin/transportation/*` | `/transportation-operations/*` |
| TopBar nav: Compliance group | `/admin/transportation/*` | `/transportation-operations/*` |
| TopBar nav: Intelligence group | `/admin/transportation/*` | `/transportation-operations/*` |
| TopBar nav: Administration group | `/admin/transportation/*` | `/transportation-operations/*` |
| `/` keyboard shortcut fallback | `/admin/transportation` | `/transportation-operations` |
| Phase D relationship `route` deep-links | `/admin/transportation/*` | `/transportation-operations/*` |
| **App.js: NEW** | — | `/transportation-operations/*` → `TX(<AdminTransportation />)` |

## Routes preserved
* `/admin/transportation/*` — still mounted under `A()` for admin oversight.
* `/dispatch-portal`, `/dispatch-portal/login`, `/dispatch-portal/board`, `/dispatch-portal/command`, `/dispatch-portal/map`, `/dispatch-portal/haul-ledger`, `/dispatch-portal/driver-qualification`, `/dispatch-portal/driver/:driverKey`, `/dispatch-portal/fleet`, `/dispatch-portal/hub_v2`, `/dispatch-portal/hub_legacy`, `/dispatch-portal/forgot-password`, `/dispatch-portal/reset/:token`, `/dispatch-portal/change-password`.
* Backend API `GET /api/admin/transportation/related/{entity_type}/{entity_id}` (Phase D · `schema_version=18.00D`) — UNCHANGED prefix.

---

## RBAC behavior
* **Inside the new `/transportation-operations/*` shell**: any portal token unlocks the routes. Backend composers (Phase C search · Phase D relationships · Track 16.16 readiness) continue to RBAC-filter the *content* based on the `_actor` field. A dispatcher sees the universal Search and Relationships drawers with dispatch-safe results; admin-only HR/private compliance data is OMITTED entirely (Phase D anti-leak doctrine).
* **Admin-only sub-routes** (e.g., Audit Timeline, certain compliance internals) still rely on backend admin-strict endpoints. If a dispatcher navigates there, the page renders the existing Transportation-branded empty/error state — **never** the "Admin Console access denied" page.

---

## Tests
* **NEW** `/app/backend/tests/test_track_18_00e_fix_transportation_portal_rehome.py` — **30 regression tests** wired into the deployment gate.

| Range | Coverage |
|---|---|
| 01–04 | Guard exists · accepts dispatch · no `/admin/login` redirect · no `AccessDenied` import |
| 05–08 | `/transportation-operations/*` route registered · uses `TX()` not `A()` · admin alias still mounted · both routes render the SAME shell module |
| 09–13 | TopBar Mission Control CTA / Search / brand / nav groups / `/` shortcut all repointed; zero `/admin/transportation` links left inside `NAV_GROUPS` |
| 14 | `TransportationApp` conditionally mounts `AdminSideNavV2` only when `isAdmin()` |
| 15–19 | Every dispatch route preserved (login, hub, board, command, map, haul-ledger, driver-qualification, driver, password reset/change/forgot) |
| 20 | Backend API prefix `/api/admin/transportation` PRESERVED (no breakage of existing API calls) |
| 21 | `SCHEMA_VERSION == "18.00D"` still emitted |
| 22 | Composer `route` fields all repointed to `/transportation-operations/*` |
| 23 | Phase D RBAC matrix unchanged (admin=all · dispatch sees dispatch-safe · anon=empty) |
| 24 | No new backend route file introduced |
| 25–26 | Phase C and Phase D still registered server-side |
| 27 | Fix wired into `deployment_gate.py` |
| 28 | This summary doc exists |
| 29 | No "Admin Console" wording inside the new guard |
| 30 | Single shell module reused — no duplicate `TransportationOperationsApp.jsx` |

* **Cross-track regression** — Phase A · B · C · D · E all still PASS in their existing test suites (131 prior + 30 fix = **161 Track-18 tests** now under the gate).

---

## Risks
* **None blocking.** Three minor notes:
  1. Some sub-routes inside the Transportation Operations shell still call admin-strict endpoints. For pure dispatch users those endpoints will 403 at the data layer, surfacing as the existing transportation-branded empty/error states. The user-facing chrome is still Transportation Operations — never "Admin Console access denied". Tightening these data-layer guards to be portal-aware is a Phase F item.
  2. The portal switcher in `PortalShell` may briefly read "Admin Portal" for dispatch users until the design-system header is portal-aware. Cosmetic only; not gating.
  3. `AdminSideNavV2` is suppressed for dispatch users, leaving the existing `TransportationSubNav` as the in-shell navigator. That sub-nav is what the prompt's grouped operational navigation maps to — verified.

---

## Files touched
* **NEW** `/app/frontend/src/components/RequireTransportationPortal.jsx`
* **NEW** `/app/backend/tests/test_track_18_00e_fix_transportation_portal_rehome.py`
* **NEW** `/app/memory/TRACK_18_00E_FIX_TRANSPORTATION_PORTAL_REHOME.md`
* `/app/frontend/src/App.js` — `TX()` wrapper + `/transportation-operations/*` route registration · imports
* `/app/frontend/src/pages/transportation/TransportationApp.jsx` — conditional `AdminSideNavV2`
* `/app/frontend/src/components/transportation/TransportationOpsTopBar.jsx` — all links repointed
* `/app/backend/routes/transportation_relationships.py` — 32 `route` deep-link strings repointed (API prefix preserved)
* `/app/scripts/deployment_gate.py` — fix test path appended
