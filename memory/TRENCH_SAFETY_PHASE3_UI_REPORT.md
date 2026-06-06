# TRENCH SAFETY PHASE 3 — UI REPORT

**Phase:** 3 of 11 · Safety Portal UI
**Date:** 2026-06-06
**Mode:** UI build · No backend changes · No deploy
**Verdict:** 🟢 PHASE 3 COMPLETE — SAFE TO CONTINUE TO EQUIPMENT INTEGRATION

---

## 1. Files added

```
/app/frontend/src/pages/trench_safety/TrenchSafetyShell.jsx        (tab strip + SafetyShell wrap)
/app/frontend/src/pages/trench_safety/TrenchSafetyHub.jsx          (Dashboard landing)
/app/frontend/src/pages/trench_safety/TrenchSafetyAssetsList.jsx   (filterable roster)
/app/frontend/src/pages/trench_safety/TrenchSafetyAssetDetail.jsx  (read-only asset workbench)
/app/frontend/src/pages/trench_safety/TrenchSafetyTabulatedData.jsx (relocated Tabulated Data)
/app/frontend/src/pages/trench_safety/TrenchSafetyQrLanding.jsx    (PUBLIC mobile QR landing)
```

## 2. Files modified

```
/app/frontend/src/App.js
  • 5 new imports + 7 new <Route> entries (4 Safety + 1 public QR + 3 legacy aliases)

/app/frontend/src/pages/SafetyHub.jsx
  • New `Trench Safety` tile (Boxes icon) in the Operational Output group · testid safety-tile-trench-safety

/app/frontend/src/lib/i18n.js
  • ~120 new keys with full Spanish parity (see TRENCH_SAFETY_PHASE3_SPANISH_CERTIFICATION.md)
```

No backend file was modified. Phase 2 contract unchanged.

## 3. Native MASCI design language adherence

| Convention | How Phase 3 follows it |
|---|---|
| SafetyShell + cyan-700 accent | `TrenchSafetyShell` wraps SafetyShell. Tab strip uses cyan-700 underline. |
| Calm KPI chrome (UX_GOVERNANCE_RULES Rule 5) | Hub KPIs use `bg-white border border-slate-200 rounded-md p-4` with `font-display text-3xl font-black` values — exact match to SafetyHub KPI block. |
| Status colour palette | Same status pill colours as Dispatch/Shop boards (emerald=Available, blue=Assigned, cyan=In Transport, amber=Inspection Hold, red=Repair, slate=Retired). |
| Coaching pattern | Amber-50 / amber-300 inset boxes with `ShieldAlert` icon, max ~3-line copy, no giant manuals. |
| Test-ID discipline | Every interactive element + every alert/KPI carries a `data-testid` (60+ test ids added). |
| Mobile-first | Asset list table progressively hides columns at `sm/md/lg/xl`. QR landing is hard-coded `max-w-md` mobile shell. |
| i18n | Every visible string passes through `useT()`. No string is English-locked. |
| No dead buttons | Detail page is read-only; Phase 6 lifecycle actions explicitly deferred via a coaching note. |

## 4. Routes registered

| Path | Component | Auth | Notes |
|---|---|---|---|
| `/safety/trench-safety` | TrenchSafetyHub | Safety+ | Dashboard landing |
| `/safety/trench-safety/assets` | TrenchSafetyAssetsList | Safety+ | Filterable roster |
| `/safety/trench-safety/assets/:assetId` | TrenchSafetyAssetDetail | Safety+ | Read-only detail |
| `/safety/trench-safety/tabulated-data` | TrenchSafetyTabulatedData | Safety+ | Hosts existing primer + library |
| `/trench-safety/assets/:assetId` | TrenchSafetyQrLanding | **PUBLIC** | Mobile-first, field-safe |
| `/safety-portal/trench-safety/*` | (Navigate redirects) | — | Alias to `/safety/*` |
| `/trench-boxes` | TrenchBoxes (legacy) | PUBLIC | **PRESERVED** |
| `/safety/trench-boxes` | (Navigate redirect to `/trench-boxes`) | — | **PRESERVED** |
| `/admin/trench-boxes`, `/admin/trench-boxes/poster`, `/pm/trench-boxes` | TrenchBoxesAdmin / TrenchBoxPoster | Admin | **PRESERVED** |

## 5. Endpoints consumed (Phase 2, unchanged)

- `GET /api/trench-safety/dashboard` → Hub KPIs / breakdowns / alerts
- `GET /api/trench-safety/assets?...filters` → Assets list
- `GET /api/trench-safety/assets/{ident}` → Asset detail header / fields
- `GET /api/trench-safety/assets/{ident}/inspections` → Detail history
- `GET /api/trench-safety/assets/{ident}/repairs` → Detail history
- `GET /api/trench-safety/assets/{ident}/deployments` → Detail history
- `GET /api/trench-safety/public/assets/{asset_id}` → Mobile QR landing
- (Tabulated Data page reuses `/api/trench-box-files?scope=trench_box` and `/api/trench-boxes` — unchanged)

## 6. Validation matrix (per directive)

| # | Requirement | Result |
|---|---|---|
| 1 | Safety tile now shows Trench Safety | ✅ Added to SafetyHub Operational Output group |
| 2 | Existing Trench Box Tabulated Data still works | ✅ `/trench-boxes` route preserved + admin/pm/poster routes preserved |
| 3 | Existing PDFs still load | ✅ Same `scope="trench_box"` file API (unchanged) |
| 4 | Trench Safety hub loads | ✅ 200 on `/safety/trench-safety` |
| 5 | Dashboard uses real data | ✅ Fetches from `/api/trench-safety/dashboard` — no hardcoded numbers |
| 6 | TB-01 through TB-07 appear | ✅ List renders 7 rows by default |
| 7 | TB-05 missing serial alert appears | ✅ Hub alert + list missing badge + detail alert + QR alert (4 surfaces) |
| 8 | Asset list search/filter works | ✅ q · asset_type · operational_status · condition · needs_review |
| 9 | Asset detail loads for TB-07 | ✅ 200 on `/safety/trench-safety/assets/TB-07` |
| 10 | QR landing loads for TB-07 | ✅ 200 + screenshot captured at `/tmp/qr_tb05.jpg` for TB-05 |
| 11 | QR page does not expose admin controls | ✅ Server-side `public_view()` projection drops sensitive fields; no edit buttons |
| 12 | English UI works | ✅ Manual probe — `EN` default |
| 13 | Spanish UI works | ✅ See `TRENCH_SAFETY_PHASE3_SPANISH_CERTIFICATION.md` |
| 14 | Mobile layout works | ✅ See `TRENCH_SAFETY_PHASE3_MOBILE_QR_CERTIFICATION.md` |
| 15 | No dead buttons | ✅ Detail page is read-only; explicit phase note explains |
| 16 | No mock data | ✅ All counts/data come from Phase 2 backend |
| 17 | No broken existing Safety routes | ✅ SafetyHub.jsx only ADDED a tile + import — all existing tiles unchanged |
| 18 | No backend regression | ✅ 28/28 pytest cases green |
| 19 | No deployment performed | ✅ Preview-only |

## 7. Out-of-scope (deferred per directive)

- QR PNG label generator → Phase 7
- Equipment Inventory deep integration → Phase 4
- Transport / Dispatch movement → Phase 5
- Inspection / Repair / Hold workflow buttons → Phase 6
- Photos uploader UI → Phase 7
- Admin / Shop / Project surfaces → Phase 8
- Reports / Global search wiring / Training surfaces → Phase 9
- OCR → Phase 10

The Asset Detail page intentionally has zero write-action buttons. It states this in a footer phase-note: *"Inspection, repair, assign/return and edit actions land in later certified phases. This Phase 3 view is read-only."*

## 8. Verdict

🟢 **PHASE 3 COMPLETE — SAFE TO CONTINUE TO EQUIPMENT INTEGRATION.**
