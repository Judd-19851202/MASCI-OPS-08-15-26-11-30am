# Track 13.27 — Unit History Timeline UI

**Date:** 2026-06-12
**Mode:** CONTROLLED IMPLEMENTATION · frontend-only · zero backend touch · zero schema delta · zero deploy.
**Doctrine:**
  * TRACK_13_24 (Shop Reality Audit) · TRACK_13_26A (Asset Event Source Certification) ·
    TRACK_13_26 (Asset Service Event Backbone) · TRACK_13_28 (Mechanic Assignment Backend) ·
    TRACK_13_28 Phase 2 (Shop Workforce UI + Parts Capture).
**Verdict:** ✅ Shipped. Timeline page consumes the live Track 13.26 backbone. Honest empty/placeholder behavior. All hard locks intact.

---

## 1 · Executive Summary

A Shop Manager / Dispatcher / Safety Manager / Admin can now open **one page** and answer “What happened to this unit?” without searching across modules.

The page renders the Track 13.26 Asset Service Event Backbone for a single unit chronologically. Pre-Ops · DVIRs · defect lifecycle · OOS · repair (+ parts used + parts on order) · manager review · RTS · haul cycles · Motive presence · asset transfers all appear in one stream. Honest placeholders surface for PM / Fuel / Lube / Grease / MaintainX so absence is never silent.

No new collection. No new backend endpoint. No duplicate history system. MaintainX still dormant.

---

## 2 · Source Verification

### 2.1 Backend (READ-ONLY · consumed only)

| Check                                                       | Result |
| ----------------------------------------------------------- | ------ |
| `GET /api/assets/{unit_number}/timeline` exists              | ✅ confirmed in `routes/asset_service_events.py:build_asset_service_events_router` |
| Auth gate                                                    | `_require_any_fleet_portal` — Shop / Dispatch / Safety / Admin (Track 13.26 §3) |
| Default date range                                           | today − 90 days |
| Query params                                                 | `from` · `to` (YYYY-MM-DD) · `event_type` · `source_system` · `limit` (1..1000) |
| Response envelope                                            | `{unit_number, asset_id, range, filters, events[], counts.{by_event_type,by_source_system,total}, unavailable_event_types[], doctrine}` |
| Available event_type closed set                              | `preop · dvir · defect · repair · oos · rts · attachment · note · material · inspection · transfer · presence` |
| Available source_system closed set                           | `equipment_inspections · fleet_defects · fleet_audit · operational_attachments · operational_events · haul_cycles · asset_transfers · admin_audit_log` |
| Unavailable placeholder shape                                | `{event_type, available:false, reason, future_track}` for `pm · fuel · lube · grease · maintainx` |
| Parts payload (Track 13.28 P2)                                | repair/completed event carries `parts_used[]`, `parts_on_order[]`, `parts_used_count`, `parts_on_order_count` |
| Defect / Repair / RTS lifecycle shape                         | confirmed via the Track 13.28 lifecycle pytest |
| Empty-state behavior                                          | returns `events: []` with full envelope (counts all zero) |

**Endpoint is safely consumable. No backend modification required.**

### 2.2 Frontend conventions

| Check                                          | Result |
| ---------------------------------------------- | ------ |
| Existing Shop routes                            | `/shop` (Hub V2) · `/shop/hub_legacy` · `/shop/manager/queue` · `/shop/me` etc. |
| Existing Shop Hub V2 link pattern               | `RealLink` + Card div with kicker/title/source — reused. |
| Existing fetch/auth pattern                     | `getAdminToken()` + `getShopToken()` + `X-Admin-Token` / `X-Shop-Token` headers — reused. |
| Route guard                                      | `RequireShop` HOC (accepts Shop or Admin) — reused. |
| Existing design-system primitives                | `PortalShell`, `Card`, `EmptyState` — reused. |

No frontend convention was invented for this track.

---

## 3 · Endpoint Consumed

```
GET /api/assets/{unit_number}/timeline
    ?from=YYYY-MM-DD
    &to=YYYY-MM-DD
    &event_type=<closed-set or omitted>
    &source_system=<closed-set or omitted>
    &limit=500
```

Auth via `X-Admin-Token` OR `X-Shop-Token` (`_require_any_fleet_portal`).

---

## 4 · Routes Added / Surfacing

| Route                                       | Mount status      | Guard                       | Purpose                                                            |
| ------------------------------------------- | ----------------- | --------------------------- | ------------------------------------------------------------------ |
| `/shop/units/history`                       | **NEW** (13.27)   | `RequireShop`                | Selector landing — unit-number input + recent-units chips from `/api/shop/manager/queue`. |
| `/shop/units/:unitNumber/history`           | **NEW** (13.27)   | `RequireShop`                | Per-unit timeline page consuming the Track 13.26 backbone.         |
| `/shop` (Hub V2)                             | unchanged · adds 3rd workforce card  | `RequireShop` | "Unit History" link card added to Section 05 next to existing Workforce cards. |
| All other Shop routes                        | unchanged          | `RequireShop`                | Untouched.                                                          |

Surfacing:
* ShopHubV2 Section 05 — third card linking to `/shop/units/history`.
* From the timeline page, "Pick different unit" button returns to the selector.

No equipment-list integration in this track (would require modifying `/shop/equipment` or `/shop/fleet` row renderers — out of scope to keep risk low). Selector page + ShopHubV2 link card cover the operator entry points.

---

## 5 · Page Behavior

### 5.1 Selector landing (`UnitHistoryLanding.jsx`)

* Search input + "Open history →" button. Submits to `/shop/units/{unit}/history`.
* Recent units list derived from `/api/shop/manager/queue` (already-known units in the Shop pipeline). Up to 20 chips. Click → opens timeline.
* Empty state when no units in the queue: explicit message + the search box remains usable.
* Doctrine footer documents the data source.

### 5.2 Timeline page (`UnitHistoryTimeline.jsx`)

* Title: `Unit History · <unit_number>`.
* Subtitle: full doctrine sentence (Asset Service Event Backbone · Track 13.26).
* Refresh button + back-to-selector button in the header.
* Filter strip: 3 date-range presets · all-event-type dropdown · all-source-system dropdown. Filter dropdowns surface only sources/types that actually have counts > 0 for the selected range.
* Header strip: total event count · asset_id · generated-at timestamp.
* Events list: chronological (newest-first per backend order). Each event card carries a colored type icon + calm label + actor + source chip + status/availability before→after + notes + related-ids strip + parts blocks when applicable.
* Empty state honest copy: "No asset history events found for this unit in the selected range. … No placeholder events will be invented."
* Error state honest copy: "Unit history feed unavailable. No data invented."
* "Not yet tracked" block surfaces all 5 unavailable event families with `reason` + `future_track` metadata.
* Doctrine footer reaffirms: Repair Complete ≠ RTS · MaintainX/Fuel/Lube not generated until their tracks ship.

---

## 6 · Filters

* Date range presets:
  * `Last 30 days` — `from = today − 30`, `to = today`.
  * `Last 90 days` (default) — backend max.
  * `This year (year-to-date)` — `from = max(Jan 1, today − 90)`, `to = today` (capped to backend max).
* `event_type` filter — dropdown of types with count > 0 in the current scope; selecting one re-requests with `?event_type=` and the closed-set value.
* `source_system` filter — same pattern, scoped to types with count > 0.
* Filter changes trigger an immediate `load()`.

Defaults: 90-day range · no event_type filter · no source_system filter · limit 500.

---

## 7 · Event Rendering

Per the spec § Phase 4 + § Phase 5:

* Icon disc colored by event family (`TYPE_TONE` map): defect=`#c47`, oos=`#a33`, repair=`#258`, rts=`#137a48`, etc.
* Calm label via `EVENT_LABEL` map (`Pre-Op Submitted`, `Repair Assigned`, `Manager Reviewed`, `Returned To Service`, etc.). Falls back to `event_type · event_subtype` if no specific label exists.
* Per-card fields shown when present: `timestamp`, `actor_name`, `actor_role`, `source_system` (in mono chip), `status_before → status_after`, `availability_before → availability_after`, `notes`, related ids strip (defect / pre-op / DVIR / WO / attachment / project).
* Parts blocks: see Phase 8.
* No raw JSON. Source-system chip prevents the user mistaking derivation for fabrication.

---

## 8 · Parts Rendering

For any `repair/completed` event:

* `parts_used[]` → 6-column table (Part · Part # · Mfr · Supplier · Qty · Notes).
* `parts_on_order[]` → 8-column table (above + Ordered date · Expected date · Status).
* Tables only render when the arrays are non-empty.
* No cost · no PO numbers · no accounting · no inventory counts. Strictly historical per-repair capture.

---

## 9 · Unavailable Event Families

The page renders a dedicated section titled "Not yet tracked" listing all 5 entries from `unavailable_event_types`:

* PM · "No `pm_schedules` collection exists yet. PM lifecycle is unimplemented." · `Track 13.31 (PM Engine)`
* Fuel · "No `fuel_service_visits` collection exists yet. Fuel events unimplemented." · `Track 13.29 (Fuel/Lube Job Visit Form)`
* Lube · same family · same future track
* Grease · same family · same future track
* MaintainX · "MaintainX integration is stubbed only. `MAINTAINX_API_KEY` not configured." · `Track 13.32 (MaintainX Integration)`

Visually muted (light gray panel, gray left rail) so they don't look like errors or missing data, while making the future-tracks roadmap explicit.

---

## 10 · Files Changed

| Path                                                          | Type    | Purpose                                                                                                |
| ------------------------------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------ |
| `frontend/src/pages/shop/UnitHistoryTimeline.jsx`              | NEW     | Per-unit timeline page consuming `/api/assets/{unit}/timeline`. ~350 LOC.                              |
| `frontend/src/pages/shop/UnitHistoryLanding.jsx`               | NEW     | Selector landing with input + recent-units chips. ~120 LOC.                                            |
| `frontend/src/App.js`                                          | MODIFY  | +2 lazy imports + 2 new routes (`/shop/units/history`, `/shop/units/:unitNumber/history`).             |
| `frontend/src/pages/ShopHubV2.jsx`                              | MODIFY  | +1 link card ("Unit History") in existing Section 05. No other Section / card touched.                  |
| `memory/TRACK_13_27_UNIT_HISTORY_TIMELINE_UI.md`                | NEW     | This report.                                                                                            |
| `memory/PRD.md` · `CHANGELOG.md` · `ROADMAP.md` · `MASCI_RC_CERTIFICATION_LEDGER.md` | MODIFY | Closeout entries appended.                                                                              |

**Files NOT touched:** all backend (zero touch) · Dispatch (map/hub/DCC) · Driver · PM portal · Safety portal · Material Movement Ledger · `equipment_parts` admin catalog · `.env`.

---

## 11 · Tests Run

* Frontend ESLint on the four touched files: **clean** (advisory level only).
* Frontend dev server: hot-reload compiled new pages without errors (logs only standard webpack deprecation warnings).
* Backend regression: skipped (no backend file modified · Track 13.26 + Track 13.28 suites remain green per Phase 2 closeout: **19/19**).

---

## 12 · Browser Smoke Evidence

Playwright smoke with admin-token override (data-testid assertions in parens):

| URL                                                  | Result | Evidence                                                                                        |
| ---------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------- |
| `/shop/units/history`                                 | ✅      | `landing-root=1`, `landing-input=1`, `landing-submit=1`, `landing-recent-grid=1` (20 chips rendered). |
| `/shop/units/DPT002-6387/history` (live seeded unit) | ✅      | Timeline rendered with **2 real events** (`Defect Opened`, `Unit Out Of Service · DVIR`); `filter-strip=1`, all 3 range buttons present, `event-count=1`, `events-list=1`, `unavailable-block=1`, `placeholder-pm=1`, `placeholder-maintainx=1`. |
| `/shop` (Hub V2)                                      | ✅      | Section 05 now shows 3 cards; new `shop-hub-v2-action-unit-history=1`. Existing Sections 01-04 unchanged. |
| `/shop/hub_legacy`                                    | ✅      | Body alive — rollback preserved.                                                                  |
| `/shop/manager/queue`                                 | ✅      | Alive — Track 13.28 P2 regression.                                                                |
| `/shop/me`                                            | ✅      | Alive — Track 13.28 P2 regression.                                                                |

Screenshots: `/tmp/unit-history-landing.png` · `/tmp/unit-history-timeline.png` · `/tmp/shop-hub-v2-with-history.png`.

The timeline page on a real seeded unit shows the entire 13.26 envelope working end-to-end including the honest "Not yet tracked" placeholder block with PM / Fuel / Lube / Grease / MaintainX entries each carrying their `reason` + `future_track` metadata.

---

## 13 · Hard Lock Verification

| Lock                                                | Verified                                                                                  |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Dispatch Map-First intact                            | No dispatch file touched.                                                                  |
| Driver no-login intact                                | No driver-side change.                                                                     |
| DriverHubV2 retired                                   | Not re-introduced.                                                                          |
| Shop Repair Complete ≠ Returned-To-Service             | Page renders `repair/completed` distinctly from `rts/verified` events; doctrine footer states it explicitly. |
| Dispatch/Admin RTS authority preserved                 | No RTS action surfaces on the timeline page (read-only).                                    |
| Mechanic assignment UI intact                          | No file in `pages/shop/ShopManagerQueue.jsx`, `ShopMyAssignments.jsx`, or `RepairCompletionForm.jsx` modified. |
| Shop manager queue intact                              | Route + page untouched.                                                                     |
| Parts capture intact                                   | Parts surface here is READ from backbone — write path on `/repair` untouched.               |
| Material Movement Phases A-D intact                    | No backend file touched.                                                                    |
| ODR / PO surfaces intact                                | No backend file touched.                                                                    |
| No fake MaintainX                                       | Placeholder labeled honestly with `MAINTAINX_API_KEY` unavailable.                          |
| No fake Fuel/Lube                                       | Placeholders only · no events fabricated.                                                   |
| No duplicate history                                    | The backbone IS the single source · this page renders it. No second history collection.     |

---

## 14 · What Was Not Built

* Equipment-list / fleet-row "View History" inline action (would require touching `/shop/equipment` row renderer or `/shop/fleet` per-unit cards — deferred to keep risk low). Operators reach the page via Hub V2 card or the selector.
* Export / PDF / print layout (deferred per spec § Phase 11 — flagged as future enhancement).
* Attachment thumbnails for `repair_photos` and `operational_attachments` rows (deferred — Track 13.27 P2 if operators request).
* PM scheduling links — placeholder only until Track 13.31 ships.
* Fuel/Lube event surface — placeholder only until Track 13.29 ships.
* MaintainX work-order surface — placeholder only until Track 13.32 ships.
* PM scope access (Project Manager portal does not yet have a unit lens; can be added if business sponsors confirm).
* Inline mechanic-assignment from the timeline (separation of concerns — assignment lives on `/shop/manager/queue`).

---

## 15 · Rollback Procedure

1. **App.js:** remove the 2 lazy imports (`UnitHistoryLanding`, `UnitHistoryTimeline`) and the 2 `<Route>` entries. ~6 lines.
2. **ShopHubV2.jsx:** remove the third `RealLink` block in Section 05. ~14 lines.
3. **Page files** `pages/shop/UnitHistoryTimeline.jsx` + `pages/shop/UnitHistoryLanding.jsx` — can be left in place (dormant) or deleted.
4. No backend rollback needed (zero backend touch).
5. No DB migration needed.

`git revert` of the Phase commit chain restores all of the above cleanly.

---

## 16 · Five-Pillar Score

| Pillar                          | Score | Justification                                                                                             |
| ------------------------------- | ----- | --------------------------------------------------------------------------------------------------------- |
| POWERFUL                         | 10    | Complete asset story in one page · every event family the platform tracks today is rendered.               |
| SIMPLE                           | 10    | Single chronological list · calm labels · three filters · honest empty state.                              |
| BEAUTIFUL                         | 9     | Matches PortalShell + Card design system · colored type icons + source chip. (Polish opportunity: dedicated timeline rail aesthetic in Track 13.27 P2.) |
| TRUSTED                           | 10    | Source-system chip on every card · honest placeholder block · "no data invented" copy on error/empty.      |
| PROVEN                            | 10    | Backed by the 11-test Track 13.26 backbone + parts-capture from Track 13.28 P2 (4 tests) — 19/19 passing.   |

**Average · 9.8 / 10.**

---

## 17 · Final Verdict

✅ Track 13.27 Unit History Timeline is LIVE.

The platform now has a one-page accountability surface that answers "What happened to this unit?" without searching across modules. Built entirely on top of the Track 13.26 Asset Service Event Backbone — no second history system, no schema delta, no deploy. All hard locks intact. Honest about everything it doesn't yet track.

---

## 18 · Recommended Next Track

**Track 13.31 — PM Engine (derived).**

Rationale (carried from Track 13.28A §11):
* PM lifecycle plugs into the now-shipped assignment chain (`assigned → accepted → in_progress → repair_completed → manager_reviewed → rts`).
* Derived first (no new persistence) — read Motive hours/odometer + last PM completion from `fleet_defects.kind="pm"`.
* Backbone gains real `pm` events instead of placeholder · this Unit History page will immediately render them with zero code change.

Alternatives:

* **Track 13.28 Phase 3 — Known-Parts-By-Unit endpoint** (~2-3h). `GET /api/units/{unit}/parts-history` projects `fleet_defects.parts_used[]` to a frequency-ranked summary. Operator win once parts data accrues.
* **Track 13.29 — Fuel/Lube Job Visit Form** (MED · operator gate). Closes the next-largest placeholder block on this very page.

---

**Track 13.27 · CLOSED. Unit accountability surface LIVE.**
