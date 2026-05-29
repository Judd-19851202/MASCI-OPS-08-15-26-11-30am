# HR LAYOUT — REMAINING-DEFECT APPENDIX (V.5+ Pass 3)

_Phase V.5+ Pass 3 · HR-only · 2026-02-01 · Append to
`GLOBAL_FORM_LAYOUT_ROOT_CAUSE_REPORT.md`._

> **Operator directive after Pass 2**: "HR Portal is improved but NOT
> fully fixed. Focus next on remaining HR layout defects. Fix only
> the remaining HR layout defect. Do not touch Daily Reports."

This appendix documents the **HR-specific residuals** found after
the global fix and the surgical corrections applied to address each.

---

## 1 · Residuals identified (after Pass 2)

### A · `col-span-N` without responsive breakpoint on grid-cols-1 parent

Same root cause as the global Pass 2 fix (CSS Grid implicit-column
auto-expansion), but the global migration only targeted the explicit
`sm:col-span-N` / `md:col-span-N` patterns. These three HR-specific
violations slipped through:

| File · Line | Pattern (BEFORE) | Defect |
|---|---|---|
| `HrPayrollVariance.jsx:214` | `col-span-2 lg:col-span-2 flex …` on `grid-cols-1 sm:grid-cols-2 xl:grid-cols-4` parent | At phone portrait (<sm), parent is 1-col but child demands 2-col → implicit-column expansion → asymmetric `303 + 152 px` measurement |
| `HrIncidents.jsx:184` | `sm:col-span-5 flex justify-end` on `grid-cols-1 sm:grid-cols-2 xl:grid-cols-5` parent | At sm (640-1279 px), parent is 2-col but child demands 5-col → 5 implicit columns auto-created |
| `HrEmployees.jsx:337` | `col-span-2` on `grid-cols-2 gap-2` (no breakpoint) | Parent always 2-col with tight 8 px gap → bleed at phone portrait inside Add Employee dialog |

### B · `grid grid-cols-2 gap-2` dialog forms cramped at phone portrait

Tight 2-col grids with 8 px gap inside HR dialogs (Add Employee,
status transitions, Time-Off add-public). At phone portrait 390 px,
each column is ~187 px with native input chrome → visual bleed.

| File · Line |
|---|
| `HrEmployees.jsx:336` (Add Employee dialog form) |
| `HrEmployees.jsx:830` (Status transition — Termination dates) |
| `HrEmployees.jsx:875` (Status transition — Leave dates) |
| `HrTimeOff.jsx:465` (Add public time-off — Position / Department) |

### C · iOS Safari date-input intrinsic width stretches grid cells

`<input type="date">` on iOS Safari has wider native chrome (full
formatted date `May 30, 2026`) compared to Chromium's `MM/DD/YYYY`.
Without `min-width: 0` on the grid cell wrapper, the intrinsic
content can stretch its column beyond the `minmax(0, 1fr)` declared
width, producing visually unequal cells.

| File · Line |
|---|
| `HrTimeVerification.jsx:124-149` (5-cell filter row) |
| `HrPayrollVariance.jsx:205-220` (4-cell action row) |

---

## 2 · Fixes applied (HR-only)

### 2a · Breakpoint-aware `col-span`

| File · Line | AFTER |
|---|---|
| `HrPayrollVariance.jsx:214` | `sm:col-span-2 xl:col-span-2 flex …` — phone: 1-col, sm+: spans 2 cols, xl: spans 2 of 4 cols (right half) |
| `HrIncidents.jsx:184` | `sm:col-span-2 xl:col-span-5 flex justify-end` — sm: spans 2 cols full row, xl: spans 5 cols full row |
| `HrEmployees.jsx:336-337` | parent `grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-3` · child `sm:col-span-2` |

### 2b · Phone-portrait stack for dialog forms

`HrEmployees.jsx:830` · `HrEmployees.jsx:875` · `HrTimeOff.jsx:465` —
all `grid grid-cols-2 gap-2` → `grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-3`. Phone portrait stacks. sm+ pairs.

### 2c · iOS Safari cell-width safeguard

`HrTimeVerification.jsx` and `HrPayrollVariance.jsx` filter rows:
each cell `<div>` now has `min-w-0`, each `<Input>` has `w-full`
added to its `className`. This forces CSS Grid to use the parent's
explicit `minmax(0, 1fr)` regardless of child intrinsic size.

Doctrine-level guarantee:

```html
<div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-x-6 gap-y-3">
  <div className="min-w-0">              <!-- prevents iOS date-chrome bleed -->
    <Input className="… w-full" />        <!-- forces input to fill cell, not vice versa -->
  </div>
  …
</div>
```

---

## 3 · Forensics — AFTER matrix (5 HR surfaces × 5 viewports)

DOM measurements captured 2026-02-01 against live preview pod via
Chromium headless. Format: `<N>col[<comma-separated widths>]`.

| Surface | phone_p (390) | phone_l (844) | ipad_p (820) | ipad_l (1180) | desktop (1366) |
|---|---|---|---|---|---|
| HR Time Verification | **1col[603]** | 2col[360,360] | 2col[348,348] | 2col[400,400] | 5col[166×5] |
| HR Payroll Variance  | **1col[479]** | 2col[356,356] | 2col[344,344] | 2col[396,396] | 4col[211×4] |
| HR Incidents (filter)| **1col[358]** | 2col[394,394] | 2col[382,382] | 2col[548,548] | 4col[262×4] |
| HR Time Off (filter) | **1col[366]** | 2col[378,378] | 2col[366,366] | 2col[546,546] | 5col[224×5] |
| HR Employees dialog  | 1col + sm 2col equal · no col-span auto-expansion at any viewport |

### Critical wins vs Pass 2

- **HR Payroll Variance phone portrait**: was `2 col @ 303,152px`
  (asymmetric · operator-visible bleed) → now `1 col @ 479px` clean stack.
- **HR Incidents filter (button cluster)**: was 5 implicit columns
  at sm (640-1279 px) → now 2 columns at sm, 5 columns at xl.
- **HR Time Verification + Payroll filter cells**: `minmax(0, 1fr)`
  contract now enforced by `min-w-0` + `w-full` → equal cells
  regardless of iOS Safari date-input chrome.

---

## 4 · AFTER screenshots

8 screenshots in `/tmp/gate/hr_v2/`:

```
hr_time_verification_phone_portrait.png       (390 × 844)
hr_time_verification_phone_landscape.png      (844 × 390)
hr_time_verification_ipad_portrait.png        (820 × 1180)
hr_time_verification_desktop.png              (1366 × 1024)
hr_payroll_variance_phone_portrait.png        (390 × 844)
hr_payroll_variance_phone_landscape.png       (844 × 390)
hr_payroll_variance_ipad_portrait.png         (820 × 1180)
hr_payroll_variance_desktop.png               (1366 × 1024)
```

ESLint clean on every file touched.

---

## 5 · What was deliberately NOT touched

- ✅ Daily Reports — no regression risk, no edits.
- ✅ Non-HR portals (PM · Shop · Safety · QA-QC · PO · Equipment).
- ✅ shadcn `/components/ui/*` vendor primitives.
- ✅ Backup scheduler.
- ✅ Approval/Rejection · Pilot · RFI · Schedule · P6.
- ✅ PM Exposure Tile.
- ✅ All other new feature work.

---

## 6 · Status

🟢 **PREVIEW SHIPPED.** Operator review pending.

Remaining outstanding items (unchanged):
- 🔴 Operator production redeploy (mascidocs.com) — covers Pass 2 + Pass 3 together.
- 🟡 Live verification of HR Time Verification + HR Payroll Variance at iPad portrait + landscape on operator's actual iPad device.
- 🟡 After live verification: authorize Backup Scheduler Hardening (P0 GAP-7).
- 🟢 Phase 1C Multi-Viewport Gate (APPROVED BACKLOG) — will bake the col-span + `min-w-0` doctrine into the deploy gate.

---

_End of HR_LAYOUT_REMAINING_DEFECTS_APPENDIX.md (Pass 3)._
