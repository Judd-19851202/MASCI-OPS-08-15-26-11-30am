# Safety Mobile Calmness Report

*Phase IV-BETA.5A · iter437 · 2026-02-27*
*Status: 🟢 IMPLEMENTED · regression-verified across desktop / iPad / mobile*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Tune Safety Hub + Incident surfaces for **mobile and iPad** ergonomics.
Per `SAFETY_MOBILE_OPERATIONAL_REVIEW.md §I`, Safety is the only portal
where operators routinely use mobile **at the moment of escalation**
(open trench, injury photo from the field). Mobile calmness is an
**operational reliability** property, not a UX preference.

## II. Viewport coverage (🟢 VERIFIED)

| Viewport | Width × Height | Pixel density | DOM walk result |
|---|---|---|---|
| desktop | 1920 × 1080 | 1× | Safety Hub: 133 elements walked, 2 hue families, loudness 66.78 |
| ipad | 1024 × 1366 | 2× | Safety Hub: 133 elements walked, 2 hue families, loudness 66.78 |
| mobile | 390 × 844 | 3× | Safety Hub: 106 elements walked, 2 hue families, loudness 68.04 |

Captured via `/app/backend/tests/pw_suite/test_visual_doctrine_baseline.py`
with the new `safety` parametrise key. Re-running the baseline now
includes Safety alongside Admin / PM / HR cells.

## III. Mobile-specific changes (🟢 VERIFIED)

1. **Hub tile grid** — already `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
   per iter318. Preserved verbatim.
2. **Tile stripe** — 4 px left border scales unchanged across viewports.
3. **CTA button** — single neutral slate-800 across all tiles. No
   per-tile colour explosion on a narrow viewport.
4. **Coaching sublines** — trimmed to ≤14 words, sentence case. At
   390 px viewport this means sublines no longer overflow.
5. **Sidebar V2** — `hidden lg:block` (mirrors HR). Does NOT render on
   mobile / iPad (since iPad portrait can be `<lg`). The mobile layout
   reverts to the legacy single-column Hub when the V2 flag is on —
   intentional, since mobile users navigate by tile, not sidebar.

## IV. Incidents page mobile contract (🟢 VERIFIED · `SafetyIncidents.jsx`)

| Element | Mobile behaviour |
|---|---|
| Page header icon block | 48 px square, slate-800 (calm at all viewports) |
| Page header stripe | 4 px red-700 left border (visible at all viewports as the page-level urgency anchor) |
| Severity pill (`SEV_PILL`) | Size + weight **preserved** at all viewports per doctrine §IV |
| Status pill (`STATUS_PILL`) | Now slate (calm), reduces panic-glance density at 390 px |
| Filter row | Single column at sm viewport, multi-col at md+ (no change) |
| Table | Horizontal scroll preserved (matches `SafetyCorrectiveActions` pattern) |
| "Open" row link | Now slate-800 (was cyan-700) — calmer when scanning a long list |

## V. iPad-specific (🟢)

iPad is the typical PM trailer device. Behaviour:

- Sidebar V2 mounts when `?safetySidebarV2=1` is present AND viewport
  ≥ lg breakpoint (1024 px landscape). iPad portrait (768 px) falls
  back to legacy layout.
- Hub tile grid renders 3 columns at lg+ for landscape, 2 columns at
  md+ (portrait).
- Severity pill, OSHA pill, severe-tier banner all render unchanged.

## VI. Preserved real-time interruption vectors (🟢)

Per directive, mobile real-time interruption is **NOT** modified:

- ✅ Push email for severe-incident is the only real-time signal
- ✅ Severe-incident email subject `🚨 SEVERE INCIDENT · …` preserved
- ✅ Email is readable in 375 px iOS Mail preview (per audit §II)
- ✅ No new in-app push, badge animation, or toast added
- ✅ File upload paths (camera capture) untouched

## VII. Doctrine reaffirmed (🟢)

- ✅ Severity pill size + weight preserved at all viewports
- ✅ Severe-tier banner stays full-width on mobile
- ✅ File-upload inputs stay native `<input type="file">`
- ✅ No in-app push / badge / toast added during incident review
- ✅ Mobile users see the calmer Hub WITHOUT the false-urgency colour
  explosion of the old palette
- ✅ Preview only · NO production deploy
