# Track 13.30 · Service Truck Daily Reconciliation

**Date:** 2026-06-12
**Mode:** CONTROLLED IMPLEMENTATION · backend + frontend · no deploy · no GitHub save · no merge.
**Predecessor:** Track 13.29 P2 (Fuel/Lube Visit Records List + Detail UI).
**Successor candidates:** Track 13.31 (PM Engine) · Track 13.33 (Asset Care Command Center).

---

## 1 · Executive Summary

Fuel/lube techs can now answer one operational question for each service truck on each day:

> *For Fuel Truck FL-01 today — did the starting fuel + fluid quantities minus the dispensed quantities (from submitted Fuel/Lube Visit Records) match the ending quantities closely enough to trust the day?*

The system pulls dispensed totals **from Track 13.29 fuel_lube_visits** (single source of fluid truth), computes `expected_end = start - dispensed`, computes `variance = actual_end - expected_end`, and classifies the day as **Within expected range** / **Needs review** / **Significant variance** / **Incomplete**. No new dispensed-source collection. No accounting. No theft language.

---

## 2 · Source Verification (Phase 0)

| Surface | Status |
|---|---|
| `POST/GET /api/shop/fuel-lube/visits` (Track 13.29) | Live · used as dispensed source |
| `GET /api/shop/fuel-lube/visits/{id}` | Live · linked-visit projection |
| `fuel_lube_visits.totals` schema | Confirms 4 fuel totals + 5 fluid totals all per-visit |
| `service_truck_reconciliation` / `fuel_reconciliation` / `tank_start` collections | NONE — confirmed via codebase grep · this track is greenfield |
| `_require_shop_or_admin_fleet` (Shop or Admin Token) | Reused · no new auth gate |
| Frontend form/list/detail patterns | Reused PortalShell + Card + EmptyState primitives |

No dedicated Fuel/Lube role exists today. **Future role gap documented:** a stand-alone `fuel_lube_tech` role would tighten gate scope. For now Shop/Admin gate matches Track 13.29.

---

## 3 · Data Model

New collection: **`service_truck_reconciliations`**.

One document per service truck per day. Shape:

```json
{
  "id": "strr-…",
  "date": "YYYY-MM-DD",
  "service_truck_unit": "FL-01",
  "tech_id": "tech-007",
  "tech_name": "Pat Smith",
  "start_quantities": { "red_diesel_gallons": 1000, "clear_diesel_gallons": 250, … },
  "dispensed_quantities": {
    "source": "fuel_lube_visits",
    "visit_count": 3,
    "visit_ids": ["flv-…", "flv-…", "flv-…"],
    "red_diesel_gallons": 840, …
  },
  "end_quantities":          { "red_diesel_gallons": 145, … },
  "expected_end_quantities": { "red_diesel_gallons": 160, … },
  "variance": { "rows": [ { "field": "red_diesel_gallons", "start": 1000,
                            "expected_end": 160, "actual_end": 145,
                            "variance": -15, "variance_pct": 0.015,
                            "status": "green", "unit": "gallons" }, … ] },
  "variance_status": "green | yellow | red | incomplete",
  "status": "start_logged | closed | needs_review",
  "notes": "operational notes only",
  "review_notes": "shop manager operational context",
  "reviewed_by": "…", "reviewed_at": "ISO-8601",
  "start_submitted_at": "ISO-8601",
  "end_submitted_at":   "ISO-8601",
  "source_system": "service_truck_reconciliation"
}
```

**Closed-set product fields** (9 total): 4 fuels (gallons) + 5 fluids (quarts).
**Forbidden fields (sanity tested):** no `cost` · `price` · `po_number` · `invoice` · `tax` · `margin` · `ledger_amount` · `payable` · `receivable` · `general_ledger`.

---

## 4 · Endpoints Added (5)

All under `_require_shop_or_admin_fleet`. Prefix: `/api/shop/service-truck-reconciliation`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/start` | Create or update start-of-day quantities. Idempotent before close (re-start overwrites). Refuses if status is `closed` or `needs_review` (409). |
| POST | `/close` | Submit end-of-day quantities. Pulls dispensed totals from `fuel_lube_visits` by truck+date (case-insensitive). Computes expected_end, variance per product, overall variance_status. Status flips to `closed` (green) or `needs_review` (yellow/red). |
| POST | `/{id}/review` | Optional Shop Manager review notes. Sets `reviewed_by` + `reviewed_at` and forces status back to `closed`. Notes ≥10 chars required. |
| GET | `` (root) | Filtered list: date_from / date_to / service_truck_unit / tech_id / variance_status / status. Default 30d · cap 90d (422 if exceeded or to < from). Returns `{count, range, reconciliations[]}`. |
| GET | `/{id}` | Detail with linked Fuel/Lube Visit summaries (id, project, tech, totals, units_serviced, issues_found_count). |

No router file touches Track 13.29's `fuel_lube_visits` data — it is read-only.

---

## 5 · Start/Close Workflow

1. **Start of day** — Tech opens `/shop/service-truck-reconciliation/new`, selects mode `Start of Day`, enters date + truck + tech + start quantities, submits. Backend POST `/start`. Status → `start_logged`. Reconciliation id displayed for confirmation.
2. **Dispensing** — Tech submits Fuel/Lube Visit Records throughout the day via the existing Track 13.29 form. These are the dispensed source.
3. **Close of day** — Same form, mode `Close of Day`. Tech enters end quantities. Backend POST `/close` pulls all `fuel_lube_visits` matching truck+date, sums totals, computes per-product expected_end + variance, classifies overall status.
4. **Result UI** — Form renders a 5-column variance grid (Product · Start · Dispensed · Expected end · Actual end + Δ) inline plus a Status chip. Detail link opens `/shop/service-truck-reconciliation/:recId`.
5. **Optional review** — Shop manager opens detail and adds review notes (≥10 chars). Status returns to `closed`.

---

## 6 · Variance Calculation Rules

For each tracked product (4 fuels in gallons, 5 fluids in quarts):

```
expected_end   = start_qty − dispensed_qty
variance       = actual_end − expected_end           (negative ⇒ less than expected)
variance_abs   = |variance|
variance_pct   = variance_abs / max(start_qty, 1)
```

| Class | Fuel rule (gallons) | Fluid rule (quarts) |
|---|---|---|
| **Green** | `abs ≤ 5` OR `pct ≤ 2%` | `abs ≤ 2` OR `pct ≤ 2%` |
| **Yellow** | `pct > 2%` AND `pct ≤ 5%` | `pct > 2%` AND `pct ≤ 5%` |
| **Red** | `pct > 5%` | `pct > 5%` |
| **Incomplete** | start logged but no close yet | same |

Overall variance status is the **worst** per-product classification (red > yellow > green). Edge case: when `start_qty=0` AND `actual_end=0`, the product line is recorded as `green` (no movement, no signal).

---

## 7 · List / Detail UI

- **List (`/shop/service-truck-reconciliation`):** 4 date-range presets (today / 7d / 30d default / 90d max), filters (truck, tech, variance status, record status), row cards with date · truck · status chips · variance summary across 6 products · linked visit count · submitted timestamps.
- **Detail (`/shop/service-truck-reconciliation/:recId`):** Header card (9 cells) · 7-column variance grid (product · start · dispensed · expected · actual · variance + Δ · per-product status chip) · linked Fuel/Lube Visits with click-through · review block (Shop Manager notes) · doctrine footer.
- Both pages show **honest empty / error / loading states**. Print uses browser-native dialog only — no fake PDF/email/CSV.

---

## 8 · Shop Hub Surfacing

Added Section 05 navigation card to `/shop`:

> **Service Truck Reconciliation** — Start/end fuel and fluid accountability by truck and day. Dispensed totals pulled from submitted Fuel/Lube Visits. Variance: *within range · needs review · significant*.

Existing 5 workforce cards untouched. `/shop/hub_legacy` rollback alive.

---

## 9 · Linked Fuel/Lube Visits

Backend `/{id}` returns `linked_visits[]` projection (read-only) with minimal fields: id · project_number · project_name · fuel_lube_tech_name · submitted_at · totals · issues_found_count · units_serviced. Frontend renders each as a card linking to `/shop/fuel-lube/:visitId`. This **closes the operator loop** — open a reconciliation, see exactly which visits drove the dispensed total, click into any visit for per-equipment breakdown.

---

## 10 · Asset Timeline Behavior

Service truck reconciliation is **truck-level operational accountability**, not per-serviced-asset. To honor the "no duplicate timeline" hard lock, this track **deliberately does not** project per-equipment events into `/api/assets/{unit}/timeline`. Equipment-level events already come from the Track 13.29 `_project_fuel_lube` projector. Truck-level events (`service_truck/reconciliation_closed`, `service_truck/variance_review_needed`) are documented as a future projector candidate IFF the service truck itself becomes a tracked asset in `equipment_master`; the projector hook point is documented in `routes/asset_service_events.py` for future activation. **No projector added in this track** — preserves the single source of truth principle and avoids speculative event sources.

---

## 11 · Export / PDF / Email Status

**Not built.** No reusable PDF/email/CSV infrastructure exists for this surface. Print uses the browser's native dialog only — explicitly documented in the detail-page doctrine footer. No dead export buttons. Future enhancements:
- Per-day reconciliation PDF
- CSV export (date-bounded · no cost fields)
- Email delivery of `needs_review` rollups

---

## 12 · Tests Run

**File:** `backend/tests/test_track_13_30_service_truck_reconciliation.py` (12 tests).

| # | Test | Verifies |
|---|---|---|
| 1 | `test_start_creates_record_and_is_idempotent_before_close` | Start creates document · re-start before close is idempotent |
| 2 | `test_close_pulls_dispensed_and_computes_variance_green` | Spec example (1000/250/100/50 → 840/60/20/18 dispensed → 145/190/80/31 actual). Red diesel variance -15 gal but pct 1.5 % → green. |
| 3 | `test_close_yellow_classification` | 4 % variance → yellow + needs_review |
| 4 | `test_close_red_classification` | 10 % variance → red + needs_review |
| 5 | `test_close_fluid_quart_thresholds` | Fluid uses 2-qt absolute + 2%/5% pct rules |
| 6 | `test_incomplete_until_close` | Start logged with no close → variance_status=`incomplete` |
| 7 | `test_list_filters_and_range_cap` | Default 30d range, 90d cap (422), bad enum (422) |
| 8 | `test_detail_includes_linked_visits` | Detail returns matching fuel_lube_visits |
| 9 | `test_review_writes_notes_and_clears_needs_review` | Review re-closes the day |
| 10 | `test_response_has_no_cost_or_accounting_fields` | Doctrine sanity sweep |
| 11 | `test_close_does_not_mutate_fuel_lube_visit` | Source read-only · status/totals/submitted_at unchanged |
| 12 | `test_cannot_restart_a_closed_day` | Closed days locked (409) |

**Result: 12/12 PASS** in 30.7 s.

**Regression sweep (24 prior tests):**
- Track 13.26 backbone — 11/11 PASS
- Track 13.28 mechanic assignment — 4/4 PASS
- Track 13.28 P2 parts capture — 4/4 PASS
- Track 13.29 fuel/lube visit — 5/5 PASS

**Total backend suite: 36/36 PASS.**

ESLint clean on all 4 modified frontend files.

---

## 13 · Browser Smoke Evidence

Captured via `mcp_screenshot_tool` with the admin token planted in localStorage:

- ShopHubV2 card `shop-hub-v2-action-service-truck-reconciliation` mounts (count=1).
- `/shop/service-truck-reconciliation` list page — root + filter strip + 4 range buttons + doctrine footer + `+ Start / Close day` button mount; **11 itest reconciliations rendered live** with `WITHIN EXPECTED RANGE` / `NEEDS REVIEW` / `INCOMPLETE` chips visible.
- `/shop/service-truck-reconciliation/new` form — root + start/close toggles + all 9 product inputs + submit button mount.
- Regression: `/shop/fuel-lube` records page still mounts. `/shop/manager/queue` still renders. `/dispatch-portal` still loads (map canvas behavior unchanged from prior tracks).
- Test data cleaned (11 strr docs + 9 visit docs deleted) before report.

---

## 14 · Hard Lock Verification

| Hard lock | Status |
|---|---|
| Dispatch Map-First | INTACT · zero map changes |
| Driver no-login | INTACT · no driver surfaces touched |
| DriverHubV2 retired | INTACT |
| Shop Repair Complete ≠ RTS | INTACT · no `/clear` exposure · no RTS path added |
| Mechanic assignment UI (Track 13.28) | INTACT |
| Unit History UI (Track 13.27) | INTACT |
| Asset Service Event Backbone (Track 13.26) | INTACT · no projector added |
| Fuel/Lube visit submit/list/detail (Track 13.29) | INTACT · read-only consumer |
| Material Movement Ledger (Track 13.19–22) | INTACT · zero touch |
| MaintainX activation | DORMANT · no SDK calls |
| FleetWatcher fabrication | INTACT · no fake data |
| No fuel accounting / cost | VERIFIED · pytest sanity sweep |
| No duplicate asset history | INTACT · no truck-level projector |
| No PO numbers / fuel tax / invoice / margin | VERIFIED · pytest sweep |
| No driver login | INTACT |
| No theft language / disciplinary copy | VERIFIED · doctrine copy reviewed |

---

## 15 · What Was NOT Built (intentional)

- **Asset-timeline projector** for `service_truck/reconciliation_closed` events (preserves the "no duplicate timeline" hard lock; truck-level events are out of scope until service trucks are formally added to `equipment_master`).
- **PDF / email / CSV export** (no reusable infrastructure; documented as future).
- **Bulk admin moderation** (delete · merge · reopen) — not in operational scope.
- **Cost / inventory / accounting / fuel tax / ERP / pay-apps / PO numbers** — forbidden by program.
- **Auto-link Motive geofence truck arrivals** to visit lines — Track 13.29 P3 candidate.
- **Per-mechanic theft register / payroll docking** — explicitly forbidden by program.

---

## 16 · Future Analytics Support

The collection's shape (closed-set product fields, deterministic statuses, per-product variance rows) is intentionally analyzable:
- *"Which trucks ran 'red' on more than 3 days last 30 days?"* — `aggregate({date,variance_status,truck})`.
- *"Which products see the most variance across the fleet?"* — `aggregate({variance.rows.field, status})`.
- *"Tech-level pattern across multiple trucks?"* — `aggregate({tech_id, variance_status})`.

These dashboards are explicitly NOT built in this track (analytics are Track 13.33 candidates) but the data substrate supports them with zero schema migration.

---

## 17 · Rollback Procedure

1. Remove the router include in `server.py` (lines mounting `_strr_router`).
2. Drop the 3 lazy imports + 3 routes in `frontend/src/App.js`.
3. Remove the ShopHubV2 nav card (Section 05).
4. Optionally drop the `service_truck_reconciliations` collection.
5. All other surfaces (Track 13.26–13.29) remain untouched and operational.

No data migration is required for rollback — the collection is greenfield and isolated.

---

## 18 · Five-Pillar Score · 9.8 / 10

- **Powerful (10):** Closes a long-standing operational accountability gap. Each service truck/day is now answerable in one operator click — start, dispensed (from real visits), expected, actual, variance, status — with a review path for managers.
- **Simple (10):** Two operational surfaces (form + records + detail), one mode toggle, four range presets, four list filters, one print button. Doctrine footers explain the rules on every surface.
- **Beautiful (9):** Reuses PortalShell + Card + EmptyState primitives. No new design system primitives introduced.
- **Trusted (10):** No accounting · no cost · no theft language · no fake exports · no source mutation · pytest sanity sweep enforces forbidden-term absence · honest empty/error/loading states · read-only join.
- **Proven (10):** 12 new tests + 24 regression = 36/36 PASS. Live browser smoke confirmed list/detail/form mount + ShopHubV2 surfacing + variance chips render against real itest data.

---

## 19 · Final Verdict

🟢 **GREEN.** Track 13.30 is COMPLETE.

- 1 backend file added · 1 server.py mount line added.
- 3 frontend files added · App.js lazy + routes added · ShopHubV2 nav card added.
- 1 new collection (`service_truck_reconciliations`).
- 0 backend file mutations to prior tracks.
- 0 deploy · 0 GitHub save · 0 merge.

---

## 20 · Recommended Next Track

- **Track 13.31 — PM Engine (derived)** — Build a PM schedule projector over `equipment_master` + `equipment_inspections` + Track 13.26 timeline. Backbone is already derived.
- **Track 13.33 — Asset Care Command Center** — Roll Track 13.26–13.30 into a single operator dashboard with rollups (open defects · in-progress repairs · variance flags · upcoming PMs).
- **MaintainX Track 13.32** remains BLOCKED on `MAINTAINX_API_KEY`.

**End Track 13.30.**
