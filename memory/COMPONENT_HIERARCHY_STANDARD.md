# Component Hierarchy Standard — Phase IV-A

**Iteration:** iter437 · Phase IV-A · 2026-02
**Status:** 🟢 COMPONENT GOVERNANCE LOCKED · BINDING ON ALL UI COMPONENTS FROM THIS POINT FORWARD
**Companion docs:** `COMPONENT_STANDARDIZATION_MATRIX.md` (Phase IV-0 — primitives map) · `ADMIN_UX_GOVERNANCE.md` (visual weight ladder) · `VISUAL_LOUDNESS_REDUCTION_PLAN.md`

This document governs how UI components compose into surfaces. It is the rulebook that prevents UI chaos as the platform scales. Every component decision — z-index, density, modal stacking, badge usage, color, typography, spacing — is bound by these rules.

The platform's visual surface is an industrial control panel, not a creative canvas. Every component placement must justify its visual cost.

---

## I. The five hierarchy principles

| Principle | What it prevents |
|---|---|
| **1. One thing is loudest** | Multiple competing reds · multiple primary CTAs · multiple alerts at once |
| **2. Tiers are absolute** | A Tier-3 element cannot visually outweigh a Tier-1 element on the same surface |
| **3. Red is reserved** | Red appears only for Tier 4–5 severity and the OPERATIONS domain stripe — nowhere else |
| **4. Z-index is declared, not local** | Every layer's z-index comes from a single platform-wide ladder, never an ad-hoc number |
| **5. Density follows context** | Dense data views (tables) ≠ form views ≠ navigation surfaces — each has its own density rules |

---

## II. Visual hierarchy tiers (the canonical Tier 0–5 ladder)

Re-declares `ADMIN_UX_GOVERNANCE.md` ladder with concrete component-level treatment.

| Tier | What lives here | Font | Color | Weight | Spacing |
|---|---|---|---|---|---|
| **0 · Operational signal** | Cluster capacity banner · Tier 4–5 alerts · current-context badge | `text-base` (16 px) | severity-color text on white OR severity-color stripe + slate-900 text | semibold | sticky top, ≥ 24 px padding |
| **1 · Domain headers** | "OPERATIONS", "WORKFORCE" labels | `text-xs` (12 px) uppercase mono tracking-wider | slate-500 with 2 px stripe | medium | 16 px top, 4 px bottom |
| **2 · Page H1** | The current page title | `text-2xl` (24 px) mobile · `text-3xl` (30 px) desktop | slate-900 | semibold | 24 px bottom |
| **3 · Section H2** | Sub-section titles within a page | `text-lg` (18 px) | slate-800 | medium | 16 px bottom |
| **4 · Body / sub-nav / table cells** | The bulk of operational content | `text-sm` (14 px) | slate-700 | normal | rhythm per §VI |
| **5 · Metadata / coaching sublines / footers** | Timestamps, counts, captions | `text-xs` (12 px) | slate-500 | normal | tight |

**Hard rule:** No surface may contain two Tier-0 elements simultaneously. If two demand Tier 0, one must drop to Tier 2 with severity color preserved as a stripe.

---

## III. Z-index doctrine (the platform-wide layer ladder)

The platform has exactly **9 z-index layers**. No component declares a z-index outside this ladder.

| z-index | Layer name | Used for |
|---|---|---|
| `z-0` | Base layer | Page content, default flow |
| `z-10` | Inline overlays | Tooltips, popovers anchored to inline elements |
| `z-20` | Sticky in-page elements | Sticky page H1, sticky table headers, sticky form-section headers |
| `z-30` | App chrome | Top-bar, bottom-nav, sticky bottom CTA bars |
| `z-40` | Modal backdrop · drawer backdrop | The dimming layer behind drawer/modal |
| `z-50` | Drawer · bottom sheet | The drawer panel itself, bottom-sheet panel |
| `z-55` | Modal panel | Standard modals, dialogs |
| `z-60` | Tier 4 escalation modal | Escalations that must be acknowledged before any other interaction |
| `z-70` | Tier 5 emergency takeover | Full-screen emergency state — covers everything |

**Forbidden:** Any literal z-index value outside this ladder. Any `z-index: 9999`, `z-index: 100000` is an automatic doctrine violation.

**Tooltips on top of modals:** Tooltips inside a modal use `z-[60]` (relative — they live in the modal's stacking context). They never declare a global high z-index.

**Toasts:** Toasts use `z-50` and are positioned outside the modal backdrop — they remain visible during modal interactions, ensuring confirmation toasts are seen.

---

## IV. Modal stack governance

The platform allows at most **one modal open at a time**. Stacked modals are a doctrine violation.

### Rules

- A modal CANNOT open another modal directly. If the modal's action requires further input, redesign to a multi-step flow within the same modal OR cancel-and-route to a dedicated page.
- A modal CAN open a bottom-sheet on mobile. (The sheet replaces the modal — z-50 — and the modal closes.)
- A Tier 4–5 escalation modal supersedes any open modal. The lower-tier modal force-closes (state preserved as a draft if applicable).
- Toasts CAN appear over a modal (z-50 toast above z-55 modal? — no: toasts are at z-50, modals at z-55. Toasts are repositioned ABOVE the modal panel via positioning, not via z-stacking. Toasts inside modal context use the modal's stacking context with relative `z-[10]`).

### Modal entry/exit

- 150 ms fade-in for backdrop, 200 ms scale-up + fade-in for panel (`scale-95 → scale-100`).
- 100 ms fade-out for both on dismiss.
- Focus traps inside the modal. ESC dismisses (for Tier ≤ 3 only). Tier 4+ require explicit `Acknowledge`.

---

## V. Notification layering

The platform shows operational notifications through three distinct layers. Each has rules about co-existence.

| Layer | Component | Tier | Coexists with |
|---|---|---|---|
| **Inline banner** | `<AlertBanner>` at top of content area | 0–2 | Other inline banners (max 1 per tier visible) · modals · toasts |
| **Top-bar bell** | Bell icon in top-right with count badge | 0–5 (all tiers represented) | Everything |
| **Modal escalation** | `<EscalationModal>` full-takeover | 4–5 only | Nothing — supersedes all other UI |
| **Toast** | Bottom-right transient | 0 only (success confirmations) | Everything |

### Coexistence rules

- **At most ONE inline banner per tier** is visible on a given surface. Multiple Tier-2 events collapse into a single "X items need attention" banner that expands into the bell-dropdown.
- **Bell badge** shows the count of UNREAD Tier ≥ 2 notifications. Tier 0–1 don't count toward the badge (they appear in the dropdown but don't escalate the bell visually).
- **Modal escalation** suppresses all banners and toasts for the duration of its presence.
- **Toasts** never appear during a Tier 4–5 escalation modal.

---

## VI. Badge rules (the strictest discipline in the system)

Badges proliferate. The platform restricts them aggressively.

### Allowed badges

| Badge | Use | Color |
|---|---|---|
| **Count badge** on bell icon | Unread Tier 2+ notifications | slate-700 bg, white text (no red unless count includes Tier 4+) |
| **Count badge** on domain header in sidebar | Pending actions in that domain | slate-700 bg, white text |
| **State badge** in tables/cards | The state of a record (`Submitted`, `Approved`, `Open`, etc.) | per state-color map below |
| **Severity badge** on alerts/notifications | Tier 2+ severity | per severity-color map (§VII) |

### State-color map (the only state colors allowed)

| State | Badge color |
|---|---|
| `Draft` | slate-200 bg, slate-700 text |
| `Open` / `Submitted` / `Pending` / `Scheduled` | blue-100 bg, blue-700 text |
| `In Progress` / `In Maintenance` / `Investigating` | amber-100 bg, amber-700 text |
| `Approved` / `Resolved` / `Active` / `Completed` | emerald-100 bg, emerald-700 text |
| `Rejected` / `Failed` / `Down` / `Disabled` | orange-100 bg, orange-700 text |
| `Closed` / `Retired` | slate-300 bg, slate-700 text |
| `Escalation` / `Emergency` | red-100 bg, red-700 text |

### Forbidden badges

- ❌ "NEW" badges next to features (everything in the platform is "new" to someone)
- ❌ "BETA" / "PREVIEW" badges in the sidebar (the preview environment is environment-level, not feature-level)
- ❌ Version-number badges in user-facing UI (version belongs in the system settings page, nowhere else)
- ❌ "PRO" / "PAID" / "PREMIUM" badges (the platform does not gate features behind cosmetic badges)
- ❌ Decorative badges with emoji or symbols (`🔥`, `★`, `!`, etc.)
- ❌ Multi-line badges (badges are always single-line, ≤ 14 characters)

### Badge density rule

A single card/row may contain at most **2 badges**: one state badge + one severity badge (if severity is non-zero). If more state information is needed, it lives in the row's expanded view, not as additional badges.

---

## VII. Red-color restrictions (the "critical-only red" doctrine)

Red is the loudest color in the human visual cortex. The platform uses it sparingly so that when it appears, it means something.

### Red is allowed ONLY in

1. **Tier 4 (Escalation) severity badges and stripes** — `red-100/700` palette
2. **Tier 5 (Emergency) takeover screens** — full-red treatment permitted
3. **The OPERATIONS domain stripe** — 2 px wide only, never as a fill
4. **`Failed` / `Down` state badges** when describing an asset's operational state
5. **Destructive action confirmations** inside a Tier 3+ modal — the primary button may be red ONLY when the action is irreversible
6. **Form-field validation errors** — error text in `red-700`, ≤ 1 line, paired with an inline icon

### Red is FORBIDDEN in

- ❌ Multiple elements on the same surface (one red element per view, max)
- ❌ Domain headers other than OPERATIONS (other domains use blue, amber, violet, orange, slate)
- ❌ Sidebar active-state highlight (use a 2-px stripe, not a red background)
- ❌ Top-bar (the top-bar is always neutral)
- ❌ Decorative accents, gradients, hover-states, dividers
- ❌ Brand identity — the platform brand color is slate-900, not red. (The OPERATIONS domain happens to use red because operations are critical, not because the brand is red.)

### The "red breathes" test

Before adding any red element, count the red elements visible on the destination surface. If the count exceeds 1, the new red is either replaced with amber (next-loudest) OR an existing red is reclassified.

---

## VIII. Fixed / sticky element rules

Fixed and sticky positioning consumes screen real-estate permanently. The platform restricts how many fixed/sticky elements may co-exist.

### Allowed fixed/sticky stack (top of screen → bottom)

```
1. Top-bar          (fixed top-0, z-30, 56 px)
2. Page H1 + filters (sticky top-14, z-20, ≤ 80 px)
3. Section header    (sticky inside scroll container, z-10, ≤ 48 px)
4. Sticky bottom CTA (fixed bottom-0, z-30, ≤ 56 px + safe-area-inset-bottom)
```

Total vertical real-estate consumed: ≤ 240 px (top 184 + bottom 56). On a 667-px iPhone SE viewport, this leaves ≥ 427 px of scrollable content — acceptable.

### Forbidden

- ❌ Two sticky banners stacked (e.g., a sticky info banner AND a sticky filter row)
- ❌ Sticky promotional / informational elements (banners earn no sticky)
- ❌ Mid-page sticky sidebars (the desktop sidebar is fixed-width left rail, not a sticky right-rail)
- ❌ Sticky elements that animate their height (visual jitter on scroll)

---

## IX. Card density rules

Cards are the platform's default container for individual records. Card density is governed per context.

### Card density tiers

| Tier | Used for | Padding | Min height | Allowed elements |
|---|---|---|---|---|
| **Dense** | Tables, list views with > 12 items | 12 px | 56 px | Title + 1 metadata line + 1 badge |
| **Standard** | Domain dashboards, summary lists | 16 px | 88 px | Title + 2 metadata lines + 1-2 badges + 1 action |
| **Expanded** | Detail views, hero cards | 24 px | 120 px+ | Title + multi-line summary + badges + 1+ actions + thumbnail |

### Card layout rules

- Title is always Tier 4 (`text-sm`, slate-900, medium) — never larger than the page H1.
- Metadata uses middle-dot separators: `Crew 7 · Rt-441 · 14:22`.
- At most ONE primary action per card (typically `Open` or the most-likely-next-verb).
- Hover state: 4-px shadow elevation + 1-px border-color shift to slate-300. No background color change.
- Active state (selected in multi-select): 2-px border in the domain stripe color + slate-50 background.

### Card grid rules

- Desktop card grid: 12-col CSS grid, cards span 4 cols (3-up) by default, 6 cols (2-up) for expanded.
- Mobile: 1-up always. No multi-column card grids on mobile.
- Card gap: 12 px (dense), 16 px (standard), 24 px (expanded).

---

## X. Typography hierarchy

The platform uses a single typeface (Inter — already loaded) with a strict 6-step scale.

| Scale | Tailwind class | Size | Use |
|---|---|---|---|
| **Display** | `text-3xl` (desktop) / `text-2xl` (mobile) | 30 px / 24 px | Page H1 (Tier 2) |
| **H2** | `text-lg` | 18 px | Section headers (Tier 3) |
| **H3** | `text-base` | 16 px | Card titles, modal titles (Tier 4 emphasized) |
| **Body** | `text-sm` | 14 px | Default operational text (Tier 4) |
| **Meta** | `text-xs` | 12 px | Sublines, timestamps, footnotes (Tier 5) |
| **Mono** | `font-mono text-xs` | 12 px | IDs, codes, audit-log entries |

### Forbidden typography

- ❌ Sizes outside this scale (`text-4xl`, `text-5xl`, custom px sizes)
- ❌ Font weights outside `font-normal`, `font-medium`, `font-semibold`, `font-bold`
- ❌ `font-bold` for body text (reserved for emphasis within a paragraph, never for entire paragraphs)
- ❌ Italic for emphasis (use weight, not slant)
- ❌ Letter-spacing adjustments except `tracking-wider` on Tier-1 uppercase eyebrows
- ❌ Custom fonts loaded for any operational surface (Inter only)
- ❌ Two type families on the same surface (Inter for sans, JetBrains Mono for mono — that's it)

---

## XI. Section rhythm

Pages flow vertically in a consistent rhythm. Sections breathe predictably.

### The canonical page rhythm (vertical sequence)

```
1. Domain breadcrumb           ← Tier 1 · 24 px tall
2. (12 px gap)
3. Page H1 + coaching subline  ← Tier 2 + Tier 5 · 56 px tall
4. (24 px gap)
5. Primary signal (optional)   ← Tier 0 banner · 56 px tall when present
6. (24 px gap if banner present, otherwise 16 px)
7. Filters / search row        ← 56 px tall
8. (16 px gap)
9. Main data surface           ← variable
10. (24 px gap)
11. Pagination / "End of results"  ← 48 px tall
```

### Rhythm rules

- Vertical gaps are multiples of 4 px (4, 8, 12, 16, 24, 32) — never arbitrary.
- Two adjacent gaps cannot both exceed 16 px (prevents "floating section" syndrome).
- A section divider (1-px slate-200 line) replaces a 32+ px gap when the visual relationship needs reinforcing.

---

## XII. Empty-state behavior

Empty states are operational events, not opportunities for marketing.

### Empty-state structure

```
[Optional 32-px neutral icon — line-style, slate-400]
{Operational fact in 6-12 words · Tier 4 · slate-700}
{Optional one-sentence context · Tier 5 · slate-500}
[Optional primary action if creating data is the obvious next step]
```

### Empty-state canonical wordings

| Surface | Empty-state copy |
|---|---|
| Daily Reports list (no reports today) | `No Daily Reports for this date range.` |
| Incidents list (no open incidents) | `No open incidents.` (calm — this is a positive operational state) |
| Pre-Op checks (none pending) | `All Pre-Op checks complete for today.` |
| Notifications dropdown (no unread) | `No unread notifications.` |
| Search results | `No results for "{query}".` (followed by `Try a different search term.`) |

### Forbidden empty-state patterns

- ❌ Illustrations / cartoons / mascots
- ❌ "Get started" CTAs (the platform does not onboard; operators are onboarded by humans)
- ❌ "It's quiet here…" / "Nothing to see…" / "Bummer!" / casual prose
- ❌ Emoji
- ❌ Multiple sentences of explanation
- ❌ "Tips" or "Did you know?" educational copy

---

## XIII. CTA placement doctrine

Where the primary CTA lives on every page is governed.

### Desktop CTA placement

- Primary CTA: **top-right of the content area**, aligned with the page H1.
- One primary CTA only. (See `OPERATIONAL_VERBIAGE_DOCTRINE.md` §XIII rule.)
- Secondary actions: in a `…` overflow menu next to the primary, OR in a footer if the page has a clear "after-action" zone.

### Mobile CTA placement

- Primary CTA: **sticky bottom bar in the thumb zone** (see `MOBILE_NAVIGATION_STANDARD.md` §III).
- Secondary actions: in a bottom-sheet triggered by `…` overflow icon in the top-bar.

### Forbidden CTA placements

- ❌ Multiple primary CTAs on the same view (e.g., "Submit" AND "Save and continue" both as primary)
- ❌ Floating action buttons (FAB) anywhere — they obscure content and have no fixed semantic role
- ❌ Primary CTA inside a card (cards have row-level actions, not page-level CTAs)
- ❌ Primary CTA below the fold on desktop (must be visible on initial render)

---

## XIV. Component composition anti-patterns

These are observed or anticipated mistakes. Phase IV-A.4 ships PR-review automation to flag them.

| Anti-pattern | Why forbidden | Correct path |
|---|---|---|
| Modal with > 1 input field at Tier 4 severity | The operator should not be filling out forms while acknowledging an escalation | Acknowledge first → route to a form view |
| Sheet that contains another sheet's trigger | Sheets cannot stack | Convert inner trigger to a route navigation |
| Banner that auto-dismisses after N seconds | Banners are persistent until resolved | Use a toast instead, or keep the banner sticky until state changes |
| Card with > 2 action buttons | Cards carry 1 primary action | Move secondary actions to an inline overflow menu |
| Page with > 1 hero element | Multiple heroes = no hero | Choose one |
| Two domain stripes visible on the same row | Records belong to one domain | Pick the dominant domain |
| Animated SVG loaders larger than 24 × 24 | Visual noise | Use a 16-px spinner, or a skeleton row |
| Skeleton rows that pulse aggressively | Distracts the eye | Use a 1.4-second pulse with 30% opacity range, not 0-100% |
| Notifications dropdown that shows > 12 items | Operators stop reading after ~7 | Show the most-recent 7 + a `View all` link |

---

## XV. Operator-trust principles for components

Operators trust the visual system when:

1. **Element treatment never lies about importance.** A small slate text is unimportant. A red stripe means something operational. A modal demands action. The visual language is predictable.
2. **The same element looks the same everywhere.** A "Submit" button on a Daily Report looks identical to a "Submit" button on an Incident form. No view-by-view styling drift.
3. **The platform never adds visual noise to look "modern."** No gradients, no glassmorphism beyond the one allowed backdrop blur, no parallax, no scroll-triggered animations on operational pages.
4. **Loading states are honest.** A spinning element implies the system is doing work. If the system is idle, no spinner appears, even if data is delayed.
5. **Error states are specific.** A 500 error says what failed and what to do. It does not say "Something went wrong."

---

## XVI. Enforcement

- **Storybook governance:** Phase IV.A.5 ships a `/storybook` build that catalogs every approved component with its tier, density, and usage rules. Any frontend PR adding a non-approved component is rejected.
- **ESLint rule (custom, Phase IV.A.5):** `no-unauthorized-z-index` — flags any literal `z-` class outside the §III ladder.
- **Visual regression (Phase IV.A.6):** Percy or Chromatic-equivalent snapshots of the approved component library. Drift triggers PR review.
- **PR checklist additions:**
  - Tier assignment declared for every new visible element
  - Z-index from the §III ladder
  - Badges from the §VI allowed list
  - Red usage justified per §VII
  - Empty states use §XII wording
  - Typography from the §X scale

---

## Verdict

🟢 **COMPONENT HIERARCHY GOVERNANCE LOCKED.** Every component decision now has a rule. Every visual layer has a tier. Every z-index has a place. Future UI chaos is structurally prevented because the governance encodes "what is allowed" rather than only "what was done."
