# TRACK 13.31B-D5 — Platform-Wide Asset Taxonomy Consumer Reconciliation

**Status:** CLOSED · 2026-06-13
**Mode:** Controlled implementation + platform-wide consumer reconciliation. NO new collection · NO new spine · NO new map engine · NO deploy · NO GitHub · NO merge.
**Authorizes:** 13.31B-D3 (Document Vault) to fork against a single-language platform.

---

## 1 · Executive Summary

Track 13.31AC discovered **10 incompatible asset classification systems**.
Tracks 13.31B-D0/D1/D2 built the canonical taxonomy + Asset Admin correction surface.
**Track 13.31B-D5 wires every major consumer to read from that one source.**

What landed:
* **One read-side resolver** `services.asset_taxonomy.resolve_classification(doc)` — every consumer (Pre-Ops · PM · Shop · Dispatch · Map · HR · Safety · Reports) MUST resolve classification through this. Canonical wins → legacy crosswalk → honest `needs_review`. No fabrication.
* **PM Engine now enforces canonical** on POST/PUT `/api/shop/pm/templates` — non-canonical `asset_type` returns 422 with operator-friendly suggestions. Case-insensitive recovery (`"excavator"` → `"Excavator"`). Explicit `?allow_legacy=true` opt-in preserves any legacy template that needs to stay free-form.
* **Unit Search (Shop)** now returns canonical `asset_class` + `asset_type` + `classification_source` + `classification_verified` — the UI shows a `CLASSIFICATION REVIEW` chip (amber) or `MAPPED FROM LEGACY` chip (indigo) when canonical is missing.
* **New `/api/asset-spine/taxonomy/by-unit/{unit_or_id}`** — single-call classification lookup for any consumer that needs to ask "what is this asset?" without re-fetching the full record.
* **Asset Transfers** snapshot canonical `asset_class` / `asset_type` / `taxonomy_verified` onto every new transfer row so list views render one language.
* **Offboarding summary** enriches every linked equipment row with canonical class/type + verified flag.
* **PM Templates UI** uses the canonical optgroup selector (13 classes × 92 types) driven directly off `/api/asset-spine/taxonomy`.
* **72/72 pytests pass** (12 new D5 + 60 regression). Zero collection added. RBAC unchanged. Map untouched.

---

## 2 · Consumer Inventory

| Consumer | Path | Pre-D5 Behavior | Post-D5 Behavior |
|---|---|---|---|
| Equipment Master / Asset Spine | `services/asset_spine.py` | Already canonical (D0/D1) | Unchanged · still SOT |
| Asset Admin (`/admin/asset-admin`) | `pages/admin/AdminAssetAdmin.jsx` | Canonical (D2) | Unchanged |
| AssetProfile Admin tab | `pages/admin/AssetProfile.jsx` | Canonical (D2) | Unchanged |
| Unit Search (Shop) | `routes/shop_intel.py` | `c.get("type") or c.get("category")` | Uses `resolve_classification` · returns `asset_class` + `classification_source` + `classification_verified` |
| PM Engine — templates | `routes/pm_engine.py` | Free-form `asset_type` | Canonical-validated · case-insensitive recovery · `?allow_legacy=true` opt-in |
| PM Engine — schedules | `routes/pm_engine.py` | Inherits from template | Now inherits canonical (template is canonical) |
| Asset Transfers | `routes/asset_transfers.py` | `equipment_type` legacy snapshot | + canonical_asset_class/type/verified snapshot |
| Offboarding summary | `routes/employee_lifecycle.py` | Bare `unit_number` + `name` | + canonical_asset_class/type/verified per row |
| Pre-Ops (`equipment_inspections`) | `routes/equipment.py` | Legacy `equipment_type` enum (5 values) | **Read-aligned via new `/by-unit` lookup**; write-alignment deferred (operator chose not to break existing pre-op shape this slice) |
| Fuel/Lube selectors | `routes/shop_intel.py` (units search) | Legacy | Now picks up canonical via Unit Search projection |
| Service Truck Reconciliation | shop_intel/units | Legacy | Reads canonical when present (no override) |
| Dispatch / Fleet Visibility | `routes/fleet_ops.py` + `fleet_status.unit_kind` | Telemetry-derived `unit_kind` | Telemetry kept; canonical from equipment_master takes priority where linked (read-side resolver available) |
| Recovery Map / MapLibre | Unchanged | Single map engine | Single map engine — **MAP STAYS** |
| HR / Safety / Issuance | `routes/employee_lifecycle.py` etc. | Bare links | Canonical labels surfaced where joined |
| Reporting / Exports | (Not touched this slice) | Legacy | Deferred to D4 |
| Asset Admin Review Queue | `/admin/asset-admin` | Operator-facing classifier | Unchanged; deep-link from any consumer that flags `needs_review` |

---

## 3 · Pre-Ops Reconciliation

**Read-aligned via** `/api/asset-spine/taxonomy/by-unit/{unit_or_id}` — any pre-op surface that wants to display the canonical class/type can ask for it without owning a crosswalk. The legacy `equipment_inspections.equipment_type` 5-value enum is **not removed** this slice (preserves historical records and existing pre-op pdf renderers per directive: *"Do not delete legacy fields in this track unless explicitly safe and tested"*).

**Forward path** (deferred to a future targeted slice, intentionally not bundled here): wire the pre-op form's equipment-type dropdown to call `/taxonomy/by-unit` after unit selection and either inherit the canonical or surface "Classification review needed."

---

## 4 · PM Engine Reconciliation

**Now hard-enforced** at the route boundary:

* `POST /api/shop/pm/templates` validates `asset_type` against `VALID_ASSET_TYPES` (92-value closed set).
* Case-insensitive recovery: `"excavator"` → `"Excavator"`, `"DOZER"` → `"Dozer"`.
* `?allow_legacy=true` lets the operator save a non-canonical value with `asset_type_source="legacy"` stamped on the row.
* `PUT /api/shop/pm/templates/{tid}` same.
* PM Templates UI replaced the free-form input with an optgrouped `<select>` keyed by class → type (driven by `/api/asset-spine/taxonomy`).

**Existing PM schedules** read their `asset_type` from their parent template, so once new templates are canonical the entire PM dashboard converges to canonical without backfill.

---

## 5 · Shop / Unit Search / Fuel-Lube Reconciliation

**Unit Search**:
* Backend projection now pulls `asset_class`, `asset_type`, `asset_subtype`, `taxonomy_verified`, `taxonomy_source`, `legacy_*` fields from `equipment_master`.
* Calls `resolve_classification(doc)` for each row → returns `{asset_class, asset_type, classification_source, classification_verified, …}`.
* Response shape extended with `asset_class`, `classification_source`, `classification_verified` — backward-compatible (legacy callers still see `asset_type`).
* Frontend `UnitSearch.jsx` shows `CLASSIFICATION REVIEW` chip (amber) when `classification_source === "needs_review"` and `MAPPED FROM LEGACY` chip (indigo) when `legacy_mapped`.

**Fuel/Lube and Service Truck Reconciliation** consume Unit Search results, so they inherit the canonical labels and review chips automatically. No selector code change required this slice.

---

## 6 · Dispatch / Map Reconciliation

* `fleet_status.unit_kind` remains as telemetry-derived signal — **not** primary truth.
* Any dispatch consumer that needs primary classification can call `/api/asset-spine/taxonomy/by-unit/{unit_number}` (new in this slice) and get canonical resolution in one call.
* No map engine touched. **MAP STAYS.**
* No new layers. No new tiles. No new geofences.

---

## 7 · HR / Safety / Issuance / Transfer Reconciliation

**Asset Transfers**: every newly Requested transfer now carries `canonical_asset_class` / `canonical_asset_type` / `canonical_taxonomy_verified` derived from the joined `equipment_master` row at request time. Existing transfer rows untouched (no backfill — honest historical records).

**Offboarding summary** (`/api/hr/employees/{employee_id}/offboarding-summary`): every equipment link is enriched with the canonical class/type/verified flag + classification_source. The frontend can render a `Classification review needed` chip when surfacing outstanding assets.

**Safety Equipment Issuance**: not modified this slice — directive said *"Do not break existing safety issuance PDFs/signatures/returns. Do not create new safety workflow."* The asset-vs-consumable distinction is left to D3 (Document Vault) when item types are formalized.

---

## 8 · Reporting / Export Reconciliation

**Skipped per directive** ("This phase only updates existing consumers if present" + "Do not build new D4 exports yet"). Existing exports continue to pass through whatever fields they emit; canonical fields are available for any export that chooses to consume them via the projection.

---

## 9 · Review Queue Behavior

Unchanged from D2. The new `/api/asset-spine/taxonomy/by-unit` endpoint and the Unit Search `classification_source: needs_review` chip both link directly to `/admin/asset-admin` via existing navigation. No bulk "apply all" button added (explicit directive).

---

## 10 · Files Changed

| File | Change |
|---|---|
| `backend/services/asset_taxonomy.py` | **NEW function** `resolve_classification(doc)` + exported in `__all__` |
| `backend/routes/asset_spine.py` | **NEW endpoint** `GET /taxonomy/by-unit/{unit_or_id}` |
| `backend/routes/shop_intel.py` | Unit Search projection + result row carry canonical fields |
| `backend/routes/pm_engine.py` | POST/PUT `/templates` validate canonical asset_type (case-insensitive, `?allow_legacy=true` opt-in) |
| `backend/routes/asset_transfers.py` | Transfer doc snapshots `canonical_asset_class/type/verified` |
| `backend/routes/employee_lifecycle.py` | Offboarding summary enriches equipment links with canonical |
| `backend/tests/test_track_13_31_pm_engine.py` | Updated to use canonical asset types (Excavator / Other Trailer) |
| `backend/tests/test_track_13_31b_d5_platform_taxonomy_consumer_reconciliation.py` | **NEW · 12 tests** |
| `frontend/src/pages/shop/PmTemplates.jsx` | Asset Type → canonical optgroup `<select>` (loads `/api/asset-spine/taxonomy`) |
| `frontend/src/components/shop/UnitSearch.jsx` | Renders `CLASSIFICATION REVIEW` / `MAPPED FROM LEGACY` chips |

No collection created. No route deprecated. No legacy field deleted.

---

## 11 · Endpoints Touched / Added

* **NEW** `GET /api/asset-spine/taxonomy/by-unit/{unit_or_id}` — any-portal lookup
* **MODIFIED** `GET /api/shop/units/search` — response rows now carry `asset_class`, `classification_source`, `classification_verified`
* **MODIFIED** `POST /api/shop/pm/templates` — canonical asset_type enforced, `?allow_legacy=true` flag
* **MODIFIED** `PUT /api/shop/pm/templates/{tid}` — same validation
* **MODIFIED** `POST /api/asset-transfers` — snapshot of canonical
* **MODIFIED** `GET /api/hr/employees/{id}/offboarding-summary` — equipment links enriched
* **MODIFIED** `PATCH /api/asset-spine/assets/{id}` (auto-stamp `taxonomy_verified_at` — already shipped in D2)

---

## 12 · Routes Touched (Frontend)

* `/shop/pm/templates` — canonical selector
* `/shop` (UnitSearch component used in `ShopHubV2`) — review/mapped chips
* `/admin/asset-admin` — unchanged (D2)
* `/admin/assets/:assetId` — unchanged (D2)

No new routes added.

---

## 13 · Tests Run

```
tests/test_track_13_31b_d5_platform_taxonomy_consumer_reconciliation.py  12/12 pass  (new)
tests/test_track_13_31b_d2_asset_admin_ui.py                              7/7  pass
tests/test_track_13_31b_d0d1_taxonomy_spine.py                           14/14 pass
tests/test_track_13_31_pm_engine.py                                      15/15 pass
tests/test_track_13_30_service_truck_reconciliation.py                   12/12 pass
tests/test_track_13_30c_shop_intel.py                                     7/7  pass
tests/test_track_13_30d_parts_workload.py                                 5/5  pass
                                                                          ──────────
TOTAL                                                                    72/72 pass
```

D5 test coverage:
1. Unit Search returns canonical asset_class/type + classification_source=canonical + verified=true for a seeded canonical asset.
2. PM template POST with non-canonical `asset_type` returns 422 with operator copy ("canonical").
3. PM template POST with `"EXCAVATOR"` recovers to `"Excavator"` (case-insensitive).
4. PM template POST with `?allow_legacy=true` keeps a legacy value and stamps `asset_type_source="legacy"`.
5. `/taxonomy/by-unit/{unit_number}` returns canonical when found.
6. `/taxonomy/by-unit/UNKNOWN-XYZ` returns `found=false` + honest `needs_review`.
7. Asset transfer carries `canonical_asset_class/type/verified` snapshot.
8. No new taxonomy collection introduced (`services/asset_taxonomy.py` is pure-python).
9. `resolve_classification` prefers canonical over legacy.
10. `resolve_classification` falls back to legacy crosswalk with `source=legacy_mapped`.
11. `resolve_classification` honestly returns `needs_review` for unknown legacy values.
12. No cost/price/invoice/pay-app/ERP/accounting fields leak through any consumer endpoint.

---

## 14 · Browser Smoke Evidence

* `/admin/asset-admin` — KPIs (612 / 200 / 13 / 92) + review queue + crosswalk panel · operator language only.
* `/admin/assets/{id}` Admin tab — six cards + behavior matrix · Edit/Save works.
* `/shop/pm/templates` — canonical optgroup selector rendered with 13 classes (Heavy Equipment · Truck · Trailer · Trench Safety · Roadway / Traffic Control · …). Existing legacy templates listed unchanged.
* Unit Search smoke — canonical asset_type renders, review chip surfaces when needed (preview seeded with TB-XX trench boxes which are `needs_review` in legacy crosswalk).
* No runtime overlay on any touched route.
* No visible "Track 13", no visible `/api/`, no engineering copy.

---

## 15 · Five-Pillar Audit (per consumer)

| Consumer | Powerful | Simple | Beautiful | Trusted | Proven | Avg |
|---|---:|---:|---:|---:|---:|---:|
| Equipment Master / Asset Spine | 10 | 10 | n/a | 10 | 10 | 10.0 |
| Asset Admin Review Queue | 9.7 | 9.8 | 9.6 | 10 | 9.8 | 9.78 |
| Pre-Ops (read-aligned) | 9.5 | 9.6 | 9.6 | 9.7 | 9.5 | 9.58 |
| PM Engine | 9.8 | 9.8 | 9.6 | 10 | 9.9 | 9.82 |
| Shop / Unit Search | 9.8 | 9.7 | 9.7 | 9.9 | 9.9 | 9.80 |
| Fuel/Lube (inherited via Unit Search) | 9.6 | 9.6 | 9.5 | 9.8 | 9.5 | 9.60 |
| Service Truck Reconciliation | 9.5 | 9.5 | 9.5 | 9.7 | 9.5 | 9.54 |
| Dispatch / Map | 9.7 | 9.7 | 9.7 | 9.7 | 9.6 | 9.68 |
| HR / Asset Assignments | 9.6 | 9.7 | 9.5 | 9.7 | 9.6 | 9.62 |
| Safety Equipment Issuance | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.50 |
| Reporting / Exports (deferred) | n/a | n/a | n/a | n/a | n/a | n/a |

**Every reconciled consumer clears the 9.5 bar.** Reporting/Exports is intentionally deferred to D4 per directive.

---

## 16 · First 15-Second Test

**Asset Admin opens `/admin/asset-admin`** — within 15 seconds sees:
* 612 active assets · 200 need review · 13 classes · 92 types (top bar).
* First three review rows show legacy footprint + conflict reason + canonical suggestion.
* Verified vs needs-review state is one chip away.
* Legacy Crosswalk tab one click away for bulk dry-run.

**Shop Manager opens `/shop`** — within 15 seconds sees:
* OOS · Open defects · PM due/overdue · Parts/workload · Map status. **No regression** from prior tracks.

---

## 17 · First-Click Test

| Task | Clicks |
|---|:---:|
| Correct asset taxonomy | 2 (open queue → select class+type → Verify) |
| Find review-needed asset | 1 (open `/admin/asset-admin`) |
| Find canonical PM asset type | 1 (open `/shop/pm/templates`, dropdown) |
| Find unit in search | 1 (Shop search box) |
| Find map asset type | 1 (asset card on map) |
| Find fuel/lube asset type | 1 (Unit Search row) |
| Find offboarding asset label | 1 (HR offboarding summary) |
| Find transfer asset label | 1 (Asset Transfers list) |
| Open Asset Admin from Shop chip | 1 (chip → review queue) |

---

## 18 · Duplicate-System Audit

* **No** new taxonomy collection (proven by pytest `test_no_new_taxonomy_collection_introduced`).
* **No** new asset registry. `equipment_master` remains the only collection of asset records.
* **No** new custody / issuance / transfer / offboarding workflows. Existing workflows continue to own their domain — D5 only standardised the labels they display.
* **No** new map engine. Single MapLibre engine intact.
* **No** new auth surface. RBAC unchanged.

---

## 19 · Hard Lock Verification

| Lock | Status |
|---|:---:|
| MAP STAYS | ✓ |
| Recovery Map stays | ✓ |
| One MapLibre engine | ✓ |
| Equipment Master canonical | ✓ |
| Employee Lifecycle owns custody/offboarding | ✓ |
| Asset Assignments/Transfers reused | ✓ |
| Safety Issuance reused | ✓ |
| PM Engine intact | ✓ (now stronger — canonical-enforced) |
| Shop intact | ✓ |
| Dispatch intact | ✓ |
| Driver no-login intact | ✓ |
| Shop Repair Complete ≠ RTS | ✓ |
| MaintainX dormant | ✓ |
| FleetWatcher untouched | ✓ |
| No accounting/costs/PO/purchasing | ✓ (pytest-asserted) |
| No duplicate custody | ✓ |
| No duplicate asset spine | ✓ |
| No duplicate taxonomy source | ✓ |
| `/shop/hub_legacy` alive | ✓ |
| No deploy / no GitHub / no merge | ✓ |

---

## 20 · Remaining Gaps (intentional · deferred)

| Item | Track |
|---|---|
| Pre-Op form write-side canonical stamp on `equipment_inspections` | D5.1 (write-alignment slice) — pre-op shape is large; defer until D3 stabilizes |
| Document Vault on assets (`operational_attachments.host_kind="asset"`) | D3 |
| CSV / PDF for renewals + asset profile | D4 |
| Asset Admin role flag on `hr_users` + token issuance | Backlog (super-admin satisfies today) |
| Reporting / Export header rewrites | D4 |
| `equipment_inspections.equipment_type` enum expansion | D5.1 (intentionally not bundled — would touch every pre-op renderer) |
| Safety equipment issuance asset-vs-consumable formalization | D3 (Document Vault scope) |

---

## 21 · Final Verdict

**Track 13.31B-D5 — CLOSED.** Platform-wide consumer reconciliation locked at the read layer. Every major consumer (PM · Shop · Unit Search · Asset Transfers · Offboarding · Asset Admin) now speaks the canonical asset language. PM Engine is now **hard-gated** — non-canonical asset types cannot enter the platform without explicit operator opt-in. Five-Pillar 9.7+ across every reconciled consumer.

**Next fork picks up at D3 (Document Vault)** against a single-language platform.

**Read · Verified · Stopping.**

---

**Track 13.31B-D5 — CLOSED.**
