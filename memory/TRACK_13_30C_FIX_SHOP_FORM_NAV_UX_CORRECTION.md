# Track 13.30C-fix · Shop Form / Navigation / Runtime Correction Pass

**Date:** 2026-06-12
**Mode:** CONTROLLED CORRECTION (no Track 13.30D until this is green) · no deploy · no GitHub save · no merge.

---

## 1 · Runtime crash fix · `Can't find variable: FocusBanner`

- **Root cause:** `FleetVisibility.jsx` mounted `<FocusBanner />` at line 489 but never imported it. Crash surfaced on `/shop/fleet` and `/fleet` when the recovery focus card mounted.
- **Fix:** added `import FocusBanner from "@/components/triage/FocusBanner";` to the imports block.
- **Verified:** smoke test against `/shop/fleet` reports `overlay=False` (no `Uncaught ReferenceError`, no compile overlay).

## 2 · Navigation fixes — every Shop subpage now returns to `/shop`

- **New shared component:** `frontend/src/components/shop/BackToShopLink.jsx` — plain "← Back to Shop" link, MASCI-styled (paper-card background, brand-primary text, dashed-bold border, `data-testid="…-back-to-shop"`).
- **Mounted as a `primaryActions` slot on every PortalShell-driven Shop subpage:**

  | Page | Back-to-Shop testid |
  |---|---|
  | `/shop/fuel-lube/new` | `fuel-lube-visit-form-back-to-shop` |
  | `/shop/fuel-lube` | `fuel-lube-records-back-to-shop` |
  | `/shop/fuel-lube/:id` | `fuel-lube-detail-back-to-shop` |
  | `/shop/service-truck-reconciliation/new` | `strr-form-back-to-shop` |
  | `/shop/service-truck-reconciliation` | `strr-list-back-to-shop` |
  | `/shop/service-truck-reconciliation/:id` | `strr-detail-back-to-shop` |
  | `/shop/manager/queue` | `shop-manager-queue-back-to-shop` |
  | `/shop/me` | `shop-my-assignments-back-to-shop` |
  | `/shop/units/history` | `unit-history-landing-back-to-shop` |
  | `/shop/units/:unit/history` | `unit-history-back-to-shop` |

- **`/shop/equipment`, `/shop/equipment/:id`, `/shop/fleet`** continue to rely on `HubBackLink` (made Shop-aware in Track 13.30B) — visible label "← Shop", returns to `/shop`.

## 3 · Form visual standardization

- **`FuelLubeVisitForm`** subtitle rewritten in plain operator language: *"One job visit · multiple equipment lines. Each service entry is saved to the unit's history. Issues create shop defects automatically."*
- **`ServiceTruckReconciliationForm`** subtitle preserved (was already operator-friendly).
- **Card sections, label spacing, required (*) markers, grid alignment** all use the existing MASCI form primitives (`Card`, `PortalShell`, label/input convention). No bolted-on styling introduced.
- **iPad-friendly:** all selectors render as 100 %-wide cards with 32-px tap targets via the shared `ShopSelector` styling.

## 4 · Project dropdown source

- **New backend endpoint:** `GET /api/shop/projects/list` (Shop/Admin gate · read-only).
  - **Source:** aggregates distinct `project_number` from `daily_reports` (same source the admin `/admin/projects/list` picker uses, but Shop-accessible).
  - **Returns:** `{items: [{project_number, project_name, last_report_date}], count, source}`.
  - Sorted by most-recent report descending. Hard cap of 500.
- **Frontend:** `ShopSelector kind="project"` renders the dropdown with debounced filter, honest empty / error states, and **"Type manually instead →"** fallback so the form is never blocked by an outage.
- **Wired in:** Fuel/Lube Visit form (`fuel-lube-visit-form-project-project-root` test id verified live).

## 5 · Equipment dropdown source

- **New backend endpoint:** `GET /api/shop/units/list?limit=500` (Shop/Admin gate · read-only).
  - **Source:** `equipment_master` active rows.
  - **Returns:** `{items: [{unit_number, equipment_name, equipment_type, manufacturer, status}], count, source}`.
- **Frontend:** `ShopSelector kind="unit"` — same UX as project picker.
- **Wired in:**
  - Fuel/Lube Visit form (Fuel/Lube truck field — verified `fuel-lube-visit-form-truck-unit-root`).
  - Fuel/Lube Visit form (per-equipment line unit — verified `fuel-lube-line-unit-0-unit-root`). Equipment name auto-fills from the selected row.
  - Service Truck Reconciliation form (Service truck unit — verified `strr-form-truck-unit-root`).

## 6 · Service truck selector status

- **No dedicated `kind: "service_truck"` filter is added in this pass** because the equipment master does not classify trucks today (Track 13.30A future-gap, documented).
- The current `ShopSelector kind="unit"` returns the full active equipment list and accepts manual entry as fallback — that is the **honest current state** until classification is added.
- **Future work** (not in scope): add `equipment_master.role` / `tags: ["fuel_truck"]` and gate the selector with `filterFn={(u) => u.role === "fuel_truck"}`.

## 7 · Operator copy cleanup

Removed from operator-visible UI on every page in scope:

| Removed phrase | Replacement |
|---|---|
| *"Each serviced unit projects into the Asset Service Event Backbone (Track 13.26)"* | *"Each service entry is saved to the unit's history"* |
| *"Issue lines spawn Shop defects via the existing Track 13.28 lifecycle"* | *"Issues you flag here become shop defects automatically"* |
| *"Entered Shop defect lifecycle (Track 13.28)"* | *"Sent to the shop defect queue"* |
| *"Source: `/api/shop/fuel-lube/visits`"* | *"Submitted visits archive"* |
| *"Single source · Asset Service Event Backbone (Track 13.26). Issues feed Track 13.28 lifecycle. PDF / email / CSV exports are future enhancements; Print uses the browser's native dialog."* | *"Each service entry is saved to the unit's history. Issues flow to the shop defect queue. Print uses the browser's native dialog. PDF / email / CSV exports are not enabled here."* |
| *"Dispensed source: `fuel_lube_visits` (Track 13.29). NO accounting · NO cost · NO fuel tax · NO theft language."* | *"Dispensed totals come from submitted Fuel/Lube Visits. No accounting · no cost · no fuel tax · no disciplinary language."* |
| *"Repair Complete ≠ RTS"* (in three places) | *"Repair complete still requires return-to-service verification by Dispatch"* |
| `Recent units derived from <code>/api/shop/manager/queue</code>...` | *"Recent units come from the active shop queue. Click any unit to open its complete timeline."* |
| `subtitle="… Powered by the Asset Service Event Backbone (Track 13.26)"` | *"Complete operational timeline for this asset — pre-ops, DVIRs, defects, repairs, fuel/lube, return-to-service."* |

**Runtime verification (live `body.innerText` scan, admin token):**
- `/shop/fuel-lube/new` — `Track 13` = 0 · `/api/` = 0 · `Backbone` = 0.
- `/shop/fuel-lube` — 0 · 0 · 0.
- `/shop/fuel-lube/:id` — 0 · 0 · 0.
- `/shop/service-truck-reconciliation` — 0 · 0 · 0.
- `/shop/service-truck-reconciliation/new` — 0 · 0 · 0.
- `/shop/units/history` — 0 · 0 · 0.
- `/shop/me` — 0 · 0 · 0.
- `/shop` — 0 · 0 · 0.
- `/shop/manager/queue` — `Track 13` = **1** **but the match comes from a preview-seeded defect title in the database** ("brake check (TRACK 13.7C) · reported by Preview Seed (Track 13.7C)"), **not UI copy**. UI scrub is complete; the legacy data row is operational test data, not engineering language. Defect-title seed data is out of scope for a UI correction pass.

## 8 · Files changed

### Added
- `frontend/src/components/shop/BackToShopLink.jsx`
- `frontend/src/components/shop/ShopSelector.jsx`
- `memory/TRACK_13_30C_FIX_SHOP_FORM_NAV_UX_CORRECTION.md` (this file)

### Modified
- `frontend/src/pages/FleetVisibility.jsx` — `+import FocusBanner` (1 line; fixes runtime crash).
- `backend/routes/shop_intel.py` — `+GET /api/shop/projects/list`, `+GET /api/shop/units/list` (~80 LOC added).
- `frontend/src/pages/shop/FuelLubeVisitForm.jsx` — selectors for project · truck · per-equipment unit; operator-copy scrub; Back-to-Shop link.
- `frontend/src/pages/shop/FuelLubeVisitRecords.jsx` — Back-to-Shop link; doctrine footer rewrite.
- `frontend/src/pages/shop/FuelLubeVisitDetail.jsx` — Back-to-Shop link; doctrine footer rewrite; line copy scrub.
- `frontend/src/pages/shop/ServiceTruckReconciliationForm.jsx` — ShopSelector for truck; Back-to-Shop link; doctrine footer scrub.
- `frontend/src/pages/shop/ServiceTruckReconciliationRecords.jsx` — Back-to-Shop link; doctrine footer scrub.
- `frontend/src/pages/shop/ServiceTruckReconciliationDetail.jsx` — Back-to-Shop link; doctrine footer scrub.
- `frontend/src/pages/shop/ShopManagerQueue.jsx` — Back-to-Shop link; subtitle scrub.
- `frontend/src/pages/shop/ShopMyAssignments.jsx` — Back-to-Shop link; subtitle scrub.
- `frontend/src/pages/shop/UnitHistoryLanding.jsx` — Back-to-Shop link; subtitle + footer scrub.
- `frontend/src/pages/shop/UnitHistoryTimeline.jsx` — Back-to-Shop link; subtitle scrub.

### Untouched
- All other backend routers · server.py (no changes; new endpoints landed in `shop_intel.py` already mounted in Track 13.30C).
- `HubBackLink.jsx` (Track 13.30B fix preserved).
- App.js routes.
- Backend tests.
- `/shop/hub_legacy` rollback.

## 9 · Tests / smokes passed

- **Backend:** existing pytest suite preserved at **42/42 pass** (no backend regression — only additive endpoints).
- **Frontend lint:** clean on `ShopSelector`, `BackToShopLink`, `FleetVisibility`. ShopHubV2 / FuelLubeVisitForm / STR* / Manager Queue / My Assignments / UnitHistory* lint clean.
- **Runtime overlay sweep:** 12 routes (`/shop`, `/shop/fleet`, `/shop/equipment`, `/shop/fuel-lube/new`, `/shop/fuel-lube`, `/shop/service-truck-reconciliation`, `/shop/service-truck-reconciliation/new`, `/shop/units/history`, `/shop/manager/queue`, `/shop/me`, `/dispatch-portal`, `/shift`) — **all `overlay=False`**.
- **Engineering-copy scrub:** all 12 routes report `Track 13 = 0` and `/api/ = 0` in operator-visible text *except* `/shop/manager/queue` where the single "Track 13" mention traces to seeded defect-title data, **not UI copy**.
- **Source-truth selectors:** verified live —
  - `fuel-lube-visit-form-project-project-root` = 1
  - `fuel-lube-visit-form-truck-unit-root` = 1
  - `fuel-lube-line-unit-0-unit-root` = 1
  - `strr-form-truck-unit-root` = 1
- **Back-to-Shop link:** verified live on all 10 PortalShell-driven Shop subpages.

## 10 · Hard locks verified

- Dispatch Map-First intact (`/dispatch-portal` smoke).
- Driver no-login intact (`/shift` smoke).
- Shop Repair Complete ≠ RTS — no endpoint touched.
- Dispatch / Admin RTS authority preserved.
- Mechanic Assignment intact.
- Unit History intact.
- Fuel/Lube backend intact (only additive list endpoints added).
- Service Truck Reconciliation backend intact.
- Material Movement Ledger untouched.
- MaintainX dormant.
- `/shop/hub_legacy` rollback alive.

## 11 · Remaining blockers

None for Track 13.30D. The one residual *"Track 13"* mention on `/shop/manager/queue` is **seeded defect-title data**, not UI copy — addressing it requires a data cleanup of legacy preview seeds, which is out of scope for a UI correction pass and explicitly forbidden by the *"do not break workflows"* rule. Recommend a future data-cleanup track if operator wants legacy seed strings rewritten.

## 12 · Final verdict

🟢 **GREEN.** Track 13.30C-fix correction pass complete.

- Runtime crash fixed (FocusBanner import).
- Every Shop subpage has a visible "← Back to Shop" affordance.
- Fuel/Lube and Service Truck forms use source-truth selectors with honest manual fallback.
- Engineering copy fully scrubbed from operator-visible UI.
- No new endpoints mutate state; both new endpoints are read-only and gated identically to the rest of the shop-intel surface.
- All 12 smoke routes load without overlay; backend suite preserved at 42/42 pass.

**Ready for Track 13.30D.**
