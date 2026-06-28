# MASCI Operational Design System

**Status:** ✅ RATIFIED · Track 18.06 source of truth
**Date:** 2026-02-10
**Authority:** Every future track must conform to this document.

> One visual language. One interaction language. One status language.
> One spacing system. One card system. One page rhythm. No one-off UI.

---

## §1 — Page Anatomy

Every operational page follows this rhythm (top → bottom):

1. **Workspace identity** — top-bar kicker (`MASCI · {Workspace}`).
2. **Page title** — Title Case, `<h1>` weight, single line whenever possible.
3. **Subtitle / purpose line** — sentence case, ≤ 100 chars.
4. **Status chip** — when the page has a binary or graded operational state.
5. **Primary CTA** — top-right; one obvious next action.
6. **Key cards / tiles** — operational signals first, decorative metrics never.
7. **Secondary context** — supporting reads.
8. **Right Rail** — related records · open actions · audit timeline (Track 18.00 Phase D).
9. **Guidance / next-step affordance** — link to the relevant Operational Guidance Center article when the page is heavy.

Sections 1–4 are **required**. Sections 5–9 are required only when operationally meaningful.

---

## §2 — Header Standard

| Slot | Style |
|---|---|
| Brand strip kicker | `font-mono text-[10px] uppercase tracking-[0.22em]` |
| Workspace identity | `MASCI · {Title-Case Workspace}` |
| Breadcrumb chevron | `›` U+203A |
| `<h1>` page title | `font-display text-2xl sm:text-3xl font-black` |
| Subtitle | `text-slate-600 text-sm` |
| Primary CTA | right-aligned, Title Case label |
| Secondary CTA | ghost/outline, right of primary or under it on mobile |
| Back link | `BackLink` component, never one-off |

Top-bar branding never says `Hub`, `Console`, or `Portal` in user-visible text (Track 18.04 lock).

---

## §3 — Card Anatomy

A card must answer **three questions in one glance**: *what is this · what's the state · what can I do*.

| Slot | Required | Notes |
|---|:---:|---|
| Icon (16–24px lucide) | ✅ | Single icon, never decorative emoji |
| Title (Title Case) | ✅ | Single line, never abbreviates a workspace name |
| Status chip | when state matters | One of the canonical statuses (§5) |
| Key value / metric | when card represents a metric | Single big number; never a chart inside a card |
| Supporting detail | optional | Sentence-case prose, ≤ 100 chars |
| Source/timestamp | when number is calculated | "As of HH:MM" or "Updated just now" |
| Primary action | ✅ when actionable | One CTA per card |
| Secondary action | rare | Use only when both actions are truly equal |

**Forbidden:** decorative-only cards · cards that exist only to fill grid space · two competing CTAs.

---

## §5 — Status Language (canonical registry)

| Status | Color band | Icon | Meaning | User action |
|---|---|---|---|---|
| **Ready** | green | check-circle | Eligible · approved · healthy | No action required |
| **Needs Attention** | amber | alert-circle | Drift detected; not blocking yet | Review soon |
| **Action Required** | red | alert-triangle | Operator must act now | Click through to act |
| **Watch** | slate | eye | Tracking; not actionable | Monitor |
| **Blocked** | red | x-circle | Cannot proceed | Resolve upstream |
| **Open** | slate | circle | Active record; in progress not yet started | Begin work |
| **In Progress** | blue | clock | Active, owned, moving | Continue |
| **Complete** | green | check | Finished | Archive / next |
| **Pending Review** | amber | clipboard-check | Submitted, awaiting reviewer | Reviewer acts |
| **Restricted for Your Role** | slate | lock | Role does not have access | Switch role or stop |

**No color without words.** Every chip carries a label. **No random reds.**

---

## §6 — Color System

| Color | Use | Forbidden use |
|---|---|---|
| Red (`#C8102E`) | Blocking · urgent safety · operational stop | Decorative accents · "branded" buttons |
| Amber | Attention · review · soon | "Warning" without action |
| Green | Ready · complete · healthy | Generic "go" |
| Blue / Slate | Informational · neutral context | Pretending to be brand |
| Purple | HR / Workforce identity | Anywhere outside HR |
| Orange | Transportation / Shop equipment | Anywhere outside transport/shop |
| Gray | Disabled · historical | Live operational data |

Every color in the platform must mean the same thing everywhere.

---

## §7 — Typography System

Aligned with `/app/memory/PLATFORM_CASE_STYLE_GUIDE.md`.

| Element | Style |
|---|---|
| Page `<h1>` | `font-display font-black text-3xl–4xl` · Title Case |
| Section header | `font-display font-black text-xl` · Title Case |
| Card title | `font-bold text-base` · Title Case |
| Body | `text-sm` · sentence case |
| Metadata | `font-mono text-[10–11px] uppercase tracking-[0.18–0.25em]` · Title Case OR ALLCAPS via CSS |
| Button source string | Title Case (CSS handles uppercase tracking where present) |
| Mobile body | minimum 14 px, lighter line-height |

---

## §8 — Spacing System

| Token | Use |
|---|---|
| `px-5 sm:px-8` | page horizontal margins |
| `py-8` | page vertical margin |
| `gap-4` | card grid baseline |
| `gap-x-8 gap-y-4` | section grid (premium feel) |
| `space-y-8` | between distinct sections |
| `space-y-3` | between card body lines |
| `min-h-[44px]` | touch targets |

No cramped UI. No random gaps. No `mb-[7px]` magic numbers.

---

## §9 — Buttons / CTA

| Variant | Use |
|---|---|
| **Primary** | one per page, the operator's obvious next step |
| **Secondary (outline)** | siblings to the primary, never more than 2 |
| **Destructive** | red border + red text, only for irreversible actions |
| **Ghost** | inline within tables / cards |
| **Link** | "View all", "Open guide" |
| **Icon-only** | requires `aria-label` |
| **Disabled** | desaturated, tooltip explains why |

Every button label must be action-oriented Title Case in source. CSS handles uppercase styling where the design calls for it.

---

## §10 — Tables / Lists

- Sticky header on tables > 1 viewport.
- Row height ≥ 44 px.
- Entire row is clickable when the row has a primary "open" action.
- Status chips left of the title column.
- Empty state explains what would have been here.
- Filter bar collapsible on mobile.
- No nested tables. Ever.

---

## §11 — Drawers / Modals

- **Drawer** when supplementary read while staying on the page.
- **Modal** when collecting input that blocks all other actions.
- **Full page** when the task takes > 30s of focused work.
- `Esc` always closes.
- Outside click closes drawers; modals only close via the cancel button.

---

## §12 — Search

- Placeholder: *"Search records, people, equipment…"* (sentence case)
- `/` keyboard hint shown in the placeholder when desktop.
- Grouped results: People · Equipment · Documents · Projects.
- RBAC-safe: no result a user is not allowed to see ever appears.
- No-result state has a "What can I search for?" link.

---

## §13 — Right Rail / Relationships

- Pinned to the right column on ≥ 1024 px.
- Collapsible above 1024 px; stacked below.
- Contains: Recent Activity · Related Records · Open Actions · Audit Timeline.
- Empty states never read "No data" — they read "No related records yet" with the operational explanation.

---

## §14 — Empty States

Every empty state answers:
- **What this area is** (one short sentence)
- **Why it is empty** (cause, not symptom)
- **What to do next** (one CTA or "this is OK")
- **Whether empty is good** (calm tone vs. red alert)

**Banned:** the bare string `"No data"`, `"Nothing here"`, `"Empty"`.

---

## §15 — Loading States

- Use **skeletons** that match the final layout (no spinners on full-page content).
- Spinners are acceptable for inline button-confirm actions only.
- No layout jumping when content lands.

---

## §16 — Restricted States

Use `TxOpsRestricted` / `TxOpsRestrictedData` (Track 18.00 Phase G). Wording: **"Restricted for your role"** (Constitution Article VI).

**Banned:** `Forbidden`, `Unauthorized`, `403`, `Access Denied`, `Admin Console`.

---

## §17 — Error States

Operational language only.

**Banned:** stack traces · raw JSON · `failed to fetch` · `undefined` · `null`.

**Approved:**
- *"This information is not available right now."*
- *"Try again."*
- *"Open related workspace."*
- *"Contact your supervisor if this continues."*

---

## §18 — Guidance Standard

Every major workspace must have a guidance article that teaches **work**, not software. See `OPERATIONAL_GUIDANCE_CENTER_AUDIT.md` (Track 18.04).

---

## §19 — Mobile / Tablet Standard

| Device | Min width | Behavior |
|---|---:|---|
| iPhone SE / small Android | 390 px | Single-column · sticky nav · touch ≥ 44 px |
| iPhone / Android | 414 px | Single-column · slightly wider density |
| iPad portrait | 768 px | Two-column where useful · Right Rail stacks below |
| iPad landscape / 14" laptop | 1024 px | Right Rail visible · two-column primary |
| 16" laptop | 1366 px | Full layout |
| Desktop | 1920 px | Full layout · centered to ~1440 max-width on long-prose pages |
| Ultrawide / monitor | 2560+ | Content centered with intelligent max-width, never stretched |

Design for: gloves · sunlight · dirty hands · one-handed use · truck cab · limited bandwidth.

---

## §20 — Accessibility

- Contrast ≥ WCAG AA on every status/text combination.
- Every interactive element keyboard-accessible.
- Focus rings visible and consistent (Tailwind `ring-2 ring-offset-2`).
- Status never communicated by color alone — always color + label + icon.
- `aria-label` on icon-only buttons.

---

## §21 — Trust Standard

Every number on screen must answer:
1. **Source** — which collection / route produced it
2. **Freshness** — "As of HH:MM" or "Updated just now"
3. **Meaning** — what it represents in operational terms
4. **Action** — what the operator does about it
5. **Confidence** — when computed (e.g. compliance score) the formula is documented in the Guidance Center.

Decorative numbers are removed or downgraded.

---

## Conformance

Track 18.06 audited every authenticated workspace against this system. See
`AUTHENTICATED_WORKSPACE_DESIGN_AUDIT.md` for per-workspace scores.

Every future track must reference this document. Drift is blocked by
`backend/tests/test_track_18_06_operational_design_system.py`.

---

## §22 — Audit Timeline Date Format (Track 18.07 addition)

| Recency | Pattern | Example |
|---|---|---|
| Today | `Today · h:mm A` | `Today · 2:14 PM` |
| Older this year | `MMM d · h:mm A` | `Jun 28 · 2:14 PM` |
| Prior years | `MMM d, yyyy · h:mm A` | `Jun 28, 2025 · 2:14 PM` |
| Detailed audit view | adds timezone abbreviation when available | `Jun 28 · 2:14 PM EST` |

**Banned:** raw ISO strings · uncontextualized "ago" without absolute date on hover · inconsistent month casing (must be `Jun`, not `JUN` or `jun`).

Applies across Transportation, Admin, Operations, HR, Safety, PM, Shop, and Right Rail audit/timeline surfaces.
