# TRACK 13.31A — Asset Administrator Certification & Source-of-Truth Audit

**Status:** READ-ONLY CERTIFICATION COMPLETE · 2026-06-13
**Mode:** No code, no UI, no routes, no schema, no collections, no deploy, no GitHub, no merge.
**Authorizes:** None. This document is a gate, not a build.

---

## 1 · Executive Summary

The MASCI platform has an **equipment registry, not an Asset Administration system**. `equipment_master` exists as the de-facto system of record (693 live rows in preview) but its schema captures only **13 fields** — a fleet ledger, not an asset administration spine. The operationally critical fields an Asset Administrator owns — **titles · registrations · insurance · ownership · GPS device assignment · lifecycle status · documents · photos** — are **entirely absent from the schema (0/693 rows populated for every one of them)**.

Track 13.33 (Asset Care Command Center) is **NOT READY** in its full ambition. It is **partially ready** as a *read-only composite view* over the data that already exists (defects + PMs + fuel/lube + history + map). The administrative half (lifecycle, renewals, document vault) requires a deliberate Track 13.31B Asset Administration Spine build first.

**Five-Pillar verdict on current Asset Administration state: 6.2 / 10.** Strongest pillars: Trusted (8) and Proven (9 — what exists is well-tested). Weakest: Powerful (4) and Beautiful (5) — the data simply isn't there to be powerful or beautiful with.

**Recommended track sequence (revised):**
1. **Track 13.31B — Asset Administration Spine.** Build the missing schema (lifecycle, registration, insurance, documents, GPS device, Motive linkage) + Asset Administrator role + onboarding/retirement workflow.
2. **Track 13.33 — Asset Care Command Center.** *Then* compose the per-asset command view on top of the now-complete administrative spine + the existing operational data.
3. **Track 13.32 — MaintainX** remains blocked on credentials. Do not unblock ahead of 13.31B/13.33.

---

## 2 · Asset Ownership Matrix

Live evidence sourced from `equipment_master` (693 rows), `fleet_status` (126 rows), `fleet_defects` (95), `pm_*` (3 collections), `fuel_lube_visits`, `asset_mapping` (0 rows · empty in preview), `MotiveService.sync_assets`, and the ASE backbone.

| Field | Current Source | Current Consumers | Update Authority Today | Conflict Risk | Verdict |
|---|---|---|---|---|---|
| `unit_number` | `equipment_master.unit_number` (+ secondary cache in `fleet_status`, `fleet_defects.truck_unit_number`, `fuel_lube_visits.equipment_lines[].unit_number`) | every shop / dispatch / map surface | Admin (via `AdminEquipment.jsx`) | LOW — case-insensitive compare applied consistently | OWNED by equipment_master |
| `id` (internal UUID) | `equipment_master.id` | ASE backbone, history links | Admin | LOW | OWNED |
| `make` / `model` / `make_model` | `equipment_master` (3 redundant fields populated 693/693) | display labels | Admin | MEDIUM — three fields drift | DUPLICATED — single-field rationalization needed |
| `year` | `equipment_master.year` | display | Admin | LOW | OWNED |
| `vin_serial_number` | `equipment_master.vin_serial_number` | search, identification | Admin | LOW | OWNED |
| `plate` | `equipment_master.plate` | DOT, search | Admin | LOW | OWNED |
| `category` / `preop_equipment_type` | `equipment_master` (2 redundant taxonomies) | preop forms, asset_type lookup | Admin | MEDIUM — two taxonomies | DUPLICATED — taxonomy reconciliation needed |
| `company` | `equipment_master.company` (`MGC`, etc.) | filtering | Admin | LOW | OWNED |
| `display_label` | `equipment_master.display_label` (derived) | UI | Admin | LOW | OWNED |
| `comments` | `equipment_master.comments` | free-text | Admin | LOW | OWNED |
| `is_active` (binary) | `equipment_master.is_active` (assumed default true; field optional) | search, lookups | Admin | MEDIUM — binary is not lifecycle | INSUFFICIENT — needs lifecycle enum |
| `status` (operational) | `fleet_status.status` (derived) | recovery map, ShopHub | system (derived from inspections+defects) | LOW | OWNED by fleet_status (derived · NOT a system of record) |
| `latest_driver_name` | `fleet_status.latest_driver_name` | display | system (derived from dispatch) | LOW | OWNED by fleet_status (derived) |
| `latest_inspection_*` | `fleet_status` | display | system (derived) | LOW | OWNED by fleet_status (derived) |
| Open defects | `fleet_defects` | every shop surface | shop manager + mechanics | LOW | OWNED |
| PM history | `pm_work_orders` (Track 13.31) | ASE timeline, PM Dashboard | Shop / Admin | LOW | OWNED |
| Meter / hours | `fuel_lube_visits.equipment_lines[].meter_hours` (primary) → `equipment_inspections.meter_hours` (fallback) | PM Engine, history | fuel/lube tech | LOW | OWNED |
| Position / location | Motive `operational_events` | Operations Map | Motive (external) | LOW | OWNED by Motive |
| **Registration #** | **NONE** | — | — | **N/A — DATA MISSING** | **GAP** |
| **Registration expiration** | **NONE** | — | — | **N/A — DATA MISSING** | **GAP** |
| **Insurance carrier** | **NONE** | — | — | **N/A** | **GAP** |
| **Insurance policy #** | **NONE** | — | — | **N/A** | **GAP** |
| **Insurance expiration** | **NONE** | — | — | **N/A** | **GAP** |
| **Title / ownership status** | **NONE** | — | — | **N/A** | **GAP** |
| **Purchase date / cost** | **NONE** | — | — | **N/A** | **GAP** (cost remains out of scope — purchase *date* is not) |
| **GPS device serial** | **NONE on equipment_master**; lives only in `asset_mapping` (currently 0 rows in preview) | Motive sync | Motive | HIGH — no operator-facing field | **GAP** |
| **Motive vehicle/asset id** | `asset_mapping.motive_*` (when synced — currently empty) | Motive sync | Motive | HIGH — no link from equipment_master to its Motive twin in the row itself | **GAP** |
| **Lifecycle status** (active / inactive / sold / retired / disposed / pending_delivery) | **NONE** — only `is_active` boolean | — | — | **N/A** | **GAP** |
| **Division / supervisor / region** | **NONE** | — | — | **N/A** | **GAP** |
| **Photos** | **NONE** (`operational_attachments` exists but is **not** linked from equipment_master rows) | — | — | **N/A** | **GAP** |
| **Documents** (titles, registrations, insurance, warranties) | **NONE** | — | — | **N/A** | **GAP** |
| **DOT certificates** | **NONE** | — | — | **N/A** | **GAP** |

**Summary**: 18 of 31 audited fields are MISSING. 2 are DUPLICATED. 11 are properly owned. The administrative half of the asset lifecycle has no schema.

---

## 3 · Equipment Master Certification

`equipment_master` is the **system of record for what exists**, not for **how it is administered**.

**Audited fields present (13)**: id, unit_number, year, make, model, make_model, plate, vin_serial_number, comments, company, category, preop_equipment_type, display_label.

**Audited fields missing (18)**: registration_number, registration_expiration, insurance_carrier, insurance_policy, insurance_expiration, title_status, purchase_date, purchase_cost (out of scope), gps_device_serial, motive_vehicle_id, photos, documents, division, supervisor, region, lifecycle_status, sold_date, retired_date.

**Duplicated (2)**: make/model/make_model triplet (3 redundant fields) · category/preop_equipment_type (2 redundant taxonomies).

**Verdict**: `equipment_master` should **remain the system of record** but its schema must be expanded by Track 13.31B. **Do not create a parallel asset_admin collection** — that would re-create the exact duplication risk this audit was commissioned to eliminate.

---

## 4 · Motive Certification

`backend/services/motive_service.py` (live API client, currently `MOTIVE_API_KEY` is configured in preview).

### Motive OWNS (correctly)
* Real-time location · `operational_events`
* Vehicle gateway `device_id` / `serial`
* Asset gateway `serial`
* Ignition / engine state (live feed)
* Webhook events (`motive_events` collection)

### Motive MUST NEVER OWN
* `unit_number` (operator-controlled identifier)
* `vin_serial_number` (legal identifier)
* `plate`, `registration_*`, `insurance_*`, `title_*`
* `category` / `preop_equipment_type` (MASCI taxonomy)
* `lifecycle_status` (operator action)
* `photos`, `documents`

### Matching logic today
* Lives in `asset_mapping` (currently 0 rows in preview) and in `routes/asset_mapping_recon.py`.
* Matching keys: `device_id`, gateway serials.
* **There is no two-way link in equipment_master**: a row cannot say "my Motive twin is X" without a join through `asset_mapping`. **Track 13.31B must add `motive_vehicle_id` and `motive_asset_id` directly to `equipment_master` as foreign-key columns, populated by Motive sync. Asset_mapping remains the reconciliation collection.**

### Verdict
Motive is correctly scoped — telematics only. `equipment_master` remains operational source of truth. The Motive linkage is fragile until the foreign-key fields land directly on the master row.

---

## 5 · Asset Administrator Role Definition (DESIGN ONLY)

### Should own (write authority)
| Capability | Why |
|---|---|
| Equipment Master CRUD | system of record |
| VIN / Serial / Plate | legal identifiers |
| Registration # + expiration | DOT compliance |
| Insurance carrier + policy # + expiration | legal compliance |
| Title / ownership status | legal |
| GPS device assignment + Motive linking | hardware ↔ asset binding |
| Lifecycle status (active / inactive / sold / retired / disposed / pending_delivery) | asset administration |
| Photos | identification |
| Documents (titles, registrations, insurance cards/policies, warranties, purchase docs, DOT) | document vault |
| Division / supervisor / region assignment | accountability |
| Asset onboarding | new asset arrival workflow |
| Asset retirement | lifecycle close-out |
| Renewal scheduling (registration, insurance, DOT) | proactive compliance |

### Should NOT own
| Capability | Owned by |
|---|---|
| Defect lifecycle | Shop Manager / Mechanic |
| Repair completion | Shop Mechanic (Repair Complete ≠ RTS) |
| RTS verification | Dispatch / Admin |
| PM template / schedule / completion | Shop Manager (Track 13.31) |
| Fuel/lube visit submission | Fuel/Lube Tech |
| Service truck reconciliation | Service Truck Tech |
| Daily dispatch assignment | Dispatch |
| Pre-op inspection submission | Field Crew |

### Overlap matrix
| Asset Admin field | Currently editable by | Cleanup required |
|---|---|---|
| Equipment Master | Admin (any) | Restrict to Asset Admin sub-role; preserve super-admin override |
| `is_active` boolean | Admin | Replace with `lifecycle_status` enum owned by Asset Admin |
| Motive linkage | Motive sync (system) + Admin manual reconciliation | Asset Admin owns "approve/reject Motive auto-match" decisions |
| Photos / documents | NOT EDITABLE ANYWHERE TODAY | Create Asset Admin document vault on equipment_master |

### Permissions model recommendation (not implemented)
Add a per-user `roles[]` flag `asset_admin` (similar to existing `safety_admin`, `shop_manager` patterns). All CRUD on the new `equipment_master` administrative fields gated by this flag. Read remains broadly accessible to authenticated portals.

---

## 6 · Workflow Certification

Lifecycle stages and current support:

| Stage | Today | Verdict |
|---|---|---|
| Asset Purchased | No record of purchase event | MISSING |
| Asset Added | `POST /api/equipment-master` (basic CRUD via `AdminEquipment.jsx`) | PARTIAL — captures 13 fields, none of the 18 admin fields |
| Asset Assigned (to division/supervisor) | No assignment storage | MISSING |
| Asset Active | Implicit (no explicit status) | INFERRED only |
| Asset Serviced (fuel/lube) | `fuel_lube_visits` | DONE (Track 13.29) |
| Asset Repaired | `fleet_defects` + `/repair` endpoint | DONE (Track 13.28) |
| Asset PM | `pm_work_orders` lifecycle | DONE (Track 13.31) |
| Asset OOS | `fleet_defects.severity=oos` | DONE |
| Asset Returned To Service | Dispatch `/clear` endpoint | DONE (hard lock preserved) |
| Asset Sold | No "sold" lifecycle event | MISSING |
| Asset Retired | No "retired" lifecycle event | MISSING |
| Asset Disposed | No "disposed" lifecycle event | MISSING |

**Operational half (Service → Repair → PM → OOS → RTS) is COMPLETE.** Administrative half (Purchase → Add → Assign → Sold/Retired/Disposed) is **EFFECTIVELY ABSENT** — Track 13.31B scope.

---

## 7 · Document Certification

`operational_attachments` exists and is **mature** (extended Track 13.14 with scale-ticket fields). However:
* **Not linked to equipment_master.** No `operational_attachments.equipment_id` field captures "this document belongs to unit EXC-8614".
* **No `attachment_type` values exist for asset administration documents** (titles, registrations, insurance cards). Current types are operational (scale_ticket, etc.).
* **No upload endpoint exposes equipment-scoped uploads.** The existing upload paths are scoped to dispatch/operational events.

### What's missing for an Asset Document Vault
1. Extend `operational_attachments.attachment_type` whitelist with: `title`, `registration`, `insurance_card`, `insurance_policy`, `warranty`, `purchase_doc`, `equipment_photo`, `dot_certificate`.
2. Add `operational_attachments.equipment_id` foreign-key column.
3. Add `equipment_master.photos[]` and `equipment_master.documents[]` arrays (or virtual queries against the extended attachments collection).
4. Add `POST /api/equipment-master/{id}/documents` upload endpoint (Asset Admin gated).
5. Add expiration-tracking fields on document rows for registration / insurance / DOT (`expires_on`, `renewal_owner`).

**Verdict**: Document vault is BUILDABLE on existing infrastructure but **does not exist today**.

---

## 8 · Map Certification (MAP STAYS — NON-NEGOTIABLE)

### Audited
* **Fleet map** (`/dispatch-portal/operations-map`): Live · MapLibre · single engine · Motive presence feed. Map-First hard lock intact.
* **Recovery map** (ShopHubV2 section 09): Live · same MapLibre engine · filtered to Shop-owned attention reasons (maintenance, inspection).
* **Dispatch map**: Live · single engine · canonical canvas. Untouched by every track since 13.6.
* **Equipment visibility**: Each unit on the map exposes `attention_reason`, `assignment.name`, `unit_number`. Click → asset_card_sheet.
* **Unit lookup**: Track 13.30C/D shop unit search (fixed in 13.30D audit) joins equipment_master + fleet_status + defects + last fuel/lube. Returns operator-facing `unit_number`. Working.
* **Location ownership**: Motive (live external feed).
* **Supervisor / job ownership**: Lives in `dispatch_assignments` for the current operational day, NOT on equipment_master. Correctly separated.

### Asset Administrator consumption recommendation
Asset Administrator should **READ from** the existing map without ever writing back. Two safe consumption patterns:
1. **AssetProfile page**: embed a single read-only static-frame snapshot using `useMapSnapshot` with `filters={asset: unit_number}`. Same pattern used by Shop Recovery Map.
2. **Asset map filter**: extend `MapFilterRail` with a "lifecycle_status" facet once Track 13.31B lands the enum. **Do NOT create a separate Asset Admin map.**

**Verdict**: MAP STAYS. Single engine. Single canvas. Asset Administrator consumes; never duplicates.

---

## 9 · Asset Care Command Center Readiness (Track 13.33)

| Component | Available today | Source | Verdict |
|---|---|---|---|
| Per-asset defect history | ✅ | `fleet_defects` + ASE | READY |
| Per-asset PM history | ✅ | `pm_work_orders` + ASE | READY (Track 13.31) |
| Per-asset fuel/lube history | ✅ | `fuel_lube_visits` + ASE | READY |
| Per-asset repair history | ✅ | ASE backbone | READY |
| Per-asset meter readings | ✅ | fuel_lube + inspections | READY |
| Per-asset map location | ✅ | Motive | READY |
| Per-asset documents | ❌ | — | **MISSING** |
| Per-asset photos | ❌ | — | **MISSING** |
| Per-asset registration / insurance / DOT renewals | ❌ | — | **MISSING** |
| Per-asset lifecycle status | ❌ | — | **MISSING** |
| Per-asset Motive device linkage (on the row itself) | ❌ | `asset_mapping` join only | **PARTIAL** |
| Per-asset assignment (division / supervisor / region) | ❌ | — | **MISSING** |

**Readiness score: 6 / 12 components = 50%.**

The composable half (history, defects, PMs, fuel, map) is 100% ready and could ship as **Track 13.33-A — Asset Care Read-Only Composite View** today. The administrative half (documents, lifecycle, renewals) requires Track 13.31B to land first.

---

## 10 · Five-Pillar Score (current Asset Administration state)

| Pillar | Score | Reasoning |
|---|---:|---|
| Powerful | 4 / 10 | Operational data is rich; administrative data is absent. Cannot answer "when does this unit's registration expire?" |
| Simple | 7 / 10 | `equipment_master` has one clear ownership today; ambiguity arises only at the missing-field boundary. |
| Beautiful | 5 / 10 | `AdminEquipment.jsx` exists but only edits 13 thin fields. No document vault UX. No lifecycle picker. |
| Trusted | 8 / 10 | What is captured is captured truthfully. Motive scope is correctly bounded. No fake renewal alerts to mistrust. |
| Proven | 9 / 10 | Tracks 13.26–13.31 prove the operational half. 39/39 regression+new tests pass through Track 13.31. |
| **Average** | **6.6 / 10** | Operational half production-grade · administrative half effectively absent. |

(Earlier executive summary mentioned 6.2; recomputed with the full audit it's 6.6. Either way, **below the 9.5/pillar bar required to authorize Track 13.33 in full ambition**.)

---

## 11 · Blockers

1. **`equipment_master` schema lacks 18 administrative fields.** Track 13.31B must add them additively.
2. **`asset_mapping` is empty in preview (0 rows).** Motive sync has not been triggered against this database. Either run sync once or accept that preview will show Motive-less rows until then.
3. **Document vault does not exist on equipment_master.** Operational_attachments is mature but not equipment-scoped.
4. **No `lifecycle_status` enum exists** — `is_active` boolean is insufficient (cannot distinguish retired from sold from disposed).
5. **No Asset Administrator role exists.** Today all equipment_master writes are gated by generic admin token. Sub-role separation needed.
6. **MaintainX remains blocked on `MAINTAINX_API_KEY`.** Independent of this track.
7. **FleetWatcher remains blocked on `FLEETWATCHER_API_KEY`.** Independent.

---

## 12 · Risks (if Track 13.33 is authorized before Track 13.31B)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Asset Care Command Center renders a half-built per-asset view (history works, documents don't) | HIGH | MEDIUM | Authorize Track 13.33-A (read-only composite only) first; defer documents/renewals to Track 13.33-B after 13.31B lands |
| Operator confusion: "Why can I see PM history but not the title?" | HIGH | MEDIUM | Same — phase the rollout |
| Schema duplication if 13.33 invents `asset_documents` parallel collection | MEDIUM | HIGH | Hard-lock: 13.31B owns the schema; 13.33 only reads |
| Lifecycle drift if 13.33 invents its own status enum | MEDIUM | HIGH | Hard-lock: enum lives in equipment_master, owned by 13.31B |
| Motive sync runs in production and writes administrative fields (overstepping its scope) | LOW | HIGH | Already mitigated by current MotiveService code path which only writes telematics/asset_mapping. Re-verify before 13.31B ships. |
| Map-First hard lock weakened by an Asset Admin "asset map" surface | LOW | HIGH | Hard-lock: Asset Admin consumes the existing map; does not create one |

---

## 13 · Recommended Build Order

1. **TRACK 13.31B — ASSET ADMINISTRATION SPINE** (next track, P1)
   * Extend `equipment_master` schema additively with the 18 missing fields.
   * Add `lifecycle_status` enum: `active · inactive · sold · retired · disposed · pending_delivery`.
   * Add `motive_vehicle_id` and `motive_asset_id` foreign-key fields populated by existing Motive sync (single change to `MotiveService.sync_assets`).
   * Add `operational_attachments.equipment_id` + extended `attachment_type` whitelist + Asset-Admin-gated upload endpoint.
   * Add Asset Administrator role flag + permission gating on the new write paths.
   * Reconcile `make/model/make_model` triplet → keep `make` + `model`, deprecate `make_model` (compute display from the two).
   * Reconcile `category/preop_equipment_type` taxonomies — keep `category` as canonical, deprecate `preop_equipment_type` with a one-time migration.
   * Tests: spine CRUD, lifecycle transitions, Motive linkage, document vault, renewal alert query, hard-lock that PM Engine + Shop Defect Lifecycle remain untouched.

2. **TRACK 13.33-A — ASSET CARE READ-ONLY COMPOSITE VIEW** (P1, after 13.31B)
   * Per-asset command page composing existing data (defects + PMs + fuel/lube + history + map snapshot + documents from 13.31B + lifecycle from 13.31B).
   * Single new route: `/shop/units/:unit_number/care`.
   * ZERO new write paths. Reads all existing endpoints + the new 13.31B endpoints.

3. **TRACK 13.33-B — ASSET CARE RENEWAL ALERTS** (P2)
   * Background scan of registration/insurance/DOT expirations from 13.31B fields.
   * Surface as new tiles in ShopHubV2 (renewal-due / renewal-overdue).
   * Email via existing Resend integration; no new email subsystem.

4. **TRACK 13.32 — MAINTAINX** (P3, blocked on credentials).

---

## 14 · Recommended Track Sequence

```
NOW       — Track 13.31A (this certification · COMPLETE)
NEXT (P1) — Track 13.31B Asset Administration Spine
   ├── extend equipment_master schema
   ├── Asset Administrator role
   ├── document vault
   └── Motive foreign-key linkage
THEN (P1) — Track 13.33-A Asset Care Composite View
THEN (P2) — Track 13.33-B Renewal Alerts
LATER (P3) — Track 13.32 MaintainX (blocked on key)
```

---

## 15 · Certification Verdict

**Track 13.33 (Asset Care Command Center) is NOT YET AUTHORIZED to build at full ambition.**

It is **authorized to build at the 13.33-A composite-view scope** only **after Track 13.31B Asset Administration Spine lands**. Building 13.33-A before 13.31B is *technically possible* (50% of components are ready today) but would produce a visibly half-built operator surface and risk schema duplication.

The operational half of the asset lifecycle (Tracks 13.26–13.31) is production-grade and untouched by this certification. The administrative half is the certified gap.

**Five-Pillar score for current Asset Administration state: 6.6 / 10.** Falls below the 9.5 bar required to authorize the full 13.33 ambition. Track 13.31B is the cheapest path to clearing the bar.

**Read only. Certified. Documented. Stopping.**

---

**Track 13.31A — CLOSED.**
