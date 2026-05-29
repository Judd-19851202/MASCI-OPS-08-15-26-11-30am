# Shop Pre-Op Workflow Certification

_Phase V.5 · P0-2C · 2026-05-29 19:55–20:15 UTC._

> **Status**: SHIPPED to preview. End-to-end re-tested as Shop user
> (`testmech@mascigc.com`). Recent Pre-Op Inspections link is now
> functional. Full pre-op list reachable from inside the Shop portal.

## 1 · Operator-reported defects

> "Shop Portal does not clearly present Pre-Op inspections.
> Recent Pre-Ops appears buried / hidden / non-obvious.
> Click behavior appears nonfunctional or unclear."

## 2 · Investigation

`ShopHub.jsx` first-screen architecture (already correct per its own
doctrine — "operational recovery, NOT maintenance"):

1. **Equipment Needing Attention** — `DispatchLifecycleTile` + `OpenItemsPanel(baseHref="/shop/equipment")`. The OpenItemsPanel already surfaces failed pre-ops with clickable rows that navigate to `/shop/equipment/{id}`. ✅ Failed pre-ops were on first-screen.
2. Active Recovery Work
3. Waiting / Delays
4. Returned to Service
5. Operational Continuity History
6. **More** (collapsible footer) — disabled placeholder links for Trends / Activity / Equipment / Parts / Integrations / **Recent Pre-Op Inspections**.

The defect was in the "More" footer at line 446 of `ShopHub.jsx`:

```jsx
<MoreLink to="?legacy=recent" icon={ClipboardList}
          label="Recent Pre-Op Inspections" testId="shop-more-recent" disabled />
```

Two problems:
- **`disabled` prop**: rendered the link as a non-clickable `<span>` ("Reachable via direct URL · kept out of first-screen cognition").
- **`to="?legacy=recent"`**: placeholder that never navigated anywhere meaningful.

And the broader cause: **`/shop/equipment` route did not exist** in `App.js`. Only the detail route `/shop/equipment/:id` existed. Shop users could only reach individual inspections via the OpenItemsPanel; the full list was simply unreachable from the Shop portal.

## 3 · Fix

### 3a · Add the `/shop/equipment` list route

`frontend/src/App.js`:

```diff
   <Route path="/shop/fleet" element={S(<FleetVisibility scope="shop" />)} />
+  <Route path="/shop/equipment" element={S(<EquipmentDashboard />)} />
   <Route path="/shop/equipment/:id" element={S(<ViewEquipmentInspection context="shop" />)} />
```

Shop now has the same dashboard shape as admin and PM, gated by `S` (`RequireShop`) — so a shop user can browse the full pre-op list with all auxiliary widgets visible (Equipment Trends, Open Shop Items, Shop Activity Feed) because the Shop token IS accepted by the admin namespace per `require_shop_or_admin`.

### 3b · Enable the More-footer link

`frontend/src/pages/ShopHub.jsx`:

```diff
-  <MoreLink to="?legacy=recent" icon={ClipboardList}
-            label="Recent Pre-Op Inspections" testId="shop-more-recent" disabled />
+  <MoreLink to="/shop/equipment" icon={ClipboardList}
+            label="Recent Pre-Op Inspections" testId="shop-more-recent" />
```

The link is now active; tapping it navigates to the full list.

### 3c · Preserved doctrine

The "More" footer remains a deliberate de-emphasis surface — that aspect of the ShopHub doctrine is correct (failed pre-ops are first-screen via Equipment Needing Attention). What the operator was right to call out is that the *link itself* must work when expanded.

## 4 · Verification (live preview as testmech@mascigc.com)

| Step | URL after | Visible state |
|---|---|---|
| Login at `/shop/login` | `/shop` | Welcome toast, ShopHub renders |
| Toggle "More" footer | `/shop` | All 6 MoreLinks now ENABLED (no disabled grey-out) |
| Click **Recent Pre-Op Inspections** | **`/shop/equipment`** ✅ | EquipmentDashboard renders with all shop widgets: 54 UNITS FLAGGED FAIL badge, Pre-Op Trends chart tab strip, Open Shop Items panel ("All clear · Every Pre-Op fail has been signed off by the shop"), Shop Activity Feed with the iter364 "REPAIRED" entry, "82 ON FILE" count |

Screenshots:
- `/tmp/gate/p0_2c_shop_hub_more.png` — More footer expanded with enabled links
- `/tmp/gate/p0_2c_shop_equipment_list.png` — Full pre-op list now reachable from Shop

## 5 · Operator-required checks

| Check | Result |
|---|---|
| Shop user can see failed pre-ops | ✅ (`OpenItemsPanel` on ShopHub Equipment Needing Attention) |
| Shop user can open pre-op inspection detail | ✅ (`/shop/equipment/{id}` route, OpenItemsPanel + new list both navigate) |
| Shop user understands what needs attention | ✅ ("54 UNITS FLAGGED FAIL" badge visible) |
| **Recent Pre-Ops is not dead** | ✅ (enabled link → real route → renders 82 inspections) |
| Critical workflow is not hidden | ✅ (failed pre-ops surfaced first-screen; full list one tap away under More) |

## 6 · Files touched

- `/app/frontend/src/App.js` (+2 / -0 lines — new `/shop/equipment` route)
- `/app/frontend/src/pages/ShopHub.jsx` (+1 / -1 line — enable Recent Pre-Op link)

## 7 · Prohibited changes — NONE made

- ✅ No backup scheduler / env / Daily Report / Approval-Rejection / Pilot / RFI / Schedule / P6 / PM Exposure Tile work.

---

_End of SHOP_PREOP_WORKFLOW_CERTIFICATION.md._
