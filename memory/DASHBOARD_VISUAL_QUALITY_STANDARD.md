# DASHBOARD_VISUAL_QUALITY_STANDARD.md

_Pass 6 · Dashboard / stats strip contract · 2026-02-01._

## Purpose

A dashboard must feel **calm, readable, operational, confident**.
Not cluttered. Not stretched. Not empty.

## Stats strips (the bad-Pass-5 pattern was wrong)

❌ **Wrong (Pass-5)**: 5 separate `<Card>` components in a `sm:grid-cols-2` grid:

```jsx
<div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
  {stats.map(s => <Card key={s.label} className="p-4 ...">{s.label}{s.value}</Card>)}
</div>
```

Operator-cited problems with that pattern:
- Each card tall with one number = empty wasted space
- 5 cards in 2-col → row 3 has 1 lonely card
- No visual cohesion · no shared frame

✅ **Right (Pass-6)**: Single `<Card>` containing internal grid with dividers:

```jsx
<Card className="p-5 mb-5 border-2 border-slate-200">
  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5
                  gap-x-6 gap-y-5 sm:divide-x sm:divide-slate-200">
    {stats.map((s, i) => (
      <div key={s.label} className={`flex flex-col ${i > 0 ? 'sm:pl-6' : ''}`}>
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
          {s.label}
        </div>
        <div className={`font-display text-3xl font-black mt-1.5 leading-none
                        ${s.highlight ? 'text-amber-700' : 'text-slate-900'}`}>
          {s.value}
        </div>
        {s.highlight ? (
          <div className="mt-1 text-[10px] font-mono uppercase tracking-wider text-amber-700">
            Variance flagged
          </div>
        ) : null}
      </div>
    ))}
  </div>
</Card>
```

## Rules

- **One Card frame** holds the entire metric strip.
- **Internal grid** with `sm:divide-x sm:divide-slate-200` provides
  vertical dividers between metrics (classic ops-dashboard pattern).
- **Each metric** is a `<div className="flex flex-col">` with:
  - tiny uppercase label
  - large number (`text-3xl font-black` minimum)
  - optional subline for context ("Variance flagged", "vs last week", etc.)
- **Highlight state** uses color (`text-amber-700` for attention,
  `text-emerald-700` for positive), NOT a different card border.
  Color carries the signal; the frame stays unified.
- **Responsive density**:
  - phone: 2-col (always pair metrics)
  - tablet+ (sm): 3-col
  - desktop (lg): full N-col

## Card grids on tile-based dashboards (Hub pages)

When the page is a **tile dashboard** (e.g. PM Hub, HR Hub, Safety Hub,
PO Hub), each tile is a navigable destination — different doctrine:

```jsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
  {tiles.map(t => (
    <Card className="p-5 border-2 border-slate-200 hover:border-{accent}-500
                    cursor-pointer transition-colors">
      <Icon className="w-8 h-8 text-{accent}-700" />
      <div className="mt-3 font-display text-base font-black">{t.title}</div>
      <div className="text-sm text-slate-600">{t.subtitle}</div>
      {t.count != null ? <div className="mt-2 text-2xl font-black">{t.count}</div> : null}
    </Card>
  ))}
</div>
```

Tiles get individual `<Card>` because they ARE navigation targets,
not metric values. Stats inside a tile are sub-information.

## Empty / loading / error states

- **Empty**: Card with centered icon + plain-English message + optional CTA. NOT a blank table.
- **Loading**: Card with `<Loader2 className="animate-spin" />` only · no skeleton flicker if the load is < 1 s.
- **Error**: Red-accent card with error message + retry button.

```jsx
<Card className="p-10 text-center text-slate-500">
  <Clock className="w-8 h-8 mx-auto text-slate-400 mb-2" />
  No supervisor-reported hours yet for this window.
</Card>
```

## Anti-patterns

- ❌ Stats as N separate Cards (creates the operator's "lonely card" symptom)
- ❌ Numbers without context labels
- ❌ Dashboards padded with empty cards or placeholder content
- ❌ Tiles without an Icon (creates a visual flat wall of text)
- ❌ Hover states that don't change cursor (breaks discoverability)

---

_End of DASHBOARD_VISUAL_QUALITY_STANDARD.md._
