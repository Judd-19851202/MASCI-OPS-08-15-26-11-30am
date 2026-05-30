# UX_QUALITY_FIX_CERTIFICATION.md

_Pass 6 · UX quality fix certification · 2026-02-01._

> **Operator standard now binding**: "The standard is not 'DOM says
> no overlap.' The standard is 'the operator says this looks elite.'"

## Status

🟡 **PREVIEW SHIPPED · OPERATOR REVIEW PENDING.**

This pass intentionally does NOT self-certify. The new operator
standard ("looks elite") cannot be auto-verified — only the operator
can issue the final pass/fail.

## Surfaces patched (Pass 6)

### 1 · HR Time Verification (`/hr/time-verification`)

**Before** (Pass-5 state · operator-rejected per IMG_0019):
- Apply button + CSV in 5th half-cell of input grid
- Date range "2026-05-25 → 2026-05-31" floated as orphan
- 5 stat Cards in 2-col grid → 2+2+1 lonely card pattern, each tall and empty

**After** (Pass 6):
- 4 inputs in clean 2×2 grid (Week Ending + Employee + Project# + Supervisor)
- Dedicated action footer with border-t separator:
  - LEFT: `WINDOW · 2026-05-24 → 2026-05-30` context chip
  - RIGHT: Export CSV (secondary) + Apply Filters (primary)
- Single consolidated stats Card with 5 metrics inline + `sm:divide-x` dividers + 3xl numbers

**Screenshot**: see chat-rendered live capture at 1366×1024 (operator's viewport).

### 2 · HR Payroll Variance (`/hr/payroll-variance`)

**Before** (Pass-5 state · operator-rejected per IMG_0020):
- Run Variance + Clear floated to right of Threshold input (detached)
- Threshold input full half-width despite holding a 2-digit number
- Textarea without explicit label
- "Accepted columns..." helper text orphan below textarea

**After** (Pass 6):
- 2-col input row: Week Ending + Threshold (constrained `sm:max-w-[200px]`)
- Explicit "EXACT CSV PAYLOAD" label above textarea
- Action footer at card bottom with border-t separator:
  - LEFT: "Accepted columns..." helper text (constrained `max-w-2xl`)
  - RIGHT: Clear (ghost) + Run Variance (primary purple)

**Screenshot**: see chat-rendered live capture.

## Shared primitives shipped

- `frontend/src/components/SectionCard.jsx` — `<SectionCard title subtitle accent footer>` + `<ActionFooter meta actions>`
- (Pre-existing) `FormGrid` and `FilterBar` retain their Pass-5 doctrine

## How to extend to other surfaces

The Pass-6 pattern is template-replicable. To patch any
form/filter Card:

1. Pull action buttons OUT of the input grid.
2. Wrap form body in `<Card className="p-5 mb-5 border-2 border-{accent}-200 bg-{accent}-50/30">`.
3. Add `<div className="mt-5 pt-4 border-t border-{accent}-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">` for the footer.
4. Move context chip (window / count / status) into the footer's left slot.
5. Move actions into the footer's right slot with `sm:ml-auto`.
6. For stats: collapse N separate Cards into 1 Card with internal `sm:divide-x sm:divide-slate-200` grid.
7. Compact-meaning inputs (counters, thresholds) get `sm:max-w-[200px]`.

## Deliberately NOT patched in this pass

Per operator's "stop after correction" directive:

- HR Time Off / HR Incidents / HR Employees / HR Field Leadership
- PO Requests filter + drawer
- All form-submit action rows across DR / Equipment / Safety / QA-QC / Incident
- Dispatch admin / Admin Users / Admin Dispatch / Admin Promo Assets

These follow the same template. Roll-out scheduled for the next
authorized pass.

## Doctrine documents shipped

- `PLATFORM_UX_QUALITY_AUDIT.md` — why Pass-5 was insufficient + Pass-6 approach
- `FILTER_BAR_UX_STANDARD.md` — binding filter bar contract
- `FORM_COMPOSITION_STANDARD.md` — binding form composition contract
- `DASHBOARD_VISUAL_QUALITY_STANDARD.md` — stats strip + tile dashboard contract
- `DEVICE_CLASS_VISUAL_REVIEW_REPORT.md` — per-device visual review
- `UX_QUALITY_FIX_CERTIFICATION.md` (this file)

## Verdict

🟡 **AWAITING OPERATOR VISUAL VERDICT.**

The new standard ("elite-looking") cannot be self-certified. The
Pass-6 patches resolve every operator-cited issue from IMG_0019-22
(Apply button placement, stats strip empty space, Run Variance
detachment, hierarchy weakness, workflow grouping). The platform-wide
doctrine is documented so the pattern can be applied to remaining
surfaces by the next authorized pass.

Operator review required to mark Pass 6 closed.

---

## Stop conditions honored

- ✅ No backup scheduler hardening
- ✅ No Approval/Rejection
- ✅ No Pilot
- ✅ No RFI · No Schedule · No P6
- ✅ No PM Exposure Tile work
- ✅ No new feature work
- ✅ Preview-only · production untouched
- ✅ No "DOM says OK" certification claim

---

_End of UX_QUALITY_FIX_CERTIFICATION.md._
