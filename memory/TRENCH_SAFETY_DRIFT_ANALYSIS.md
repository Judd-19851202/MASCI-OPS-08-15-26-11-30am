# Trench Safety — Drift Analysis
**Date:** 2026-02-07
**Source matrix:** `TRENCH_SAFETY_SURFACE_OWNERSHIP_AUDIT.md`

---

## 🔴 DRIFT-1 — Tabulated Data CRUD on Admin Console
**Severity:** HIGH

**Where it is now:** `/admin/trench-boxes` (file: `frontend/src/pages/TrenchBoxesAdmin.jsx`) routes through the **Admin Console** wrapper (`AP(...)`) and writes to `POST/PUT/DELETE /api/trench-boxes` — all gated by `require_admin`.

**Where it must live (per directive):** Safety Portal owns Tabulated Data management (Upload PDF, Replace PDF, Link PDF, Manage Library, Verify Matching Assets).

**Root cause:** The library predates the OMEGA directive. `/trench-boxes` was a public viewer and the admin-CRUD twin landed under `/admin/trench-boxes` historically. Phase 3 of the Trench Safety Operations System added a Safety Portal *viewer* (`/safety/trench-safety/tabulated-data`) but never moved the writer.

**Impact:** Safety leaders must hold an admin role to upload a manufacturer sheet — pushes admin role to every safety officer or forces tickets to platform admin. Friction + permissions sprawl.

**Required correction:**
1. Add Upload / Replace / Delete PDF UI inside `/safety/trench-safety/tabulated-data` for Safety role.
2. Change `POST/PUT/DELETE /api/trench-boxes` from `require_admin` → `require_safety_or_admin`.
3. Keep an Admin Console "advanced configuration" entry only for **bulk import**, **Asset Type Definitions**, **OCR config** — i.e. platform-level admin only.
4. Migrate or hide `/admin/trench-boxes` for Safety role (or redirect to `/safety/trench-safety/tabulated-data`).

---

## 🔴 DRIFT-2 — Photo Upload backend gate is Shop
**Severity:** MEDIUM

**Where it is now:** `backend/routes/trench_safety/qr_photos.py:207` — `POST /trench-safety/assets/{ident}/photos` uses `require_shop_or_admin`.

**Where it must live (per directive):** Safety Portal owns Photo Management (Upload, Internal vs Public visibility, Asset Photo Library).

**Root cause:** Phase 7 backend draft anticipated Shop technicians uploading repair photos. Directive clarifies Safety owns the photo lifecycle (Shop's repair photos still attach, but the canonical photo authority is Safety).

**Impact:** Today, a safety officer who is *not* a shop tech cannot upload a photo. Forces over-privileging or impossible workflows.

**Required correction:**
1. Change `POST /…/photos` from `require_shop_or_admin` → `require_safety_or_admin` (Safety owns).
2. Keep Shop able to *attach photos to repair records* via the repair endpoint (a different path) — but the asset-level photo library is Safety-owned.
3. Phase 7 frontend Upload UI must live on the Safety Portal asset detail page (not Shop).

---

## 🔴 DRIFT-3 — Repair Review + Field Report Review only in Shop Portal
**Severity:** HIGH

**Where it is now:**
- `GET /trench-safety/shop/repairs` is only reachable via `/shop/trench-safety-repairs`.
- Public damage reports auto-create `trench_safety_repairs` rows. Those rows surface in the Shop queue only.

**Where it must live (per directive):**
- Safety Portal owns "Review Repair Queue", "Safety Verification", "Release Logic".
- Safety Portal owns "Review Field Reports", "Resolve Reports", "Assign Follow-Up".

**Root cause:** Phase 6 delivered the Shop side. The Safety side (verify + release after Shop completes) is backend-only (`POST /…/repairs/{id}/verify`, `require_safety_or_admin`) with no UI surface.

**Impact:**
- Safety cannot see incoming public damage reports without going to a portal that isn't theirs.
- The hand-off after Shop completes a repair (Safety re-inspection / release) has no UI.

**Required correction:**
1. Add a "Repair Review" page on the Safety Portal `/safety/trench-safety/repairs` showing **all** repair states (Open, In Progress, Waiting on Parts, Vendor Repair, **Completed**, Closed After Verification).
2. Filter / focus state for repairs in `Completed` status with `requires_reinspection=true` → "Awaiting Safety verification".
3. Verify dialog on Safety side (`POST /…/repairs/{id}/verify`) with `reinspection_passed` toggle.
4. Public field reports (created by `POST /trench-safety/public/damage-report`) need their own "Field Reports" inbox on Safety Portal — they should be visible *before* the Shop queue picks them up.

---

## 🔴 DRIFT-4 — Legacy `/trench-boxes` duplicates `/trench-safety/tabulated-data`
**Severity:** LOW (UX clarity)

**Where it is now:** Both pages compose `TabulatedDataPrimer` + `TrenchBoxTabulatedLibrary` verbatim. `/trench-boxes` is the older route (still linked from QR posters); `/trench-safety/tabulated-data` is the new public surface.

**Root cause:** Phase 3 added the public dashboard but left the legacy `/trench-boxes` intact to preserve printed QR posters that point at it.

**Impact:** Two URLs serve identical content. Minor UX confusion and future maintenance risk.

**Required correction:**
1. Keep `/trench-boxes` as a **301 → `/trench-safety/tabulated-data` Navigate** so printed posters keep working.
2. Update any internal links that still reference `/trench-boxes` to use the new route.
3. Document the alias in the public navigation report.

---

## ⚠️ Frontend Gaps (not technically drift, but blockers for Safety Portal Command Center)

Each of these has working backend + permissions but **zero Safety Portal UI**:

| Gap | Backend Endpoint | Notes |
|---|---|---|
| Create Asset | `POST /trench-safety/assets` | Add a "+ New Asset" CTA on `/safety/trench-safety/assets` with a dialog. |
| Edit Asset | `PUT /trench-safety/assets/{id}` | Add Edit pencil on Asset Detail (currently read-only). |
| Change Status | `POST /trench-safety/assets/{id}/status` | Add status menu respecting `validate_status_transition`. |
| Audit Timeline panel | `GET /trench-safety/assets/{id}/audit` | Add a collapsible "Timeline" section on Asset Detail. |
| Create Inspection | `POST /trench-safety/assets/{id}/inspections` | Inspection form dialog (pass/fail + severity). |
| Inspection History | `GET /…/inspections` | Inspection list on Asset Detail. |
| Open Hold | `POST /…/holds` | Hold dialog (Safety/Inspection/Maintenance, reason). |
| Clear Hold | `POST /…/holds/{id}/clear` | Clear hold dialog with reason. |
| Cert Upload | `POST /…/certifications` | Certification upload form (PDF + expires_at). |
| Cert Revoke | `POST /…/certifications/{id}/revoke` | Revoke dialog with reason. |
| Repair Review Queue | `GET /trench-safety/shop/repairs` (re-use) | Add Safety-Portal version that includes pending Safety verification. |
| Safety Verify Repair | `POST /…/repairs/{id}/verify` | Verify dialog with `reinspection_passed` + notes. |
| QR Generate / Download | `GET /…/qr-label.png` | Phase 7 FE. |
| Photo Upload + Visibility | `POST /…/photos` | Phase 7 FE. |
| Photo Library | `GET /…/photos` | Phase 7 FE. |
| Field Reports inbox | derived from `trench_safety_repairs.source=Public QR Damage Report` | New surface. |

---

## Verdict
Drift is real, isolated, and correctable without rewriting the backend. The Safety Portal needs a focused **Command Center sprint** (Phase 7.5 / "Safety Command Center") that:
1. Moves Tabulated Data write-CRUD into Safety Portal and re-gates the backend (`require_safety_or_admin`).
2. Re-gates Photo Upload backend to `require_safety_or_admin`.
3. Adds Safety-Portal Repair Review + Verify + Field Reports inbox.
4. Adds the missing Asset / Inspection / Hold / Certification / Audit UIs that are currently backend-only.
5. Redirects `/trench-boxes` to `/trench-safety/tabulated-data`.

After Phase 7.5 lands, **then** Phase 7 (QR Labels + Photo Management frontend) can resume cleanly — because the Photo and QR work lives inside an existing Asset Detail surface, not in a vacuum.
