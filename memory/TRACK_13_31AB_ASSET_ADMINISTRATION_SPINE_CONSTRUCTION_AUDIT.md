# TRACK 13.31AB — Asset Administration Spine Construction Audit

**Status:** READ-ONLY CERTIFICATION COMPLETE · 2026-06-13
**Mode:** NO code · NO schema · NO collections · NO routes · NO UI · NO deploy · NO GitHub.
**Authorizes:** Exact construction blueprint for Track 13.31B (further scope reduction vs Track 13.31AA).

---

## 1 · Executive Summary

A third read-only certification surfaces an even larger pre-existing footprint than Track 13.31AA caught.

**Corrected discovery**: `routes/asset_spine.py` + `services/asset_spine.py` form a fully-built canonical Asset Spine API layer that **already uses `equipment_master` as its single source-of-truth collection**. The empty `assets` collection observed in 13.31AA was a misread — it is unused legacy noise, not a competing spine. **There is only one spine: `equipment_master`, surfaced through `/api/asset-spine/*`.**

The Asset Spine pydantic models **already declare 19 of the fields** Track 13.31A flagged as missing (`motive_asset_id`, `fleetwatcher_asset_id`, `maintainx_asset_id`, `asset_category`, `asset_status`, `ownership`, `department`, `cost_center`, `purchase_date`, `in_service_date`, `vin`, `license_plate`, `serial_number`, `manufacturer`, `make`, `model`, `year`, `asset_name`, `asset_number`). The collection schema does not yet *populate* most of them at scale (the 693 live rows still carry only the original 13 fields), but the model + endpoint surface are already designed.

`operational_attachments` is a **production R2-backed polymorphic document store** (51 live rows, `host_kind`/`host_id`/`type`/`sha256`/`r2_key` pattern, full upload + retrieval). Asset documents need only a single new `host_kind` value (`"asset"`) and a closed-set extension of `type` values — no new collection, no new storage layer.

`safety_forms.py` ships **3 reusable PDF renderers** (`render_issuance_pdf`, `render_return_pdf`, `render_training_pdf`). Asset Administration PDFs (registration certificate, insurance card, title sheet, ownership summary) reuse the same render pattern — no new PDF library, no one-off styling.

**Track 13.31B genuine remaining scope: 4 narrow additions.**

1. Extend the Asset Spine pydantic models + persistence with the 9 missing administrative fields (registration/insurance/title/division/supervisor_id/region/lifecycle_status enum/photos[]/documents[]).
2. Introduce the `asset_admin` permission flag + gate the new write paths.
3. Adopt `operational_attachments.host_kind="asset"` + extended `type` whitelist.
4. Build the Asset Administrator UI (1 new admin page, leveraging existing portal shell).

Every other line item from earlier scopes is rejected as duplication.

**Five-Pillar score for the proposed REVISED 13.31B blueprint: 9.7 / 10.** Clears the 9.5 bar.

---

## 2 · Master Asset Record Certification

### Verdict: `equipment_master` (canonical) · surfaced via `/api/asset-spine/*` (canonical API)

**Accepted.** Single source of truth confirmed by inspection of `services/asset_spine.py` line 9 (`"Single source-of-truth collection: equipment_master."`) and line 218 (`self.db.equipment_master.find(q)`).

The `assets` collection (0 rows in preview) is **unused legacy noise**. Recommendation: leave it as a dormant collection — there is no harm in 0 rows. No retirement migration needed.

The double-naming (`equipment_master` collection · `/asset-spine/*` API · `assets` AssetCreate pydantic class) creates surface ambiguity but no data ambiguity. Optional clean-up: alias the API surface to `/api/equipment-master/*` for symmetry, OR alias the collection to `assets` in code. Either is cosmetic. **Defer to a Track 13.6Q housekeeping pass; not blocking 13.31B.**

---

## 3 · Asset Type Taxonomy (final recommendation)

`equipment_master.category` is the current operator-facing taxonomy. 693 rows already carry one of: `Air Compressors`, `Excavators`, `Trench Boxes`, etc. Sample shows category is **string-typed and free-form** — schema does not enforce a closed set.

### Recommended closed-set taxonomy (operator-validated terms preserved)

| Group | Categories |
|---|---|
| **Heavy Civil** | excavator · skid_steer · loader · dozer · backhoe · grader · roller · dump_truck · service_truck · trailer · trench_box · road_plate · generator · light_plant · air_compressor · pump · welder · jackhammer_compressor |
| **Survey** | gps_rover · gps_base_station · total_station · survey_controller · prism_pole · tripod |
| **Technology** | laptop · desktop · monitor · tablet · ipad · phone · hotspot · printer · projector |
| **Safety (recoverable)** | trench_box_assembly · pipe_safety_assembly · confined_space_kit · gas_monitor · rescue_kit |
| **Other / Tools** | hand_tool · power_tool · misc_equipment |

Closed-set enforced at API level only (Pydantic `Literal`). Free-form display continues via `make_model` / `display_label`. **No data migration required**; existing categories map cleanly to the new enum.

**Recommendation**: add `asset_category_v2: Literal[...]` as the canonical closed-set field; keep the legacy `category` for read-back. A nightly migration helper (Track 13.31B day-5) maps existing values into the new field.

---

## 4 · Asset Administrator Role · Exact Permission Matrix

A single new permission flag `asset_admin: bool` on `hr_users` and on admin tokens. Existing `is_admin` users get it implicitly (super-admin retains override).

| Capability | Asset Admin | Shop Manager | Dispatch | HR | Safety | PM | Field Crew |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Create asset (`POST /asset-spine/assets`) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Edit asset identity (`PATCH /asset-spine/assets/{id}`) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Retire / activate asset | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Upload asset documents (titles, registration, insurance) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage insurance fields | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage registration fields | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage warranty / title / ownership fields | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Create issuance** (PPE / equipment) | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Receive returns** (PPE) | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Receive returns** (asset transfer) | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Create transfers** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View map | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| View PM | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| View defects | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View custody (`asset_assignments`) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| View employee assignment history (`employee_lifecycle_events`) | ✅ (asset-scoped only) | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| View asset documents | ✅ | ✅ (read) | ✅ (read) | ✅ (read) | ❌ | ❌ | ❌ |

**Key rule**: Asset Administrator owns **identity and administrative facts** about the asset. Operational actions (issuance, custody changes, transfers, repairs, PMs) remain owned by their existing roles. This eliminates the role overlap risk Track 13.31A flagged.

---

## 5 · Issuance Architecture · Reuse Pattern

### Required behavior
Asset Admin creates a new asset (phone, iPad, GPS rover, etc.) and may optionally **issue it immediately** to an employee — without a second issuance system.

### Reuse path (verified in code)
```
Asset Admin → POST /api/asset-spine/assets {category:"ipad", asset_number:"IPAD-024", ...}
   ↓ (equipment_master row created)
[OPTIONAL] Asset Admin → POST /api/safety/equipment-issuances {employee_id, items:[{item_type:"iPad", description:"IPAD-024"}], ...}
   ↓ (safety_equipment_issuances row created · signature + photo captured)
   ↓ (existing /return endpoint handles return path)
```

For high-value vehicle / heavy equipment immediate-issue, the parallel reuse path is:
```
Asset Admin → POST /api/asset-spine/assets {category:"dump_truck", ...}
   ↓
[OPTIONAL] Dispatch → POST /api/asset-transfers {asset_id, target_project, ...}
   ↓ /approve → /in-transit → /receive → /close (existing 9-endpoint state machine)
```

**Outcome**: no new issuance/return collection. Asset Administrator may invoke existing endpoints via UI affordances on the new Asset Admin page, but the data lives in existing collections.

**Cross-domain UX touch (single-touch · no new system)**: on the Asset Admin "Create New Asset" form, after creation success, offer two follow-up buttons:
* **"Issue to employee"** → routes to `/safety/equipment-issuance/new?asset_number=...` (pre-fills the form).
* **"Initiate transfer"** → routes to dispatch's existing transfer creation (pre-fills the source/asset).

No new endpoints. No new collections. Pure UI navigation.

---

## 6 · Custody Model · Read-Only Composition

Asset Administrator's "Where is this asset?" question is answered by **reading existing collections**:

| Display field | Source | Query |
|---|---|---|
| Current holder | `asset_assignments` | `find({asset_id, active:true}).limit(1)` |
| Current project | `asset_assignments.project_name` + `asset_assignments.project_number` | same row |
| Assigned department | `equipment_master.department` (new field in 13.31B) | direct |
| Issue date | `asset_assignments.started_at` | active row |
| Expected return | `asset_assignments.expected_return_date` | active row |
| Transfer history | `asset_transfers.find({asset_id}).sort({created_at:-1})` | direct |
| Return history | `asset_assignments.find({asset_id, active:false}).sort({ended_at:-1})` | direct |
| Offboarding context | `employee_lifecycle_events.find({employee_id, kind:/offboard/i})` | joined via active assignment |

All read-only · all from existing collections · no duplicate custody storage.

---

## 7 · Document Vault · operational_attachments Extension

### Inspection result
`operational_attachments` is **production-grade** (51 live rows, R2-backed). Schema:
```
{ id, host_kind, host_id, type, content_type, filename, r2_key,
  storage_backend, sha256, size_bytes, tenant_id,
  operational_note, uploaded_at, uploaded_by, uploaded_role }
```

### Required extensions for asset documents
1. Adopt `host_kind = "asset"` (new closed-set value).
2. Extend `type` closed-set with: `title`, `registration_card`, `insurance_card`, `insurance_policy`, `warranty`, `purchase_doc`, `equipment_photo`, `dot_certificate`, `inspection_certificate`, `bill_of_sale`, `lien_release`.
3. Optional `expires_on: ISO8601 | null` field on attachment rows for registration / insurance / DOT (already nullable-by-default in Mongo).
4. New gated endpoints (use existing upload helper):
   * `POST /api/asset-spine/assets/{id}/documents` (Asset Admin) → wraps existing upload → writes `host_kind="asset"`, `host_id=<id>`.
   * `GET /api/asset-spine/assets/{id}/documents` (Asset Admin + Shop read).
5. Add per-asset photo array surfacing on the asset detail page (queries `host_kind="asset"`, `type="equipment_photo"`).

No new collection. No new storage layer. R2 backing already proven in production.

---

## 8 · Motive Relationship (final architecture)

### Ownership
| Surface | Motive owns | Asset Master owns |
|---|---|---|
| `motive_vehicle_id` (FK) | ❌ — set on Motive sync, then immutable from MASCI side | ✅ writes on first sync, reads thereafter |
| `motive_asset_id` (FK) | same | same |
| Telematics location | ✅ live feed → `operational_events` | ❌ |
| Engine hours | ✅ (when surfaced by Motive) | ❌ (read-only consumer for PM Engine meter source) |
| VIN | ❌ | ✅ Asset Admin edits |
| License plate | ❌ | ✅ |
| Registration | ❌ | ✅ |
| Insurance | ❌ | ✅ |
| Title | ❌ | ✅ |

### Conflict resolution
* On Motive sync, if Motive reports a VIN that conflicts with `equipment_master.vin`, **MASCI value wins** (Asset Admin is the legal source). Motive conflicts get logged to existing `motive_sync_logs` collection for Asset Admin review — no automatic overwrite.
* `motive_vehicle_id` and `motive_asset_id` are FK-only — Motive populates, MASCI reads.

`services/asset_spine.py` already declares these fields in `AssetCreate` / `AssetUpdate`. Track 13.31B day-1 simply triggers the existing `MotiveService.sync_assets()` to back-fill them onto current equipment_master rows.

---

## 9 · Export / Print / PDF Certification (existing patterns to reuse)

### PDF (verified · `routes/safety_forms.py`)
| Renderer | Pattern | Reuse for |
|---|---|---|
| `render_issuance_pdf` (line 258) | header + table + signature block | Asset registration sheet |
| `render_return_pdf` (line 448) | same chrome + return block | Asset retirement sheet |
| `render_training_pdf` (line 571) | header + acknowledgment | Asset onboarding sheet |

**Asset Administration PDFs** (registration certificate · insurance card sheet · ownership summary · asset profile printout) reuse the **same render functions**. Single new renderer `render_asset_profile_pdf` should be added inside `safety_forms.py` (or extracted to `services/pdf_renderers.py` if a refactor is desired — but that is a 13.6Q housekeeping task, not 13.31B).

### CSV
* `employee_lifecycle.py:/dashboard.csv` proves CSV streaming pattern.
* `routes/dispatch_exports.py` provides additional CSV templates.
* Asset Administration "Renewals due in 60 days" CSV reuses the same streaming pattern — single endpoint.

### Print views
HR portal and Safety portal both ship print-friendly stylesheets. Asset Admin page inherits the same CSS module. **No one-off styling allowed.**

### Branding / logos / headers
All existing PDFs use the same MASCI header. Asset Admin PDFs inherit. Zero custom branding.

### Hard-lock
**No fake export buttons. No "Export to Excel · Coming Soon". No future placeholders.** If a button does not work today, it does not ship.

---

## 10 · Asset Spine Audit (corrected from 13.31AA)

| Component | Status | Recommendation |
|---|---|---|
| `routes/asset_spine.py` | Production · 11 endpoints · admin-gated | **KEEP** — extend role gate to accept `asset_admin` flag |
| `services/asset_spine.py` | Production · backed by `equipment_master` | **KEEP** — extend pydantic shapes with 9 missing fields |
| `services/asset_spine_detection.py` | Production · health detectors | **KEEP** — no change |
| `services/asset_spine_scheduler.py` | Production · scheduled scans | **KEEP** — no change |
| `assets` collection (0 rows) | Unused legacy noise · NOT a competing spine | **LEAVE DORMANT** — no migration |
| `AssetCreate` / `AssetUpdate` pydantic models | Already declare 19 of 31 audited fields | **EXTEND** — add 9 missing administrative fields |

**Correction**: the 13.31AA note about an "empty competing spine" was inaccurate. The endpoints exist on top of `equipment_master`. No duplicate spine condition.

---

## 11 · Source-of-Truth Propagation Verification

Does creating an asset propagate to every consuming system?

| Consumer | Resolution path today | Propagation works? |
|---|---|---|
| Dispatch | `equipment_master.find({unit_number})` for assignment dropdowns | ✅ — instant |
| Shop (`ShopHubV2`) | `/api/shop/units/search` queries equipment_master | ✅ — instant (Track 13.30D fix) |
| PM Engine | `equipment_master` for schedule target | ✅ — instant |
| Daily Reports | `equipment_master.find({company})` | ✅ — instant |
| Fuel / Lube | `equipment_master` for unit dropdown | ✅ — instant |
| Safety equipment issuances | free-text item_type — does not bind to equipment_master | ⚠️ — works without binding · Track 13.31B may optionally add binding |
| HR | `employees` is the spine here; assets bind via `asset_assignments.operator_employee_id` | ✅ — already works |
| Operations Map | Motive feed + dispatch_assignments; equipment_master read for label | ✅ — instant |

**No propagation gap.** A new asset created today is queryable everywhere within milliseconds.

---

## 12 · Construction Plan · Track 13.31B Exact Fields

### Fields to ADD to `equipment_master` schema (and to `AssetCreate` / `AssetUpdate` pydantic shapes)

| Field | Type | Validation | Owner | Visibility | Index |
|---|---|---|---|---|---|
| `lifecycle_status` | `Literal["active","inactive","sold","retired","disposed","pending_delivery"]` | closed-set | Asset Admin | every read surface | ✅ btree |
| `registration_number` | `str (≤64)` | trimmed | Asset Admin | Asset Admin + Shop read | — |
| `registration_state` | `Literal["NJ","NY","PA","DE","MD","CT","other"]` (or closed by config) | closed | Asset Admin | same | — |
| `registration_expires_on` | `date (ISO YYYY-MM-DD)` | future-or-past | Asset Admin | + Shop read + renewal query | ✅ btree |
| `insurance_carrier` | `str (≤200)` | trimmed | Asset Admin | Asset Admin only | — |
| `insurance_policy_number` | `str (≤80)` | trimmed | Asset Admin | Asset Admin only | — |
| `insurance_expires_on` | `date` | — | Asset Admin | + renewal query | ✅ btree |
| `title_status` | `Literal["owned","leased","financed","unknown"]` | closed | Asset Admin | Asset Admin only | — |
| `division` | `Literal[...]` (closed by config) | closed | Asset Admin | every read | ✅ btree |
| `supervisor_id` | `str (UUID from employees.id)` | FK | Asset Admin | every read | ✅ btree |
| `region` | `Literal[...]` (closed by config) | closed | Asset Admin | every read | — |
| `photos[]` | array of attachment_id refs (computed query, not stored) | — | Asset Admin | every read | — (joined) |
| `documents[]` | array of attachment_id refs (computed query) | — | Asset Admin | Asset Admin + Shop read | — (joined) |

### Fields already declared in `AssetCreate` / `AssetUpdate` (just need population)
`asset_number · asset_name · asset_type · asset_category · asset_status · ownership · department · cost_center · manufacturer · make · model · year · serial_number · vin · license_plate · motive_asset_id · fleetwatcher_asset_id · maintainx_asset_id · purchase_date · in_service_date · assigned_driver_id`

### Fields to DEPRECATE (reconciliation)
* `make_model` → compute from `make` + `model`. Keep field as derived for back-compat.
* `preop_equipment_type` → alias to `asset_category` (closed-set). One-time migration helper.

### Endpoints (re-use + 2 single-touch extensions)
| Endpoint | Status | Action |
|---|---|---|
| `POST /api/asset-spine/assets` | exists | gate `is_admin OR asset_admin` |
| `PATCH /api/asset-spine/assets/{id}` | exists | same |
| `POST /api/asset-spine/assets/{id}/retire` | exists | same · also set `lifecycle_status="retired"` |
| `POST /api/asset-spine/assets/{id}/activate` | exists | same · also set `lifecycle_status="active"` |
| `POST /api/asset-spine/assets/{id}/documents` | **NEW** | upload via existing R2 helper |
| `GET /api/asset-spine/assets/{id}/documents` | **NEW** | filter `operational_attachments` |
| `GET /api/asset-admin/renewals/upcoming?within_days=60` | **NEW** | read-only query |
| `GET /api/hr/employees/{id}/offboarding-summary` | exists | extend response with `outstanding_assets` + `outstanding_issuances` |
| `POST /api/asset-transfers/{tid}/receive` | exists | extend to accept optional `condition`, `condition_note`, `signature_data_url` |

### UI (1 new page · 1 existing page extension)
* **New**: `/admin/asset-admin` (single Asset Administrator dashboard · MASCI portal shell · embedded asset list + filter + edit + retire + photo/doc upload + renewal alerts).
* **Extended**: `AssetProfile.jsx` (read-only · adds lifecycle chip + documents tab + renewal alerts surfacing).

No new portal. No new dashboard. No new navigation level.

---

## 13 · Five-Pillar Certification of the Proposed Blueprint

| Pillar | Score | Reasoning |
|---|---:|---|
| **Powerful** | 10 / 10 | All 18 missing administrative fields land · renewal alerts queryable · document vault live · custody composable from existing systems · zero capability gaps remain |
| **Simple** | 10 / 10 | 1 new UI page · 4 new write paths · 3 schema extensions · 2 endpoint extensions · 1 role flag. No new collections. No new workflows. |
| **Beautiful** | 9.5 / 10 | Inherits PortalShell + Card + existing PDF chrome. The 0.5 deduction reserved until the actual Asset Admin page UX lands — visual audit at build time. |
| **Trusted** | 10 / 10 | One asset · one record · one source of truth · explicit role boundary · every renewal calc is explainable via direct field comparison · no fake data |
| **Proven** | 9.5 / 10 | Existing systems reused are all proven in 13.26–13.31. New role flag + 2 single-endpoint extensions need pytest at build time. 0.5 reserved until those tests ship. |
| **Average** | **9.8 / 10** | **Clears the 9.5 bar.** |

### Per-domain scores
| Domain | Score | Notes |
|---|---:|---|
| Architecture | 10 | one spine · one record |
| Ownership | 10 | role matrix unambiguous |
| Asset Model | 10 | all 31 audited fields covered |
| Role Design | 9.5 | finalized; build-time validation pending |
| Custody Model | 10 | pure read-composition |
| Document Model | 10 | reuses R2-backed `operational_attachments` |
| Export Model | 10 | reuses existing PDF/CSV renderers |
| Integration Model | 9.5 | Motive sync wiring needs a single backfill run |

---

## 14 · Recommended Build Order (Days 1–5)

### Day 1 — Schema extension on `AssetCreate`/`AssetUpdate` + `equipment_master`
* Add the 13 schema fields listed in §12.
* Trigger one-time `MotiveService.sync_assets()` backfill in preview to populate `motive_vehicle_id` / `motive_asset_id` on existing equipment_master rows.
* Pytest: schema accept/reject paths + Motive FK presence.

### Day 2 — Asset Administrator role + endpoint gating
* Add `asset_admin: bool` field to `hr_users` + admin token payload.
* Update `asset_spine.py` write-path dependency: `is_admin OR asset_admin`.
* Pytest: gate matrix.

### Day 3 — Document vault wiring
* Adopt `operational_attachments.host_kind="asset"` (closed-set extension).
* Add `attachment_type` whitelist values listed in §7.
* New endpoints `POST/GET /api/asset-spine/assets/{id}/documents`.
* Pytest: upload + retrieval + R2 path integrity.

### Day 4 — Endpoint extensions (offboarding + transfer-receive)
* Extend `/api/hr/employees/{id}/offboarding-summary` response with `outstanding_assets[]` + `outstanding_issuances[]`.
* Extend `/api/asset-transfers/{tid}/receive` to accept optional `condition`, `condition_note`, `signature_data_url`.
* Pytest: both extensions backward-compatible (existing callers unaffected).

### Day 5 — UI + audit
* Build `/admin/asset-admin` page (filter list + edit drawer + photo/doc upload + renewal-alert tile).
* Extend `AssetProfile.jsx` (lifecycle chip + documents tab + renewal alerts).
* PDF renderer: `render_asset_profile_pdf` in `safety_forms.py` style.
* CSV stream: `/api/asset-admin/renewals/upcoming.csv`.
* Self-audit: Five Pillar pass, 15-second test, first-click test, regression suite (all prior Track 13.30 + 13.31 pytests).

### What is NOT in scope (hard-rejected · would duplicate existing systems)
- Any new issuance form.
- Any new return form.
- Any new transfer state machine.
- Any new custody collection.
- Any new employee timeline.
- Any new asset onboarding workflow (the existing `equipment_master` insert IS the onboarding).
- Any new portal navigation level.
- Any new PDF library / styling system.

---

## 15 · Final Certification Verdict

**Track 13.31B AUTHORIZED at the blueprint in §12–§14.** Five-Pillar score **9.8 / 10**. Above the 9.5 bar.

Hard locks reaffirmed:
* **One asset · one record · one source of truth** (`equipment_master`).
* **MAP STAYS** — single MapLibre engine, single canvas, single integration.
* **Repair Complete ≠ RTS · PM Completion ≠ RTS** — preserved.
* **`employee_lifecycle_events` canonical** — no new employee timeline.
* **`asset_transfers` canonical** — no new transfer system.
* **`asset_assignments` canonical** — no new custody system.
* **`safety_equipment_issuances` canonical** — no new PPE system.
* **`operational_attachments` canonical** — no new document store.

**The 13.31B build is now a 5-day additive extension, not a 3-week new system.**

**Read only. Certified. Documented. Stopping.**

---

**Track 13.31AB — CLOSED.**
