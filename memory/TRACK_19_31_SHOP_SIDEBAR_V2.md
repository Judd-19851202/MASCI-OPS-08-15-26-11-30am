# TRACK 19.31 · SHOP PORTAL SIDEBAR V2

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Six Pillars Aggregate: 57/60 · Production Strong**
**Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md`

## Charter
Add Sidebar V2 to the Shop portal so Shop users get the same domain-grouped, muscle-memory-consistent navigation pattern already used by HR, Safety, Admin, PM, and Dispatch. First feature track under the Track 19.30 Production Readiness Quality Gate.

## What shipped

### 1 · `frontend/src/components/shop/sidebar/domainMap.js`
6 base domains + 1 conditional Asset Administrator domain + footer rail:
- **Recovery & Attention** (red stripe · Radar icon) — Shop Command Center · OOS · Open Defects · Units with Defects · RTS Pending · Acknowledged Defects.
- **Work Assignments** (amber stripe · ClipboardList) — Manager Queue · My Assignments · Active Recovery.
- **Fleet & Equipment** (blue stripe · Truck) — Fleet Visibility · Equipment Pre-Ops · Unit History.
- **Preventive Maintenance** (violet stripe · Calendar) — PM Dashboard · PM Schedules · PM Templates · Work Orders.
- **Service & Support** (teal stripe · Fuel) — New Fuel/Lube Visit · Fuel/Lube Records · New Truck Reconciliation · Reconciliation Records · Trench Safety Repairs.
- **Asset Care** (slate stripe · Boxes) — Asset Care & Readiness workspace.
- **Asset Administrator** (cyan stripe · KeyRound) — Records Intake · Records Queue · Bulk Historical Intake. Emitted only when `is_asset_admin=true` OR admin token present.
- **Footer rail (pinned):** My Tasks · Guidance.

All routes verified to exist in `App.js` — **zero new backend or frontend routes introduced**.

### 2 · `frontend/src/components/shop/sidebar/ShopSideNavV2.jsx`
Mirrors PM SideNavV2 shape exactly. Adds Shop-specific visibility rule (Asset Administrator lane conditional). Feature-flag resolver (`isShopSidebarV2Enabled`) supports:
- `?shopSidebarV2=0` query param (sticky · escape hatch)
- `masci.shop.sidebar.v2` localStorage
- `REACT_APP_SHOP_SIDEBAR_V2` env
- **Default: ON**

### 3 · `frontend/src/pages/ShopHubV2.jsx` integration
Passes `sideNav={isShopSidebarV2Enabled() ? <ShopSideNavV2 /> : undefined}` to `PortalShell`. Tile-grid HubV2 body preserved intact. Asset-admin visibility polish from Track 19.28 unchanged.

## Verification (smoke-tested live)

Playwright smoke against `https://backup-forensics.preview.emergentagent.com/shop` with real super-admin credentials (`jaymn.judd@mascigc.com`):

| Check | Result |
|---|---|
| `[data-testid="shop-side-nav-v2"]` present | ✅ |
| All 6 base domains render | ✅ |
| Asset Administrator lane visible when `is_asset_admin=true` | ✅ |
| Asset Administrator lane hidden when `is_asset_admin=false` | ✅ (negative test passed) |
| Desktop (1920 × 900) | ✅ |
| Mobile (390 × 844) | ✅ |
| Tile-grid HubV2 body preserved | ✅ (visible in screenshot) |
| Frontend lint | ✅ Clean |
| No dead nav items | ✅ Every route in App.js |

Screenshot artifact: `/tmp/shop_v2_desktop_assetadmin.png`.

## Rollback path
- **Feature flag off:** append `?shopSidebarV2=0` to any Shop URL, or `localStorage.setItem('masci.shop.sidebar.v2', '0')` — sidebar reverts to no-sidebar HubV2 (pre-19.31 state).
- **Full rollback:** revert 3 files (`domainMap.js`, `ShopSideNavV2.jsx`, `ShopHubV2.jsx` sideNav prop line).
- **Legacy hub still at `/shop/hub_legacy`** (untouched).
