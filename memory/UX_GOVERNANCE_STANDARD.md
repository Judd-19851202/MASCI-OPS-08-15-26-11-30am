# UX Governance Standard — Phase IV-C

**Iteration:** iter437+ · Phase IV · 2026-02
**Status:** 🟡 STANDARD LOCKED · ENFORCEMENT INCREMENTAL

Platform doctrine: **CALM · INDUSTRIAL · OPERATIONAL · TRUSTWORTHY · FAST.**

---

## Core principles (in priority order)

1. **One interaction philosophy.** A button does the same thing visually and behaviorally everywhere it appears. No surprises.
2. **Low cognitive load.** A user should never have to read more than 12 words to know what an element does.
3. **Discoverability beats density.** White space is not wasted space — it's how operators find the action they need under field conditions.
4. **Mobile-safe by default.** Every interactive element is ≥ 44×44 px touch target. Every form works on iPad without a keyboard.
5. **No motion as decoration.** Motion only conveys state (loading, transition between two real states). No hover wobbles, no scroll-triggered fades.

---

## Component baseline (uses existing shadcn + lucide-react · no new dependencies)

### Buttons

| Variant | When | Tailwind |
|---|---|---|
| Primary | Submit, confirm, "Open …" | `bg-slate-900 text-white hover:bg-slate-800 px-4 py-2 rounded-md text-sm font-medium` |
| Secondary | Cancel, dismiss, "Back" | `bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 px-4 py-2 rounded-md text-sm font-medium` |
| Destructive | Delete, revoke, hard cleanup | `bg-red-600 text-white hover:bg-red-700 px-4 py-2 rounded-md text-sm font-medium` |
| Ghost | Toolbar, in-card actions | `text-slate-600 hover:bg-slate-100 px-3 py-1.5 rounded-md text-sm` |

**Forbidden:** indigo/violet gradients, drop shadows, 3D bevels, full-width buttons unless mobile-only.

**Test-id contract:** Every button has `data-testid="<scope>-<action>-btn"` (e.g., `data-testid="time-off-approve-btn"`).

### Spacing scale

ONLY these spacing values. Picking one not on this list = doctrine violation.

```
gap-1   = 4px    · between icon + label
gap-2   = 8px    · within a control row
gap-3   = 12px   · between related fields
space-y-4 = 16px · between unrelated fields
space-y-6 = 24px · between sections
space-y-8 = 32px · between page chunks (header / main / footer)
```

### Forms

- Labels above inputs, never beside, never inside (Material-style "floating labels" forbidden).
- Required fields marked with a slate-700 asterisk; "(required)" word never appears.
- Errors render in a single `<p>` below the field in `text-xs text-red-600`. No icons in error text.
- Submit buttons disabled until validation passes — never validate on submit.
- Time/date inputs use `<Input type="date">` / `<Input type="time">` — never custom calendars on mobile.

### Cards

- White background · 1px slate-200 border · 6px radius · no drop shadow.
- Header: tiny eyebrow (uppercase mono · slate-600 · 10px · letter-spacing 0.18em), then H2 below.
- Body padding `p-4` desktop / `p-3` mobile.
- Loading state: lucide `<Loader2 className="w-3 h-3 animate-spin text-slate-400" />` top-right corner.

### Tables

- Used for **data with > 4 columns of equal weight**. For 2-3 columns or stacks of records, use stacked cards instead.
- Header row: `bg-slate-50 text-xs uppercase tracking-wider text-slate-600 font-bold`
- Row hover: `hover:bg-slate-50` (no transition).
- Row click: makes the entire row a link (the cursor + an `<a>` wrapper), never a per-cell "View" button.
- Mobile: tables auto-collapse to stacked cards below `md:`.

### Modals (dialogs)

- Always use `<Dialog>` from `components/ui/dialog.jsx`.
- Max width `max-w-lg` for forms · `max-w-2xl` for content viewing · `max-w-4xl` for the lightbox.
- Always include a close button in the header AND a cancel button in the footer.
- ESC key always closes.
- Background scroll always locked while open.

### Section headers

```jsx
<header className="bg-white border border-slate-200 rounded-md p-5 mb-4 flex items-start gap-3">
  <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-800 text-white shrink-0">
    <Icon className="w-6 h-6" />
  </div>
  <div className="flex-1">
    <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
      {DOMAIN}
    </span>
    <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
      {Title}
    </h1>
    <p className="text-sm text-slate-600 mt-1">{description}</p>
  </div>
</header>
```

This is the **only** acceptable page-header pattern. The `/admin/database` panel from Phase Sigma-III is the reference implementation.

### Empty states

```
<icon · w-12 h-12 · text-slate-300>
<H3 · text-base · font-medium · text-slate-700>
<p · text-sm · text-slate-500 · max-w-md · mt-2>
<primary action button · mt-4 (optional)>
```

No illustrations, no cute mascot, no "Oops!" wording. Empty states are silent confirmations that there's nothing to do here yet.

### Status badges

| State | Style |
|---|---|
| ok / green | `inline-flex items-center px-2 py-0.5 rounded text-xs font-mono uppercase bg-emerald-50 text-emerald-700 border border-emerald-200` |
| warning / amber | `... bg-amber-50 text-amber-700 border-amber-200` |
| critical / red | `... bg-red-50 text-red-700 border-red-200` |
| neutral / info | `... bg-slate-100 text-slate-700 border-slate-200` |

Uppercase + monospace + tiny — looks operational, not consumer.

### Severity colors (project-wide canonical palette)

```css
--sev-ok      : emerald-600 #059669
--sev-warning : amber-600   #d97706
--sev-critical: red-600     #dc2626
--sev-info    : slate-600   #475569
--sev-accent  : indigo-700  #4338ca   /* primary action only */
```

**No** sky / teal / cyan / fuchsia / pink / lime in operational surfaces. These exist only in promo assets where they belong.

### Action placement

- Page-level primary action: top-right of the page header. NEVER bottom-left, NEVER floating.
- Card-level actions: top-right of the card.
- Row-level actions: rightmost column. Never the leftmost.
- Destructive actions: always require a confirmation dialog with explicit text ("Type DELETE to confirm" for irreversible deletes).

---

## Filters / search

- Search input always at top-left of the data area, full-width on mobile, max-w-md on desktop.
- Filter chips render to the right of search · clear-all button at the far right.
- "No results" empty state uses the canonical empty-state pattern above.

---

## Mobile-safe rules (enforced at PR review)

- 44×44 px minimum touch target on every interactive element.
- No `position: fixed` floating action button — operators hate them in the field.
- Tables collapse to stacked cards below `md:`.
- Modals become full-screen below `sm:`.
- Photo lightbox: pinch-zoom enabled, swipe-to-dismiss enabled.
- No hover-only interactions (every hover state has a tap equivalent).

---

## What this standard refuses to allow

- ❌ Drop shadows on cards (flat doctrine)
- ❌ Gradient backgrounds (industrial doctrine)
- ❌ Animated charts
- ❌ Carousel/auto-rotating heroes
- ❌ Loading spinners larger than 16 px (calm doctrine)
- ❌ Toast notifications that linger > 8 s
- ❌ Emoji icons in operational text (lucide-react only)
- ❌ Multiple typography systems on one page

---

## Verdict

🟡 **STANDARD LOCKED.** Existing pages will be brought into conformance incrementally — every PR that touches a page MUST leave that page closer to (never further from) this standard.

Reference implementations already conforming: `/admin/database`, `/admin/system-health`, the new login-page capacity banner, the storage observability card.
