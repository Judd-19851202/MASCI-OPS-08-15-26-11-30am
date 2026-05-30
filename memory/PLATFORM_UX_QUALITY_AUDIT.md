# PLATFORM_UX_QUALITY_AUDIT.md

_Pass 6 · Platform-wide UX quality reset · 2026-02-01._

## Mandate

Operator: "MASCI Ops must feel like a professional operations
platform, not an internal developer tool. Certify a page only when
it looks intentionally designed for the device."

## Why prior passes were insufficient

Pass 2-5 fixed every technical bleed and every cramped cell width.
But the operator's IMG_0021 / IMG_0022 still showed UX failures
that DOM-level rules can't detect:

1. **Orphan action buttons.** Apply/CSV in HR Time Verification sat
   in a 5th half-cell that visually looked like a "leftover" slot.
   Run Variance / Clear in HR Payroll Variance floated to the right
   of a single Threshold input, detached from the workflow.
2. **Empty wasteful cells.** 5 stat Cards stacked in 2-col gave
   row 1 = 2 cards, row 2 = 2 cards, row 3 = 1 lonely card.
   Each card was tall with one number — empty space dominated.
3. **Weak field hierarchy.** No visual grouping of "inputs" vs
   "actions" vs "context." Everything sat in one undifferentiated grid.
4. **No context chips.** The active window "2026-05-25 → 2026-05-31"
   floated as raw text below the inputs without label or visual weight.
5. **Inconsistent input proportions.** Threshold (single 2-digit
   number) got full half-width like a long-text input.

## Approach

- Introduce shared primitives for proper composition (not just spacing).
- Patch the 2 operator-cited surfaces (HR Time Verification +
  HR Payroll Variance) as the proof-of-pattern.
- Document the patterns so they can be applied across remaining surfaces
  without re-inventing per-page.

## Shared primitives introduced (Pass 6)

| Primitive | File | Purpose |
|---|---|---|
| `SectionCard` | `/components/SectionCard.jsx` | Card wrapper with title + subtitle + footer slot |
| `ActionFooter` | `/components/SectionCard.jsx` | Dedicated right-aligned action row with optional left meta chip, separated from form body by border-top |
| (unchanged) `FormGrid` | `/components/FormGrid.jsx` | 1-col mobile / 2-col `lg:` form grid with 32 px gap |
| (unchanged) `FilterBar` | `/components/FilterBar.jsx` | 1-col mobile / 2-col `sm:` filter grid |

Future page authoring uses these primitives. Existing pages may
inline the same pattern without importing the primitive (preserves
diff size; doctrine is the contract, not the import).

## Pass-6 surfaces patched

| Surface | Issue | Fix |
|---|---|---|
| **HR Time Verification** filter card | Apply/CSV sat in 5th cell · date range floated as orphan · stats in 5 wasteful tall cards | Inputs in clean 2-col grid · dedicated action footer (border-top) with window-context chip LEFT + Export CSV + Apply Filters RIGHT · stats consolidated into single horizontal strip with sm:dividers |
| **HR Payroll Variance** form card | Run Variance + Clear floated to right of Threshold input (detached from workflow) · Threshold input full-half-width despite being a 2-digit number · no label on textarea | Inputs in clean 2-col · Threshold constrained to `sm:max-w-[200px]` · explicit "EXACT CSV PAYLOAD" label on textarea · action footer at card bottom with helper text LEFT + Clear + Run Variance RIGHT |

See `UX_QUALITY_FIX_CERTIFICATION.md` for before/after screenshots.

## Doctrine to apply to remaining surfaces

```
1.  Every form/filter Card has a clear visual hierarchy:
       header (title + subtitle)
       body (input grid)
       footer (border-top + action row right-aligned + optional context chip left)

2.  Action buttons NEVER sit inline with inputs. They live in the
    Card's footer, separated by border-top, right-aligned, with the
    primary action rightmost.

3.  Stat/metric strips are SINGLE cards with internal flex/grid,
    not N separate Card components. Use `sm:divide-x sm:divide-slate-200`
    + `sm:pl-6` on children for vertical dividers between metrics.

4.  Compact-meaning inputs (counts, percents, thresholds) get a
    `max-w-[180-220px]` so they don't dominate their grid cell.

5.  Context chips (active window, date range, applied-filter count)
    use `font-mono text-[11px] uppercase tracking-[0.2em] text-slate-500`
    and live in the action footer's meta slot.
```

## Surfaces NOT yet patched in this pass

(Need same pattern applied · prioritized by user-facing impact)

- HR Time Off list filter + Add dialog
- HR Incidents filter
- HR Employees filter + Add Employee dialog
- HR Field Leadership filter
- HR Driver Qualification filter
- PO Requests filter + Drawer action row
- Daily Report submit/save action row
- Equipment Pre-Op submit row
- Safety Meeting / Incident / QA-QC submit rows
- Dispatch admin filter + drawer
- Admin Users / Admin Dispatch / Admin Promo Assets filters

The mechanical pattern in `HrTimeVerification.jsx` lines 122-165
and `HrPayrollVariance.jsx` lines 195-242 is the template.

## Stop condition honored

- ✅ No backup scheduler / Approval/Rejection / Pilot / RFI / Schedule / P6 / new feature work
- ✅ Preview-only · production untouched
- ✅ Operator review pending before claiming "certified"

---

_End of PLATFORM_UX_QUALITY_AUDIT.md._
