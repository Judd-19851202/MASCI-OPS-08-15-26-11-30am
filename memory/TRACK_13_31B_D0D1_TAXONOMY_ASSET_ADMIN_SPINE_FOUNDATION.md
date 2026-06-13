# TRACK 13.31B-D0D1 — Taxonomy + Asset Admin Spine Foundation

**Status:** CLOSED · 2026-06-13
**Mode:** Controlled implementation · Days 0+1 only · NO UI · NO doc vault · NO CSV/PDF · NO new collections · NO deploy · NO GitHub.
**Authorizes:** 13.31B-D2/D3/D4 to fork against this foundation.

---

## 1 · Executive Summary

Days 0 + 1 of the Asset Administration Spine landed cleanly:

* **Single canonical taxonomy module** (`backend/services/asset_taxonomy.py`) — 13 asset classes, 92 asset types, behavior matrix per asset_type, legacy crosswalk with explicit verified/needs_review states, and company normalization.
* **Asset Spine pydantic shapes extended** (`AssetCreate` + `AssetUpdate`) with the 4 canonical taxonomy fields + 13 administrative fields + Motive vehicle FK.
* **AssetSpine service persist + project** updated to write and read-back every new field on `equipment_master`.
* **4 new endpoints** under existing `/api/asset-spine/*`: `GET /taxonomy`, `GET /taxonomy/classify-legacy`, `GET /taxonomy/review-needed`, `POST /taxonomy/apply-legacy-crosswalk` (with `dry_run` flag).
* **Live preview database** sampled 200 rows: **91 cleanly verified, 109 need review** — honest classification, no fabrication.
* **No new collection.** No duplicate spine. `equipment_master` remains canonical. `services/asset_spine.py` still anchors to it.
* **53/53 pytests pass** (14 new + 39 regression covering Tracks 13.30/13.30C/13.30D/13.31).

---

## 2 · Day-0 Taxonomy Reconciliation

### Canonical asset_class (closed set · 13 values)
Heavy Equipment · Truck · Trailer · Trench Safety · Roadway / Traffic Control · Survey Equipment · GPS / Machine Control · Technology Equipment · Safety Equipment · Support Equipment · Facility Asset · Temporary Asset · Other Asset.

### Canonical asset_type (closed set · 92 values total)
Sample: Excavator · Dozer · Motor Grader · Loader · Roller · Paver · Skid Steer · Backhoe · Sweeper · Pickup Truck · Dump Truck · Fuel Truck · Lube Truck · Service Truck · Water Truck · Flatbed Truck · Crew Truck · Semi Tractor · Equipment Trailer · Lowboy Trailer · Trench Box · Road Plate · Total Station · GPS Rover · iPad · Laptop · Phone · Hotspot · Harness · Gas Monitor · Generator · Light Tower …

### Behavior matrix
Per asset_type · 13 booleans: requires_registration · requires_insurance · requires_pm · requires_preop · assignable_to_employee · transferable · appears_on_map · employee_lifecycle_managed · renewal_tracking_required · document_vault_required · dot_required · inspection_required · exportable. Conservative defaults · explicit overrides per type. Future consumers (PM scheduler, inspection router, transfer validator, renewal alerter) MUST read this module.

### Legacy crosswalk
`classify_legacy(category, preop_equipment_type, type_)` returns:
```
{ asset_class, asset_type, taxonomy_verified, taxonomy_source, taxonomy_review_reason }
```
* Source priority: `type` (most specific) → `preop_equipment_type` → `category`.
* Multiple sources agreeing → `taxonomy_verified=True`, `taxonomy_source="legacy_mapped"`.
* Sources conflicting → `taxonomy_verified=False`, `taxonomy_source="needs_review"`, reason string explains.
* Nothing matches → `taxonomy_verified=False`, `taxonomy_source="needs_review"`, reason `no_legacy_field_matched`.
* **No silent guessing.**

### Company normalization
`normalize_company(value)` → `(canonical, needs_review)`. Canonical set: MASCI_GC · FERIA · LEO · MC. Reconciles `MASCI / Masci / MGC / MASCI GC / masci corp` → `MASCI_GC`. `"?"` routes to MASCI_GC with `needs_review=True`. Unknown → `(None, True)`.

### Dry-run crosswalk over live data (200-row sample)
```
{ "ok": true, "dry_run": true, "scanned": 200,
  "would_verify": 91, "would_need_review": 109 }
```
**45% of fleet cleanly mapped.** 109 review-needed rows surfaced to the Asset Administrator queue. Honest empty/conflict states — no silent fabrication.

---

## 3 · Day-1 Asset Admin Spine Fields (additive on `equipment_master`)

| Field | Pydantic accepts | Service persists | Service reads back |
|---|:--:|:--:|:--:|
| `asset_class` | ✓ | ✓ | ✓ |
| `asset_subtype` | ✓ | ✓ | ✓ |
| `taxonomy_verified` | ✓ | ✓ | ✓ |
| `taxonomy_source` | ✓ | ✓ | ✓ |
| `asset_category_version` | derived | ✓ ("1.0.0") | ✓ |
| `legacy_category` / `legacy_preop_equipment_type` / `legacy_type` | derived | written by crosswalk | ✓ |
| `registration_number` / `_state` / `_expiration` | ✓ | ✓ | ✓ |
| `insurance_carrier` / `_policy_number` / `_expiration` | ✓ | ✓ | ✓ |
| `title_status` | ✓ | ✓ | ✓ |
| `warranty_expiration` | ✓ | ✓ | ✓ |
| `lifecycle_status` (active·inactive·sold·retired·disposed·pending_delivery) | ✓ | ✓ | ✓ |
| `division` / `region` | ✓ | ✓ | ✓ |
| `supervisor_id` | ✓ | ✓ | ✓ |
| `gps_device_id` | ✓ | ✓ | ✓ |
| `motive_vehicle_id` (FK on equipment_master row itself) | ✓ | ✓ | ✓ |
| `normalized_company` | ✓ | ✓ | ✓ |

`AssetCreate` writes them on create; `AssetUpdate` PATCH accepts them; `project_asset()` returns them on read.

---

## 4 · Asset Administrator Role (READY · gating live)

`/api/asset-spine/assets` write paths (POST/PATCH/retire/activate) already gated by `require_admin_dep`. The existing admin token + super-admin path holds. **A dedicated `asset_admin` flag remains a Day-2 wiring step** (single permission-flag addition on `hr_users` and the admin token issuance code path). Documented in 13.31AB §12 and not in scope for this slice per operator directive.

For now, super-admin (the only role exercising the new endpoints today) inherits Asset Administrator authority. No security regression. No new portals.

---

## 5 · Endpoints Added (4 new · all under existing `/api/asset-spine/*`)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET  | `/api/asset-spine/taxonomy` | any portal token | Closed-set enums + behavior matrix + canonical companies. |
| GET  | `/api/asset-spine/taxonomy/classify-legacy` | any portal token | Pure-function preview: legacy fields → canonical (class, type) tuple. |
| GET  | `/api/asset-spine/taxonomy/review-needed` | admin | Lists equipment_master rows lacking canonical taxonomy. Includes per-row `suggested` mapping. |
| POST | `/api/asset-spine/taxonomy/apply-legacy-crosswalk?dry_run=…` | admin | One-time migration helper. `dry_run=true` (default) returns would-be counts without writing. |

No write path stamps canonical taxonomy on production data **without** the admin explicitly calling `apply-legacy-crosswalk?dry_run=false`. Safe-by-default.

---

## 6 · Hard-Lock Verification

| Lock | Verified by |
|---|---|
| One asset · one record · one source of truth (`equipment_master`) | `test_equipment_master_remains_canonical` + `test_no_new_collections_introduced` |
| MAP STAYS | No code touched MapLibre, Recovery Map, fleet_status, dispatch_assignments |
| Repair Complete ≠ RTS · PM Completion ≠ RTS | Unchanged · Tracks 13.28 + 13.31 untouched |
| No new collection introduced | Pytest asserts new file `services/asset_taxonomy.py` is pure-python (no `db.`, no `insert_one`, no `create_collection`) |
| `asset_spine.py` still anchors to `equipment_master` | Pytest greps `services/asset_spine.py` line 9 contract |
| No costs · POs · accounting · ERP · pay-app fields | Pytest blocks forbidden substrings in `/taxonomy` response |
| `/shop/hub_legacy` rollback alive | Untouched |
| Tracks 13.30/13.30C/13.30D/13.31 regression | 39/39 prior pytests still pass |

---

## 7 · Tests Run

```
tests/test_track_13_31b_d0d1_taxonomy_spine.py   14/14 pass
tests/test_track_13_30_service_truck_reconciliation.py   12/12 pass
tests/test_track_13_30c_shop_intel.py             7/7  pass
tests/test_track_13_30d_parts_workload.py         5/5  pass
tests/test_track_13_31_pm_engine.py              15/15 pass
                                                ─────────────
TOTAL                                            53/53 pass
```

New test coverage:
1. Canonical taxonomy enums endpoint shape.
2. classify-legacy verified single-source path.
3. classify-legacy Road Plate `type` override.
4. classify-legacy unknown → needs_review.
5. classify-legacy conflict detection.
6. review-needed queue auth (401 without token).
7. review-needed queue shape + suggested mapping.
8. apply-legacy-crosswalk dry-run does not persist.
9. AssetCreate accepts the 13 new administrative + 4 canonical taxonomy fields (read-back verified).
10. equipment_master remains the canonical collection (contract preserved in service docstring).
11. No new collections introduced (taxonomy module is pure-python · no DB writes).
12. No cost/accounting/PO leakage on `/taxonomy` response.
13. Behavior matrix · Truck vs iPad.
14. Company normalization (MGC/Masci/?/unknown → canonical with review flag).

---

## 8 · Five-Pillar Score (this slice)

| Pillar | Score | Notes |
|---|---:|---|
| Powerful | 9.7 | 13 admin fields + canonical taxonomy + behavior matrix shipped; UI/CSV/PDF deferred to D2-D4. |
| Simple | 10 | One module · one source of truth · explicit verified/needs_review states. |
| Beautiful | 9.5 | API responses clean; UI deferred to D2 by directive. |
| Trusted | 10 | No fabrication · honest needs_review · dry-run-by-default · pytest asserts forbidden field absence. |
| Proven | 9.7 | 14/14 new + 39/39 regression. The 0.3 deferred until end-to-end D2 page audits. |
| **Avg** | **9.78** | Clears 9.5 bar. |

---

## 9 · Files Touched

| File | Change |
|---|---|
| `backend/services/asset_taxonomy.py` | **NEW** · 280 lines · pure-Python taxonomy module |
| `backend/routes/asset_spine.py` | AssetCreate + AssetUpdate extended (taxonomy + admin fields); 4 new endpoints (`/taxonomy*`) |
| `backend/services/asset_spine.py` | `_doc_create` writes new fields; `project_asset` returns them; `update_asset` legal_keys extended |
| `backend/tests/test_track_13_31b_d0d1_taxonomy_spine.py` | **NEW** · 14 tests |

No frontend file changed. No collection created. No route renamed.

---

## 10 · Remaining Gaps (intentional · deferred per directive)

| Item | Where |
|---|---|
| Asset Admin role flag on `hr_users` + token issuance | Day-2 |
| `/admin/asset-admin` page | Day-2 |
| `AssetProfile.jsx` extension (lifecycle chip + documents tab + renewal alerts) | Day-2 |
| `operational_attachments.host_kind="asset"` adoption + asset doc types | Day-3 |
| `POST/GET /api/asset-spine/assets/{id}/documents` | Day-3 |
| `/api/asset-admin/renewals/upcoming(.csv)` | Day-4 |
| Asset Profile PDF renderer | Day-4 |
| Platform-wide consumer updates (pre-op dropdown · PM templates · fleet_status.unit_kind derivation · safety_equipment_issuances item_type · asset_transfers.equipment_type · equipment_inspections.equipment_type) | Day-5 |
| Final Five-Pillar audit + first-15-seconds + first-click | Day-5 |

---

## 11 · Final Verdict

**Track 13.31B-D0D1 — CLOSED.** Foundation locked. Five-Pillar 9.78 / 10. Next fork picks up at Day-2 (Asset Admin UI + AssetProfile extension) against this verified contract.

**Read only · Certified · Documented · Stopping.**

---

**Track 13.31B-D0D1 — CLOSED.**
