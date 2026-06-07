# Trench Safety — Surface Lock GO / NO-GO
**Date:** 2026-02-07
**Stage:** Pre-Phase-7 resumption · Surface Ownership audit
**Mode:** Read-only audit. **No code changes performed** during this certification.

---

## 1. Audit scope
Per OMEGA Trench Safety Surface Ownership Lock directive, every trench-safety function across the four current surfaces (Public Safety Tile · Safety Portal · Admin Console · Shop Portal) was inventoried, mapped against the directive's required surface, and classified as ✅ correct · 🔴 drift · ⚠️ frontend gap · ⏳ future.

Inputs:
- `backend/routes/trench_safety/*.py` (all auth gates).
- `backend/server.py` legacy `/trench-boxes` CRUD.
- `frontend/src/App.js` route table.
- `frontend/src/pages/trench_safety/*` and `frontend/src/pages/TrenchBoxesAdmin.jsx` UI surfaces.

Outputs (this audit's deliverables):
- `TRENCH_SAFETY_SURFACE_OWNERSHIP_AUDIT.md`
- `TRENCH_SAFETY_DRIFT_ANALYSIS.md`
- `TRENCH_SAFETY_COMMAND_CENTER_VERIFICATION.md`
- `TRENCH_SAFETY_SURFACE_CORRECTION_PLAN.md`
- `TRENCH_SAFETY_SURFACE_LOCK_GO_NO_GO.md` (this document)

---

## 2. Drift detected

| ID | Drift | Severity |
|---|---|---|
| DRIFT-1 | Tabulated Data CRUD (Upload / Replace / Delete PDFs) lives on Admin Console (`/admin/trench-boxes` · `require_admin`); directive places it in Safety Portal. | HIGH |
| DRIFT-2 | Photo Upload backend gate is `require_shop_or_admin`; directive places Photo Management in Safety Portal. | MEDIUM |
| DRIFT-3 | Repair Review + Field Report Review surface only on Shop Portal (`/shop/trench-safety-repairs`); directive places Repair Review, Safety Verification, Release Logic, Field Report Review in Safety Portal. | HIGH |
| DRIFT-4 | Legacy public `/trench-boxes` duplicates `/trench-safety/tabulated-data` content. | LOW |

## 3. Safety Portal Command Center completeness

| Section | Verdict |
|---|---|
| Asset Management | ⚠️ Partial (read-only) |
| Tabulated Data Management | 🔴 DRIFT |
| Inspection Management | 🔴 MISSING (backend-only) |
| Hold Management | 🔴 MISSING (backend-only) |
| Certification Management | 🔴 MISSING (backend-only) |
| Repair Management | 🔴 DRIFT + MISSING |
| QR Management | ⏳ Awaiting Phase 7 frontend |
| Photo Management | 🔴 DRIFT (auth) + ⏳ |
| Report Review | 🔴 DRIFT |
| Audit History | 🔴 MISSING (backend-only) |

The Public Safety Tile is **clean** — every required public-tile feature is present, no admin features leak through.

## 4. Verdict

🔴 **FAIL — SURFACE DRIFT DETECTED.**

Reasoning: Phase 7 cannot resume in good conscience because the surface the directive requires it to land on — the Safety Portal Command Center — is not complete. The Public Tile is correctly scoped, but four drift items and an extensive set of frontend gaps mean the Safety Portal does not function as the Command Center described in the directive.

## 5. Required next actions before Phase 7 resumes

Per `TRENCH_SAFETY_SURFACE_CORRECTION_PLAN.md` (proposed Phase 7.5 — Safety Portal Command Center Hardening):

1. Re-gate Tabulated Data CRUD endpoints to `require_safety_or_admin` and move the UI into `/safety/trench-safety/tabulated-data`.
2. Re-gate Photo Upload endpoint to `require_safety_or_admin`.
3. Stand up `/safety/trench-safety/repairs` (Repair Review + Verify) and `/safety/trench-safety/field-reports` (incoming damage reports) on the Safety Portal.
4. Redirect legacy `/trench-boxes` → `/trench-safety/tabulated-data`.
5. Add Asset CRUD UI (Create / Edit / Status / Audit Timeline) to Safety Portal.
6. Add Inspections / Holds / Certifications UIs to Safety Portal Asset Detail.
7. Only then resume Phase 7 (QR + Photo Management frontend) — it will now land inside a complete Asset Detail surface.

## 6. Lock

🔴 **SURFACE LOCK NOT GRANTED.** Phase 7 frontend resumption is **paused** pending Phase 7.5 (Safety Portal Command Center Hardening) authorisation.

No code changes were made in this audit. The previous public UX correction sprint and the Phase 7 backend test fix remain green (Phase 7 backend tests: 14/14).

**STOP per directive. Awaiting operator authorisation to proceed with the Surface Correction Plan.**
