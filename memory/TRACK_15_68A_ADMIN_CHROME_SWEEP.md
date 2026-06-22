# TRACK 15.68A · Admin Guide + Admin Chrome Sweep

_Status: 🟡 Partial (high-leverage chrome shipped, long tail deferred)_

## Migrated this fork
- **`AdminGuide.jsx`** — `portalName` switched from hardcoded `"MASCI"` to `branding.platform_short_name`. Print-header `Operations Platform` + `mascidocs.com` host now read from `branding.platform_display_name` + `branding.marketing_url`. Page subtitle + footer brand string genericized.

## Not migrated (next phase candidates)
- `components/admin/MaintainxP0Tab.jsx` (6 hits) — operator labels comparing MaintainX inventory vs MASCI inventory.
- `components/admin/MappingCleanupTab.jsx` (4 hits).
- `pages/admin/AdminIntegrationCenter.jsx` (5 hits).
- `pages/admin/AdminDlsShiftQR.jsx`, `pages/admin/AssetProfile.jsx`.
- `pages/Hub.jsx` admin tile sub-headers.

## Verdict
**Partial.** `AdminGuide` is the biggest single admin surface and is now tenant-aware. Other admin tabs still need explicit migration.
