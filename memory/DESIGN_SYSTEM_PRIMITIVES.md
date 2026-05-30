> **STATUS: ABANDONED / UNAUTHORIZED DIRECTION (2026-02-01)**
> This document was produced during a redesign pivot that the operator explicitly rejected.
> Do NOT implement any "design system primitive" from this file.
> Retained only for audit history. The stabilization mission is: fix real layout defects only.


# DESIGN_SYSTEM_PRIMITIVES.md

_Pass 7 · Shared design primitives spec · 2026-02-01._

## Mission

Establish the canonical set of design primitives so every page is
composed from the same vocabulary. Pages differ at the **composition**
level, not the **primitive** level.

## Primitive inventory

| Primitive | File | Status | Purpose |
|---|---|---|---|
| `SectionCard` | `/components/SectionCard.jsx` | ✅ Shipped | Card wrapper with title + subtitle + body + optional footer |
| `ActionFooter` | `/components/SectionCard.jsx` | ✅ Shipped | Right-aligned action row with optional left meta chip, border-top separated |
| `FilterBar` | `/components/FilterBar.jsx` | ✅ Shipped | 1-col mobile / 2-col tablet+ filter grid |
| `FormGrid` | `/components/FormGrid.jsx` | ✅ Shipped | 1-col mobile / 2-col lg form grid with 32 px gap |
| `MetricStrip` | _TODO Pass-8_ | 📐 Stub spec | Single-Card horizontal stat strip with internal `sm:divide-x` dividers |
| `FormSection` | _TODO Pass-8_ | 📐 Stub spec | Numbered form-section card (step header + body + Continue button) |
| `DrawerLayout` | _TODO Pass-8_ | 📐 Stub spec | Right-side drawer shell with header + scrollable body + sticky footer actions |
| `ModalLayout` | _TODO Pass-8_ | 📐 Stub spec | Centered modal shell with header + body + footer · max-w responsive |

## Stub specs (to be implemented in Pass-8 alongside family rollout)

### `MetricStrip`

```jsx
<MetricStrip
  metrics={[
    { label: "FLEET ONLINE", value: "23/28", color: "emerald" },
    { label: "PRE-OP FAILED", value: "2", color: "red", subline: "needs shop attention" },
    { label: "AWAITING DISPATCH", value: "5", color: "amber" },
    { label: "OUT OF SERVICE", value: "3", color: "slate" },
  ]}
/>
```

Renders as: single `<Card>` containing `grid grid-cols-2 sm:grid-cols-{N} gap-x-6 gap-y-5 sm:divide-x sm:divide-slate-200`. Each metric: tiny uppercase label · `text-3xl font-black` value · optional colored subline.

### `FormSection`

```jsx
<FormSection
  step={3}
  totalSteps={6}
  title="Weather & Site Conditions"
  subtitle="Record observed conditions at the time of crew start."
  accent="blue"
  onBack={...}
  onContinue={...}
  metaLabel="SAVED LOCALLY · just now"
>
  <FormGrid>…inputs…</FormGrid>
</FormSection>
```

Renders as: SectionCard with explicit "SECTION N OF M" header chip, large title, subtitle, body, footer with Back + Continue · Section (n+1) primary action.

### `DrawerLayout`

```jsx
<DrawerLayout
  open={open}
  onClose={onClose}
  title="PO-2451 · Hilti Concrete Supply"
  subtitle="$2,840.00 · PROJ 25-103 · 2026-05-29"
  flag={<Badge>OVER THRESHOLD</Badge>}
  width="lg"
  footer={
    <ActionFooter
      align="end"
      actions={[
        <Button variant="outline" className="border-red-300 text-red-700">Reject</Button>,
        <Button className="bg-emerald-700 text-white">Approve</Button>,
      ]}
    />
  }
>
  …drawer body…
</DrawerLayout>
```

Right-side drawer · header sticky · scrollable body · sticky footer. Width tokens: `sm` (400 px) · `md` (520 px) · `lg` (640 px) · `xl` (760 px).

### `ModalLayout`

```jsx
<ModalLayout
  open={open}
  onClose={onClose}
  title="Add Employee"
  size="md"
  footer={<ActionFooter align="end" actions={[<Button variant="ghost">Cancel</Button>, <Button>Save</Button>]} />}
>
  <FormGrid>…</FormGrid>
</ModalLayout>
```

Centered modal · backdrop blur · responsive `max-w-{sm|md|lg|xl}`. Mobile auto-fullscreen.

## Color accent tokens

Used consistently across primitives. Each accent has a paired
`border-N-200` / `bg-N-50/30` / `text-N-700` / `bg-N-700 hover:bg-N-800`.

| Accent | Use |
|---|---|
| **blue** | Family A · Field forms · Daily Reports · Safety Meetings |
| **purple** | Family B · Approval consoles · HR / Payroll · PO |
| **emerald** | Family C · Operational status · Equipment / Fleet / Dispatch / Shop |
| **slate** | Family D · Configuration consoles · Admin / Settings / Users |
| **amber** | Alert state · Over-threshold · Awaiting dispatch |
| **red** | Failure state · Pre-op failed · Reject action · Critical |

## Anti-patterns (forbidden)

- ❌ Inline Tailwind grid strings for form rows / filter bars (use `FormGrid` / `FilterBar`)
- ❌ Per-page custom Card paddings / borders (use `SectionCard`)
- ❌ Inline `<Dialog>` constructions for forms (use `ModalLayout`)
- ❌ Inline drawer constructions (use `DrawerLayout`)
- ❌ Stats as N separate Cards (use `MetricStrip`)
- ❌ Action buttons placed inside the input grid (always in `ActionFooter`)

---

_End of DESIGN_SYSTEM_PRIMITIVES.md._
