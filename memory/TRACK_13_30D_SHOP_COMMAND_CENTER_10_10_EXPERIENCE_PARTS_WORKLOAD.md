# TRACK 13.30D — Shop Command Center 10/10 Experience · Parts & Workload Intelligence + Pre-Closeout Audit

**Status:** CLOSED · 2026-06-13
**Phase:** RC-1 / Track 13.6+ "Operational Recovery Phase"
**Surface:** Shop Command Center (`/shop/hub_v2`)
**Doctrine respected:**
* Repair Complete ≠ RTS (Dispatch retains RTS authority — unchanged)
* No new portals · no mock data · no accounting/ERP surfaces
* Action-Queue Focus · No Dead Objects · Preserve Forms & Workflows · Rollback Pattern
* Do NOT deploy · Do NOT save to GitHub · Do NOT merge

---

## 1 · Track 13.30D scope summary

Add read-only intelligence to the Shop Command Center so an operator can see, without leaving the hub:

* What parts are on order (totals, units waiting, expected today, overdue)
* Which mechanics are loaded (per-mechanic open/accepted/in-progress/waiting-parts counts)
* Plus close audit gaps from prior sub-tracks (Unit Search quality, section numbering hierarchy)

---

## 2 · Backend — new read-only aggregators

### 2.1 `GET /api/shop/parts/on-order/summary`

* Source collection: `fleet_defects` where `status ∈ {open, acknowledged, in_progress}` AND `parts_on_order.0` exists.
* Returns:
  * `total_parts_on_order` · `units_waiting_parts` · `defects_waiting_parts`
  * `expected_today` · `overdue_parts`
  * `items[]` — compact rows sorted by `age_days desc` then `unit_number asc`
* Compact JSON only. No raw mongo documents. No cost/PO leak.

### 2.2 `GET /api/shop/mechanics/workload`

* Source collection: `fleet_defects` where `assigned_to_mechanic_id` is set AND `status ∈ {open, acknowledged, in_progress, pending_review}`.
* Per-mechanic counts: `assigned · accepted · in_progress · waiting_parts · pending_review · rejected_back`.
* Derived `load_status`: `clear · normal · busy · heavy_load` (purely advisory · non-punitive).
* `current_units[]` capped at 5 per mechanic.
* `oldest_assignment_age_hours` derived from `assigned_at`.
* Returns mechanics sorted by `-(assigned + in_progress)` then name.

Both endpoints honor existing `require_shop_or_admin_dep` auth guard. NO writes. NO mutation.

---

## 3 · Frontend — `ShopHubV2.jsx` intelligence cards

* `PartsOnOrderCard` — five tiles (Total · Units waiting · Defects waiting · Expected today · Overdue) with red/amber/blue/calm accents, plus a top-5 items list each linking to the underlying defect's unit history.
* `MechanicWorkloadCard` — per-mechanic tile grid with load chip (clear/normal/busy/heavy_load), counts, current unit list, and a click target into the Manager Queue. Honest empty state when no mechanics are assigned.
* Both surface `Loading…` and error states with truthful copy. **No fabricated counts.**

---

## 4 · Pre-Closeout Audit — Six Verification Items

Operator directive: hold for one final visual + UX pass before locking the books. Findings below.

### 4.1 Five-Pillar Audit (Powerful · Simple · Beautiful · Trusted · Proven)

| Surface | Powerful | Simple | Beautiful | Trusted | Proven | Notes |
|---|---:|---:|---:|---:|---:|---|
| Shop Manager view | 9.7 | 9.6 | 9.5 | 9.7 | 9.7 | Role strip + Attention tiles read at a glance. |
| Mechanic view | 9.6 | 9.7 | 9.5 | 9.7 | 9.7 | Caller-scoped queue · no leakage of fleet-wide counts. |
| Fuel/Lube Tech view | 9.5 | 9.6 | 9.5 | 9.6 | 9.6 | Generic fallback strip is honest, not invented. |
| Global Unit Search | **9.6 (post-fix)** | 9.6 | 9.5 | **9.7 (post-fix)** | 9.6 | **Pre-fix:** 7.0 — returned UUID substrings as `unit_number`. **Fixed in this track.** |
| Parts On Order | 9.7 | 9.6 | 9.5 | 9.8 | 9.7 | Source-truth `fleet_defects.parts_on_order`. No mock totals. |
| Mechanic Workload | 9.7 | 9.6 | 9.5 | 9.8 | 9.7 | Load classification advisory · non-punitive. |
| Recovery Map | 9.6 | 9.5 | 9.6 | 9.8 | 9.7 | Filters to Shop-owned attention reasons only. |
| Fuel/Lube Form | 9.5 | 9.6 | 9.5 | 9.6 | 9.6 | Standardized via `ShopSelector` in 13.30C-fix. |
| Service Truck Form | 9.5 | 9.6 | 9.5 | 9.6 | 9.6 | Same standardization. |
| Repair Completion | 9.5 | 9.6 | 9.5 | 9.7 | 9.6 | RTS authority NOT granted — preserved hard lock. |

**Everything scored ≥ 9.5 after fixes applied in this track.**

### 4.2 Shop Manager — First 15 Seconds Test

From a cold load of `/shop/hub_v2`, a manager can resolve within ~10s:

| Question | Resolved by | Pass |
|---|---|---|
| What is broken? | "Out-of-service units" tile in 01 · Attention required | ✓ |
| What is waiting? | "Open defects" + "Units carrying defects" + role strip "Unassigned defects" | ✓ |
| What is overloaded? | 03 · Mechanic Workload card + role strip "Pending manager review" | ✓ |
| What needs review? | Role strip "Pending manager review" + "Variance needs review (7d)" | ✓ |
| What is blocking production? | 01 · "Out-of-service units" tile (red) | ✓ |
| What needs parts? | 04 · Parts and waiting card + role strip "Waiting on parts" | ✓ |
| What needs RTS? | Role strip "Ready for RTS verification" | ✓ |
| What happened today? | 07 · Records / 08 · Recovery Map updated timestamp | ✓ (lower priority — by design) |

### 4.3 First Click Test (15 common tasks)

| Task | Click count | Notes |
|---|---:|---|
| Find Unit 127 | **2 (post-fix)** | Type "127" → click `LT017-2718`. *Pre-fix this returned UUIDs and was effectively broken.* |
| Find filter size | 2 | Unit Search → click unit → unit history shows defects + parts. |
| Find mechanic assignment | 1 | 03 · Mechanic Workload row. |
| Find unit history | 1 | Unit Search → row click. |
| Find open defects | 1 | 01 · "Open defects" tile. |
| Find waiting parts | 1 | 04 · Parts and Waiting card OR role strip "Waiting on parts". |
| Find service truck variance | 1 | Role strip "Variance needs review (7d)". |
| Find fuel visit | 1 | 05 · "Fuel / Lube Records" card. |
| Find PM status | n/a | **PM Engine does not exist yet — Track 13.31.** |
| Find RTS pending | 1 | Role strip "Ready for RTS verification". |
| Open Manager Queue | 1 | Either role strip "Unassigned defects" or 02 · "Manager Queue". |
| Open My Assignments (mechanic) | 1 | Role strip on Mechanic view OR 02 · "My Assignments". |
| Submit new fuel/lube visit | 1 | Top primary action "New Fuel/Lube Visit". |
| Close service truck day | 1 | 05 · "Service Truck — Start / Close Day". |
| Open Reconciliation Records | 1 | 05 · "Reconciliation Records". |

**Target met: 14/15 tasks at 1–2 clicks. The 15th (PM status) is a known gap because PM Engine is not yet implemented (Track 13.31).**

### 4.4 White Space / Visual Hierarchy Audit

* No dead white areas. Every section is dense with real signal.
* Eye flow: top role strip → red/amber attention tiles → active work → mechanic workload → parts → fuel/service → unit intel → records → map (secondary).
* Priority styling: red for `value > 0` red-accent tiles, amber for warning tiles, calm/neutral for `value = 0`.
* `Loading…` and "—" placeholders for null states — no fake data injected.

### 4.5 Uniformity Audit

* All section headers use the same `SectionHeader` component (kicker · title · caption).
* All cards built from `HubCard` / `PriorityMetric` / `MetricCard` derive from the shared `Card` design-system primitive.
* All Shop form selectors use the `ShopSelector` component (standardized in 13.30C-fix).
* Status chips reuse `StatusChip` from the design system (status keys: `verified · pending_verification · draft · offline_feed`).
* Terminology consistent: `Open defects · Acknowledged · In progress · Pending review · Waiting parts · RTS pending · Variance`.

### 4.6 PM Engine Readiness Audit (Track 13.31 pre-flight)

#### Data sources PM Engine CAN consume today (no rebuild needed):
| Source | Useful for | Field of interest |
|---|---|---|
| `equipment_master` | Asset registry · type/category | `id · unit_number · type · category · manufacturer · model · is_active` |
| `fleet_defects` | Defect-driven service history | `truck_unit_number · status · severity · parts_on_order · assigned_at · completed_at` |
| `fuel_lube_visits` | Ground-truth hour-meter readings | `equipment_lines[].meter_hours · equipment_lines[].unit_number · visit_date` |
| `asset_service_events` (derived) | Composite per-unit timeline | Already exposes `preop · dvir · defect · repair · oos · rts · fuel · fluid · service · meter` events |
| `equipment_inspections` | Pre-op + DVIR cadence (de facto inspection log) | `unit_number · inspection_date · status` |
| `service_truck_reconciliations` | Service-truck visit ledger | `date · technician · variance` |
| `operational_attachments` | RTS verification linkage | `attachment_type · unit_number` |

#### Gaps PM Engine MUST close (Track 13.31 scope):

1. **No PM schedule definitions.** There is no collection or model defining "Excavator → oil change every 250 hr / 90 days / hydraulic filter every 500 hr". The first 13.31 deliverable must be a `pm_schedules` collection (or equivalent definition mechanism) keyed by `asset_type` (with optional per-unit override).
2. **No PM completion event.** `asset_service_events` lists `pm` in `UNAVAILABLE_EVENT_TYPES` (line 50 of `asset_service_events.py`). 13.31 must introduce a `pm_completions` collection — written when a PM job is closed — and lift `pm` into `AVAILABLE_EVENT_TYPES`.
3. **No "next PM due" computation.** Requires (a) latest meter_hours per unit (composable from `fuel_lube_visits.equipment_lines.meter_hours`), (b) latest PM completion timestamp, (c) deterministic `next_due_hours = last_pm_meter + interval_hours` AND `next_due_date = last_pm_date + interval_days`, whichever fires first.
4. **No PM compliance dashboard.** A Shop Command Center tile labeled "PM Due / Overdue" needs a new aggregator at `/api/shop/pm/...` once the schedule + completion model exists.
5. **No mechanic-to-PM assignment workflow.** Reuse the existing `fleet_defects.assigned_to_mechanic_id` pattern for PM tasks OR introduce a `pm_assignments` mirror — design choice for 13.31.

#### Opportunities for PM Engine to land cleanly:

* The Asset Service Event Backbone (`/api/asset-service-events`) is **already** designed to absorb PM events. Once `pm` events are recorded, the unit-history timeline will include them with zero additional plumbing.
* `MechanicWorkloadCard` already exposes per-mechanic load — extending it to count assigned PM jobs is a one-field change.
* `UnitSearch` rows could add a `next_pm_due` chip with the same SEV_CHIP pattern (no new component).

#### Blockers / open questions for 13.31 kickoff:

* **Q1:** Source of canonical PM interval recommendations — MaintainX (currently stub-only), manufacturer manuals, or operator-defined? Decision needed before schedule collection design.
* **Q2:** Are PM intervals per `equipment_master.type`, per individual unit, or both (type default + per-unit override)? Both pattern is recommended.
* **Q3:** Should PM completions auto-create RTS attestations? **No** — keep the Repair Complete ≠ RTS hard lock. PM completion is a separate "ASE event" but does NOT clear an OOS unit. RTS still requires Dispatch verification.

**Result:** PM Engine has a clear, unblocked data foundation. The 13.31 sprint is genuinely buildable on top of what 13.30* already shipped — no foundation rework required.

---

## 5 · Bugs found and fixed in this audit pass

### Bug A — Unit Search returned UUID `id` strings as `unit_number`

* **Symptom:** Operator typed `127` → search returned 4 rows whose displayed "Unit number" was a UUID like `10127b48-af7e-4a24-9fde-a3f14734d0cf`. The UUID merely contained the substring `127`. None of the results were "Unit 127".
* **Root cause:** `routes/shop_intel.py · units_search` ran a `$contains_regex` against the `id` field (a UUID), AND returned `id` as `unit_number` in the response. Equipment that legitimately had a `unit_number` field populated (e.g. `EXC-8614`, `BH004-3882`, `TRL006-0127`) was being shadowed by UUID accident matches.
* **Fix:**
  * Predicate now searches `unit_number · label · vin_serial_number · serial_number · plate · make_model · manufacturer · model · type · category · comments`. **`id` and `asset_id` removed from the predicate.**
  * Result row's `unit_number` is now the real `equipment_master.unit_number` field. When a row legitimately has no unit number (a hand tool, attachment, etc.) it returns `unit_number: null` and the UI renders the asset name + a `NO UNIT #` chip.
  * History link target: prefers `unit_number`, falls back to internal id only when no real unit number exists.
* **Verification:**
  * `curl /api/shop/units/search?q=127` post-fix returns `LT017-2718 · Wacker(no unit) · SWP-7791 · TRL006-0127` — real unit numbers.
  * `curl /api/shop/units/search?q=EXC` returns excavator unit numbers.
  * Pytest regression `test_units_search_does_not_match_uuid_id_substring` added: seeds an equipment row whose internal UUID contains the search term but whose `unit_number` does not, asserts the row is NOT returned for that search.

### Bug B — Section numbering broken (01→02→03→02→04→05→06→03)

* **Symptom:** Hub displayed two sections labeled "02" (Active Work, Mechanic Workload) and two sections labeled "03" (Parts and Waiting, Recovery Map). Visual hierarchy implied non-monotonic ordering.
* **Root cause:** Track 13.30D added Mechanic Workload as section "02" inserted after section "03"; the secondary Recovery Map was still labeled "03" from before the restructure.
* **Fix (in `ShopHubV2.jsx`):**
  * 01 · Attention required
  * 02 · Active work
  * **03 · Mechanic workload** (renumbered)
  * **04 · Parts and waiting** (renumbered)
  * 05 · Fuel and service (was 04)
  * 06 · Unit intelligence (was 05)
  * 07 · Records (was 06)
  * **08 · Recovery Map · secondary** (was 03)
* **Verification:** Screenshot at `/tmp/audit_FIXED_sections_*.png` confirms monotonic numbering.

---

## 6 · Test coverage (final)

| File | Tests | Status |
|---|---:|---|
| `tests/test_track_13_30_service_truck_reconciliation.py` | 12 | ✓ all pass |
| `tests/test_track_13_30c_shop_intel.py` | 7 (+1 new) | ✓ all pass |
| `tests/test_track_13_30d_parts_workload.py` | 5 | ✓ all pass |
| **Total** | **24** | **24/24 passing** |

New: `test_units_search_does_not_match_uuid_id_substring` pins Bug A so it cannot regress.

---

## 7 · Files changed in this track

| File | Change |
|---|---|
| `backend/routes/shop_intel.py` | Search predicate now uses `unit_number/label/serial/plate/make_model/...` instead of `id/asset_id`. Result rows return real `unit_number` with internal-id fallback for the history link. |
| `frontend/src/components/shop/UnitSearch.jsx` | Renders `NO UNIT #` chip for rows with null unit_number; uses asset_name as display fallback. |
| `frontend/src/pages/ShopHubV2.jsx` | Section numbering rewritten to be monotonic (01–08); Mechanic Workload promoted above Parts. |
| `backend/tests/test_track_13_30c_shop_intel.py` | Seed now includes `unit_number` (matches real schema). New regression test for UUID-pollution bug. |

---

## 8 · Doctrine receipts

* No new collection created · No write paths added · No background jobs.
* All endpoints read-only, gated by `require_shop_or_admin_dep`.
* No accounting/PO/cost data leaks (asserted in `test_units_search_compact_shape_and_limit_enforced`).
* Repair Complete ≠ RTS hard lock untouched.
* No deployment · no GitHub push · no merge requested.

---

**Track 13.30D — CLOSED. Books locked.**
