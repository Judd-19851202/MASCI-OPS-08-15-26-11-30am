# TRACK 15.68 · Legal / Historical Handling

_Status: 🟡 Plan only — no legal-template migration this fork_

## Inventory
- `pages/legal/TermsOfService.jsx` — 45 MASCI references
- `pages/legal/PrivacyPolicy.jsx` — 27 MASCI references

These contain "MASCI General Contractors Inc.", physical address, contact email, and contract language tied to the MASCI operating entity.

## Classification (per amendment §4)
| Sub-bucket | Hits | Action |
|---|---|---|
| Historical legal content (MASCI as operating entity) | All 72 | Stays under MASCI tenant. Customer #2 must NEVER inherit. |
| Tenant legal template | TBD | Must extract all entity-specific strings to `{branding.company_name}`, `{branding.support_email}`, `{branding.legal_address}` (new field) |
| Obsolete dead content | 0 | None identified |

## Required (next session)
1. Add `legal_address`, `legal_entity_name`, `legal_phone`, `legal_jurisdiction` to `tenant_branding` doc + `/api/branding/current` response.
2. Template both `TermsOfService.jsx` and `PrivacyPolicy.jsx` via `useBranding()`.
3. Render MASCI's current text under MASCI tenant from those fields.
4. Render Customer #2's text from their `tenant_branding` doc.
5. Per amendment: "Customer #2 must never inherit MASCI legal identity." Current state **violates this** because the legal pages literally hardcode "MASCI General Contractors Inc."

## Verdict
**NOT YET COMPLIANT.** Track 15.68 stays OPEN until legal templates are migrated.
