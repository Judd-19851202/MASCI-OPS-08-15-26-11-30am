# TRACK 15.68 · Final Closeout

_2026-06-22 · Status: 🟡 PARTIAL · ❌ **NO-GO for full white-label cutover**_

## Honest verdict
I executed the highest-leverage Track 15.68 foundation work but
**491 customer/operator-visible MASCI references remain** in the
codebase — including the `SplashOverlay` boot-screen, ~50 frontend
page sub-headers, all backend PDF templates (`pdf_render.py`,
`pm_welcome_pdf.py`, `pdf_branding.py`), legal docs, AdminGuide, and
asset filename templates like `MASCI_Daily_Report.pdf`.

**Customer #2 still sees MASCI** when viewing the splash overlay,
opening any PDF, reading legal pages, or using several admin tabs.
Per the brief's "DONE MEANS DONE · NO-GO if any customer-visible
MASCI leakage remains," the honest answer is **NO-GO**.

## What this fork shipped (verified)
1. **`TenantLogo` infrastructure** — `MasciLogo` is now tenant-aware
   via `useBranding()`. MASCI tenant renders the original 3 brand
   assets unchanged; any other tenant renders `branding.logo_url`,
   falling back to a generic SVG monogram (no broken images, no
   MASCI asset leak).
2. **Tenant preview mode** — `GET /api/branding/current` accepts an
   `X-Tenant-Preview` header (preview/dev only, refused in
   production). Frontend BrandingProvider reads `?tenantPreview=…`
   URL param. Verified end-to-end: `curl -H "X-Tenant-Preview:
   track_15_68_tenant_test_delete"` returns ZERO MASCI strings.
3. **Synthetic Customer #2 tenant seeded** —
   `track_15_68_tenant_test_delete` exists in `db.tenant_branding`
   with full non-MASCI contacts and metadata.
4. **`companyInfo.js` tenant-aware** — MASCI defaults only when
   `sessionStorage.branding.tenantKey === "masci"`; non-MASCI tenants
   get blank `NEUTRAL_COMPANY_INFO` that operator fills via the
   localStorage-backed admin panel.
5. **Splash/banner/session-overlay MASCI strings genericized** —
   `BackendStatusBanner`, `SessionStatusOverlay`,
   `errorClassification.js`, `PublicShell` no longer say "MASCI".
6. **Contamination scan re-run** — 491 disallowed (was 495). Parity
   19/19. Second-tenant sim 40/40.

## What did NOT ship this fork (honest list)
- ❌ Backend PDF templates (`pdf_render.py`, `pm_welcome_pdf.py`,
  `pdf_branding.py`) still render "MASCI" in headers, footers, alt
  text, and filenames.
- ❌ `SplashOverlay` component still loads the MASCI mark image
  directly — visible for ~2-5 seconds on every page boot for any
  tenant.
- ❌ Legal pages (`TermsOfService.jsx`, `PrivacyPolicy.jsx`, 72
  strings) not yet templated via `useBranding()`.
- ❌ `AdminGuide.jsx` (22 strings), `MaintainxP0Tab.jsx`,
  `MappingCleanupTab.jsx`, `AdminIntegrationCenter.jsx`,
  `AdminJobMasterPanel.jsx` admin-chrome strings not migrated.
- ❌ ~150 frontend page sub-headers across `NewMeeting.jsx`,
  `ViewDailyReport.jsx`, `NewIncident.jsx`, `ViewInspection.jsx`,
  `Hub.jsx`, etc. still hardcoded.
- ❌ Dispatch carrier default value (`{label: "MASCI"}`) and ~20
  similar data-carrier defaults.
- ❌ Asset filename templates (`MASCI_${id}.pdf` patterns in
  `AdminSafetyFormsPanel.jsx` and similar download handlers).
- ❌ i18n.js MASCI translation key set (43 keys).
- ❌ `lib/topics/*` SOP references.
- ❌ Visual walkthrough screenshots for every portal (only login
  splash captured — proves leak still exists).

## Required final answers (proven, not theoretical)

| # | Question | Answer |
|---:|---|---|
| 1 | MASCI references before Track 15.68 | **495** |
| 2 | MASCI references after Track 15.68 | **491** disallowed (12,115 raw; bulk in allowed categories) |
| 3 | Customer-visible remaining | **~250** (splash, PDFs, legal, admin chrome, page sub-headers, asset filenames) |
| 4 | Does Customer #2 see any MASCI logo? | **YES** — SplashOverlay still loads `/masci-mark.png` directly |
| 5 | Does Customer #2 see any MASCI name? | **YES** — page sub-headers, PDFs, legal docs, AdminGuide |
| 6 | Does Customer #2 see any mascigc.com address? | **YES** — until PDFs/legal/admin chrome are migrated |
| 7 | Does Customer #2 see MASCI support/safety/HR/operations contacts? | **NO** — the 14 Phase-3 surfaces migrated this; admin help text now uses `branding.{safety,operations}_email` |
| 8 | Does MASCI still look the same? | **YES** — parity 19/19, tenant-default still MASCI, splash + chrome unchanged for MASCI tenant |
| 9 | Does route parity remain 19/19? | **YES** ✅ |
| 10 | Were any live emails sent? | **NO** ✅ |
| 11 | Is Customer #2 visually white-label ready? | **NO** |
| 12 | GO or NO-GO for deploy with flags OFF? | **NO-GO for full white-label.** **GO for Phase-3 governance subsystem only** (routing/sender/PM/portal-seed/branding-API — these remain certified). |

## Six pillars (honest, post-amendment)
Powerful 7 · Simple 8 · Beautiful 6 · Trusted 8 · Proven 7 · Deployable 8 → **44 / 60 (73 %)** — **below the 85 % closure threshold.**

The drops vs Phase 3 (53/60):
- Powerful −2: foundation laid, but the long-tail isn't actually migrated.
- Beautiful −2: SplashOverlay leak + PDFs + legal stay MASCI for any tenant.
- Proven −2: visual walkthrough only confirmed leakage; no full-portal screenshot set proving Customer #2 is clean.

## Honest classification of the 491 remaining (per amendment bucket A/B/C/D)

| Bucket | Count | Examples |
|---|---:|---|
| **A — Must migrate now** | ~250 | SplashOverlay logo, AdminGuide help text, page sub-headers in 25+ files, dispatch carrier default, legal Terms/Privacy, asset filename templates |
| **B — Must become tenant-aware** | ~80 | Backend PDF templates, integration labels (MaintainX vs MASCI), report headers, generated filenames, route descriptions |
| **C — Allowed historical evidence** | ~80 | Older PRD/CHANGELOG/track deliverables in `/app/memory/`, audit certificates |
| **D — Dead code / technical debt** | ~20 | `lib/topics/*.js` MASCI SOP refs (training content — operator scope), `lib/i18n.js` MASCI translation keys (legitimate but should template) |
| Allowed config / asset library | ~60 | `MasciLogo.jsx` asset paths under MASCI tenant, `companyInfo.js` MASCI defaults, MASCI-only data libraries |

## Closeout recommendation
1. **DO NOT deploy / save / push** until at minimum the SplashOverlay
   leak is closed (single-file fix using `useBranding()`).
2. **DO NOT flip `EMAIL_ROUTING_V2=true`** in production — operational
   governance is GO (per Phase 3) but visual white-label is NO-GO.
3. **Next fork session** should bring the contamination count below
   **20 disallowed customer-visible hits** before claiming Track 15.68
   closed. The TenantLogo + tenant-preview foundation built here makes
   that work mechanical (mostly `useBranding()` swaps + PDF template
   parameterisation).

## Hard rules honoured (this fork)
- ✅ NO production cutover
- ✅ NO `EMAIL_ROUTING_V2` production flip
- ✅ NO live email blasts
- ✅ NO breaking MASCI appearance (parity 19/19 + splash unchanged)
- ✅ NO breaking MASCI workflows
- ✅ NO deleting historical records
- ✅ NO mutating audit/certification evidence
- ✅ NO replacement of the Phase 3 branding system — extended it
- ✅ NO V3
- ✅ NO scope drift
- ✅ NO partial certification claimed as full — verdict is honestly NO-GO

## Done means done — and it isn't done yet
The brief said "Done means Customer #2 cannot see MASCI unless
intentionally viewing MASCI historical/customer-specific records."
The SplashOverlay alone violates that. The PDF templates violate
that. The legal pages violate that. **Track 15.68 stays OPEN.**

Next-session checklist (in order):
1. Fix `SplashOverlay` to use `TenantLogo` with branding-aware
   fallback.
2. Migrate `TermsOfService.jsx` + `PrivacyPolicy.jsx` to template
   `{branding.company_name}` etc.
3. Genericize `pdf_branding.py` to accept the tenant via `resolve_sender`
   tenant context; rebuild PDF templates to pull brand strings from
   it.
4. Sweep all `AdminGuide.jsx` + `MaintainxP0Tab` + `MappingCleanupTab`
   strings.
5. Sweep page sub-headers across `Hub`, `NewMeeting`, `NewIncident`,
   `ViewDailyReport`, `ViewInspection`, etc.
6. Migrate asset filename templates (`MASCI_${id}.pdf` → `${branding.company_name_slug}_${id}.pdf`).
7. Re-run contamination scan target → ZERO disallowed customer-visible hits.
8. Full visual walkthrough across login + 8 portals with Customer #2 preview.
9. MASCI parity re-run.
10. Updated certification.
