# MASCI Role-First Portal Pattern

**Reference standard:** Field Leadership Portal (`/leadership`) — Five-Pillar score 25/25.

**Doctrine:** Every MASCI portal must serve a real operator role. No portal may invent its own visual language. The pattern below is the shared spine; portal-specific tints layer on top via `paletteFor(<role>)`.

---

## The pattern (six parts, in order)

### 1. Role headline
- Top of the page, immediately under the platform chrome.
- Format: `<KICKER lozenge> · <Role>` then a sentence-case bold headline describing what this role does, then a 1-2 line lede.
- Example (FL): `RESTRICTED · CREW DOCUMENTATION` → `Field Leadership` → "Crew accountability, employee documentation, equipment responsibility, recognition, and workforce-management tools for MASCI field leadership."

### 2. Compliance / status lozenge (if applicable)
- Single line in the role tint, immediately under the headline.
- Tells the operator the operational truth contract (e.g. "All forms must be factual and compliant…").
- Optional. Used when the role has a documented compliance constraint.

### 3. First-screen action grid OR project/work list
- The hero region is **always actionable**, never a KPI strip alone.
- Two acceptable shapes:
  - **Action grid** (FL pattern): 3-6 cards, each a one-tap entry point with title + 1-line description + `New Entry →` button.
  - **Work list** (PM pattern proposed in Track 13): scoped to the operator's owned items (my projects, my dailies, my approvals) with click-through to detail.
- KPI tiles, if present, sit BELOW the work list, not above it.

### 4. Recent activity / memory feed
- Lightweight horizontal or compact list of the last 3-5 events the role cares about.
- Format: `<TYPE LABEL>` + `<ID>` + `<one-line summary>` + relative timestamp.
- Source: portal-scoped activity feed (`/api/<role>/recent-activity` or shared `audit_log` filter).

### 5. Honest empty states
- A bare `0` is never acceptable in a content row.
- Required shape: `<count> <noun> — <next-action-sentence>`.
  - Good: "No active projects assigned to this PM. Admin can assign projects from Project Manager Directory."
  - Bad: "0 Active Projects" with no copy.
- Loading: skeleton, never blank.

### 6. Clickable everything
- Every count, every card, every section title — clickable.
- Click destination is the actual list/detail/filtered view, not a duplicate dashboard.
- If a count is shown, the destination MUST exist. No dead cards.

---

## What every MASCI portal inherits (do not override)

| Element | Source | Rule |
|---|---|---|
| Top safety stripe + preview banner | platform chrome | always visible |
| Header (logo, Back/Hub, Search, Bell, Portal switcher, EN/ES, Sign out) | shared components | inherit, do not restyle |
| Role tint | `paletteFor(<role>)` | role-tinted accents only on left-edge stripes / sub-headers / primary CTAs |
| Card shape | `bg-white border border-slate-200 rounded-md p-5 sm:p-7` | always |
| KPI tile shape | `<Tile>` with number + label + status badge | always |
| Section title shape | font-mono `tracking-[0.22em]` kicker + bold headline + lede | always |
| Touch targets | 32 px floor, 44 px for primary actions | RC-1 hardened |
| Translations | `useT()` for every visible string | RC-1 hardened |

---

## What every MASCI portal must NOT do

- ❌ Invent a new theme/color set
- ❌ Open the first screen with operations-paste KPIs that have nothing to do with the role
- ❌ Show a count without a click-through
- ❌ Show a bare `0` in a content row
- ❌ Hide critical role tools behind tabs labeled by resource type instead of by question
- ❌ Embed fleet/trucking data on a non-dispatch portal (and vice versa)
- ❌ Lose the Preview banner, the search bar, or the portal switcher
- ❌ Build a portal that doesn't pass the 5:30 AM 10-second test: *"What does this role need to know / do right now?"*

---

## Decision checklist before any portal merges

1. Can the user answer the **top 5 role questions** within 10 seconds of landing?
2. Is the hero **actionable** (work list or action grid), not passive (KPI strip alone)?
3. Does every visible count **click through** to real data?
4. Are all **empty states** narrative ("No X — next action is Y"), not bare zeros?
5. Does the chrome / typography / palette / spacing match the rest of the platform?
6. Does the page pass the **117-case RC-2 predeploy gate**?

If any of those answers are NO, the portal is not ready.

---

## Field Leadership reference annotation

```
┌─ Safety stripe + Preview banner ─────────────────────────────┐
├─ Header: logo · Home · Back · Search · Bell · LangToggle ──┤
├─ KICKER: RESTRICTED · CREW DOCUMENTATION                    │
│  H1: Field Leadership                                        │
│  Lede: Crew accountability, employee documentation, …        │
├─ Compliance lozenge: "All forms must be factual…"           │
├─ Recent field memory (3-5 rows, type + ID + summary + time)  │
├─ DAILY CREW DOCUMENTATION section                           │
│  ┌─Verbal Coaching──┐ ┌─Employee Write-Up─┐ ┌─Attendance──┐ │
│  │ 1-line desc      │ │ 1-line desc        │ │ 1-line desc │ │
│  │ [New Entry →]    │ │ [New Entry →]      │ │ [New Entry →]│ │
│  └──────────────────┘ └────────────────────┘ └─────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

Every portal rebuild in Track 13 (and beyond) inherits this structure.
