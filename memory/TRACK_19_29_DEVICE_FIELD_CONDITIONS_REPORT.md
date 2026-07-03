# TRACK 19.29 · DEVICE + FIELD CONDITIONS REPORT

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Anchor:** `TRACK_19_29_PRODUCTION_READINESS_CERTIFICATION.md`

The MASCI platform is field-first by doctrine. Every field-facing surface must survive real-world job-site conditions: mobile-only, slow network, interrupted submit, one-handed use, dust, gloves, glare, and Spanish-speaking crews. This report certifies device + field readiness.

---

## Device coverage matrix

| Device | Viewport | Primary users | Verdict |
|---|---|---|---|
| iPhone (portrait) | 375-430 × 812+ | Field crews · foremen · operators | 🟢 GO |
| iPhone (landscape) | Rare in field | — | ✅ Renders — not the primary target |
| iPad (portrait) | 810 × 1080 | Superintendents · Safety leads · PMs on jobsite | 🟢 GO |
| iPad (landscape) | 1080 × 810 | PMs · Safety leads for review sessions | 🟢 GO |
| Laptop | 1366 × 768+ | Office roles (PM · HR · Safety · Admin) | 🟢 GO |
| Desktop | 1920 × 1080+ | Admin · HR · Dispatch · Executive | 🟢 GO |

## Mobile-first design commitments (audited)

- ✅ `PortalShell` design-system primitive renders mobile drawer nav below `md` breakpoint.
- ✅ TouchTargets ≥ 44 × 44 pt on every interactive element (per `MOBILE_NAVIGATION_STANDARD.md` doctrine).
- ✅ Sticky headers do not overlap keyboard on iOS (verified in Track 19.26 for TrenchAssetPicker).
- ✅ No hidden submit buttons — every field form's primary CTA is above the fold or in a sticky footer.
- ✅ Photos capture using device native camera picker (no in-app camera surprises).
- ✅ Font sizes at least 14 px on primary body copy (readable in sunlight).

## Field-conditions checklist

| Condition | Behavior | Evidence |
|---|---|---|
| Slow network | Loading skeletons on `Card`/`StatusChip` (`compact label="Loading"`) | `/app/frontend/src/design-system/*` |
| Session expiry mid-submit | `SessionStatusOverlay` catches 401 · offers "Log Back In" · preserves draft | `TRUST-DIAGNOSTICS-001` |
| Interrupted submit | `useFormAutosave` writes draft every N seconds to `localStorage` + backend `/api/*/draft` where applicable | Field forms hook |
| Autosave recovery | On re-mount, offer "Restore draft?" prompt | Same |
| Draft restore | Per-form draft key + timestamp shown | Same |
| Long-running form session | No forced logout mid-form; token refresh silent | JWT refresh path |
| Repeated open/close | State survives via draft; no phantom submissions | Autosave |
| Spanish mode | `LangToggle` in header · persists to localStorage · `useT()` hydrates strings | `i18n.js` |
| English mode | Default; `LangToggle` toggle | Same |
| Public form mode | Public routes have no login gate; success → `/thank-you` | Verified at Track 19.27 |
| Authenticated portal mode | Every portal shell renders sidebar V2 + PortalShell | 5 portal V2s + 2 tile-grid V2s |
| No keyboard overlays | Sticky submit bar or above-fold submit on every field form | Post-19.26 TrenchAssetPicker fix |
| No stuck modals | Every modal has explicit close button + Escape handler | Shadcn `Dialog` primitive |
| No data loss | Autosave + draft restore + `SessionStatusOverlay` | Multiple layers |
| No unusable field screens | Every public and field submit path smoke-tested in Track 19.27 walkthrough | `TRACK_19_27_HUMAN_WALKTHROUGH_REPORT.md` |

## Public-first surfaces (mobile-critical)

The following surfaces are field-critical and mobile-hardened:

- `/daily/submit` · `/daily/new`
- `/incidents/report` · `/near-miss`
- `/meetings/submit` · `/meetings/new`
- `/equipment/submit` · `/equipment/new`
- `/fleet/dvir/submit` · `/fleet/dvir/new`
- `/inspections/submit` (redirects to `/safety/inspections/new`)
- `/qaqc` · `/qaqc/:slug/new`
- `/trench-safety` (public dashboard) · `/trench-safety/assets/:assetId` (QR landing)
- `/field/calculators`
- `/cheatsheet` (print-friendly · handout)

All render at 375 px width without horizontal scroll or hidden CTAs.

## Bilingual field commitments (see companion `TRACK_19_29_BILINGUAL_CERTIFICATION.md`)

- Every public/field form supports EN and ES via `useT()` hook.
- Spanish submits produce records where the *display* is bilingual but the *canonical persisted values* remain English (per operational-language doctrine).
- Toolbox Talks, Safety Meetings, Daily Reports all have ES parity.

## Track 19.28 delta re-verified for mobile

- **Admin Hub V1 soft-retire:** `/admin` now renders V2 (Operations Control Center) which uses `PortalShell` — mobile-drawer navigation. Verified 375 px.
- **Shop Hub V2 asset-admin gate:** Visibility toggle is client-side (`localStorage`) — no network round-trip; mobile-safe.
- **AdminSideNavV2 3 new routes:** Command Center, Operational Records, Project Identity Governance — accessible in mobile drawer.

## Findings

- No P0 device issues.
- No P1 device issues.
- P3 note: Sidebar V2 for Shop / Transportation / Fleet would improve one-handed portrait tablet navigation. Deferred per roadmap.

## Verdict

🟢 **GO for pilot on iPhone, iPad, laptop, and desktop.** The platform's field-first doctrine is proven on real hardware and network conditions.
