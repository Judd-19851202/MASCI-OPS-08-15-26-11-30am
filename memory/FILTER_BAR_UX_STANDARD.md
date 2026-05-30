# FILTER_BAR_UX_STANDARD.md

_Pass 6 · Filter bar visual quality contract · 2026-02-01._

## Purpose

A filter bar must read as a deliberate ops control surface, not as
"random fields in a box."

## Required structure

```jsx
<Card className="p-5 mb-5 border-2 border-{accent}-200 bg-{accent}-50/30">
  {/* 1 · Input grid */}
  <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
    <div className="min-w-0">
      <Label className="font-mono text-[10px] uppercase tracking-[0.2em] ...">FIELD NAME</Label>
      <Input className="... w-full" />
    </div>
    {/* …more cells… */}
  </div>

  {/* 2 · Action footer */}
  <div className="mt-5 pt-4 border-t border-{accent}-200
                  flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
    {/* 2a · Context chip (left) */}
    <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-slate-500">
      WINDOW · <span className="text-slate-700 font-bold">{start} → {end}</span>
    </div>

    {/* 2b · Actions (right) */}
    <div className="flex gap-2 sm:ml-auto">
      <Button variant="outline" className="h-10">Export CSV</Button>
      <Button className="h-10 px-6 bg-{accent}-700">Apply Filters</Button>
    </div>
  </div>
</Card>
```

## Rules

### Inputs
- Always `grid grid-cols-1 sm:grid-cols-2` (1-col on phone, 2-col tablet+).
- Never `xl:grid-cols-{4,5}` — page `max-w-7xl` constraint makes 3+ col
  cells unreadable (see VISUAL_LAYOUT_QUALITY_CORRECTION_REPORT.md).
- `gap-x-6 gap-y-4` (24 px horizontal, 16 px vertical).
- Every cell wrapper: `min-w-0` (forces `minmax(0, 1fr)`).
- Every `<Input>` className includes `w-full`.

### Labels
- `font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold`.
- Always above input, never inline.

### Action footer
- `mt-5 pt-4 border-t` separates from input grid (16 px breathing room).
- Actions RIGHT (`flex gap-2 sm:ml-auto`).
- Primary action rightmost · secondary actions to its left.
- Primary action: `h-10 px-6 bg-{accent}-700 text-white`.
- Secondary action: `h-10 variant="outline"`.

### Context chip (optional)
- Lives in footer LEFT.
- `font-mono text-[11px] uppercase tracking-[0.2em] text-slate-500`.
- Holds active window / applied filter count / batch status.

### Stacking behavior
- Phone portrait: footer stacks vertically (`flex-col sm:flex-row`).
- Tablet+: footer is horizontal (meta left, actions right).

## Anti-patterns (forbidden)

- ❌ Action buttons inline as an Nth grid cell (creates orphan-looking half-width button)
- ❌ Date range as raw `<div>` floating below the input grid (operator-cited orphan symptom)
- ❌ Actions only labeled by icon (icon-only Export CSV button looks like noise)
- ❌ Single-digit / counter inputs at full half-width (use `sm:max-w-[200px]`)
- ❌ More than 2-col on tablet · more than 4-col on desktop wide

## Color-accent palette

| Accent | Border / bg | Use case |
|---|---|---|
| purple | `border-purple-200 bg-purple-50/30` | HR / payroll surfaces |
| slate | `border-slate-200 bg-white` | Default / neutral |
| emerald | `border-emerald-300 bg-emerald-50/30` | Success / completion |
| amber | `border-amber-300 bg-amber-50/30` | Variance / attention |
| red | `border-red-300 bg-red-50/30` | Failure / blocked |

---

_End of FILTER_BAR_UX_STANDARD.md._
