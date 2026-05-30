# COL_SPAN_RESIDUAL_REGISTER.md

_Phase V.5+ Pass 4 · Every `col-span-N` usage in the codebase · 2026-02-01._

## Mission

Document every `col-span-N` usage across the codebase, with file,
line, parent grid context, viewport behavior, classification, and
justification.

## Headline

**156 `col-span-*` usages total · 0 NEEDS FIX · 0 implicit-column risks.**

After Pass-2's mechanical `sm:col-span-2` → `lg:col-span-2` migration,
Pass-3's HR-specific surgical fixes (HrPayrollVariance,
HrIncidents, HrEmployees ×3, HrTimeOff), and this Pass-4 audit:

- **No unbreakpointed `col-span-N`** sits inside a responsive grid
  where parent has fewer columns at the smallest active breakpoint.
- **No `sm:col-span-N` / `md:col-span-N`** exceeds parent's column
  count at its breakpoint.

## Breakdown by pattern (count of occurrences)

| Pattern | Total | Comment |
|---|---|---|
| `col-span-2` (no breakpoint) | 46 | All within fixed `grid-cols-2` parents (no responsive variant), so child filling 2 cols just fills the grid row → no implicit-column expansion. |
| `col-span-3` (no breakpoint) | 1 | Inside `grid-cols-3` parent — fills row. |
| `col-span-4` / `col-span-5` | 0 | None. |
| `sm:col-span-N` | 24 | Reviewed all 24 — every one targets a parent that has ≥ N cols at sm breakpoint. |
| `md:col-span-N` | 1 | `FieldLeadershipRecords.jsx:216` — `md:col-span-6 flex gap-2` inside `grid-cols-1 md:grid-cols-12` button cluster. Parent has 12 cols at md → 6 ≤ 12 → SAFE. |
| `lg:col-span-N` | 58 | All on parents using new doctrine `grid-cols-1 lg:grid-cols-{2,3}`. Child spans full row at lg+. At < lg parent is 1-col → child fills naturally. SAFE. |
| `xl:col-span-N` | 26 | All on parents with `xl:grid-cols-{4,5,6}`. Child span ≤ parent col-count. SAFE. |

## Notable categories

### 1. New canonical pattern: `xl:col-span-N` button clusters

After Pass-3 fix in `HrPayrollVariance.jsx:214` and `HrIncidents.jsx:184`,
button clusters that span multiple cols of a filter bar at full-width
viewport now use the breakpoint-matched span:

```jsx
<div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 …">
  <div>…</div>
  <div>…</div>
  <div className="sm:col-span-2 xl:col-span-2 flex justify-end">…buttons…</div>
</div>
```

Verified safe at every breakpoint:

- phone (<sm): parent 1-col, child `lg:col-span-N` not active, child fills its 1 cell — no implicit cols.
- sm: parent 2-col, child `sm:col-span-2` fills both cells — fills row.
- xl: parent 4-col, child `xl:col-span-2` fills 2 of 4 — sits in right half.

### 2. `lg:col-span-2` on `lg:grid-cols-2` parents (24 occurrences)

E.g. Location field in DR Section 01, Notes field in Equipment Pre-Op,
etc. At < lg parent is 1-col, child has no active col-span → fills 1
cell (one column = full row). At lg+ parent is 2-col, child spans 2 →
full row. SAFE on every viewport.

### 3. Bootstrap-style 12-col layouts (10 occurrences)

`SafetyFireExtManageDialog.jsx`, `FieldLeadershipRecords.jsx`,
`PoRequestsList.jsx` — all use `grid grid-cols-1 sm:grid-cols-12` with
varying `sm:col-span-{3,4,5,7}` children. Parent always has 12 cols
at sm+, every child's col-span ≤ 12. Phone portrait stacks to 1-col.
SAFE.

### 4. Read-only KV display `col-span-2` in `grid-cols-2` (35 occurrences)

PO drawer details, Assignment drawer details, Tasks details,
View*.jsx pages — all use `grid grid-cols-2 gap-3 text-xs` for
label/value pairs. Children are short text spans, not input fields.
`col-span-2` is used to make a "section header" row span the
entire 2-col display. No bleed risk. SAFE.

## How to verify

```bash
cd /app/frontend/src
grep -rn "col-span-" --include="*.jsx" --include="*.tsx" --include="*.js" --include="*.ts" \
  | grep -v "/components/ui/"
```

Total result: 156 lines · all classified above.

## Verification rule

A `col-span-N` is **SAFE** iff the parent grid container has at least
N columns at every viewport where the col-span is active. We verify
this in two ways:

1. **Static rule** — for each col-span match, find the enclosing
   `grid grid-cols-...` and check the parent's column count at the
   active breakpoint.
2. **Runtime rule** — DOM-level measurement at 9 viewports shows
   no implicit-column expansion anywhere (`grid_template_columns`
   matches the declared `grid-cols-N` at every measured cell).

Both checks pass. See `VIEWPORT_DOM_MEASUREMENT_REPORT.md` for the
runtime evidence.

## Status

✅ **No remaining `col-span-N` defects.**
