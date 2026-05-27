# Cross-Portal Coaching Standard — Phase IV-BETA

**Iteration:** iter437 · Phase IV-BETA · 2026-02
**Status:** 🟢 BINDING ON ALL PORTAL COPY · ENFORCED VIA DEPLOY GATE `verify_coaching_sublines.py`
**Inherits from:** `OPERATIONAL_VERBIAGE_DOCTRINE.md` §IX · `COMMUNICATION_TONE_STANDARD.md`

The platform does not merely expose functionality. It coaches the operator — quietly, in a single calm sentence per surface, every time. This document binds that coaching contract across all 7 portals.

A surface without a coaching subline is a surface that asks the operator to remember what it is for. The platform's job is to never make the operator do that work.

---

## I. The coaching contract

Every navigable surface (domain header, page H1, list view, form view, modal title where applicable) carries:

1. **A noun** — what this surface is (Tier 4 strong).
2. **A coaching subline** — what to do here, in ≤ 14 words (Tier 5 calm).

Both are bound by the verbiage doctrine: no marketing, no "Welcome to…", no exclamation, no feature lists.

---

## II. The three coaching shapes

Every coaching subline takes one of three shapes. Mixing shapes within a surface is forbidden.

### Shape A — Operational scope

States what activity the surface covers.

```
Daily Reports
Review and approve field-leadership submissions.
```

```
Incidents
Open and recent safety/quality deviations.
```

### Shape B — Operational target

States what the operator should do here.

```
Pre-Op Checks
Today's pre-shift checks across your fleet.
```

```
Compliance Export
Date-range CSV for audits and insurance reviews.
```

### Shape C — Operational state

States the current operational fact (used on landing surfaces with live data).

```
Operations
Field activity across all active projects.
```

```
Crew Compliance
Training, PPE, CAPA exposure, expirations.
```

---

## III. The 14-word budget

Every subline ≤ 14 words. Hard limit. The reason: a glance is 1–2 seconds. 14 words at 250 wpm reading speed = 3.4 seconds. Anything longer becomes prose, and prose breaks the calm-glance pattern.

When 14 words is not enough, the surface is doing two jobs — split it.

---

## IV. Forbidden coaching patterns

| Pattern | Why forbidden |
|---|---|
| "Welcome to…" | Marketing tone |
| "Here you can…" | Feature listing |
| "Easily manage…" | Patronizing adverb |
| "Just submit…" | Patronizing adverb |
| "Don't forget to…" | Imperative scolding |
| "This is where you…" | Tour-guide voice |
| Bullet lists in sublines | Subline is one sentence |
| Multiple sentences in a subline | Length budget violation |
| Lists of features (e.g., "View, edit, approve, comment") | Doctrine §IX |
| Exclamation marks | Severity color carries urgency, not punctuation |
| Emoji | Operational copy is emoji-free |
| Questions ("What would you like to do?") | Surfaces declare; they do not ask |
| Casual contractions ("you're", "don't") | Calm operational voice uses full forms |

---

## V. The coaching subline by surface type

### A. Sidebar domain row

Format: `Domain · {Shape A or C, ≤ 12 words}`

Examples (from existing locked artifacts):

| Portal | Domain | Subline |
|---|---|---|
| Admin | Operations | Field activity across all active projects. |
| Admin | Workforce | People, certifications, time-off, onboarding. |
| Admin | Equipment & Fleet | Asset lifecycle, maintenance, pre-op, suppliers. |
| Admin | Communications | Email routing, notifications, escalation flow. |
| Admin | Safety & Compliance | Incidents, audits, certifications, OSHA. |
| Admin | System & Governance | Storage, backups, deploy health, observability. |
| PM | Project Operations | Field activity across your assigned projects. |
| PM | Financials & Cost | Purchase orders, change exposure, budget signals. |
| PM | Field Coordination | RFIs, subcontractors, materials, logistics. |
| PM | Document Control | Drawings, specs, JHAs, trench boxes, posters. |
| PM | Compliance & Risk | Incidents, audits, certifications, OSHA. |
| PM | System & Communications | Email routing, notifications, escalations. |

### B. Sidebar child entry

Format: `Page · {Shape A, ≤ 10 words}`

Coaching is optional for sidebar children when the parent domain subline covers the same scope. When present, it adds operational specificity.

### C. Page H1 + subline

Every page renders an H1 with a single subline below.

Pattern:
```jsx
<h1 className="text-2xl font-semibold text-slate-900">Daily Reports</h1>
<p className="text-xs text-slate-500 mt-1">Review and approve field-leadership submissions.</p>
```

When viewing a single record (detail page):
```jsx
<h1 className="text-2xl font-semibold text-slate-900">
  Daily Report · 2026-02-27 · Crew 7
</h1>
<p className="text-xs text-slate-500 mt-1">
  Submitted by J. Ramirez at 16:47 · 12 entries · awaiting your approval.
</p>
```

### D. List view filter row

A list view's filter row carries no coaching — the page H1 subline already does. But the empty state inside the list uses coaching:

```
No Daily Reports for this date range.
Adjust the date range or check the filters above.
```

### E. Modal title + body

Per `COMMUNICATION_TONE_STANDARD.md` §XII:

```
Title: Reject Daily Report
Body: Rejecting returns the report to the foreman for revision. Provide a one-sentence reason.
```

The body sentence IS the coaching — it states the consequence.

### F. Form section header

Long forms (Daily Report, Incident Report) use coaching at each section header:

```
Crew Information
Who was on site today.
```

```
Hazards Identified
List any hazards observed during the shift.
```

These sublines guide the operator through the form's mental model.

---

## VI. Coaching by operational role

A super-admin and a field foreman both see the same coaching. The platform does NOT vary copy by role — that would create operational ambiguity ("did my admin see the same thing?").

What DOES vary by role:
- Which surfaces are visible (per `*_INFORMATION_PRIORITY_MAP.json` `role_visibility_recommendations`).
- Which actions are available (server-side permissions).

The wording is constant.

---

## VII. Coaching by portal accent

A surface in the PM portal and the Admin portal — when both expose the same operational concept — carries the SAME coaching subline.

Example: "Daily Reports" in Admin operations and "Daily Reports" in PM project-operations both have the subline `Review and approve field-leadership submissions.`

Where the operational scope differs (e.g., Admin Daily Reports = all PMs' submissions; PM Daily Reports = my-projects-only), the subline is adjusted minimally:

| Portal | Subline |
|---|---|
| Admin | Review and approve field-leadership submissions. |
| PM | Review submissions from crews on your projects. |

The verb (`Review`) stays canonical. The scope qualifier (`from crews on your projects`) is the only variation.

---

## VIII. Mobile coaching compression

Per `OPERATIONAL_VERBIAGE_DOCTRINE.md` §XI, mobile copy compresses by dropping articles and prepositions. Coaching sublines DO NOT compress on mobile — they remain the full sentence. Reasons:

1. Coaching is read at glance; compression risks ambiguity.
2. The subline is already ≤ 14 words.
3. Compression in critical reads would degrade trust.

What DOES compress on mobile: button verbs (`Submit Daily Report` → `Submit`), table column headers, timestamps. Not sublines.

---

## IX. Coaching for AI / search / global search

Global search results also carry coaching:

```
Daily Report · 2026-02-27 · Crew 7
Submitted by J. Ramirez · approved by M. Chen at 14:22.
```

The subline contextualizes the result in one calm sentence.

---

## X. Empty-state coaching

Per `COMPONENT_HIERARCHY_STANDARD.md` §XII, empty states have a 2-line coaching shape:

```
Title (Tier 4, ≤ 12 words, operational fact)
Subline (Tier 5, ≤ 18 words, optional, what to do next)
```

Examples:

| Surface | Empty title | Empty subline |
|---|---|---|
| Daily Reports list | `No Daily Reports for this date range.` | `Adjust the date range or check the filters above.` |
| Incidents list | `No open incidents.` | (omitted — positive state) |
| Pre-Op list | `All Pre-Op checks complete for today.` | (omitted — positive state) |
| Notifications dropdown | `No unread notifications.` | (omitted) |
| PM Jobs list | `No active jobs assigned to you.` | `New job assignments appear here automatically.` |

---

## XI. The coaching deploy gate (Phase IV-BETA.4)

The script `/app/scripts/verify_coaching_sublines.py` runs on every deploy:

1. Parse the built bundle for every `<SideNavV2>` domain entry · `<PageHeader>` instance · `<EmptyState>` use.
2. Verify the subline is present.
3. Verify the subline is ≤ 14 words.
4. Verify the subline contains no forbidden phrases from §IV.
5. Verify the subline ends with a period.

A surface that fails ≥ 1 check fails the deploy.

---

## XII. Coaching maintenance

| Trigger | Action |
|---|---|
| New surface added | PR must include coaching subline conforming to §II shape · reviewed for tone |
| Operational scope changes | Subline reviewed and updated in the same PR · doctrine version bumped |
| Doctrine amendment | All affected sublines audited and rewritten · regression test the deploy gate |
| Quarterly review | Operations leadership reviews top-20 sublines for clarity · adjustments via doctrine PR |

---

## XIII. Operator-trust principles for coaching

1. **A new PM signs in and understands every sidebar entry without asking.** Coaching does that work invisibly.
2. **A subline never lies about scope.** "Today's pre-shift checks" really means today's, not this week's.
3. **A subline never promises a feature.** "Easily…" is forbidden because it is unprovable.
4. **A subline never expires.** When operational scope changes, the subline changes — the platform does not let stale coaching live.
5. **A subline never preaches.** It states facts. The operator decides what to do with them.

---

## Verdict

🟢 **CROSS-PORTAL COACHING STANDARD LOCKED.** Every surface speaks in the same calm operational voice. The deploy gate ensures it stays that way.
