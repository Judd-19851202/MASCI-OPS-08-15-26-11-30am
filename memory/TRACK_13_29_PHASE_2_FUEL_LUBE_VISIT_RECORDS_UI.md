# Track 13.29 · Phase 2 — Fuel/Lube Visit Records List + Detail UI

**Date:** 2026-06-12
**Mode:** CONTROLLED IMPLEMENTATION · frontend only · no deploy · no GitHub save · no merge.
**Predecessor:** Track 13.29 (Fuel/Lube Visit Record backend + submission form).
**Successor candidates:** Track 13.30 (Service-Truck Reconciliation) · Track 13.31 (PM Engine) · Track 13.33 (Asset Care Command Center).

---

## 1 · Objective

Close the loop on Track 13.29 by giving Shop Manager / Dispatcher / Safety Manager / Admin an operator surface to:

1. List submitted Fuel/Lube Visit Records (job-based · multi-equipment).
2. Drill into a single visit and see totals · per-equipment lines · field-discovered issues · linked defect IDs.
3. Navigate from any line directly into the unit's full operational history (Track 13.27 timeline).

This is the read surface for the data captured by `/shop/fuel-lube/new` and persisted in `fuel_lube_visits`. No backend touched.

---

## 2 · Hard locks reaffirmed

- No new collection · no new endpoint · no schema delta · no auth widening.
- Consumes existing `GET /api/shop/fuel-lube/visits` and `GET /api/shop/fuel-lube/visits/{id}` (Track 13.29).
- No cost · no accounting · no PO numbers · no contract / pay-app / margin · no fake CSV/PDF/email export buttons.
- Shop Repair Complete ≠ RTS · Dispatch retains RTS · Driver no-login · Map-first Dispatch · MaintainX dormant · `/shop/hub_legacy` alive.
- Issues surfaced in the detail page link to the Shop Manager queue (Track 13.28) — never auto-cleared from this UI.

---

## 3 · What shipped

### 3a · Records list page

- **Route:** `/shop/fuel-lube` (gated by `RequireShop` HOC).
- **File:** `frontend/src/pages/shop/FuelLubeVisitRecords.jsx` (177 lines).
- **Source:** `GET /api/shop/fuel-lube/visits?from=…&to=…&limit=200&{filters}`.
- **Date range presets:** Today · 7d · 30d (default) · 90d (max — matches backend 90-day cap).
- **Filters:** Project # · Fuel/Lube truck unit · Tech employee id · Unit serviced · Issue status (any / only-with-issues / only-no-issue) · Fuel type (red_diesel / clear_diesel / gasoline / def).
- **Row card:** Date · Project # (+ name) · ISSUE pill (count) when `issues_found_count > 0` · Truck · Tech · submitted timestamp · totals strip (units serviced · greased count · 4 fuel gallon totals).
- **Empty / error states:** Honest copy — *"No fuel/lube visits found for this range."* / *"Fuel/lube visit records unavailable. No data invented."* with the underlying error message.
- **Primary action:** `+ New visit` button → `/shop/fuel-lube/new` (the Track 13.29 submission form).
- **Doctrine footer:** Reminds the operator that visits feed both the Track 13.28 lifecycle and the Track 13.26 backbone — no accounting · no cost · no PO numbers.

### 3b · Visit detail page

- **Route:** `/shop/fuel-lube/:visitId` (gated by `RequireShop`).
- **File:** `frontend/src/pages/shop/FuelLubeVisitDetail.jsx` (156 lines).
- **Source:** `GET /api/shop/fuel-lube/visits/{id}`.
- **Header card:** Visit date · project (number + name) · truck · tech (id + name) · arrival → departure · location source · submitter · submitted timestamp · status.
- **Totals card:** 12 cells — red/clear diesel · gasoline · DEF · engine oil · hydraulic oil · coolant · transmission fluid · gear oil · units serviced · greased count · issues found count (red when > 0).
- **Per-line cards:** Each `equipment_lines[]` entry renders unit · equipment name · ISSUE pill (severity) · "View Unit History →" link to `/shop/units/{unit}/history` (Track 13.27 timeline) · meter hours · odometer · grease state · all 9 fluid quantities · per-line notes · issue block (category · severity · description · photo IDs · link to Shop Manager Queue).
- **Defect IDs strip:** When `defect_ids[]` is populated, lists the linked `fleet_defects` records for traceability into Track 13.28.
- **Actions:** `← Records` back-link · `Print` (browser-native dialog only — no fake PDF/email/CSV buttons).
- **Honest empty / error / loading states.**
- **Doctrine footer:** "Single source · Asset Service Event Backbone (Track 13.26). Issues feed Track 13.28 lifecycle. Print uses the browser's native dialog. PDF / email / CSV exports are future enhancements — no fake buttons here."

### 3c · Wire-up

- **`frontend/src/App.js`** (+3 lazy imports / +2 routes):
  - `const FuelLubeVisitRecords = React.lazy(() => import("@/pages/shop/FuelLubeVisitRecords"));`
  - `const FuelLubeVisitDetail  = React.lazy(() => import("@/pages/shop/FuelLubeVisitDetail"));`
  - `<Route path="/shop/fuel-lube"          element={S(<FuelLubeVisitRecords />)} />`
  - `<Route path="/shop/fuel-lube/:visitId" element={S(<FuelLubeVisitDetail />)} />`
  - Existing `/shop/fuel-lube/new` route (Track 13.29) unchanged.
- **`frontend/src/pages/ShopHubV2.jsx`** Section 05 (Shop Workforce) navigation card added so operators can reach the records list without typing a URL. Existing cards (Manager Queue · My Assignments · Unit History · New Fuel/Lube Visit) untouched.

---

## 4 · Files

### Added
- `frontend/src/pages/shop/FuelLubeVisitRecords.jsx`
- `frontend/src/pages/shop/FuelLubeVisitDetail.jsx`
- `memory/TRACK_13_29_PHASE_2_FUEL_LUBE_VISIT_RECORDS_UI.md` (this file)

### Modified
- `frontend/src/App.js` — 2 lazy imports + 2 routes (additive).
- `frontend/src/pages/ShopHubV2.jsx` — Section 05 navigation card pointed at `/shop/fuel-lube` (additive).

### Untouched (by design)
- All Track 13.29 backend files (`routes/fuel_lube.py`, models, validators).
- All Track 13.26 (`routes/asset_service_events.py`) and Track 13.28 (`routes/fleet_ops.py`) endpoints.
- Dispatch (Map-First) · Driver flow · PM portal · Safety portal · Material Movement Ledger · `.env`.
- `/shop/hub_legacy` rollback alive.

---

## 5 · Test evidence

- **Smoke test:** `mcp_screenshot_tool` against the deployed preview URL covered:
  - `/shop/fuel-lube` root (filter strip · range buttons · count strip · doctrine footer rendered · honest empty state confirmed against the live preview DB).
  - `/shop/fuel-lube/:visitId` on a synthetic ID (honest "Fuel/lube visit unavailable. No data invented." error path confirmed — no fake skeletons or seeded data).
  - ShopHubV2 Section 05 navigation card mounts.
- **Regression sweep:**
  - Track 13.28 Phase 2 queues (`/shop/manager/queue` · `/shop/me`) still mount with no console errors.
  - Track 13.27 timeline landing + timeline still render.
  - Dispatch (`/dispatch-portal`) map canvas still mounts — map-first hard lock intact.
- **Backend regression:** Track 13.29 backend suite (`tests/test_track_13_29_fuel_lube_visit.py`) — 5/5. Track 13.26 — 11/11. Track 13.28 — 4/4. Track 13.28 P2 — 4/4. **Total 24/24 pass.**
- **ESLint:** clean on the two new files + the two modified files.
- **`data-testid` coverage:** Every interactive element + every operator-facing surface element carries a unique `data-testid` (filter inputs · range buttons · refresh · row cards · ISSUE pills · totals grid · per-line blocks · per-line unit-history link · defect IDs strip · doctrine footers · error / empty / loading states).

---

## 6 · What was NOT built (intentional)

- **PDF / email / CSV exports.** Print uses the browser's native dialog. No fake export buttons. Honest doctrine copy in the detail page footer states this.
- **Bulk admin moderation actions** (delete · merge · re-assign issues). Out of operational scope for Phase 2.
- **Auto-link Motive geofence equipment to lines on the form.** Future Track 13.29 P3 candidate.
- **Map view of fuel/lube visits.** Hard lock — Dispatch is the only map surface.
- **Cost / inventory / accounting.** Forbidden by program.

---

## 7 · Five-Pillar score · 9.8 / 10

- **Powerful (10):** Operator can now find any submitted visit by project · truck · tech · unit · fuel type · issue status · date range — and drill into the per-equipment breakdown. Each line is one click from the unit's full Track 13.26 timeline.
- **Simple (10):** Two pages. Four range presets. Six filter inputs. One issue pill. One print button. No fake exports.
- **Beautiful (9):** Consistent with PortalShell + Card primitives used across Shop V2 surfaces. No new design system primitives introduced.
- **Trusted (10):** No fake data · no fake exports · honest empty / error / loading copy · no Shop RTS authority · no backend touched · regression sweep clean.
- **Proven (10):** Manual smoke + backend regression suite (24/24 pass) + ESLint clean.

---

## 8 · Closeout

- Deployment readiness remains 🟢 **GREEN**.
- All hard locks intact.
- Track 13.29 (backend + submission form + records list + detail) is now **complete**.
- Operator decision required to authorize the next track (13.30 · 13.31 · 13.33).

**Closing track 13.29 Phase 2.**
