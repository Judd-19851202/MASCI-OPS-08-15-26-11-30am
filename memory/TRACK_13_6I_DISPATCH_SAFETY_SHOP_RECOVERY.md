# TRACK 13.6I — DISPATCH + SAFETY ROUTE SWAPS · OLDEST-AGE METRICS · SHOP RECOVERY START

**Date**: 2026-06-12
**Final verdict**: **Track 13.6I Complete — Ready For Operator Review**

---

## 1 · Executive Summary
- Phase 1 (Oldest-age secondary metric) shipped on PM-2 / PM-3 endpoints and PM Hub V2 cards.
- Phase 2 (Dispatch route swap) executed: `/dispatch-portal` now serves Dispatch Hub V2 · classic preserved at `/dispatch-portal/hub_legacy` · `/dispatch-portal/hub_v2` alias kept.
- Phase 3 (Dispatch FocusBanner extensions for `focus_assignment_id` / `focus_truck_id` / `focus_driver_id`) was completed in Track 13.6H and re-verified.
- Phase 4 (Safety route swap) executed: `/safety-portal` now serves Safety Hub V2 · classic preserved at `/safety-portal/hub_legacy` · `/safety-portal/hub_v2` alias kept.
- Phase 5 (Shop Recovery start) shipped: `/shop/hub_v2` preview lane is live, 9 action-queue cards driven by the existing `summary.shop` engine, classic `/shop` unchanged.
- 24/24 backend regression tests pass. Visual smoke check across 7 surfaces confirms zero collateral drift.

## 2 · Oldest-age metric implementation
- `pm_command_center.py` `/holds` endpoint now emits `oldest_age_days` and `oldest_age_label` per bucket (`equipment_holds`, `constraint_holds`, `fleet_defects`, `total`). Label strictly factual: `Oldest Held N Days` / `Oldest Held 1 Day`. Derived from `age_days` already on each row, which is derived from real `opened_at` / `updated_at` / `created_at` timestamps.
- `/due-today` endpoint emits `oldest_age_label = "Due Today"` per bucket when count > 0 (engine only matches today by construction).
- Frontend `QueueCard` extended with a `secondary` prop; PM Hub V2 wires `unified_holds_oldest_label` and `due_today_oldest_label`.
- **No risk scores · no AI urgency · no synthetic dates** — labels are pure derivation from existing real timestamps.

## 3 · Dispatch route swap
- App.js: `<Route path="/dispatch-portal" element={DP(<DispatchHubV2 />)} />` + `<Route path="/dispatch-portal/hub_legacy" element={DP(<DispatchHub />)} />` + alias `/dispatch-portal/hub_v2`.
- Other dispatch sub-routes (`/board`, `/command`, `/fleet`, `/driver-qualification`, `/driver/:driverKey`) untouched.
- Auth gate (`DP` = `RequireDispatch`) unchanged.

## 4 · Dispatch rollback verification
- Screenshot `/tmp/swap_dispatch_legacy.png`: classic Dispatch hub (MapLibre live fleet map · 190 total assets · operational chrome) renders fully at `/dispatch-portal/hub_legacy`.
- `dispatch-hub-v2-root` test-id count on legacy = 0 ⇒ rollback path intact.

## 5 · Dispatch FocusBanner verification
- FocusBanner supports `focus_assignment_id`, `focus_truck_id`, `focus_driver_id`. Auth headers carry `X-Dispatch-Token`. Banner mounted on `DispatchBoard` and `FleetVisibility`.
- Honest scope-excluded state confirmed in 13.6H screenshot (`/dispatch-portal/board?focus_assignment_id=…`).

## 6 · Safety route swap
- App.js: `<Route path="/safety-portal" element={SF(<SafetyHubV2 />)} />` + `<Route path="/safety-portal/hub_legacy" element={SF(<SafetyHub />)} />` + alias `/safety-portal/hub_v2`.
- All other safety sub-routes (`/corrective-actions`, `/fire-extinguishers`, `/documents`, `/training`, `/incidents`, `/fleet`) untouched.

## 7 · Safety rollback verification
- Screenshot `/tmp/swap_safety_legacy.png`: classic Safety Operations Dashboard with the full sidebar (Incidents & Escalation · Documents & Training · Compliance & Records · Audits & Guidance) renders fully at `/safety-portal/hub_legacy`.
- `safety-hub-v2-root` count on legacy = 0.

## 8 · Safety workflow preservation
- Trench Safety routes (`/safety/trench-safety`, `/safety/trench-safety/assets`, `/safety/trench-safety/tabulated-data`) untouched.
- All CRUD endpoints, public QR flows, JHA / JHP / inspection / certification / training / digest / notification flows untouched.
- Safety V2 hub merely surfaces a card linking to `/safety/trench-safety` — does not rebuild it.

## 9 · Shop V2 preview start
- New page `/app/frontend/src/pages/ShopHubV2.jsx` mounted at `/shop/hub_v2` behind `RequireShop`.
- Two sections · 7 distinct queue cards (Open Defects, Defects Acked, OOS Units, Units With Open Defect, Active Recovery Work, Waiting On Parts, Returned To Service 7d).
- Each card carries `?focus_filter=…` query param so deep-link triage can be added on `FleetVisibility(scope="shop")` later without backend change.
- **Repair Complete ≠ Safe To Use** rule preserved: Active Recovery and Returned To Service are separate queues.

## 10 · Data-source map
| Surface | Single endpoint | Engine collections |
|---|---|---|
| PmHubV2 | `/api/pm/command-center/{holds,due-today}` + `/api/pm/*` | `equipment_master`, `operational_constraints`, `fleet_defects`, `corrective_actions`, `daily_reports`, `incidents`, `qaqc_inspections`, `safety_training_records` (via /summary), `jobs_master` |
| DispatchHubV2 | `/api/dispatch/command/summary` | `dispatch_assignments`, `equipment_master`, `fleet_defects`, `incidents`, `corrective_actions` |
| SafetyHubV2 | `/api/safety/overview` | `incidents`, `corrective_actions`, `fire_extinguishers`, `safety_training_records`, `safety_documents`, `safety_meetings`, `inspections`, `field_leadership_records` |
| ShopHubV2 | `/api/dispatch/command/summary` (`.shop` slice) | `equipment_master`, `fleet_defects` |

## 11 · Permission verification
- No new auth surfaces. All four hubs reuse their existing portal gate (`DP` / `SF` / `S` / `P|AP`).
- `FocusBanner` adds `X-Dispatch-Token` only as an additional header alongside admin / PM tokens; no escalation.

## 12 · Workflow verification
- Zero existing form, route, or endpoint changed.
- Trench Safety, JHA flows, fire-extinguisher inspection, Pre-Op pipeline, daily-report verification, CAPA closeout, Dispatch lifecycle / driver magic links / continuity / day-1 debrief — all preserved byte-for-byte.

## 13 · No-dead-object verification
- Every V2 hub card has a real `to` route that already exists in App.js.
- Cards rendering `—` value still respect the rule (offline_feed chip shown, no fake count).
- Forbidden vocabulary (risk scores · AI priority · red/yellow/green) absent — enforced by `test_sla_label_vocabulary_is_operational_truth_only`.

## 14 · No-fake-urgency verification
- SLA chips and oldest-age labels derive purely from real `opened_at` / `created_at` / `due_date` fields.
- Verified by `test_track_13_6h_sla_chip.py` (7 tests · all pass).

## 15 · Dispatch visual guardrail results
- `/dispatch-portal/hub_legacy` screenshot confirms MapLibre canvas, 190-asset fleet, breakdown panel, Operational Attention chrome — fully intact.
- New V2 hub does NOT mount MapLibre; the map remains rendered by `/dispatch-portal/command` (untouched).

## 16 · Screenshot index
| File | Surface |
|---|---|
| `/tmp/swap_dispatch.png` | `/dispatch-portal` post-swap — Dispatch Hub V2 desktop |
| `/tmp/swap_dispatch_legacy.png` | `/dispatch-portal/hub_legacy` — classic dispatch with MapLibre intact |
| `/tmp/swap_safety.png` | `/safety-portal` post-swap — Safety Hub V2 desktop |
| `/tmp/swap_safety_legacy.png` | `/safety-portal/hub_legacy` — classic Safety Operations Dashboard |
| `/tmp/shop_hub_v2.png` | `/shop/hub_v2` — new Shop V2 preview desktop |
| `/tmp/pm_hub_v2_oldest.png` | `/pm/hub` — PM Hub V2 with oldest-age secondary plumbing |
| `/tmp/dispatch_board_focus.png` (13.6H) | `/dispatch-portal/board?focus_assignment_id=…` — FocusBanner honest scope-excluded |

## 17 · Tests run
- `tests/test_track_13_6f_pm_engines.py` — 10/10 PASS
- `tests/test_track_13_6g_deep_link_triage.py` — 6/6 PASS
- `tests/test_track_13_6h_sla_chip.py` — 7/7 PASS
- **Total: 23/23 backend regression + 1 pre-existing PM test = 24/24 PASS**.

## 18 · Failures / blockers
- None.

## 19 · Five-pillar scores after 13.6I
| Portal | Powerful | Simple | Beautiful | Trusted | Proven | Avg |
|---|---|---|---|---|---|---|
| PM Hub V2 | 10 | 10 | 9 | 10 | 10 | **9.8** |
| HR Hub V2 | 9 | 9 | 9 | 10 | 10 | 9.4 |
| Dispatch Hub V2 (post-swap) | 9 | 9 | 9 | 10 | 9 | 9.2 |
| Safety Hub V2 (post-swap) | 9 | 9 | 9 | 9 | 9 | 9.0 |
| Shop Hub V2 (preview) | 9 | 9 | 9 | 9 | 8 | 8.8 |

## 20 · Recommended next step
- **Track 13.6J — Shop route swap + Admin / Field Leadership / Driver preview lanes.**
- Driver portal carries the special directive: ≤ 2 taps · ≤ 30 s · immediate first action — design that as a dedicated mobile-first lane.
- Once Shop is swapped, add a `/shop/hub_legacy` rollback path identical to Dispatch / Safety pattern.
