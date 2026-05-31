# Pillar 1 → Pillar 2 · Executive Accountability Integration

**Batch:** Pillar 1 · Accountability Engine · Design only
**Date:** 2026-05-31
**Scope:** Specify how the Accountability Engine plugs into the Executive Operations Command Center so every RED / AMBER item answers the 5 executive questions: **What's wrong · Who owns it · What's being done · When is it due · What happens next.** **No code · no UI change in this batch · no new dashboard card.**
**Discipline:** OMEGA · evidence-only · Phase A Command Center surface remains untouched until operator authorizes Phase 1A-4.

---

## 1 · The five executive questions, today vs target

| Question | Today (production · source_hash `54b8a402…`) | Target after Pillar 1 |
|---|---|---|
| Q1 · What's wrong? | ✅ `card.warning.message` + `item.what_wrong` | unchanged |
| Q2 · Who owns it? | 🟡 5 of 9 owner strings hardcoded in `command_center.py` (see Audit §5) | 🟢 derived from the Accountability projection (`owner_role + owner_user_id + owner_display_name`) |
| Q3 · What's being done? | 🔴 `item.current_status` is a free-form string per rule (e.g. "Open · awaiting assignment") with no event evidence | 🟢 `last_activity_kind + last_activity_at` from the timeline, displayed verbatim |
| Q4 · When is it due? | 🟡 `item.eta` is a rule-fixed string (e.g. "Within 24 hours") | 🟢 `due_at` from the projection; overdue overlay applied |
| Q5 · What happens next if ignored? | 🔴 not answered anywhere | reserved — answered by Pillar 1B Escalation Framework (not this batch) |

**Pillar 1 closes Q2 + Q3 + Q4. Q5 is intentionally deferred.**

---

## 2 · The current Command Center contract (preserved as-is)

`/api/admin/command-center/snapshot` returns:

```json
{
  "pill": "RED|AMBER|GREEN",
  "pulse": { ... },
  "cards": [
    {
      "card_id": "jobs|safety|equipment|accountability|approvals",
      "pill": "...",
      "warnings": [ ... ],
      "items": [
        {
          "what_wrong": "...",
          "why_red": "...",
          "owner": "...",            // ◄── 5/9 hardcoded today
          "current_status": "...",    // ◄── free-form today
          "eta": "...",               // ◄── rule-fixed string today
          "drill_to": "...",
          "rule_id": "...",
          "severity": "..."
        }
      ]
    }
  ],
  "calendar": { ... },
  "cached": false
}
```

**This payload shape is not changing in this batch.** What changes is the **source** of `owner`, `current_status`, and `eta` — they begin to read from the projection instead of being hardcoded.

---

## 3 · Per-card integration plan

### 3.1 · Card 1 — Jobs Today

| Rule | Current owner derivation | After Pillar 1 |
|---|---|---|
| JOBS-DR-MISSING | `job.primary_pm_name` (line 328) | `project(jobs.daily_report_missing).owner_display_name`; the projection uses `primary_pm_user_id` if the directory link exists, falls back to `primary_pm_name` |
| JOBS-ISSUE-NO-OWNER | hardcoded "UNASSIGNED" (line 371) | unchanged (truthful by definition) |
| JOBS-ISSUE-NO-PATH | hardcoded "Safety" (line 406) | `project(safety.incidents).owner_display_name` — empty incidents fall back to "Safety" |

`current_status` becomes the canonical status (`open`/`in_progress`/`pending_review`) plus the `last_activity_kind` from the timeline (e.g. `last_activity_kind=assigned · at=12h ago`).

### 3.2 · Card 2 — Safety Today

| Rule | Current | After Pillar 1 |
|---|---|---|
| SAF-CRITICAL-UNRESOLVED | hardcoded "Safety" (line 478) | `project(safety.incidents).owner_display_name`; the projection promotes linked CA assignee when present |
| SAF-OSHA-OPEN | hardcoded "Safety" (line 532) | same |
| SAF-CA-OVERDUE | `ca.assigned_to_name` (line 568) | `project(safety.corrective_actions).owner_display_name` — preserves today's behavior **plus** resolves email → user_id |
| SAF-CA-CHRONIC | (no items today) | `project(safety.corrective_actions)` |

The D1/D2 closure check (`_incident_is_resolved`) becomes part of the projection's `status` derivation (Lifecycle §4.5). No behavior change; just relocation.

### 3.3 · Card 3 — Equipment Today

| Rule | Current | After Pillar 1 |
|---|---|---|
| EQP-OOS-OLD | hardcoded "Shop" (line 660) | `project(equipment.dvir).owner_display_name`; `acknowledged_by_name` promoted when present |
| EQP-OOS-NEW | hardcoded "Shop" | same |
| EQP-BACKLOG | hardcoded "Shop" (aggregate) | unchanged — aggregate, no per-item owner |

Closes Audit risk A-02. Note: the underlying `fleet_defects` collection still has no `assignee_role`/`user_id` field — the projection reads `shop` role with `acknowledged_by_name` as display. The Roadmap proposes adding those fields in Phase 1A-5 (post-authorization).

### 3.4 · Card 4 — Accountability Overdue

Already wired to `db.tasks` directly. After Pillar 1:

| Field | Source |
|---|---|
| `owner` | `task.assignee_user_id` → directory lookup; falls back to `assignee_role` |
| `current_status` | canonical status + `last_activity_kind` from timeline |
| `eta` | `due_at` |

Closes Audit risk A-06 (role-only ownership remains valid but is treated as lower-fidelity in display).

### 3.5 · Card 5 — Approvals Aging

| Rule | Current | After Pillar 1 |
|---|---|---|
| APP-AMBER / APP-RED / APP-WEEK | `po.requested_by_name` (line 874) — **the requester, not the approver** | `project(po.requests).owner_display_name` — derived from approval routing's "current pending approver" |

Closes Audit risk A-05 and the false-attribution flagged in Audit §5.

---

## 4 · New `drilldown` payload (additive · existing endpoint already exists)

The Command Center already exposes `GET /api/admin/command-center/drilldown/{card_id}/{item_id}` (`command_center.py:1069-1109`). Today it returns the raw source document plus three derived fields (`actions_underway`, `owner`, `expected_resolution`).

After Pillar 1, the drilldown payload **adds** (does not remove) two sub-objects:

```json
{
  // ── existing fields unchanged ──
  "card_id": "...",
  "item_id": "...",
  "source_doc": { ... },
  "actions_underway": "...",
  "owner": "...",
  "expected_resolution": "...",

  // ── NEW · added by Pillar 1 ──
  "accountability": {
    "accountability_id":   "...",
    "owner_role":          "...",
    "owner_user_id":       "...",
    "owner_display_name":  "...",
    "assigned_at":         "...",
    "assigned_by":         { "role": "...", "name": "..." },
    "due_at":              "...",
    "status":              "<canonical>",
    "priority":            "...",
    "first_viewed_at":     null,
    "last_activity_at":    "...",
    "last_activity_kind":  "...",
    "escalation_level":    0,
    "resolved_at":         null,
    "resolved_by":         null,
    "resolution_notes":    null
  },
  "timeline": [ ... last 25 events, newest first ... ]
}
```

**Pre-existing `owner` and `actions_underway` strings remain on the response for backward compatibility.** Once the SPA is updated to read `accountability.*`, those legacy strings become deprecated (but not removed) in a later phase.

---

## 5 · Backward compatibility (zero-break guarantee)

| Surface | Pre-Pillar 1 | Post-Pillar 1 Phase 1A | Risk |
|---|---|---|---|
| `/api/admin/command-center/snapshot` payload shape | unchanged | unchanged | none |
| `card.items[].owner` field | hardcoded string in many rules | derived string from projection; same field name; same data type | none — display-level change |
| `card.items[].current_status` | rule-fixed | projection-derived | none — display-level change |
| `card.items[].eta` | rule-fixed | `due_at` (ISO string) when projection has one; falls back to today's rule-fixed string | none — display-level change; the SPA already renders `eta` as text |
| `drilldown` payload | 3 derived fields | 3 derived fields **plus** `accountability` + `timeline` sub-objects | additive; SPA ignores unknown keys |
| Frontend `AdminCommandCenter.jsx` | renders text as-is | renders text as-is | unchanged in Phase 1A; UI affordances arrive in Phase 1A-6 |

The first frontend code change is **gated** behind an explicit Phase 1A-6 authorization. Phase 1A-1..1A-5 are backend-only.

---

## 6 · Accountability Dashboard — design only

This batch is explicitly NOT authorized to ship a new dashboard card. However, the operator requested an Accountability Dashboard *design* as deliverable #6 (the directive lists it). The design lives here as a future surface and is **not built** in this batch.

### 6.1 · Surface: `/admin/accountability` (NEW · NOT BUILT)

A single read-only page that **complements** (does not replace) the Command Center. Three sections, top-to-bottom:

**Section A · Ownership Map** — table of every open or in-progress accountable item, grouped by `owner_role`. Columns:

| Column | Source |
|---|---|
| Owner (role · name) | projection |
| Open items | count |
| Avg age | derived from `assigned_at` |
| Overdue items | count where OD-1 |
| Aging (red bars) | bucketed by `now - due_at` |
| Last activity | `last_activity_at` |

**Section B · Stale Ownership** — items where `now - last_activity_at > 7 days` and `status ∈ {open, in_progress}`. Sorted by staleness.

**Section C · Resolution Velocity** — rolling 30-day chart of `resolved` events per role, plus close-rate (resolved / created). Drilldown to the same Pillar 1 drilldown payload (§4).

### 6.2 · Endpoints (NOT BUILT)

| Endpoint | Returns |
|---|---|
| `GET /api/admin/accountability/ownership-map` | Section A data |
| `GET /api/admin/accountability/stale` | Section B data |
| `GET /api/admin/accountability/velocity?days=30` | Section C data |

All admin-strict. All read-only. None implemented in this batch.

### 6.3 · Why this is *not* a duplicate of the Command Center

The Command Center answers **"What is hurting MASCI right now?"**

The Accountability Dashboard answers **"Where is ownership working — and where is it not?"**

They share the projection; they answer different operator questions. The Command Center is incident-oriented (per-rule RED/AMBER); the Accountability Dashboard is owner-oriented (per-role health). Both are read-only.

---

## 7 · Sequence of executive value delivery

| Phase (Roadmap detail) | What the executive gains | Visible change |
|---|---|---|
| 1A-1 · Specifications (this batch) | nothing yet | none |
| 1A-2 · Timeline collection + write hooks | future-facing audit trail | no UI change |
| 1A-3 · Projection function (read-only) | drilldown answers expand | drilldown panel shows accountability + timeline |
| 1A-4 · Command Center items use the projection | Q2 + Q3 + Q4 answered from data | item rows show real owners + real status + real due dates |
| 1A-5 · `fleet_defects` + `incidents` gain native `assigned_*` fields | per-item ownership becomes structural, not derived | no Command Center change; the projection just gets richer |
| 1A-6 · Accountability Dashboard page | role-level visibility | new page at `/admin/accountability` |
| 1B · Escalation Framework | Q5 answered | new column on items; out of scope here |

Operator authorizes each step independently. None of these are committed by this design batch.

---

## 8 · Risks specific to integration

| # | Risk | Likelihood | Severity | Mitigation in design |
|---|---|---|---|---|
| I-1 | Replacing a hardcoded "Safety" with a projection-derived display name surfaces an unexpected employee name to executives | LOW | LOW | Roadmap Phase 1A-3 ships behind a feature flag; output reviewed in preview against `masci_safety_preview` before production |
| I-2 | Projection latency adds to snapshot response time | LOW | LOW | Projection is read-only; cache TTL (15s) on `/snapshot` is preserved; per-item drilldown is on-demand |
| I-3 | `accountability` sub-object on `drilldown` confuses SPA renderers if SPA is updated before backend | NONE | — | Backend ships first; SPA reads optional keys |
| I-4 | The "current pending approver" derivation for POs (Section 3.5) requires reading approval routing, which today varies per PO | MEDIUM | LOW | Roadmap Phase 1A-4 ships a single approver-resolution helper; fallback to `requested_by_name` if routing is ambiguous |
| I-5 | The `viewed` event creates per-user-per-item write traffic | MEDIUM | LOW | Idempotent within 24h (Timeline §5); expected event volume from §8 of Timeline spec is ~0.5 MB/day |
| I-6 | The "Pulse Strip" already reconciles in production — adding projection should not break that | LOW | LOW | Projection touches `card.items[].owner`/`current_status`/`eta`; pulse counters compute from `severity` field, unchanged |

---

## 9 · Acceptance criteria (apply to the implementation phase, NOT this batch)

The implementation phase will be accepted only if:

1. The Command Center snapshot payload's shape is byte-identical except for the *content* of `owner`, `current_status`, and `eta` strings.
2. Every Command Center item has a non-empty `owner` that traces to a projection input (not a string literal).
3. Every Command Center drilldown returns an `accountability` sub-object satisfying the §3.1 contract from the Architecture spec.
4. Every Command Center drilldown returns up to 25 timeline events, newest first.
5. Existing pytest suite (`test_command_center_phase_a.py` · 20/20) continues to pass.
6. New pytest suite (`test_accountability_projection.py` and `test_accountability_timeline.py`) demonstrates contract conformance for `db.tasks`, `db.corrective_actions`, `db.po_requests`, `db.fleet_defects`, `db.incidents`, and `jobs.daily_report_missing`.
7. No regression in pulse aggregate reconciliation.

These criteria are restated in the Roadmap deliverable.

---

## 10 · What this integration is NOT

- ❌ Not an implementation. No code changes.
- ❌ Not an escalation tier. Pillar 1B owns Q5.
- ❌ Not a new card on the Command Center. The Command Center surface stays at 5 cards.
- ❌ Not a UI redesign of `AdminCommandCenter.jsx`. The component remains untouched until Phase 1A-6.
- ❌ Not authorized to ship.

This integration spec is the **invariant** the implementation phase will build against.
