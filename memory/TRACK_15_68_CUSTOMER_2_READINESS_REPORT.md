# TRACK 15.68 · Customer #2 Readiness Report

_2026-06-22 · Verdict: 🟡 partial · ❌ NO-GO for full white-label_

## Three-tier readiness assessment

### Tier 1 — Ready NOW (Phase 3 governance)
| Capability | Status |
|---|:--:|
| Email routing (19 routes per tenant) | ✅ |
| Sender identity resolution | ✅ |
| Reply-to resolution | ✅ |
| PM directory + fallback to ADMIN_DEAD_LETTER_TO | ✅ |
| Portal seeds (safety/shop/HR) env-driven | ✅ |
| Compliance ALWAYS_CC env-driven | ✅ |
| Tenant branding API (`/api/branding/current`) | ✅ |
| Tenant preview header (`X-Tenant-Preview`) | ✅ |
| Audit rows tenant-scoped | ✅ |
| Customer #2 onboarding via env + Mongo upsert (no code) | ✅ for email subsystem |

### Tier 2 — Ready AFTER chrome cutover (Bucket A migrations)
| Capability | Status | Blocker |
|---|:--:|---|
| Splash overlay branded | ❌ | `SplashOverlay.jsx` hardcodes `/masci-mark.png` |
| Legal Terms/Privacy templated | ❌ | 72 hardcoded MASCI strings |
| AdminGuide tenant-aware | ❌ | 22 hardcoded strings |
| Page sub-headers tenant-aware | ❌ | ~150 strings across 25+ page files |
| Operations-map labels tenant-aware | ❌ | 13 strings |
| Dispatch default carrier tenant-aware | ❌ | `{label: "MASCI"}` default |
| Asset filename templates tenant-aware | ❌ | `MASCI_${id}.pdf` patterns |

### Tier 3 — Requires future tenant provisioning / module work
| Capability | Status | Notes |
|---|:--:|---|
| Backend PDF templates | ❌ | `pdf_render.py`, `pm_welcome_pdf.py`, `pdf_branding.py` hardcode MASCI brand. Needs tenant-driven brand resolution. |
| `lib/topics/*` SOP refs | ❌ | Training content — operator scope |
| `i18n.js` MASCI translation keys (43) | ❌ | Translation map — values should template via BrandingProvider |
| Tenant logo upload pipeline | ⚠️ | `branding.logo_url` accepts a URL but no admin uploader exists; operator must host externally and paste URL |
| Module gating (Customer #2 may want fewer portals) | ⚠️ | All portals enabled by default. Per-tenant module flag system not yet built. |

## Operator-independence check (per amendment §6)
| Step | Requires engineering? |
|---|:--:|
| Set tenant_key env | NO — env block |
| Create tenant_branding doc | NO — Admin UI panel exists (TenantBrandingPanel) |
| Seed 19 routes | NO — Admin UI panel exists (EmailRoutingV2Panel) |
| Run route health check | NO — UI button (Phase 3) |
| Replace splash logo | **YES** — code edit required (Bucket A blocker) |
| Replace legal docs | **YES** — code edit required (Bucket A blocker) |
| Replace PDF templates | **YES** — code edit required (Tier 3 blocker) |

## Honest verdict
**Customer #2 can be onboarded TODAY for the email/routing/branding-API
subsystem with zero code changes.** They cannot use the UI yet without
seeing MASCI in the splash, PDFs, legal pages, and ~250 chrome strings.

**Track 15.69 (Email V2 cutover) gate:** Phase 3 work is sufficient
for the cutover from a deliverability + governance standpoint. However,
the brief states cutover requires "Customer #2 cannot accidentally
inherit MASCI identity." That bar is NOT met today.

**Recommendation:** keep `EMAIL_ROUTING_V2=false`. Run one more
implementation fork to close Bucket A + relevant Tier 3 items, then
re-certify.
