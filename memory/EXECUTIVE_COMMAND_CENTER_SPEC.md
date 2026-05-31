# Executive Operations Command Center — Specification (Pillar 2)

**Classification:** OMEGA Pillar 2 · DESIGN / SPEC ONLY · No code · No DB · No endpoints · No UI · No notifications · No workflow changes
**Generated:** 2026-05-31 UTC
**Author:** E1
**Audience:** Operations Leadership · Executive Leadership Team (Jaymn primary)
**Companion docs:** `EXECUTIVE_COMMAND_CENTER_AUDIT.md` · `EXECUTIVE_HEATMAP_SPEC.md` · `EXECUTIVE_DATA_SOURCE_MAP.md` · `EXECUTIVE_IMPLEMENTATION_ROADMAP.md`
**Implementation status:** 🚫 NOT AUTHORIZED — this is a blueprint only

---

## 1 · Mission

> *"What is hurting MASCI right now? What will hurt MASCI next? Who owns it? What is being done about it? When is it expected to be resolved?"*

The Executive Operations Command Center is a **single horizontal surface** that answers those five questions for the entire company in **≤5 minutes** from a single login, **without opening any other module.**

**Owner:** Operations Leadership.
**Audience:** Executive Leadership Team.
**Primary access roles** (production): super-admin, executive_leadership, operations_director, operations_leadership.
**Future filtered views** (Phase C): PM leadership, Safety leadership, Shop leadership, Dispatch leadership.

---

## 2 · Five-second / Sixty-second / Five-minute layout doctrine

The Command Center MUST satisfy three nested time budgets:

| Budget | View | Operator question |
|---|---|---|
| 5 seconds | **Pulse Strip** — top-of-screen single horizontal bar | "Is the company healthy or not?" — one overall RAG pill + headline number (e.g., "3 RED items requiring action today") |
| 60 seconds | **Priority Stack** — 5 cards immediately below the strip | "What are my top 5 priorities today?" — the recommender output (EXV-3) ranked by composite score |
| 5 minutes | **Ten Domain Cards** — answers to the 10 operator questions | Each card is a RAG-scored summary with drill-down to the existing per-domain admin page |

The screen is **vertical**. Nothing requires horizontal scroll. Nothing requires opening another browser tab.

---

## 3 · Pulse Strip (5-second view)

A single horizontal bar at the very top of `/admin/command-center`.

| Element | Content | Source |
|---|---|---|
| Overall pill | GREEN / AMBER / RED | composite max of all 10 domain cards (worst wins) |
| Headline | "N RED items · M AMBER items · K open priorities" | aggregated counts from §5 |
| Last-refreshed timestamp | `computed_at` ISO + relative ("12 sec ago") | same `computed_at` field pattern as `/admin/recovery/snapshot` |
| Build & env identifier | `release` first 8 chars · `app_env` | reuse `/api/version` pattern (already exists) |
| Drill action | click pill → expand to full warnings list | client-only behavior |

This strip is the **only** thing the operator needs to see before deciding whether to read the rest of the screen.

---

## 4 · Priority Stack (60-second view)

Five horizontally-arranged cards directly below the Pulse Strip. Each card is one of the **top 5 items requiring leadership attention** as ranked by the recommender (EXV-8).

| Field | Content |
|---|---|
| Rank | 1–5 |
| RAG tag | GREEN / AMBER / RED (always AMBER/RED in this stack — GREEN items are filtered out) |
| Headline | one sentence (e.g., "PO #2148 awaiting approval — 9 days · Critical") |
| Domain | safety · equipment · jobs · accountability · pm-load · supervisor-load · approvals · project-risk · bottlenecks · recommender-fallback |
| Owner | role · name (e.g., "Chris Wright (PM)") |
| Action verb | "Approve" · "Review" · "Acknowledge" · "Reassign" · "Resolve" (button label) |
| ETA | when is it expected to be resolved (from `tasks.due_at` or `corrective_actions.due_date`) |
| Drill | click → opens the existing detail page for that record (no new endpoint required) |

The Priority Stack is the answer to operator question #10 ("What should the Operations Director focus on next?").

---

## 5 · Ten Domain Cards (5-minute view)

Below the Priority Stack, a 5×2 grid of domain cards. Each card answers exactly one of the operator's mandated questions.

| # | Card title | Operator question | RAG basis (see `EXECUTIVE_HEATMAP_SPEC.md`) | Drill-to |
|---|---|---|---|---|
| 1 | **Jobs Today** | What jobs need attention today? | active job count vs DRs filed today, vs open incidents tied to job | `/admin/jobs?status=needs_attention` (filter behavior, no new endpoint required) |
| 2 | **Safety Today** | What safety issues need attention today? | open `incidents` ≥ severity-medium AND/OR open `corrective_actions` past due AND/OR open `compliance_findings` ≥ amber | `/admin/incidents` + `/admin/compliance-findings` |
| 3 | **Equipment Today** | What equipment issues need attention today? | active `asset_holds` + `fleet_defects(status=open)` + `equipment_inspections(out_of_service=yes)` | `/admin/equipment-inspections?status=open` |
| 4 | **Accountability Overdue** | What accountability items are overdue? | `tasks(status=open AND due_at < now)` + `corrective_actions(due_date < now)` + `notifications(acknowledged=false AND created > 7d ago)` | `/admin/accountability` (logical filter on existing `/api/tasks` + `/api/notifications`) |
| 5 | **PM Load** | What PMs are overloaded? | per-PM aggregation: assigned jobs × open incidents × open DRs awaiting review (see EXV-4 score) | `/admin/project-managers/activity` (already exists) |
| 6 | **Supervisor Load** | What supervisors are overloaded? | per-FL-user aggregation: linked daily reports × open field_leadership_records × assigned dispatch crew-day-count | `/admin/people` → FL panel (already exists) |
| 7 | **Approvals Aging** | What approvals are aging? | `po_requests(status=pending AND submitted < N days ago)` bucketed by 3d / 5d / 7d+ | `/admin/po-requests?status=pending&age=…` |
| 8 | **Projects at Risk** | What projects are at risk? | per-project composite (safety + equipment + DR cadence + PO churn + variance) — see EXV-6 in heatmap spec | `/admin/pnl` + per-project drill |
| 9 | **Operational Bottlenecks** | What operational bottlenecks exist? | dispatch assignments stuck >24h · DRs unreviewed >48h · POs stuck in approval >5d · OOS equipment with no work order >24h | `/admin/operations-events?status=stuck` (filter on existing collection) |
| 10 | **Recommender** | What should the Operations Director focus on next? | the same input that fed the Priority Stack — exposed here as the full ranked list (top 20) with reason codes | (renders inline; clicks open the underlying record) |

Each domain card contains, at minimum:
- RAG pill (GREEN/AMBER/RED)
- One-line headline number (e.g., "3 RED · 7 AMBER")
- The 2–3 highest-severity items (each with owner, age, and drill link)
- "View all" link to the existing detail page

**Card layout doctrine:** identical structure across all 10 cards so leadership reads them at uniform glance speed.

---

## 6 · Drill paths (no new endpoints required)

The Command Center is a **synthesizer**, not a data store. Every drill-down opens an existing admin page:

| From card | Drill destination | Endpoint already exists? |
|---|---|---|
| Jobs Today | `/admin/jobs/{id}` | ✅ |
| Safety Today | `/admin/incidents/{id}` · `/admin/compliance/findings/{id}` | ✅ |
| Equipment Today | `/admin/equipment/{id}` · `/admin/equipment-inspections/{id}` | ✅ |
| Accountability Overdue | `/api/tasks/{id}` (existing per-portal task detail) | ✅ |
| PM Load | `/admin/project-managers` row | ✅ |
| Supervisor Load | `/admin/people` FL row | ✅ |
| Approvals Aging | `/admin/po-requests/{id}` | ✅ |
| Projects at Risk | `/admin/pnl?project_number=…` | ✅ |
| Operational Bottlenecks | `/admin/operations-events/{id}` | ✅ |
| Recommender | underlying record drill (depends on which source supplied the top-ranked item) | ✅ |

The only **synthesis API** ever proposed by this spec is one read-only endpoint (in a future implementation batch, not now) modeled on `/api/admin/recovery/snapshot`: e.g., `GET /api/admin/command-center/snapshot`. Its body returns the same JSON structure exposed in `EXECUTIVE_DATA_SOURCE_MAP.md`.

---

## 7 · Refresh & freshness contract

- Snapshot is **read-only** and **computed on demand** (not cached longer than 60 sec server-side) — mirrors `recovery/snapshot.computed_at`.
- All counts are evaluated against MongoDB at request time (no eventual-consistency lag).
- Operator can **manually refresh** with a button (same UX as `/admin/recovery`).
- No write paths. No cron. No background fan-out for this view (that lives in Pillar 4 · Escalation).

---

## 8 · Non-goals (out of scope for Pillar 2 entirely)

- ❌ NOT a notification surface. No emails, no SMS, no bell pings emitted from this view.
- ❌ NOT an escalation engine. Escalation triggers belong to Pillar 4.
- ❌ NOT a field-experience surface. Foreman/operator UX belongs to Pillar 3.
- ❌ NOT a write surface. The Command Center never mutates state directly. It only routes the operator to existing write surfaces.
- ❌ NOT a multi-tenant or per-PM scope. Per-role filtered views are Phase C and DEFERRED.
- ❌ NOT a redesign of any existing dashboard. Existing admin pages remain unchanged.
- ❌ NOT a new mobile experience. Desktop-first, leadership-meeting-projector target.

---

## 9 · Acceptance criteria for a future implementation batch

Any future batch that implements the Command Center must demonstrate, with evidence:

1. Operations Director can log in and see the Pulse Strip within 5 seconds (page-load p95 ≤ 2000 ms · pulse-strip render < 500 ms).
2. The top 5 priorities for the day appear within 60 seconds — without operator scrolling or clicking.
3. All 10 mandated questions are answered on the same screen within 5 minutes.
4. Every RAG state on every card cites the rule that produced it (auditable — same `warnings[]` pattern as `/admin/recovery/snapshot`).
5. Every red/amber item is associated with an **owner**, an **action verb**, and an **expected resolution time**.
6. No new MongoDB collection is required. No collection schema is mutated. (See `EXECUTIVE_DATA_SOURCE_MAP.md`.)
7. The implementation reduces leadership time-to-priority-identification by ≥80% (60 min → ≤5 min), measured against a baseline hunt time captured before launch.

These acceptance criteria become the gating evidence for closing the Phase A implementation batch.

---

## 10 · The five questions the Command Center must always answer

For each Red and Amber item on the screen, the Command Center MUST surface (no exceptions):

1. **What is hurting MASCI right now?** → headline + RAG
2. **What will hurt MASCI next?** → aging buckets + projected escalation (Phase B+)
3. **Who owns it?** → owner role + name
4. **What is being done about it?** → linked task/CA status
5. **When is it expected to be resolved?** → `due_at` / `due_date` / ETA

A widget that cannot answer all five of these for an item in its list is **incomplete** and must be rejected from the Command Center until it can.
