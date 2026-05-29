# Broken Route Fix Plan

_Phase V.5 · P0 Platform Trust Restoration · 2026-05-29 20:32 UTC._

> Inventory of every routing defect found in the audit, grouped by
> priority. **NO FIXES IN THIS PASS** — fix plan is documentation only.

## 1 · Currently SHIPPED to preview (awaiting redeploy)

| ID | Defect | Fix shipped |
|---|---|---|
| ROUTE-1 | PM `/pm/equipment` bounced to `/pm/login` | `api.js` namespace-aware 401 + `EquipmentDashboard` portal-context widget gating + list endpoint PM scope filter |
| ROUTE-2 | `/shop/equipment` list route missing | `App.js` adds `<Route path="/shop/equipment" element={S(<EquipmentDashboard />)} />`; ShopHub "Recent Pre-Op Inspections" link enabled |
| PO-1 | PO receipt PDF blank tab on iPad | new `GET /api/po-requests/{id}/receipt` stream endpoint + frontend Blob-URL helper |
| LAYOUT-1 (P0-1) | Form field bleed on iPad | platform-wide canonical grid migration (215 occurrences) + `FormGrid.jsx` primitive |

## 2 · Documented P1 — defer until P0 cycle closes

| ID | Defect | Surface | Severity | Recommended fix |
|---|---|---|---|---|
| ROUTE-3 | `/equipment/:id` (no portal prefix) redirects to `/admin/equipment/:id` unconditionally | `App.js:353` `RedirectWithId base="/admin/equipment"` | P1 | replace with a portal-context-aware redirect that reads any present portal token from localStorage and routes to `/admin/...` or `/shop/...` or `/pm/...` accordingly; fall back to login if none present |
| ROUTE-4 | `/inspections/:id` redirect same pattern | `App.js:355` | P1 | mirror ROUTE-3 |
| BTN-1 | Shop Equipment Trash button visible but 403 on click | `EquipmentDashboard.jsx` row action | P1 | `!isPmContext && !isShopContext &&` gate (Shop is read-allowed on inspection records but admin-only on delete) |
| BTN-2 | HR "Edit employee" button visible but persist gated to admin | `HrEmployees.jsx` row action | P2 | re-check permission rendering; either grant HR edit on safe fields, or hide button when no admin token |
| BTN-3 | Dispatch "Add driver" visible to all dispatch users; lead-only persists | `DispatchDrivers.jsx` toolbar | P2 | conditional render on `dispatch_user.lead === true` |
| ROUTE-5 | PM sidebar entry to `/admin/exposure-tile` (PM Exposure Tile not routed live per operator stop-condition) | `PmHub.jsx` More menu | P2 | hide sidebar entry while PM Exposure Tile remains unrouted |

## 3 · Out of scope of fix (intentional / by-design)

- `/admin/equipment/:id` accessible from PM via `AP` wrapper — intentional cross-portal admin-namespace access. PM gets admin-namespace pathname but is recognized by backend as scoped PM token. This is deliberate.
- `/equipment/new` (form route) is publicly submittable by design — anonymous foremen can file inspections without logging in. Rate-limited.
- Direct-URL access to admin routes without nav links — intentional doctrine ("operator-only emergency paths").
- Public share-link routes (`/share/...`) — intentional anonymous access with rate limits.

## 4 · Stale tests (block pre-deploy orchestrator but not production)

| Test | Assertion | Current state |
|---|---|---|
| `test_iter219_portal_titles_and_discoverability::test_portal_hub_persona_tags_its_title[DispatchHub.jsx-...]` | expects "Dispatch · MASCI" tab title | hub renamed to "Dispatch Command · MASCI" intentionally; test needs `EXPECTED_TITLES` update |
| same test for `ShopHub.jsx-...` | expects "Shop · MASCI" | hub renamed to "Shop Recovery · MASCI" |
| `test_daily_reports::test_delete_and_verify_removed` | expects DELETE → 200 | freeze contract returns 410; test needs retirement |
| `test_daily_reports::test_delete_404_for_unknown` | expects DELETE unknown → 404 | freeze contract returns 410; test needs retirement |
| `test_wave_1a::test_unified_projector_surfaces_new_dr` | non-deterministic when preview DB has > 200 DRs/day | needs `project_number` filter; not a prod issue |

**Recommended order**: address tests AFTER the next prod redeploy stabilizes; tests block the orchestrator's BLOCK verdict but the orchestrator is advisory.

## 5 · Net-state verdict

| Severity | Open | Fixed (preview) |
|---|---|---|
| P0 | **0** | 4 (ROUTE-1, ROUTE-2, PO-1, LAYOUT-1) |
| P1 | 3 (ROUTE-3, ROUTE-4, BTN-1) | 0 |
| P2 | 3 (BTN-2, BTN-3, ROUTE-5) | 0 |
| P3 (test-only) | 5 | 0 |

**No active P0 routing defects remain in preview.** P1/P2 items are documented for a future operator-authorized hardening pass; per the operator's directive ("STOP after audit · DO NOT FIX ANYTHING"), no implementation begins.

---

_End of BROKEN_ROUTE_FIX_PLAN.md._
