# Trench Safety — Surface Ownership Audit
**Date:** 2026-02-07
**Mode:** Read-only audit. No code changes made.
**Scope:** Every trench-safety function across Public · Safety Portal · Admin Console · Shop Portal.

---

## 1. Surfaces in the codebase today

| Surface | Routes | Auth gate |
|---|---|---|
| **Public Safety Tile** | `/trench-safety`, `/trench-safety/tabulated-data`, `/trench-safety/references`, `/trench-safety/report`, `/trench-safety/assets/:id`, legacy `/trench-boxes` | None |
| **Safety Portal (gated)** | `/safety/trench-safety`, `/safety/trench-safety/assets`, `/safety/trench-safety/assets/:id`, `/safety/trench-safety/tabulated-data` | `require_safety_or_admin` |
| **Admin Console** | `/admin/trench-boxes`, `/admin/trench-boxes/poster`, alias `/pm/trench-boxes` | `require_admin` (AP wrapper) |
| **Shop Portal** | `/shop/trench-safety-repairs` | `require_shop_or_admin` |

Backend endpoints live under `backend/routes/trench_safety/` and `backend/server.py` (legacy `/trench-boxes`).

---

## 2. Feature × Surface Matrix

Legend: ✅ correct · 🔴 DRIFT · ⚠️ FRONTEND GAP (backend OK, no Safety Portal UI) · ⏳ Future / planned later phase

### 2.1 PUBLIC SAFETY TILE (must own)

| Feature | Required Surface | Current Location | Status |
|---|---|---|---|
| QR Scan landing | Public | `/trench-safety/assets/:id` | ✅ |
| Asset Lookup | Public | `/trench-safety` dashboard + PublicAssetLookup | ✅ |
| Asset Status display | Public | QR landing status pill | ✅ |
| Serial Number display | Public | QR landing hero block + details row | ✅ |
| Asset Location display | Public | QR landing Current Use card | ✅ |
| Tabulated Data access | Public | `/trench-safety/tabulated-data` | ✅ |
| Safety References | Public | `/trench-safety/references` | ✅ |
| OSHA References | Public | inside `/trench-safety/references` cards | ✅ |
| Stop-Work Guidance | Public | references page + dashboard banner | ✅ |
| Damage Reporting | Public | `/trench-safety/report` + QR modal | ✅ |
| Unsafe Condition Reporting | Public | report form `kind=Unsafe Condition` | ✅ |
| Missing Pin Reporting | Public | report form `kind=Missing Pins` | ✅ |
| Missing Label Reporting | Public | report form `kind=Missing Labels` | ✅ |
| Field-Safe Photos display | Public | Backend `GET /trench-safety/public/assets/{id}/photos` exists. Public UI consumption pending Phase 7 frontend. | ⏳ |
| Bilingual (EN/ES) | Public | LangToggle on every public page | ✅ |

### 2.2 PUBLIC SAFETY TILE (must NOT own — leak check)

| Feature | Leaked into Public? |
|---|---|
| Asset Creation | No |
| Asset Editing | No |
| Inspection Management | No |
| Hold Management | No |
| Certification Management | No |
| Repair Management | No |
| QR Management | No (PNG endpoint gated `safety_or_admin`) |
| Photo Administration | No |
| OCR Administration | No (not yet built) |
| System Configuration | No |

✅ Public surface is clean — no admin functions leak.

### 2.3 SAFETY PORTAL (must own)

| Feature | Backend | Frontend Surface | Status |
|---|---|---|---|
| **ASSETS** | | | |
| Create Asset | `POST /trench-safety/assets` (safety_or_admin) | **None on Safety Portal** | ⚠️ FE GAP |
| Edit Asset | `PUT /trench-safety/assets/{id}` (safety_or_admin) | **None — Asset Detail is read-only per Phase 3 comment** | ⚠️ FE GAP |
| Asset Details | `GET /trench-safety/assets/{id}` | `/safety/trench-safety/assets/:id` | ✅ |
| Asset Status change | `POST /trench-safety/assets/{id}/status` | **None — only Assign/Return dialogs exist** | ⚠️ FE GAP |
| Asset Audit History | `GET /trench-safety/assets/{id}/audit` | **Not rendered on detail page** | ⚠️ FE GAP |
| **TABULATED DATA** | | | |
| Upload PDF | `POST /api/trench-boxes` (admin) | `/admin/trench-boxes` (Admin Console) | 🔴 DRIFT-1 |
| Replace PDF | `PUT /api/trench-boxes/{id}` (admin) | `/admin/trench-boxes` (Admin Console) | 🔴 DRIFT-1 |
| Link PDF to asset | (manual via library) | `/admin/trench-boxes` (Admin Console) | 🔴 DRIFT-1 |
| Manage library | `DELETE /api/trench-boxes/{id}` (admin) | `/admin/trench-boxes` (Admin Console) | 🔴 DRIFT-1 |
| View library (read-only) | `GET /api/trench-boxes` (public) | `/safety/trench-safety/tabulated-data` | ✅ |
| Verify Matching Assets | Not implemented | Not implemented | ⏳ |
| **INSPECTIONS** | | | |
| Create Inspection | `POST /trench-safety/assets/{id}/inspections` (safety_or_admin) | **None** | ⚠️ FE GAP |
| Inspection History | `GET /trench-safety/assets/{id}/inspections` | **None on detail page** | ⚠️ FE GAP |
| Pass / Fail | included in create payload | **None** | ⚠️ FE GAP |
| Severity Assignment | included in create payload | **None** | ⚠️ FE GAP |
| **HOLDS** | | | |
| Open Safety Hold | `POST /trench-safety/assets/{id}/holds` (safety_or_admin) | **None** | ⚠️ FE GAP |
| Open Inspection Hold | same | **None** | ⚠️ FE GAP |
| Certification Hold (auto) | engine in `_helpers.recompute_certification_hold` | engine ✅ · status visible on Hub | ✅ engine, ⚠️ no manual UI |
| Open Maintenance Hold | same | **None** | ⚠️ FE GAP |
| Release / Clear hold | `POST /…/holds/{id}/clear` (safety_or_admin) | **None** | ⚠️ FE GAP |
| **CERTIFICATIONS** | | | |
| Upload Certification | `POST /trench-safety/assets/{id}/certifications` (safety_or_admin) | **None** | ⚠️ FE GAP |
| Expiration Tracking | Hub alerts row + auto-expire sweep | Hub shows "Cert Due/Missing" count only | ⚠️ Partial |
| Certification Status | `certification_status_for()` helper | Not on detail page | ⚠️ FE GAP |
| Revoke / Patch | `PATCH /…` + `POST /…/revoke` (safety_or_admin) | **None** | ⚠️ FE GAP |
| **REPAIRS** | | | |
| Review Repair Queue | `GET /trench-safety/shop/repairs` (shop_or_admin) | **Only at `/shop/trench-safety-repairs`** | 🔴 DRIFT-3 |
| Safety Verification | `POST /…/repairs/{id}/verify` (safety_or_admin) | **None on Safety Portal** | ⚠️ FE GAP |
| Release Logic (re-inspection) | engine ✅ | **None on Safety Portal** | ⚠️ FE GAP |
| **QR MANAGEMENT** | | | |
| Generate QR PNG | `GET /…/qr-label.png` (safety_or_admin) | Phase 7 FE pending | ⏳ |
| Reprint QR | Audit endpoint exists | Phase 7 FE pending | ⏳ |
| Download QR | Same | Phase 7 FE pending | ⏳ |
| **PHOTO MANAGEMENT** | | | |
| Upload Photos | `POST /…/photos` **(shop_or_admin)** | Phase 7 FE pending | 🔴 DRIFT-2 (auth gate) |
| Internal vs Field-safe visibility | Backend supports `visibility` field | Phase 7 FE pending | ⏳ |
| Asset Photo Library | `GET /…/photos` (any_portal) | Phase 7 FE pending | ⏳ |
| Delete Photo | `DELETE /trench-safety/photos/{id}` (safety_or_admin) | Phase 7 FE pending | ⏳ |
| **REPORT REVIEW** | | | |
| Review Field Reports | Public POSTs create `Open` repair rows | **Only visible in Shop queue** | 🔴 DRIFT-3 |
| Resolve Reports | Same repair lifecycle | Shop only | 🔴 DRIFT-3 |
| Assign Follow-Up | Implicit via repair updates | **None** | ⚠️ FE GAP |
| **AUDIT** | | | |
| Asset Timeline | `audit_events` keyed by `asset_id` | **Not rendered** | ⚠️ FE GAP |
| Inspection Timeline | same source | **Not rendered** | ⚠️ FE GAP |
| Hold Timeline | `trench_safety_holds` + audit | **Not rendered** | ⚠️ FE GAP |
| Cert Timeline | `trench_safety_certifications` + audit | **Not rendered** | ⚠️ FE GAP |
| Repair Timeline | `trench_safety_repairs` + audit | **Not rendered** | ⚠️ FE GAP |

### 2.4 ADMIN CONSOLE (must own ONLY)

| Feature | Required Surface | Current | Status |
|---|---|---|---|
| Global Settings | Admin | Exists outside trench scope | ✅ |
| Permissions / Role Access | Admin | Exists outside trench scope | ✅ |
| Asset Type Definitions | Admin | Constants in `_models.py`; no UI | ⏳ |
| OCR Configuration | Admin | Phase 10 future | ⏳ |
| QR Configuration | Admin | Phase 10 / Admin · not built | ⏳ |
| Feature Flags | Admin | Exists | ✅ |
| Tenant Settings | Admin | Exists | ✅ |
| Platform Configuration | Admin | Exists | ✅ |
| Asset Retire | Terminal admin action | `require_admin` on `POST /…/retire` | ✅ (terminal, acceptable) |
| **Tabulated Data CRUD (PDFs)** | **Safety Portal** per directive | **Lives here (`/admin/trench-boxes`)** | 🔴 DRIFT-1 |

### 2.5 SHOP PORTAL (cross-surface — referenced for clarity)

| Feature | Current | Status |
|---|---|---|
| Shop Repair Queue list | `/shop/trench-safety-repairs` | Phase 6 — operationally correct (Shop fixes boxes). The Safety side of the repair lifecycle (verify, release) must duplicate the queue in the Safety Portal for review. |

---

## 3. Drift Summary

| ID | Drift | Severity |
|---|---|---|
| 🔴 DRIFT-1 | Tabulated Data CRUD (Upload / Replace / Manage Library) is in Admin Console, must be in Safety Portal | HIGH |
| 🔴 DRIFT-2 | Photo Upload backend gate is `require_shop_or_admin`; Directive places Photo Management in Safety Portal | MEDIUM |
| 🔴 DRIFT-3 | Repair Queue Review + Resolve Reports surface only on Shop Portal; Safety Portal has no review surface | HIGH |
| 🔴 DRIFT-4 | Legacy public `/trench-boxes` page duplicates `/trench-safety/tabulated-data` content (same Primer + Library) | LOW (UX) |

## 4. Frontend Gaps (backend exists, no Safety Portal UI)

`Create Asset` · `Edit Asset` · `Change Status` · `Audit Timeline panel` · `Create Inspection` · `Inspection History list` · `Open / Clear Hold` · `Upload / Revoke Certification` · `Repair Review queue + Verify dialog (Safety side)` · `QR generate / reprint / download` · `Photo upload + visibility toggle + library` · `Field Reports review surface`.

These are all P0 blockers for "Safety Portal as the Trench Safety Command Center" per directive.

---

## 5. Verdict

🔴 **FAIL — SURFACE DRIFT DETECTED.**

The Public surface is clean. The Safety Portal exists but is overwhelmingly read-only; nearly every "write" action that the directive places in the Safety Portal has either drifted to Admin / Shop / Backend-only or has no UI at all. Phase 7 should not resume until the Safety Portal Command Center is completed and the drift items are corrected.

See:
- `TRENCH_SAFETY_DRIFT_ANALYSIS.md` — drift-by-drift root cause.
- `TRENCH_SAFETY_COMMAND_CENTER_VERIFICATION.md` — what is and isn't in the Safety Portal today.
- `TRENCH_SAFETY_SURFACE_CORRECTION_PLAN.md` — proposed corrective sprint.
- `TRENCH_SAFETY_SURFACE_LOCK_GO_NO_GO.md` — final verdict + lock.
