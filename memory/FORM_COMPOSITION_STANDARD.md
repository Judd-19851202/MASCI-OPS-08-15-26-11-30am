# FORM_COMPOSITION_STANDARD.md

_Pass 6 · Form composition contract · 2026-02-01._

## Purpose

A form must read as a workflow, not as a stack of inputs. Every form
Card has: **header → sections → footer with primary action**.

## Required structure

```jsx
<Card className="p-5 mb-5 border-2 border-{accent}-200 ...">
  {/* 1 · Header */}
  <div className="mb-4">
    <h2 className="font-display text-lg font-black">{title}</h2>
    <p className="mt-1 text-sm text-slate-600">{subtitle}</p>
  </div>

  {/* 2 · Form sections — each section is a logical group */}
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
    {/* …inputs… */}
  </div>

  {/* (optional 2b · narrow textarea / multi-line input) */}
  <div className="mt-4">
    <Label>{labelForTextarea}</Label>
    <Textarea rows={6} className="w-full" />
  </div>

  {/* 3 · Footer with helper text + actions */}
  <div className="mt-4 pt-4 border-t border-{accent}-200
                  flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
    <p className="text-xs text-slate-500 max-w-2xl">{helperHint}</p>
    <div className="flex gap-2 sm:ml-auto shrink-0">
      <Button variant="ghost" className="h-10">Cancel</Button>
      <Button className="h-10 px-6 bg-{accent}-700">Submit</Button>
    </div>
  </div>
</Card>
```

## Rules

### Header
- Single `h2` with `font-display text-lg font-black`.
- Optional subtitle below: `text-sm text-slate-600`.
- Header in its own `<div className="mb-4">`.

### Sections
- Form rows use `grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4`.
- iPad portrait stacks to 1-col (operator visual standard).
- iPad landscape + desktop get 2-col with 32 px gap.

### Inputs
- Label always above input.
- Every cell wrapper: `min-w-0`.
- Every `<Input>` className includes `w-full` (unless compact-meaning,
  see "Compact inputs").

### Compact inputs (Pass-6 doctrine)
A "compact input" holds short data: counts, percents, thresholds,
durations, codes. These should NOT span a full half-cell because
the empty space reads as unfinished. Constrain:

```jsx
<Input className="... w-full sm:max-w-[200px]" />
```

Example: HR Payroll Variance Threshold (minutes) — single 2-digit
number, gets `sm:max-w-[200px]` so the cell doesn't feel empty.

### Multi-line content
- Textarea always has its own `<Label>` immediately above (don't rely
  on the surrounding section header).
- `<Textarea>` className: `w-full font-mono text-xs border-2 border-slate-300` for code/CSV content.

### Action footer
- ALWAYS separated by `border-t` (16 px+ breathing room above).
- Primary action rightmost · secondary to its left · destructive
  variant="ghost" or `text-red-700`.
- Primary: `h-10 px-6 bg-{accent}-700 text-white`.
- Helper hint text (if any) lives LEFT, with `max-w-2xl` so it
  doesn't push actions off-screen on tablet.

## Anti-patterns (forbidden)

- ❌ Primary action button placed inline with inputs as a grid cell
- ❌ Multiple primary actions side-by-side (violates clear hierarchy)
- ❌ Cancel / Clear placed RIGHT of Submit (Submit must be rightmost)
- ❌ Textarea without an explicit `<Label>` above
- ❌ Compact-meaning input at full half-width without `max-w-`
- ❌ Action row without `border-t` separator (looks like floating buttons)

## Section grouping

When a form has > 6 inputs, split into multiple section Cards rather
than one giant grid. Each section gets its own header:

```jsx
<SectionCard title="Project Information">…</SectionCard>
<SectionCard title="Crew & Hours">…</SectionCard>
<SectionCard title="Photos & Notes">…</SectionCard>
```

The final SectionCard or a separate "Submission" Card holds the
primary action.

---

_End of FORM_COMPOSITION_STANDARD.md._
