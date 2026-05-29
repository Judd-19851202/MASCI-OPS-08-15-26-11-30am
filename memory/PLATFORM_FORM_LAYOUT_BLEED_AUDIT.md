# Platform Form Layout Bleed Audit

_Phase V.5 · 2026-05-29 19:23 UTC._

> Operator-reported P0 live iPad field bleed across multiple form
> surfaces. This document captures the investigation that preceded the
> shared-component fix.

## 1 · Reproduction

| Step | Result |
|---|---|
| Navigate to `/daily/new` on iPad portrait (768–820 px viewport) | Project Name / Project Number borders visually touch in 2-col layout |
| Navigate to `/meetings/new` on iPad portrait | Date / Time fields collide at center seam |
| Navigate to `/equipment/new` on iPad portrait | Project / Operator pair bleeds together |
| Navigate to `/qaqc/concrete/new` on iPad portrait | Inspector / Work Area pair bleeds together |
| Inspect rendered DOM | All four forms use the same Tailwind grid: `grid grid-cols-1 sm:grid-cols-2 gap-{3,4}` |

Baseline screenshot: `/tmp/gate/before_dr_ipad_portrait.png` (iPad
portrait 820 × 1180). Project Name input ends at x=391 px; Project
Number begins at x=426 px — only **35 px of gap** for two adjacent
1-px borders + 12 px input padding on each side. WebKit chrome
consumes the rest. Bleed visible.

## 2 · Shared pattern inventory

`grep -rn "grid grid-cols-1 sm:grid-cols-2 gap-" frontend/src/`
returned **84 occurrences across 44 files**, distributed:

| Pattern | Count | Risk |
|---|---|---|
| `gap-1` | 2 | acceptable (decorative, not form rows) |
| `gap-2` | 9 | borderline — kept (specialty rows) |
| `gap-3` | **37** | **PRIMARY BLEED SOURCE** |
| `gap-4` | **32** | secondary bleed source — same root cause |
| `gap-5` | 1 | acceptable |
| `gap-6` | 1 | already safe |

**Root cause**: Tailwind `sm:` breakpoint = 640 px. iPad portrait
viewport widths (iPad mini 768 px, iPad 9th-gen 810 px, iPad Air
820 px, iPad Pro 11" 834 px) ALL hit `sm:` and snap to 2-col with
only 12–16 px of column gap. Adjacent inputs effectively touch
because input padding (12 px) + border (1 px) + WebKit chrome (~2 px)
on each side consumes most of the 12–16 px gap.

## 3 · Local "Row" helper duplication

Three forms re-implemented the same broken pattern as a local helper
component:

| File | Line | Implementation |
|---|---|---|
| `pages/NewQaqcInspection.jsx` | 607 | `<div className="grid grid-cols-1 sm:grid-cols-2 gap-3">{children}</div>` |
| `pages/NewSafetyEquipmentIssuance.jsx` | 645 | identical |
| `pages/NewSafetyEquipmentTraining.jsx` | 492 | identical |

This duplication explained why a per-page fix would not have scaled —
the broken pattern existed at multiple altitude levels.

## 4 · Affected surfaces (operator-confirmed live bleed)

- Daily Reports — Report Information section (Project Name / Project
  Number · Location / GPS button row · Prepared By / Superintendent
  picker pair)
- Equipment / Operator forms — Project & Operator section, Date / Time row
- Safety Meetings — Job / Date / Time / Conducted By section
- QA/QC concrete + rebar inspections — Inspector / Work Area row
- HrDailyReports, HrSafetyRecords, ViewIncident, ViewMeeting, ViewDailyReport, ViewQaqcInspection — all read-screen views inherited the same bleed
- Admin panels: AdminDigestConfig, AutoEmailRoutingPanel, EquipmentMasterPanel — admin forms inherited the same bleed

## 5 · Why a shared-component fix was the right call

A surface-by-surface patch would have:
- left the three `Row` helpers as time-bombs
- required touching every form individually with no enforcement
  against future regressions
- missed the 20+ view-screen surfaces that inherited the bleed
- doubled the diff surface for testing

The chosen fix:
- created a canonical `FormGrid` component (single source of truth)
- migrated all 69 offending Tailwind strings in one mechanical batch
  to the new safe pattern
- updated the three local `Row` helpers to inherit the same safe
  pattern (handled automatically by the mechanical replacement)

## 6 · Audit complete · proceed to fix

The fix is documented in `PLATFORM_FORM_GRID_FIX_CERTIFICATION.md`.
Validation evidence is in `IPAD_LAYOUT_VALIDATION_REPORT.md`. The
binding doctrine is `FORM_SPACING_DOCTRINE.md`.

---

_End of PLATFORM_FORM_LAYOUT_BLEED_AUDIT.md._
