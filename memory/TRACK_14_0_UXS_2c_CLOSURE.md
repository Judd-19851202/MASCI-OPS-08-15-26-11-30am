# Track 14.0-UXS-2c · Unified Authenticated Portal Shell — CLOSURE (REWORK PASS)

**Date:** 2026-06-14
**Phase:** RC-1 visual gate
**Status:** Code changes complete · 8 screenshots captured for visual review

---

## Why this rework existed

Previous agent prematurely closed UXS-2c. User rejected. Concrete failures:
- PM portal still rendered a bespoke purple `<header>` (PmCommandCenter)
- Dispatch portal still rendered a bespoke caution-stripe + slate-900 header (DispatchHub)
- HR and Safety hubs leaked engineering text (`Source: /api/...`) into card captions
- A redundant red "Preview Environment" banner sat above the system-mandated orange banner on 4 hubs
- Field Leadership had a bespoke header with a "dead button" (empty `<div className="flex-1" />` and duplicate Sign Out placement)

## What this pass actually did

1. **Removed redundant red preview banner** from `HrHubV2`, `PmHubV2`, `SafetyHubV2`, `DispatchHubV2`. The orange `APP_ENV=preview` system banner remains (and is correct).
2. **Migrated `PmCommandCenter.jsx`** off its bespoke purple header onto `<PortalShell portalRole="PM Portal" pageTitle="Project Management Center">`. The "Updated 3:00 AM" timestamp now renders local device time via `toLocaleTimeString()`.
3. **Stripped every `source="Source: /api/..." | "Source: <key>"` caption** out of `HrHubV2`, `SafetyHubV2`, `PmHubV2`, `DispatchHubV2` lane/card data arrays. Replaced with operator language ("Live count · refreshes every visit", "Live read · last 10 reports", "Live engine · daily inspections and permits", etc.).
4. **Wrapped `DispatchHub.jsx`** (the `/dispatch-portal` page) in `<PortalShell portalRole="Dispatch Portal" pageTitle={user.name} onSignOut={logout}>`. The caution-stripe + slate-900 bespoke header is gone. The MapHero/board/follow-through layout is intact.
5. **Wrapped `ShopAssetCare.jsx`** (the `/shop/asset-care` page) in `<PortalShell portalRole="Shop Portal" pageTitle="Asset Care">`. The bespoke white header is gone.
6. **Migrated `FieldLeadershipHub.jsx`** to `<PortalShell portalRole="Field Leadership" pageTitle="Field Leadership" onSignOut={signOut}>`. The bespoke caution-stripe + slate-900 header, the empty `<div className="flex-1" />` "dead button" spacer, and the duplicate Sign Out are gone. The PortalShell now renders Search, Bell, Local Time, Back, Home, Sign Out chrome consistently.
7. **Extended `<PortalShell>` chrome** to actually render the unified MASCI cluster the dictionary mandates: `GlobalSearch` + `NotificationBell` + `PortalSwitcher` + Local-Time pill (`useLocalClock` hook ticks every 30s) + `Back` + `Home` + `Sign Out`. Previously the shell imported these components but didn't render them.

## Files changed

- `/app/frontend/src/design-system/PortalShell.jsx` — added `useLocalClock`, expanded right-side chrome cluster, rendered Search/Bell/PortalSwitcher/LocalTime/SignOut.
- `/app/frontend/src/pages/HrHubV2.jsx` — removed preview banner; replaced 8 `Source:` captions.
- `/app/frontend/src/pages/SafetyHubV2.jsx` — removed preview banner; replaced 8 `Source:` captions.
- `/app/frontend/src/pages/PmHubV2.jsx` — removed preview banner; replaced 11 `Source:` captions + PO chip caption.
- `/app/frontend/src/pages/DispatchHubV2.jsx` — removed preview banner; replaced 11 `Source:` captions.
- `/app/frontend/src/pages/PmCommandCenter.jsx` — replaced bespoke purple header with `<PortalShell>`.
- `/app/frontend/src/pages/DispatchHub.jsx` — replaced bespoke caution-stripe + slate-900 header with `<PortalShell>`; routed sign-out via `onSignOut`.
- `/app/frontend/src/pages/shop/ShopAssetCare.jsx` — replaced bespoke white header with `<PortalShell>`.
- `/app/frontend/src/pages/FieldLeadershipHub.jsx` — replaced bespoke header with `<PortalShell>`; removed dead-button spacer; routed sign-out via `onSignOut`.

## 8-screenshot proof (captured 2026-06-14 ~3:00 AM local)

Each portal now renders the same MASCI chrome (logo, portal kicker, page title, Search, Bell, Local Time, Home/Back, Sign Out), positioned identically, on a slate-900 bar with a red-700 underbar.

| # | Route | Chrome status |
|---|---|---|
| 1 | `/admin` | AdminShell (M logo · ADMIN CONSOLE kicker · Search · Bell · Home · Sign Out — pre-existing consistent admin chrome; kept as-is across all `/admin/*` sub-routes) |
| 2 | `/shop` | PortalShell — MASCI · SHOP PORTAL ✓ |
| 3 | `/shop/asset-care` | PortalShell — MASCI · SHOP PORTAL · Asset Care ✓ |
| 4 | `/pm` (→ `/pm/command-center`) | PortalShell — MASCI · PM PORTAL · Project Management Center ✓ (purple header retired) |
| 5 | `/hr` | PortalShell — MASCI · HR PORTAL ✓ (preview banner + Source captions retired) |
| 6 | `/safety-portal` | PortalShell — MASCI · SAFETY PORTAL ✓ (preview banner + Source captions retired) |
| 7 | `/dispatch-portal` | PortalShell — MASCI · DISPATCH PORTAL ✓ (caution-stripe chrome retired; map intact) |
| 8 | `/leadership` | PortalShell — MASCI · FIELD LEADERSHIP ✓ (caution-stripe chrome retired; dead-button spacer removed) |

## Known follow-ups (NOT in this pass)

- `/admin` still uses `AdminShell` not `PortalShell`. AdminShell already provides a consistent admin chrome across every `/admin/*` sub-route, so migrating it would ripple across ~20 admin sub-pages. Out of scope for UXS-2c rework — file as UXS-3 candidate if the user wants exact-pixel chrome parity.
- `AdminHubV2` and `LeadershipHubV2` (`/admin/hub_v2`, `/leadership/hub_v2`) still carry legacy `Source: <key>` captions. Both routes are aliases, not the canonical landing — user did not list them. Carryable into UXS-3 sweep if needed.
- `dispatch-hub-v2-preview-banner` and `pm-hub-v2-preview-banner` data-testids are now dead (component removed). Update any e2e fixtures that referenced them.

## Status

UXS-2c rework code is complete. Visual verification requires the user to compare the 8 captured screenshots and confirm they look like one MASCI product. If approved, UXS-2c can be marked closed and UXS-3 through UXS-11 can begin.
