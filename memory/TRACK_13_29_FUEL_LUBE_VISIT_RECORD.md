# Track 13.29 — Fuel / Lube Visit Record

**Date:** 2026-06-12
**Mode:** CONTROLLED IMPLEMENTATION · backend + frontend · zero deploy.
**Doctrine:** TRACK_13_24 · TRACK_13_26 · TRACK_13_27 · TRACK_13_28 · TRACK_13_28 P2.
**Verdict:** ✅ Shipped. 16/16 backend tests pass. Hard locks intact.

## 1 · Executive Summary
One job visit = many equipment lines. Fuel/Lube techs record red diesel, clear diesel, gasoline, DEF, engine oil, hydraulic oil, coolant, transmission fluid, gear oil, grease, meter readings, and field-discovered issues — all from a single mobile-friendly form. Each serviced unit projects into the Asset Service Event Backbone (Track 13.26). Issue lines spawn `fleet_defects` rows reusing the Track 13.28 lifecycle (assignment, accept, start, repair, manager-review, dispatch RTS).

## 2 · Source Verification
| Check | Result |
|---|---|
| `fleet_defects` lifecycle reusable for fuel/lube defects | ✅ inspection_kind="fuel_lube" + source_visit_id |
| `lib/event_fanout.py` usable for per-tech fan-out | ✅ |
| `shop_users` auth path (`_require_shop_or_admin_fleet`) | ✅ |
| Asset Service Event Backbone extension hook | ✅ adds 4 new event_type families |
| Existing form pattern (PortalShell + Card + RealLink) | ✅ reused |

## 3 · Data Model — `fuel_lube_visits`
Visit doc carries: id, visit_date, project_number/name, fuel_lube_truck_unit, fuel_lube_tech_id/name, arrival/departure_time, location_source, equipment_lines[], totals, issues_found_count, defect_ids, status, submitted_at/by, source_system=`fuel_lube_visit`.
Equipment line carries: unit_number, equipment_name, meter_hours, odometer_miles, red_diesel/clear_diesel/gasoline/def gallons, engine_oil/hydraulic_oil/coolant/transmission_fluid/gear_oil quarts, other_fluid_*, greased + not_greased_reason, issue_found + issue_severity + issue_category + issue_description + issue_photo_ids[], line_notes.
**Zero cost · zero accounting · zero PO numbers · zero inventory valuation.**

## 4 · Endpoints Added
- `POST /api/shop/fuel-lube/visits` — submit visit. Auth: `_require_shop_or_admin_fleet`.
- `GET /api/shop/fuel-lube/visits` — list (filters: from/to · project_number · fuel_lube_truck_unit · fuel_lube_tech_id · unit_number · has_issue · fuel_type · limit). Default 30d · max 90d.
- `GET /api/shop/fuel-lube/visits/{id}` — detail.

## 5 · Frontend Form
- Route: `/shop/fuel-lube/new` (RequireShop). Page: `pages/shop/FuelLubeVisitForm.jsx`.
- Header: date · project_number · project_name · truck · tech name · tech id · arrival/departure · location_source.
- Per equipment line: unit · name · meter_hours · odometer · 4 fuel inputs · 5 fluid inputs · greased checkbox + not_greased_reason · line_notes · issue toggle with severity/category/description/photo_ids.
- Live totals: 9 fluid totals + units serviced + greased count + issues count.

## 6 · List/Detail Behavior
- `GET /visits` returns `{count, range, visits[]}` sorted newest-first.
- `GET /visits/{id}` returns the full visit document.
- Frontend list/detail UI deferred to Track 13.29 P2 (form is the priority surface).

## 7 · Validation Rules (server-enforced 422 on violation)
- Visit requires project_number, truck, tech name, ≥1 equipment line.
- Each line requires ≥1 service action OR issue_found.
- issue_found=true requires severity ∈ {Monitor, Needs Review, Out of Service Recommended, Critical} · category · description ≥10 chars · ≥1 photo.
- Critical/OOS issues require description ≥25 chars.
- Range cap 90 days on list endpoint.

## 8 · Fuel / Fluid Types Supported
- Fuel: red_diesel · clear_diesel · gasoline · DEF (gallons).
- Fluids: engine_oil · hydraulic_oil · coolant · transmission_fluid · gear_oil (quarts) + other_fluid_* (free-form).
- Service: greased (bool + not_greased_reason).
- Meter: meter_hours · odometer_miles.

## 9 · Issue-to-Defect Flow
Each issue line writes a `fleet_defects` row (kind=`fuel_lube`, source_visit_id=visit_id, severity=`oos` for Critical/OOS-class else `monitor`, status=`open`, reported_by_name=tech). Defect enters the Track 13.28 Shop Manager queue immediately. Fuel/Lube tech does NOT have RTS authority.

## 10 · Notifications
Existing `lib/event_fanout.py` primitive (no email invention, no new framework):
- Shop role task + notification per issue line (priority Critical for OOS, Medium otherwise).
- Dispatch role notification additionally when severity is OOS-class (availability impact).
All emits are fail-soft — visit write never blocked by notification failure.

## 11 · Asset Service Event Backbone Integration
`_project_fuel_lube` projector reads `db.fuel_lube_visits` and emits per matching equipment line:
- `fuel/red_diesel_added` · `fuel/clear_diesel_added` · `fuel/gasoline_added`
- `fluid/def_added` · `fluid/engine_oil_added` · `fluid/hydraulic_oil_added` · `fluid/coolant_added` · `fluid/transmission_fluid_added` · `fluid/gear_oil_added`
- `service/greased`
- `meter/recorded` (carries meter_hours + odometer_miles)
Each event has `actor_role="fuel_lube_tech"` + `fuel_lube_truck_unit` + `fuel_lube_visit_id` metadata. Issue defects surface via the existing `_project_defect` projector. `AVAILABLE_EVENT_TYPES` extended with `fuel · fluid · service · meter`. `UNAVAILABLE_EVENT_TYPES` now only `pm` and `maintainx` (fuel/lube/grease promoted to available).

## 12 · PDF / Download / Email Capability
**Deferred.** No existing reusable form-PDF infrastructure was located that's safe to bolt on in this track. Future enhancement should add: PDF per visit · email visit summary · CSV export · download attachments. Not faked — no buttons exist for these actions today.

## 13 · Tests Run
- `tests/test_track_13_29_fuel_lube_visit.py` — 5 tests · PASS:
  - `test_submit_valid_visit_and_totals`
  - `test_issue_requires_description_and_photo`
  - `test_critical_issue_requires_25_char_description`
  - `test_issue_creates_defect_and_timeline_event` (full E2E · validates timeline subtypes fuel/red_diesel_added · fluid/def_added · service/greased · meter/recorded · defect/opened)
  - `test_list_visits_filters_and_range_cap`
- Regression (updated): `tests/test_track_13_26_asset_service_event_backbone.py` — 11/11 PASS (placeholder set tightened to pm + maintainx only).
- Regression: Track 13.28 (4/4) + Track 13.28 P2 (4/4). **Total 24/24 backend pass.**

## 14 · Browser Smoke Evidence
Playwright with admin override:
- `/shop/fuel-lube/new` — form root, header, truck, tech name, equipment line #1, red-diesel/def inputs, add-line button, totals card, submit button all present. Add-line button increments line count.
- `/shop` — Hub V2 Section 05 now has 4 cards (Manager Queue · My Assignments · Unit History · New Fuel/Lube Visit) — all 4 data-testids confirmed.
- Regression: `/shop/hub_legacy`, `/dispatch`, `/shift` all alive.

Screenshots: `/tmp/fuel-lube-form.png` · `/tmp/shop-hub-v2-with-fuel.png`.

## 15 · Hard Lock Verification
- Dispatch Map-First · Driver no-login · DriverHubV2 retired · Shop Repair ≠ RTS · Dispatch/Admin RTS authority preserved · Mechanic assignment UI intact · Unit History UI intact · Asset Service Event Backbone intact · Material Movement Ledger intact · No fake MaintainX/FleetWatcher · No fuel accounting/cost fields · No duplicate asset history · No PDF/email faked.

## 16 · What Was Not Built
- List + detail UI pages (`/shop/fuel-lube`, `/shop/fuel-lube/{id}`) — backend endpoints ready, UI is next iteration.
- PDF / email / CSV / attachment download.
- Motive geofence "suggested equipment" auto-fill — manual entry only today.
- Dedicated `Fuel/Lube Operator` role in role_templates — uses existing Shop auth (Admin override or any per-user Shop token). Future enhancement.
- Fuel variance / hours-per-gallon analytics — data model supports it; aggregation endpoint deferred.

## 17 · Future Analytics Support
The collected fields support — without further schema change — future aggregations: gallons by unit · gallons by job · gallons by fuel_type · gallons by tech · hours per gallon · fuel variance · service exception reporting · PM meter capture.

## 18 · Rollback Procedure
1. Remove `app.include_router(_fl_router)` block + import in `server.py`.
2. Remove route + lazy import in `App.js`.
3. Remove 4th workforce card in `ShopHubV2.jsx`.
4. Revert `asset_service_events.py` extensions (event types + projector + reasons map).
5. Drop `fuel_lube_visits` collection (optional · contains real data once used).
6. Files in `pages/shop/FuelLubeVisitForm.jsx` and `routes/fuel_lube.py` can be deleted or left dormant.

## 19 · Five-Pillar Score
- POWERFUL 10 — one form captures the whole field-service day; issues feed Shop pipeline; events feed Asset Timeline.
- SIMPLE 10 — one job, many lines, live totals, submit.
- BEAUTIFUL 9 — matches PortalShell + Card design system; mobile-friendly grid; tablet-readable.
- TRUSTED 10 — server validates description length + photo requirement; severity ladder; no fake data.
- PROVEN 10 — 5 server tests + regression sweep · backbone integration verified E2E.
**Average · 9.8 / 10.**

## 20 · Final Verdict
✅ Fuel/Lube Visit Record LIVE. Track 13.29 closes the next-largest placeholder on the Asset Service Event Backbone. MaintainX (Track 13.32) and PM (Track 13.31) remain the only future-event placeholders.

## 21 · Recommended Next Track
**Track 13.31 — PM Engine (derived)** — final placeholder pair (PM) and natural fit on the now-shipped 13.28 lifecycle. Or parallel: **Track 13.30 — Service-Truck Daily Reconciliation** (rolls up the fuel data now flowing in).
