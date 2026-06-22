# TRACK 15.68 · Reference Classification (491 remaining)

_2026-06-22_

Re-classified per the Execution Amendment buckets A/B/C/D.

## Bucket A — Must migrate NOW (~250 hits)

| Surface | Hits | File(s) |
|---|---:|---|
| Splash overlay logo asset | 1 | `components/SplashOverlay.jsx` |
| Page sub-headers / "MASCI · Section" labels | ~150 | `pages/Hub.jsx`, `pages/NewMeeting.jsx`, `pages/ViewDailyReport.jsx`, `pages/NewIncident.jsx`, `pages/ViewInspection.jsx`, `pages/V2Compare.jsx`, `pages/TrainingHub.jsx`, `pages/guidance/OperationalGuidanceCenter.jsx`, `pages/trench_safety/PublicExcavationForm.jsx`, `pages/trench_safety/PublicTrenchSafetyDashboard.jsx`, `pages/admin/AdminIntegrationCenter.jsx`, `pages/admin/AdminDlsShiftQR.jsx`, `pages/admin/AssetProfile.jsx`, `pages/ViewIncident.jsx`, `pages/shop/ShopAssetCare.jsx` |
| Legal templates | 72 | `pages/legal/TermsOfService.jsx`, `pages/legal/PrivacyPolicy.jsx` |
| Admin help / guide text | 22 | `pages/AdminGuide.jsx` |
| Operations map MASCI references | 13 | `components/operations-map/MapCanvas.jsx` |
| Dispatch carrier default value | 5 | `components/dispatch/AssignmentCreateDrawer.jsx` |
| Asset filename templates | ~10 | `MASCI_${label}_${id.slice(0,8)}.pdf` in `AdminSafetyFormsPanel.jsx`, `AdminJobMasterPanel.jsx`, `ViewInspection.jsx` and similar download handlers |
| Trench/PublicTrenchHeader/EmployeePicker tags | 2 | `components/trench/PublicTrenchHeader.jsx`, `components/trench/EmployeePicker.jsx` |

## Bucket B — Must become tenant-aware (~80 hits)

| Surface | Hits | File(s) |
|---|---:|---|
| Backend PDF templates | ~40 | `backend/pdf_render.py`, `backend/pm_welcome_pdf.py`, `backend/pdf_branding.py` (alt text, brand name, header strings, default brand) |
| Admin integration labels | 20 | `components/admin/MaintainxP0Tab.jsx`, `components/admin/MappingCleanupTab.jsx` |
| Asset taxonomy "MASCI_GC" canonical | 7 | `backend/services/asset_taxonomy.py` (data taxonomy — relabelled as `OWNER_GC` or tenant-tagged on cutover) |
| `lib/topics/*` SOP references | 4 | `lib/topics/public_interaction.js`, `lib/topics/general.js`, `lib/topics/general.es.js` |
| `lib/i18n.js` MASCI translation keys | 43 | translation map — keys can stay; values template via BrandingProvider in next phase |

## Bucket C — Allowed historical evidence (~80 hits)

| Surface | Hits | Reason |
|---|---:|---|
| `/app/memory/*` (older track files) | 6,679 | Audit trail. The Phase 3 + 15.68 documents themselves reference MASCI as the operating tenant. Per amendment: "do not mutate audit/certification evidence." |
| `backend/projects.py` MASCI_JOBS seed | 233 | MASCI-tenant-only seed data. Tenant-scoped at insert (only runs for MASCI tenant). |
| Test fixtures | 1,865 | `*test*`, `__tests__`, `test_reports/`. Per brief: "Test Fixture YES". |

## Bucket D — Dead code / technical debt (~20 hits)

| Surface | Hits | Notes |
|---|---:|---|
| `components/MasciLogo.jsx` asset paths | 6 | The MASCI brand image files live here. The component itself is now tenant-aware (Track 15.68 work). Asset files (`/masci-mark.png`) stay as the MASCI-tenant asset; never loaded for non-MASCI tenant. **NOT a leak.** |
| `lib/companyInfo.js` MASCI defaults | 6 | Tenant-aware lookup added (Track 15.68). MASCI defaults only returned when `sessionStorage.branding.tenantKey === "masci"`. **NOT a leak.** |
| Asset filenames in download handlers | ~10 | `AdminJobMasterPanel.jsx` uses `MASCI_jobs.xlsx` as default download filename. Should template via `branding.company_name_slug`. Scheduled for next-session sweep. |

## Headline counts (raw scan)
```
total_hits        12,115
disallowed         491    ← frontend pages/components/design-system not yet migrated
allowed           ~11,600
```

## Honest summary
- **Bucket A is the gate.** Until A is zero, Track 15.68 stays OPEN.
- **Bucket B** is the next phase after A — backend PDFs and translation maps require their own branding plumbing.
- **Bucket C** is intentionally untouched. The audit trail is the
  source of truth — mutating it would breach the hard rule
  "no mutating audit/certification evidence."
- **Bucket D** is mostly false-positive (`MasciLogo` is the file that
  CONTAINS the new tenant-aware logic; `companyInfo.js` defaults are
  tenant-gated).

Track 15.68 verdict: **NO-GO** because Bucket A is not zero.
