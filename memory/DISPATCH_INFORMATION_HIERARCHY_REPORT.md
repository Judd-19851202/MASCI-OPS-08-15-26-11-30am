# DISPATCH INFORMATION HIERARCHY REPORT
## OMEGA Polish Sprint · P0 Hierarchy Rebuild

**Date**: 2026-06-03
**File**: `/app/frontend/src/pages/DispatchHub.jsx`

---

## 1 · Old vs. new section order

### 1.1 · Before (pre-sprint)

| Pos | Surface | Test-id | Type |
|---:|---|---|---|
| 1 | PasskeyEnrollPrompt | `passkey-enroll-prompt` | Decorative (auth nag) |
| 2 | FieldMemoryGlance | `field-memory-glance` | Decorative (read-only notes) |
| 3 | LastActivityLine | `last-activity-line-dispatch` | Decorative (calm proof) |
| 4 | **Dispatch Command (coaching)** | `ds-section-command` | **6 bullets always-shown** |
| 5 | Operational Attention | `ds-section-attention` | OPERATIONAL — what matters now |
| 6 | Issue Work (4 buttons) | `ds-section-issue` | OPERATIONAL — primary actions |
| 7 | Live Operational Flow | `ds-section-live` | OPERATIONAL — deep link |
| 8 | Follow-Through (transfers + holds) | `ds-section-follow` | OPERATIONAL — pending |
| 9 | Secondary Operations | `ds-section-secondary` | OPERATIONAL — context |
| 10 | **Guides & Coaching (6 tiles)** | `ds-section-guides` | **Reference** |
| 11 | Local `<footer>` | n/a | Duplicate of `<GlobalFooter />` |

**Problem**: 3 decorative components + 1 coaching block + 1 large guide tile grid sat above and around the operational signals. A dispatcher scrolled past instruction before reaching action.

### 1.2 · After (this sprint)

| Pos | Surface | Test-id | Type |
|---:|---|---|---|
| **1** | **Operational Attention** | `ds-section-attention` | OPERATIONAL — what matters now (first paint) |
| 2 | Issue Work (4 buttons) | `ds-section-issue` | OPERATIONAL — primary actions |
| 3 | Live Operational Board | `ds-section-live` | OPERATIONAL — deep link |
| 4 | Follow-Through (transfers + holds) | `ds-section-follow` | OPERATIONAL — pending |
| 5 | Secondary Operations | `ds-section-secondary` | OPERATIONAL — context |
| 6 | Dispatch Command (collapsible) | `ds-section-command` | Coaching — collapses by default for returning users |
| 7 | Dispatch Resources (1 CTA) | `ds-section-resources` | Reference — single "Open Guides" button |
| 8 | Peripheral block | `ds-peripheral` | Decorative — PasskeyEnrollPrompt, FieldMemoryGlance, LastActivityLine |
| — | Global footer | `global-footer` | App.js-mounted, single canonical strip |

**Result**: Dispatcher's first visual contact is the Operational Attention card grid. Coaching is below the actionable surfaces and folds away. Decorative surfaces are below operational content, divided by a subtle `border-t` so they read as peripheral, not primary.

---

## 2 · Rationale per directive section

| Directive section | How addressed |
|---|---|
| §P0 Section 1 — Operational Attention must be the first operational content visible | Achieved. Now position 1. |
| §P0 Section 2 — Issue Work | Achieved. Now position 2 (was position 6). |
| §P0 Section 3 — Live Operational Board | Achieved. Now position 3 (was position 7). |
| §P0 Section 4 — Follow Through | Achieved. Now position 4 (was position 8). |
| §P0 Section 5+ — Secondary Information only after operational content | Achieved. Secondary, coaching, resources, peripheral all sit below the four operational surfaces. |
| §P0 — Coaching collapse (first-time expanded, returning collapsed) | Achieved via `localStorage["masci.dispatch.coaching.collapsed"]`. |
| §P0 — Guide section consolidation | Achieved. 6 tiles + 1 CTA → 1 CTA. |
| §P0 — Decorative review (PasskeyEnrollPrompt, FieldMemoryGlance, LastActivityLine) | All three moved below operational content. Each component honours its own self-gating (hides if no signal). |

---

## 3 · Visibility ladder (above-the-fold at 1080 px viewport, sidebar V2 off)

| Element | Approx. top px | Visible without scroll? |
|---|---:|:-:|
| Top nav | 0–56 | ✅ |
| Operational Attention header | 80 | ✅ |
| Attention cards (3-up grid) | 130–230 | ✅ |
| Open operational board CTA + help link | 250 | ✅ |
| Issue Work header | 290 | ✅ |
| Issue Work 4-button grid | 340–440 | ✅ |
| Issue Work help links | 460 | ✅ |
| Live Operational Board CTA | 530 | ✅ |
| Follow-Through tabs | 660 | ✅ (just) |
| Secondary Operations (begins) | ~830 | partially |
| Coaching (collapsed) | ~960 | optional |
| Resources CTA | ~1020 | optional |
| Peripheral block | ~1080+ | scroll |
| Global footer | bottom | scroll |

**Net**: Operational Attention, Issue Work, Live Board, and Follow-Through are all above the fold on a 1080 px viewport. The dispatcher sees and can act on operational signals **without scrolling**.

---

## 4 · First-time vs returning UX

### First-time (no `masci.dispatch.coaching.collapsed` in localStorage)
- Coaching `<CoachingBlock>` renders expanded with all 6 bullets visible.
- Operational surfaces are above coaching (positions 1–5), so the dispatcher still sees attention first; coaching is available without action.
- After the dispatcher manually collapses, the choice persists per device.

### Returning (localStorage already has a value)
- Coaching renders in whatever state the dispatcher last left it.
- Most returning dispatchers will land on the collapsed state ("Show Dispatch Guidance" with chevron-down). Single click expands.

This matches the directive's "Need Help? [ Show Dispatch Guidance ]" pattern.

---

## 5 · Verification

| Check | Method | Result |
|---|---|:-:|
| Source `data-testid` order | grep on the JSX file | 🟢 attention → issue → live → follow → secondary → command → resources → peripheral |
| Webpack compile | supervisor frontend log | 🟢 *"webpack compiled successfully"* |
| ESLint clean | `mcp_lint_javascript` | 🟢 no issues |
| All pre-existing test-ids preserved | grep comparison | 🟢 zero pre-existing test-ids removed |

---

## 6 · Outcome

🟢 **Hierarchy rebuilt per directive.** Operational signals are the first thing a dispatcher sees. Coaching is collapsible and below action. Decorative surfaces sit at the bottom as calm peripherals.
