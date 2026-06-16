# WHITE-LABEL · BRANDING MATRIX

**Phase 6 deliverable.** Every customer-visible branding surface.

## Status legend

- 🟢 already env-driven
- 🟡 partially configurable (env override exists but default is MASCI)
- 🔴 hardcoded — requires white-label work

## Visual identity surfaces

| Surface | Today | Where | Fix path |
|---------|-------|-------|----------|
| Platform display name | 🔴 "MASCI HUB" / "MASCI Safety Hub" | `i18n.js:173+`, `PortalShell.jsx`, FastAPI title, page titles, login screen | BrandConfig.platform_name |
| Company display name | 🔴 "MASCI" | hub banner templates, legal pages, training docs, help text | BrandConfig.company_name |
| Logo (light bg) | 🔴 `/masci-mark-onlight.png` | `MasciLogo.jsx:49` | per-customer asset path |
| Logo (dark bg) | 🔴 `/masci-mark.png` | `MasciLogo.jsx:49` · `pdf_render.py:31-32` | per-customer asset path |
| Wordmark | 🔴 `/masci-wordmark.png` | `MasciLogo.jsx` | per-customer asset path |
| Full lockup | 🔴 `/masci-full-lockup.png` | `MasciLogo.jsx` | per-customer asset path |
| Favicon | 🔴 `frontend/public/favicon.ico` | static | per-customer asset |
| PWA icons (`apple-touch-icon.png` etc) | 🔴 static | `frontend/public/` | per-customer asset |
| Primary color (PM red) | 🔴 hardcoded `red-600/700/800` Tailwind classes scattered | every PmShell/PM page | central CSS variable + per-customer theme |
| Secondary color (Safety cyan) | 🔴 `cyan-700` | SafetyShell | central CSS variable |
| Accent (HR purple, FL amber, Shop slate, Dispatch slate) | 🔴 scattered Tailwind classes | every portal | central CSS variable |
| Background gradient | 🔴 hardcoded | various login pages | central CSS variable |

## Copy / text surfaces

| Surface | Today | Where | Fix path |
|---------|-------|-------|----------|
| Login hero title | 🔴 "MASCI Safety Hub · Sign in" | `SignIn.jsx`, `AdminLogin.jsx` | BrandConfig.t("login.title") |
| Welcome / onboarding copy | 🔴 references MASCI | `data/training.js`, `guidance/content.py` | BrandConfig.t() · i18n keys |
| Holiday banner templates | 🔴 baked into copy (EN+ES) | `hubBannerTemplates.js:206-208 · 242-244 · 256-258` | BrandConfig.template_render() |
| OSHA visit banner | 🔴 "OSHA Compliance Officer is visiting MASCI job sites" | `hubBannerTemplates.js:150 · 152` | template |
| Critical incident banner | 🔴 "Serious incident on a MASCI project" | `hubBannerTemplates.js:164 · 166` | template |
| Operations Manual | 🔴 MASCI-named throughout | `ops_manual.py` | template |
| Help / training content | 🔴 MASCI-named | `guidance/content.py`, `data/training.js`, `data/training_es.js` | i18n key/value remap |
| Admin Guide | 🔴 MASCI-named | `pages/AdminGuide.jsx` | i18n |
| Terms of Service | 🔴 "MASCI General Contracting" entity · `mascidocs.com` domain | `pages/legal/TermsOfService.jsx:46 hits` | per-customer legal pages |
| Privacy Policy | 🔴 same | `pages/legal/PrivacyPolicy.jsx:31 hits` | per-customer legal pages |
| Support email / phone | 🔴 hardcoded MASCI contact | various help pages | BrandConfig.support_email · phone |
| Public form titles | 🟡 some env-driven, most hardcoded | various | audit per-form |
| QR labels | 🔴 baked MASCI branding | inspection QR generator | BrandConfig.qr_brand |

## Email surfaces

| Surface | Today | Where | Fix path |
|---------|-------|-------|----------|
| Sender domain | 🟡 from Resend account default | Resend dashboard | per-customer Resend domain |
| `RESEND_FROM` env var | 🟢 supported | `phase4.py` callers | already env-driven |
| Reply-to | 🔴 hardcoded MASCI safety inbox | various email helpers | BrandConfig.reply_to |
| Email logo (header) | 🔴 MASCI logo | email render module | per-customer asset |
| Email footer | 🔴 "MASCI Hub" disclaimer | various email helpers | BrandConfig.email_footer |
| Subject prefix | 🔴 sometimes "MASCI HUB · …" | sporadic | BrandConfig.subject_prefix |
| Default recipients | 🟡 env-overridable | `email_routing.py:75 · 76 · 87` (env-driven) · 14-31 (hardcoded fallback) | extend env-driven on every fallback |

## PDF / report surfaces

| Surface | Today | Where | Fix path |
|---------|-------|-------|----------|
| PDF header logo | 🔴 `LOGO_PATH = "masci-mark-onlight.png"` | `pdf_render.py:31` | BrandConfig.pdf_logo_path |
| PDF watermark | 🔴 `WATERMARK_PATH = "masci-mark.png"` | `pdf_render.py:32` | BrandConfig.pdf_watermark_path |
| PDF section labels | 🔴 "MASCI Crews on Site", "MASCI Hauling" | `pdf_render.py:755 · 1101` | BrandConfig.t("pdf.section.company_crews") |
| Filename pattern | 🔴 contains "MASCI" in some helpers | various PDF generators | BrandConfig.filename_prefix |
| Training PDF brand | 🔴 "MASCI HUB" baked | `training_pdf.py:724-725` | BrandConfig.t() |
| Cover page company name | 🔴 hardcoded | various PDF generators | BrandConfig.company_name |

## Verdict

**~50 customer-visible branding surfaces** are currently hardcoded. None of them have a central source of truth. A BrandConfig provider (single object, single source of truth, env-driven values) would parameterize all of them in 2-3 weeks of focused work.
