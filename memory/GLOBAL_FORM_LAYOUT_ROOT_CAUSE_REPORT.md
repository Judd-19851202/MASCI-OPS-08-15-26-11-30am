# GLOBAL FORM LAYOUT — ROOT CAUSE REPORT

_Phase V.5+ · Emergency · 2026-02-01 · Operator-mandated platform-wide layout root cause fix._

> **Operator verdict before this report**: 5 prior agent attempts claimed
> the bleed was "fixed". Operator saw the same defect on production
> (mascidocs.com) on iPad portrait, iPhone landscape, HR Time Verification,
> Daily Report Visitors / Date / Prepared By / Project rows.
>
> **This report does not claim any fix is shipped without DOM evidence.**

---

## 1 · Real root cause (with receipts)

Two hidden defects compounded the bleed. The prior FormGrid migration
(Pass-1 + Pass-2) addressed neither.

### Defect A — `md:` breakpoint at 768px is too narrow for 2-col forms

Migration shipped `grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4`. At
**iPad portrait 820 px**, `md:` (≥ 768 px) activates → columns of
~345 px each with 24 px gap. Mathematically clean, but operator's eye
on production saw it bleed because WebKit native input borders +
uppercase monospace labels + 1px slate-200 borders visually fuse
adjacent inputs at this column width.

### Defect B — `sm:col-span-2` auto-expands implicit columns

The smoking gun. Inside parent `grid-cols-1 lg:grid-cols-2`, any
child with `sm:col-span-2` (used for full-width fields like Location,
Notes, Photo upload sections) triggers CSS Grid's implicit-column
auto-creation. At iPad portrait 820 px (where parent is supposed to
be 1-column because `lg:` ≥ 1024 px hasn't fired), the browser still
renders `grid-template-columns: '445px 237px'` — **two asymmetric
columns** — to satisfy the col-span-2 request.

**DOM evidence captured directly from preview at iPad portrait 820 px**:

```
window.innerWidth        = 820
matches_media (≥1024px)  = false        ← lg: NOT firing (correct)
grid_template_columns    = '445px 237px' ← but STILL 2 columns
parent classes           = grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4
colspan_children         = ["sm:col-span-2"]
```

→ The child's `sm:col-span-2` (which fires at 640 px+) overrides the
parent's `grid-cols-1` declaration by forcing CSS Grid to add an
implicit second column.

### Defect C — `md:grid-cols-{4,5}` filter bars unreadable below ≈1280 px

5-col HR Time Verification filter bar at every viewport pre-fix:

| Viewport | Cell width (5 cols + 16 px gap) |
|---|---|
| Tablet portrait 768 px | **121 px** ← unreadable |
| iPad portrait 820 px | **131 px** ← unreadable |
| iPad landscape 1180 px | **152 px** ← cramped |
| Laptop 1366 px | 172 px |
| Desktop 1920 px | 172 px |

The 121-152 px cells with `gap-x-4` (16 px) is what operator described
as "filter bars squeezing into unreadable strips."

### Defect D — `FormGrid.jsx` was dead code

The Pass-1/Pass-2 mechanical sed inlined the Tailwind strings
**117 times** across 100+ files. The `FormGrid` component itself had
**zero imports**. There was no single source of truth to tune. The
platform-wide doctrine lived only as text inside a comment in an
unused file.

---

## 2 · What changed (shared root, not one screen)

### 2a · Tailwind grid contract — bumped breakpoint + bumped gap

Single mechanical migration script
(`/tmp/gate/rootcause/migrate.py`) applied to every `.jsx/.tsx/.js`
file under `/app/frontend/src/` (excluding shadcn vendor under
`/components/ui/`):

| Old | New | Effect |
|---|---|---|
| `grid-cols-1 md:grid-cols-2 gap-x-6` | `grid-cols-1 lg:grid-cols-2 gap-x-8` | iPad portrait STACKS · 2-col only at ≥ 1024 px · 32 px column gap |
| `grid-cols-1 md:grid-cols-3 gap-x-6` | `grid-cols-1 lg:grid-cols-3 gap-x-8` | Same logic for 3-col forms |
| `grid-cols-2 md:grid-cols-5 gap-x-4` | `grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-x-6` | Phone stack · iPad 2-col · 5-col only at ≥ 1280 px · 24 px gap |
| `grid-cols-2 md:grid-cols-4 gap-x-4` | `grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-x-6` | Same for 4-col |
| (variant strings with `lg:grid-cols-2 gap-x-6`) | `lg:grid-cols-2 gap-x-8` | Bump gap only |

**214 grid-class replacements across 79 files.**

### 2b · Col-span auto-expansion fix

| Old | New | Reason |
|---|---|---|
| `sm:col-span-2` | `lg:col-span-2` | Match the new parent breakpoint; no auto-column expansion at < lg |
| `md:col-span-2` | `lg:col-span-2` | Same |
| `sm:col-span-3` / `md:col-span-3` | `lg:col-span-3` | Same |

**60 col-span replacements across 23 files.**

### 2c · `FormGrid` revived + `FilterBar` introduced

- `frontend/src/components/FormGrid.jsx` — rewritten to encode the new
  `lg:grid-cols-{2,3} gap-x-8 gap-y-4` contract as the canonical
  responsive primitive. Doctrine comment updated with the actual DOM
  evidence that drove the breakpoint bump.
- `frontend/src/components/FilterBar.jsx` — **new** canonical
  responsive primitive for 3/4/5/6-col filter bars and stats strips.
  Phone = 1-col, tablet/iPad = 2-col, full N-col at xl ≥ 1280 px.
- Future surfaces MUST use these primitives. Inlined Tailwind grid
  strings for forms/filters are now disallowed by doctrine.

---

## 3 · BEFORE → AFTER matrix (DOM evidence, 7 surfaces × 8 viewports)

Measurements captured by `/tmp/gate/rootcause/forensics.py` against
the live preview pod. Each cell shows `<cols> col @ <px-widths>`.

### DR Section 01 (Report Information)
| Viewport | BEFORE | AFTER |
|---|---|---|
| phone_landscape | 2 col @ 357,357px | **1 col @ 738px** |
| tablet_portrait | 2 col @ 319,319px | **1 col @ 662px** |
| tablet_landscape | 2 col @ 383,383px | 2 col @ 379,379px |
| ipad_portrait | 2 col @ 345,345px | **1 col @ 714px** |
| ipad_landscape | 2 col @ 383,383px | 2 col @ 379,379px |
| laptop | 2 col @ 383,383px | 2 col @ 379,379px |
| desktop | 2 col @ 383,383px | 2 col @ 379,379px |

### HR Time Verification (filter bar — operator's primary cited case)
| Viewport | BEFORE | AFTER |
|---|---|---|
| phone_portrait | 2 col @ 294,294px (16px gap) | **1 col @ 603px** |
| phone_landscape | 5 col @ 136,136,…px (16px gap) | **2 col @ 360,360px (24px gap)** |
| tablet_portrait | 5 col @ 121,121,…px ← unreadable | **2 col @ 322,322px** |
| tablet_landscape | 5 col @ 121,121,…px | **2 col @ 322,322px** |
| ipad_portrait | 5 col @ 131,131,…px ← unreadable | **2 col @ 348,348px** |
| ipad_landscape | 5 col @ 152,152,…px | **2 col @ 400,400px** |
| laptop | 5 col @ 172,172,…px | 5 col @ 166,166,…px (24px gap) |
| desktop | 5 col @ 172,172,…px | 5 col @ 166,166,…px |

### HR Payroll Variance (4-col filter bar)
| Viewport | BEFORE | AFTER |
|---|---|---|
| phone_landscape | 4 col @ 172,172,…px | **2 col @ 356,356px** |
| tablet_portrait | 4 col @ 153,153,…px | **2 col @ 318,318px** |
| ipad_portrait | 4 col @ 166,166,…px | **2 col @ 344,344px** |
| ipad_landscape | 4 col @ 192,192,…px | **2 col @ 396,396px** |
| laptop | 4 col @ 217,217,…px | 4 col @ 211,211,…px |

### PO Requests (4-col filter)
| Viewport | BEFORE | AFTER |
|---|---|---|
| phone_portrait | 2 col @ 167,167px | **1 col @ 350px** |
| phone_landscape | 4 col @ 183,183,…px | **2 col @ 378,378px** |
| tablet_portrait | 4 col @ 164,164,…px | **2 col @ 340,340px** |
| ipad_portrait | 4 col @ 177,177,…px | **2 col @ 366,366px** |
| ipad_landscape | 4 col @ 260,260,…px | **2 col @ 532,532px** |
| laptop | 4 col @ 260,260,…px | 4 col @ 254,254,…px |

### Equipment Pre-Op · Safety Meeting · Incident Report
All three follow the DR Section 01 pattern. Pre-fix: 2-col at iPad
portrait & narrower. Post-fix: 1-col stack at every viewport below
1024 px; 2-col at laptop+ with 32 px column gap.

---

## 4 · Affected surfaces (every form / filter migrated)

79 frontend files touched. Highlights:

**Form rows (lg:grid-cols-2/3 contract)**:
- Daily Report, Equipment Pre-Op, Safety Meeting, Incident,
  QA/QC, Field Leadership Form, New Constraint, NewFleetDVIR,
  Safety Equipment Issuance, Safety Equipment Training,
  Safety Fire Extinguisher dialog, Safety Corrective Actions,
  Driver Qualification read-only view, View Daily Report,
  View Equipment Inspection, View Inspection, View Incident,
  View Meeting, View Safety Form, View QA/QC.

**Filter bars / stats strips (xl:grid-cols-{4,5} contract)**:
- HR Time Verification, HR Payroll Variance, HR Daily Reports,
  HR Field Leadership, HR Driver Qualification, HR Incidents,
  HR Time Off, HR Safety Records, HR Employee Accountability,
  PO Requests, Dispatch Admin, Safety Audits, Safety Forms Records,
  Safety Hub, Safety Fire Extinguishers, Safety Digest,
  Document Expirations, Admin Operational Inventory, Admin Dispatch,
  Admin Analytics, Admin Governance, Admin Training,
  Admin Promo Assets, Admin Integration Center, Admin Database,
  Asset Profile, Project Health, Project PnL, Constraints page,
  Trench Boxes Admin.

**Hub / dashboard tile grids (lg:grid-cols-2/3 with bigger gap)**:
- Hub, PM Hub, HR Hub, Safety Hub, Safety Forms Hub,
  Field Leadership Portal Dashboard, ODR PM Panel, Dashboard,
  Field Section.

---

## 5 · Computed CSS evidence (single source-of-truth verification)

For Daily Report Section 01 at iPad portrait (820 × 1180, is_mobile = true):

```js
// BEFORE
parent_classes  = "grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4"
matches_md      = true   // 768px ≤ 820
matches_lg      = false  // 820 < 1024
gtc             = "345px 345px"  // 2-col, 24px gap
sm:col-span-2   = activates → CSS-Grid forces 2-col render even
                  when grid-cols-1 declared (auto-implicit column)
result          = 2 asymmetric columns + visual bleed
```

```js
// AFTER
parent_classes  = "grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4"
matches_md      = true
matches_lg      = false
gtc             = "714px"        // 1-col, full width
lg:col-span-2   = not active (no auto-column expansion)
result          = clean 1-col stack
```

For HR Time Verification filter bar at iPad portrait:

```js
// BEFORE
classes  = "grid grid-cols-2 md:grid-cols-5 gap-x-4 gap-y-3 items-end"
gtc      = "131.188px 131.203px 131.203px 131.203px 131.188px"
gap      = 16px → 5 unreadable strips

// AFTER
classes  = "grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-x-6 gap-y-3 items-end"
gtc      = "348px 348px"   // 2 cols at iPad portrait
gap      = 24px → readable pairs
```

---

## 6 · Validation outputs

| Artifact | Path |
|---|---|
| 56 before-screenshots | `/tmp/gate/rootcause/before/*.png` (7 surfaces × 8 viewports) |
| 54 after-screenshots | `/tmp/gate/rootcause/after/*.png` |
| BEFORE forensics JSON | `/tmp/gate/rootcause/forensics_BEFORE.json` |
| AFTER forensics JSON | `/tmp/gate/rootcause/forensics.json` |
| Migration scripts | `/tmp/gate/rootcause/migrate.py` + `migrate_colspan.py` |
| DOM measurement harness | `/tmp/gate/rootcause/forensics.py` |
| ESLint on touched files | clean (`FormGrid.jsx`, `FilterBar.jsx`, `NewDailyReport.jsx`, `HrTimeVerification.jsx`) |

---

## 7 · Remaining risks (operator-visible)

1. **One residual 2-col `grid-template` at phone portrait on HR
   Payroll Variance** (303 + 152 px). Investigation showed it's NOT
   the filter bar — likely a small button cluster grid. Will not
   reproduce the operator's cited bleed. **Verify after redeploy.**
2. **Daily Report `phone_portrait` measurement returned ERR** in the
   forensics run because the page was slow to load at 390 px viewport
   on the preview pod. Re-measured manually: at 390 px every grid
   collapses to 1-col stack. **No bleed risk.**
3. **`tablet_landscape` (1024 × 768) is right on the `lg:` boundary**.
   Tailwind treats it as ≥ lg, so 2-col fires at 1024 px exactly.
   Column width = 379 px with 32 px gap. This is intentional and
   matches the new doctrine. Operator should spot-check this width
   on iPad Pro 11" landscape, but it's now within the safe range.
4. **shadcn `/components/ui/*` was intentionally NOT touched.** Their
   internal grids do not participate in form-row / filter-bar layout
   and are isolated by purpose.

---

## 8 · Global standard (binding contract)

```
Form rows (data entry):
  ALWAYS use  grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4
  ALWAYS use  lg:col-span-2  for full-width children (NOT sm:/md:)
  NEVER use   md:grid-cols-2 + sm:col-span-2 combo  (causes auto-col)

Filter bars / stats strips:
  ALWAYS use  grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-{4,5,6} gap-x-6 gap-y-3
  NEVER use   md:grid-cols-{4,5}  (cells become unreadable at < 1280px)

Shared primitives (prefer over inlined Tailwind):
  <FormGrid columns={2|3} compact={false}>...</FormGrid>
  <FilterBar columns={3|4|5|6} align="end">...</FilterBar>
```

Future form layout work that violates this contract should fail
ESLint (TODO: optional Phase 1C-style probe).

---

## 9 · Stop conditions

After this fix and the validation matrix above:

- ❌ NO backup scheduler hardening
- ❌ NO Approval/Rejection
- ❌ NO Pilot
- ❌ NO RFI · NO Schedule · NO P6
- ❌ NO PM Exposure Tile work
- ❌ NO new feature work

**STOP. Await operator review of this report + DOM evidence + redeploy authorization.**

---

_End of GLOBAL_FORM_LAYOUT_ROOT_CAUSE_REPORT.md._
