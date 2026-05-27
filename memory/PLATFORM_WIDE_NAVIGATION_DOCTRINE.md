# Platform-Wide Navigation Doctrine — Phase IV-BETA

**Iteration:** iter437 · Phase IV-BETA · 2026-02
**Status:** 🟢 BINDING ON ALL PORTAL NAVIGATION SURFACES
**Inherits from:** `SIDEBAR_REARCHITECTURE.md` · `MOBILE_NAVIGATION_STANDARD.md` · `CROSS_PORTAL_CONSISTENCY_STANDARD.md`

The MASCI platform has seven authenticated portals. Each portal's navigation must feel like a chapter of one book — not seven separate books. This doctrine binds the navigation contract platform-wide.

---

## I. The seven portal navigation surfaces

| Portal | Shell file (current/target) | Primary domain | Notes |
|---|---|---|---|
| Admin | `AdminShell.jsx` + `SideNavV2.jsx` (Phase IV.A.1) | OPERATIONS (red) | V2 shipped, flag-gated |
| PM | `PmShell.jsx` → `PmShellV2` (Phase IV-BETA.1) | PROJECT OPERATIONS (red) | V2 lands this phase |
| HR | `HrShell.jsx` (pending Phase IV-BETA.2) | WORKFORCE (blue) | V2 in Phase IV-BETA.2 |
| Dispatch | `DispatchShell.jsx` (pending) | DISPATCH (amber) | V2 in Phase IV-BETA.3 |
| Safety | `SafetyShell.jsx` (pending) | INCIDENTS (orange) | V2 in Phase IV-BETA.3 |
| Field Leadership | `FieldLeadershipShell.jsx` (pending) | DAILY FIELD (red) | V2 in Phase IV-BETA.4 |
| Driver / Dispatch driver | `DriverShell.jsx` (pending) | DAILY DRIVING (slate) | V2 in Phase IV-BETA.4 |

Each shell wraps the same primitives (Sheet, top-bar, sidebar slot, body slot) — only the domain map and portal accent differ.

---

## II. The navigation contract (every portal must satisfy)

### A. Top-bar (z-30)

| Slot (left → right) | Element | Required? |
|---|---|---|
| 1 | Hamburger trigger (mobile / iPad portrait) | YES (`lg:hidden`) |
| 2 | MASCI logo + lockup | YES |
| 3 | Breadcrumb (portal name + page title) | YES |
| 4 | Global search input (desktop) · search icon (mobile) | YES |
| 5 | PortalSwitcher (dropdown of accessible portals) | YES |
| 6 | NotificationBell | YES |
| 7 | OfflineIndicator | YES |
| 8 | SystemHealthBadge (admin scope, hidden on lower portals) | OPTIONAL |
| 9 | Home link to public Hub | YES |
| 10 | Change Password link | YES |
| 11 | Sign Out button | YES |

Top-bar height: 56 px. Border-bottom: 1 px slate-800. NO saturated portal color in the top-bar background — chrome is platform-neutral.

### B. Sidebar (z-20, desktop only)

| Aspect | Specification |
|---|---|
| Width | `w-64` (256 px) |
| Position | `sticky top-14` (below top-bar) |
| Background | `bg-slate-900` |
| Border | `border-2 border-slate-800 rounded-md` |
| Content | `<SideNavV2>` (per-portal subclass) |
| Footer | `<BackendVersionBadge>` only (slate-400, mono, tiny) |

### C. Mobile drawer (z-50)

| Aspect | Specification |
|---|---|
| Width | `w-72` (288 px) portrait · `w-80` (320 px) landscape |
| Background | `bg-slate-900` |
| Border | NO border-right stripe (saturated borders eliminated) |
| Layout | `flex flex-col` |
| Header (Tier 0) | `shrink-0`, portal name, close button |
| Body (Tier 1) | `flex-1 min-h-0 overflow-y-auto overscroll-contain` + `WebkitOverflowScrolling: 'touch'` |
| Footer rail (Tier 2) | `shrink-0`, cross-portal pinned items |

### D. Sidebar content (`<SideNavV2>`)

| Aspect | Specification |
|---|---|
| Outer | `<nav className="space-y-3 p-3" data-testid="{portal}-side-nav">` |
| Domain count | Per-portal: 5–7 domains (PM has 6, Admin has 6) |
| Domain row | 2-px stripe left · icon · mono-uppercase label · slate-500 subline · chevron |
| Active domain row | `bg-slate-800/60` background tint at 5% — NEVER saturated portal color |
| Child row | Indented 12 px · `min-h-[44px]` · icon (small) · label · slate-500 subline · `bg-slate-800 text-white` when active |
| Footer rail | `pt-3 mt-3 border-t border-slate-800` · `Pinned` label · cross-portal items |
| Persistence | `localStorage["masci.{portal}.sidebar.openDomains"]` = array of expanded domain IDs |

---

## III. Cross-portal navigation patterns

### A. PortalSwitcher

The PortalSwitcher dropdown lives in every portal's top-bar. Behavior:

- Lists only the portals the operator's account has tokens for.
- Current portal is highlighted with the domain stripe color.
- Clicking a portal navigates to `/{portal}` (the portal's overview), never deep-linking.
- Switch action persists the current portal's sidebar state but does not transfer it.
- Switch is logged to `admin_audit` (every portal switch is auditable).

### B. Footer rail (cross-portal pinned)

Items pinned in EVERY portal's sidebar footer:

| Item | Route | Available in |
|---|---|---|
| My Tasks | `/tasks` | All portals |
| Guidance | `/guidance` | All portals |

PM portal adds PO Requests to its Financials & Cost domain rather than the footer rail (operational placement per PM-specific frequency).

### C. Sidebar state independence

Each portal's sidebar state is independent (different localStorage keys). Switching from Admin to PM does not collapse Admin's expanded domains. This preserves multi-role operator muscle memory.

---

## IV. Mobile navigation entry points

### A. Drawer

The primary nav entry on mobile. Same trigger position across all portals (top-left hamburger).

### B. Bottom-nav

NOT used in Admin or PM portals (drawer is sufficient).

Bottom-nav IS appropriate for:
- Field Leadership portal (field-first, simple 4-tab nav: Jobs · Reports · Pre-Op · Me)
- Driver portal (4-tab: Today's Routes · Pre-Op · Incidents · Me)

When used, bottom-nav follows the rules in `MOBILE_NAVIGATION_STANDARD.md` §XI.

### C. Push notifications

Push deep-links route directly to the actionable surface, NOT to the portal overview. The drawer/sidebar state is unaffected by deep-link navigation.

### D. Cross-portal deep links

A notification email links to a `{portal}/{route}/{id}` URL. The frontend:
1. Validates the operator's token for that portal.
2. If valid → route directly.
3. If invalid → redirect to `/sign-in?return={url}` (universal sign-in restores intent).

---

## V. Navigation accessibility

| Requirement | Implementation |
|---|---|
| Keyboard navigation | Tab cycles through top-bar → sidebar → main content in DOM order |
| Skip-to-content link | `<a href="#main">Skip to main content</a>` at top of every shell (visually hidden until focused) |
| ARIA labels | Hamburger: `aria-label="Open navigation"` · Active domain row: `aria-current="page"` |
| Focus indicators | Visible ring on focus (`focus-visible:ring-2 ring-slate-400`) |
| Color contrast | All text passes WCAG AA against its background (per `OPERATIONAL_VERBIAGE_DOCTRINE.md` doctrine — verbiage doctrine assumes contrast compliance) |
| Touch targets | 44 × 44 minimum, enforced in component governance |

---

## VI. Forbidden navigation patterns

| Anti-pattern | Why forbidden |
|---|---|
| Bottom-nav with > 5 tabs | Each tab gets too small, label truncates |
| Bottom-nav with > 5 tabs | Each tab gets too small, label truncates |
| Hamburger menu on desktop | Drawer is mobile-only · desktop has persistent sidebar |
| Sidebar that horizontally collapses (icon-only mode) | Hides operational context · re-introduces cognitive lookup |
| Sticky promotional banners in navigation | The platform has no promotions |
| Auto-rotating sidebar entries | Operators expect stable surfaces |
| Mega-menus | Sub-entries belong in the sidebar's Tier 2, not in a popover-over-everything menu |
| Right-rail nav | Forbidden — right is reserved for content actions |
| Floating action button | No FAB in any portal |

---

## VII. Cross-portal URL conventions

| Pattern | Used for |
|---|---|
| `/{portal}` | Portal overview |
| `/{portal}/{domain-or-route}` | First-class portal surface |
| `/{portal}/{route}/{id}` | Detail view |
| `/tasks` (no portal prefix) | Cross-portal pinned: my tasks |
| `/guidance` (no portal prefix) | Cross-portal pinned: guidance |
| `/po-requests` (no portal prefix) | Cross-portal: PO requests |
| `/project-health` (no portal prefix) | Cross-portal: project health |
| `/asset-transfers` (no portal prefix) | Cross-portal: asset transfers |
| `/sign-in` | Universal sign-in |

Cross-portal routes (no `/{portal}` prefix) are accessible from any authenticated portal that has at least one token allowing them.

---

## VIII. Deep-link integrity

Every URL must be:

1. **Bookmarkable** — a PM bookmarks `/pm/incidents/abc-123` and the URL works tomorrow.
2. **Shareable** — a PM emails a colleague the URL; colleague signs in and lands directly on the surface.
3. **Push-targetable** — the notification email links exactly to the surface that needs action.
4. **Persistent across redeploys** — URL schema changes require a 60-day deprecation window + redirects.

The deploy gate (Phase IV-BETA.4) verifies that every URL in built bundles maps to a registered Route in `App.js` AND has an entry in the corresponding `{portal}_INFORMATION_PRIORITY_MAP.json`.

---

## IX. Portal-switching state preservation

When an operator switches portals:

| State | Behavior |
|---|---|
| Current scroll position | Lost (new portal has its own surface) |
| Open filters / search | Lost (filters are portal-scoped) |
| Sidebar open domains | Preserved per-portal (each portal's state independent) |
| Notifications | Preserved (single notification source) |
| Draft form data | Preserved if the form was within the current portal — drafts auto-restore on return |

---

## X. Operator-trust principles for platform navigation

1. **The hamburger is always top-left on mobile.** Across every portal.
2. **The Sign Out button is always top-right.** Across every portal.
3. **The PortalSwitcher is always to the left of NotificationBell.** Across every portal.
4. **The active domain is always visually distinguishable in ≤ 1 second of glancing.** Stripe + tint.
5. **The same URL pattern works in every portal.** No portal-specific URL trick.

---

## Verdict

🟢 **PLATFORM-WIDE NAVIGATION DOCTRINE LOCKED.** Every portal's navigation surface — current and future — derives from this single contract. Operators experience one nav model across seven portals.
