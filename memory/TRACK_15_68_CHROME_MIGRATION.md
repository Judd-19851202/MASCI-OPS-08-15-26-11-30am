# TRACK 15.68 · Chrome Migration

_Status: 🟡 Partial — Phase 3 baseline preserved; ~250 Bucket-A strings remain_

## Migrated this fork (incremental, on top of Phase 3's 14 surfaces)
- `design-system/PublicShell.jsx` — `MASCI · {surfaceName}` → `{surfaceName}`
- `components/BackendStatusBanner.jsx` — "MASCI backend" → "backend"
- `components/SessionStatusOverlay.jsx` — error overlay titles genericized
- `lib/errorClassification.js` — error copy ("MASCI services" → "platform services", "MASCI Services Temporarily Unavailable" → "Services Temporarily Unavailable")
- `lib/companyInfo.js` — `getCompanyInfo()` now returns blank `NEUTRAL_COMPANY_INFO` for non-MASCI tenants
- `components/MasciLogo.jsx` — tenant-aware (Phase 2 of this track)

## Migrated in Phase 3 (preserved)
14 surfaces: `PortalShell`, `ForgedOpsAttribution`, `CheatSheetCard`,
`JhaPlansPosterCard`, `TrenchBoxPosterCard`, `ShareFormDialog`,
`PromoHeroLoop`, `PosterErrorBoundary`, `BackupHeroPanel`,
`CloudArchivesPanel`, `AdminSafetyFormsPanel`, `AdminShopUsersPanel`,
`EmployeeMasterPanel`, `SupplierMasterPanel`.

## Not migrated (Bucket A — ~250 strings, next session)
`SplashOverlay`, `Hub`, `NewMeeting`, `ViewDailyReport`, `NewIncident`,
`ViewInspection`, `V2Compare`, `TrainingHub`, all `pages/admin/*`,
`pages/trench_safety/*`, `pages/legal/*`, `AdminGuide`, dispatch
carrier defaults, asset filename templates.

## Verdict
**Foundation expanded; bulk migration deferred to next session.**
