# Pillar 1 · Accountability Timeline Specification

**Batch:** Pillar 1 · Accountability Engine · Design only
**Date:** 2026-05-31
**Scope:** Define the shape, semantics, and read pattern of the single append-only `db.accountability_timeline` collection that becomes the platform's universal audit trail for accountable items. **No code · no inserts · no migration.**
**Discipline:** OMEGA · evidence-only · no new endpoints or fan-out · no Pillar 1B escalation.

---

## 1 · Intent

§4 of the Audit identified **5 divergent timeline shapes** in production today (`tasks.audit[]`, `corrective_actions.status_history[]`, `po_requests.audit[]`, `employee_lifecycle.status_history[]`, `admin_audit`). The Executive Command Center cannot answer "What has happened on this item?" in a single read without a per-source reducer.

The timeline collection collapses all five into one append-only event log per accountable item.

---

## 2 · Collection: `db.accountability_timeline`

### 2.1 · Document shape

```
{
  "id":                  "<uuid>",                      // event id (unique)
  "accountability_id":   "<uuid>",                      // = §3.1 of Architecture
  "source_module":       "<enum>",                      // = ALLOWED_SOURCE_MODULES + new entries
  "source_record_id":    "<string>",                    // row id in the source collection
  "event_kind":          "<enum>",                      // see §3
  "event_seq":           <integer>,                     // monotonic per accountability_id (1, 2, 3, ...)
  "actor": {
    "role":              "<ALLOWED_ROLES + operations_leadership>",
    "name":              "<string>",
    "user_id":           "<string|null>",
    "employee_id":       "<string|null>"
  },
  "at":                  "<ISO-8601 UTC>",              // never local-time
  "notes":               "<string|null>",               // ≤ 2000 chars
  "from_status":         "<canonical|null>",            // only when event_kind="status_changed"
  "to_status":           "<canonical|null>",            // only when event_kind="status_changed"
  "changes":             { "<field>": { "from": ..., "to": ... }, ... } | null,
  "linked_notification_id": "<string|null>",            // if the event spawned a bell entry (read-only mirror)
  "ip":                  "<string|null>",               // request IP, when available; redacted in non-admin reads
  "user_agent":          "<string|null>",               // short UA string; never PII
  "system_origin":       "<string>"                     // free-tag (e.g. "cli", "ui", "scheduled", "import")
}
```

### 2.2 · Field rules

| Field | Rule |
|---|---|
| `id` | UUIDv4; unique. The collection's `_id` is **not** projected (MongoDB ObjectId is excluded from every response — pattern matches the rest of the platform). |
| `accountability_id` | Required; foreign reference. Index. |
| `source_module` | Required; from the enum extension defined in `ACCOUNTABILITY_ENGINE_ARCHITECTURE.md` §3.1. Index. |
| `source_record_id` | Required. Compound index `(source_module, source_record_id, at)`. |
| `event_kind` | Required; one of §3. |
| `event_seq` | Required; equals `count(timeline where accountability_id == self) + 1` at insert. Index. |
| `actor` | Required. `role` is mandatory; `name` is mandatory (defaults to role label if unknown — e.g. "Safety"). `user_id` / `employee_id` are optional. |
| `at` | Required. Stored as ISO-8601 UTC string AND BSON `datetime` — write both forms (per platform date-doctrine; same approach as the D5 Path B helpers). |
| `notes` | Optional. Required when `event_kind ∈ {commented, status_changed(to_status==cancelled), reopened, escalated}`. |
| `from_status` / `to_status` | Required iff `event_kind == "status_changed"`; null otherwise. |
| `changes` | Required iff `event_kind ∈ {updated, assigned}` and at least one field changed. |
| `linked_notification_id` | Read-only mirror of any `db.notifications` row spawned by the event; the timeline does not author notifications. |
| `ip`, `user_agent` | Optional. Captured at the route boundary only. Redacted in non-admin responses. |
| `system_origin` | Required. Free-form tag for forensic queries. |

### 2.3 · Indexes (defined now, created in implementation phase)

| Index | Purpose |
|---|---|
| `{accountability_id: 1, event_seq: 1}` unique | Timeline read for a single item, ordered |
| `{source_module: 1, source_record_id: 1, at: -1}` | Drill from a source row to its timeline |
| `{actor.user_id: 1, at: -1}` | "What did this user do?" admin forensic |
| `{at: -1}` | Global recent-activity feed |
| `{event_kind: 1, at: -1}` partial on `event_kind ∈ {resolved, closed, reopened, escalated}` | Executive close-rate analytics |

### 2.4 · TTL

**Append-only. NO TTL in this batch.** The platform's existing retention strategy is "data lives until explicitly archived"; accountability events are operational evidence that must persist. If retention becomes a concern at scale, a future phase may add a TTL on `closed` items older than N years — but that is **out of scope** here.

---

## 3 · `event_kind` enumeration

| Kind | When emitted | Who emits |
|---|---|---|
| `created` | Source row is inserted (1 per row, always) | The route that created the source row |
| `assigned` | `owner_role`, `owner_user_id`, or `owner_employee_id` is set or changed (RA-2 of Lifecycle Spec) | Any route mutating the owner |
| `viewed` | First time `owner_user_id` (or any owner-eligible user, when role-only) opens the detail surface; idempotent within 24h per accountability_id × user_id | Detail-page route — gated by middleware (Phase 1A-3) |
| `updated` | Any non-status, non-owner field on the source row mutates | Any update route |
| `commented` | A free-text comment is appended | The comment route |
| `status_changed` | Canonical status transitions (Lifecycle §2) | Any route that mutates status |
| `resolved` | Canonical status becomes `resolved` (one per resolution) | Closure route |
| `closed` | Canonical status becomes `closed` | Closure route |
| `reopened` | A `resolved` or `closed` item moves back to `open`/`in_progress` | Reopen route |
| `escalated` | RESERVED · Pillar 1B only · **never emitted in this batch** | n/a |

**Hard constraint:** every state-changing operation produces **exactly one** `status_changed` row. If the same operation also resolves or closes, it produces an additional `resolved` or `closed` row at the same `at`. This is the explicit double-event pattern so the timeline can answer both "did status change?" and "was this the closure event?" with separate filters.

---

## 4 · Read patterns

### 4.1 · Single-item timeline (for drilldown)

```
GET /api/admin/accountability/timeline/{accountability_id}?limit=50
```
- Returns events ordered by `event_seq DESC`.
- `event_seq=1` is always the `created` event.
- Admin-strict in this batch; per-portal access TBD in Phase 1A-4.

### 4.2 · Per-source pivot (for non-task collections)

When the operator drills into an `incident` or `fleet_defect` (which has no internal task linkage), the read uses:

```
GET /api/admin/accountability/timeline?source_module=safety.incidents&source_record_id=<id>
```

This is the same collection, indexed by `(source_module, source_record_id, at)`.

### 4.3 · Recent-activity (executive)

```
GET /api/admin/accountability/recent?since=<iso>&kind=resolved,closed,reopened
```
- Backs the future "Accountability Pulse" panel (out of scope of this batch).

**None of these endpoints exist in this batch.** They are the *contract* the implementation phase will satisfy.

---

## 5 · Idempotency rules

| Event | Idempotency window | Behavior on duplicate |
|---|---|---|
| `created` | one per accountability_id forever | hard reject duplicate insert |
| `viewed` | one per accountability_id × actor.user_id within 24h | silently no-op |
| `assigned` | none — every owner change is recorded | always insert |
| `updated` | merge within 60 seconds if same actor + same accountability_id + non-overlapping field set | last-write timestamp wins; changes merged |
| `commented` | none | always insert |
| `status_changed` | one per `(from_status, to_status, actor.user_id)` within 5 seconds | silently no-op (debounces double-click) |
| `resolved` / `closed` / `reopened` | one per status entry into the target state | hard reject duplicate within the same status segment |

---

## 6 · Read-side construction rules

The projection function (Architecture §6) builds `last_activity_at`, `last_activity_kind`, and `first_viewed_at` from this collection by:

```
first_viewed_at = min(at) where event_kind="viewed" and actor.user_id == owner_user_id
last_activity_at = max(at) over all events for accountability_id
last_activity_kind = event_kind of the event with last_activity_at
escalation_level = 0   // reserved · Pillar 1B
```

`escalation_level` is **always read as 0** in this batch. The field is structurally reserved on the projection; no event ever sets it; no code ever reads `event_kind="escalated"` because the kind is never emitted.

---

## 7 · Non-destructive co-existence with native arrays

This batch does **not** delete or migrate `tasks.audit[]`, `corrective_actions.status_history[]`, `po_requests.audit[]`, or `employee_lifecycle.status_history[]`. They continue to live on their source rows.

When implementation lands, every code site that writes to a native array will also (in the same transaction-ish block, accepting the existing fire-and-forget pattern used by `task_service.create()`) write the matching `accountability_timeline` event. Removal of native arrays is **not authorized** and is **not on the roadmap**.

This means the timeline is **additive**, not **replacement**. The cost: one extra collection write per accountability-affecting operation. The benefit: one collection answers Pillar 1's executive questions.

---

## 8 · Size and growth estimate (sanity check)

Assumption set, anchored on the live preview snapshot probed in `COMMAND_CENTER_RECERTIFICATION_REPORT.md`:

- Active jobs: 29 → ~10 daily reports / job / day = ~290 DR submissions/day (potential `created` + `viewed` events).
- Open incidents stream: 2-10/week → ~5 events per incident lifecycle.
- PO requests: 139 pending in AMBER bucket today → ~50 lifecycle transitions/day across the fleet.
- Fleet defects: 44 backlog → ~10 transitions/day.
- Corrective actions: 4 overdue + chronic → ~5 transitions/day.

**Order-of-magnitude expectation:** 500–1,500 timeline events/day. Average row size ≈ 350 bytes. **≈ 0.5 MB/day → ~180 MB/year.** The append-only collection is dwarfed by `db.daily_reports` (which today already inlines photo blobs). No retention concern in the 5-year horizon.

---

## 9 · Conformance contract for source workflows (implementation phase)

When implementation lands, every source workflow that emits accountability changes must:

1. Compute the `accountability_id` deterministically (see Architecture §3.1).
2. Insert the matching event in `db.accountability_timeline` **after** the source-row mutation succeeds.
3. Use the canonical `event_kind` for the operation; no custom kinds.
4. Capture `actor`, `system_origin`, and `at` at the route boundary, not in the data layer.
5. Never delete or update timeline rows. Corrections go in via a new `updated` event referencing the prior `event_seq` in `notes`.

This contract is enforced by code review and a `tests/test_accountability_timeline_invariants.py` suite in the implementation phase — not in this batch.

---

## 10 · What this timeline is NOT

- ❌ Not a notification feed. Notifications continue to live in `db.notifications`.
- ❌ Not a global admin audit log. That stays in `db.admin_audit`; `accountability_timeline` is per-item operational evidence.
- ❌ Not an escalation engine. `event_kind="escalated"` is reserved and never written in this batch.
- ❌ Not a replacement for source-collection state. Source rows are still the system of record for their domain.
- ❌ Not a workflow engine. The timeline records facts; it does not enforce transitions.

The timeline is the **single readable history** of every accountable item — built by addition, defined by this spec, implemented when the operator authorizes the roadmap.
