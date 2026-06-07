# Trench Safety · Phase 7.5A — Architecture
**Date:** 2026-02-07
**Verdict:** 🟢 COMMAND CENTER FOUNDATION COMPLETE

## Premise
The Surface Ownership Audit returned 🔴 FAIL. Phase 7.5A corrects the four drift items and builds the missing Safety Portal Command Center foundation (assets, tabulated data, inspections, holds, certifications, audit history). Admin Portal mirrors the Safety Portal — same components, same auth gate, same business logic.

## Non-negotiable rules followed
- **Build once, reuse everywhere.** A single React module `TrenchSafetyActions.jsx` exports every dialog + panel. Safety Portal and Admin Portal both consume it.
- **Same auth gate.** Backend endpoints accept either `X-Safety-Token` or `X-Admin-Token` through the module-level `require_safety_or_admin` function added to `server.py` (mirrors the existing `make_require_safety_or_admin` factory used elsewhere in the codebase).
- **Same translations.** Every new string has both EN (source) and ES translation in `lib/i18n.js`.
- **MASCI visuals.** Reuses `TrenchSafetyShell`, `SafetyShell`, shadcn Dialog/Button/Select/Input, lucide icons, the cyan/amber/red palette, and the existing `data-testid` conventions.
- **No dead buttons.** Every new button calls a working endpoint and toasts success/failure via sonner.

## Surface map after Phase 7.5A

| Surface | Routes | Auth | Owns |
|---|---|---|---|
| Public Tile | `/trench-safety/*` | none | Asset Lookup · QR · Status · Serial · Field Photos · Tabulated Data Viewer · Safety References · Report Issue |
| **Safety Portal** | `/safety/trench-safety/*` | `safety_or_admin` | Assets (CRUD · Retire · Status) · Tabulated Data CRUD · Inspections · Holds · Certifications · Audit Timeline |
| **Admin Portal** | `/admin/trench-safety/*` ← **NEW** | `safety_or_admin` | Same as Safety Portal (superset access; Admin can also retire) |
| Shop Portal | `/shop/trench-safety-repairs` | `shop_or_admin` | Repair Queue (Shop side — Safety verify lands in 7.5B) |

`/trench-boxes` (legacy public) → 301 to `/trench-safety/tabulated-data`. `/admin/trench-boxes` retained as a parallel Admin entry but Tabulated Data management is now reachable inside the Safety/Admin Trench Safety Command Center.

## Drift remediation

| ID | Drift | Fix |
|---|---|---|
| DRIFT-1 | Tabulated Data CRUD on Admin-only | Re-gated `POST/PUT/DELETE /api/trench-boxes` to `safety_or_admin`; surfaced upload/delete in `/safety/trench-safety/tabulated-data` (component reuse via `adminMode={true}`); Admin Portal mirror at `/admin/trench-safety/tabulated-data` uses the same component. |
| DRIFT-2 | Photo Upload gate was `shop_or_admin` | Re-gated `POST /trench-safety/assets/{id}/photos` to `safety_or_admin`. |
| DRIFT-3 | Repair Review only in Shop | Out of Phase 7.5A scope (the directive lists 6 sections; Repairs is 7.5B). |
| DRIFT-4 | Legacy `/trench-boxes` dup | Redirected to `/trench-safety/tabulated-data`. |

## Files touched
**Backend:**
- `backend/server.py` — Added module-level `require_safety_or_admin`; re-gated `POST/PUT/DELETE /api/trench-boxes`.
- `backend/routes/trench_safety/qr_photos.py` — Re-gated `POST /…/photos` to `safety_or_admin`.

**Frontend (new):**
- `src/pages/trench_safety/TrenchSafetyActions.jsx` — shared dialogs + panels.

**Frontend (modified):**
- `src/pages/trench_safety/TrenchSafetyAssetsList.jsx` — `+ New Asset` CTA.
- `src/pages/trench_safety/TrenchSafetyAssetDetail.jsx` — Edit / Retire / Change Status buttons + Holds / Inspections / Certifications / Audit Timeline panels.
- `src/pages/trench_safety/TrenchSafetyTabulatedData.jsx` — `adminMode={true}`.
- `src/App.js` — Admin Portal mirror routes + legacy redirect.
- `src/lib/i18n.js` — ~100 new EN→ES translation keys.

## Tests
- Phase 7 backend regression: **14/14 pass** after re-gating photo upload (the suite uses X-Admin-Token which satisfies `safety_or_admin`).
- Curl smoke: Tabulated Data create, Asset create, Hold open, Inspection record, Audit fetch all return 200 OK with proper actor tracking.
- Frontend lint: zero blocking issues.
- Frontend smoke: legacy `/trench-boxes` redirects correctly; new Asset Detail panels render.
