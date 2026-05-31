# Executive Command Center — Implementation Roadmap (Pillar 2)

**Classification:** OMEGA Pillar 2 · ROADMAP ONLY · No code · No DB · No endpoints · No UI · No notifications · No workflow changes
**Generated:** 2026-05-31 UTC
**Author:** E1
**Audience:** Operations Leadership · future implementation agent (when authorized)
**Companion docs:** `EXECUTIVE_COMMAND_CENTER_AUDIT.md` · `EXECUTIVE_COMMAND_CENTER_SPEC.md` · `EXECUTIVE_HEATMAP_SPEC.md` · `EXECUTIVE_DATA_SOURCE_MAP.md`

---

## 1 · Sequencing doctrine

Three phases, **each shippable independently**, each gated by operator-authored evidence:

| Phase | Theme | Time-to-value | Risk |
|---|---|---|---|
| **A — Core single-glass** | Pulse Strip + 7 high-confidence cards + threshold-driven RAG + snapshot endpoint | 1–2 batches | LOW |
| **B — Recommender & Project Risk** | Add cards 8/10, scoring composer, CSV export, optional snapshot cache | 1 batch | LOW–MEDIUM |
| **C — Filtered role views** | Per-leadership-role filtered Command Centers (PM/Safety/Shop/Dispatch lenses) | 1 batch | MEDIUM |

No phase blocks the existing platform. Each phase ends with a closeout report and explicit operator GO before the next begins. **Same OMEGA cadence used for Backup & Recoverability.**

---

## 2 · Phase A — Core single-glass (FOUNDATION)

### A.1 Deliverables

| # | Item | Type | Source |
|---|---|---|---|
| A-1 | `db.command_center_thresholds` seeded with defaults from `EXECUTIVE_HEATMAP_SPEC.md` §4 | DB (admin-seed only) | NEW (1 doc) |
| A-2 | `GET /api/admin/command-center/snapshot` (admin-strict) | endpoint | NEW |
| A-3 | `GET/PATCH /api/admin/command-center/thresholds` (admin-strict + `X-Directory-Token`) | endpoint | NEW |
| A-4 | `/admin/command-center` page · Pulse Strip + 7 cards | UI | NEW |
| A-5 | `/admin/command-center/thresholds` page · simple admin form | UI | NEW |
| A-6 | `AdminHub` tile pointing to `/admin/command-center` | UI | EDIT existing |
| A-7 | `pytest` suite under `/app/backend/tests/test_command_center_*.py` covering: threshold doc lifecycle · 7 cards × (GREEN/AMBER/RED transitions) · drill payload integrity · ObjectId leak contract | tests | NEW |

### A.2 Cards included in Phase A (7 of 10)

✅ Jobs Today · ✅ Safety Today · ✅ Equipment Today · ✅ Accountability Overdue · ✅ PM Load · ✅ Approvals Aging · ✅ Operational Bottlenecks.
🟡 **Deferred to Phase B:** Supervisor Load (needs FL aggregation work) · Projects at Risk (needs composite per-project rollup) · Recommender (needs scoring composer).

### A.3 Phase A acceptance criteria (gating evidence for closeout)

1. Pulse Strip renders on `/admin/command-center` within 2 seconds p95 (preview + prod probe).
2. Each of the 7 cards correctly renders GREEN/AMBER/RED with at least one synthetic-data test transition per card (pytest suite).
3. `warnings[]` array is correctly populated for every fired rule (item count + drill URL).
4. Threshold edits via `/admin/command-center/thresholds` round-trip and recompute the snapshot in ≤ 60 sec.
5. Snapshot endpoint returns < 1.5 sec p95 (preview).
6. **Zero** new collections beyond `command_center_thresholds`. Verified by `grep -rE 'await db\.[a-z_]+\.(insert|update)' /app/backend/routes/command_center*.py` showing only the threshold collection.
7. **Zero** modifications to any existing collection schema. Verified by `git diff` showing no edits to other route files except `AdminHub.jsx` tile + `server.py`/router-include.
8. **Zero** notifications/emails/tasks emitted by Phase A code (Pillar 4 territory).
9. Time-to-priority-identification: leadership self-reports ≤ 5 minutes during a Phase-A pilot session (capture in `PILLAR_2_PHASE_A_CLOSEOUT.md`).
10. The OMEGA backup freeze is preserved (no touches to `recovery_dashboard.py`, `singleton_scheduler.py`, `_iter_photo_refs`).

### A.4 Phase A stop conditions

- Any failed acceptance criterion → STOP, write partial report, await operator review.
- Any net-new collection beyond `command_center_thresholds` → STOP, escalate.
- Any code change in `/app/backend/lib/singleton_scheduler.py` or `routes/recovery_dashboard.py` → IMMEDIATE STOP (OMEGA backup-freeze violation).

### A.5 Phase A out-of-scope (explicit)

- No mobile responsive design (desktop-first).
- No per-PM/per-supervisor lenses (Phase C).
- No CSV export (Phase B).
- No background scoring cron (compute on demand).
- No notifications/emails (Pillar 4).

### A.6 Phase A estimated implementation surface

| Footprint | Estimate |
|---|---|
| New backend file | `/app/backend/routes/command_center.py` ~250–350 LOC |
| New frontend pages | `/app/frontend/src/pages/admin/AdminCommandCenter.jsx` ~400 LOC · `AdminCommandCenterThresholds.jsx` ~200 LOC |
| New pytest file | `/app/backend/tests/test_command_center_phase_a.py` ~400 LOC |
| Edits to existing | `server.py` router-include · `AdminHub.jsx` 1 tile · `_INDEX.md` + `PRD.md` entries |
| Database | 1 new collection (`command_center_thresholds`) with 1 seed doc |
| Total | < 1500 LOC including tests |

---

## 3 · Phase B — Recommender, Projects at Risk & CSV export

### B.1 Deliverables

| # | Item | Source |
|---|---|---|
| B-1 | Card 6 (Supervisor Load) wired with FL aggregation | extend Phase-A code |
| B-2 | Card 8 (Projects at Risk) composite rollup logic | extend Phase-A code |
| B-3 | Card 10 (Recommender) — `priority_score` composer + Top-20 detail page | extend |
| B-4 | `/admin/command-center/recommender-detail` UI | NEW page |
| B-5 | `GET /api/admin/command-center/snapshot.csv` | NEW endpoint |
| B-6 | Optional cache collection `command_center_snapshots` (only if compute > 60 sec) | conditional NEW |
| B-7 | pytest expansion: composite scoring, recommender ordering, CSV format contract | NEW |

### B.2 Phase B acceptance criteria

1. Top-5 Priority Stack renders within 60 seconds of login.
2. Recommender ranking is **deterministic** — identical inputs → identical Top-20 order across 3 consecutive snapshots.
3. CSV export produces a single-pass file readable by Excel/Sheets without truncation.
4. Projects-at-Risk RAG correctly handles a 0-project corner case (no division-by-zero, no AMBER false positive).
5. Optional snapshot cache stays internally consistent (no stale `computed_at` > 90 sec).

---

## 4 · Phase C — Filtered role lenses

### C.1 Deliverables

| # | Item | Source |
|---|---|---|
| C-1 | Role-filtered query layer that subsets cards to a single PM / Safety lead / Shop lead / Dispatch lead | extend |
| C-2 | `/pm/command-center` (PM-scoped) | NEW page (scoped UI) |
| C-3 | `/safety-portal/command-center` (Safety-scoped) | NEW page (scoped UI) |
| C-4 | `/shop/command-center` (Shop-scoped) | NEW page (scoped UI) |
| C-5 | `/dispatch-portal/command-center` (Dispatch-scoped) | NEW page (scoped UI) |
| C-6 | Per-portal cron-driven daily digest email (Pillar 4 INTEGRATION — must be authorized as a Pillar-4 batch first) | DEFERRED · cross-pillar |
| C-7 | pytest expansion: per-role scope enforcement (PM cannot see other PM's items, Safety can't see PM-only HR detail, etc.) | NEW |

### C.2 Phase C acceptance criteria

1. PM-lens shows only items in `compute_pm_scope(actor)` (existing per-PM scoping helper from `routes/pm_admin.py`).
2. Safety-lens shows only safety-domain cards and never PM-load or supervisor-load detail.
3. Shop-lens shows only equipment + fleet cards.
4. Dispatch-lens shows only dispatch + asset-hold cards.
5. Each per-portal lens shares the **same scoring engine and threshold doc** as the executive view (no fork).

---

## 5 · Cross-phase dependency graph

```
                      ┌──────────────────────────────────┐
                      │ Pillar 0 · Backup & Recoverability│ FROZEN ✅
                      └──────────────────────────────────┘
                                       ▼
                      ┌──────────────────────────────────┐
                      │ Phase A · Core Command Center    │
                      │ 7 cards · Pulse Strip · Thresholds│
                      └──────────────────────────────────┘
                                       ▼
                      ┌──────────────────────────────────┐
                      │ Phase B · Recommender + Projects │
                      │ Cards 6/8/10 · CSV · Optional cache│
                      └──────────────────────────────────┘
                                       ▼
            ┌────────────────────────────┴───────────────────────────────┐
            ▼                                                            ▼
┌──────────────────────────┐                            ┌──────────────────────────────┐
│ Phase C · Filtered lenses│                            │ Pillar 4 · Escalation Framework│
│ PM/Safety/Shop/Dispatch  │                            │ (per-portal digests, alerts)  │
└──────────────────────────┘                            └──────────────────────────────┘
```

Phase B can begin only after Phase A closeout passes acceptance criteria.
Phase C can begin only after Phase B closeout.
Pillar 4 (escalation, digests, alerting) is a **separate pillar** and must be authorized independently — Phase C consumes its outputs but does not implement them.

---

## 6 · OMEGA discipline guardrails

Every implementation batch under this roadmap MUST:

1. Declare the 5 mandatory inputs at batch start (business outcome · owner · notification path · escalation path · executive visibility path).
2. Cite exact files to touch with line ranges.
3. Specify acceptance criteria with measurable evidence.
4. Specify stop conditions (when to halt and write a partial report).
5. Write a closeout report under `/app/memory/PILLAR_2_PHASE_<X>_CLOSEOUT.md`.
6. Update `PRD.md` + `_INDEX.md` on closeout.
7. **Not** touch the frozen Backup & Recoverability surface (`/app/memory/BACKUP_RECOVERABILITY_EPIC_CLOSEOUT.md` §5 inventory).
8. Run the testing agent after Phase A and Phase B (per project standards) — read-only smoke tests on the executive snapshot endpoint.

---

## 7 · Open questions for operator (DO NOT RESOLVE UNILATERALLY)

The following decisions are **deferred to operator authorization** at the start of the first implementation batch. Listing here so they are not missed:

1. **RBAC for the Command Center landing route** — should it be admin-strict only, or admit a new `executive_leadership` role to the directory? (Current platform has super_admin · admin · pm · hr · safety · shop · dispatch · fl. No `executive` role yet.)
2. **Threshold tuning audience** — admin only, or any super_admin? Suggest: admin-strict + super_admin only.
3. **Refresh cadence** — fully on-demand, or auto-refresh every N seconds when the page is open? Suggest: on-demand button + optional 60-sec auto-refresh toggle in user prefs.
4. **CSV export retention** — should exports be ephemeral (server-render-then-stream) or persisted (writable collection)? Suggest: ephemeral (no persistence required).
5. **Pilot user set** — Phase A pilot should include the Operations Director + 1 executive + 1 PM lead + 1 Safety lead. Confirm before launch.
6. **Mobile** — confirm desktop-only for Phase A (per spec §8 non-goals).

These are flagged early so the operator can preempt scope drift during the first implementation batch's `ask_human` gate.

---

## 8 · Stop here

This roadmap is complete. **No implementation is authorized.** The agent's next action is to STOP and await operator authorization to begin Phase A — at which point the future agent MUST collect the five mandatory inputs again before writing the first line of code.

No drift. No sprawl. No speculative features.
