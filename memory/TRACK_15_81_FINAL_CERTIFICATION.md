# TRACK 15.81 · Dispatch Map Portal Access Failure — FINAL CERTIFICATION

**Status:** GO
**Date:** 2026-02-?? (preview-side fix, awaiting production deploy)
**Six Pillars:** Powerful · Simple · Beautiful · Trusted · Proven · Deployable — all satisfied.
**RBAC weakened?** NO. Admin Console route `/operations-map` is untouched.

---

## Phase 1 — Reproduction

| Field | Value |
|---|---|
| Login | `jaymn.judd@mascigc.com` (Super Admin, multi-portal) signed into `/dispatch-portal` |
| Portal context (browser) | Dispatch (URL begins with `/dispatch-portal`) |
| Active tokens (Dispatch login alone) | `masci.dispatch.token` ONLY — no `masci.admin.token` unless `/sign-in` multi-login was used |
| Click | Asset marker in Live Fleet Map · Count tile · "Open Full Live Map" CTA |
| Generated URL | `/operations-map` (or `/operations-map?asset=<unit>`) |
| Target route component | `OperationsMapPage` |
| Route guard | `RequireAdmin` (`A()` wrapper in `App.js` line 747) |
| Guard verdict | Token absent → `isSignedInAnywhere()` returns true (Dispatch token present) → renders `<AccessDenied attemptedPortal="admin" />` |
| User-visible result | "403 · Access Restricted · You don't have access to Admin Console" |
| Backend API used by the page | `/api/operations-map/*` — already accepts ANY portal token via `make_require_any_portal_token` |
| Expected portal scope | Dispatch (because the click happened inside the Dispatch shell) |
| Actual portal scope routed | Admin Console |

→ **Pure routing / link-target bug. Backend RBAC was already correct.**

---

## Phase 2 — Route Ownership Audit

| Action | Generated Route (before fix) | Owning Portal (before fix) | Required Role | Current Behavior | Correct Behavior |
|---|---|---|---|---|---|
| Dispatch Live Fleet Map · asset click | `/operations-map?asset=...` | Admin Console (`A()`) | admin token | 403 for dispatch-only sessions | Dispatch-owned map detail in-portal |
| Dispatch Live Fleet Map · count tile (attention/offline/working/idle/assigned/total) | `/operations-map` | Admin Console (`A()`) | admin token | 403 for dispatch-only sessions | Open Dispatch-owned full live map |
| Dispatch Live Fleet Map · "Open Full Live Map" CTA | `/operations-map` | Admin Console (`A()`) | admin token | 403 for dispatch-only sessions | Open Dispatch-owned full live map |
| Dispatch Live Fleet Map · "Open Operational Board" CTA | `/dispatch-portal/board` | Dispatch | dispatch token | OK | Unchanged — correct already |
| Dispatch Live Snapshot · empty-state link | `/operations-map` | Admin Console (`A()`) | admin token | 403 for dispatch-only sessions | Dispatch-owned full live map |
| Dispatch Live Snapshot · count tiles | `/operations-map` | Admin Console (`A()`) | admin token | 403 for dispatch-only sessions | Dispatch-owned full live map |
| Dispatch Live Snapshot · "Open Full Live Map" CTA | `/operations-map` | Admin Console (`A()`) | admin token | 403 for dispatch-only sessions | Dispatch-owned full live map |
| Admin Console · navigation to Live Map | `/operations-map` | Admin Console (`A()`) | admin token | OK | Unchanged — admin-only intentional |

**Cross-portal violations found: 6** (Hero × 3, Snapshot × 3). **All routed back into Dispatch.**

---

## Phase 3 — RBAC / Portal Guard Audit

1. **Does Super Admin have global portal access?**
   - Via `/sign-in` (multi-login): yes — every portal token is minted and `usePortalHydration("admin", ...)` silently mints an admin token on demand.
   - Via direct Dispatch login: **NO** — only the Dispatch token is present. This is the production failure case the screenshot captured.
2. **If yes, why is `/operations-map` blocked?**
   - When dispatch-only, `RequireAdmin.hasToken = isAdmin() = false`. `usePortalHydration` finishes with state `"ready"=false`. `isSignedInAnywhere()` is true (dispatch token exists) → renders `AccessDenied attemptedPortal="admin"`.
3. **Should this action stay inside Dispatch instead?** **Yes** — the click originated in the Dispatch shell on an operationally-essential map.
4. **Which guard produced the 403?** `RequireAdmin` (`/app/frontend/src/components/RequireAdmin.jsx`).
5. **Which field/claim failed?** No `masci.admin.token` present + the user already has a non-admin portal session.
6. **Is the route mislabeled as Admin-only?** No — `/operations-map` is a legitimate Admin Console route. The bug is the **link** in Dispatch surfaces pointing to it.
7. **Is the link wrong?** **Yes** — six links in two Dispatch portal components targeted the Admin Console URL.

→ **Link bug, NOT a guard bug. Fix is at the link source, not the guard.**

---

## Phase 4 — Fix Implemented (Preferred Fix A "Correct the Dispatch Link")

Files changed:

1. `/app/frontend/src/App.js`
   - **Added** Dispatch-owned alias route:
     ```jsx
     <Route path="/dispatch-portal/map" element={DP(<OperationsMapPage />)} />
     ```
     Mounts the SAME `OperationsMapPage` component under `RequireDispatch` (the existing Dispatch guard). No new portal, no new component, no new endpoint.
2. `/app/frontend/src/components/DispatchMapHero.jsx`
   - Asset-marker click navigates to `/dispatch-portal/map?asset=<unit>`.
   - Count-tile clicks (`attention`, `offline`, `working`, `idle`, `assigned`, `total`) all link to `/dispatch-portal/map`.
   - "Open Full Live Map" CTA → `/dispatch-portal/map`.
3. `/app/frontend/src/components/DispatchLiveSnapshot.jsx`
   - Empty-state link, count tiles, and "Open Full Live Map" CTA all → `/dispatch-portal/map`.

What did NOT change (deliberately):

- `<Route path="/operations-map" element={A(<OperationsMapPage />)} />` — Admin Console mount stays admin-only.
- `RequireAdmin`, `RequireDispatch` — both guards unchanged.
- `make_require_any_portal_token` — backend gate already accepts Dispatch tokens.
- Any RBAC backend route, password policy, or audit gate.

Net additive footprint: **1 new route, 6 link target updates, 1 new regression file**.

---

## Phase 5 — UX Failure State

For the **genuinely-unauthorized** case (e.g. a Field-Leadership-only user wanders to `/dispatch-portal/map`), `RequireDispatch` either:

- Silently mints a Dispatch token if the user's directory session entitles them (`usePortalHydration("dispatch", false)`), OR
- Renders `<AccessDenied attemptedPortal="dispatch" />` — which carries the correct "Back to your portal" CTA and the **correct portal name** ("Dispatch"). No more misleading "Admin Console" copy on a Dispatch action.

Normal Dispatch users on the new `/dispatch-portal/map` route never hit any failure surface — the guard is `RequireDispatch`, which their token satisfies by definition.

---

## Phase 6 — Regression Tests

Added: `/app/backend/tests/test_track_15_81_dispatch_map_portal.py` (9 tests, all green locally).

| Test | Asserts |
|---|---|
| `test_dispatch_portal_owned_map_route_exists` | `<Route path="/dispatch-portal/map" element={DP(<OperationsMapPage />)} />` is in `App.js` |
| `test_admin_operations_map_route_still_admin_only` | `<Route path="/operations-map" element={A(<OperationsMapPage />)} />` UNCHANGED |
| `test_dispatch_map_hero_has_no_admin_console_links` | `DispatchMapHero.jsx` has zero `to="/operations-map"` / `navigate("/operations-map")` and at least one `/dispatch-portal/map` |
| `test_dispatch_live_snapshot_has_no_admin_console_links` | Same guard for `DispatchLiveSnapshot.jsx` |
| `test_no_dispatch_portal_component_links_to_admin_operations_map` | Broad sweep across `pages/Dispatch*.jsx`, `components/Dispatch*.jsx`, and `components/dispatch/**` |
| `test_operations_map_snapshot_accepts_dispatch_token` | Backend `/api/operations-map/snapshot` returns 200 for dispatch token |
| `test_operations_map_timeline_accepts_dispatch_token` | Backend `/api/operations-map/timeline` returns 200 for dispatch token |
| `test_operations_map_search_accepts_dispatch_token` | Backend `/api/operations-map/search` returns 200 for dispatch token |
| `test_operations_map_anonymous_still_rejected` | Anonymous call MUST still 401/403 — proves RBAC is not weakened |

Wired into the permanent regression suite at `/app/scripts/deployment_gate.py` line 76+ (`REGRESSION_FILES`). Deployment gate exits 0 with the new file included.

---

## Phase 7 — Production Smoke Plan (post-deploy)

1. Open `mascidocs.com/dispatch-portal/login`, sign in as Super Admin (`jaymn.judd@mascigc.com`).
2. Confirm `DispatchHub` loads with the Live Fleet Map hero visible.
3. Click a map asset marker → expect URL `/dispatch-portal/map?asset=<unit>`. NO 403.
4. Click each count tile (Attention / Offline / Working / Idle / Assigned / Total) → expect URL `/dispatch-portal/map`. NO 403.
5. Click "Open Full Live Map" → expect URL `/dispatch-portal/map`. NO 403.
6. Click "Open Operational Board" → expect URL `/dispatch-portal/board` (unchanged behavior).
7. Scroll to the Live Fleet Snapshot strip lower on Dispatch hub. Repeat steps 4-5 with its tiles + CTA.
8. Confirm `/dispatch-portal/map` page renders the full operations-map UI (top bar, filter rail, MapLibre canvas, timeline dock) and the data fetched is non-empty (or at minimum the contract envelope returns 200).
9. Sign out, sign in as a pure Dispatcher (`dispatch@mascigc.com`), repeat steps 2-8. Confirm no 403 and no "Admin Console" copy is ever shown.
10. As an unauthenticated visitor, navigate to `https://mascidocs.com/operations-map` directly. Expect bounce to `/admin/login`. **Admin Console route remains protected.**
11. As an unauthenticated visitor, navigate to `https://mascidocs.com/dispatch-portal/map`. Expect bounce to `/dispatch-portal/login` (`RequireDispatch` default). No 403 leak.

---

## Phase 8 — Final Certification

| # | Question | Answer |
|---|---|---|
| 1 | What exact click caused the 403? | Map marker click, count tile click, or "Open Full Live Map" CTA inside `DispatchMapHero` / `DispatchLiveSnapshot` |
| 2 | What exact route was generated? | `/operations-map` (and `/operations-map?asset=...`) |
| 3 | Which portal owned that route? | Admin Console (`A()` = `RequireAdmin`) |
| 4 | Which guard blocked it? | `RequireAdmin` → `AccessDenied attemptedPortal="admin"` |
| 5 | Link bug, guard bug, or both? | **Link bug only.** Backend already accepted dispatch tokens. |
| 6 | Can Super Admin now use Dispatch map actions? | **YES** — `/dispatch-portal/map` is reached via `RequireDispatch` which Super Admin satisfies by carrying every portal token. |
| 7 | Can Dispatcher use allowed Dispatch map actions? | **YES** — Dispatch token is exactly what `RequireDispatch` wants. |
| 8 | Are true Admin routes still protected? | **YES** — `/operations-map`, `/admin/*` all unchanged. Static + live regression tests prove it. |
| 9 | Did the fix weaken RBAC? | **NO.** Zero changes to guards, gates, or admin-only routes. New route mounts the SAME component under the SAME-strength Dispatch guard the rest of `/dispatch-portal/*` uses. |
| 10 | Are regression tests passing? | **YES** — 9/9 green in `test_track_15_81_dispatch_map_portal.py`; deployment gate passes with the new file included. |
| 11 | GO or NO-GO? | **GO.** |

---

## Hard Rule Compliance Check

- [x] Dispatch map click no longer throws misleading Admin Console 403.
- [x] Admin Console security NOT weakened.
- [x] Dispatcher allowed actions no longer route into Admin Console.
- [x] Regression tests enforce all of the above.
- [x] No new portal created.
- [x] No broad auth rewrite.
- [x] Additive, minimal, rollbackable (single new route + 6 string changes).

**RESULT: GO.**
