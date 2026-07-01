# Track 19.10 · FormShell + HelpDrawer Primitives · Design Spec

## FormShell (`frontend/src/components/FormShell.jsx`)

### Purpose
Provide every operational form with the same visual scaffolding so different forms feel like one platform. **OPT-IN**: existing forms are not auto-refactored; each form decides when to consume this primitive during its dedicated redesign track.

### Contract
```jsx
<FormShell
  kicker="New Report"           // small uppercase overline text
  title="Equipment Pre-Op"      // large form title
  subtitle="OSHA walk-around…"  // optional secondary line
  draftSlot={<DraftBadge/>}     // consumer passes their own indicator
  progressSlot={<ProgressPill/>}// consumer passes their own progress cue
  headerRightSlot={<HelpButton/>}
  stickyFooter={<SubmitButton/>}
  containerTestId="form-shell-equipment"
>
  <Section number="01">…</Section>
</FormShell>
```

### Design decisions
* **Stateless** — every piece of state lives on the parent page. Adopting this primitive cannot break inspection engines, fail-cascade, audit spine, or any protected behaviour.
* **Bilingual by construction** — every operator-facing string routes through `useT()` (the sr-only accessibility label and header hierarchy).
* **Progressive** — subtitle, progressSlot, draftSlot, headerRightSlot, stickyFooter are all optional. A form can adopt piecewise.
* **Sticky header + footer** — consistent 5:30-AM-foreman anchor: title stays visible while scrolling, submit stays visible while working.

### Consumers (as of 19.10 Slice 1)
None (opt-in). Component sits ready for 19.11 / 19.12 / 19.13.

---

## HelpDrawer (`frontend/src/components/HelpDrawer.jsx`)

### Purpose
Single, context-aware, lazy-mount help surface. Replaces the three overlapping helper systems (`LifecycleGuide`, `HelpTipBlock`, section-header prose) identified in Track 19.08 audit. **Proof-of-concept only in Slice 1** — existing helpers remain live until operators validate the pattern.

### Contract
```jsx
<HelpDrawer
  open={helpOpen}
  onOpenChange={setHelpOpen}
  triggerLabel={t("Open help")}     // button text
  title={t("Equipment Pre-Op · Guidance")}
  testIdPrefix="equipment-help-drawer"
  sections={[
    { title: t("Why this matters"), body: t("...") },
    ...
  ]}
/>
```

### Design decisions
* **Trigger is inline** — a small pill-shaped button; not a floating action button. On mobile the drawer slides in from the bottom; on desktop it slides in from the right.
* **Accessibility** — `role="dialog"`, `aria-modal="true"`, `aria-controls` on trigger, `aria-label` on drawer, close button visible.
* **No content authorship in the primitive** — the drawer only renders sections passed by the consumer. This lets each form's coaching content evolve independently.
* **Bilingual by construction** — every string (button label, section header, empty state) routes through `useT()`.

### Consumers (as of 19.10 Slice 1)
* Equipment Pre-Op — proof-of-concept wiring. Three seed sections.

---

## Coexistence with existing help systems

The existing coaching stack (`LifecycleGuide` "5 COACHING TIPS AVAILABLE" strip, `HelpTipBlock` per-section boxes, section-header prose) is **fully preserved** in Slice 1. This is deliberate — the drawer must prove itself in field usage before the older layers can be retired. The Track 19.08 audit documented that this consolidation would be a P1 opportunity; Slice 1 stages the primitive without pulling the trigger on consolidation.

## Retirement plan (informational — NOT executed in 19.10)

Once operators confirm the HelpDrawer meets their needs:
1. Copy the content from `LifecycleGuide` / `HelpTipBlock` into structured `sections[]` arrays consumed by HelpDrawer.
2. Delete `LifecycleGuide` and `HelpTipBlock` component usages from forms one at a time (per redesign track).
3. Preserve the underlying content collections (`guidance/`) — they may still power PDF training packets.
