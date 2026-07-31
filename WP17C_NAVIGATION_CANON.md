# WP-17C Navigation Canon

Source of truth: `WP17B_NAVIGATION_AUDIT.md`, the locked ledger, and the representative shell implementation.

## Canonical navigation model
Every nav item must define:
- canonical label
- canonical icon concept
- destination
- portal ownership
- usage tier
- role visibility
- permission requirement
- mobile behavior
- active-state behavior
- hidden/deprecated state

## Usage tiers
- **DAILY** — first-class work every day
- **FREQUENT** — used often, but not always first
- **OCCASIONAL** — valuable but lower-frequency
- **ADVANCED** — specialized operational tools
- **ADMINISTRATIVE** — governance/configuration/maintenance
- **CONTEXTUAL** — only from within a task flow
- **HIDDEN** — intentionally not shown in standard nav
- **DEPRECATED** — temporary alias only

## Shared behavior rules
- Desktop sidebar is the canonical authenticated nav.
- Collapsed sidebar must keep recognizable icons and active state.
- Tablet and phone nav must preserve the same hierarchy, not invent a second IA.
- Breadcrumbs reflect IA, not raw URL segments.
- Back navigation returns to the previous meaningful work surface when possible.
- Portal switching is explicit and never mixed into task groups.
- Search can surface hidden/detail destinations but must label them clearly.

## Canonical visibility rules
- Daily/frequent items live in the visible portal sidebar.
- Advanced/admin items can live lower in the sidebar or behind a clear domain group.
- Contextual/detail items do not appear in primary nav.
- Hidden routes may appear only in search, breadcrumbs, or task flows.
- Deprecated aliases are never primary nav entries.

## Representative canonical maps

### Public entry
- **Primary:** Sign in, Training Center, Cheat Sheet
- **Secondary:** company help/contact, start-here onboarding
- **Hidden:** internal compares, debug helpers

### Admin OS
- **Primary domains:** Admin OS, Platform Tools, Business Operations
- **Tiering rule:** posture/search first; daily admin domains second; deep tools third
- **Search-only:** detail pages and hidden admin utilities from `domainMapV3`

### PM
- **Primary domains:** Project Operations, Financials & Cost, Field Coordination
- **Secondary domains:** Document Control, Compliance & Risk, System & Communications
- **Noise rule:** a PM landing may surface the next action, but not every route as a hero card

## Mobile canon
- Same labels as desktop
- No truncated ambiguity like `Ops` when the desktop label is `Operations Control`
- No unscrollable nav trays
- Touch targets >= 44px
- Portal switcher and user/session controls remain accessible without covering content

## Active-state canon
- Exact match for true landings
- Prefix-aware active state for nested pages
- Hidden/detail pages highlight the owning visible destination or domain

## Transportation exception rule
Transportation may resolve the same IA through two path prefixes, but the nav model, labels, and order remain identical.
