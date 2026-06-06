# TRENCH SAFETY OPERATIONS SYSTEM — EXISTING SURFACE REVIEW

**Phase 1 of 11 · OMEGA DIRECTIVE: TRENCH SAFETY OPS BUILD**
**Audit date:** 2026-06-04
**Status:** SURFACE REVIEW COMPLETE — BEFORE-CODE BASELINE LOCKED
**Mode:** READ-ONLY (no code changes in this phase)

This document is the **anchor**: every later phase must preserve every surface listed here, or note the explicit migration in the relevant build doc.

---

## 1. Existing trench-box surface (THE BASELINE)

### 1.1 Frontend routes (from `/app/frontend/src/App.js`)

| Route | Component | Audience | Public? |
|---|---|---|---|
| `/trench-boxes` | `TrenchBoxes` (page) | All crews | YES (public) |
| `/safety/trench-boxes` | redirects → `/trench-boxes` | Safety | YES (public) |
| `/admin/trench-boxes` | `TrenchBoxesAdmin` | Admin | NO (admin-gated) |
| `/admin/trench-boxes/poster` | `TrenchBoxPoster` | Admin | NO |
| `/pm/trench-boxes` | `TrenchBoxesAdmin` (PM alias) | PM | NO |

### 1.2 Frontend files (existing)

| File | Lines | Role |
|---|---|---|
| `/app/frontend/src/pages/TrenchBoxes.jsx` | 47 | Public field-reference page (primer + library) |
| `/app/frontend/src/pages/TrenchBoxesAdmin.jsx` | 311 | Admin CRUD + tabulated-data file manager |
| `/app/frontend/src/pages/TrenchBoxPoster.jsx` | 65 | QR poster printout |
| `/app/frontend/src/components/TrenchBoxTabulatedLibrary.jsx` | 345 | Drag-drop PDF library (per-box folders + general) |
| `/app/frontend/src/components/TrenchBoxPosterCard.jsx` | 205 | Printable QR card per box |
| `/app/frontend/src/components/TabulatedDataPrimer.jsx` | 81 | Plain-English/Spanish primer |
| `/app/frontend/src/lib/tabulatedDataPrimer.js` | 351 | Primer content strings (English + Spanish parity) |

### 1.3 Backend (FastAPI)

All in `/app/backend/server.py` lines 2455-2712:

| Endpoint | Auth | Notes |
|---|---|---|
| `GET /api/trench-box-files?scope=trench_box` | public | grouped library listing |
| `GET /api/trench-boxes` | public | list (PDF stripped — heavy field excluded) |
| `GET /api/trench-boxes/{id}` | public | single record |
| `GET /api/trench-boxes/{id}/file` | public | stream PDF (forced `application/pdf` + `nosniff`) |
| `POST /api/trench-boxes` | `require_admin` | create |
| `PUT /api/trench-boxes/{id}` | `require_admin` | update |
| `DELETE /api/trench-boxes/{id}` | `require_admin` | delete |
| `POST /api/trench-box-files` | `require_admin` | upload file to scope |
| `DELETE /api/trench-box-files/{id}` | `require_admin` | delete file from scope |

### 1.4 Existing Mongo model — `TrenchBox`

Fields currently persisted on `db.trench_boxes`:
```
id, manufacturer, model, serial_number, box_type,
length_ft, width_min_ft, width_max_ft,
sidewall_height_ft, sidewall_thickness_in, weight_lbs,
max_depth_type_a_ft, max_depth_type_b_ft,
max_depth_type_c_60_ft, max_depth_type_c_80_ft,
spreader_count, stacking_allowed, stacking_max,
notes, tabulated_data_file (data-url, PDF magic-byte validated),
tabulated_data_filename,
created_at, updated_at
```

**Key restore set** (line 7918): `_RESTORE_SAFETY_AUX = {"equipment_units", "job_hazard_plans", "trench_boxes"}` — this collection participates in the Admin Restore flow, so **schema-breaking changes need a migration story**.

### 1.5 File storage scope

Tabulated-data PDFs are stored under file scope `"trench_box"` via the same primitives used elsewhere:
- `list_all_files_grouped(db, scope="trench_box")` → grouped listing
- `list_files_for_project(db, box_id, scope="trench_box")` → per-box list
- `upload_file_for_project(db, scope="trench_box", project_id=<box_id_or_"general">)` → upload
- `delete_file_for_project(...)` → delete

A reserved `project_id="general"` bucket exists for the **General / Educational** folder (the United Rentals primer lives here).

### 1.6 Existing content to preserve (NON-NEGOTIABLE)

- The TabulatedDataPrimer with English + Spanish parity (351-line content file).
- The "Step 1 · Upload & Manage Files" → "Step 2 · Master List" admin pattern.
- All uploaded PDFs on the live `trench_box_files` collection (do NOT migrate or re-key them).
- The Safety tile entry currently pointing to `/trench-boxes`.

---

## 2. Existing platform conventions (what we must MIMIC, not reinvent)

### 2.1 Routing / portals

App.js wraps routes in role-protectors: `AP()` for admin/pm, `RequireSafety`, `RequireShop`, `RequireHr`, `RequireFl`, `RequireDispatch`. Trench Safety must reuse these guards — no new auth surfaces.

### 2.2 Tokens (verified against `/app/memory/test_credentials.md`)

7 token families, all enforced server-side:
- `X-Admin-Token` (super-admin + admin)
- `X-Safety-Token` (Safety portal)
- `X-Shop-Token` (Shop)
- `X-Dispatch-Token` (Dispatch)
- `X-PM-Token` (Project Managers, per-PM scope)
- `X-HR-Token` (HR)
- `X-FL-Token` (Field Leadership)

`/api/operations/*` already uses `make_require_any_portal_token` for the read-side. Trench Safety read endpoints should mirror that gate.

### 2.3 Audit events

Existing pattern: `await db.audit_events.insert_one({...})` from `routes/admin_directory_k4.py`, `routes/admin_ops.py`, `routes/pm_routes.py`, `server.py`. **Do NOT create a new collection** — extend `db.audit_events` with `kind` values like `trench_asset_*`.

### 2.4 Photo storage

`/app/backend/photo_storage.py` provides S3-backed (with local fallback) primitives:
- `upload_data_url(data_url, source_id)` → ref
- `upload_photo_bytes(...)`
- `presigned_get_url(ref, ttl)` for retrieval
- `delete_photo(ref)`

Trench safety photos must use these primitives — no new uploader.

### 2.5 Asset transfers

`/app/backend/routes/asset_transfers.py` is the single SOT pattern for moving equipment:
- `db.asset_transfers` collection with status enum (Requested → In Transit → Received).
- `equipment_master.location` is mutated only on Received.
- Statuses: `Requested`, `In Transit`, `Received`, `Cancelled`.

Trench safety movement should INTEGRATE with this — not bypass it.

### 2.6 Equipment master

The single SOT for all assets is `db.equipment_master`. Trench safety assets must register here under `category="Trench Safety"` so they:
- Appear in global search.
- Appear in supervisor equipment pickers.
- Carry a unified `location` field that asset_transfers updates atomically.

### 2.7 Internationalisation

`/app/frontend/src/lib/i18n.js` (4,902 lines) is the canonical source:
- English is canonical (submitted data stored in English).
- Spanish is a fill-aid: keys in English, translations in `es`.
- `useT()` hook gives `{t, lang, setLang}`.
- `<html lang>` is auto-synced for native spell-check.
- Existing `LangToggle` component is the UI control.

**Every new Trench Safety string must have an entry in i18n.js with Spanish parity.**

### 2.8 Coaching / guidance

Pattern lives in `/app/backend/guidance/` (`content.py`, `tips.py`) and frontend coaching components. Coaching is collapsible, contextual, and bilingual. Do NOT replicate the SHA training pattern — use the existing collapsed-coaching card.

### 2.9 Vocabulary (verified)

The platform standard status vocabulary:
- **Needs Review, Action Required, Pending Verification, Inspection Hold, Repair, Available, Assigned, Returned, Retired, Closed**

Failed-inspection language uses **Inspection Hold** (no "Failed" badge on the asset itself).

### 2.10 Test-ID discipline

Existing pattern: `data-testid="kebab-case-functional-name"` on every interactive element. Examples: `safety-tile-tasks`, `new-trench-btn`, `delete-trench-${id}`, `save-trench-btn`.

### 2.11 Restore / backups

`/app/backend/backup_verification.py` + admin restore flow restores `trench_boxes` as part of `_RESTORE_SAFETY_AUX`. **Any new collection we introduce must be added to the restore set** or it will be lost on restore.

---

## 3. Existing safety-tile / safety-portal surface

Reviewed `/app/frontend/src/pages/SafetyHub.jsx` and the sidebar component — current Safety hub already exposes ~15 tiles (tasks, CA, incidents, audits, expirations, training, employees, fire extinguishers, forms records, docs, digest, reports, topic library, fleet, training-center).

`SafetyHub.jsx` does NOT currently expose a "Trench Safety" tile — the only entry today is via the public `/trench-boxes` URL. The Safety sidebar (`SafetySideNavV2.jsx`) likewise has no trench reference.

**Implication:** Adding the "Trench Safety" tile is a true new surface, not a re-skin.

---

## 4. Equipment / dispatch / search wiring

### 4.1 Equipment routes inventoried

Found in `/app/backend/routes/`:
- `equipment.py` — equipment-master CRUD
- `asset_transfers.py` — movement state machine
- `fleet_ops.py` — fleet-level operations
- `dispatch_*` — 8 dispatch-side routes
- `global_search.py` — global search endpoint
- `master_lookup.py`, `master_where_used.py`, `master_history.py` — cross-collection lookup helpers

### 4.2 Global search

`/app/backend/routes/global_search.py` is the single SOT for cross-collection search. Trench-safety assets are NOT in it today. **Phase 9 must register the trench-safety collection here.**

### 4.3 Dispatch movement

Dispatch movement updates `db.equipment_master.location` via `asset_transfers`. The Trench Safety asset, once registered in `equipment_master`, will automatically participate in dispatch movement — **no new dispatch code is required for movement**, only for the trench-safety-specific UI surfaces.

---

## 5. What survives unchanged

Per the directive ("Existing Trench Box Tabulated Data page must be preserved and moved into Safety → Trench Safety → Tabulated Data"):

| Item | Plan |
|---|---|
| `TrenchBoxes.jsx` (public field-reference page) | Re-mount under `/safety/trench-safety/tabulated-data`. Original `/trench-boxes` URL becomes a redirect (NOT removed). |
| `TabulatedDataPrimer.jsx` + `tabulatedDataPrimer.js` (Spanish parity) | UNTOUCHED — re-rendered inside new tabulated-data page. |
| `TrenchBoxTabulatedLibrary.jsx` (PDF library) | UNTOUCHED — re-rendered. Continues to use `scope="trench_box"`. |
| `db.trench_boxes` model (CRUD) | UNTOUCHED for now. Replaced/superseded by `db.trench_safety_assets` over time but coexists during transition. |
| `/api/trench-boxes` endpoints | UNTOUCHED. New endpoints live at `/api/trench-safety/*`. |
| Admin Restore aux set | UNTOUCHED. Will ADD new collections to the set. |
| `i18n.js` Spanish strings for primer/library | UNTOUCHED — extended for the new vocabulary only. |

---

## 6. What this means for the build (constraints feeding into Phase 2)

1. **Coexistence over migration.** `db.trench_boxes` (the manufacturer master) is a DIFFERENT thing from `db.trench_safety_assets` (the per-physical-unit MASCI asset roster). They will coexist. TB-01 through TB-07 are PHYSICAL UNITS in the new system; the existing `trench_boxes` rows are MANUFACTURER REFERENCE DATA.
2. **Equipment Master as SOT.** Each new trench-safety asset must mirror into `db.equipment_master` with `category="Trench Safety"` so it inherits global search, location, and dispatch participation for free.
3. **No new auth.** Reuse the 7 existing token families and the `require_*` dependencies.
4. **No new audit collection.** Extend `db.audit_events` with new `kind=trench_asset_*` values.
5. **Photos via `photo_storage.py`.** No new uploader.
6. **i18n is mandatory on every string.** Adding to the 4902-line `i18n.js` is part of the work, not optional.
7. **Backups must extend `_RESTORE_SAFETY_AUX`** to add `trench_safety_assets`, `trench_safety_inspections`, etc.

---

## 7. Risks identified pre-code

| Risk | Severity | Mitigation |
|---|---|---|
| `db.trench_boxes` vs `db.trench_safety_assets` naming confusion | MED | Hard-rule: `trench_boxes` = manufacturer reference; `trench_safety_assets` = MASCI physical units. Documented in this file. |
| Asset duplication between `equipment_master` and `trench_safety_assets` | MED | Use `equipment_master.id` as the canonical asset_id. `trench_safety_assets` holds trench-specific extension fields only; joins by id. |
| Live URL `/trench-boxes` users break after relocation | LOW | Keep `/trench-boxes` working as a redirect to the new path. Existing QR labels in the field continue to resolve. |
| Spanish parity slipping | MED | Add a one-script CI check that fails the build if any new key in a TrenchSafety component lacks a Spanish entry. |
| Restore-set forget | HIGH | Add new collections to `_RESTORE_SAFETY_AUX` as part of Phase 2 commit — checked off in Phase 2 deliverable. |
| OCR vendor lock | MED | Use the project's existing emergent integration playbook in Phase 10; do not hard-code Tesseract. |

---

## 8. Phase-1 verdict

✅ **SURFACE REVIEW COMPLETE.**

Baseline locked, conventions extracted, integration points identified, risks logged. Ready to advance to **Phase 2 — Data Model + API + Seed** pending operator scope confirmation (see follow-up plan in chat).

