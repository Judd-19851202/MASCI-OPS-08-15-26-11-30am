# Command Center · Accountability Consumption Report · Phase 1A-4

**Batch:** Pillar 1 · Phase 1A-4
**Date:** 2026-05-31
**Scope:** Document how each Command Center card now consumes the Accountability Projection Layer for ownership derivation, and how the drilldown endpoint surfaces the canonical projection + timeline. Anchored to live code line numbers in the post-1A-4 `command_center.py` (md5 `38bae4866b672dd254f6cfc6e49b9a8d`).
**Discipline:** OMEGA · evidence-only.

---

## 1 · Consumption mode

The Command Center now consumes the projection **in-process**, not over HTTP. The projection library lives at `/app/backend/lib/accountability_projection.py` and is imported directly:

```python
# command_center.py · line 12
from lib import accountability_projection as _acc_proj
```

This avoids an internal HTTP round-trip for every card item and keeps the snapshot endpoint's cold latency bounded. The Accountability **service** (`/api/admin/accountability/*` from Phase 1A-3) remains the external consumer surface; the Command Center is the **internal** consumer of the same contract.

---

## 2 · Per-card consumption map

### 2.1 · Card 1 · Jobs Today

| Rule | Pre-1A-4 owner derivation | Post-1A-4 owner derivation |
|---|---|---|
| JOBS-DR-MISSING | `job.primary_pm_name` ∥ `job.primary_pm_email` ∥ "Unassigned PM" (line 328) | unchanged (this is already a projection-style derivation — virtual signal kind) |
| JOBS-ISSUE-NO-OWNER | hardcoded "UNASSIGNED" (line 371) | unchanged (truthful by definition — surface IS the unassigned set) |
| JOBS-ISSUE-NO-PATH | hardcoded `"Safety"` (was line 406) | **`await _acc_proj.project_incident(db, inc)["owner_display_name"]`** (new line ≈ 410) |

### 2.2 · Card 2 · Safety Today

| Rule | Pre-1A-4 owner | Post-1A-4 owner |
|---|---|---|
| SAF-CRITICAL-UNRESOLVED | hardcoded `"Safety"` (line 478) | **`await _acc_proj.project_incident(db, inc)["owner_display_name"]`** |
| SAF-OSHA-OPEN | hardcoded `"Safety"` (line 532) | **`await _acc_proj.project_incident(db, o)["owner_display_name"]`** per OSHA-unresolved incident |
| SAF-CA-OVERDUE | `ca.assigned_to_name` ∥ "Unassigned" (line 568) | unchanged (already real per-row) — but now the projection's drilldown payload exposes the same name through the canonical contract |
| SAF-CA-CHRONIC | (no items in current preview snapshot) | future-ready |

### 2.3 · Card 3 · Equipment Today

| Rule | Pre-1A-4 owner | Post-1A-4 owner |
|---|---|---|
| EQP-OOS-OLD | hardcoded `"Shop"` (line 660) | **`_acc_proj.project_fleet_defect(d)["owner_display_name"]`** · sync projection · returns `acknowledged_by_name` when present, "Shop" otherwise |
| EQP-OOS-NEW | (no items in current preview snapshot) | future-ready (same projection function) |
| EQP-BACKLOG | aggregate counter · no per-item owner | unchanged (no per-item to attribute) |

**Note:** the EQP-OOS-OLD `find()` projection was expanded to also fetch `acknowledged_at`, `acknowledged_by_name`, `reported_at`, `severity`, `item_text`, `repaired_at`, `repaired_by_name` — so the projection function has enough fields to compute the canonical shape. The list of returned items is unchanged.

### 2.4 · Card 4 · Accountability Overdue

Already sourced directly from `db.tasks`. No owner-string change needed in this phase (the projection mirrors what was already being read). However:

| Field | Source post-1A-4 |
|---|---|
| `owner` | `task.assignee_role` capitalized (unchanged in snapshot · same as Phase A) |
| Drilldown enrichment | `accountability` sub-object now exposes `assignee_user_id`, `due_at`, `last_activity_kind`, etc. for the same task |

### 2.5 · Card 5 · Approvals Aging

| Rule | Pre-1A-4 owner | Post-1A-4 owner |
|---|---|---|
| APP-AMBER · APP-RED · APP-WEEK | `p.get("requested_by_name") or "Requester"` (line 874) — **the requester, not the approver** | **`_acc_proj.project_po_request(p)["owner_display_name"]`** → resolves to `"Pending Approver"` for pending statuses, requester for terminal-cancelled (Lifecycle §4.3) |

**This is the operationally most important change in Phase 1A-4.** Per the directive: "Approver-not-requester verified".

**Note:** the APP-* `find()` projection was expanded to also fetch `requested_by_role`, `requested_by_user_id`, `requested_by_employee_id` so the projection function has the requester chain available for the Rejected/Cancelled terminal case.

---

## 3 · Drilldown enrichment

### 3.1 · Endpoint

`GET /api/admin/command-center/drilldown/{card_id}/{item_id}` — admin-strict.

### 3.2 · Response shape (post-1A-4)

```json
{
  // ── Legacy keys (unchanged · byte-stable for SPA backward compat) ──
  "card_id":              "<card>",
  "item_id":              "<id>",
  "source_doc":           { ...raw row from source collection... },
  "actions_underway":     "<source status or 'see source'>",
  "owner":                "<owner_display_name from projection, or legacy chain fallback>",
  "expected_resolution":  "<due date or 'Not set'>",

  // ── Phase 1A-4 additive keys ──
  "accountability": {
    "accountability_id":   "...",
    "source_module":       "...",
    "source_record_id":    "...",
    "title":               "...",
    "owner_role":          "...",
    "owner_user_id":       null,
    "owner_employee_id":   null,
    "owner_display_name":  "...",
    "assigned_at":         "...",
    "assigned_by":         { "role": "...", "name": "..." },
    "due_at":              "...",
    "status":              "<canonical>",
    "priority":            "...",
    "first_viewed_at":     null,
    "first_viewed_by":     null,
    "last_activity_at":    "...",
    "last_activity_kind":  "...",
    "escalation_level":    0,                // RESERVED · always 0
    "resolved_at":         null,
    "resolved_by":         null,
    "resolution_notes":    null,
    "overdue":             false,
    "timeline_events":     [ ... ]
  },
  "timeline": [ ...last 25 canonical events, oldest→newest ... ]
}
```

### 3.3 · Dispatch logic (line 1098-1135 post-1A-4)

```python
if card_id == "accountability":
    accountability_payload = _acc_proj.project_task(doc)
elif card_id == "approvals":
    accountability_payload = _acc_proj.project_po_request(doc)
elif card_id == "equipment":
    accountability_payload = _acc_proj.project_fleet_defect(doc)
elif card_id == "safety":
    # Either incident OR corrective_action — distinguish by fields.
    if "assigned_to_name" in doc or "status_history" in doc:
        accountability_payload = _acc_proj.project_corrective_action(doc)
    else:
        accountability_payload = await _acc_proj.project_incident(db, doc)
elif card_id == "jobs":
    # jobs_master rows have no projection (not in 6 certified sources)
    # — fall through to None. Incident/CA rows project as above.
    ...
```

**Error tolerance:** if projection fails for any reason (malformed row, missing required field, unexpected exception), the drilldown still returns 200 with `accountability=None`. The legacy keys are always present. **The drilldown never breaks because of projection errors.**

---

## 4 · The legacy `owner` field — backward-compat semantics

The drilldown's legacy `owner` string now follows this chain:

```
owner = projection.owner_display_name              (when accountability is non-null)
     or doc.assigned_to_name                       (CA fallback)
     or doc.assignee_user_id                       (task fallback)
     or doc.requested_by_name                      (PO fallback · LEGACY · not preferred)
     or doc.primary_pm_name                        (job fallback)
     or doc.assignee_role                          (task role fallback)
     or "Unassigned"
```

When the projection is available, `owner === accountability.owner_display_name`. This is enforced by `test_drilldown_owner_matches_projection_when_accountability_present`.

When the projection is unavailable (jobs_master rows, projection error), the chain falls back to the pre-1A-4 behavior — guaranteeing the legacy field is always populated.

---

## 5 · Cache behavior

| Cache | Pre-1A-4 | Post-1A-4 |
|---|---|---|
| Snapshot endpoint (15s TTL) | preserved · per-key `("snapshot",)` | preserved · same key |
| Drilldown endpoint | uncached (always fresh) | uncached (always fresh) — projection is fast on a single document |
| Projection module | stateless (pure function) | unchanged |

No new cache layer introduced.

---

## 6 · Performance impact (live preview)

| Operation | Pre-1A-4 cold | Post-1A-4 cold | Delta |
|---|---|---|---|
| `/snapshot` | ~700 ms | ~750 ms | +50 ms (additional incident projection async lookups per OSHA/critical incident · capped at 5 items each) |
| `/drilldown` (single item) | ~150 ms | ~200 ms | +50 ms (single projection · CA lookup for incident-class card_ids only) |
| `/snapshot` warm (15s cache hit) | ~80 ms | ~80 ms | unchanged |

Latencies remain within Phase 1A-3's performance envelope (cold ≤ 2 s). No tuning required.

---

## 7 · What is NOT consumed in this phase

| Projection capability | Consumed by Command Center? | Why not (if no) |
|---|---|---|
| `timeline_events[]` per source | ✅ surfaced on `/drilldown` (last 25) | — |
| Canonical `status` mapping | ⚠️ partial — currently surfaced only via `accountability.status` on drilldown; the legacy `current_status` string on snapshot items is unchanged | preserving existing visual is the directive |
| `due_at` canonical | ⚠️ partial — surfaced via `accountability.due_at` on drilldown; legacy `eta` string on snapshot items unchanged | preserving existing visual is the directive |
| `escalation_level` | ✅ exposed via `accountability.escalation_level` on drilldown (always 0) | Pillar 1B reservation |
| Virtual-signal projections (DR-missing, no-owner, etc.) | ❌ Command Center still uses its own per-rule construction for these | virtual signals don't have a backing row · Command Center IS the source · projection would be circular |

The directive's scope explicitly limits Phase 1A-4 to **owner string replacement + drilldown enrichment**. Other projection surfaces (canonical status string on snapshot items, due_at on snapshot items, virtual-signal projection) are deferred.

---

## 8 · Frontend impact

| Concern | Status |
|---|---|
| `AdminCommandCenter.jsx` modified? | ❌ **No** — md5 stable at `4cb825b4830871d1d407d206d4ae5519` |
| Sidebar modified? | ❌ No |
| Routes modified? | ❌ No |
| New SPA fetch added? | ❌ No |
| Visual changes? | ❌ No — the field that renders the `owner` text in the SPA receives a different string but renders it identically |

Per the directive: **"Preserve existing visual design and card structure."** Achieved by changing only the *content* of the existing `owner` string field — not its shape, presence, or rendering path.

---

## 9 · OMEGA discipline check

| Discipline rule | Verdict |
|---|---|
| Source workflows untouched | 🟢 |
| Projection library byte-stable | 🟢 |
| Service router byte-stable | 🟢 |
| Frontend untouched | 🟢 |
| No new collection · no new endpoint | 🟢 |
| Escalation NOT activated | 🟢 (`escalation_level=0` enforced) |
| No notifications/emails/SMS/cron | 🟢 |
| No deployment | 🟢 |

---

## 10 · Closeout

🟢 The Executive Command Center derives ownership and accountability context from the Accountability Service rather than hardcoded workflow-specific logic. Five rule paths converted · drilldown enriched · frontend untouched · 92/92 prior pytests still green plus 16/16 new 1A-4 pytests green (108 total) · live preview probe confirms the approver-not-requester fix and the drilldown shape.

🛑 **STOPPED.**
