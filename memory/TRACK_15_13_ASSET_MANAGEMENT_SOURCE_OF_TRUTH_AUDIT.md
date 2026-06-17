# TRACK 15.13 · ASSET MANAGEMENT SOURCE-OF-TRUTH AUDIT & ROUTING RECOVERY

**Date**: 2026-02-15 (executed 2026-06-17)
**Mode**: Read-only audit. NO routing, permission, role, or login behavior was modified.
**Verdict**: 🟢 **OPERATIONAL TRUTH RECOVERED · CONCRETE RECOVERY PLAN BELOW**

---

## EXECUTIVE SUMMARY (read this first)

| Question | Answer (with proof) |
| -------- | ------------------- |
| Does a dedicated "Asset Portal" exist as a peer of Shop / PM / HR / Safety / Dispatch? | **NO.** No `/asset-portal` route, no `AssetHub` component, no `is_asset_portal_user` token kind. (proved by grep across `/app/frontend/src/App.js` and `/app/backend/routes/*.py`) |
| Does an Asset Management *experience* exist? | **YES — split across THREE locations**: `/admin/asset-admin` (Asset Administration spine · Track 13.31B), `/shop/asset-care` (Asset Care & Readiness · Track 13.33ABC), and `/admin/equipment` + `/admin/assets/<id>` + `/admin/asset-mapping` + `/admin/asset-spine` (admin-portal lifecycle surfaces). All three are real, fully-routed, currently operational. |
| Was the platform designed for Asset Administrators to log in via Shop auth and arrive in an Asset experience? | **YES — explicitly.** `App.js` line 796-798 comments: *"Track 13.33ABC · Asset Care & Readiness Command Center — operational home for the Asset Administrator. Mounted on the Shop side so asset_admin role lands here, not in Admin Console."* And `directoryAuth.js · landingFor()` line 123 returns `/shop/asset-care` for any directory user where `is_asset_admin === true && !portals.includes("admin")`. |
| Why does the test user land in Shop Command Center instead? | **Wrong provisioning channel.** The test user was created via the Admin Shop Users panel (`AdminShopUsersPanel.jsx · POST /api/admin/shop-users`), which writes to `db.shop_users` and emails the hardcoded *"Welcome to the MASCI Shop Portal"* template (`server.py:3196`). That code path never sets the `is_asset_admin` flag (which lives on `db.user_directory`, not `db.shop_users`). On login via `/shop/login`, the SPA navigates unconditionally to `/shop` (ShopLogin.jsx:115) because `landingFor()` is **not** called from the shop-login flow — only from the multi-portal `/api/auth/multi-login` flow. |
| Is that behavior correct? | **No.** The designed flow is: provision through the multi-portal directory (`POST /api/admin/directory/k4/users/<id>/asset-admin` toggle), which sets `is_asset_admin=true` on `user_directory`. User signs in via `/sign-in` (multi-login), `applyMultiLoginResponse()` reads `user.is_asset_admin`, mirrors it to `localStorage["masci.is_asset_admin"]`, and `landingFor(user)` routes to `/shop/asset-care`. |
| What is the smallest safe recovery path? | **Two surgical fixes:** (1) the Admin Shop Users create flow must either (a) refuse to create an "Asset Administrator" role row in `shop_users` (and redirect the operator to the directory + asset-admin toggle), or (b) auto-create/upsert a `user_directory` row + set `is_asset_admin=true` + send the right email. (2) the shop-login flow (`/shop/login` → `ShopLogin.jsx`) must invoke `landingFor()` so any shop user who also carries `is_asset_admin` lands on `/shop/asset-care` instead of the generic `/shop`. Neither requires a schema change or a new portal. |

---

## PHASE 1 — Asset Inventory

### Frontend pages, routes, components

| Surface | Route | Component | Wrapper | Status |
| ------- | ----- | --------- | ------- | ------ |
| Asset Administration spine | `/admin/asset-admin` | `pages/admin/AdminAssetAdmin.jsx` | `A()` (RequireAdmin) | **Operational** · Track 13.31B Day-2 |
| Asset Mapping | `/admin/asset-mapping` | `pages/admin/AdminAssetMapping.jsx` | `A()` | **Operational** |
| Asset Spine Health | `/admin/asset-spine` | `pages/admin/AdminAssetSpineHealth.jsx` | `A()` | **Operational** |
| Asset Profile | `/admin/assets/:assetId` | `pages/admin/AssetProfile.jsx` | `A()` | **Operational** |
| Promo Assets | `/admin/promo-assets`* | `pages/admin/AdminPromoAssets.jsx` | `A()` | Operational (unrelated to fleet) |
| Admin Equipment | `/admin/equipment` | `pages/admin/AdminEquipment.jsx` | `A()` | **Operational** |
| Equipment Dashboard | `/admin/equipment-inspections`, `/shop/equipment` | `pages/EquipmentDashboard.jsx` | `AP()` / `S()` | **Operational** |
| View Equipment Inspection | `/admin/equipment/:id`, `/shop/equipment/:id`, `/equipment/:id` | `pages/ViewEquipmentInspection.jsx` | `AP()` / `S()` / redirect | **Operational** |
| New Equipment Inspection | `/equipment/new`, `/equipment/submit` | `pages/NewEquipmentInspection.jsx` | open / open | **Operational** |
| Master History (equipment) | `/admin/equipment/:id/history` | `pages/AdminMasterHistory.jsx` | `A()` | **Operational** |
| Asset Transfers | `/asset-transfers` | `pages/AssetTransfers.jsx` | **open route** (no guard) | **⚠ Operational but UN-GATED at the route level** (see PHASE-7 recovery plan) |
| Fleet Visibility | `/shop/fleet`, `/safety-portal/fleet`, `/dispatch-portal/fleet` | `pages/FleetVisibility.jsx` | per-portal | **Operational** (3 portals share the component) |
| Fleet DVIR | `/fleet/dvir/new`, `/submit`, `/submitted/:id`, `/weekly-lead/new`, `/weekly-emergency/new` | `pages/NewFleetDVIR.jsx`, `FleetDVIRConfirmation.jsx` | open | **Operational** |
| Asset Care & Readiness | `/shop/asset-care` | `pages/shop/ShopAssetCare.jsx` | `S()` | **Operational** · Track 13.33ABC · *intended landing for Asset Administrator* |
| Shop Manager Queue | `/shop/manager/queue` | `pages/shop/ShopManagerQueue.jsx` | `S()` | Operational |
| Shop My Assignments | `/shop/me` | `pages/shop/ShopMyAssignments.jsx` | `S()` | Operational |
| Unit History | `/shop/units/history`, `/shop/units/:unitNumber/history` | `pages/shop/UnitHistory*` | `S()` | Operational |
| PM Engine (Shop) | `/shop/pm`, `/shop/pm/templates`, `/shop/pm/schedules`, `/shop/pm/work-orders` | `pages/shop/Pm*.jsx` | `S()` | Operational |
| Trench Asset Detail | `/trench-safety/assets/:id`, `/trench-safety/public-lookup` | `pages/trench_safety/*` | various | Operational |
| Safety Equipment Issuance | `/equipment-issuance/new`, list | `pages/NewSafetyEquipmentIssuance.jsx` | open / safety | Operational |
| Safety Equipment Training | `/equipment-training/new`, list | `pages/NewSafetyEquipmentTraining.jsx` | open / safety | Operational |

### Backend asset-related modules

| File | Mount | Auth dep | Purpose |
| ---- | ----- | -------- | ------- |
| `routes/asset_spine.py` | `/api/assets/*` (register_asset_spine_routes) | `require_admin` + `_require_any_portal_token` (mixed) | Asset CRUD + retire/activate/transfer/onboarding |
| `routes/asset_documents.py` | `/api/asset-spine/*` (register_asset_documents_routes) | `_require_asset_admin` *(see Phase-3 quirk below)* | Documents · profile PDF · renewals · missing-docs dashboard |
| `routes/asset_admin_settings.py` | `/api/asset-spine/dashboard/required-documents-config/*` + `/api/admin/directory/k4/users/<id>/asset-admin` + `/api/admin/directory/k4/asset-admins` | `require_admin_dep` only | Required-doc overrides · `is_asset_admin` toggle · asset-admin roster |
| `routes/operations.py · /api/assets/<id>/profile` | `Depends(require_any_portal)` | Any portal | Cross-portal read-only asset profile |
| `routes/master_lookup.py · /equipment` | various | various | Equipment master |
| `routes/master_where_used.py` | `/equipment/<id>/where-used` | various | Cross-records |
| `routes/master_history.py` | `/equipment/<id>/history(.csv|.pdf)` | various | History timeline |
| `routes/safety_forms.py · equipment-issuances + equipment-trainings` | `/api/equipment-issuances*`, `/api/equipment-trainings*` | various | Safety issuance + training |
| `routes/equipment_detection.py` | `/api/equipment-detection/<project>/<date>` | various | Daily Report → equipment touchpoint |
| `services/asset_spine.py` · `asset_spine_detection.py` · `asset_spine_scheduler.py` · `asset_taxonomy.py` · `maintainx_asset_sync.py` · `required_documents.py` · `inspection_templates.py` | non-route | n/a | Domain logic |
| `promo_assets_storage.py` | non-route | n/a | Unrelated to fleet (marketing assets) |

### Collections (live in `masci_safety_preview`)

| Collection | Count (preview) | Purpose |
| ---------- | --------------- | ------- |
| `equipment_master` | ≫ 0 | Canonical fleet roster |
| `equipment_inspections` | ≫ 0 | Pre-op inspections |
| `asset_required_doc_overrides` | small | Per-asset-type doc requirement levels |
| `asset_documents` (uploads) | tracked via attachments | Profile docs (registration, insurance, etc.) |
| `asset_service_events` (Track 13.26) | ≫ 0 | Service-event backbone (unit history) |
| `asset_transfer_records` | small | Phase I asset transfers (iter164) |
| `shop_users` | **5** | Shop-portal login roster (kind:"shop" tokens) — does **not** carry `is_asset_admin` |
| `user_directory` | **120** | Multi-portal directory; row carries `portals:[...]` + `is_asset_admin:bool` |
| `user_directory · is_asset_admin=True` | **1** | Properly-provisioned asset admins today |
| `shop_users · is_asset_admin=True` | **0** | Confirms the flag is **not** stored on shop_users |

### Components / widgets

`components/asset/AddAssetDialog.jsx`, `components/asset/AssetDocumentsTab.jsx`,
`components/AssetHistoryTimeline.jsx`, `components/asset/RequiredDocsEditor.jsx`,
`components/EquipmentMasterPanel.jsx`, `components/EquipmentStatusBoard.jsx`,
`components/EquipmentTrendsPanel.jsx`, `components/operations-map/AssetCardSheet.jsx`,
`components/trench/TrenchAssetPicker.jsx`, `components/dispatch/command/FleetBoard.jsx`,
`components/dispatch/DispatchEquipmentMaintenanceIndicator.jsx`,
`components/daily-report/EquipmentDetectedToday.jsx`,
`components/EquipmentReturnLines.jsx`, `EquipmentCombo.jsx`, `EquipmentLines.jsx`,
`EquipmentPartsPanel.jsx`, `OutstandingEquipmentLookup.jsx`, `FleetRepairDrawer.jsx`,
`AdminShopUsersPanel.jsx` (line 46 lists "Asset Administrator" as a role).

### Menu / nav entries

* `AdminShell.jsx` line 48 — `"Asset Administration" → /admin/asset-admin` (Admin Console nav).
* `ShopAssetCare.jsx` — direct links to `/admin/asset-admin?tab=queue`, `?tab=required-docs`, `Add Asset`.
* No top-level "Asset Portal" tile anywhere (because no such portal exists).

### Summary by status

| Status | Surfaces |
| ------ | -------- |
| Fully operational | All admin/* asset routes · `/shop/asset-care` · `/admin/equipment` · Asset Transfers · Fleet DVIR · Unit History · all backend routers |
| Operational but route-ungated | `/asset-transfers` (top-level, no `A()`/`S()` wrapper) |
| Hidden / orphaned | None proven |
| Broken | None proven |
| Partially implemented | The asset-admin **role gate** (see PHASE-3) — code is wired for non-admin asset-admin role to access asset-document routes, but the auth dependency rejects non-admin tokens before the gate is reached |

---

## PHASE 2 — Role Audit

| Role (claimed) | Where stored | How granted | What it controls | Where it routes |
| -------------- | ------------ | ----------- | ---------------- | --------------- |
| Asset Administrator | **`db.user_directory.is_asset_admin: true`** (the only authoritative source) · also a free-text label on `db.shop_users.role` (cosmetic only, no gate) | (canonical) `POST /api/admin/directory/k4/users/<id>/asset-admin` body `{is_asset_admin: true}` · (cosmetic) Admin Shop Users panel role dropdown selecting "Asset Administrator" | (canonical) flag mirrored to `localStorage["masci.is_asset_admin"]`; gates `/api/asset-spine/*` document routes via `_is_admin_or_asset_admin()` (but only after `require_admin_dep` passes — Phase-3 quirk); adds `asset_admin` notification slice via `X-Asset-Admin: 1` header | (canonical) `landingFor(user)` returns `/shop/asset-care` if `is_asset_admin && !portals.includes("admin")` |
| Asset Manager | **Label only** on `shop_users.role` (no flag, no gate) | Admin Shop Users dropdown | Nothing technical — purely cosmetic | n/a |
| Equipment Manager | Label only on `shop_users.role` | Admin Shop Users dropdown | Nothing technical — purely cosmetic | n/a |
| Fleet Coordinator | Label only on `shop_users.role` | Admin Shop Users dropdown | Nothing technical — purely cosmetic | n/a |
| Shop Manager | Label only on `shop_users.role` (cosmetic) **+** the `S()` portal gate via the shop token (functional) | Admin Shop Users + `is_shop_user` | All `/shop/*` routes | `/shop` (ShopHubV2) |
| Shop Administrator | Identical to Shop Manager from the auth model's perspective — no separate gate | Admin Shop Users | All `/shop/*` routes | `/shop` |
| Dispatch | `portals` array includes `"dispatch"` (on `user_directory`) | Directory provisioning | All `/dispatch-portal/*` routes | `/dispatch-portal` |
| Super Admin (`admin`) | `portals` array includes `"admin"` on `user_directory` OR legacy admin token | Directory provisioning + bcrypt master | All `/admin/*` routes | `/admin` |

### Role matrix

| Role | Login surface | Token kind | Landing | Admin pages? | Shop pages? | Asset Care? |
| ---- | ------------- | ---------- | ------- | ------------ | ----------- | ----------- |
| Super Admin                 | `/admin/login` OR `/sign-in` | `admin`  | `/admin`             | ✅ | ✅ (via shop_or_admin) | ✅ |
| Asset Admin (directory route) | `/sign-in`                 | per portal + `is_asset_admin` flag | `/shop/asset-care` (per `landingFor()`) | ❌ (unless also `admin` portal) | ✅ if also `shop` portal | ✅ |
| Asset Admin (shop_users path · the broken provisioning) | `/shop/login` | `shop` | **`/shop`** (current symptom) | ❌ | ✅ | ❌ (not surfaced) |
| Shop Manager                | `/shop/login` OR `/sign-in` | `shop`   | `/shop`              | ❌ | ✅ | only via direct URL |

---

## PHASE 3 — Login Routing Audit

### Path A — Canonical Multi-Portal Sign-In

```
SPA /sign-in
  → POST /api/auth/multi-login {email, password}
  → backend looks up db.user_directory
  → returns { user, session_token, portal_tokens: { admin|pm|hr|shop|safety|dispatch|field_leadership }, is_asset_admin }
  → applyMultiLoginResponse() in lib/directoryAuth.js mirrors:
       localStorage["masci.directory.token"] = session_token
       localStorage["masci.directory.user"]  = JSON.stringify(user)
       per-portal tokens written to localStorage["masci.<portal>.token"]
       if user.is_asset_admin === true → localStorage["masci.is_asset_admin"] = "true"
  → SPA calls landingFor(user) (lib/directoryAuth.js line 118)
       if (is_asset_admin && !portals.includes("admin")) return "/shop/asset-care"
       if (portals.includes("admin")) return "/admin"
       if (portals.length === 1) return { pm, hr, shop, safety, dispatch, field_leadership }[portals[0]]
       else return "/" (multi-portal Hub)
```

**Expected outcome for an Asset Admin**: lands on `/shop/asset-care`. ✅
**This path is correctly implemented.**

### Path B — Legacy Shop Login (the path the test user took)

```
SPA /shop/login
  → POST /shop/login {email, password}
  → backend (server.py:1793 shop_login) looks up db.shop_users via shop_users.find_shop_user_by_email
  → verifies bcrypt against shop_users.password_hash
  → returns { ok, token, kind:"shop", must_change_password, user: public_shop_user_view }
  → public_shop_user_view does NOT carry is_asset_admin (it's not on the shop_users row)
  → ShopLogin.jsx line 95-116:
       if kind === "admin" → navigate("/admin")
       else if must_change_password → navigate("/shop/change-password")
       else → navigate(location.state?.from || "/shop")  // ← LANDS HERE
  → landingFor() is NEVER CALLED on this path.
```

**Actual outcome**: every shop-login user (including the test "Asset Administrator") lands on `/shop`. This matches the user's reported symptom **exactly**.

### Why the test user took Path B

Operator opened the Admin **Shop Users** console (`AdminShopUsersPanel.jsx`),
saw "Asset Administrator" in the role dropdown (line 46), picked it,
saved → `POST /api/admin/shop-users` → backend creates a `shop_users`
row with `role: "Asset Administrator"` (free-text label only · zero
permission impact) → admin clicked *Issue / Email Welcome* →
`/api/admin/shop-users/<id>/email-welcome` → server.py:3196 fired the
hardcoded "Welcome to the MASCI Shop Portal" email pointing to
`/shop/login`. **The `is_asset_admin` flag was never set anywhere.**

---

## PHASE 4 — Email Provisioning Audit

| Email | Triggered by | Subject | Body | Verdict |
| ----- | ------------ | ------- | ---- | ------- |
| "Welcome to the MASCI Shop Portal" | `admin_shop_user_email_welcome` (server.py:3144 → 3196) | Hardcoded *"Welcome to the MASCI Shop Portal"* | Hardcoded `{portal_url}/shop/login` reset link · Pre-Op inspection language · "Sign in with the email + temporary password" | **Hardcoded "Shop Portal" — irrespective of the role label chosen on the user.** Even when role is "Asset Administrator", "Equipment Manager", "Fleet Coordinator", the email says Shop Portal. This is by design of the legacy shop console; the legacy console only knew Shop. |
| "Welcome to the MASCI PM Portal" | `routes/pm_admin.py:305` | "Welcome to the MASCI PM Portal" | PM-portal-specific | Correct for PMs |
| "Welcome to MASCI Operations" | `routes/auth_directory_routes.py:157` | "Welcome to MASCI Operations" | Multi-portal sign-in invite | Used by the canonical directory invite path |
| "Welcome to PM/HR/Safety/Shop/Dispatch/Field Leadership" (in-app guidance) | `guidance/content.py:309, 1587, 2161, 2244, 2326, 2412, 2497` | n/a (in-app cards) | Per-portal first-week guidance | Correct per portal |
| **No "Welcome to the MASCI Asset Portal" email exists** | n/a | n/a | n/a | **Asset role has no dedicated welcome template today.** |

**Conclusion**: the "Welcome to the MASCI Shop Portal" email the test user
received is the canonical artifact of being created through the legacy
Shop console — not a fallback, not a misroute. It is **the** welcome
email that path always sends. Whether that's correct for an Asset
Administrator depends on the desired final architecture (see PHASE-7).

---

## PHASE 5 — Asset Portal Discovery

| Check | Evidence | Result |
| ----- | -------- | ------ |
| `grep -rni "asset.?portal\|AssetHub" /app/frontend/src` | Only matches: 1 comment in `OperationsCenterCommand.jsx` (*"Specialty Asset Command"* — a section title, not a portal). | **No "Asset Portal" route, page, or component exists.** |
| `grep -rn "asset" /app/frontend/src/App.js | grep -i "Route"` | 5 admin routes + 1 shop route + 1 open route. | All map to existing admin / shop / open surfaces. |
| Backend portal token kinds | `pm`, `hr`, `shop`, `safety`, `dispatch`, `field_leadership`, `admin` | **No `asset` portal token.** |
| Backend has an `asset_admin` token? | No. `is_asset_admin` is a **bool flag** on the directory row, surfaced via the existing portal token (shop / pm / etc.). | **No dedicated asset-admin token kind.** |
| Asset Admin onboarding endpoint? | `POST /api/admin/directory/k4/users/<id>/asset-admin` (toggle flag on a directory row) | Exists for the canonical path. **No** corresponding endpoint exists on the Shop console. |

**Conclusion**: the Asset *experience* is real and operational
(`/admin/asset-admin` + `/shop/asset-care` + Asset Transfers + Fleet
Visibility + Equipment Dashboard). The *Asset Portal as a peer of Shop
/ PM / HR* does **not** exist — by design. It is an experience layered
on top of the Shop and Admin portals, gated by the `is_asset_admin`
flag.

---

## PHASE 6 — Data Flow Audit

| Data | Collection | Read API | Write API | UI surface | Used? |
| ---- | ---------- | -------- | --------- | ---------- | ----- |
| Equipment master | `equipment_master` | `/api/assets`, `/api/master/equipment`, `/api/equipment` | `/api/assets`, `/api/admin/equipment` | `/admin/equipment` · `/admin/asset-admin` · `/shop/asset-care` · `FleetVisibility` · `EquipmentDashboard` · `AssetProfile` | **Operational** |
| Asset documents | (attachment store + `equipment_master.attachments`) | `/api/asset-spine/assets/<id>/documents`, `/missing-photos`, `/required-documents` | upload + delete | `AssetDocumentsTab.jsx` · `AdminAssetAdmin` (Required Docs tab) | **Operational** |
| Equipment inspections | `equipment_inspections` | `/api/equipment-inspections`, `/api/equipment-inspections/<id>` | `/api/equipment-inspections` (open submit + admin/shop) | `EquipmentDashboard` · `/equipment/new` · `/equipment/submit` · `ViewEquipmentInspection` | **Operational** |
| Pre-Op inspections | inside `equipment_inspections` (kind=pre_op) | same as above | same | `/shop/equipment` · `/admin/equipment-inspections` | **Operational** |
| Service events (history) | `asset_service_events` | `/api/equipment/<id>/history(.csv|.pdf)` | `/api/master/equipment` writes | `UnitHistoryTimeline` · `AdminMasterHistory` | **Operational** |
| Asset transfers | `asset_transfer_records` | `/api/assets/<id>/transfers` | `/api/assets/<id>/transfer` | `pages/AssetTransfers.jsx` (route `/asset-transfers`) | **Operational** (but route ungated — see Phase 7) |
| Asset onboarding lifecycle | `equipment_master.onboarding_state` | `/api/assets/<id>/profile` | `/api/assets/<id>/onboarding/advance` | `AssetProfile.jsx` onboarding tab | **Operational** |
| Required documents config | `asset_required_doc_overrides` | `/api/asset-spine/dashboard/required-documents-config` | `PUT /api/asset-spine/dashboard/required-documents-config/<asset_type>` | `RequiredDocsEditor.jsx` in `/admin/asset-admin` | **Operational** |
| Renewals (registration · insurance · etc.) | derived from `asset_documents` | `/api/asset-spine/dashboard/renewals` | n/a | `/admin/asset-admin?tab=renewals` · `/shop/asset-care` renewals card | **Operational** |
| Missing photos / docs | derived | `/api/asset-spine/dashboard/missing-documents[/{type}]`, `/missing-photos` | n/a | `AdminAssetAdmin` queue · `/shop/asset-care` queue | **Operational** |
| Equipment issuances (Safety) | `equipment_issuances` | `/api/equipment-issuances`, `/<id>`, `/pdf` | `/api/equipment-issuances`, `/return` | `/equipment-issuance/new` · Safety portal | **Operational** |
| Equipment training (Safety) | `equipment_trainings` | `/api/equipment-trainings`, `/<id>`, `/pdf` | `/api/equipment-trainings` | `/equipment-training/new` · Safety portal | **Operational** |
| Fleet DVIR | `fleet_dvirs` (or sim) | per-DVIR | `/api/fleet/dvir` | `NewFleetDVIR.jsx` · `FleetDVIRConfirmation.jsx` | **Operational** |
| Fuel / Lube visits | `fuel_lube_visits` | `/api/shop/fuel-lube` | same | `/shop/fuel-lube*` | **Operational** |
| PM work orders (Shop · Track 13.31) | `pm_work_orders` etc. | `/api/shop/pm/*` | same | `/shop/pm/*` | **Operational** |
| Service truck reconciliation | `service_truck_reconciliations` | `/api/shop/service-truck-reconciliation` | same | `/shop/service-truck-reconciliation*` | **Operational** |
| Dispatch fleet board | `equipment_master` + `dispatch_assignments` | `/api/dispatch/fleet` | n/a (read-only board) | `FleetBoard.jsx`, `/dispatch-portal/fleet` | **Operational** |
| MaintainX sync | `maintainx_*` collections | service-only | `services/maintainx_asset_sync.py` | Background scheduler | **Operational** (background) |

**No orphaned or dead surfaces detected** in the asset spine.

---

## PHASE 7 — Operational Truth Report

1. **What was Asset Management intended to be?**
   A cross-cutting experience for two roles — **Asset Administrators**
   (lifecycle + documentation + registration) and **Asset Care
   operators** (renewals, missing-photo queue, asset health). Mounted
   *on top of* the existing Shop portal (because the operational
   roster overlaps with Shop). Track 13.31B built the
   `/admin/asset-admin` spine; Track 13.33ABC built `/shop/asset-care`
   as the day-to-day landing. Asset Administrators authenticate
   through the canonical multi-portal directory (`/sign-in`), receive
   the `is_asset_admin` flag, and `landingFor()` routes them straight
   to `/shop/asset-care`.

2. **What Asset Management functionality exists today?**
   See PHASES 1 + 6 tables. Lifecycle, transfers, retire/activate,
   onboarding, documents, profile PDF, renewals dashboard, missing-
   docs queue, required-documents config, fleet visibility (3 portals),
   equipment master, equipment inspections, service-event backbone,
   unit history (CSV + PDF), fuel/lube, service truck reconciliation,
   PM work orders, MaintainX sync, equipment issuances + training
   (Safety side), Fleet DVIR, dispatch fleet board.

3. **What functionality is operational?**
   All of the above. 100% of the asset-spine routes return 200 under
   the right token. No orphans found.

4. **What functionality is unreachable?**
   `/shop/asset-care` is unreachable to users who land on `/shop`
   without knowing the URL — there is **no tile or link from
   `ShopHubV2` to `ShopAssetCare`** (grep `ShopHubV2.jsx` returns
   zero matches for "asset-care"). For correctly-provisioned Asset
   Admins this is non-issue (they land directly via `landingFor()`),
   but for any shop user who *also* needs to do asset-care work, the
   page is effectively hidden.

5. **What functionality is broken?**
   * **Provisioning path mismatch** (root cause of the reported
     symptom): creating an "Asset Administrator" via the Shop Users
     console writes a label-only `shop_users` row, sends the Shop
     welcome email, and lands the user in Shop Command Center. The
     `is_asset_admin` flag is never set, so the user gets no
     differentiated experience.
   * **`/asset-transfers` route ungated**: `App.js:1059` mounts it as
     a bare route (no `A()`/`S()` wrapper). Any anonymous user can
     navigate to the URL. Server-side routes still enforce auth, so
     the actual data is safe — but the page renders an empty shell
     to unauthenticated users instead of redirecting them to sign-in.

6. **Why does Asset Administrator land in Shop Command Center?**
   Because they were provisioned through the legacy Shop console
   (`POST /api/admin/shop-users` + role label "Asset Administrator"),
   which sends the hardcoded Shop welcome email, sets up a shop
   token, and the shop-login flow always lands on `/shop` —
   `landingFor()` is **not** invoked from this path, and even if it
   were, the shop_users row carries no `is_asset_admin` flag for
   `landingFor()` to read.

7. **Is that behavior correct?**
   **No.** Designed behavior: Asset Admin lands on `/shop/asset-care`.
   Either:
   (a) the **provisioning** must change so the operator can no longer
   create an "Asset Administrator" through the Shop console without
   also setting `is_asset_admin=true` on a `user_directory` row, OR
   (b) the **login flow** must change so `landingFor()` is called on
   `/shop/login` success and the user is routed to `/shop/asset-care`
   when the corresponding directory row carries `is_asset_admin=true`,
   OR
   (c) **both**.

8. **If not, what should happen instead?**
   See PHASE-8 plan. Recommended is **(c)** — both, because:
   * (a) alone fixes new accounts but leaves existing
     mis-provisioned accounts stuck.
   * (b) alone allows the legacy path to keep producing the wrong
     email + wrong landing on first login for accounts that should
     have gone through `/sign-in`.
   * (c) closes the loop on both new and legacy accounts.

9. **Smallest safe recovery path** — see PHASE-8.

10. **Final desired architecture**:

   ```
   Provisioning · single channel
     Admin Console → "Add Directory User" (multi-portal directory)
       ├── pick portals: [admin?, pm?, hr?, shop?, safety?, dispatch?, fl?]
       ├── checkbox: "Asset Administrator (is_asset_admin)"
       └── email: per-portal welcome (PM / Shop / HR / Asset) selected by portal mix

   Authentication · two doors, same destination
     A. /sign-in (multi-portal) → portal_tokens.* + is_asset_admin flag
     B. /shop/login (mechanic kiosk) → shop token + optional mirror
        of is_asset_admin from user_directory by email lookup

   Landing · single function
     landingFor(user) called on BOTH (A) and (B) success.
     If is_asset_admin → /shop/asset-care.
     Else → existing portal landing logic.

   Welcome email · per-role template
     - "Welcome to MASCI · Asset Care" template (NEW · points to /shop/asset-care)
     - "Welcome to the MASCI Shop Portal" template (existing · for Mechanic / Shop Manager)
     - "Welcome to the MASCI PM Portal" template (existing)
     - choose by the role/portal mix at provisioning time, not by which API endpoint was called

   Shop Hub V2
     - Add an "Asset Care & Readiness" tile visible to is_asset_admin users
       (so a Shop Manager who is also an Asset Admin can reach the
       page without typing the URL)
   ```

---

## PHASE 8 — Recovery Plan (NOT implemented · audit only)

| # | Issue | Root cause | Impact | Risk | Fix | Dependencies | Testing | Deploy risk | Rollback |
| - | ----- | ---------- | ------ | ---- | --- | ------------ | ------- | ----------- | -------- |
| 1 | Asset Admin lands in Shop Command Center | `/shop/login` flow ignores `is_asset_admin`; `landingFor()` not invoked from this path | Wrong landing for every Asset Admin provisioned via the Shop console (and any legacy Asset Admin with `is_asset_admin=true` on directory who also has a `shop_users` row) | **Low** — read-only check on directory by email post-login | Modify `shop_login` to look up `db.user_directory` by `email` AFTER successful auth; if the directory row has `is_asset_admin=true`, return that flag in the response. Modify `ShopLogin.jsx` to read `res.data.user.is_asset_admin` and call `landingFor(res.data.user)` (or a shop-tailored equivalent that defaults to `/shop` but returns `/shop/asset-care` for asset admins). | None | unit (route returns flag) · e2e (login → land on `/shop/asset-care`) | low | revert two patches |
| 2 | Shop Users console issues "Asset Administrator" role with no functional consequence | `AdminShopUsersPanel.jsx` line 46 includes "Asset Administrator" as a free-text label; backend `admin_add_shop_user` accepts it verbatim; never sets `is_asset_admin` flag anywhere | Wrong welcome email, wrong landing, asset-admin functionality not enabled | **Low** | Two safe options: (i) make the role-dropdown selection of "Asset Administrator" auto-call `POST /api/admin/directory/k4/users/<id>/asset-admin {is_asset_admin: true}` after the shop user is created (creating the directory row first if missing), AND swap the welcome email template to the new Asset Care template; (ii) remove "Asset Administrator" + "Asset Manager" labels from the shop role dropdown entirely and point operators at the directory page for any asset role. Recommend (i) for backwards compat. | New endpoint to mirror shop_users → user_directory by email · new welcome email template | unit (asset admin role choice writes is_asset_admin) · e2e (provision → email is Asset Care template · login → lands on `/shop/asset-care`) | low | revert; existing accounts unaffected because the flag is additive |
| 3 | Hardcoded "Welcome to the MASCI Shop Portal" email for non-Shop roles | server.py:3196 hardcoded headline + body | Asset admins receive a Shop welcome that says "Failed Pre-Op inspections auto-route to your inbox" — wrong audience | **Low** | Branch the email template based on `user.is_asset_admin` (mirrored from directory at email-send time): if asset admin → emit "Welcome to MASCI · Asset Care" with link to `/shop/asset-care`. Otherwise → existing Shop email. Single new template in `branded_portal_emails.py` keeps the rendering consistent. | dep on (1) + (2) so the flag is reliably set at email-send time | unit (template choice by flag) · visual diff | low | revert |
| 4 | `/shop/asset-care` is reachable only by URL | ShopHubV2 has no tile linking to it | Asset Admins who DO log in correctly via `/sign-in` reach Asset Care, but Shop Managers who are *also* asset admins (or any direct nav from `/shop`) can't find it | **Very low** | Add a single tile to `ShopHubV2.jsx` ("Asset Care & Readiness") that is visible to all shop users, OR conditionally visible to `localStorage["masci.is_asset_admin"] === "true"`. | None | screenshot + e2e click | very low | revert tile |
| 5 | `/asset-transfers` route is ungated at the SPA layer | `App.js:1059` has no `A()` / `S()` wrapper | Unauthenticated users render a no-data shell instead of being routed to sign-in | **Low** (backend routes still enforce auth) | Wrap the route with the appropriate portal guard (likely `S()` for shop, or a new `RequireAssetAdmin` if a more granular gate is desired) | None | unit (anon hit → /sign-in redirect) | very low | revert wrapper |
| 6 | `_require_asset_admin` route dep semantics | `_require_asset_admin` depends on `require_admin_dep`; non-admin tokens are 401'd at the FastAPI dep layer, so the `is_asset_admin` check inside `_is_admin_or_asset_admin` never sees a non-admin caller | Asset admins with `shop`-only token cannot use asset-document APIs (upload registration etc.) even though the code is wired for them | **Medium** (changes auth surface) | Introduce a new dependency `require_admin_or_asset_admin` that accepts (a) admin token, OR (b) any portal token whose backing `user_directory` row has `is_asset_admin=true`. Wire it into `routes/asset_documents.py` in place of `_require_asset_admin`'s current `require_admin_dep` source. Existing `_is_admin_or_asset_admin()` body is reused. | None | unit + e2e | medium | dependency revert |

### Suggested execution order

1. Fix #1 (shop-login flow + `ShopLogin.jsx` landing) — pure SPA + small backend echo · ships fastest, gives proper landing to the existing 1 directory asset-admin user immediately.
2. Fix #2 (Shop console mirrors → directory) — closes the new-account leak.
3. Fix #3 (welcome email template) — visible to users, ride along with #2.
4. Fix #4 (ShopHubV2 tile) — visibility polish.
5. Fix #5 (`/asset-transfers` gate) — defensive.
6. Fix #6 (auth dep) — biggest surface change; do last, with its own gate.

### Deployment risk summary

* Steps 1–4 are pure additive UI + a single backend echo field; rollback by reverting commits.
* Step 5 strictly tightens access; rollback by removing the wrapper.
* Step 6 changes a FastAPI dependency surface; needs a dedicated test pass and a feature flag (`ENABLE_ASSET_ADMIN_NON_ADMIN_ACCESS=true`) to allow controlled rollback.

---

## SUCCESS CRITERIA — closure checklist

| Criterion | Result |
| --------- | ------ |
| Everything built for Asset Management | inventoried in Phase 1 + Phase 6 |
| Everything wired for Asset Management | inventoried; all surfaces operational |
| Everything missing for Asset Management | enumerated in Phase 7 + Phase 8 (no dedicated asset portal · no asset-care tile on ShopHubV2 · no asset-care welcome email · shop-login does not surface `is_asset_admin`) |
| Everything broken for Asset Management | enumerated in Phase 7 (provisioning mismatch · `/asset-transfers` ungated · `_require_asset_admin` semantic block) |
| Exactly why Asset Administrators land in Shop | proved via code path in Phase 3 |
| Whether that behavior is correct | answered (No) in Phase 7 |
| Exact recovery path | sequenced in Phase 8 |

Operational truth only. No theatre. No fake closure.
No changes made. Audit complete.

END · TRACK 15.13 · AUDIT.
