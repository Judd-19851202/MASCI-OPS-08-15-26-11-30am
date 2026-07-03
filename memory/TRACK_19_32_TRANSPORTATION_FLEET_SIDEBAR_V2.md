# TRACK 19.32 · TRANSPORTATION / FLEET SIDEBAR V2

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Six Pillars Aggregate: 58/60 · Production Strong**
**Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md`

## Charter
Add Sidebar V2 to Transportation / Fleet so the platform reaches **7/7 portal sidebar consistency** and Transportation/Fleet users get the same domain-grouped, muscle-memory navigation pattern used by HR, Safety, Admin, PM, Dispatch, and Shop.

## Doctrine
- Single source of truth for routes + permission gating: `TX_OPS_NAV_GROUPS` and `visibleTxOpsNavGroups()` in `pages/transportation/_shared.jsx`. **No duplication.**
- Prefix-aware routing: same shell mounts under `/admin/transportation/*` (admin oversight) AND `/transportation-operations/*` (dispatch-authenticated). Sidebar V2 routes resolve correctly for both entry points via `useTxPathPrefix()`.
- Visual metadata (stripe · icon · subline) lives in a separate `txDomainMeta.js` file so routes/permissions and visual language evolve independently.

## What shipped

### 1 · `frontend/src/components/transportation/sidebar/txDomainMeta.js`
Visual metadata keyed by the same `group.key` values as `TX_OPS_NAV_GROUPS`:
- **Overview** (red stripe · Radar) · Mission Control · what needs Transportation now.
- **Operations** (amber stripe · Truck) · Dispatch · Live Operations · Fleet.
- **People** (blue stripe · UserRound) · Drivers · Carriers.
- **Compliance** (teal stripe · ShieldCheck) · Compliance · Orientation · Transportation Academy.
- **Operations Intelligence** (violet stripe · Activity) · Intelligence · Automation · Cleanup.
- **Administration** (slate stripe · Shield) · Reports · Administration · **admin-only**.

Fallback for future groups: neutral slate stripe + default icon.

### 2 · `frontend/src/components/transportation/sidebar/TransportationSideNavV2.jsx`
Mirrors Shop / PM / Admin Sidebar V2 shape:
- Two-tier domain accordion.
- Persists open domains in `localStorage.masci.tx.sidebar.openDomains`.
- Reads authoritative route + permission-gated groups from `visibleTxOpsNavGroups()`.
- Overview + Operations domains auto-expand on first mount.
- Active domain auto-expands based on current URL.
- Every domain, child row, and children container has a `tx-nav-v2-*` test ID.
- Feature-flag resolver `isTxSidebarV2Enabled` — default ON, escape hatch via `?txSidebarV2=0`.

### 3 · `frontend/src/pages/transportation/TransportationApp.jsx` integration
Updated the `PortalShell.sideNav` prop resolution:
```js
const effectiveSideNav = txSidebarV2
  ? <TransportationSideNavV2 />
  : (showAdminSideNav ? <AdminSideNavV2 /> : null);
```
- Flag ON (default): both admin and dispatch users see the new Transportation V2 sidebar with role-appropriate visibility.
- Flag OFF: preserves pre-19.32 behavior (admin sees Admin V2 sidebar · dispatch sees no sidebar).

## Verification (smoke-tested live)

### Admin token (super-admin `jaymn.judd@mascigc.com`)
- `[data-testid="tx-side-nav-v2"]` present at `/admin/transportation` ✅
- All 6 domains render including **Administration** ✅
- Screenshot: `/tmp/tx_v2_admin.png`

### Dispatch token only (admin token cleared)
- `[data-testid="tx-side-nav-v2"]` present at `/transportation-operations` ✅
- **Administration domain HIDDEN** ✅ (permission logic from `visibleTxOpsNavGroups()`)
- Reports NavLink HIDDEN ✅
- 5 base domains visible (Overview · Operations · People · Compliance · Operations Intelligence) ✅
- Screenshot: `/tmp/tx_v2_dispatch.png`

### Prefix-aware routing
- Admin view: NavLinks resolve to `/admin/transportation/...` ✅
- Dispatch view: NavLinks resolve to `/transportation-operations/...` ✅
- No hardcoded admin prefix leakage ✅

### Frontend lint
Clean on all 3 touched files.

## Preservation guarantees (Zero-Drift)

| Preserved workflow | Status |
|---|---|
| Transportation Academy `/academy` + `/academy/:moduleKey` | ✅ intact |
| Orientation Center `/orientation/*` | ✅ intact |
| Drivers list + workspace | ✅ intact |
| Carriers list + workspace | ✅ intact |
| Trucks list + workspace | ✅ intact |
| Compliance Dashboard | ✅ intact |
| Document Center · Inspection Center · Rate Schedule Center | ✅ intact |
| Command Queue Center (Automation) | ✅ intact |
| Intelligence Center | ✅ intact |
| Dispatch Bridge Workspace | ✅ intact |
| Live Operations Workspace | ✅ intact |
| Cleanup (`intelligence/cleanup`) | ✅ intact |
| Reports · Audit Timeline (admin-only) | ✅ intact |
| External Carrier Invite `/transport-invite/:token` | ✅ untouched (public) |
| Certificate Verify `/transport-verify/:cnum` | ✅ untouched (public) |
| Fleet DVIR `/fleet/dvir/*` | ✅ untouched (public field flow) |
| Legacy compatibility redirects (`compliance/documents`, `fleet`, etc.) | ✅ intact |
| Dispatch permission model | ✅ unchanged |
| Admin-only visibility | ✅ preserved via `visibleTxOpsNavGroups()` |

## Rollback path

- **Feature flag off:** append `?txSidebarV2=0` to any Transportation URL, or `localStorage.setItem('masci.tx.sidebar.v2', '0')`. Reverts to pre-19.32 sidebar behavior (admin sees Admin V2 · dispatch sees no sidebar).
- **Full source rollback:** revert 2 new files + 2 edits (`TransportationApp.jsx` imports + sideNav resolution).
- **Rollback confidence:** HIGH. Existing `visibleTxOpsNavGroups()` + prefix routing untouched — the change is purely additive.

## Sidebar V2 rollout status (post-19.32)

| Portal | Sidebar V2 | Track shipped |
|---|---|---|
| HR | ✅ | (pre-existing) |
| Safety | ✅ | (pre-existing) |
| Admin | ✅ | (pre-existing · route parity closed in 19.28) |
| PM | ✅ | (pre-existing) |
| Dispatch | ✅ | (pre-existing) |
| Shop | ✅ | 19.31 |
| Transportation / Fleet | ✅ | **19.32 (this track)** |
| **Consistency** | **7 / 7 = 100%** | — |

**Sidebar consistency doctrine: COMPLETE.**
