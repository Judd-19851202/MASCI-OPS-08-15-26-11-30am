# Visual Governance Inheritance
## Phase V.0 · Architecture & Governance · 2026-05-27

> Visual doctrine inheritance contract for the RFI + Schedule
> subsystems. Doctrine-locked.

---

## 1 · Purpose

Every new surface produced for RFI and Schedule Intelligence must be
visually and behaviourally indistinguishable from PM, HR, Safety, and
Admin V2 — **identical spacing, typography, components, escalation
language, mobile behaviour, and chrome**. No "AI slop". No drift.

This document is the inheritance contract. It is referenced by every
implementation phase from V.1 onward.

---

## 2 · Spacing & Layout Doctrine

| Property | Value |
|---|---|
| Page horizontal padding | `px-5 sm:px-8` (matches PmShell / SafetyShell) |
| Page vertical padding | `py-8` (above-fold) · `pb-16` (scroll bottom) |
| Section gap | `space-y-8` between major sections |
| Card padding | `p-4` mobile · `p-6` desktop |
| Block internal spacing | `space-y-3` for related items · `space-y-6` between blocks |
| Sidebar width (desktop) | `w-64` (identical to PM V2, HR V2, Safety V2) |
| Sidebar internal padding | `py-5 px-3` |
| Mobile sidebar | bottom-sheet pattern · matching SafetySideNavV2 mobile fallback |
| Maximum content width | `max-w-7xl` (matches existing shells) |

---

## 3 · Typography Doctrine

| Element | Class |
|---|---|
| Page H1 | `font-display text-3xl sm:text-4xl font-black` |
| Section H2 | `font-display text-xl font-bold` |
| Mono kicker (uppercase tracking-wide) | `font-mono text-xs uppercase tracking-[0.2em] text-cyan-700` (PM scope: indigo-700 · HR: purple-700) |
| Body | `text-sm sm:text-base text-slate-700` |
| Subline / coaching | `text-xs sm:text-sm text-slate-500` · max ≤14 words |
| Severity pill text | `font-mono text-[10.5px] uppercase tracking-wide` |
| Audit-trail timestamps | `font-mono text-[11px] text-slate-500` |

PM scope kicker color: **indigo-700**. RFI / Schedule pages live in
PM. They wear the PM accent. Not cyan (that's Safety), not violet
(that's HR).

---

## 4 · Component Palette

Use **existing** Shadcn / internal components. Do not introduce new
primitives:

| Need | Component |
|---|---|
| Button (primary) | `<Button>` with `variant="default"` · slate-800 background (matches Safety Hub V2 P1B trim) |
| Button (secondary) | `<Button variant="outline">` |
| Card | `<Card>` (existing) |
| Form | `<Form>` + `react-hook-form` + `zod` (existing PM forms pattern) |
| Dialog | `<Dialog>` (existing) |
| Toast | `sonner` (existing) |
| Table | `<Table>` (existing) · no third-party data grid |
| Tabs | `<Tabs>` (existing) |
| Tooltip | `<Tooltip>` (existing) |
| Date picker | existing calendar component |
| Combobox / activity picker | extend existing combobox · do not introduce a new library |

**Forbidden:** new chart libraries, new icon sets (use `lucide-react`),
new animation libraries (use CSS or existing motion patterns), new
color systems.

---

## 5 · Color Discipline

| Surface | Color |
|---|---|
| Page background | `blueprint-bg` (existing) |
| Card chrome | `bg-white border border-slate-200` |
| Dark header chrome | `bg-slate-900 border-b-4 border-indigo-700` (PM accent) |
| Stripe accents | one stripe per domain · slate-600 for "Operational Records" |
| Severity red | `red-700` · used ONLY for: critical-path impact pill, safety/compliance pill, the single red dot on activities with active overdue CP constraints |
| Severity amber | `amber-600` · used for "Action Required" priority pill ONLY |
| Default text | `slate-700` |
| Muted text | `slate-500` |
| Disabled | `slate-300` |
| Success ack | `emerald-700` text only — NO emerald backgrounds, NO emerald pills (calmness doctrine) |

The Operational Records sidebar domain stripe is **slate-600**.
Schedule Intelligence does **not** get its own bright color. The
intelligence is in the data, not the chrome.

---

## 6 · Loudness Budget (per page)

Every new page must measure under the same calmness budget that
governs PM, HR, Safety:

| Metric | Budget |
|---|---|
| Hue family count (distinct accent colors per page) | ≤ 4 |
| Badge density (colored badges per 100 elements) | ≤ 15 |
| Escalation noise (red / amber elements per page) | ≤ 5 routine · ≤ 8 worst-case |
| Calmness score (composite) | ≥ 70 |
| Direction in trendline | `stable` after 5 records |

These are the same thresholds the existing `diff_doctrine_baseline.py`
measures. Each new page registers in the baseline probe. Drift past
the budget triggers chip yellow.

---

## 7 · Mobile Doctrine

Every new surface must respect the existing mobile doctrine:

- Touch targets ≥ 44px square.
- Sidebar collapses to a bottom drawer.
- Forms scroll cleanly (no overflow clipping).
- Tables become card-style stacks under `sm` breakpoint.
- Photo capture opens the native camera.
- No `position: fixed` modals taller than 80vh.
- No horizontal scroll except inside a deliberate Gantt window (V.5+
  and only if shipped).

Mobile is the **primary** field surface. Desktop is the dense fallback.

---

## 8 · Component Reuse Manifest

The RFI + Schedule subsystems will reuse the following existing
components without modification:

- `PmShell` · `PmPageShell` (existing layout)
- `SideNavV2` (existing PM sidebar · amended with new domain)
- `GovernanceHealthChip` (existing chip · consumes new exposure signals)
- `NotificationBell` (existing)
- `GlobalSearch` (existing · will index new RFIs / activities)
- `LangToggle` · `CompanyInfoDialog` · `MasciLogo`
- `FieldMemoryGlance` (existing · contextual recall)
- `PasskeyEnrollPrompt` (existing)
- `LastActivityLine` (existing)
- `IntegrationHealthCard` (existing)

If a component does not yet exist (RFI form fields, schedule activity
table, constraint inline badge), it is built **inside** the established
patterns. No new design systems.

---

## 9 · Governance Instrumentation Mandate

Every new page MUST:

1. Be reachable from the PM sidebar V2 (the routes in §3 of the
   architecture doc).
2. Have at least one `data-testid` for governance probes.
3. Be included in `test_visual_doctrine_baseline.py`'s portal list.
4. Be included in `test_governance_health_chip.py` if the page is a
   hub-style landing surface.
5. Produce a trendline record on `--append` runs.
6. Honour the auto-deploy checkpoint pipeline (no special-case opt-out).

No new page is "exempt" from instrumentation. Doctrine > velocity.

---

## 10 · Inheritance Checklist (use at every implementation PR)

A new RFI / Schedule surface PR cannot merge without:

- [ ] Reuses `PmShell` / `PmPageShell` (no custom chrome)
- [ ] Kicker · H1 · subline pattern intact (kicker indigo-700)
- [ ] No new icons outside `lucide-react`
- [ ] No new color tokens
- [ ] No new fonts
- [ ] No `border-2` chrome
- [ ] No animated banners
- [ ] No emoji in user-facing copy
- [ ] All interactive elements carry `data-testid` (kebab-case)
- [ ] Mobile breakpoint behaviour matches PM Hub
- [ ] Severity language uses approved terminology
- [ ] Loudness budget probe passes (run `diff_doctrine_baseline.py --append` after change · `direction` stays `stable`)
- [ ] Visual doctrine baseline probe includes the new URL

---

## 11 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Checklist (§10) is mandatory on every V.1+ PR.
