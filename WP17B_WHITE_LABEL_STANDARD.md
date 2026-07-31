# WP-17B White-Label Standard

## Exact named white-label / branding owners: `10`
1. `backend/branded_portal_emails.py`
2. `backend/branding_resolver.py`
3. `backend/pdf_branding.py`
4. `backend/pdf_branding_rl.py`
5. `backend/scripts/generate_hub_logos.py`
6. `backend/scripts/rebuild_brand_assets.py`
7. `frontend/src/components/MasciLogo.jsx`
8. `frontend/src/components/TenantBrandingPanel.jsx`
9. `frontend/src/lib/BrandingProvider.jsx`
10. `frontend/src/lib/brandFilename.js`

## Findings
- White-label behavior already affects web shell, PDFs, and emails.
- Branding logic is present in both frontend and backend, which is correct for outputs, but rules must be canonically documented.
- Brand identity is not missing; its governance is under-documented.

## Standard
- One canonical tenant-brand resolver
- One logo/source-of-truth policy
- One filename/output-branding rule
- One web/email/PDF parity rule

## Disposition
- Existing runtime branding owners: `KEEP`
- Rule documentation and parity enforcement: `STANDARDIZE`