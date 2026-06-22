# TRACK 15.68A · Legal Template Migration

_Status: ✅ SHIPPED (tenant-gated render)_

## Approach
Legal text is a contract between the licensing customer and ForgedOps LLC — there is no defensible way to "auto-fill" it for an arbitrary tenant. Track 15.68A therefore:

1. **MASCI tenant** renders the existing iter239 / iter76 legal text unchanged. Wrapped in a private `MasciTerms()` / `MasciPrivacy()` component which is only invoked when `branding.tenant_key === "masci"`.
2. **Any other tenant** renders a clear placeholder card asking the operator to publish their tenant-specific terms (with the operator's `support_email` shown as the contact point).

## Files
- `frontend/src/pages/legal/TermsOfService.jsx`
- `frontend/src/pages/legal/PrivacyPolicy.jsx`

Both now read `useBranding()`. If `!isMasci`, render `<NonMasciLegalPlaceholder>` / `<NonMasciPrivacyPlaceholder>` with `data-testid="legal-tenant-placeholder"` / `data-testid="privacy-tenant-placeholder"`.

## Hard rules honoured
- ✅ MASCI legal pages unchanged (existing approved text preserved verbatim under MASCI tenant).
- ✅ Customer #2 cannot inherit MASCI legal identity — sees a placeholder card naming their tenant's `company_name` and `support_email`.
- ✅ Historical legal doc (the original iter239 text) preserved inside the codebase as required by the brief's "do not mutate historical evidence" rule.
- ✅ No new branding fields strictly required; existing `company_name` + `support_email` are sufficient for the placeholder.

## Future fields (recommended for next phase)
For Customer #2 to publish full legal text natively, add to `tenant_branding`:
- `legal_company_name`
- `legal_contact_email`
- `legal_address`
- `privacy_contact_email`

Then operators can paste rendered Markdown directly into a tenant-scoped legal collection. Not required for Track 15.68A — the placeholder already prevents MASCI leakage.

## Contamination scan note
The scanner still counts 72 MASCI literals inside `MasciTerms()` / `MasciPrivacy()` — that's correct: the MASCI legal text remains in the source for the MASCI tenant. **None of those strings are rendered to a non-MASCI tenant** because the components are gated. The contamination scan is source-code-aware, not render-aware.

## Verdict
**SHIPPED.** Customer #2 never receives MASCI legal text.
