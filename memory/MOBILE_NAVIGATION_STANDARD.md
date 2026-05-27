# Mobile Navigation Standard — Phase IV-A

**Iteration:** iter437 · Phase IV-A · 2026-02
**Status:** 🟢 MOBILE DOCTRINE LOCKED · iOS SAFARI SCROLL FIX PERMANENTLY CODIFIED
**Companion docs:** `SIDEBAR_REARCHITECTURE.md` (desktop nav structure) · `ADMIN_UX_GOVERNANCE.md` (Tier ladder)
**Regression-locked by:** `/app/backend/tests/pw_suite/test_admin_mobile_nav_scroll.py`

The platform's default operator is on an iPad in the sun, on an iPhone in a truck cab, on a Galaxy in gloves. Mobile is not a responsive afterthought — mobile is the primary surface for field-adjacent admin work. Desktop is the supervisor's surface. The two must feel like the same platform spoken at different volumes.

This document is the binding standard for every mobile surface in the admin portal AND the field portal. Every nav decision, sheet, drawer, modal, scroll container, and touch target is governed by these rules.

---

## I. The five mobile governance principles

| Principle | Operational implication |
|---|---|
| **1. Thumb-first, not tap-anywhere** | Primary actions live in the lower-third thumb-reach zone. Top-bar elements are passive (logo, hamburger, current-context label). |
| **2. ≤ 6 things at once** | Any mobile surface that shows more than 6 high-weight elements without scrolling has failed. Groups, collapse, or split. |
| **3. Scrolls never trap** | Every scroll container declares its overflow contract. Nested scrolls require explicit `overscroll-contain`. No scroll path may end at "the operator is stuck." |
| **4. Touch targets are 44 × 44 minimum** | Apple HIG minimum. Spacing between targets ≥ 8 px. Hit-areas may extend beyond visible bounds via padding. |
| **5. iOS Safari is the lowest common denominator** | If it works on iOS Safari, it works everywhere. If a behavior requires Chromium-only quirks, it does not ship. |

---

## II. The drawer doctrine (the mobile sidebar)

The drawer is the **operational launcher**. It is not a compressed desktop sidebar. It is a curated entry point to the 6 governed domains.

### Drawer structural rules

| Aspect | Specification | Rationale |
|---|---|---|
| Trigger location | Top-left hamburger, 44 × 44 px hit area | Thumb-reach on right-hand-held phone, eye-target on left-hand-held |
| Width | `w-72` (288 px) on portrait, `w-80` (320 px) on landscape | Leaves ≥ 60 px tap-out area to dismiss |
| Open animation | 200 ms ease-out slide from left + 100 ms backdrop fade | Long enough to be perceived, short enough not to delay |
| Close behaviors | (a) tap outside · (b) tap close-X · (c) tap a domain that navigates · (d) swipe-left gesture | Four redundant paths — operator cannot get stuck open |
| Backdrop | `rgba(15, 23, 42, 0.55)` (slate-900 @ 55%) | Calm dim — not solid black, not blurred (blur is too heavy on iOS) |
| Z-index | `z-50` for drawer, `z-40` for backdrop, `z-60` for emergency takeovers | Single declared stack — see `COMPONENT_HIERARCHY_STANDARD.md` §III |

### Drawer scroll governance (THE FIX, CODIFIED)

The iOS Safari scroll bug fixed in Phase IV-A.0 (`/app/frontend/src/components/ui/sheet.jsx`) is now doctrine. All future drawer implementations must follow this exact pattern.

#### The mandatory drawer scroll pattern

```jsx
<SheetContent className="flex flex-col p-0">
  {/* Tier 0 · Sticky header — shrink-0 */}
  <div className="shrink-0 px-4 py-3 border-b">
    <DrawerHeader />
  </div>

  {/* Tier 1 · Scroll container — flex-1 min-h-0 overflow-y-auto */}
  <div
    data-testid="admin-mobile-nav-scroll"
    className="flex-1 min-h-0 overflow-y-auto overscroll-contain"
    style={{ WebkitOverflowScrolling: 'touch' }}
  >
    <DrawerNavBody />
  </div>

  {/* Tier 2 · Sticky footer (optional) — shrink-0 */}
  <div className="shrink-0 px-4 py-3 border-t">
    <DrawerFooter />
  </div>
</SheetContent>
```

#### Required classes / styles — non-negotiable

| Class / style | Why |
|---|---|
| `flex flex-col` on `SheetContent` | Establishes the vertical flex context. Without this, children stack but do not constrain height. |
| `shrink-0` on header/footer | Prevents header/footer from shrinking when content overflows. |
| `flex-1` on scroll container | Claims all remaining vertical space. |
| `min-h-0` on scroll container | **CRITICAL** — without `min-h-0`, a flex child's intrinsic content height prevents `overflow-y` from activating. This is the single most-common cause of iOS scroll failure. |
| `overflow-y-auto` on scroll container | Activates scroll only when needed. `scroll` would always show a scrollbar; `auto` is correct. |
| `overscroll-contain` on scroll container | Prevents the parent page from rubber-banding when the operator hits the end of the drawer's scroll. |
| `WebkitOverflowScrolling: 'touch'` (inline style) | iOS Safari momentum scrolling. Without this, scroll is sticky and pixel-by-pixel. With this, scroll feels native. |

#### Forbidden drawer patterns

- ❌ `h-full` on a child of `SheetContent` without `flex-col` — collapses scroll context
- ❌ `position: absolute` children inside the scroll container — they escape the flex flow
- ❌ Multiple nested `overflow-y-auto` containers — operators don't know which one will scroll
- ❌ Drawer height that varies with content (`h-auto`) — gives operators inconsistent open behavior
- ❌ `position: sticky` on items inside the scroll container — iOS Safari renders sticky with bugs inside `position: fixed` ancestors

---

## III. Thumb-zone prioritization (where elements live)

The screen divides into three zones. Mobile UI rules where each control type belongs.

```
┌─────────────────────────────────┐
│  TOP ZONE (passive only)        │   ← Logo, hamburger, current-context label,
│  ~0–25% from top                │     notification bell, account avatar
├─────────────────────────────────┤
│                                 │
│  CONTENT ZONE (scrollable)      │   ← Lists, cards, forms, data
│  ~25–80% from top               │
│                                 │
├─────────────────────────────────┤
│  THUMB ZONE (active actions)    │   ← Primary CTA, bottom-nav, sheet-trigger
│  ~80–100% from top              │     buttons, "Submit", "Approve"
└─────────────────────────────────┘
```

### Placement rules

| Element | Required zone |
|---|---|
| Primary CTA (`Submit`, `Approve`, `Acknowledge`) | Thumb zone (bottom-fixed bar when on a long-scroll form) |
| Bottom-nav tabs (if used) | Thumb zone, full-width |
| Hamburger trigger | Top zone, left |
| Notification bell | Top zone, right |
| Account/profile avatar | Top zone, far right |
| Search input | Top of content zone (sticky if list is long) |
| Filters | Top of content zone |
| Secondary actions ("Reject", "Cancel", "More") | Thumb zone in a sheet, or in a `…` menu in the top-right |

### Sticky bottom bar — when required

For any view where the operator's primary action requires scrolling past the fold (Daily Report form, Incident form, Inspection checklist), the primary CTA MUST be sticky at the bottom in the thumb zone:

```jsx
<div className="sticky bottom-0 left-0 right-0 bg-white/95 backdrop-blur border-t px-4 py-3 z-30">
  <Button className="w-full h-12" data-testid="primary-cta-button">
    Submit Daily Report
  </Button>
</div>
```

The sticky bar must:
- Be opaque enough to obscure scroll content behind it (`bg-white/95`)
- Be ≥ 56 px tall (button is 48 px, padding makes total ≥ 56)
- Live above any virtual keyboard (use `visualViewport` API if keyboard interferes — see §X)

---

## IV. Collapse behavior

Mobile surfaces use progressive disclosure. The operator sees the summary first; they expand to see detail.

### Domain rows in the drawer

- Default state on fresh login: only `Operations` expanded.
- Tap a collapsed domain → expand inline, drawer scrolls so the tapped domain stays visible.
- Tap an expanded domain → collapse.
- One-tap navigate: tapping a Tier-2 sub-entry collapses the drawer and routes.

### Inline expansion on list views

- Cards in a list (e.g., Daily Reports list) are collapsed by default to show 3 lines of summary.
- Tap card → expands inline to show full summary + actions.
- Only one card may be expanded at a time. Tapping a second card collapses the first.

### Accordions in forms

- Forms with > 6 fields organize into accordions (e.g., Daily Report sections: `Crew`, `Tasks`, `Hazards`, `Photos`, `Signatures`).
- First accordion is auto-expanded.
- Tapping the next section auto-collapses the previous (one-at-a-time discipline).

---

## V. Scroll governance

Every scroll container in the mobile experience must declare its contract.

### The four scroll contracts

| Contract | Used for | Required classes |
|---|---|---|
| **Page scroll** | The main app body scrolls vertically | `<body>` default — no special classes; never `overflow-hidden` on body |
| **Drawer scroll** | Sidebar drawer content | `flex-1 min-h-0 overflow-y-auto overscroll-contain` + iOS touch |
| **Sheet scroll** | Bottom-sheet content (modals on mobile) | Same as drawer, but with `max-h-[85vh]` |
| **List scroll** | A horizontally-scrolling chip row | `overflow-x-auto overscroll-x-contain snap-x snap-mandatory` |

### Forbidden scroll patterns

- ❌ Nested page-scroll inside page-scroll (parent + child both `overflow-y-auto` without sticky boundaries)
- ❌ Horizontal scroll inside vertical scroll without snap-points
- ❌ Scroll containers without a visible "more content below" affordance when overflow exists (use a 16-px gradient fade at the container's bottom edge)
- ❌ Pull-to-refresh on operational views (operators trigger refreshes deliberately via a refresh control, not by gesture)

### No-scroll-trap doctrine

A scroll trap is any state where the operator scrolls in a direction and the scroll never reaches a definitive end. Common causes:

- A list that auto-loads infinitely with no "End of results" marker → **violation**. All lists must show `End of results · {n} items` after the last item.
- A drawer that scrolls past the last item and rubber-bands → **violation**. Use `overscroll-contain`.
- A modal that allows scrolling outside the modal → **violation**. Body must be `overflow-hidden` when a modal is open.
- A keyboard-pushed view where the input is above the keyboard but the submit button is below it → **violation**. See §X.

---

## VI. Sheet vs Modal — when to use which

These two patterns are confused in the current codebase. Phase IV-A locks the distinction.

### Bottom sheet — used when

- The action requires showing context AND collecting input (e.g., `Reject Daily Report` requires showing the report context AND a reason field)
- The action is reversible and the operator may want to peek at the underlying view
- The content height is variable
- Default height: `max-h-[85vh]`, `min-h-[40vh]`
- Dismissable by swipe-down, tap-outside, or explicit Cancel button

### Modal — used when

- The action is binary (Confirm or Cancel) with one sentence of consequence
- The action is irreversible (close incident, delete draft, force-close job)
- Tier 4 escalation acknowledgment (full-screen behavior)
- Default size: centered, `max-w-md`
- NOT dismissable by tap-outside for Tier 4+ — requires explicit acknowledgment

### Forbidden

- Modals on top of modals — if a modal action requires another decision, the first modal is misdesigned
- Sheets on top of sheets — sheet → modal is allowed, sheet → sheet is not
- Full-screen takeovers for anything below Tier 4 — full-screen is for emergencies, not for forms

---

## VII. Touch target sizing

The platform enforces Apple HIG / WCAG AA touch standards strictly.

| Element type | Minimum hit area | Minimum spacing from neighbor |
|---|---|---|
| Primary button | 48 × 48 px | 12 px |
| Secondary button | 44 × 44 px | 12 px |
| Icon button | 44 × 44 px (hit area; visible icon may be smaller, centered) | 8 px |
| List row | 56 × full-width (rows are tap-targets) | 1 px divider |
| Domain row in drawer | 64 × full-width | none (rows abut) |
| Tab in bottom-nav | 64 × (screen-width / tab-count) | none |
| Input field | 48 px tall | 16 px |
| Checkbox / radio | 24 × 24 visible · 44 × 44 hit area | 12 px between options |
| Toggle | 32 × 20 visible · 44 × 44 hit area | 12 px |

### Hit-area extension pattern

When a visible control is smaller than its required hit area, the hit area extends via padding on a wrapper element:

```jsx
<button className="p-3 -m-3"> {/* hit area: 44+ px via padding · negative margin restores layout */}
  <Icon className="w-5 h-5" />
</button>
```

---

## VIII. Mobile spacing rhythm

Mobile uses a **denser** rhythm than desktop because vertical space is precious. But density is rhythmic, not arbitrary.

| Use | Mobile spacing | Desktop equivalent |
|---|---|---|
| Between sections of a page | 16 px | 24 px |
| Between cards in a list | 8 px | 12 px |
| Between fields in a form | 12 px | 16 px |
| Inside a card | 12 px padding | 16 px |
| Page horizontal padding | 16 px | 24 px |
| Between domain header and first sub-entry | 4 px | 8 px |

**Rule:** Mobile spacing is exactly 75% of desktop spacing in the same context. Never less (cramps the eye), never more (wastes vertical space).

---

## IX. Icon usage discipline

Icons aid scanning but never replace verbiage.

### Allowed icon roles

- **Navigation icons** in drawer/bottom-nav (with text label always present)
- **Severity glyphs** (single icon per severity tier — `info`, `bell`, `triangle`, `alert-circle`, `siren`)
- **Inline state indicators** in dense tables (one column, max)
- **Action-button decorations** ONLY when the verb is in the canonical list AND the icon is semantically tight (e.g., `paperclip` for `Attach`, `download` for `Download`)

### Forbidden icon uses

- ❌ Icon-only buttons in any primary action role
- ❌ Icons next to text labels when they don't add semantic information (e.g., a rocket next to "Launch")
- ❌ Multiple icons in a single button or row
- ❌ Decorative emoji-style icons in operational views
- ❌ Icons that change color/animation as the *only* state signal (color-blind operators)

### Icon library discipline

The platform uses one icon library: `lucide-react`. No mixing with `react-icons`, FontAwesome, Material Icons, or custom SVG outside of severity glyphs. Mixing libraries creates visual inconsistency in stroke weight and grid.

---

## X. iOS Safari governance (the strictest constraint)

iOS Safari is the most-restrictive browser the platform supports. Every mobile behavior is tested on iOS Safari before any other browser.

### iOS Safari known constraints — codified

| Constraint | Mitigation in this platform |
|---|---|
| Children of `position: fixed` do not auto-scroll | Use the §II drawer scroll pattern with `min-h-0` and `WebkitOverflowScrolling: 'touch'` |
| `100vh` excludes browser chrome inconsistently | Use `100dvh` (dynamic viewport height) or JS measurement via `window.innerHeight` |
| Tap delay (~300 ms historic, mostly gone but still present in some configs) | Use `touch-action: manipulation` on interactive elements |
| Bounce/rubber-banding at scroll boundaries | `overscroll-behavior-contain` on every scroll container |
| Pinch-zoom on input focus | `viewport` meta tag includes `maximum-scale=1.0, user-scalable=no` on operational pages |
| Date/time inputs render natively | The platform uses custom date/time pickers from shadcn (not native `<input type="date">`) to ensure cross-platform consistency |
| `backdrop-filter: blur(…)` is performance-heavy | Limited to 1 use per screen at ≤ 12 px blur radius |
| Safe-area insets at notch/home-indicator | Use `env(safe-area-inset-*)` for all bottom-fixed bars |

### Keyboard-safe behavior

When the on-screen keyboard appears, the platform must:

1. Keep the focused input visible (scroll it into view above the keyboard).
2. Keep the primary CTA visible (sticky bottom bar lifts above the keyboard via `visualViewport` API).
3. Never allow the keyboard to obscure the input being typed into.
4. Never allow the keyboard to dismiss spontaneously while typing.

Implementation pattern (reference for Phase IV.A.1):

```jsx
useEffect(() => {
  const handler = () => {
    const vv = window.visualViewport;
    if (!vv) return;
    document.documentElement.style.setProperty(
      '--keyboard-offset',
      `${window.innerHeight - vv.height - vv.offsetTop}px`
    );
  };
  window.visualViewport?.addEventListener('resize', handler);
  window.visualViewport?.addEventListener('scroll', handler);
  return () => {
    window.visualViewport?.removeEventListener('resize', handler);
    window.visualViewport?.removeEventListener('scroll', handler);
  };
}, []);
```

Sticky bottom bar uses `transform: translateY(calc(-1 * var(--keyboard-offset, 0px)))`.

---

## XI. Bottom-nav governance

The platform may use a bottom-nav (mobile-only) for the field portal and for the admin portal's mobile drawer alternative on small phones. When used:

### Bottom-nav rules

| Aspect | Specification |
|---|---|
| Number of tabs | 3, 4, or 5 — never 6, never 2 |
| Tab order | Operational frequency, left-to-right (most-used leftmost) |
| Visible tab content | Icon (24 px) + label (≤ 8 chars) |
| Active state | Stripe-color icon tint + slate-900 label (no full color fill) |
| Height | 64 px + safe-area-inset-bottom |
| Position | `fixed bottom-0` with `env(safe-area-inset-bottom)` padding |
| Z-index | `z-30` (below modals, sheets, drawers) |

### Bottom-nav is NOT for

- The 6 admin domains (those live in the drawer; bottom-nav is too few tabs)
- Domain switching with > 5 destinations
- Quick actions (`Submit`, `Acknowledge`) — those are sticky CTAs, not nav

### Field portal bottom-nav (canonical example)

```
[ Jobs ]  [ Reports ]  [ Pre-Op ]  [ Incidents ]  [ Me ]
```

Five tabs, all operational, all field-frequent. `Me` carries account + notifications.

---

## XII. Sticky-header doctrine

Sticky headers are powerful and dangerous. They give the operator persistent context; they also consume scarce vertical space.

### Sticky-header allowed cases

1. **The main top-bar** (logo, hamburger, current-context) — `sticky top-0 z-30`, ≤ 56 px tall.
2. **Page H1 + filters** on list views with > 1 screen of content — `sticky top-14 z-20`, ≤ 80 px tall.
3. **Active-record summary** when scrolling inside a long form (e.g., the Daily Report header stays visible while scrolling the body).

### Sticky-header forbidden cases

- ❌ Sticky banners for Tier 0–1 informational messages (they earn no sticky)
- ❌ Sticky promotional bars (the platform has no promotions)
- ❌ Multiple sticky elements totaling > 144 px vertical (more than 25% of small-phone viewport)
- ❌ Sticky elements that animate height on scroll (visual jitter)

### Sticky-header collapse on scroll

For the page H1 + filters sticky, the H1 may collapse to a 32-px compact title after the operator scrolls > 240 px. The collapse is a single discrete state change (no smooth shrinking), with a 150 ms cross-fade.

---

## XIII. Operational psychology of mobile UI

Mobile operators are not "users on small screens." They are:

- **Time-constrained** — every extra tap is a tax on their shift.
- **Vision-constrained** — sun glare, dust, sweat on lens — calm dark elements on light backgrounds outperform light-on-dark in field conditions.
- **Attention-constrained** — they are likely doing something physical while glancing at the screen. Critical info must register in ≤ 2 seconds.
- **Cognitively loaded** — they hold the operational picture in their head; the platform must not also demand cognitive load to operate.
- **Often interrupted** — a phone call, a coworker, a fall hazard — the platform must preserve in-progress work robustly (autosave, draft state, no destructive surprises).

### The 2-second test

For every mobile surface, ask: "If the operator looks at this for 2 seconds and then has to look away, can they (a) know what the platform wants from them, and (b) know what they were doing when they look back?"

If the answer to either is no, the surface fails.

---

## XIV. Anti-patterns observed (must not recur)

| Anti-pattern | Where it appeared | Status |
|---|---|---|
| Drawer with all 29 entries equal-weight, no scroll, bottom items unreachable | Old `AdminShell.jsx` | ✅ Fixed in IV.A.0 (scroll) · pending IV.A.1 (hierarchy) |
| Modal opens on top of drawer | (none currently) | 🟡 Codified as forbidden |
| Sticky bar obscured by iOS keyboard | (none currently) | 🟡 `visualViewport` pattern required for any future sticky CTA on form views |
| Pull-to-refresh accidentally triggered while scrolling lists | (none currently — RR disabled) | 🟡 Stays disabled platform-wide |
| Native `<input type="date">` showing inconsistent UI across iOS / Android | Some legacy forms | 🟡 Migrate to shadcn date picker in Phase IV.A.5 |

---

## XV. Codified iOS sidebar scroll fix — Phase IV-A.0

The exact change shipped this iteration:

**File:** `/app/frontend/src/components/ui/sheet.jsx`

**Change:** `SheetContent` is now a flex column. The body wrapper is a `flex-1 min-h-0 overflow-y-auto overscroll-contain` container with `WebkitOverflowScrolling: 'touch'`. The header is `shrink-0`.

**Test:** `/app/backend/tests/pw_suite/test_admin_mobile_nav_scroll.py`
- Asserts the scroll container exists with overflow-y `auto` or `scroll`.
- Asserts the last sidebar entry becomes visible after a programmatic scroll-to-bottom.
- Skipped on desktop and iPad viewports (mobile-only regression).

**Status:** 2 passed, 4 skipped at iteration close.

This test is now part of the pre-deploy gate. Any future change to `sheet.jsx`, `AdminShell.jsx`, or the drawer styling that breaks the assertion will fail deploy.

---

## XVI. Enforcement

- **Pre-deploy gate:** The Playwright mobile suite runs on every deploy. Mobile scroll regression = deploy block.
- **PR review checklist for any mobile-touching PR:**
  - Touch target ≥ 44 × 44? · Spacing ≥ 8 px?
  - Thumb-zone placement honored?
  - Drawer scroll pattern (§II) preserved?
  - Sticky stack within 144 px total?
  - iOS Safari tested in pre-merge (Playwright iPhone 13 viewport)?
- **Quarterly mobile review:** Platform engineering tests the entire admin portal on iPhone SE (smallest supported), iPhone 13, iPad Mini, iPad Pro, and Android (Pixel 7). Findings are doctrine amendments.

---

## Verdict

🟢 **MOBILE NAVIGATION DOCTRINE LOCKED · iOS SAFARI BUG REGRESSION-ARMED.** The platform's mobile experience is now governed by explicit, measurable, testable rules. The drawer scroll bug that shipped for weeks is now structurally impossible to reintroduce without breaking the deploy gate.
