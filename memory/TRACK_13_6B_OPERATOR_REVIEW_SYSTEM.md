# Track 13.6B · Operator Review System

**Mode:** Preview-only · internal-only · no operator-facing surface introduced.
**Generated:** 2026-06-12 (UTC)

> Specifies the internal review hub (`/_internal/v2-index`) and side-by-side comparison view (`/_internal/v2-compare/:portal`) that satisfy Rules #4 and #5 of Track 13.6B.

---

## 1. Why a review system exists

Per Rule #5: **no portal route may be swapped until the operator has reviewed it on the corresponding Side-by-Side vs Current page.** A persistent review system makes that approval gate visible, durable, and easy to revisit.

---

## 2. `/_internal/v2-index` — Review Hub

### 2.1 Purpose

Single internal landing that lists every V2 preview lane (operational and planned), with metadata and quick links. Not linked from any operator navigation. Direct URL only.

### 2.2 Contents (today)

| Section | Entries |
| --- | --- |
| **Operational previews** | PM V2 · HR V2 · Design System Demo |
| **Planned lanes** | Admin V2 · Dispatch V2 · Safety V2 · Shop V2 · Driver V2 |

### 2.3 Per-lane metadata rendered

| Field | Source / shape |
| --- | --- |
| Title | Human-readable portal name |
| Status chip | `verified` (operational) or `draft` labelled "Planned" |
| Summary | One-line description of what the preview demonstrates |
| Track | Originating track ID |
| Built date | ISO date of last preview update |
| Five-pillar avg | Computed from the per-pillar scores |
| Actions | `Open Preview` (primary) · `Side-by-Side vs Current` · `Open Current Portal` |

### 2.4 Footer rule

Renders the migration rule (§5 of 13.6B) verbatim so any operator visiting the hub immediately knows the approval gate.

### 2.5 `data-testid` index

```
v2-index-root
v2-index-banner
v2-index-section-operational
v2-index-section-planned
v2-index-row-{lane.id}           ← e.g., v2-index-row-pm-v2
v2-index-{lane.id}-preview       ← e.g., v2-index-pm-v2-preview
v2-index-{lane.id}-compare       ← e.g., v2-index-pm-v2-compare
v2-index-{lane.id}-current       ← e.g., v2-index-pm-v2-current
v2-index-rules-note
v2-index-last-activity
```

---

## 3. `/_internal/v2-compare/:portal` — Side-by-Side Comparison

### 3.1 Purpose

Renders the live current portal and the V2 preview together so an operator can visually compare without leaving the review system. Supports `:portal ∈ {pm, hr}` today; extending to `admin / dispatch / safety / shop / driver` requires only a config entry per portal.

### 3.2 Layout

| Pane | Source | Notes |
| --- | --- | --- |
| Left — **Live current** | `<iframe src="/{portal}/hub">` (HR) or `<iframe src="/pm/hub">` (PM) | Iframe inherits the user's cookie; if not authenticated, the iframe shows the portal login screen. A note + "Open in new tab" link lets the operator authenticate without leaving the comparison page. |
| Right — **V2 preview** | `<iframe src="/_internal/{portal}-v2-preview">` | Always loads; no auth required. |

### 3.3 Header

A green-tinted band on the V2 pane and a paper-rail band on the current pane make it unambiguous which side is which.

### 3.4 Unknown portal handling

Visiting `/_internal/v2-compare/<unknown>` renders an `EmptyState` with a calm message and a back link to `/_internal/v2-index`. No 404, no broken page.

### 3.5 `data-testid` index

```
v2-compare-root-{portal}
v2-compare-banner
v2-compare-instructions-{portal}
v2-compare-grid-{portal}
v2-compare-current-{portal}        ← container
v2-compare-current-{portal}-iframe
v2-compare-current-{portal}-open-new-tab
v2-compare-v2-{portal}
v2-compare-v2-{portal}-iframe
v2-compare-v2-{portal}-open-new-tab
v2-compare-rule-{portal}
v2-compare-back-index
v2-compare-unknown                  ← when :portal is not in PORTAL_CONFIG
v2-compare-back-to-index
```

---

## 4. Five-pillar score for the review system itself

| Pillar | Score | Justification |
| --- | :-: | --- |
| Powerful | 9 | Single hub for every V2 preview · per-portal side-by-side compare · zero-friction operator approval workflow. |
| Simple | 9 | One page lists every lane · one click opens the preview · one click opens the compare. |
| Beautiful | 9 | Same Phase B1 primitives as the previews — consistent visual language. |
| Trusted | 9 | All links use `<Link to=>`. Iframe loads the real portal — never a mock. |
| Proven | 8 | Screenshots captured for desktop and iPad-portrait of the index; desktop for both compare views. |

**Average: 8.8 / 10.**

---

## 5. Extensibility plan

When a new portal preview comes online (Admin · Dispatch · Safety · Shop · Driver):

1. Build the preview at `/_internal/{portal}-v2-preview`.
2. Add a config entry to `PORTAL_CONFIG` in `V2Compare.jsx` (4 fields: currentTo · currentNote · v2To · purpose).
3. Add an entry to `PREVIEW_LANES` in `V2Index.jsx` (id, portal, title, track, built date, status, score, preview/compare/current links, summary).
4. No other change is required. The review hub and compare view auto-render the new lane.

This satisfies Rule #4's "Future Admin V2 / Dispatch V2 / Safety V2 / Shop V2 / Driver V2" entries in the hub — the hub already lists all five as `planned`.

---

## 6. Standing rules

No deploy. No GitHub save. No merge. The review system reads no live mutation API and writes nothing.
