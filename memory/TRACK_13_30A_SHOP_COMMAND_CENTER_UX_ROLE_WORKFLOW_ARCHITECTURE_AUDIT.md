# Track 13.30A · Shop Command Center · UX + Role Workflow Architecture Audit

**Date:** 2026-06-12
**Mode:** READ-ONLY CERTIFICATION + ARCHITECTURE DESIGN.
**Implementation occurred:** **NO.** No code · no routes · no UI · no backend · no deploy · no GitHub save · no merge.
**Predecessor:** Track 13.30 (Service Truck Daily Reconciliation).
**Successor candidates (RECOMMENDED ORDER):** **13.30B → 13.30C → 13.31 → 13.33**.

---

## 1 · Executive Summary

The Shop backend is **strong** (24 + 12 = 36 backend pytest pass across 13.26 → 13.30). The Shop **frontend** has begun drifting toward a "track graveyard": ShopHubV2 now stacks 5 sections / 17 nav cards organized **by track number**, not by **role + decision**.

The user's morning question — *"At 6 AM, what needs attention?"* — is not answered in the first viewport on any role. There is no **global unit search**, no **mechanic workload** view, no **parts-on-order** rollup, no **PM due** signal, no **fuel/lube variance alert** signal, and the **HubBackLink component does not know Shop-only users exist** (it routes Shop tokens to platform `/`, not `/shop`).

**Verdict:** Stop building features. Before 13.31 (PM Engine) or 13.33 (Asset Care Command), ship a Command Center refactor + Global Unit Search. The data substrate is already strong enough — the missing piece is **orchestration**.

**Top P0 build:** **Track 13.30B — Shop Command Center Section Restructure + HubBackLink Shop-aware fix.** Two-file frontend refactor + 1-line HubBackLink fix · zero new backend · zero new collection · 2-day effort. Highest leverage per hour.

---

## 2 · Current ShopHubV2 Reality

**Mount:** `/shop` (and `/shop/hub_v2`) behind `RequireShop`. Legacy rollback `/shop/hub_legacy` still live (Track 13.6I doctrine).

**Single backend signal source today:** `GET /api/dispatch/command/summary.shop` → returns `{defects_open, defects_acknowledged, oos_units, active_recovery, waiting_on_parts, returned_to_service_7d, defect_open_units}` (7 ints).

**Current section layout (top → bottom):**

| # | Section name | Cards / surfaces | Source endpoint(s) | Live counts? |
|---|---|---|---|---|
| Header | Preview banner | "Shop Hub V2 · Live Shop operations hub …" copy | window.location.host check | n/a |
| 01 | Equipment Needing Attention | Open Defects · Defects Acknowledged · OOS Units · Units With Open Defect | summary.shop.* | YES (4) |
| 02 | Recovery Pipeline | Active Recovery Work · Waiting On Parts · Returned To Service (7d) | summary.shop.* | YES (3) |
| 03 | Recovery Map (secondary) | MapLibre lens (maintenance + inspection attention only) | `/api/operations-map/snapshot` (filtered client-side) | YES |
| 04 | Shop Records | Equipment Pre-Ops · Truck DVIRs · Defect History | links only (no counts on hub) | NO |
| 05 | Shop Workforce | Manager Queue · My Assignments · Unit History · New Fuel/Lube Visit · Fuel/Lube Records · Service Truck Reconciliation | links only | NO |
| Footer | Trace note | "Shop Hub V2 · Track 13.6I recovery." doctrine reminder | static | n/a |

**Card count today: 13 live cards + 1 map embed.** Track 13.31 (PM) and 13.33 (Asset Care Command) would push this past 17 cards. **Drift is real.**

---

## 3 · UI Defects

### 3a · Banner / copy problems
| Defect | Location | Severity | Recommendation |
|---|---|---|---|
| `shop-hub-v2-preview-banner` only renders when `/preview/i.test(host)` — but every production environment shows it because the URL still contains "preview" semantics. Copy mentions "Track 13.6I recovery" — internal-only. | ShopHubV2:341, 350 | **MED** | Replace with the PROD-context environment banner already in `App.js`, OR remove the banner entirely (the trace note at the footer already documents the rollback path). Internal track copy is **not** operator-facing. |
| Footer "trace note": "Shop Hub V2 · Track 13.6I recovery." | ShopHubV2:634 | **LOW** | Remove track number from operator copy. Reword to operational invariant: *"Repair Complete ≠ Returned To Service. Legacy hub at /shop/hub_legacy."* |
| Section captions reference "live" / "real counts" defensively (e.g. "01 · Equipment Needing Attention · live") | ShopHubV2:378, 426 | **LOW** | The `· live` decorator is internal-doctrine and operator-noise. Drop. The operator does not need reassurance the data is live; trust is earned by **correctness**, not by self-promotion. |

### 3b · Track-graveyard copy (operator-noise)
Every card carries a *"Source: /api/…"* italic footnote and many include a track number (e.g. *"Track 13.28 lifecycle endpoints"*, *"Track 13.29 P2"*, *"Track 13.30"*). This is **engineering metadata** leaking into operator surfaces.

| Pattern | Where | Recommendation |
|---|---|---|
| `Source: /api/...` italics on every card | ShopHubV2:489, 503, 517, 552, 566, 594, 608, 622 | Keep as a **dev tooltip / inspector affordance only** — hide from operator copy. Operators don't read URLs. |
| "Track 13.28 / 13.29 P2 / 13.30" mentions | ShopHubV2:552, 566, 594, 608, 622 | Remove all track numbers from card subtitles. |
| "(MOUNTED AT: /shop/hub_v2 …)" comment header doctrine | ShopHubV2:1–17 | OK to keep in source; not rendered. No action. |

### 3c · Layout problems
| Defect | Severity | Recommendation |
|---|---|---|
| **The first six visible cards** (Section 01) are 4× metric counters: *Open Defects · Defects Acknowledged · OOS Units · Units With Open Defect*. Three of those four (`defects_open`, `defects_acknowledged`, `defect_open_units`) **overlap** — a defect-open unit is by definition carrying an open defect. Operators see the same situation counted three different ways. | **HIGH** | Collapse to 2 cards: *Out-Of-Service Units* and *Open Defects (units : count)* with a compound `12 units · 31 defects` value. |
| Section 02 has **3 cards all linking to `/shop/equipment`** (Active Recovery · Waiting On Parts · RTS 7d). Three different counters, all open the same destination — destination doesn't filter by the count's intent. | **HIGH** | All 3 should deep-link to `/shop/equipment?filter=active_recovery` / `?filter=waiting_on_parts` / `?filter=rts_7d`, OR consolidate into a single Recovery Pipeline section that lists individual rows, not just counters. |
| Section 04 (Records) and Section 05 (Workforce) both link to record/queue surfaces. Mechanics scrolling for "My Assignments" find it **below the Recovery Map and the Records section** — too deep. | **HIGH** | Move "My Assignments" and "Manager Queue" cards into Section 01 (Attention Required). Records belong further down. |
| No **role detection**. Shop Manager, Mechanic, Fuel/Lube Tech, and Admin all see the same exact hub. There is no first-class signal that *the user is a mechanic and their queue has 3 items*. | **HIGH** | Add a role-aware top section that surfaces the caller's own queue counts when the auth gate recognizes them (Track 13.30B candidate). |
| No **search bar**. The most common shop task — *"look up unit ABC-123"* — requires clicking Unit History → typing a unit number → submit. That is 3 clicks + a typing context switch instead of 1 click. | **HIGH (the biggest UX gap)** | Add a global Unit Search input in the hub header (Track 13.30C candidate). |
| **Section 02 "Returned To Service (7d)"** ties Section 01's defect counts to a 7-day window with no per-defect actionability. It is a vanity metric, not a queue. | **MED** | Re-classify as an **archive** card (Section 06) or remove. |
| The Recovery Map sits as Section 03 (secondary lens) between the counters and the records — it interrupts task flow. Shop Manager rarely uses the map at 6 AM. | **LOW** | Move map below Workforce + Records, or fold it into a tab inside Section 01. |

### 3d · Dead / misleading buttons
| Defect | Where | Severity |
|---|---|---|
| `primaryActions` has *Equipment Pre-Ops* button (left) + *Fleet Visibility* button (right) hardcoded. Mechanic doesn't care about Pre-Ops first thing. Shop Manager wants Manager Queue first. Fuel/Lube Tech wants the Fuel/Lube form first. | ShopHubV2:365 | **MED** |
| The 4-card Section 04 grid contains the **Fuel/Lube Records** card (Track 13.29 P2) — but it lives in *Section 05 Workforce* alongside "My Assignments". Workforce ≠ Records. Confusing taxonomy. | ShopHubV2:540 | **MED** |
| There is no deep-link from any "Open Defects" card to **the specific units flagged**. Defects open in `/shop/fleet?focus_filter=defects` — a list, not a unit detail. The operator must scroll to find their unit. | ShopHubV2:386 | **LOW** |
| Service Truck Reconciliation card → list page (`/shop/service-truck-reconciliation`). For a fuel/lube tech at 6 AM, they want **the form** (`/new`), not the list. | ShopHubV2:614 | **LOW** |

### 3e · Internal-banner sweep on sub-pages

Scanned all `/app/frontend/src/pages/shop/*.jsx` + UnitHistory pages + FuelLube pages + ServiceTruck pages. No red operator-visible banners or certification stubs were found. The only operator-visible "alert"-style banner is the preview banner on `ShopHubV2.jsx:350` (which **is** internal copy).

---

## 4 · Navigation Defects (Back / Hub buttons)

### 4a · `HubBackLink` is Shop-blind — **HIGH severity**

**File:** `/app/frontend/src/components/HubBackLink.jsx`.

```js
// Current logic
const admin = isAdmin();
const pm = !admin && isPm();
const to = admin ? "/admin" : pm ? "/pm" : "/";   // ← Shop user lands at "/"
const label = admin ? "Admin" : pm ? "PM" : "Hub";
```

There is **no `isShop()` branch.** A signed-in Shop user (using `X-Shop-Token`, no admin token) clicks the "← Hub" button anywhere under `/shop/*` and is **kicked to the platform home page (`/`)** instead of `/shop`. The same applies to `useHubHome()` (logo home target).

**Pages affected** (all rely on `<HubBackLink />` via the shared hub header):
- `/shop/equipment` (Equipment Dashboard / Pre-Ops list)
- `/shop/equipment/:id` (View Equipment Inspection)
- `/shop/fleet` (Fleet Visibility)
- Several other `/shop/*` sub-routes that embed `HubBackLink`

**Symptom for a Shop-only user:** Click "← Hub" → land at platform front door → see Sign-In selector → must re-navigate to `/shop`. Two clicks of friction at every back-arrow.

**Fix scope (Track 13.30B):** Add one branch:

```js
import { isShop } from "@/lib/shopAuth";  // already exists
const shop = !admin && !pm && isShop();
const to    = admin ? "/admin" : pm ? "/pm" : shop ? "/shop" : "/";
const label = admin ? "Admin" : pm ? "PM" : shop ? "Shop" : "Hub";
```

Plus the same branch in `useHubHome()`. One file. ~6 lines. Zero backend.

### 4b · Sub-page back-button audit

| Sub-page | Back button | Goes to | Verdict |
|---|---|---|---|
| `/shop/fuel-lube/:visitId` | "← Records" `[data-testid="fuel-lube-detail-back"]` | `/shop/fuel-lube` | ✓ Correct (in-context) |
| `/shop/service-truck-reconciliation/:id` | "← Records" `[data-testid="strr-detail-back"]` | `/shop/service-truck-reconciliation` | ✓ Correct |
| `/shop/units/:unit/history` | "← Find another unit" `[data-testid="unit-history-back"]` | `/shop/units/history` | ✓ Correct |
| `/shop/fuel-lube/new` | "View manager queue" inline | `/shop/manager/queue` | ✓ Correct |
| `/shop/equipment` | `<HubBackLink />` → "← Hub" | `/` (platform) — **DEFECT** | ✗ See 4a |
| `/shop/equipment/:id` | `<HubBackLink />` → "← Hub" | `/` (platform) — **DEFECT** | ✗ See 4a |
| `/shop/fleet` | `<HubBackLink />` → "← Hub" | `/` (platform) — **DEFECT** | ✗ See 4a |
| `/shop/manager/queue` | (no top-level Back/Hub button — PortalShell only) | n/a | (no defect; users use browser back) |
| `/shop/me` | (PortalShell only) | n/a | (no defect) |

**Conclusion:** 3 high-traffic Shop record pages (`equipment`, `equipment/:id`, `fleet`) currently break Shop-only context. One file fix in Track 13.30B.

---

## 5 · Role-Based First-Five Needs

### 5a · Shop Manager (6 AM login)
1. What units are **down (OOS)**? → `summary.shop.oos_units` ✅ live
2. What defects are **open / unassigned**? → `/api/shop/manager/queue` buckets[`unassigned`] ✅ live
3. What work is **waiting on manager review**? → `/api/shop/manager/queue` buckets[`pending_review`] ✅ live
4. What is **waiting on parts**? → `summary.shop.waiting_on_parts` ✅ live
5. What PM / service work is **due or overdue**? → ❌ NOT LIVE (Track 13.31 future · documented in 13.26 backbone as `pm` placeholder)

Also wants: variance alerts (`service_truck_reconciliations` where `variance_status ∈ {yellow,red}` last 7d · 🟡 derivable from existing list endpoint · no new backend); mechanics workload (per-mechanic open count from `tasks_notifications` or `fleet_defects.assigned_to_mechanic_id` group — 🟡 derivable, ~2h backend); RTS pending count (already in `manager/queue` buckets[`rts_pending`]); unit search (❌ not built).

### 5b · Mechanic
1. **What is assigned to me?** → `/api/shop/me/assignments` buckets[`assigned`] ✅ live
2. **What have I accepted / in progress?** → buckets[`accepted`] + buckets[`in_progress`] ✅ live
3. **What needs parts?** → ❌ NOT LIVE (mechanic-scoped parts gap · could be derived from `fleet_defects` where `assigned_to_mechanic_id == me AND parts_on_order != []`)
4. **What's waiting on my notes / completion?** → buckets[`in_progress`] ✅ live (same as #2 — duplicated for emphasis)
5. **What was rejected back to me?** → ❌ NOT EXPLICITLY DERIVED (Track 13.28 Phase 2 has manager review reject path · field exists; just not aggregated)

Also wants: unit history (✅ via Track 13.27); per-unit parts history (✅ surfaced inline in Track 13.27 timeline); repair-notes drafts (❌); photos / attachments (✅ via existing inspection routes).

### 5c · Fuel/Lube Tech
1. **What job / truck am I servicing today?** → ❌ NOT LIVE (would derive from `dispatch_assignments` or a tech-scoped projection)
2. **Start-of-day reconciliation open?** → ✅ live · derivable from `/api/shop/service-truck-reconciliation?status=start_logged&tech_id=me`
3. **Fuel/Lube Visit form** → ✅ `/shop/fuel-lube/new` (Track 13.29)
4. **My submitted visits today** → ✅ live · derivable from `/api/shop/fuel-lube/visits?fuel_lube_tech_id=me&from=today`
5. **End-of-day reconciliation needed?** → ✅ live · derivable from same `?status=start_logged` query

Also wants: issues I reported today (✅ derivable from visits filtered by tech + `has_issue=true`); units serviced today (✅); variance status (✅ via Track 13.30).

### 5d · Service Writer / Parts Coordinator (role does not exist today)
1. Parts on order → 🟡 partial (`fleet_defects.parts_on_order[]` exists per defect; no aggregate)
2. Repairs waiting on parts → ✅ derivable (`fleet_defects` where `parts_on_order != []`)
3. Parts expected today → ❌ NOT LIVE (no expected-receipt date field on `parts_on_order`)
4. Units down because of parts → ✅ partial (intersection of `parts_on_order != []` AND `fleet_status.status=oos`)
5. Per-unit parts history → ✅ via Track 13.27 timeline (parts surfaced inline on `repair/completed` events)

**This role has no dedicated portal today.** Track 13.31 candidate has a "Parts Intelligence" sub-track.

### 5e · Dispatch viewer / Dispatch partner
1. Which units are OOS? → ✅ `summary.shop.oos_units` (same source)
2. Which trucks are unavailable? → ✅ `fleet_status.status='oos'`
3. RTS pending count? → ✅ `manager/queue.buckets.rts_pending`
4. Units waiting on shop? → ✅ `defect_open_units` or `fleet_status.status='in_shop'`
5. Service trucks active today? → ✅ Track 13.30 list (`status=start_logged`) — dispatch should NOT manage this (it's a shop accountability tool), but read-visibility is OK

(Dispatch already has its own portal; this row is for cross-portal visibility only.)

### 5f · Admin / Leadership
1. Fleet downtime → ✅ `oos_units` + average days-OOS
2. Open defects → ✅ `defects_open`
3. PM compliance → ❌ NOT LIVE (Track 13.31)
4. Fuel / service variance → ✅ via Track 13.30 list aggregations
5. Parts + repair bottlenecks → 🟡 partial

---

## 6 · Current Route / Source Inventory

### 6a · Frontend routes under `/shop/*` (today)
```
/shop                                       → ShopHubV2          (RequireShop)
/shop/hub_v2                                → ShopHubV2          (RequireShop) · alias
/shop/hub_legacy                            → ShopHub            (RequireShop) · rollback
/shop/manager/queue                         → ShopManagerQueue   (RequireShop)
/shop/me                                    → ShopMyAssignments  (RequireShop)
/shop/units/history                         → UnitHistoryLanding (RequireShop)
/shop/units/:unitNumber/history             → UnitHistoryTimeline(RequireShop)
/shop/fuel-lube                             → FuelLubeVisitRecords  (RequireShop)
/shop/fuel-lube/new                         → FuelLubeVisitForm     (RequireShop)
/shop/fuel-lube/:visitId                    → FuelLubeVisitDetail   (RequireShop)
/shop/service-truck-reconciliation          → ServiceTruckReconciliationRecords (RequireShop)
/shop/service-truck-reconciliation/new      → ServiceTruckReconciliationForm    (RequireShop)
/shop/service-truck-reconciliation/:recId   → ServiceTruckReconciliationDetail  (RequireShop)
/shop/trench-safety-repairs                 → ShopTrenchSafetyRepairs (RequireShop)
/shop/fleet                                 → FleetVisibility (scope=shop)
/shop/equipment                             → EquipmentDashboard
/shop/equipment/:id                         → ViewEquipmentInspection (context=shop)
/shop/login · /shop/reset/:token · /shop/change-password → auth surfaces
```

**Count:** 13 operational routes + 3 auth surfaces + 1 legacy rollback = **17 mounted routes**.

### 6b · Backend endpoints actually used by Shop UI today
| Endpoint | Method | Shop UI consumer | Notes |
|---|---|---|---|
| `/api/dispatch/command/summary` | GET | ShopHubV2 metric counters | Cross-portal read engine. `shop` key carries 7 fields. |
| `/api/operations-map/snapshot` | GET | Recovery Map lens | Client-filtered to `attention_reason ∈ {maintenance,inspection}` |
| `/api/shop/manager/queue` | GET | ShopManagerQueue.jsx | Returns 6 buckets + counts |
| `/api/shop/me/assignments` | GET | ShopMyAssignments.jsx | Mechanic-scoped queue |
| `/api/shop/fleet/defects/{id}/assign` | POST | ShopManagerQueue | Track 13.28 |
| `/api/shop/fleet/defects/{id}/reassign` | POST | ShopManagerQueue | Track 13.28 |
| `/api/shop/fleet/defects/{id}/accept` | POST | ShopMyAssignments | Track 13.28 |
| `/api/shop/fleet/defects/{id}/start` | POST | ShopMyAssignments | Track 13.28 |
| `/api/shop/fleet/defects/{id}/repair` | POST | RepairCompletionForm | Track 13.28 P2 |
| `/api/shop/fleet/defects/{id}/manager-review` | POST | ShopManagerQueue | Track 13.28 |
| `/api/shop/fuel-lube/visits` | GET/POST | FuelLubeVisitRecords + Form | Track 13.29 |
| `/api/shop/fuel-lube/visits/{id}` | GET | FuelLubeVisitDetail | Track 13.29 P2 |
| `/api/shop/service-truck-reconciliation` | GET | STR Records | Track 13.30 |
| `/api/shop/service-truck-reconciliation/start` | POST | STR Form | Track 13.30 |
| `/api/shop/service-truck-reconciliation/close` | POST | STR Form | Track 13.30 |
| `/api/shop/service-truck-reconciliation/{id}` | GET | STR Detail | Track 13.30 |
| `/api/shop/service-truck-reconciliation/{id}/review` | POST | STR Detail | Track 13.30 |
| `/api/assets/{unit}/timeline` | GET | UnitHistoryTimeline | Track 13.26 backbone |
| `/api/equipment-inspections` | GET | EquipmentDashboard | Pre-Op list |
| `/api/shop/fleet/by-unit` | GET | FleetVisibility | Per-unit DVIR + defect state |
| `/api/fleet/defects/{id}/detail` | GET | Defect detail drawer | |
| `/api/shop/fleet/defects` | GET | Defect history list | |
| `/api/tasks-notifications` | GET | (cross-portal feed) | Not yet consumed by ShopHubV2 |

**No endpoints are missing for Manager / Mechanic / Fuel-Lube workflows.** The gaps are aggregation + composition + role-aware presentation.

---

## 7 · Future Placement Architecture

| Capability | Primary Role | Hub Section (target) | Source Endpoint | Status |
|---|---|---|---|---|
| PM Engine (due / overdue) | Manager + Admin | 01 Attention Required | NEW: `/api/shop/pm/due` (Track 13.31 derived) | NOT BUILT · scheduled |
| Known Parts by Unit | Mechanic + Manager | 05 Unit Intelligence | Derived from `/api/assets/{unit}/timeline` (already surfaces parts_used per repair event) | Live (read-only); aggregation gap |
| Fuel Usage / Hours-per-Gallon intelligence | Manager | 04 Fuel / Service | Derived from `fuel_lube_visits.equipment_lines[]` joined to `meter_hours` | NOT BUILT · 13.33 candidate |
| Service Truck Reconciliation | Fuel/Lube Tech + Manager | 04 Fuel / Service | `/api/shop/service-truck-reconciliation` | ✅ Live (Track 13.30) |
| Fuel/Lube Records (list + detail) | Fuel/Lube Tech + Manager | 04 Fuel / Service + 06 Records | `/api/shop/fuel-lube/visits` | ✅ Live (Track 13.29 + P2) |
| MaintainX Work Orders | Mechanic + Manager | 02 Active Work + 06 Records | NEW: `/api/maintainx/work-orders` | **BLOCKED** on `MAINTAINX_API_KEY` |
| Asset Care Command Center | Admin / Leadership | TOP CARD (or admin hub) | Composes 13.26 + 13.28 + 13.30 + 13.31 | NOT BUILT · 13.33 |
| Parts On Order | Mechanic + Service Writer | 03 Parts + Waiting | Derived from `fleet_defects.parts_on_order != []` | Derivable today (no agg endpoint) |
| Parts Received | Service Writer | 03 Parts + Waiting | NEW: `/api/shop/parts/received` | NOT BUILT |
| Mechanic Workload | Manager | 02 Active Work | Derived: group `fleet_defects` by `assigned_to_mechanic_id` | Derivable today (no agg endpoint) |
| Global Unit Search | All roles | TOP (header) | NEW: `/api/shop/units/search?q=…` | NOT BUILT (highest UX leverage) |
| Unit Timeline | All roles | 05 Unit Intelligence | `/api/assets/{unit}/timeline` | ✅ Live (Track 13.26) |
| Asset Health Score | Admin | 01 Attention Required | NEW (composite) | NOT BUILT · 13.33 |

---

## 8 · Target Shop Command Center Structure (DESIGN ONLY)

### 8a · Top of viewport (above section 01)
1. **Global Unit Search bar** — single input "Unit # / asset / truck / equipment" with debounced suggestions. Submit → `/shop/units/:unit/history`. Highest UX leverage.
2. **Role-aware "Your queue" strip** — if caller is a mechanic: *"You have N assignments · M in progress · P needing notes."* If Shop Manager: *"N unassigned · M pending review · P rts pending."* If Fuel/Lube tech: *"You have N open reconciliations · 0 visits submitted today."*

### 8b · Section structure (target)

| # | Section | Cards | Source endpoints |
|---|---|---|---|
| **01 · Attention Required** | OOS Units · Open Defects (units : count) · Pending Manager Review · Waiting Parts · PM Overdue (when 13.31 ships) · Variance Alerts last 7d | summary.shop · manager/queue · STR list (`variance_status=red`) |
| **02 · Active Work** | Unassigned · Assigned · In Progress · My Assignments · Mechanic Workload | manager/queue · me/assignments |
| **03 · Parts + Waiting** | Parts On Order · Waiting Parts · Parts Received (when built) · Known Parts lookup | Derived from fleet_defects |
| **04 · Fuel / Service** | New Fuel/Lube Visit · Fuel/Lube Records · Service Truck Reconciliation · Variance Alerts · Fuel/Lube Issues This Week | fuel-lube · service-truck-reconciliation |
| **05 · Unit Intelligence** | Unit Search (also in header) · Unit History · Known Parts by Unit · PM status (13.31) · Last Fuel/Service · Open Defects | assets/timeline · summary.shop |
| **06 · Records** | Equipment Pre-Ops · Truck DVIRs · Defect History · Reconciliation Records · Fuel/Lube Visit Records | existing record routes |
| **07 · Map / Location** (collapsible by default) | Recovery Map | operations-map/snapshot |

**Total card count:** ~18–20 cards (similar to today), but **organized by decision flow**, not by track number, and **the first 5 cards visible in viewport answer the 5 "what needs attention" questions** above the fold.

### 8c · Banner / copy cleanups (target)
- Drop the `preview` banner from ShopHubV2 (it leaks `Track 13.6I`).
- Drop `· live` decorators on section headers.
- Drop italics-Source-footnotes on operator cards (keep them as `title=""` tooltips for inspector affordance).
- Drop all track-number mentions (`Track 13.28`, `Track 13.29 P2`, `Track 13.30`) from card subtitles.

---

## 9 · Global Unit Search Architecture (DESIGN ONLY)

### 9a · Required endpoint (NOT BUILT)
`GET /api/shop/units/search?q=<term>&limit=20` returning:
```json
{
  "results": [{
    "unit_number": "ABC-123",
    "asset_id": "asset-…",
    "asset_name": "CAT 336F",
    "asset_type": "excavator",
    "current_status": "available | oos | in_shop | failed_dvir",
    "open_defect_count": 3,
    "assigned_mechanic_id": "tech-007",
    "assigned_mechanic_name": "Pat Smith",
    "pm_status": "due | overdue | current | unknown",
    "last_fuel_lube_visit": "2026-06-12 · 145 gal red diesel · 0 issues",
    "parts_on_order_count": 2,
    "active_work_order_id": "flv-defect-…",
    "links": {
      "history":  "/shop/units/ABC-123/history",
      "defects":  "/shop/fleet/by-unit?unit=ABC-123",
      "timeline": "/api/assets/ABC-123/timeline"
    }
  }]
}
```

### 9b · Source endpoint composition (read-only · derivable today)
- `equipment_master` (asset + asset_name + asset_type · search index on `unit_number`)
- `fleet_status` (current status)
- `fleet_defects` (open_defect_count + assigned_mechanic + parts_on_order_count · grouped by truck_unit_number)
- `fuel_lube_visits` (last_fuel_lube_visit summary · grouped by equipment_lines.unit_number)
- `equipment_inspections` (PM status — placeholder until 13.31 lands)

**No new collection.** **No mutation.** All sources already live.

### 9c · UX placement
- Top of `/shop` hub as a header search input.
- Top of `/shop/units/history` as the existing input (already there — make hub version delegate to that page on Enter).
- Submit → `/shop/units/:unit/history` (consistent with Track 13.27).

### 9d · Build effort
Backend (1 new endpoint, ~120 LOC): ~3h.
Frontend (header input + suggestion dropdown): ~3h.
Pytest coverage: ~2h.
**Total: ~1 day (Track 13.30C candidate).**

---

## 10 · Card / Count Source Truth Map

| Card (proposed) | Count / Status | Endpoint | Field | Live today? | Notes |
|---|---|---|---|---|---|
| Open Defects | int | `/api/dispatch/command/summary` | `shop.defects_open` | ✅ | unchanged |
| OOS Units | int | same | `shop.oos_units` | ✅ | unchanged |
| Pending Manager Review | int | `/api/shop/manager/queue` | `counts.pending_review` | ✅ | already returned · just not surfaced on hub |
| RTS Pending | int | `/api/shop/manager/queue` | `counts.rts_pending` | ✅ | same |
| Waiting Parts | int | `/api/dispatch/command/summary` | `shop.waiting_on_parts` | ✅ | unchanged |
| My Assignments | int | `/api/shop/me/assignments` | `counts.assigned + .in_progress` | ✅ | unchanged |
| Unassigned Work | int | `/api/shop/manager/queue` | `counts.unassigned` | ✅ | not surfaced on hub today |
| In Progress | int | `/api/shop/manager/queue` | `counts.in_progress` | ✅ | not surfaced on hub today |
| Parts On Order | int | NEW agg endpoint (Track 13.30D) | derived from `fleet_defects.parts_on_order` | 🟡 derivable | needs aggregator |
| Fuel/Lube Visits Today | int | `/api/shop/fuel-lube/visits?from=today&to=today` | `count` | ✅ | client-side composition |
| Fuel/Lube Issues This Week | int | `/api/shop/fuel-lube/visits?from=-7d&has_issue=true` | aggregation across visits | ✅ | composition |
| Reconciliation Variance Alerts | int | `/api/shop/service-truck-reconciliation?variance_status=red&from=-7d` | `count` | ✅ | composition |
| PM Due | int | NEW (Track 13.31) | — | ❌ | future track |
| PM Overdue | int | NEW (Track 13.31) | — | ❌ | future track |
| Unit Search | search input | NEW (Track 13.30C) | — | ❌ | highest UX leverage |
| Known Parts by Unit | drill-in only | `/api/assets/{unit}/timeline` (filter event_type=repair · parts_used[]) | — | ✅ | already in Track 13.27 timeline |
| MaintainX Open Work Orders | int | — | — | 🟥 BLOCKED on credentials | Track 13.32 |
| Mechanic Workload | grid | NEW agg endpoint or grouped client-side over `manager/queue.buckets` | — | 🟡 derivable | needs aggregator |
| Variance Alerts (rollup) | int | composition | — | ✅ | client-side composition |
| Fuel/Lube Issues (rollup) | int | composition | — | ✅ | client-side composition |

**No proposed card lacks a source.** 13 of 19 cards are **live today**; 4 cards are **derivable client-side without backend work**; 2 cards require a new aggregator (Parts On Order + Mechanic Workload); 2 cards await **future tracks** (PM, MaintainX).

---

## 11 · Click Depth Audit

| Task | Current click depth | Target | Gap |
|---|---|---|---|
| Assign a mechanic | 3 (hub → Manager Queue → row → Assign modal) | 2 (hub-Section 02 → row Assign) | -1 |
| Mechanic starts repair | 3 (hub → My Assignments → row → Start) | 2 | -1 |
| Manager reviews repair | 3 (hub → Manager Queue → Pending Review bucket → row) | 2 | -1 |
| Dispatch sees OOS truck | 2 (hub → OOS card → unit) | 2 | OK |
| Find unit history | **4** (hub → Workforce section scroll → Unit History card → input → submit) | 1 (hub header search) | **-3 (biggest gap)** |
| Find known part number for unit | 4 (hub → Unit History → unit → scroll timeline for repair events) | 2 (hub search → unit page) | -2 |
| Find all fuel visits for a job | 3 (hub → Workforce section → Fuel/Lube Records → filter by project) | 2 | -1 |
| Find service truck variance | 3 (hub → Workforce → STR Records → filter `red`) | 1 (hub Section 01 Variance Alerts card → list pre-filtered) | -2 |
| Find DVIR for a truck | 3 (hub → Records → Truck DVIRs → click unit) | 2 (hub search → DVIR tab on unit page) | -1 |
| Find pre-op for equipment | 3 (hub → Records → Equipment Pre-Ops → click row) | 2 (hub search → Pre-Op tab) | -1 |
| Find open defects for one unit | 3 (hub → Open Defects card → list → scroll for unit) | 1 (hub search → unit page Defects tab) | -2 |
| Find waiting parts | 2 (hub → Waiting Parts card) | 2 | OK |
| Find PM due | n/a (not built) | 1 (after 13.31) | n/a |
| Find repair notes | 4 (hub → Manager Queue or My Assignments → row → expand) | 3 | -1 |

**Headline finding:** Adding a **header Unit Search** removes 1–3 clicks from **6 of the 14 most common Shop tasks** with one new endpoint + one new header component.

---

## 12 · Five-Pillar Evaluation (Current ShopHubV2)

| Pillar | Score | Reasoning |
|---|---|---|
| **Powerful** | 6 / 10 | Strong backend (36/36 pytest). Hub surfaces 7 live signals. But unit search is missing, mechanic workload is missing, parts-on-order is unsurfaced, variance alerts are unsurfaced. |
| **Simple** | 5 / 10 | 17 cards · 5 sections · "preview" banner · track-graveyard copy · 3-click depth for most-common tasks. First 5 things you need are NOT in the first viewport. |
| **Beautiful** | 7 / 10 | Card primitives are consistent. PortalShell looks clean. But operator-noise copy (Source: /api/…, Track 13.28 mentions) feels engineering-first, not operator-first. |
| **Trusted** | 9 / 10 | Every count traces to a real source. No fake exports. Hard locks documented in card copy. Doctrine footer present. |
| **Proven** | 8 / 10 | Backend pytest 36/36 pass · ESLint clean · live browser smoke confirmed mounts. UX defects (HubBackLink, click depth) not yet measured against operator workflows. |

**Total: 7.0 / 10.** Strong substrate · structural drift.

---

## 13 · Final Recommendation

**A · Build ShopHubV2 Command Center refactor + HubBackLink Shop-aware fix FIRST (Track 13.30B). Then Global Unit Search (Track 13.30C). THEN PM Engine (Track 13.31).**

### Why option A over B / C / D
- **Option A (Command Center refactor + HubBackLink fix · Track 13.30B):** 2-day frontend-only effort. Unblocks all roles immediately. Zero new backend. Resolves the **HIGH** severity HubBackLink defect (3 routes broken for Shop-only users) before more features land.
- **Option B (Global Unit Search · Track 13.30C):** 1-day effort (1 backend endpoint + 1 frontend component). Highest single-feature leverage per hour. Should follow A, not precede it, because A delivers the **container** B sits in.
- **Option C (PM Engine · Track 13.31):** 4–6 day effort. Strong feature but adds a NEW section to a hub that already has structural drift. Build the container first.
- **Option D (Parts Intelligence):** 3-day effort. Derives a strong dashboard from existing data BUT only the parts coordinator role gets value. Lower per-role leverage than A.
- **Option E (Sign-off window):** Premature — three known UI defects (HubBackLink, click depth, banner copy) would ship with the hub. Fix those first.

### Five-pillar justification of A
- **Powerful (10):** Role-aware first-five framing means each user sees their work immediately.
- **Simple (10):** Click depth drops from 3 to 1 on the most-common tasks.
- **Beautiful (9):** Banner/copy cleanup eliminates internal noise.
- **Trusted (10):** Every count keeps its source-truth provenance (just moved to tooltip).
- **Proven (10):** All sources already pytest-covered (36/36).

### Source-truth justification of A
- **Zero new collection.** **Zero new endpoint.** Track 13.30B is **purely** a presentation reorganization + 1 component fix.
- All proposed top-tier cards (sections 01–05) source from endpoints already shipping and already tested.

---

## 14 · Build Queue (recommended order)

| Order | Track | Scope | Effort | Risk | Blockers |
|---|---|---|---|---|---|
| **1** | **13.30B** | ShopHubV2 Command Center restructure (7 sections · role-aware "Your queue" strip · banner cleanup · track-copy removal) + HubBackLink Shop-aware fix | 2 d | LOW | none |
| **2** | **13.30C** | Global Unit Search (new `/api/shop/units/search` endpoint + header input) | 1 d | LOW | depends on 13.30B header slot |
| **3** | **13.30D** | Parts-On-Order aggregator + Mechanic Workload aggregator (2 new derived endpoints · 2 new hub cards) | 2 d | LOW | depends on 13.30B |
| **4** | **13.31** | PM Engine (derived projector) | 5 d | MED | depends on 13.30B section slot |
| **5** | **13.33** | Asset Care Command Center (composes 13.26 + 13.28 + 13.30 + 13.31) | 4 d | LOW | depends on 13.31 |
| **6** | **13.32** | MaintainX Integration | 5 d | **HIGH** | **BLOCKED on `MAINTAINX_API_KEY`** |

---

## 15 · What NOT To Build

- Do **not** build more "Track X" cards on ShopHubV2 before 13.30B ships.
- Do **not** add accounting / cost / fuel tax / PO / pay-app / contract / RFI / submittal / change-order surfaces (forbidden by program).
- Do **not** build a "theft register" or "fuel discrepancy review" disciplinary surface — variance is operational only.
- Do **not** build a parallel asset history surface — Track 13.26 backbone is the single source.
- Do **not** activate MaintainX integration until `MAINTAINX_API_KEY` is operator-supplied.
- Do **not** mutate `fuel_lube_visits`, `fleet_defects`, `service_truck_reconciliations` from the search endpoint — all reads only.
- Do **not** deploy. Do **not** Save to GitHub. Do **not** merge.

---

## 16 · Hard Lock Verification

| Lock | Status |
|---|---|
| Shop Repair Complete ≠ RTS | INTACT — endpoint-level enforcement unchanged |
| Dispatch / Admin RTS authority | INTACT — `/api/dispatch/fleet/defects/{id}/clear` gated by `_require_dispatch_or_admin` |
| Dispatch Map-First | INTACT — no map changes proposed |
| Driver no-login | INTACT |
| DriverHubV2 retired | INTACT |
| One map engine | INTACT — Recovery Map reuses certified MapLibre engine |
| One source of truth (Asset Service Event Backbone) | INTACT — search composes from existing collections; no new history collection |
| No fake MaintainX | INTACT — Track 13.32 awaits credentials |
| No fake FleetWatcher | INTACT — labeled `not_connected` everywhere |
| No accounting · cost · pay apps · ERP · contracts | INTACT |
| No duplicate asset history | INTACT — no new asset history collection proposed |
| No duplicate defect lifecycle | INTACT — Track 13.28 lifecycle remains the single defect spine |

---

## 17 · Final Verdict

🟢 **GREEN — audit complete · no implementation occurred · operator decision required for build authorization.**

**Recommended next directive from operator:** *"Build Track 13.30B."*

---

## 18 · Open questions for operator (optional)

1. Should the global Unit Search live in the ShopHubV2 header **and** the platform-wide top bar, or only on `/shop` for now?
2. Should "Mechanic Workload" appear by name (e.g., "Pat Smith · 3 open") or anonymized (mechanic IDs only) — has bearing on data-privacy posture?
3. Is there a Service Writer / Parts Coordinator role planned, or are these tasks owned by the Shop Manager? (affects whether Parts Intelligence becomes a 6th role view or stays inside Manager view).
4. Variance alerts on the hub — should yellow + red rollup together, or only red?

**End Track 13.30A.**
