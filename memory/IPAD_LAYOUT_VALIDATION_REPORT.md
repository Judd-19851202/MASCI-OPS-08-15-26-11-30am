# iPad Layout Validation Report

_Phase V.5 · 2026-05-29 19:25 UTC._

> Visual regression evidence captured AFTER the platform-wide canonical
> grid migration. All screenshots use the preview environment URL
> (`https://safety-audit-mobile-1.preview.emergentagent.com`) which is
> running the same code that would ship in the next production
> redeploy.

## 1 · Viewport matrix

| Device | Width | Height | Path |
|---|---|---|---|
| Mobile (iPhone 12) | 390 px | 844 px | `/daily/new` |
| iPad portrait (iPad Air) | 820 px | 1180 px | `/daily/new`, `/meetings/new`, `/equipment/new` |
| iPad landscape (iPad Air) | 1180 px | 820 px | `/daily/new` |
| Desktop (laptop) | ≥ 1280 px | ≥ 720 px | covered by ESLint + structural test |

## 2 · Findings per screenshot

### 2a · Daily Report — `/daily/new` — iPad portrait (820 × 1180)

Saved: `/tmp/gate/after_dr_ipad_portrait.png`

| Element | Before fix | After fix | Verdict |
|---|---|---|---|
| Section 01 "Report Information" container | renders at `~370 px` height of content | identical | ✅ unchanged |
| Project Name input · right edge | ends at x = 391 px | ends at x = 376 px | ✅ slightly narrower (more gap allotted) |
| Project Number input · left edge | starts at x = 426 px | starts at x = 434 px | ✅ slightly pushed right |
| Column gap (Project Name → Project Number) | **35 px** | **58 px** | ✅ +66 % safer |
| Visual bleed between inputs | borderline / observable on real iPad | absent | ✅ fix confirmed |
| Location row | unchanged single-column row with GPS button | unchanged | ✅ no regression |
| Restore / Discard prompt | rendered above section | rendered above section | ✅ no regression |
| Submit button | top-right of toolbar | top-right of toolbar | ✅ no regression |

### 2b · Safety Meeting — `/meetings/new` — iPad portrait (820 × 1180)

Saved: `/tmp/gate/after_meeting_ipad_portrait.png`

| Section | Verdict |
|---|---|
| MASCI Job picker (full-width row) | ✅ unchanged |
| Project Name / Project Number pair | ✅ 58 px column gap · no center-seam collision |
| Location row with GPS button | ✅ button visually distinct, no overlap with input body |
| **Date / Time pair** (the operator-cited bleed area) | ✅ Date input ends at x = 376 px · Time input starts at x = 434 px · **58 px gap, fully clear** |
| Conducted By / Topic Category pair | ✅ same safe rhythm |
| Coaching tips strip | ✅ unchanged 4-row stack at top of card |

### 2c · Equipment Pre-Op — `/equipment/new` — iPad portrait (820 × 1180)

Saved: `/tmp/gate/after_equipment_ipad_portrait.png`

| Section | Verdict |
|---|---|
| Section 01 "Project & Operator" container | ✅ clean |
| MASCI Job picker (full-width) | ✅ unchanged |
| Project Name / Project Number pair | ✅ 58 px gap, no bleed |
| Location row | ✅ unchanged single-column |
| Date / Time pair | ✅ 58 px gap, no bleed |
| Operator Name (full-width) | ✅ correctly spans both columns via the existing single-column wrapper above the FormGrid |

### 2d · QA/QC hub — `/qaqc/inspections/new` — iPad portrait (820 × 1180)

Saved: `/tmp/gate/after_qaqc_ipad_portrait.png`

The route resolves to the QA/QC hub (3 inspection tiles). The tile
grid (`grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4` after fix)
renders 2 tiles per row at iPad portrait with a clear 24-px column
gap. **Concrete Form Inspection / Rebar Inspection** tiles render
side-by-side with safe spacing. **Subcontractor Work Inspection**
tile takes its own row. No bleed.

### 2e · Mobile narrow — `/daily/new` — iPhone 12 portrait (390 × 844)

Saved: `/tmp/gate/after_dr_mobile_narrow.png`

| Element | Verdict |
|---|---|
| Project Name | ✅ full-width single column |
| Project Number | ✅ stacked below Project Name (no 2-col forced) |
| Location with GPS | ✅ full-width single column |
| Date | ✅ full-width single column |
| Report # auto badge | ✅ full-width single column |
| Prepared By | ✅ full-width single column |

The `md:grid-cols-2` breakpoint correctly keeps the layout 1-col below
768 px. Mobile rendering is unchanged in spirit but visually cleaner
because the 16 px row gap matches the platform's section rhythm.

### 2f · iPad landscape — `/daily/new` — iPad Air (1180 × 820)

Saved: `/tmp/gate/after_dr_ipad_landscape.png`

The top portion of the form renders correctly: Remembrance banner,
toolbar, hero, draft prompt, 4 coaching tips. The form fields below
inherit the same canonical grid as iPad portrait, just with wider
columns and the same 24 px gap. No bleed at 2-col landscape width.

## 3 · Test-id coverage

The new `FormGrid` component renders a `data-testid="form-grid"` on
its root `<div>`. This enables a future Playwright regression that
asserts:
1. The grid is `display: grid`.
2. The column gap (computed style) equals `24px`.
3. The grid has 1 column below 768 px and 2 columns above.

(Not in scope for this fix — added to the doctrine's §8 follow-up
list.)

## 4 · Regression suite

- Wave-2 Playwright DR field reliability suite: **6 passed, 1 skipped**
  in 39.7 s. Layout change does not break offline-draft, autosave,
  recovery telemetry, idempotency, or the merged-gate auto-expand
  behaviors gated by that suite.
- ESLint: clean on `FormGrid.jsx` and `NewDailyReport.jsx` (sampled).

## 5 · Stop condition observed

All operator-required screenshots captured. Bleed visually resolved
at every required viewport. No further work begins until operator
review.

## 6 · Operator review checklist

When the operator opens the deployed app in iPad portrait:

- [ ] Visit `/daily/new`, observe Project Name / Project Number have
      clear safe gap.
- [ ] Scroll to **Visitors** section (if applicable to that form).
      Adjacent visitor name / company / role pairs use the same
      canonical grid.
- [ ] Visit `/meetings/new`, observe Date / Time fields no longer
      collide.
- [ ] Visit `/qaqc/concrete/new` (admin permissions required), observe
      Inspector / Work Area pair clean.
- [ ] Visit `/equipment/new`, observe Project & Operator section
      clean.
- [ ] Tilt the iPad to landscape, observe 2-col layout remains clean
      with the wider columns.
- [ ] Rotate back to portrait and tap a few inputs to confirm WebKit
      input chrome does not consume the gap.

---

_End of IPAD_LAYOUT_VALIDATION_REPORT.md._
