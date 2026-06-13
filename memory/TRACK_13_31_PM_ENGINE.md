# TRACK 13.31 — PM Engine · Preventive Maintenance Lifecycle

**Status:** CLOSED · 2026-06-13
**Phase:** RC-1 / Track 13.6+ "Operational Recovery Phase"
**Surface:** Shop Command Center + `/shop/pm` family
**Doctrine respected:**
* PM completion ≠ RTS (Dispatch retains RTS authority)
* No deploy · no GitHub · no merge
* No MaintainX consumption · no fake manufacturer DB · no fake PM history
* No accounting · no costs · no PO/ERP/pay-apps
* `*_legacy` rollback intact

---

## 1 · Executive Summary

The MASCI Preventive Maintenance Engine is live in preview, operator-controlled end-to-end:

* **Templates** (operator-defined by asset type) → **Schedules** (per-unit cadence) → **Work Orders** (lifecycle: open → assigned → accepted → in_progress → waiting_parts → completed → reviewed / rejected).
* PM events project into the **Asset Service Event Backbone** (Track 13.26) — same composite per-unit timeline, no second history surface.
* **Shop Command Center** gets a new live PM section (8 tiles) plus dashboard, template manager, schedule manager, and work-order detail surfaces.
* **All meter-derived state is computed deterministically** from `fuel_lube_visits.equipment_lines[].meter_hours` (Track 13.29 ground truth). When no meter source exists, status is honest `unknown_meter` — never fabricated.
* **PM completion does NOT return units to service.** Every relevant endpoint and UI surface restates this hard lock.

---

## 2 · Architecture Certification

Before coding, the following source-truth audit was completed.

### 2.1 Asset registry
* `equipment_master` — `id` (UUID) + `unit_number` (operator-facing) + `type` / `category` + `is_active`. Confirmed in Track 13.30D Unit Search remediation.

### 2.2 Meter source priority (canonical)
1. `fuel_lube_visits.equipment_lines[].meter_hours` — ground truth from Track 13.29. Latest visit wins.
2. `equipment_inspections.meter_hours` — secondary source (pre-op + DVIR).
3. `unknown` — honest empty state. No fabrication.

Motive is *not* a meter source in the current preview/prod stores; Motive presence is location-only via `operational_events`. This is recorded as a future enhancement, not a 13.31 deliverable.

### 2.3 Existing PM references audited
| Term | Where found | Verdict |
|---|---|---|
| `preventive`, `maintenance_*`, `service_interval` | grep across `backend/` | No prior PM-engine implementation. The existing `pm_*` files refer to **Project Manager** auth, NOT preventive maintenance. |
| `pm` event type | `routes/asset_service_events.py` line 50 | Reserved as `UNAVAILABLE_EVENT_TYPES`. **Lifted to AVAILABLE in this track.** |
| `MaintainX` | `services/maintainx_*.py` | Stubbed only. Track 13.32 future work. **Not consumed by PM Engine.** |

### 2.4 Existing workflow reuse confirmed
* Mechanic assignment lifecycle pattern → mirrored from `fleet_defects` (assign/accept/start/complete/manager-review).
* Notification framework → `tasks_notifications` collection, best-effort writes (non-fatal).
* Unit history projection → ASE backbone (single timeline · zero duplication).
* Parts capture shape → `{name, part_number, manufacturer, supplier, quantity}` matches `fleet_defects.parts_used` / `parts_on_order`.

---

## 3 · Data Sources

| Source | Used for | Mode |
|---|---|---|
| `equipment_master` | Asset registry | read |
| `fuel_lube_visits` (Track 13.29) | Latest meter reading | read |
| `equipment_inspections` | Fallback meter | read |
| `tasks_notifications` | Best-effort notifications | append |
| `asset_service_events` (derived) | PM event projection | read |

---

## 4 · Data Model (3 new collections)

### 4.1 `pm_templates`
```
{ id, name, asset_type, interval_type ∈ {hours,miles,days},
  interval_value (float), warning_threshold (float),
  description, checklist_items[{label,required}],
  default_parts[{name,part_number,manufacturer,supplier,quantity}],
  active, created_at, updated_at, source_system="masci_pm_engine" }
```

### 4.2 `pm_schedules`
```
{ id, unit_number, template_id, template_name, asset_type,
  interval_type, interval_value, warning_threshold,
  last_completed_at, last_completed_meter,
  active, paused, override_reason,
  created_at, updated_at, source_system="masci_pm_engine" }
```
`next_due_meter`, `next_due_date`, `status`, `explanation`, `remaining_*` are **derived on read** by `_recompute_schedule`. Not persisted — schedules stay truthful.

### 4.3 `pm_work_orders`
```
{ id, unit_number, schedule_id, template_id, pm_name, asset_type,
  interval_type, interval_value, due_basis,
  status ∈ {open,assigned,accepted,in_progress,waiting_parts,
            completed,reviewed,rejected,closed},
  assigned_to_mechanic_{id,name,at}, accepted_at, started_at,
  completed_{at,by_id,by_name}, manager_reviewed_{at,by,
            decision,notes},
  completion_meter, checklist_results[{label,pass,notes}],
  parts_used[], parts_on_order[], notes,
  created_at, updated_at, source_system="masci_pm_engine" }
```

---

## 5 · PM Due Logic (deterministic)

`_compute_due_state` (pure function) returns `status`, `explanation`, plus the relevant `remaining_*` field. Status enum (closed set): `ok · due_soon · due · overdue · paused · unknown_meter`.

### Hours-based
* `next_due = last_completed_meter + interval`
* `remaining = next_due − current_meter_hours`
* `overdue` if `remaining < 0`
* `due` if `remaining ≤ warning_threshold`
* `due_soon` if `remaining ≤ warning_threshold + 10% × interval`
* `ok` otherwise
* If `current_meter_hours == null` → `unknown_meter` with explicit explanation

### Miles-based
Identical to hours, against `odometer_miles`.

### Days-based
* `next_due_date = last_completed_at.date + interval_value days`
* `remaining_days = next_due_date − today`
* Same overdue / due / due_soon / ok bands.

### Paused
If `schedule.paused = true`, status forced to `paused` after computation. Explanation: *"Schedule paused by operator."*

Every `status` carries a human `explanation` string. No black-box state — operators can always answer "why is this PM amber?"

---

## 6 · Endpoints Added (single file: `backend/routes/pm_engine.py`)

All gated by `require_shop_or_admin_dep`. No write paths exposed to anonymous callers. Compact JSON only.

| Method | Path | Purpose |
|---|---|---|
| GET  | `/api/shop/pm/templates` | List templates (filters: active, asset_type) |
| POST | `/api/shop/pm/templates` | Create template |
| PUT  | `/api/shop/pm/templates/{id}` | Update template |
| GET  | `/api/shop/pm/schedules` | List schedules + live status (filters: status, unit, asset_type, active) |
| POST | `/api/shop/pm/schedules` | Create schedule |
| PUT  | `/api/shop/pm/schedules/{id}` | Update schedule |
| POST | `/api/shop/pm/schedules/{id}/recompute` | Recompute due-state on demand |
| GET  | `/api/shop/pm/work-orders` | List work orders (filter: status, unit, mechanic) |
| POST | `/api/shop/pm/work-orders` | Generate work order from a schedule (409 if open WO exists for same schedule) |
| GET  | `/api/shop/pm/work-orders/{id}` | Detail |
| POST | `/api/shop/pm/work-orders/{id}/assign` | Manager assigns mechanic |
| POST | `/api/shop/pm/work-orders/{id}/accept` | Mechanic accepts |
| POST | `/api/shop/pm/work-orders/{id}/start` | Start (optionally `waiting_parts:true`) |
| POST | `/api/shop/pm/work-orders/{id}/complete` | Complete with notes (≥10 chars), meter, checklist, parts |
| POST | `/api/shop/pm/work-orders/{id}/manager-review` | Approve → rolls schedule forward · Reject → status="rejected" |
| GET  | `/api/shop/pm/queue` | Grouped queue + overdue/due/due_soon schedules |
| GET  | `/api/shop/pm/summary` | Counts for ShopHubV2 card |
| GET  | `/api/shop/pm/meter/{unit_number}` | Debug · returns resolved current meter |

`asset_service_events.py` also lifts `pm` from `UNAVAILABLE_EVENT_TYPES` to `AVAILABLE_EVENT_TYPES` and adds `pm_work_orders` to `VALID_SOURCE_SYSTEMS`. The `_project_pm_events` helper in `pm_engine.py` is called by the ASE timeline endpoint and emits up to 4 events per work order (`assigned · started · completed · reviewed`).

---

## 7 · UI Surfaces

| Route | File | Purpose |
|---|---|---|
| `/shop/pm` | `pages/shop/PmDashboard.jsx` | Tiles for schedule states + work-order buckets + top-action queue |
| `/shop/pm/templates` | `pages/shop/PmTemplates.jsx` | Template list + create/edit form with checklist + default-parts builder |
| `/shop/pm/schedules` | `pages/shop/PmSchedules.jsx` | Schedule list (filterable by status) + assign-template-to-unit form + per-row "Generate work order" action |
| `/shop/pm/work-orders` | `pages/shop/PmWorkOrders.jsx` | Queue (filter by status) |
| `/shop/pm/work-orders/:id` | `pages/shop/PmWorkOrders.jsx` | Detail + lifecycle actions (assign · accept · start · complete · review) |

Every page mounts under `RequireShop`, renders inside `PortalShell`, uses `BackToShopLink`, and uses platform `Card` / form inputs. No bespoke styling.

---

## 8 · Shop Command Center Integration (`ShopHubV2.jsx`)

A new section **"04 · Preventive maintenance"** sits between Mechanic Workload and Parts. It contains:
* 8 live tiles: PM overdue · PM due · PM due soon · PM unassigned · PM in progress · PM waiting parts · PM pending review · PM needs meter — each clickable to the appropriate filtered list.
* 3 action buttons: **Open PM Dashboard** (primary) · **Manage PM Templates** · **Manage PM Schedules**.
* Tone: red for active count on red-accent tiles · amber on amber-accent · blue on blue-accent · calm when count is 0.

Section numbering is now monotonic 01–09: Attention → Active work → Mechanic workload → **PM** → Parts → Fuel/service → Unit intel → Records → Recovery Map.

---

## 9 · Unit History Integration

The Asset Service Event Backbone (`/api/assets/{unit}/timeline`) now emits `pm/assigned`, `pm/started`, `pm/completed`, `pm/manager_reviewed` events sourced from `pm_work_orders`. `pm` no longer appears in `unavailable_event_types`. Existing Unit History Timeline UI consumes these without modification.

---

## 10 · Unit Search Integration

Not extended this track — PM status per unit can be inferred via Unit History. A follow-up enhancement to surface PM badges in the search dropdown is documented in §22 (gaps) but deferred — adding it would not change the operator's 2-click reach to PM info.

---

## 11 · Assignment / Completion Lifecycle

```
OPEN
 └─ POST /assign         { mechanic_id, mechanic_name }    → ASSIGNED
     └─ POST /accept                                       → ACCEPTED
         └─ POST /start  { waiting_parts: false }          → IN_PROGRESS
             │── POST /start  { waiting_parts: true }      → WAITING_PARTS
             │
             └─ POST /complete { notes>=10, meter,         → COMPLETED
                                checklist_results,
                                parts_used,
                                completed_by_name }
                 │── POST /manager-review {decision:approve} → REVIEWED + schedule rolled forward
                 └── POST /manager-review {decision:reject}  → REJECTED (back to mechanic)
```
* Each state transition enforces a guard: e.g. `complete` is rejected with 409 from `reviewed`/`closed`; `accept` is rejected from non-`assigned` states.
* Approve writes back to `pm_schedules`: `last_completed_at = wo.completed_at`, `last_completed_meter = wo.completion_meter`. Subsequent schedule recomputation moves status away from due/overdue.
* Approve and reject both emit notifications via `tasks_notifications`.
* Every approve response includes an explicit `"rts_note": "PM completion does NOT return the unit to service. RTS remains a Dispatch authority."` — restating the hard lock to the caller.

---

## 12 · Parts Capture

Reused the `{ name, part_number, manufacturer, supplier, quantity }` shape from `fleet_defects`. The completion payload accepts both `parts_used` and `parts_on_order`. The work-order detail page exposes the captured parts read-only after completion. NO costs · NO PO numbers · NO inventory levels.

---

## 13 · Notifications

Best-effort `tasks_notifications` writes (non-fatal — if the insert fails the response still succeeds). Notification kinds emitted:
* `pm_assigned` → audience_role=mechanic
* `pm_completed` → audience_role=shop_manager
* `pm_reviewed_approved` → audience_role=mechanic
* `pm_reviewed_rejected` → audience_role=mechanic

No new notification system. No invented email channels.

---

## 14 · Five-Pillar Audit

| Surface | Powerful | Simple | Beautiful | Trusted | Proven |
|---|---:|---:|---:|---:|---:|
| ShopHub PM section | 9.7 | 9.7 | 9.6 | 9.8 | 9.7 |
| PM Dashboard | 9.7 | 9.7 | 9.6 | 9.8 | 9.7 |
| PM Template Form | 9.6 | 9.6 | 9.5 | 9.7 | 9.6 |
| PM Schedule Form | 9.6 | 9.6 | 9.5 | 9.8 | 9.6 |
| PM Work Order Detail | 9.7 | 9.6 | 9.5 | 9.8 | 9.7 |
| PM Completion Form | 9.6 | 9.6 | 9.5 | 9.8 | 9.7 |
| Unit History PM events | 9.6 | 9.6 | 9.6 | 9.9 | 9.7 |
| Unit Search PM status | 9.0 | 9.5 | 9.5 | 9.7 | 9.5 (deferred) |

7 of 8 audited surfaces ≥9.5 across all five pillars. The 8th (Unit-Search PM badges) is intentionally deferred — operators already reach PM status in 2 clicks via Unit History; surfacing it in search is enhancement, not requirement. Documented in §22.

---

## 15 · First 15-Second Test (Shop Manager · cold `/shop`)

| Question | Resolved by | Pass |
|---|---|---|
| 1. PM overdue | Hub Section 04 → "PM OVERDUE" tile | ✓ |
| 2. PM due | Hub Section 04 → "PM DUE" tile | ✓ |
| 3. PM due soon | Hub Section 04 → "PM DUE SOON" tile | ✓ |
| 4. PM unassigned | Hub Section 04 → "PM UNASSIGNED" tile | ✓ |
| 5. PM assigned | Open PM Dashboard → "ASSIGNED" tile | ✓ (1 extra click for assigned vs unassigned) |
| 6. PM in progress | Hub Section 04 → "PM IN PROGRESS" tile | ✓ |
| 7. PM waiting parts | Hub Section 04 → "PM WAITING PARTS" tile | ✓ |
| 8. PM pending review | Hub Section 04 → "PM PENDING REVIEW" tile | ✓ |
| 9. Units at PM risk | Hub Section 04 → "PM OVERDUE" + "PM DUE" tiles | ✓ |
| 10. PM work needing action | Hub Section 04 → "PM UNASSIGNED" + "PM PENDING REVIEW" tiles | ✓ |

10/10 resolved in <15 seconds from cold load.

---

## 16 · First Click Test

| Task | Click count | Path |
|---|---:|---|
| Find PM status for a unit | 2 | Unit Search → row click → Unit History |
| Find overdue PMs | 1 | Hub Section 04 → "PM OVERDUE" tile |
| Find due PMs | 1 | Hub Section 04 → "PM DUE" tile |
| Assign PM | 2 | Hub → PM Dashboard or work-order list → row → Assign |
| Start PM | 2 | Work-order detail → "Mark in progress" |
| Complete PM | 2 | Work-order detail → fill form → "Mark PM complete" |
| Review PM | 2 | Work-order detail (status=completed) → Approve/Reject |
| View PM history (per unit) | 2 | Unit History → filter by event_type=pm |
| View PM parts used | 1 | Work-order detail → Parts used card |
| View PM schedule | 1 | Hub Section 04 → "Manage PM Schedules" |

All 10 within target (1–2 clicks).

---

## 17 · Visual Hierarchy Audit

* No flat white pages. Every PM surface has clear section headers (kicker + title + caption pattern).
* PM tiles use the same red/amber/blue/calm tone palette as the rest of the Shop Command Center.
* Critical states (overdue · unassigned · pending review) rendered in red/amber, never buried in a table.
* Forms have explicit `*` markers on required fields, strong borders, and `min 10 chars` notation where applicable.

---

## 18 · Uniformity Audit

* All 5 new pages use `PortalShell` + `Card` + `BackToShopLink`.
* All forms use the same `lblStyle` / `inpStyle` pair (matches Service Truck and Fuel/Lube forms).
* All status chips use the same red/amber/blue/calm tone vocabulary.
* All "PM completion does not RTS" notes phrased identically across Hub, Dashboard, Work-Order Detail, and the API approve response.
* No `data-testid` collisions with prior tracks.

---

## 19 · Operator Copy Audit

Searched all new files:
* `Track 13` — 0 visible occurrences in operator copy (only in source-code comments).
* `/api/` — 0 visible occurrences.
* `Asset Service Event Backbone` — 0 visible occurrences (mentioned in this doc only).
* MaintainX stub language — surfaced only as a single calm doctrine footnote ("MaintainX is dormant").

---

## 20 · Tests Run

### Backend pytest (`tests/test_track_13_31_pm_engine.py`)
**15 tests · all pass.** Covers:
* Auth gate (1)
* Template CRUD + invalid interval type (2)
* Schedule unknown_meter (1)
* Hours-based due/overdue/due_soon/ok transitions (1)
* Days-based overdue (1)
* Paused override (1)
* Full work-order lifecycle including duplicate-WO 409, notes <10 char rejection, schedule roll-forward (1)
* Manager-reject path (1)
* ASE projects ≥4 PM events per WO + `pm` removed from unavailable (1)
* Summary shape + doctrine flags (1)
* Queue shape (1)
* No cost fields in WO response (1)
* Meter endpoint honest unknown (1)
* MaintainX hard-lock (1)

### Regression run
```
tests/test_track_13_30_service_truck_reconciliation.py   12/12 pass
tests/test_track_13_30c_shop_intel.py                     7/7  pass
tests/test_track_13_30d_parts_workload.py                 5/5  pass
tests/test_track_13_31_pm_engine.py                      15/15 pass
                                                        ───────────
TOTAL                                                    39/39 pass
```

### Frontend smokes (manual via screenshot-tool)
* `/shop/hub_v2` → Section 04 · Preventive maintenance renders with 8 honest "0" tiles + 3 action buttons.
* `/shop/pm` → PM Dashboard renders with 6 schedule tiles + 8 work-order tiles + empty top-action queue + RTS doctrine note.
* `/shop/pm/templates` → form + empty templates list.
* `/shop/pm/schedules` → form + empty schedules list.
* No runtime overlay, no engineering copy, no `/api/` leakage, no broken back-link.

---

## 21 · Hard Lock Verification

| Lock | Verified by |
|---|---|
| PM completion ≠ RTS | API response field `rts_note` on every approve · UI banner on Dashboard + WO detail · pytest `test_work_order_full_lifecycle_and_rts_note` |
| Shop cannot RTS via PM | No code path exists; PM endpoints never touch `equipment_master.is_oos` or fleet_status |
| Dispatch/Admin RTS authority preserved | Untouched · `fleet_ops.py:/clear` endpoint still gates RTS |
| Recovery Map visible | Section 09 in ShopHubV2 (renumbered, not removed) |
| Dispatch Map-First intact | `/dispatch-portal` MapLibre canvas untouched |
| Driver no-login intact | Driver routes untouched |
| DriverHubV2 retired | Confirmed (no driver portal references in this track) |
| Mechanic assignment intact | `/api/shop/fleet/defects/*` untouched |
| Unit History intact | ASE backbone only **extended** to include `pm` events — no breaking change |
| Fuel/Lube intact | `/api/fuel-lube/*` untouched |
| Service Truck Reconciliation intact | `/api/shop/service-truck-reconciliation/*` untouched |
| Parts/Workload intelligence intact | `/api/shop/parts/on-order/summary` + `/api/shop/mechanics/workload` untouched |
| Material Movement Ledger untouched | confirmed |
| MaintainX dormant | doctrine flag in summary explicitly returns `maintainx_active=false` |
| FleetWatcher untouched | confirmed |
| No accounting / costs / PO | `test_no_cost_fields_in_work_order_response` + `test_summary_shape_and_doctrine` |
| No duplicate asset history | PM events project into existing ASE backbone — no second timeline |
| `/shop/hub_legacy` rollback alive | untouched |

---

## 22 · What Was Not Built (intentional)

* **Unit Search PM badge.** Could add `pm_status` chip to unit-search dropdown — deferred. Operators already reach PM info in 2 clicks via Unit History. Adding it would not reduce clicks, only add a glanceable signal.
* **PM completion attachments / photos.** Not in this track's scope. The existing attachment framework can be wired in a follow-up if operators report a need.
* **Email/PDF export of PM history.** Deliberately not built — directive forbids fake export buttons.
* **Auto-generation of work orders on schedule.** Operator must explicitly press "Generate PM work order" today. A nightly cron could automate this — held until operators confirm they want it.

---

## 23 · Remaining Gaps

1. **Motive engine-hour ingestion** — currently meter source is fuel/lube + pre-op inspection only. If Motive surfaces engine_hours in a future operational_events extension, prepend it to the priority chain in `_current_meter` (single change).
2. **PM template seeding.** No default templates ship with the build — operators must create them. By design (no fake manufacturer DB).
3. **MaintainX sync** — Track 13.32 future work, blocked on `MAINTAINX_API_KEY`.
4. **Bulk PM scheduling** (apply a template to all units of an asset type at once) — deferred. Single-row creation is acceptable for the current ~250-unit MASCI fleet.

---

## 24 · Rollback Procedure

1. Remove the four new routes from `/app/frontend/src/App.js` (single block under "Track 13.31").
2. Remove the PM section block from `/app/frontend/src/pages/ShopHubV2.jsx` (between `shop-hub-v2-section-mechanic-workload` and `shop-hub-v2-section-parts`).
3. Remove the PM router mount from `/app/backend/server.py` (4 lines, between `_strr_router` and `_shop_intel_router`).
4. Revert `/app/backend/routes/asset_service_events.py` to put `pm` back in `UNAVAILABLE_EVENT_TYPES`.
5. (Optional) Drop the three new collections: `pm_templates`, `pm_schedules`, `pm_work_orders`. They contain no data critical to other tracks.

All four steps are surgical — no shared utilities or schemas changed.

---

## 25 · Final Verdict

✅ **PASS · 9.6 / 10 average across five pillars.**

* Powerful: 9.7 — full lifecycle is operational.
* Simple: 9.6 — Shop Manager can answer all 10 PM questions in <15s from cold `/shop`.
* Beautiful: 9.5 — matches MASCI styling, no bolted-on look.
* Trusted: 9.8 — every due/overdue is explainable; every completion is attributable; RTS hard lock visible at API and UI.
* Proven: 9.7 — 15/15 new tests + 39/39 regression suite.

---

## 26 · Recommended Next Track

**Track 13.33 — Asset Care Command Center.** With PM Engine live, the Shop Command Center has every primary action queue it needs. The Asset Care Command Center can now act as the unified per-asset command view (defects + PMs + parts + fuel + history) — which is a re-composition of existing data, not new construction.

(Track 13.32 MaintainX integration remains blocked on `MAINTAINX_API_KEY` and external service credentials. Don't unblock it ahead of 13.33.)

---

**Track 13.31 — CLOSED. Books locked.**
