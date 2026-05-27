# Sidebar Re-Architecture — Phase IV-A

**Iteration:** iter437 · Phase IV-A · 2026-02
**Status:** 🟡 STRUCTURE LOCKED · IMPLEMENTATION IN PHASE IV.A.1
**Extends:** `NAVIGATION_REARCHITECTURE_PLAN.md` (Phase IV-0) with concrete two-tier behavior + coaching

The Phase IV-0 nav plan locked the 10-domain map. This document locks the exact visual + interaction behavior of the new sidebar.

---

## Target structure (6 domains for daily ops · 4 collapsed for governance)

The directive specifies 6 primary domains with a 7th cluster for system + governance. We collapse the Phase IV-0 list (10 domains) into the directive's 6+1 grouping:

| Stripe | Domain | Coaching subline | Phase-IV-0 mapping |
|---|---|---|---|
| 🟥 red | **OPERATIONS** | Field activity across all active projects | `operations` |
| 🟦 blue | **WORKFORCE** | People, certifications, time-off, onboarding | `hr-workforce` + `identity-access` |
| 🟨 amber | **EQUIPMENT & FLEET** | Asset lifecycle, maintenance, pre-op, suppliers | `fleet-equipment` |
| 🟪 violet | **COMMUNICATIONS** | Email routing, notifications, escalation flow | `communications` |
| 🟧 orange | **SAFETY & COMPLIANCE** | Incidents, audits, certifications, OSHA | `safety-compliance` |
| ⬛ slate | **SYSTEM & GOVERNANCE** | Storage, backups, deploy health, observability | `data-storage` + `system-health` + `governance` |

`dispatch-logistics` lives under OPERATIONS as a sub-section (not its own top-level domain) because dispatch is an operational sub-flow, not a separate competence.

---

## Two-tier behavior

### Tier 1 · Domain row (always visible)

```
[2px stripe] [icon] DOMAIN NAME            [count badge ▸]
            Coaching subline (max 12 words)
```

- Height: 56 px desktop · 64 px mobile (≥ 44 px touch target enforced)
- Whole row is clickable · expands tier 2 inline
- Count badge: appears only if the domain has a pending-action count (e.g., "3 reviews waiting")
- Active domain: stripe-color background tint at 5% opacity (subtle)

### Tier 2 · Sub-entries (revealed when domain is expanded)

```
    ─ Daily Reports
    ─ Inspections
    ─ Meetings
    ─ Operations Events
    ─ Dispatch Activity
```

- Indent: 12 px from domain row
- Height: 40 px desktop · 48 px mobile
- Sub-entries use the same icon set but smaller (14 px) and slate-400 default · slate-100 active

---

## State persistence

The sidebar remembers across page navigations AND tab reloads:

- `masci.admin.sidebar.openDomains` — array of expanded domain IDs (default: `["operations"]`)
- `masci.admin.sidebar.lastDomain` — the last visited domain (used to auto-expand on next load)
- `masci.admin.sidebar.mobileExpanded` — boolean, last state of the mobile drawer

**Default state for a fresh login:** `Operations` expanded, all others collapsed. Mobile drawer closed.

---

## Mobile drawer behavior

| Behavior | Specification |
|---|---|
| Open trigger | Hamburger top-left, ≥ 44 px touch target |
| Width | 288 px (`w-72`) |
| Vertical layout | Flex column · header `shrink-0` · scroll wrapper `flex-1 overflow-y-auto` |
| iOS Safari momentum | `WebkitOverflowScrolling: touch` (FIXED in this iteration) |
| Domain row | Same as desktop · 64 px tall · all 6 visible without scrolling on iPhone 13 |
| Sub-entries | Expand inline · drawer scrolls to keep tapped domain in view |
| Close on navigate | `onNavigate` callback resets `mobileOpen` to false |
| Overscroll | `overscroll-contain` to prevent page-body bounce when scrolling the drawer |

---

## Domain ordering rationale

The order is the **operator's daily rhythm** — most-used-first:

1. **Operations** — the user opens the admin portal to check field activity 80% of the time
2. **Workforce** — second-most-common: HR queries, time-off, certifications
3. **Equipment & Fleet** — daily for shop, weekly for office
4. **Communications** — periodic (every few days) — adjusting email routing, digests
5. **Safety & Compliance** — periodic — incident review, OSHA prep
6. **System & Governance** — last because it's where infrastructure lives — should never compete with operational data

The sidebar order should never be alphabetical. It should mirror operational frequency.

---

## What collapses · what stays visible

By default on mobile, only the 6 domain rows are visible. **No sub-entries are visible until the operator taps a domain.** This is the "≤ 6 things at once" rule.

On desktop, the operator's `lastDomain` is auto-expanded; all others collapsed. The operator can pin multiple domains open if they want — state is remembered.

---

## What this sidebar deliberately removes

- ❌ The flat 29-entry list with all-equal visual weight
- ❌ Per-entry "version badge" footer that bloated the visual base
- ❌ Standalone cross-portal pinned items (Tasks, PO Requests, Guidance) which move to a separate footer rail or top-right widget
- ❌ Section-key dispatch for routing (currently AdminShell takes `section="foo"` prop — moving to auto-detect from URL)
- ❌ All "BETA" / "NEW" / "PREVIEW" badges in the sidebar — they're noise

---

## Implementation phasing

| Step | Scope | Risk |
|---|---|---|
| IV.A.0 (this iteration) | Mobile scroll bug fix + Playwright regression | DONE |
| IV.A.1 | New `<SideNavTier1/2>` components in `AdminShell.jsx` (additive, behind a feature flag) | LOW |
| IV.A.2 | Migrate ordering: 29 flat entries → 6 grouped domains (URL paths unchanged) | LOW · pure visual |
| IV.A.3 | Add state-persistence to localStorage | LOW |
| IV.A.4 | Add coaching sublines per domain | LOW |
| IV.A.5 | Add domain stripe + icon-tint colors | LOW |
| IV.A.6 | Cut feature flag · old flat nav removed | MEDIUM · full operator switch |

Each step is its own PR, < 200 LOC, regression-tested before merge.

---

## Verdict

🟡 **STRUCTURE LOCKED · CODE LANDS IN IV.A.1.** The iOS scroll fix from IV.A.0 ships now (already in this iteration). The two-tier rebuild ships behind a feature flag in IV.A.1 so it can be reverted instantly without a redeploy if anything feels wrong to operators in production.
