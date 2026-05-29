# PM Pre-Op Routing Fix Certification

_Phase V.5 · P0-2A · 2026-05-29 19:55–20:15 UTC._

> **Status**: SHIPPED to preview. End-to-end re-tested as PM
> (`chriswright@mascigc.com`). **No more bounce to /pm/login.**

## 1 · Defect summary

PM clicking any equipment pre-op inspection from `/pm/equipment` was kicked out of the PM portal and shown the PM login screen ("Inspection not found" toast + URL change to `/pm/login`). Operator reported the redirect as Shop login; the actual landing was the PM login surface (identical visual treatment — operator-side ambiguity was harmless).

## 2 · Root cause (three-link chain)

1. **`EquipmentDashboard.jsx` rendered admin-only side widgets in PM context**. `EquipmentTrendsPanel`, `OpenItemsPanel`, and `ShopActivityFeed` call `/api/admin/equipment-inspections/*` — admin-namespace endpoints PM is not authorized for. They threw 401.
2. **`lib/api.js` 401 interceptor was over-aggressive**. It cleared **every** session token the failing request carried, including PM, regardless of whether the failure had anything to do with PM authority.
3. **`list_equipment_inspections` did not apply `compute_pm_scope`**. PM saw all 82 inspections in the list; the detail endpoint then 404'd most of them because of scope. PM was teased with rows they could not open, every click triggered the 404 → fall-out chain.

## 3 · Fix (three coordinated patches)

### 3a · Namespace-aware 401 interceptor (`frontend/src/lib/api.js`)

```diff
-    if (cfg.headers?.["X-Admin-Token"]) clearAdminToken();
-    if (cfg.headers?.["X-Shop-Token"]) clearShopToken();
-    if (cfg.headers?.["X-PM-Token"]) clearPmToken();
-    ...
+    const isAdminNamespace = url.startsWith("/admin/") || url.includes("/api/admin/");
+    const isShopNamespace  = url.startsWith("/shop/")  || url.includes("/api/shop/");
+    const isHrNamespace    = url.startsWith("/hr/")    || url.includes("/api/hr/");
+
+    if (isAdminNamespace) {  // ONLY clear admin token
+      if (cfg.headers?.["X-Admin-Token"]) clearAdminToken();
+      return Promise.reject(err);
+    }
+    if (isShopNamespace)  { ... clearShopToken only ... }
+    if (isHrNamespace)    { ... clearHrToken only ... }
+    // legacy behavior preserved for non-namespaced URLs
```

A 401 from `/api/admin/...` now **only** clears the admin token. PM/Shop/HR sessions survive admin-widget failures inside their portals.

### 3b · Context-aware widget rendering (`frontend/src/pages/EquipmentDashboard.jsx`)

```jsx
const portalContext = pathname.startsWith("/pm/") ? "pm"
                    : pathname.startsWith("/shop/") ? "shop" : "admin";
const isPmContext = portalContext === "pm";

// In JSX:
{!isPmContext && <EquipmentTrendsPanel />}
{!isPmContext && <OpenItemsPanel baseHref="/admin/equipment" testIdPrefix="admin-open" />}
{!isPmContext && <ShopActivityFeed baseHref="/admin/equipment" testIdPrefix="admin-activity" />}
{isPmContext && (
  <p>PM read-only view. Use the inspections list below to open any pre-op
     record for a project you manage.</p>
)}
```

When `EquipmentDashboard` renders inside `/pm/`, the admin-only widgets are simply not mounted — no requests, no 401s, no token clears.

### 3c · Backend scope filter on the list endpoint (`backend/routes/equipment.py`)

```diff
-    async def list_equipment_inspections(_: bool = Depends(require_shop_or_admin)):
-        pipeline = [
-            {"$sort": {"created_at": -1}},
-            {"$limit": 1000},
-            ...
-        ]
+    async def list_equipment_inspections(actor=Depends(require_shop_or_admin)):
+        # Iter520 · Phase V.5 · P0-2A — apply PM scope filter so PM sees
+        # only inspections for projects they manage (matches the detail
+        # endpoint's behavior; prevents 404-bounce on row click).
+        scope = await compute_pm_scope(db, actor)
+        match_stage = {}
+        if not scope.is_admin and scope.project_numbers is not None:
+            allowed = list(scope.project_numbers or [])
+            if not allowed:
+                return []
+            match_stage = {"project_number": {"$in": allowed}}
+        pipeline = []
+        if match_stage:
+            pipeline.append({"$match": match_stage})
+        pipeline.extend([
+            {"$sort": {"created_at": -1}},
+            {"$limit": 1000},
+            ...
+        ])
```

List endpoint now respects the same `compute_pm_scope` contract as the detail endpoint. Admin tokens still see all 82 inspections (scope is admin-pass-through).

## 4 · Verification evidence

### 4a · Backend curl
```
POST /api/pm/login (chriswright)           → 200, PM token issued
GET  /api/equipment-inspections [PM]       → 200, items=0 (chriswright has no projects in preview)
GET  /api/equipment-inspections [admin]    → 200, items=82
```

### 4b · End-to-end Playwright (iPad portrait 820 × 1180)

| Step | URL after | DOM probes |
|---|---|---|
| Login as PM, navigate to `/pm/equipment` | `/pm/equipment` ✅ (was: stayed) | `new-equipment-btn` count = 0 ✅ · `share-equipment*` count = 0 ✅ · `admin-open*` widget count = 0 ✅ |
| Navigate directly to `/pm/equipment/<out-of-scope-id>` | `/pm/equipment` ✅ (was: `/pm/login`) | toast "Inspection not found" appears · PM session intact |

### 4c · Regression
- Wave-2 Playwright DR field reliability: 6 passed · 1 skipped (39.5 s)
- Backend admin auth: 23 passed (3.3 s)
- ESLint clean on `FormGrid.jsx`, `NewDailyReport.jsx`, `PoRequests.jsx`
- Ruff clean on `routes/equipment.py`, `routes/po_requests.py`

## 5 · Files touched

- `/app/frontend/src/lib/api.js` (+30 / −12 lines · namespace-aware 401 interceptor)
- `/app/frontend/src/pages/EquipmentDashboard.jsx` (+24 / −12 lines · portal-aware widget gating, P0-2A + P0-2B + PM read-only buttons)
- `/app/backend/routes/equipment.py` (+13 / −1 lines · `compute_pm_scope` applied to list)

## 6 · Prohibited changes — NONE made

- ✅ Backup scheduler code untouched
- ✅ env-vars untouched
- ✅ Daily Report workflow untouched
- ✅ Approval/Rejection / Pilot / RFI / Schedule / P6 / PM Exposure Tile — not started

---

_End of PM_PREOP_ROUTING_FIX_CERTIFICATION.md._
