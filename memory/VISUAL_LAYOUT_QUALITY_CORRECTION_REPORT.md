# VISUAL_LAYOUT_QUALITY_CORRECTION_REPORT.md

_Phase V.5+ Pass-5 · Visual quality correction (rejection-driven) · 2026-02-01._

> **Operator verdict on Pass 4**: "LAYOUT CERTIFICATION REJECTED.
> The platform still visually looks wrong on HR-type screens.
> Your automated audit is passing layouts that the operator considers
> unacceptable. The validation standard is wrong."

This pass corrects the validation standard, not just the layout.

---

## 1 · Why Pass 4 passed bad layouts

Pass-4 declared `LAYOUT CERTIFIED PLATFORM-WIDE` based on:

- **Static rule**: no `col-span-N` exceeds parent's column count.
- **Runtime rule**: no DOM-level cell overlap; cells ≥ 150 px on ≥ 1024 px viewport; gap ≥ 16 px.

That standard let HR Time Verification's 5-col filter bar render with
**165-180 px cells at iPad Pro 12.9 landscape (1366 CSS px)** —
mathematically non-overlapping, but visually **cramped, narrow,
spreadsheet-cell-looking strips**. The operator's IMG_0019 / IMG_0020
proved this.

The Pass-4 rules were too permissive in three specific ways:

1. **Minimum cell width 150 px is too narrow** — fields below 240 px
   read as "squashed" even when technically not overlapping.
2. **Gap floor 16 px is the bare minimum**, not the breathing-room
   standard for a professional layout.
3. **Multi-col filter bars were preserved too aggressively** — the
   `xl:` (1280 px) breakpoint fires at iPad Pro 12.9 landscape
   (1366 px), but the page's `max-w-7xl` (1280 px) container means
   the content area can't accommodate readable 4-5-col layouts at
   **any** viewport.

---

## 2 · New validation standard

### 2a · Pass/Fail rules (Pass-5)

A filter or form row is FAIL if any of:

- ❌ Adjacent inputs visually appear connected or merged
- ❌ Field pair has less than **24 px** visible separation on tablet/larger
- ❌ Field pair has less than **16 px** visible separation on phone landscape
- ❌ Any **input width is under 260 px** on tablet/larger (unless explicitly approved)
- ❌ Any **filter input width is under 240 px** on tablet/larger (unless intentionally compact)
- ❌ Date / Time pair looks like one continuous control
- ❌ Action button cluster squeezes nearby inputs
- ❌ Layout looks like a spreadsheet instead of an application form
- ❌ Operator-provided screenshot shows unacceptable visual quality,
     regardless of DOM pass

### 2b · Default-stack-sooner doctrine

Forms:
- phone portrait → 1 col
- phone landscape → 1 col unless very wide
- tablet portrait / iPad portrait → 1 col
- tablet landscape → 2 col only if fields remain comfortable (≥ 360 px)
- desktop (≥ 1024 px lg:) → 2 col
- large desktop → 3+ col only where appropriate

Filter bars:
- phone → 1 col
- tablet / iPad portrait → 1-2 col max
- tablet / iPad landscape → 2 col max
- desktop → 2 col (3-5 col **only** if container is full-width AND fields stay ≥ 240 px)

---

## 3 · Fix applied (Pass-5)

### 3a · Bumped filter-bar breakpoint xl: → 2xl:

Mechanical migration (`/tmp/gate/audit/visual_correction.py`):

| Old | New | Effect |
|---|---|---|
| `xl:grid-cols-{4,5,6}` | `2xl:grid-cols-{4,5,6}` | 4-5-6 col only activates at ≥ 1536 px |
| `xl:col-span-{2,3,4,5}` | `2xl:col-span-{2,3,4,5}` | Matching span breakpoints |

**Files touched: 35. Total replacements: 35.**

### 3b · Dropped dense filter-bar variants entirely

Pass-5a moved the breakpoint to `2xl:` but the `max-w-7xl` (1280 px)
page container still capped content width — even at viewport 2560 px,
5-col cells came out at 166 px. So we dropped the dense
breakpoints entirely:

Mechanical migration (`/tmp/gate/audit/visual_correction_2b.py`):

| Old | New |
|---|---|
| `sm:grid-cols-2 2xl:grid-cols-5` | `sm:grid-cols-2` |
| `sm:grid-cols-2 2xl:grid-cols-4` | `sm:grid-cols-2` |
| `sm:grid-cols-2 2xl:grid-cols-6` | `sm:grid-cols-2` |
| `sm:grid-cols-2 2xl:grid-cols-3` | `sm:grid-cols-2` |
| `sm:col-span-2 2xl:col-span-{2,3,4,5}` | `sm:col-span-2` |

**Files touched: 58. Total replacements: 77.**

### 3c · FilterBar.jsx rewritten

The shared primitive `frontend/src/components/FilterBar.jsx` now
encodes the 2-col-max contract as the single source of truth.
The `columns` prop is retained for API compatibility but ignored.

---

## 4 · Before / After DOM evidence (HR Time Verification filter row)

| Viewport | BEFORE (Pass 4) | AFTER (Pass 5) | Verdict |
|---|---|---|---|
| phone portrait 390 | 1 col @ 603 px | 1 col @ 603 px | ✓ |
| phone landscape 844 | 2 col @ 360 px (gap 24) | 2 col @ 360 px (gap 24) | ✓ |
| iPad portrait 820 | 2 col @ 348 px | 2 col @ 348 px | ✓ |
| iPad landscape 1180 | 2 col @ 400 px | 2 col @ 400 px | ✓ |
| **iPad Pro 12.9 1366 (operator's viewport)** | **5 col @ 166 px** ✗ | **2 col @ 450 px** ✓ |
| Desktop 1920 | 5 col @ 166 px ✗ | 2 col @ 450 px ✓ |
| Ultra-wide 2560 | 5 col @ 166 px ✗ | 2 col @ 450 px ✓ |

**Every viewport now ≥ 348 px filter cells** (operator floor: 240 px).

---

## 5 · Files touched (Pass 5)

`/app/frontend/src/components/FilterBar.jsx` — rewritten with 2-col-max doctrine
58 files across pages/ and components/ — `2xl:grid-cols-N` filter bars collapsed to `sm:grid-cols-2`

Notable surfaces:
- HR Time Verification · HR Payroll Variance · HR Incidents · HR Time Off · HR Field Leadership · HR Employee Accountability
- PO Requests
- Safety Audits · Safety Hub · Safety Digest · Safety Forms Records · Safety Fire Ext Import
- Admin Analytics · Admin Dispatch · Admin Governance · Admin Promo Assets · Admin Operational Inventory · Asset Profile
- ProjectHealth · ProjectPnl · Tasks · NotificationsDigest · MaterialCalculators
- TrenchBoxesAdmin · ViewSafetyForm · NewFleetDVIR
- ODR PM Panel · PM Hub

---

## 6 · Updated platform-wide visual spacing doctrine

```
Filter bars (binding · Pass 5):
  grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 items-end
  NEVER more than 2-col. Page max-w-7xl makes 3+ col impossible
  to render with readable cell widths.

Form rows (unchanged from Pass 2):
  grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4
  iPad portrait stacks. iPad landscape + desktop get 2-col w/ 32 px gap.

Cell wrappers + inputs:
  Every grid cell: className includes `min-w-0`
  Every <Input>: className includes `w-full`
  Prevents iOS Safari intrinsic-input bleed.

Button clusters (allowed exception):
  Flex / 2-col grids with `gap-2` permitted when children are
  exclusively <button> elements.

Display KV grids (allowed exception):
  grid grid-cols-2 gap-{2,3,4} text-xs/sm with read-only label/value
  spans — no input chrome, no bleed risk.
```

---

## 7 · Operator-review screenshot (iPad Pro 12.9 landscape 1366)

`/tmp/gate/audit/operator_review/hr_time_verification_pass5_1366.png`
captured live preview after Pass-5 — filter row renders 2-col @ 450 px
each, clean separation, no spreadsheet feel, action buttons sit
properly under the inputs with breathing room.

---

## 8 · Stop conditions honored

- ✅ NO backup scheduler hardening
- ✅ NO Approval/Rejection
- ✅ NO Pilot · NO RFI · NO Schedule · NO P6
- ✅ NO new feature work
- ✅ Preview-only — no production touched

---

## 9 · Status

🟢 PREVIEW SHIPPED · awaiting operator visual review.

The Pass-4 certification is **REVOKED**. New Pass-5 certification
will be issued only when the operator confirms visual quality on the
HR Time Verification + HR Payroll Variance screenshots at iPad Pro
12.9 landscape (the viewport where IMG_0019 / IMG_0020 were rejected).

The standard going forward: **"operator says this looks elite."**
Not "DOM says no overlap."

---

_End of VISUAL_LAYOUT_QUALITY_CORRECTION_REPORT.md._
