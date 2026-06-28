# TRACK 18.12 · Mission Control Access + Layout Repair

**Status:** ✅ GO · P0 access defect closed · P1 layout repair shipped · Regression-locked
**Date:** 2026-02-10

---

## Root cause

The bug surfaced for the **fourth time** because Mission Control + the SubNav + the Right Rail + the Search + the Command Queue tabs **hardcoded user-facing routes** with the `/admin/transportation/...` prefix. The Track 18.09C amendment made `pages/transportation/TransportationApp.jsx` the single source of truth shared between two doorways (`/admin/transportation/*` admin-strict + `/transportation-operations/*` dispatch-accessible), but the **chrome inside that shared component** still emitted admin-prefixed links. A dispatch-authenticated user clicking any Mission Control card / sub-nav link / search result / right-rail row was silently navigated to `/admin/transportation/...` — where the admin-strict gate (`A(...)`) denied them.

The previous tracks fixed **redirects** (path-relative — Track 18.09C) and **governance boundaries** (CI linter — Track 18.10), but **not the chrome's outbound href emitter**. Track 18.12 closes that gap.

---

## Broken paths found (26)

See `MISSION_CONTROL_CLICK_PATH_AUDIT.md` for the full per-click matrix. Summary by component:

| Component | Hardcoded admin links | Fix |
|---|---:|---|
| `MissionControl.jsx` — 8 operator-question cards | 14 (actionHref + drillHref × 8 minus the Card 6 RecentActivity which now takes `prefix`) | All switched to `${prefix}/...` |
| `_shared.jsx::TransportationSubNav` | 1 NavLink builder (covers 11 sub-nav links) | `${prefix}/${item.to}` |
| `_views.jsx::TopCleanupOpportunityCard` | 1 | `${prefix}/intelligence/cleanup` |
| `_command_queue.jsx::CommandQueueCenter` | 1 NavLink builder (3 sub-tabs) | `${prefix}/command-queue/${t.to}` |
| `TransportationSearch.jsx::onPickResult` | 1 navigation function | `_rewriteToPrefix(route, prefix)` before navigating |
| `TransportationWorkspaceShell.jsx::RelatedRow + AuditRow` | 2 row primitives | shared `_rewriteToPrefix` helper |

## Access fixes made

1. **New `useTxPathPrefix()` hook** exported from `_shared.jsx`. Returns `/transportation-operations` when the URL starts with that prefix, otherwise `/admin/transportation`.
2. **`useTxLocation()` updated** to strip *either* prefix (was admin-only).
3. **Six files updated** to consume `useTxPathPrefix()` and emit prefix-aware hrefs (MissionControl, _shared, _views, _command_queue, TransportationSearch, TransportationWorkspaceShell).
4. **Backend-emitted routes are rewritten** at render time via `_rewriteToPrefix(target, prefix)` (right-rail + search) — any `/admin/transportation/...` value from the API gets converted to the active prefix before navigation.

## Mission Control layout

New **Workspace Actions strip** between Mission Brief and the operator-question cards:

- 8 consistent chips (Dispatch / Drivers / Carriers / Fleet / Orientation / Compliance / Live Operations / Cleanup).
- One CTA per chip · icon + label + short hint.
- Responsive grid: 2 cols (mobile) → 4 cols (tablet) → 8 cols (desktop).
- Premium hover (`hover:border-slate-900 hover:shadow-sm`).
- R8-compliant (each chip is its own `<Link>`).
- ODS-aligned with the rest of the platform.

See `MISSION_CONTROL_LAYOUT_REPAIR_REPORT.md`.

## Role-aware visibility

* Dispatch users · all Mission Control workspace strip chips visible · all 8 operator-question cards visible · sub-nav fully visible · search rail visible · right rail visible.
* Restricted operational data feeds (HR sync, cleanup signals, etc.) fall through `TxOpsRestrictedData` inline — Transportation-branded restricted state, **never** Admin Console denial copy.
* Admin users · everything visible · admin side nav also rendered via `PortalShell`.

## Dispatch user walkthrough (verified live)

| Step | Path |
|---|---|
| Login | `/sign-in` → multi-portal | ✅ |
| Landing | `/transportation-operations` → Mission Control renders | ✅ |
| Workspace strip · Dispatch | → `/transportation-operations/dispatch` (DispatchBridgeWorkspace) | ✅ |
| Workspace strip · Drivers | → `/transportation-operations/drivers` | ✅ |
| Workspace strip · Carriers | → `/transportation-operations/carriers` | ✅ |
| Workspace strip · Fleet | → `/transportation-operations/trucks` | ✅ |
| Workspace strip · Orientation | → `/transportation-operations/orientation` | ✅ |
| Workspace strip · Compliance | → `/transportation-operations/compliance` | ✅ |
| Workspace strip · Live Operations | → `/transportation-operations/live-operations` | ✅ |
| Workspace strip · Cleanup | → `/transportation-operations/intelligence/cleanup` | ✅ |
| Card 1 · "Open Fleet" | → `/transportation-operations/trucks` | ✅ |
| Card 4 · "Open Dispatch" | → `/transportation-operations/dispatch` | ✅ |
| Card 6 · "Open audit timeline" | → `/transportation-operations/audit` | ✅ |
| Sub-nav · Drivers | → `/transportation-operations/drivers` | ✅ |
| Search result | → `/transportation-operations/...` (rewritten from backend admin route) | ✅ |
| Right Rail · Related record | → `/transportation-operations/...` | ✅ |

**Every click stays inside `/transportation-operations`. Zero Admin Console denial. Zero `/admin/transportation` bounce.**

## Admin walkthrough

* `/admin/transportation` → Mission Control renders under admin shell. ✅
* Same Mission Control card clicks land at `/admin/transportation/...`. ✅
* Admin side nav visible. ✅
* Admin-only record detail pages remain admin-strict. ✅
* `/transportation-operations` also works for admin (TX gate accepts admin token). ✅

## Search + Right Rail

* Search results that return backend-emitted `/admin/transportation/...` routes are rewritten to the active prefix in `onPickResult`. ✅
* Right Rail `RelatedRow` and `AuditRow` rewrite backend-emitted admin routes via the shared `_rewriteToPrefix` helper. ✅

## Restricted states

* Inline `TxOpsRestricted` + `TxOpsRestrictedData` already use Transportation-branded copy. ✅
* No "Admin Console" / "Admin Portal" / "Back to Dispatch Portal" copy in any `pages/transportation/*` or `components/transportation/*` file. **Enforced by `test_21_no_forbidden_admin_console_copy_in_tx_ui`.**

## Security / RBAC

* No auth changes (dispatch + admin gates intact).
* No RBAC changes.
* `X-Admin-Token` plumbing preserved.
* Admin-only endpoints remain admin-strict.
* Driver magic-link routes untouched.
* Dispatch portal routes untouched.

## Routes preserved

* `/admin/transportation/*` admin-strict ✅
* `/transportation-operations/*` TX-gated ✅
* `/dispatch-portal/*` ✅
* `/dr/*` driver token ✅
* `/api/admin/transportation/*` API prefix ✅

## Dispatch / Driver preservation

* `/dispatch-portal/board`, `/dispatch-portal/command`, `/dispatch-portal/map`, `/dispatch-portal/haul-ledger` — untouched.
* Driver magic-link routes untouched.

## Tests

* `backend/tests/test_track_18_12_mission_control_access_layout.py` — **36 lock assertions** (35 directive-mandated + 1 anchor).
* Track 18.00 Phase B mission-control test (`test_08_dispatch_card_is_link_only`) updated to accept the prefix-aware variant.
* Track 18 family green.

## Live smoke

* Hub renders. ✅
* `/sign-in` renders. ✅
* `/transportation-operations` renders Mission Control + Workspace Strip + 8 cards. ✅
* Every workspace strip chip click stays in `/transportation-operations/...`. ✅
* `/admin/transportation` renders for admin. ✅
* `/dispatch-portal/board` renders. ✅
* No console errors. ✅
* Mobile (390 px) + tablet (768 px) + desktop (1920 px) layouts verified. ✅

## Deployment gate

Track 18.12 wired into `scripts/deployment_gate.py` REGRESSION_FILES.

## Risks

None blocking. Minor: future backend search composers that emit admin-prefixed routes are automatically rewritten — but if a new composer emits routes outside `/admin/transportation/` (e.g., a typo), the rewrite is a no-op. Mitigation: the Track 18.10 governance linter + Track 18.12 chrome contract together prevent operational chrome from ever hardcoding the admin prefix.

## Deferrals

None.

## Final certification

🟢 **GO. Mission Control is usable. The layout belongs.**

Transportation Operations is **executable**.
Administration is **governance**.
Six Pillars upheld.

A dispatch user can now click every visible Mission Control control without being routed into Admin Console denial — verified live by `testing_agent_v3_fork`.
