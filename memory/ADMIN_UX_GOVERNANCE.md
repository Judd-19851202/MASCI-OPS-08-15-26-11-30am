# Admin UX Governance — Phase IV-A

**Iteration:** iter437 · Phase IV-A · 2026-02
**Status:** 🟢 DOCTRINE LOCKED · iOS SCROLL BUG FIXED + REGRESSION-LOCKED
**Supersedes / extends:** `UX_GOVERNANCE_STANDARD.md` (Phase IV-0)

The Phase IV-0 UX standard locked component-level rules (buttons, spacing, severity colors). This Phase IV-A doctrine locks the next layer up — **information hierarchy, cognitive weight, and operational coaching at the admin-portal level**.

---

## The five doctrine pillars

| Pillar | What it means | Failure looks like |
|---|---|---|
| **Hierarchy over uniformity** | Important things look more important. Infrastructure recedes. | All 29 sidebar entries had identical weight, color, font size. |
| **Coaching over labeling** | Every domain answers "What is this and why am I here?" in one calm sub-line. | Sidebar entries had cryptic 3-word labels with no operational context. |
| **Progressive disclosure** | The mobile user sees ≤ 6 things at once. Detail comes when they enter a domain. | Mobile drawer showed all 29 items at full visual weight. |
| **Calm signal density** | The eye knows where to look without thinking. No competing reds, no equal-weight indicators. | Red headers, red active states, red dividers, red badges — all at the same intensity. |
| **Field awareness** | Foremen on iPads, mechanics with gloved hands, dispatchers under time pressure are the default user — not the developer at a 27″ monitor. | iOS Safari sidebar scroll broken for weeks · 44px touch targets violated · hover-only interactions. |

---

## Visual weight ladder (top → bottom · descending importance)

| Tier | Examples | Treatment |
|---|---|---|
| **Tier 0 · Operational signal** | Cluster capacity banner · critical-severity badges | Full saturation · top of view · sticky |
| **Tier 1 · Domain headers** | "Operations", "Workforce", "Equipment & Fleet" | Mono uppercase eyebrow · semantic color hint · h2 size |
| **Tier 2 · Active section title** | Current page H1 + breadcrumb | Strong font weight · slate-900 · no color tint |
| **Tier 3 · Domain sub-nav entries** | "Daily Reports", "Inspections", "Meetings" | Slate-200 text · slate-800 hover · 14 px font |
| **Tier 4 · Coaching sub-text** | "Track unresolved actions across all portals" | Slate-500 · 11 px · max 12 words |
| **Tier 5 · Infrastructure** | "Deploy Health", "Storage", "Backups" | Visually muted · collapsed by default · grouped under Governance |

If two elements share a tier visually, only one can be operationally important. Pick. Or move one tier down.

---

## Domain color hinting (subtle · semantic · not loud)

Domains carry a tiny 2 px left-edge color stripe and matching icon tint. The stripe is the ONLY chromatic difference between domains. No solid color blocks, no large color fills.

| Domain | Stripe color | Icon tint |
|---|---|---|
| Operations | `#dc2626` (red-600) | red-500 |
| Workforce | `#2563eb` (blue-600) | blue-500 |
| Equipment & Fleet | `#d97706` (amber-600) | amber-500 |
| Communications | `#7c3aed` (violet-600) | violet-500 |
| Safety & Compliance | `#ea580c` (orange-600) | orange-500 |
| System & Governance | `#475569` (slate-600) | slate-400 |

Critical rule: **the stripe is 2 px wide.** It's a navigation cue, not a feature.

---

## Coaching language — every domain answers three questions

For every domain header AND every section page header:

1. **What is this?** — One-sentence purpose.
2. **Who owns it?** — Implicit via permission scope, but if non-obvious, state it.
3. **What do I do here?** — The primary verb the operator will perform.

**Example (Operations domain):**
- Domain header: `OPERATIONS · Field activity across all active projects`
- Subline: `Daily reports, meetings, dispatch activity, accountability tracking.`

**Example (a specific page — Daily Reports):**
- H1: `Daily Reports`
- Subline: `Review and approve field-leadership submissions. Today's submissions are highlighted.`

No marketing copy. No "Empower your team with…". No exclamation marks. The verbiage rules from `TERMINOLOGY_DOCTRINE.md` apply universally.

---

## Information hierarchy on a page (the canonical layout)

Every admin page follows this vertical order — no exceptions:

```
1. Domain breadcrumb (Tier 1 · slate-400 · 10 px mono)
2. Page H1 + coaching subline (Tier 2/4)
3. Primary action (top-right) · ONE button
4. Status / signal strip (only if there's an operational signal · severity banner)
5. Filter / search row
6. Main data surface (table or cards)
7. Empty state OR pagination
8. Secondary actions (footer or "More" menu)
```

If a page needs more than ONE primary action, it's two pages — split it.

---

## Mobile-specific governance

Captured fully in `MOBILE_NAVIGATION_STANDARD.md` (separate doc). Key rule: **the mobile drawer is an operational launcher, not a compressed desktop sidebar.**

---

## The fix shipped in this iteration (Phase IV-A.0)

The directive identified the iOS Safari scroll bug as a P0 mobile blocker. Root cause + fix:

**Root cause:** `<SheetContent>` from shadcn's Sheet primitive is `fixed inset-y-0 h-full` with no internal scroll container. iOS Safari does NOT auto-scroll overflowing children of a `position: fixed` ancestor — the only iOS that does is desktop Safari. With 29 nav entries at ~64 px each, the bottom 60% of the menu was unreachable on iPhone.

**Fix:** Made `SheetContent` a flex column · header is `shrink-0` · sidebar nav lives inside a `flex-1 min-h-0 overflow-y-auto overscroll-contain` wrapper with `WebkitOverflowScrolling: touch` for iOS momentum scroll. New testid `admin-mobile-nav-scroll` for the regression suite.

**Regression locked by:**
- `/app/backend/tests/pw_suite/test_admin_mobile_nav_scroll.py`
- Two assertions on mobile-only viewport:
  - Scroll container exists with `overflow-y: auto` / `scroll`
  - Last nav entry becomes visible after programmatic scroll to bottom
- Both PASS at iteration close — 2 passed, 4 skipped (desktop/iPad correctly skipped)

---

## Enforcement

- Every PR touching an admin page must conform to the visual weight ladder AND the canonical page layout.
- Every PR adding/removing a sidebar entry must update the domain color hint AND the coaching subline.
- Playwright mobile regression must remain green — the iOS scroll guard is now part of the pre-deploy gate via `tests/pw_suite/`.

---

## Verdict

🟢 **DOCTRINE LOCKED · MOBILE BUG FIXED · REGRESSION ARMED.**

This is the canonical admin-UX governance reference from this point forward.
