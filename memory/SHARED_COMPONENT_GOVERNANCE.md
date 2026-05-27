# Shared Component Governance — Phase IV-BETA

**Iteration:** iter437 · Phase IV-BETA · 2026-02
**Status:** 🟢 BINDING ACROSS ALL PORTALS · ENFORCED VIA STORYBOOK + ESLINT
**Inherits from:** `COMPONENT_HIERARCHY_STANDARD.md` (Phase IV-A) · `COMPONENT_STANDARDIZATION_MATRIX.md` (Phase IV-0)

The platform has one component library. Every portal draws from it. Drift between portals is structurally prevented by the rules below — codified into the build pipeline.

This document is the canonical specification of how each shared component behaves across all 7 portals.

---

## I. The 12 governed shared components

These are the only components allowed to render in operational portal surfaces. New components require a doctrine amendment PR.

| Component | Source | Used by all portals for |
|---|---|---|
| `<Shell>` (portal-specific subclass) | `components/{Admin,Pm,Hr,...}Shell.jsx` | Top-bar + sidebar + body slot |
| `<SideNavV2>` (per-portal subclass) | `components/{portal}/sidebar/SideNavV2.jsx` | Domain-grouped 2-tier nav |
| `<Sheet>` | `components/ui/sheet.jsx` | Mobile drawer (iOS-fixed) |
| `<Dialog>` | `components/ui/dialog.jsx` | Modal confirmations · Tier 4 escalations |
| `<Button>` | `components/ui/button.jsx` | Every clickable action |
| `<Card>` | `components/ui/card.jsx` | Record containers · list items |
| `<Table>` (+`<TableHead>`, `<TableRow>`, `<TableCell>`) | `components/ui/table.jsx` | Dense data |
| `<Input>` + `<Select>` + `<Checkbox>` | `components/ui/*` | Forms · filters |
| `<Badge>` | `components/ui/badge.jsx` | State badges · severity badges |
| `<Toast>` (Sonner) | `components/ui/sonner.tsx` | Success confirmations (Tier 0) |
| `<AlertBanner>` (new in IV-BETA.2) | `components/ui/alert-banner.jsx` | Inline operational signal banner |
| `<EmptyState>` (new in IV-BETA.2) | `components/ui/empty-state.jsx` | Canonical empty-state container |

---

## II. Sidebar governance (the `<SideNavV2>` contract)

Every portal's `<SideNavV2>` must:

1. Render Tier-1 domain rows in a flex column.
2. Each domain row has: 2-px stripe (left) · icon (slate-300) · label (mono uppercase) · subline (slate-500 ≤ 12 words) · chevron.
3. Tier-2 sub-entries appear indented 12 px from the domain row.
4. Min row height: 44 px desktop · 56 px (domains) / 48 px (children) mobile.
5. Active state: 2-px stripe color + `bg-slate-800` background — NEVER saturated portal color background.
6. State persistence: localStorage key `masci.{portal}.sidebar.openDomains`.
7. Domain auto-expansion on route change via `findActiveDomainId(pathname)` helper.
8. Footer rail (cross-portal pinned) below domains, separated by 1-px slate-800 border.
9. Drawer-scope only: wrapped in `flex-1 min-h-0 overflow-y-auto overscroll-contain` parent with `WebkitOverflowScrolling: 'touch'`.

A `<SideNavV2>` that diverges from this contract is rejected at PR review.

---

## III. Card governance

Every portal's card-shaped UI must:

| Aspect | Rule |
|---|---|
| Default border | 1-px `border-slate-200` |
| Hover border | 1-px `border-slate-300` |
| Active selection border | 2-px domain stripe color (left border only) |
| Background | `bg-white` (light surfaces) or `bg-slate-900` (dark drawer panels) |
| Padding | `p-3` (dense) · `p-4` (standard) · `p-6` (expanded) |
| Title typography | `text-sm font-medium` (cards in dense lists) · `text-base font-semibold` (standard cards) |
| Hover elevation | `hover:shadow-sm` — NEVER `shadow-md` or higher on idle/hover |
| Border-radius | `rounded-md` (6 px) — uniform across all cards |
| Action zone | At most ONE primary action button per card |

Hub-grade hero cards (e.g., PM Crew Compliance card) may use `p-5` and include up to 4 inline metric tiles, but must still conform to the border/shadow/radius rules.

---

## IV. Table governance

Every portal's table must:

| Aspect | Rule |
|---|---|
| Header row | `bg-slate-50` · `text-xs uppercase font-mono tracking-wider text-slate-500` |
| Row divider | 1-px `border-slate-100` |
| Hover row | `bg-slate-50` background-color shift only — no shadow, no transform |
| Row height | ≥ 44 px (touch target) |
| Sortable column header | Slate-700 caret icon · click toggles asc/desc/off |
| Sticky header | `position: sticky` on the `<thead>` row · z-20 within the table scroll container |
| Empty state | Renders `<EmptyState>` component inline · NEVER renders 0 rows with no message |
| Pagination | "End of results · {n} items" always shown after the last page |

---

## V. Filter row governance

Every list view's filter row must:

| Aspect | Rule |
|---|---|
| Layout | Horizontal flex row, wraps on narrow viewports |
| Search input | Always first (leftmost), with `<Search>` icon prefix |
| Filter chips | Right of search · use `<Badge>` variant `outline` · clickable |
| Reset button | Right-most, `<Button variant="outline" size="sm">` labeled `Reset` |
| Vertical spacing | 16 px below filter row before content |
| Sticky on long lists | Sticky at `top-14` (below top-bar) with z-20 |

---

## VI. Button governance

| Variant | Use case | Color |
|---|---|---|
| `default` (primary) | The page's 1 primary action | `bg-slate-900 text-white hover:bg-slate-800` |
| `outline` (secondary) | Secondary actions, Cancel | `border-slate-300 text-slate-700 bg-white` |
| `ghost` | Tertiary inline actions | `text-slate-700 hover:bg-slate-100` |
| `destructive` | Irreversible destructive actions (rare) | `bg-red-600 text-white hover:bg-red-700` |
| `severity-{tier}` (new IV-BETA.2) | Tier-3 / Tier-4 acknowledge buttons | Per severity-color map |

**Forbidden:**
- Primary buttons colored portal-accent (no `bg-amber-600` PM primaries · no `bg-red-700` admin primaries)
- Buttons with gradient fills
- Buttons with icon-only at Tier-3+ priority (icon-only is OK for ghost utility buttons in chrome)

Button sizes: `sm` (32 px) · `default` (40 px) · `lg` (48 px primary mobile CTA). Touch target padding ensures all hit ≥ 44 × 44.

---

## VII. Sheet (mobile drawer) governance

Every `<Sheet>` use across portals must:

1. Use the iOS-fixed `<SheetContent>` from `components/ui/sheet.jsx`.
2. If contains scrollable nav: include the canonical scroll wrapper (`flex-1 min-h-0 overflow-y-auto overscroll-contain` + `WebkitOverflowScrolling: 'touch'`).
3. Use `w-72` (288 px) for nav drawers · `max-w-md` for confirmation sheets.
4. Backdrop: `rgba(15, 23, 42, 0.55)` slate-900 @ 55% (no blur).
5. Close on: tap outside · ESC · explicit close button · navigate event.

---

## VIII. Dialog (modal) governance

| Aspect | Rule |
|---|---|
| Max width | `max-w-md` (28 rem) for confirmations · `max-w-lg` for short forms |
| Title | Verb + noun (`Reject Daily Report`) — never `Are you sure?` |
| Body | ≤ 2 sentences stating consequence |
| Primary button | Verb-named (matches title verb) · color matches severity (slate-900 default · red-600 destructive · severity color for Tier 4) |
| Secondary button | Always `Cancel` (left of primary) |
| Tier 4 modals | NOT dismissable by ESC or tap-outside · primary button labeled `Acknowledge` |
| Z-index | `z-55` (modals) · `z-60` (Tier 4 escalations) |

Maximum one open dialog at a time — enforced at runtime by the shared `<Dialog>` portal root.

---

## IX. Banner governance

`<AlertBanner>` (new component landing in IV-BETA.2):

| Tier | Background | Border | Dismissable | Persistent |
|---|---|---|---|---|
| 0 (Note) | `bg-slate-50` | `border-slate-200` | Yes | No (manual dismiss) |
| 1 (Reminder) | `bg-blue-50` | `border-blue-200` | Yes | No |
| 2 (Attention) | `bg-amber-50` | `border-amber-300` | Yes (returns on next load if state persists) | Yes (on state) |
| 3 (Action Required) | `bg-orange-50` | `border-orange-400` | No — resolves on action | Yes |
| 4 (Escalation) | `bg-red-50` | `border-red-500` | No — converts to modal if not actioned in 60 s | Yes |

Rules:
- ≤ 1 banner per tier per surface.
- Multiple Tier-2 events collapse into one "X items need attention" banner.
- Banners never animate; they appear and remain.

---

## X. Notification governance

`<NotificationBell>` (top-bar component):

| Aspect | Rule |
|---|---|
| Position | Top-bar, right side, before OfflineIndicator |
| Badge count | Number of unread Tier 2+ notifications |
| Badge color | `bg-slate-700` for ≤ Tier 3 · `bg-red-600` when any Tier 4+ exists |
| Dropdown | Shows top 7 by tier+recency · `View all` link bottom |
| Item layout | Severity icon · noun-phrase title (1 line) · timestamp + tier badge (1 line) |
| Mark as read | Auto-mark on dropdown open (Tier 0–2) · explicit tap (Tier 3+) |

The bell is single-source: a notification surfaced in any portal appears in every portal's bell for the same operator account.

---

## XI. Section-header governance

In-page section header pattern (applied identically across all portals):

```jsx
<div className="flex items-baseline justify-between mb-4">
  <div>
    <h2 className="text-lg font-medium text-slate-800">{title}</h2>
    {subline && (
      <p className="text-xs text-slate-500 mt-0.5">{subline}</p>
    )}
  </div>
  {action && <div>{action}</div>}
</div>
```

`title` is Tier-3. `subline` is Tier-5 (optional, ≤ 12 words). `action` is one outlined button (no primary).

---

## XII. Loading-state governance

| Loading scope | Component | Rule |
|---|---|---|
| Page-level load | `<Loader2 className="animate-spin" />` + centered "Loading…" | 1.4 s pulse, no faster |
| List skeleton | 3 skeleton rows with `bg-slate-100 animate-pulse rounded-md h-12` | Cap 3 rows visible |
| Inline indicator | `<Loader2 className="w-3.5 h-3.5 animate-spin" />` next to action | Only during action submission |
| Background sync | NO ambient spinner — operations happen silently | The pulsing sync indicator from old Admin sidebar is FORBIDDEN |

---

## XIII. Empty-state governance

`<EmptyState>` (new component landing in IV-BETA.2):

```jsx
<EmptyState
  icon={ClipboardCheck} // optional, slate-400, 32 px
  title="No submissions for this date range."
  subline="Try a different date range or check the filters above."
  action={<Button variant="outline">Reset filters</Button>} // optional
/>
```

Rules:
- Icon: optional, slate-400, line-style only, 32 px max.
- Title: ≤ 12 words, operational fact.
- Subline: ≤ 18 words, optional, slate-500.
- Action: ≤ 1 button, outlined.
- Forbidden: illustrations, emoji, "Get started" CTAs.

---

## XIV. Enforcement

### Storybook governance (Phase IV-BETA.4)

Every shared component lives in `/storybook` with:
- Default state · Hover state · Active state · Disabled state
- Mobile (375 px) · Tablet (768 px) · Desktop (1440 px) viewports
- Documented props with TypeScript types

A PR adding a new portal feature must reference the storybook entry for every component used.

### ESLint rules (Phase IV-BETA.4)

| Rule | Catches |
|---|---|
| `no-unauthorized-z-index` | `z-` classes outside the 9-layer ladder |
| `no-portal-accent-on-primary` | Primary buttons with `bg-amber-*`, `bg-red-7*` (except `destructive` variant) |
| `no-bg-gradient` | Any `bg-gradient-*` class |
| `no-emoji-in-strings` | Emoji in JSX strings (operational copy is emoji-free) |
| `require-testid-on-interactive` | Buttons / links without `data-testid` |

### Visual regression (Phase IV-BETA.4)

Snapshot diffs run on every PR for:
- Each portal's `/overview` surface
- Each portal's `<SideNavV2>` (open + closed states)
- Each portal's mobile drawer (open state on 375 px)
- The shared dialog modal in 3 severity variants

Drift > 5% area = PR review escalation.

---

## XV. Component-version tracking

Each shared component carries a `__doctrine_version` constant:

```jsx
export const Button = ...;
Button.__doctrine_version = "IV-A.1";
```

A registry script (Phase IV-BETA.4) scans all components on build and rejects mismatches. Upgrading a component's doctrine version requires:
1. Update component implementation
2. Update `__doctrine_version`
3. Update Storybook entry
4. Visual regression suite passes
5. All portals using the component are tested

---

## Verdict

🟢 **SHARED COMPONENT GOVERNANCE LOCKED.** Every cross-portal component now has a binding contract, an enforcement mechanism, and a versioning trail. Drift between portals is prevented at build time.
