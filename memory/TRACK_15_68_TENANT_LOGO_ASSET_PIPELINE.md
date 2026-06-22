# TRACK 15.68 · Tenant Logo / Asset Pipeline

_Status: ✅ Foundation SHIPPED · Asset migrations pending_

## What shipped
`components/MasciLogo.jsx` is now tenant-aware via `useBranding()`. Also exports `TenantLogo` alias.

**Behaviour matrix**

| Tenant | `branding.logo_url` | Renders |
|---|---|---|
| MASCI (default) | n/a | Original `/masci-mark.png` / wordmark / lockup (unchanged) |
| Customer #2 | URL set | `<img src={branding.logo_url}>` with `onError` hide |
| Customer #2 | empty | `<GenericMonogram>` — first letter of `company_name` on `primary_color` background |
| No tenant resolved | — | Generic monogram |

No broken images (img onError hides; monogram fallback renders).
No console errors observed.

## Audit
| Surface | Status |
|---|---|
| Portal shell logos (`PortalShell.jsx`) | ✅ goes through MasciLogo (now tenant-aware) |
| Cheat-sheet / poster cards | ✅ via MasciLogo |
| Admin panels | ✅ via MasciLogo |
| Login / splash logo | ❌ **STILL LEAKS** — `SplashOverlay.jsx` loads `/masci-mark.png` directly bypassing MasciLogo |
| PDF headers | ❌ Backend `pdf_render.py` / `pm_welcome_pdf.py` use literal MASCI assets and alt text |

## Verdict
Foundation is in place. The 2 remaining leaks (SplashOverlay + backend PDFs) require explicit next-session migration.
