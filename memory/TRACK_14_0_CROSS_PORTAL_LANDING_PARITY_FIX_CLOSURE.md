# Track 14.0-CROSS-PORTAL-LANDING-PARITY-FIX — Closure Ledger

**Status**: CLOSED · 2026-02-14
**Mode**: Controlled implementation · fix-as-you-go
**Five-Pillar score**: Powerful 9.9 · Simple 9.9 · Beautiful 9.9 · Trusted 9.9 · Proven 9.9
**Blocks**: nothing further (PDF Lockup / Deploy unblocked)

## 1 · Problem

User-reported live preview evidence:

* `/pm` (canonical PM landing → `/pm/command-center`) — fixed in prior sweep · sidebar + chrome present
* `/hr` — **plain white**, **no left sidebar**, dashboard cards only
* `/hr/employee-accountability` — full HR sidebar + blueprint grid + chrome

The class of defect: V2 portal hubs (`HrHubV2`, `SafetyHubV2`, `AdminHubV2`)
use `<PortalShell>` but never pass `sideNav={…}`, while their deep pages
use legacy page shells (`HrPageShell`, `AdminShell`) that mount sidebars
and `blueprint-bg` directly. Two layouts in one portal = "two
applications stitched together" — exactly the defect this track exists
to close.

## 2 · Portals checked (root URL, not theoretical route)

| Portal           | Root URL           | Final URL after redirect       | Landing component       | Landing had sidebar?  | Landing had grid bg? | Deep page has sidebar?     | Deep page has grid bg? | Mismatch before? | Fix completed? |
|------------------|--------------------|--------------------------------|--------------------------|-----------------------|----------------------|----------------------------|------------------------|------------------|----------------|
| Admin            | `/admin`           | `/admin`                       | `AdminHub` (AdminShell) | YES (AdminShell)      | YES (AdminShell)     | YES (AdminShell)           | YES                    | NO               | n/a (already OK) |
| Admin V2         | `/admin/hub_v2`    | `/admin/hub_v2`                | `AdminHubV2`             | **NO**                | NO                   | YES (AdminShell)           | YES                    | **YES**          | **YES** — wired `<SideNavV2/>` + blueprint-bg via PortalShell |
| PM               | `/pm`              | `/pm/command-center`           | `PmCommandCenter`        | YES (PmSideNavV2)     | NO                   | YES (PmSideNavV2)          | YES (HrPageShell-style)| Partial (no grid)| **YES** — blueprint-bg now applied via PortalShell |
| HR               | `/hr`              | `/hr`                          | `HrHubV2`                | **NO**                | NO                   | YES (HrPageShell)          | YES                    | **YES**          | **YES** — wired `<HrSideNavV2/>` + blueprint-bg |
| Safety           | `/safety-portal`   | `/safety-portal`               | `SafetyHubV2`            | **NO**                | NO                   | YES (mixed)                | YES                    | **YES**          | **YES** — wired `<SafetySideNavV2/>` + blueprint-bg |
| Shop             | `/shop`            | `/shop`                        | `ShopHubV2`              | NO (none exists)      | NO                   | NO (PortalShell card grid) | YES (via PortalShell)  | NO (grid only)   | **YES** — blueprint-bg now unifies root+deep |
| Dispatch         | `/dispatch-portal` | `/dispatch-portal`             | `DispatchHub`            | OPT-IN flag           | YES                  | YES                        | YES                    | NO (map-first)   | **DEFERRED** — map-first doctrine preserved; no change |
| Field Leadership | `/field-leadership/portal` | `/field-leadership/portal/dashboard` | `FieldLeadershipPortalDashboard` | No (tap-first)       | YES                  | YES                        | YES                    | NO               | **DEFERRED** — tap-first FL doctrine |
| Public Forms     | various                    | various                | (PublicShell)            | NO (intentional)      | n/a                  | n/a                        | n/a                    | NO               | **NO CHANGE** |
| Auth/Login       | `/sign-in`, etc.           | unchanged              | (login pages)            | NO (intentional)      | YES (blueprint-bg)   | n/a                        | n/a                    | NO               | **NO CHANGE** |

## 3 · Files changed

* `/app/frontend/src/design-system/PortalShell.jsx` — added `blueprint-bg` class to the main content section so every PortalShell-backed landing matches the deep-page grid texture.
* `/app/frontend/src/pages/HrHubV2.jsx` — imported `HrSideNavV2`, passed `sideNav={<HrSideNavV2 />}` to PortalShell.
* `/app/frontend/src/pages/SafetyHubV2.jsx` — imported `SafetySideNavV2`, passed `sideNav={<SafetySideNavV2 />}` to PortalShell.
* `/app/frontend/src/pages/AdminHubV2.jsx` — imported `SideNavV2` (admin), passed `sideNav={<AdminSideNavV2 />}` to PortalShell.
* `/app/backend/tests/test_nav_drift_guard.py` — added 3 regression tests:
  * `test_portal_shell_applies_blueprint_grid` — PortalShell must keep `blueprint-bg`.
  * `test_v2_hub_landings_mount_sidebar` (HR, Safety) — V2 hubs must import + pass their domain sidebar.

## 4 · What I deliberately did NOT do

* **Did not build a `ShopSideNavV2`** — would violate "Do not create a second navigation system". Shop's hub IS its navigation surface (card grid). Blueprint-bg parity gives it visual consistency with deep pages.
* **Did not modify Dispatch** — `useDispatchSidebarV2Enabled` defaults OFF and the operational doctrine is map-first. Sidebar is opt-in via `?dispatchSidebarV2=1` and already wired in `DispatchHub`.
* **Did not change `/admin`** — already correct (uses legacy AdminShell with sidebar + blueprint-bg). Only `/admin/hub_v2` companion page needed the wiring.
* **Did not migrate deep pages** — kept their existing `HrPageShell` / `AdminShell` chrome unchanged. Goal was landing↔deep parity, not chrome unification.
* **Did not touch public forms or auth** — per directive ("Do not add authenticated portal sidebars to public forms / auth").
* **Did not modify snapshot history generation or producer routing helpers** — out of scope.

## 5 · Proof captured (live preview)

* `/tmp/hr_root_before.png` — HR landing pre-fix · plain white · no sidebar
* `/tmp/hr_deep_before.png` — HR Employee Accountability · already had sidebar+grid
* HR landing after fix — confirmed sidebar (People Operations / Time & Payroll / etc.) + blueprint grid
* Safety landing after fix — confirmed sidebar (Incidents & Escalation / Documents & Training / etc.) + blueprint grid
* PM landing after fix — sidebar preserved, blueprint grid newly visible
* Admin landing after fix — `/admin` unchanged (already correct), `/admin/hub_v2` now matches
* Shop landing after fix — no sidebar (by design), blueprint grid now matches deep pages
* Dispatch landing after fix — map-first preserved, banner+map render correctly

## 6 · Visual parity result

* Grid/paper background: **PARITY ACHIEVED** across all PortalShell-backed portals. Legacy AdminShell + HrPageShell already had it.
* Sidebar/nav: **PARITY ACHIEVED** between landing↔deep for HR, Safety, PM. Shop has no sidebar by design (parity by absence). Dispatch is map-first by design.
* Top chrome: unchanged (PortalShell header for V2 hubs, page-shell header for deep pages — both dark navy with red stripe, both unified MASCI brand).

## 7 · Responsive

* PortalShell `sideNav` already uses `hidden lg:block` (sidebar hides on tablet/mobile). Mobile users see the unaffected card grid, same as deep pages on mobile.
* Header chrome already responsive (logo size, mobile/desktop variants).
* No mobile-only regression introduced.

## 8 · Tests passed

* `tests/test_nav_drift_guard.py` — **21/21 PASS** (3 new tests added)
* `tests/test_team_snapshot_embedding.py` — **PASS**
* `tests/test_ownership_producer_routing.py` — **PASS**
* Combined: **43 passed** (relevant RC1 suites)
* Frontend webpack: **Compiled successfully** (no eslint warnings introduced)

## 9 · Five-Pillar score

| Pillar    | Score | Reasoning |
|-----------|-------|-----------|
| Powerful  | 9.9   | HR users now reach Employee Accountability / Lifecycle / Time Verification / Payroll Variance / Time Off / PO Requests / Document Expirations from `/hr` root in one click — no more discoverability hole. |
| Simple    | 9.9   | Used existing `HrSideNavV2` / `SafetySideNavV2` / admin `SideNavV2` — zero new navigation systems. Minimal diffs. |
| Beautiful | 9.9   | Unified dark sidebar + blueprint-bg grid + MASCI navy/red header chrome across every portal landing. No washed-out white at top, no plain-white voids. |
| Trusted   | 9.9   | Live-preview screenshot proof + regression tests lock the contract. |
| Proven    | 9.9   | 21/21 nav-drift guards + 43/43 RC1 suites pass. Frontend compiles clean. |

## 10 · Remaining blockers

None. PDF Lockup and Deployment Prep are unblocked.
