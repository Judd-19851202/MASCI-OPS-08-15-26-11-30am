# Pillar 1 · Accountability Engine · Implementation Roadmap

**Batch:** Pillar 1 · Accountability Engine · Design only
**Date:** 2026-05-31
**Scope:** Phased implementation plan for the Accountability Engine. Each phase is independently authorizable. Acceptance criteria are explicit. **No code · no schema change · no deployment in this batch.**
**Discipline:** OMEGA · evidence-led · zero scope drift · Escalation/Notifications/Pillar 3/Pillar 4 explicitly excluded.

---

## 1 · Phasing principle

Every phase below satisfies five constraints:

| Constraint | Why |
|---|---|
| **C-A · Self-contained** | A phase can ship and be reverted without affecting the next phase. |
| **C-B · Read-only first** | Schema-touching phases come after read-only phases. |
| **C-C · Existing Command Center byte-stable** | The Phase A snapshot payload shape never changes; only the *content* of three string fields (Integration §2). |
| **C-D · Pytest-anchored** | Every phase ships its own pytest module. |
| **C-E · OMEGA-authorized** | No phase begins until operator issues an explicit `AUTHORIZE PHASE 1A-N` directive. |

---

## 2 · Phase ladder

| Phase | Title | Type | Operator authorization required? | Touches code? | Touches DB? | Touches UI? |
|---|---|---|---|---|---|---|
| **1A-1** | Specifications (this batch) | DESIGN | ✅ already authorized | ❌ | ❌ | ❌ |
| **1A-2** | `db.accountability_timeline` + write hooks | BACKEND | required | ✅ | ✅ new collection | ❌ |
| **1A-3** | Projection function (read-only) + drilldown enrichment | BACKEND | required | ✅ | ❌ | ❌ |
| **1A-4** | Command Center items wired to projection | BACKEND | required | ✅ | ❌ | ❌ (text content only) |
| **1A-5** | Native `assigned_*` fields on `incidents` + `fleet_defects` | BACKEND | required | ✅ | ✅ additive fields | ❌ |
| **1A-6** | Accountability Dashboard page (`/admin/accountability`) | FRONTEND | required | ✅ | ❌ | ✅ new page |
| **1A-7** | Pytest hardening + production deploy | DEPLOY | required | ✅ tests only | ❌ | ❌ |

**Pillar 1B (Escalation Framework) is a separate operator authorization track. None of the phases above contain escalation work.**

---

## 3 · Phase detail

### Phase 1A-1 · Specifications (THIS BATCH · already authorized)

**Deliverables:** 6 markdown documents in `/app/memory/`:
- `ACCOUNTABILITY_ENGINE_AUDIT.md`
- `ACCOUNTABILITY_ENGINE_ARCHITECTURE.md`
- `ACCOUNTABILITY_LIFECYCLE_SPEC.md`
- `ACCOUNTABILITY_TIMELINE_SPEC.md`
- `EXECUTIVE_ACCOUNTABILITY_INTEGRATION.md`
- `ACCOUNTABILITY_ENGINE_ROADMAP.md` (this file)
+ `PRD.md` and `_INDEX.md` updates.

**Acceptance:** documents written, registered, and ratified by operator review.

**Status:** 🟢 DELIVERED in this batch. No code. No deploy.

---

### Phase 1A-2 · Timeline collection + write hooks

**Goal:** Establish the append-only `db.accountability_timeline` and wire every existing code path that mutates an accountability-affecting field to also emit a matching timeline event.

**Code touches (estimate):**

| File | Change |
|---|---|
| `/app/backend/routes/accountability_timeline.py` | NEW · ~200 LOC · pure-data write/read service |
| `/app/backend/routes/tasks_notifications.py` | +20 LOC · emit `created/assigned/status_changed/resolved/closed/reopened` events when the underlying task mutates |
| `/app/backend/routes/safety_portal/corrective_actions.py` | +30 LOC · emit matching events on insert + status changes |
| `/app/backend/routes/po_requests.py` | +30 LOC · emit on every `_audit_push` call site |
| `/app/backend/routes/fleet_ops.py` | +30 LOC · emit on `open → acknowledged → repaired → cleared` transitions |
| `/app/backend/routes/employee_lifecycle.py` | +20 LOC · emit on lifecycle status_history pushes |
| `/app/backend/server.py` | +5 LOC · mount route |

**DB touches:**

| Collection | Change |
|---|---|
| `db.accountability_timeline` | NEW · indexes per Timeline spec §2.3 |

**No deletion or migration of native arrays.** Native `tasks.audit[]`, `corrective_actions.status_history[]`, `po_requests.audit[]`, `employee_lifecycle.status_history[]` continue to write as they do today.

**Pytest:** `tests/test_accountability_timeline.py` — ≥ 20 cases:

- Event shape conformance (§2.1)
- `event_seq` monotonicity
- Idempotency rules (§5)
- One-event-per-status-change invariant
- Index existence

**Acceptance criteria:**

1. Timeline collection seeds with indexes on backend boot.
2. Every existing code path that wrote to a native audit/status_history array now also writes a matching timeline row.
3. ≥ 20 pytests green.
4. Live preview probe: at least 1 timeline event exists for every accountability-affecting operation performed during a smoke test.
5. Snapshot endpoint payload byte-identical to pre-1A-2 (no command center change).
6. Backups, recovery, scheduler, Command Center auth gates unchanged.

**Rollback:** revert two commits; drop the new collection. Native arrays still hold the truth.

**Authorization gate:** operator issues `AUTHORIZE PHASE 1A-2`.

---

### Phase 1A-3 · Projection function (read-only) + drilldown enrichment

**Goal:** Build the `project_accountability(source_module, source_record)` function. Wire it into the existing Command Center drilldown endpoint (additive payload only).

**Code touches (estimate):**

| File | Change |
|---|---|
| `/app/backend/lib/accountability_projection.py` | NEW · ~250 LOC · pure-function library |
| `/app/backend/routes/command_center.py` | +30 LOC · drilldown adds `accountability` + `timeline` sub-objects (§4 of Integration spec) |

**DB touches:** read-only. No schema change.

**Pytest:** `tests/test_accountability_projection.py` — ≥ 30 cases:

- Per source_module: status mapping correctness (Lifecycle §4.1–§4.6)
- Owner derivation per A-01..A-09 of the Audit
- Backward compatibility: legacy drilldown fields unchanged
- Pulse aggregate reconciliation still exact

**Acceptance criteria:**

1. Drilldown returns the 9-question contract for every existing card item type.
2. Existing 20/20 `test_command_center_phase_a.py` continues to pass.
3. ≥ 30 new projection pytests green.
4. Snapshot payload byte-identical.
5. No new write traffic generated by the projection.

**Authorization gate:** `AUTHORIZE PHASE 1A-3`.

---

### Phase 1A-4 · Command Center items wired to projection

**Goal:** Replace the 5/9 hardcoded `owner` strings in `command_center.py` (Audit §5) with projection-derived values. Same for `current_status` and `eta`.

**Code touches (estimate):**

| File | Change |
|---|---|
| `/app/backend/routes/command_center.py` | ~40 LOC modified across the 5 card builders |

**No new endpoint. No new collection.**

**Pytest:** `test_command_center_phase_a.py` grows by ~10 cases proving the owner/status/eta now come from the projection.

**Acceptance criteria:**

1. Every card item's `owner` string traces to a projection input, not a literal.
2. Pulse aggregate reconciliation remains exact.
3. The five Path B defects (D1/D2/D5) remain green.
4. The snapshot endpoint shape is byte-identical (only string contents change).
5. Live preview probe shows real PM names on JOBS-DR-MISSING, real CA assignees on SAF-CA-OVERDUE, the **current approver** (not requester) on APP-* items, etc.

**Authorization gate:** `AUTHORIZE PHASE 1A-4`.

---

### Phase 1A-5 · Native `assigned_*` fields on `incidents` + `fleet_defects`

**Goal:** Close Audit risks **A-01** and **A-02** at the source. Add `assignee_role`, `assignee_user_id`, `assignee_employee_id`, and `assigned_at` to `db.incidents` and `db.fleet_defects` so the projection no longer has to derive owners; it reads them.

**Code touches (estimate):**

| File | Change |
|---|---|
| `/app/backend/routes/fleet_ops.py` | +50 LOC · accept `assignee_*` on create + PATCH; default `assignee_role="shop"` |
| `/app/backend/routes/safety_portal/_models.py` | +20 LOC · IncidentCreate extension |
| Incident create routes (admin / safety / portal) | +20 LOC each · accept `assignee_*` |
| `/app/backend/lib/accountability_projection.py` | refactor: prefer native field, fallback to derived |

**DB touches:**

| Collection | Change |
|---|---|
| `db.incidents` | NEW optional fields (additive; existing rows are forward-compatible — projection falls back to derived) |
| `db.fleet_defects` | same |

**Backfill strategy:** **none** in this phase. Existing rows have null `assignee_*`; the projection's pre-1A-5 fallback path applies. Backfill is a future operator decision (would require a separate authorization).

**Pytest:** `tests/test_accountability_native_owners.py` — ≥ 15 cases:

- New rows accept and persist `assignee_*`.
- Old rows continue to project correctly via fallback.
- Reassignment writes an `assigned` timeline event (per Lifecycle §6 / RA-2).
- Auth gates unchanged.

**Acceptance criteria:**

1. Incidents and fleet defects can now hold structural owners.
2. Path A (existing rows · no owner field) still projects via fallback.
3. Path B (new rows · explicit owner) projects directly from the field.
4. No regression in the existing 20+30+10 = 60 pytests from prior phases.

**Authorization gate:** `AUTHORIZE PHASE 1A-5`.

---

### Phase 1A-6 · Accountability Dashboard page

**Goal:** Ship `/admin/accountability` — the operator-facing surface described in `EXECUTIVE_ACCOUNTABILITY_INTEGRATION.md` §6.

**Code touches (estimate):**

| File | Change |
|---|---|
| `/app/backend/routes/accountability_dashboard.py` | NEW · ~300 LOC · three read-only endpoints (ownership-map, stale, velocity) |
| `/app/frontend/src/pages/admin/AdminAccountability.jsx` | NEW · ~400 LOC · 3 sections per spec |
| `/app/frontend/src/components/layout/AdminShell.jsx` | +5 LOC · sidebar link |
| `/app/frontend/src/App.jsx` | +5 LOC · register route |

**DB touches:** read-only.

**Pytest:** `tests/test_accountability_dashboard.py` — ≥ 25 cases. **Frontend testing:** `testing_agent_v3_fork` smoke test for the new page only.

**Acceptance criteria:**

1. New page reachable at `/admin/accountability` (admin-gated).
2. Three sections render against live preview data.
3. Backend endpoints admin-strict (401 unauth · 200 admin).
4. No regression in Phase A Command Center pytests.
5. No regression in scheduler/backups/recovery surfaces.

**Authorization gate:** `AUTHORIZE PHASE 1A-6`.

---

### Phase 1A-7 · Pytest hardening + production deploy

**Goal:** Consolidate the suite, run the OMEGA pre-deploy gate (12 gates), and deploy.

**Code touches:** tests only. Zero production code change.

**Pytest consolidation target:** ≥ 100 cases across the Accountability Engine modules.

**Acceptance criteria:**

1. 100/100 pytests green.
2. OMEGA pre-deploy 12-gate scorecard 12/12.
3. Live preview snapshot pulse reconciliation: exact match.
4. Production probe post-deploy: V1..V9 same shape as `COMMAND_CENTER_PRODUCTION_CERTIFICATION.md`.
5. No regression in any pre-existing test suite anywhere in `/app/backend/tests/`.

**Authorization gate:** `AUTHORIZE PHASE 1A-7` — and a separate explicit production-deploy authorization (same model as Path B).

---

## 4 · What is OUT of this roadmap (explicit non-goals)

| Out-of-scope item | Reason |
|---|---|
| Escalation Framework (Pillar 1B) | Separate authorization track; cannot start until 1A-7 ships |
| New email / SMS / Slack / cron notifications | Explicitly excluded by directive |
| New dashboard cards on the Command Center | Surface is locked at 5 cards |
| Migration / deletion of `tasks.audit[]`, `corrective_actions.status_history[]`, `po_requests.audit[]`, `employee_lifecycle.status_history[]` | Timeline is additive, not replacement |
| Backfill of historical owners on `incidents` / `fleet_defects` | Requires separate authorization |
| White-label / multi-company / billing | Pillar 3 / Pillar 4 |
| Backup, recovery, scheduler, storage, R2, drill framework | FROZEN |
| Refactor of `command_center.py` beyond the targeted changes | OMEGA discipline |

---

## 5 · Risk register (cumulative across phases)

| # | Risk | Probability | Severity | Phase | Mitigation |
|---|---|---|---|---|---|
| RM-1 | Timeline write contention with high-throughput sources (fleet_defects, DR-missing) | LOW | LOW | 1A-2 | Append-only insert with single index; size estimate 0.5 MB/day (Timeline §8) |
| RM-2 | Projection latency on snapshot | LOW | LOW | 1A-3 | 15s cache TTL preserved; projection is per-item, not aggregate |
| RM-3 | Surface-visible owner changes startle the operator (e.g. "Safety" → "Tom") | MEDIUM | LOW | 1A-4 | Phase 1A-4 ships behind a config flag; preview-validated before prod |
| RM-4 | New `assignee_*` fields on existing collections introduce schema drift | LOW | LOW | 1A-5 | All new fields optional; null-safe projection |
| RM-5 | New dashboard page introduces a new failure surface | MEDIUM | LOW | 1A-6 | Read-only; gated behind admin-strict; rollback by removing route |
| RM-6 | The viewed-event spec creates per-user-per-item writes that mistakenly fire on bot/CI traffic | LOW | LOW | 1A-2 | Idempotent within 24h; route boundary gates on actor.user_id non-null |
| RM-7 | Operator authorizes a phase out of order (e.g. 1A-6 before 1A-3) | LOW | MEDIUM | all | Each phase declares prerequisites; agent refuses to start 1A-N without 1A-(N-1) shipped |

---

## 6 · Sequencing reminder (dependency graph)

```
1A-1 (specs · this batch)
   │
   ▼
1A-2 (timeline)
   │
   ▼
1A-3 (projection · read-only)
   │   ┌────────────────────────┐
   ▼   ▼                        │
1A-4 (Command Center wiring)   1A-5 (native assignee fields)
   │                            │
   ▼                            ▼
1A-6 (Accountability Dashboard)
   │
   ▼
1A-7 (pytest hardening + deploy)
```

1A-3 can ship before 1A-2 only if the projection ignores timeline-derived fields (acceptable degraded mode). Recommended order: 1A-2 → 1A-3.

1A-4 and 1A-5 can ship in either order; 1A-5 is **optional** for the executive integration to work (the projection already has fallbacks).

---

## 7 · Acceptance summary (one-line)

The Accountability Engine is fully delivered when, for every RED or AMBER item on the Executive Command Center, the operator can click in and **read — from data, not from a string literal — who owns it, when it was assigned, when it is due, when it was last touched, and what has happened on it**, with **zero regression** to the Phase A Command Center, the Recovery Dashboard, the backup scheduler, or any pre-existing test.

This batch ships the specifications that make that delivery possible. **No code follows.**

---

## 8 · STOP condition

🛑 **All six design deliverables and the PRD/INDEX updates are complete.**
🛑 **No code change · no schema migration · no endpoint · no UI · no deploy.**
🛑 **Awaiting operator's explicit `AUTHORIZE PHASE 1A-2` directive (or any reordering / rejection).**

OMEGA discipline applies. NO DRIFT.
