# TRACK 15.68A · Splash / Login / Portal Shell Fix

_Status: ✅ SHIPPED_

## What changed
`components/SplashOverlay.jsx` is now fully tenant-aware via `useBranding()`.

| Tenant | Logo | Stripe | Platform name | Tagline |
|---|---|---|---|---|
| MASCI | `/icon-512.png` (unchanged) | `#b91c1c` red (unchanged) | "MASCI OPERATIONS PLATFORM" | "Run every job. Control every detail. Protect everything." |
| Customer #2 (with `logo_url`) | `branding.logo_url` (with `onError` hide) | `branding.primary_color` | `branding.platform_display_name` UPPERCASED | "Customer #2 · Operations" |
| Customer #2 (no `logo_url`) | Generic SVG monogram — first letter of `company_name` on `primary_color` | `branding.primary_color` | platform name | tagline |
| No tenant resolved | Generic neutral monogram on teal | "OPERATIONS PLATFORM" | tagline | tagline |

## Proof (screenshots in `/tmp/`)
- `track_15_68a_customer2_splash.png` — Customer #2 preview shows **teal "C" monogram** + Customer #2 Operations Platform. **NO MASCI MARK**.
- `track_15_68a_masci_splash.png` — MASCI tenant shows the original **red M mark** + red caution stripe. **PARITY PRESERVED**.

## Audit of related shells
| Surface | State |
|---|---|
| `SplashOverlay.jsx` | ✅ Migrated (this fork) |
| `PortalShell.jsx` | ✅ Phase 3 (Track 15.67) — platform_display_name from BrandingProvider |
| `PublicShell.jsx` | ✅ Phase 3 — surface label no longer hardcodes MASCI |
| `BackendStatusBanner.jsx` | ✅ Track 15.68 |
| `SessionStatusOverlay.jsx` | ✅ Track 15.68 |
| `errorClassification.js` | ✅ Track 15.68 |
| Login screen (`SignIn.jsx`) | ⚠️ Page sub-header still contains "MASCI Operations Platform" — page-chrome sweep target |

## Verdict
**SHIPPED.** Customer #2 splash + portal shell chrome render without MASCI logo or MASCI strings.
