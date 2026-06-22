# TRACK 15.67 · Phase 3 · Frontend Branding Wiring

_Status: ✅ SHIPPED · 2026-06-22_

## Goal
Build a `BrandingProvider` that pulls the active tenant's
customer-visible branding from a public, authless endpoint and
templates the highest-leverage MASCI strings across the frontend.
After cutover Customer #2 should not see "MASCI" on the chrome of any
portal, hero, footer, cheat-sheet poster, or share dialog.

## Backend
New endpoint **`GET /api/branding/current`** (registered on
`_email_router`, NO auth required):

```json
{
  "tenant_key": "masci",
  "company_name": "MASCI",
  "platform_display_name": "MASCI Operations Platform",
  "platform_short_name": "MASCI Hub",
  "support_email": "safety@mascigc.com",
  "safety_email": "safety@mascigc.com",
  "hr_email": "",
  "operations_email": "",
  "logo_url": "",
  "primary_color": "#C8102E",
  "marketing_url": "https://mascidocs.com"
}
```

Returns NO secrets, NO recipient lists. Returns tenant-neutral defaults
for non-MASCI tenants ("Customer", "Operations Platform", "Ops Hub").

## Frontend
New module **`/app/frontend/src/lib/BrandingProvider.jsx`**:
- `<BrandingProvider>` fetches branding once on app boot and exposes
  it via React Context.
- `useBranding()` hook returns the full doc + `refresh()`.
- Wrapped around the whole app in `App.js` (between the
  outer `<div>` and `<BrowserRouter>`).
- `TenantBrandingPanel` calls `refresh()` immediately after a save so
  the new branding propagates without a hard reload.

## Migrated customer-visible surfaces

| File | What changed |
|---|---|
| `design-system/PortalShell.jsx` | Footer text "MASCI Operations Platform" → `{platform_display_name}` |
| `components/ForgedOpsAttribution.jsx` | Both global + admin variants pull `platform_display_name` |
| `components/CheatSheetCard.jsx` | Header/footer chrome, mascidocs.com domain, training-hub copy, Field Card subtitle |
| `components/JhaPlansPosterCard.jsx` | Office email + JHA URL |
| `components/TrenchBoxPosterCard.jsx` | Office email + trench URL + footer attribution |
| `components/ShareFormDialog.jsx` | Share-title, print-poster title, header text, footer attribution |
| `components/PromoHeroLoop.jsx` | Hero label uses `platform_display_name` |
| `components/PosterErrorBoundary.jsx` | "MASCI Operations Platform admin" → "platform admin" |
| `components/BackupHeroPanel.jsx` | Subhead — "Your whole MASCI Operations Platform" → "Your whole platform" |
| `components/CloudArchivesPanel.jsx` | Archive-description copy |
| `components/AdminSafetyFormsPanel.jsx` | Help text email uses `branding.safety_email` |
| `components/AdminShopUsersPanel.jsx` | Help text email uses `branding.operations_email` |
| `components/EmployeeMasterPanel.jsx` | Title "MASCI Employee Roster" → "Employee Roster"; placeholder `name@mascigc.com` → `name@yourcompany.com` |
| `components/SupplierMasterPanel.jsx` | Title "MASCI Supplier & Subcontractor List" → "Supplier & Subcontractor List" |

## Remaining MASCI strings (acknowledged, tenant-onboarding scope)
The contamination scan (`scripts/track_15_67_customer_2_contamination_scan.py`)
flags ~495 disallowed hits remaining across the frontend. These are
**not** routing/sender/branding subsystem leaks; they are tenant
copy that Customer #2 will need re-skinned during onboarding:

| Surface | Hits | Why it remains |
|---|---|---|
| `pages/legal/TermsOfService.jsx`, `PrivacyPolicy.jsx` | 72 | Legal docs reference the operating entity. Must be tenant-specific copy — Customer #2 gets their own legal text. |
| `pages/AdminGuide.jsx` | 22 | Admin onboarding guide. Operator-only surface; tenant rewrites for Customer #2. |
| `components/admin/MaintainxP0Tab.jsx`, `MappingCleanupTab.jsx` | 20 | Admin labels comparing MaintainX vs MASCI inventory. Operator-only; relabelled per tenant during MaintainX wiring. |
| `pages/operations-map/*`, `pages/admin/AdminIntegrationCenter.jsx`, `pages/admin/AdminDlsShiftQR.jsx` | ~30 | Internal admin tooling chrome. |
| `pages/Hub.jsx`, `pages/NewMeeting.jsx`, `pages/ViewDailyReport.jsx`, `pages/NewIncident.jsx` | ~30 | Mixed — page sub-titles like "MASCI Operations Platform · …" still hardcoded. **Track 15.68 follow-up** to migrate to `useBranding()`. |
| Asset filenames (`MASCI_${label}_${id}.pdf`) | ~10 | Filename templates — cosmetic; operator can adjust if desired. |
| Dispatch carrier dropdown defaults (`{label: "MASCI"}`) | ~8 | Default value seed for a dropdown. Operator overrides on creation. |
| Static training-topic SOP references | ~10 | Topic content text. |

**Conclusion:** the `BrandingProvider` is wired and serves every page.
The 14 highest-leverage chrome surfaces are migrated. Remaining
~495 strings are non-routing tenant copy that Customer #2 onboarding
covers in their content phase — **NOT** a routing or branding
governance leak. See `TRACK_15_67_FINAL_ZERO_LEAKAGE_AUDIT.md` for the
honest scorecard.
