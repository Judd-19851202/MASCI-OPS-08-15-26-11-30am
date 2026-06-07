# Trench Safety — Public UX Correction Report
**Sprint:** Public Trench Safety UX Correction (post Phase 6, pre Phase 7)
**Date:** 2026-02-07
**Scope:** Public-facing `/trench-safety` surfaces only. No admin/portal changes. No backend behavioural changes beyond field-safe projection extension.

---

## 1. Findings (from preview screenshots)

| # | Symptom | Surface |
|---|---|---|
| 1 | Public Trench Safety landing too thin/basic — felt like a placeholder, not a field command surface | `/trench-safety` |
| 2 | `Tabulated Data` and `Safety References` tiles both linked to `/trench-boxes` — same content, two names | `/trench-safety` |
| 3 | Asset/QR field view did not surface the Serial Number near the top — crews had to scroll | `/trench-safety/assets/:assetId` |
| 4 | All public trench pages only had `HOME`, which yanked users to MASCI Home instead of contextual back | All public trench pages |

---

## 2. Corrections Applied

### 2.1 Public landing upgraded (`/trench-safety`)
- Added an explicit **Trench Safety purpose paragraph** under the title.
- Promoted **Asset Lookup** into a dark accented panel — the primary action.
- Added a dedicated **QR Scan Guidance** strip with the directive line *"Scanning does not move this asset."*
- Added a **Stop-Work Authority** banner + a **Match-the-box-to-its-tabulated-data** coaching strip.
- Split the action tiles into three distinct destinations (Tabulated Data · Safety References · Report a Problem).
- Expanded **Fleet Overview** with a second row of asset-type counts (Trench Boxes, End Panels, Spreader Bars, Other Assets).
- Added a **Competent Person Required** reminder block.

### 2.2 Distinct Tabulated Data + Safety References surfaces
- **NEW** `/trench-safety/tabulated-data` → composes the existing `TabulatedDataPrimer` + `TrenchBoxTabulatedLibrary` verbatim. Holds manufacturer-engineered OSHA PDFs, soil-type/spreader/depth limits.
- **NEW** `/trench-safety/references` → OSHA / general trench safety guidance, competent-person reminders, stop-work, unsafe-condition examples, missing pins, missing labels, safe-use reminders, tabulated-data-match coaching.
- Each surface **cross-links** to the other so crews can flip without bouncing through the dashboard.
- Action tiles on the landing now point at the **distinct** routes — no more duplicate behind two names.

### 2.3 Standalone Report surface (`/trench-safety/report`)
- The damage / unsafe-condition / missing-pins / missing-labels report can now be opened from a direct URL with optional `?asset_id=` prefill — useful for posters, QR labels, and stop-work moments where a crew is in a different physical scan context.

### 2.4 Serial Number visibility on QR landing
- Added a **prominent Serial Number block** inside the hero card (just under the status pill).
- Present-serial assets (e.g., TB-01) display the serial in monospace bold.
- Missing-serial assets (e.g., TB-05) render a **red bordered alert** that reads `Missing — Action Required` with an explicit "Verify the physical serial plate before use · Report to Safety" line.
- The detail card now also lists `Serial Number` as a labelled row so it appears in the standard Asset Details table.

### 2.5 Public projection extended
- `_helpers.public_view` now exposes `serial_number` (kept inside the field-safe set, which already exposed `missing_serial_number`, `condition`, `current_location`, etc.).
- No internal/audit data was added.

---

## 3. Files Changed

### Backend
- `backend/routes/trench_safety/_helpers.py` — added `serial_number` to the `public_view` keep set.

### Frontend
- **Created** `frontend/src/components/trench/PublicTrenchHeader.jsx` — reusable contextual header with HOME + back link + LangToggle.
- **Created** `frontend/src/pages/trench_safety/PublicTrenchSafetyTabulatedData.jsx`.
- **Created** `frontend/src/pages/trench_safety/PublicTrenchSafetyReferences.jsx`.
- **Created** `frontend/src/pages/trench_safety/PublicTrenchSafetyReport.jsx`.
- **Rewritten** `frontend/src/pages/trench_safety/PublicTrenchSafetyDashboard.jsx`.
- **Rewritten** `frontend/src/pages/trench_safety/TrenchSafetyQrLanding.jsx`.
- **Updated** `frontend/src/App.js` — registered three new public routes.

---

## 4. Validation Evidence

| # | Requirement | Result |
|---|---|---|
| 1 | Public Trench Safety landing is upgraded | ✅ Screenshot · purpose + stop-work + lookup + QR guidance + 3 tiles + fleet overview rendered. |
| 2 | Tabulated Data and Safety References are distinct | ✅ Two routes, two pages, two content sets. Cross-link present each direction. |
| 3 | TB-01 public asset page shows serial number | ✅ Hero shows `Serial Number: C080102`. Details table shows `Serial Number: C080102`. |
| 4 | TB-05 public asset page shows missing serial alert | ✅ Hero shows red-bordered `Serial Number: Missing — Action Required` plus a "Verify the physical serial plate before use" line. Details table also flags it. |
| 5 | Contextual back navigation works on all public trench pages | ✅ `/trench-safety` → `/safety` · `/trench-safety/assets/:id` → `/trench-safety` · same for tabulated-data, references, report. |
| 6 | HOME still works separately | ✅ Distinct HOME button in the header (and the MASCI mark) both route to `/`. |
| 7 | No admin functions exposed publicly | ✅ Field-safe projection only · no edit / assign / inspection-create / cert-issue surfaces appear on public routes. |
| 8 | English works | ✅ Screenshot. |
| 9 | Spanish works | ✅ `Seguridad de Zanjas`, `Atrás`, `Búsqueda de Activo`, `Datos Tabulados`. |
| 10 | Mobile works | ✅ 480 × 700 viewport renders cleanly · header, hero, lookup, tiles stack vertically. |
| 11 | Existing Phase 7 backend test fix is not disturbed | ✅ `pytest backend/tests/test_trench_safety_phase7.py` → **14 passed, 0 failed**. |
| 12 | No deployment | ✅ Preview only · no production push. |

---

## 5. Verdict

🟢 **PUBLIC TRENCH SAFETY UX FIXED — SAFE TO RESUME PHASE 7**
