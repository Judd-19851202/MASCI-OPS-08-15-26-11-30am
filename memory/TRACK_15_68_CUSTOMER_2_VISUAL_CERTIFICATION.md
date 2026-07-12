# TRACK 15.68 · Customer #2 Visual Certification

_Status: ❌ FAILED — visual walkthrough confirmed MASCI leakage_

## Method
1. Seeded synthetic tenant `track_15_68_tenant_test_delete` in `db.tenant_branding` (Customer #2 Construction LLC, all customer2.example contacts).
2. Loaded preview at `https://backup-forensics.preview.emergentagent.com/?tenantPreview=track_15_68_tenant_test_delete`.
3. Captured login/splash screenshot.

## Visual evidence
The SplashOverlay rendered the **MASCI red "M" mark** even with the preview tenant active. The mark loaded from `/masci-mark.png` because `SplashOverlay` references the asset path directly instead of going through the tenant-aware `MasciLogo` / `TenantLogo` component.

Screenshot: `/tmp/track_15_68_customer2_walkthrough.png`

## Walkthrough results

| Surface | Expected | Actual | Pass? |
|---|---|---|:--:|
| Login splash | Customer #2 monogram on `#0F766E` | MASCI red "M" mark | ❌ |
| API `/api/branding/current` | Customer #2 contacts | Customer #2 contacts | ✅ |
| Portal shell footer | "Customer #2 Operations Platform" | (not reached — splash still up) | — |
| Admin email routing | (not navigated) | — | — |
| Daily Report PDF | Customer #2 header | Backend PDF templates still render "MASCI" | ❌ |
| Legal Terms | Customer #2 legal entity | Hardcoded "MASCI General Contractors Inc." | ❌ |
| AdminGuide | Customer #2 strings | 22 hardcoded MASCI references | ❌ |

## Required for PASS
1. Migrate `SplashOverlay` to use `TenantLogo`.
2. Migrate backend PDF templates via `pdf_branding.py` resolver.
3. Template legal pages via `useBranding()`.
4. Sweep AdminGuide + admin chrome.
5. Re-run full 8-portal walkthrough.

## Verdict
**FAIL** — Customer #2 visual certification did not pass. The Phase 3
governance layer is correct (API returns no MASCI), but the
client-side render still surfaces MASCI assets and copy.
