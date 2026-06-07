# Trench Safety — Public UX Correction GO / NO-GO
**Sprint:** Public Trench Safety UX Correction
**Date:** 2026-02-07
**Stage:** Pre Phase 7 resumption
**No deployment performed.** Preview environment only.

---

## 1. Sprint Scope (from operator directive)

1. ✅ Public Trench Safety landing must feel like a real field command section, not a placeholder.
2. ✅ Tabulated Data and Safety References must be split into two clearly different experiences (no duplication under two names).
3. ✅ Every public asset / QR field view must show Serial Number clearly near the top; TB-05 must read `Serial Number: Missing — Action Required`.
4. ✅ Every public trench page gets contextual back navigation; HOME is preserved as a separate affordance and is not the only way out.
5. ✅ Existing Phase 7 backend test fix is not disturbed.

---

## 2. Required validation matrix

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Public Trench Safety landing is upgraded | ✅ | Purpose copy, stop-work, lookup panel, QR guidance, 3 distinct tiles, two-row fleet overview, competent-person reminder. Screenshot in `TRENCH_SAFETY_PUBLIC_UX_CORRECTION_REPORT.md`. |
| 2 | Tabulated Data and Safety References are distinct | ✅ | Two routes (`/trench-safety/tabulated-data`, `/trench-safety/references`), two file modules, no overlapping content, deliberate cross-links between them. See `TRENCH_SAFETY_REFERENCE_SPLIT_REPORT.md`. |
| 3 | TB-01 public asset page shows serial number | ✅ | Hero block + details row both display `C080102`. Playwright: `TB01 serial='C080102' missing_alert=0`. |
| 4 | TB-05 public asset page shows missing serial alert | ✅ | Hero red-bordered block displays `Missing — Action Required` with verify-physical-plate line. Playwright: `TB05 serial='Missing — Action Required' missing_alert=1`. |
| 5 | Contextual back navigation works on all public trench pages | ✅ | `/trench-safety` → `/safety`; `/trench-safety/assets/:id` → `/trench-safety`; same for tabulated-data, references, report. Playwright: navigation transitions verified. |
| 6 | HOME still works separately | ✅ | Distinct HOME affordance in the header right cluster; routes to `/`. Playwright: `home -> https://…/`. |
| 7 | No admin functions exposed publicly | ✅ | Public projection only exposes field-safe keys; no edit / assign / inspect-create / cert-issue surfaces on public routes. |
| 8 | English works | ✅ | Screenshots in EN. |
| 9 | Spanish works | ✅ | `Seguridad de Zanjas`, `Atrás`, `Búsqueda de Activo`, `Datos Tabulados`. |
| 10 | Mobile works | ✅ | 480×700 viewport renders cleanly · header, hero, lookup, tiles stack vertically without truncation. |
| 11 | Existing Phase 7 backend test fix is not disturbed | ✅ | `pytest backend/tests/test_trench_safety_phase7.py` → **14 passed, 0 failed**. |
| 12 | No deployment | ✅ | Preview environment only. |

---

## 3. Files touched

### Backend
- `backend/routes/trench_safety/_helpers.py` — extend `public_view` keep set with `serial_number`.

### Frontend
- **New** `frontend/src/components/trench/PublicTrenchHeader.jsx`
- **New** `frontend/src/pages/trench_safety/PublicTrenchSafetyTabulatedData.jsx`
- **New** `frontend/src/pages/trench_safety/PublicTrenchSafetyReferences.jsx`
- **New** `frontend/src/pages/trench_safety/PublicTrenchSafetyReport.jsx`
- **Rewritten** `frontend/src/pages/trench_safety/PublicTrenchSafetyDashboard.jsx`
- **Rewritten** `frontend/src/pages/trench_safety/TrenchSafetyQrLanding.jsx`
- **Updated** `frontend/src/App.js`

### Memory / certification
- `memory/TRENCH_SAFETY_PUBLIC_UX_CORRECTION_REPORT.md`
- `memory/TRENCH_SAFETY_PUBLIC_NAVIGATION_REPORT.md`
- `memory/TRENCH_SAFETY_REFERENCE_SPLIT_REPORT.md`
- `memory/TRENCH_SAFETY_SERIAL_VISIBILITY_CERTIFICATION.md`
- `memory/TRENCH_SAFETY_PUBLIC_UX_GO_NO_GO.md` (this document)

---

## 4. Anti-regression
- Phase 7 backend test suite executes against `localhost:8001` — all 14 tests green after the changes. The `_helpers.public_view` mutation only added a key; no existing key was removed.
- Authenticated `safety/trench-safety/*` portal routes are untouched.
- Legacy `/trench-boxes` route remains live for old posters/QRs.
- No Mongo collection schema change.

---

## 5. Final Verdict

🟢 **PUBLIC TRENCH SAFETY UX FIXED — SAFE TO RESUME PHASE 7**

STOP per operator directive. Phase 7 (QR Labels + Photo Management — frontend completion + certification) does not resume without explicit operator authorisation.
