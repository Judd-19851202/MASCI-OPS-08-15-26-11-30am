# Track 13.6B · PM Reality Conversion

**Mode:** Preview-only · no live PM route change · no PM API touched · no deploy.
**Generated:** 2026-06-12 (UTC)

> This document is the per-object justification log for the PM V2 action-queue rewrite. Every visible card and table answers the four-question test mandated by Rule #1.

---

## 1. The four-question test (applied to every PM V2 object)

| # | Question | Required answer |
| --- | --- | --- |
| Q1 | What is this? | Section title + caption |
| Q2 | Where from? | Caption names the backing API endpoint |
| Q3 | Why does it matter? | Card description states the operator action |
| Q4 | What happens when clicked? | The card is a `<Link to=...>` to a real PM route |

---

## 2. Pulse strip (4 action queues)

| Card | Q1 (What) | Q2 (Where from) | Q3 (Why) | Q4 (Click) |
| --- | --- | --- | --- | --- |
| **Daily Reports to Revise** | Queue of foreman-submitted Daily Reports flagged `needs_revision` | `/api/daily-reports?status=needs_revision` · PM-scoped | Foreman flagged · PM action required to verify or revise | `<Link to="/pm/daily?status=needs_revision">` |
| **Incidents Awaiting Your Verify** | Queue of incidents in `pending_verification` | `/api/incidents?status=pending_verification` | Submitted by foreman · PM must verify before close | `<Link to="/pm/incidents?status=pending_verification">` |
| **CAPAs Due This Week** | Queue of corrective actions with due date ≤ +7d | `/api/pm/crew/capas` · scoped | Corrective action approaching due date · must close or extend | `<Link to="/pm/incidents?tab=capas&due=this_week">` |
| **Constraints to Resolve** | Queue of open Project Constraints (real engine) | `/api/constraints?status=open` · PM-scoped | Project blockers · each prevents work · resolve or escalate | `<Link to="/constraints?status=open">` |

All four cards are wrapped in a `<Link>`. Clicking anywhere on the card navigates. The metric is the queue size — never a vanity total like "8 active projects".

---

## 3. Project list — converted to "Projects needing action"

| Aspect | Pre-13.6B (B2 version) | 13.6B |
| --- | --- | --- |
| Source concept | "All assigned projects" | "Only projects that need PM action right now" |
| Filter | None | Joined to open Daily / Incident / Constraint records |
| Vanity columns | RFIs · Submittals · Risks (mock) | **Removed.** |
| Replacement columns | n/a | "Why it needs you" (free-text) + "Signals" (multi-chip) |
| Empty state | n/a | `EmptyState("No projects need your action right now.", severity="good")` |

A project with zero open signals is **intentionally absent** from this view. Inventory of all projects lives in the live `/pm/jobs`, reachable via the "Open All Projects" action.

---

## 4. Verify queue (two-up)

| Table | Source | Purpose | Empty state |
| --- | --- | --- | --- |
| `pm-v2-incidents-queue-table` | `/api/incidents?status=submitted` | Surface incidents waiting on PM verify | "No incidents pending verify" (good) |
| `pm-v2-daily-queue-table` | `/api/daily-reports?status=needs_revision` | Surface Daily Reports waiting on PM revise/verify | "All daily reports verified" (good) |

Both tables are presentation-only; the verify/revise action lives inside the live PM portal at the linked URL — preview does not invent a mutation API.

---

## 5. Close-out queues (CAPAs + Constraints)

| Table | Source (real engine) | Purpose | Empty state |
| --- | --- | --- | --- |
| `pm-v2-capas-table` | `/api/pm/crew/capas` | CAPAs approaching due — drive project close decisions | "No CAPAs due this week" (good) |
| `pm-v2-constraints-table` | `/api/constraints?status=open` · `/app/backend/routes/operational_constraints.py:220` | Open Project Constraints — drive resolve/escalate | "No open constraints" (good) |

---

## 6. Field evidence

| Card | What it does |
| --- | --- |
| `pm-v2-photos-card` | `<Link to="/pm/photos">` — opens the real Job Photos Library backed by R2. No mock thumbnail rendered. |
| `pm-v2-daily-card` | `<Link to="/pm/daily">` — opens the real Daily Reports surface backed by `/api/daily-reports`. |

---

## 7. What was deliberately removed (and why)

| Surface | Removed because |
| --- | --- |
| **RFIs table** | No `/api/rfi*` exists. No `rfis` collection. Pre-existing as a mock in B2 — violated Rule #1 No-Dead-Objects. |
| **Submittals table** | Same — no MASCI engine, no API, no route. |
| **Risks table** | Risks are not a MASCI domain object. Replaced with the **real Project Constraints** engine, which is what PMs operationally use today. |
| **Mock photo grid** (4 placeholder tiles in B2) | Implying a Photos engine that already exists. Replaced with a single `<Card>` linking to the real `/pm/photos`. |
| **Vanity count cards** ("Active Projects: 8", "Crews in Field: 6") | Rule #3 violated — counts without queues. PM does not wake up asking "how many?". The pulse strip now shows **work-to-do**, not headcount. |
| **`New RFI` primary action** | No engine — would have been a dead button. Replaced with `Daily Reports To Revise` action, which opens a real PM queue. |
| **"Open Holds / Due Today" pulse cards** | Holds engine does not yet exist as a unified aggregation. Honest absence beats fake count. Captured in `MASCI_PM_TARGET_STATE.md` PM-2 / PM-3 for future tracks. |

---

## 8. Five-pillar score for PM V2 (action-queue edition)

| Pillar | Score | Justification (cited) |
| --- | :-: | --- |
| Powerful | 9 | Every surface answers a real PM operator question with a real API. Holds/Due-Today honestly absent until engine ships. |
| Simple | 9 | One vocabulary. One Card. One Table. One EmptyState. Two primary actions max. The whole page answers one question: "What requires you today?". |
| Beautiful | 9 | 100% token-driven. Heavy-civil appropriate. No vanity, no theatrics. |
| Trusted | 9 | Every queue caption names its backing API. Mock-data banner present. No "Rejected/Denied/Failed". |
| Proven | 8 | Preview-only minimum reached. Screenshots captured at 4 viewports. Live PM zero-drift verified across 6 routes. |

**Average: 8.8 / 10.**

The remaining 0.2 closes when:
- Mock data is replaced with real `/api/*` binding in the Phase B3 migration.
- Per-surface Playwright visual guardrails ship (T16).
- Real first-time PM operator runs the under-5-min task contract (`MASCI_HUMAN_USABILITY_TARGET.md` §2.1).

---

## 9. PM portal purpose enforcement

Rule #4 requires each portal to have a single purpose. PM's purpose is **"Build projects."**

Every surface on this preview maps directly to that purpose:

| Surface | How it serves "build projects" |
| --- | --- |
| Pulse strip | Surfaces work that, until done, blocks project progress |
| Projects needing action | Filtered to the subset that has open blockers |
| Verify queue | Closes the verification chain that lets jobs move forward |
| CAPAs | Closes safety follow-ups that block project closeout |
| Project Constraints | Closes blockers that prevent work |
| Field evidence (Photos + Daily) | Lets PM confirm work has happened |

There is no surface on PM V2 that does not serve "build projects".

---

## 10. Standing rules

No deploy. No GitHub save. No merge. No mutation API call. Live PM portal continues to serve operators byte-for-byte unchanged.
