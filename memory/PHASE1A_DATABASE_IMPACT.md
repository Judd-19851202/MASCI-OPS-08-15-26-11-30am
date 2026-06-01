# Phase 1A · Database Impact

**Program:** OMEGA · PCP · Phase 1A · Final Build Package
**Mode:** Design-only · companion to `PHASE1A_FINAL_ARCHITECTURE.md`
**Date:** 2026-06-01

---

## 1 · Summary

| Operation | Count |
|---|---|
| New collections | **2** (`workflow_state_events` · `jha_acknowledgements`) |
| Modified collections | **5** (incidents · daily_reports · payroll_variance_batches · qaqc_inspections · inspections) |
| Schema-additive fields | **~28** (none removed) |
| New indexes | **9** (3 on each new collection · 1 on each modified collection) |
| Startup migrations | **5** (one per modified collection · idempotent) |
| Data shape conversion | **1** (qaqc_inspections.deficiencies: text array → object array · read-shim) |
| Backward incompatibility | **0** (all additive; existing payloads unchanged) |

---

## 2 · New collection · `workflow_state_events`

### 2.1 · Document shape
```json
{
  "_id": "ObjectId",
  "id": "uuid",
  "workflow_type": "incident | daily_report | payroll_variance_batch | qaqc_inspection | qaqc_deficiency | site_inspection | site_finding",
  "doc_id": "<workflow record id>",
  "parent_doc_id": "<parent id for child records> | null",
  "from_state": "OPEN | IN_PROGRESS | PENDING_REVIEW | PENDING_CLOSURE | CLOSED | null",
  "to_state":   "OPEN | IN_PROGRESS | PENDING_REVIEW | PENDING_CLOSURE | CLOSED",
  "actor_user_id": "string | null",
  "actor_role": "safety | admin | super-admin | hr | pm | fl | system-auto",
  "actor_display_name": "string",
  "reason": "string | null",
  "metadata": { "...arbitrary": "..." },
  "occurred_at": "ISO ts",
  "ttl_at": "ISO ts (occurred_at + 7y)"
}
```

### 2.2 · Indexes
```js
db.workflow_state_events.createIndex(
  { workflow_type: 1, doc_id: 1, occurred_at: -1 },
  { name: "ix_state_events_per_doc" }
);

db.workflow_state_events.createIndex(
  { workflow_type: 1, to_state: 1, occurred_at: -1 },
  { name: "ix_state_events_admin_filter" }
);

db.workflow_state_events.createIndex(
  { workflow_type: 1, doc_id: 1, to_state: 1, actor_user_id: 1, occurred_at_minute: 1 },
  { unique: true, name: "ix_state_events_idempotency" }
);

db.workflow_state_events.createIndex(
  { ttl_at: 1 },
  { expireAfterSeconds: 0, name: "ix_state_events_ttl" }
);
```

### 2.3 · Storage estimate
* Avg row: ~600 B
* Expected throughput: ~50 transitions/week per active workflow type × 5 workflows × 52 weeks = **~13,000 rows/year**
* 7y retention: ~91,000 rows · ~55 MB · negligible

---

## 3 · New collection · `jha_acknowledgements`

### 3.1 · Document shape (per `PHASE1A_WORKFLOW_DESIGN.md` §5.5.3)
* 19 fields including base64 signature OR `verbal_attested` token + attester role
* 7-year TTL via `ttl_at`

### 3.2 · Indexes
```js
db.jha_acknowledgements.createIndex(
  { jha_id: 1, shift_date: -1 },
  { name: "ix_jha_ack_per_jha_day" }
);

db.jha_acknowledgements.createIndex(
  { job_id: 1, shift_date: -1 },
  { name: "ix_jha_ack_per_job_day" }
);

db.jha_acknowledgements.createIndex(
  { acknowledged_at: -1 },
  { name: "ix_jha_ack_recent" }
);

db.jha_acknowledgements.createIndex(
  { ttl_at: 1 },
  { expireAfterSeconds: 0, name: "ix_jha_ack_ttl" }
);
```

### 3.3 · Storage estimate
* Avg row: ~3 KB (base64 signature dominates)
* ~500 acks/week × 52 weeks = ~26,000 rows/year
* 7y retention: ~182,000 rows · ~550 MB

---

## 4 · Modified collections

### 4.1 · `incidents`
**Fields added (additive · default `OPEN` via migration):**
```
lifecycle_state           str       OPEN | IN_PROGRESS | PENDING_REVIEW | PENDING_CLOSURE | CLOSED
state_changed_at          ISO ts
state_changed_by          str (actor_user_id)
closed_at                 ISO ts (null until CLOSED)
closed_by                 str
reopened_count            int (default 0)
osha_closure_attested     bool (default false)
_lifecycle_migrated_at    ISO ts (Sprint 1B-style marker)
```
Index added: `{ lifecycle_state: 1, created_at: -1 }` for admin queries.

### 4.2 · `daily_reports`
**Fields added:**
```
lifecycle_state           str  default OPEN
state_changed_at          ISO ts
state_changed_by          str
approved_at               ISO ts
approved_by               str
return_reason             str (cleared on resubmission)
revision_count            int (default 0)
_lifecycle_migrated_at    ISO ts
```
Index added: `{ lifecycle_state: 1, incident_date: -1, job_id: 1 }`.

### 4.3 · `payroll_variance_batches`
**Fields added:**
```
lifecycle_state           str  default OPEN
state_changed_at          ISO ts
state_changed_by          str
finalized_at              ISO ts
finalized_by              str
finalization_attestation  str
_lifecycle_migrated_at    ISO ts
```
Index added: `{ lifecycle_state: 1, week_ending: -1 }`.

### 4.4 · `qaqc_inspections`
**Fields added:**
```
lifecycle_state                str  default OPEN
state_changed_at               ISO ts
state_changed_by               str
closed_at                      ISO ts
closed_by                      str
deficiencies_format_version    int (default 2)  # 1=text array · 2=object array
_lifecycle_migrated_at         ISO ts
```

**Deficiencies field reshape (read-shim · no destructive migration):**
* Legacy v1: `deficiencies: ["text 1", "text 2", ...]`
* New v2: `deficiencies: [{id, text, lifecycle_state, assigned_to, resolved_at, resolved_by, resolution_notes}, ...]`
* On read: v1 records returned in v2 shape with `id=md5(inspection_id:index)`, `lifecycle_state="OPEN"`, other fields null
* On write: always v2 shape; `deficiencies_format_version=2` stamped

Index added: `{ lifecycle_state: 1, inspection_date: -1, job_id: 1 }`.

### 4.5 · `inspections` (Site Safety)
**Fields added:**
```
lifecycle_state           str  default OPEN
state_changed_at          ISO ts
state_changed_by          str
closed_at                 ISO ts
closed_by                 str
findings                  array (new field)
findings_format_version   int (default 1)  # 1=new structured array
_lifecycle_migrated_at    ISO ts
```
Legacy `inspections` records get `findings: []` on migration. New finding fields collected on next submission.

Index added: `{ lifecycle_state: 1, inspection_date: -1, job_id: 1 }`.

---

## 5 · Startup migrations (idempotent · ~50 LOC each)

Each migration block follows this pattern:

```python
async def _migrate_incidents_lifecycle(db) -> dict:
    """Ensure every incident has lifecycle_state set; idempotent."""
    res = await db.incidents.update_many(
        {"lifecycle_state": {"$exists": False}},
        {"$set": {"lifecycle_state": "OPEN",
                  "_lifecycle_migrated_at": _now()}}
    )
    return {"workflow": "incidents", "migrated": res.modified_count}
```

Migrations run as part of `server.py:_startup_indexes_and_migrations()` (existing hook). All 5 run sequentially. Each emits a log line + writes to `audit_events` with kind `phase1a_migration`.

---

## 6 · Backwards compatibility audit

| Risk | Mitigation |
|---|---|
| Existing API clients receive new fields | Additive only · clients ignoring unknown fields unaffected (standard JSON parsing) |
| `IncidentSummary` list response shape | UNCHANGED · `lifecycle_state` deliberately NOT added to summary (Phase 1B can add) |
| Daily Report `audit_footer` derived endpoint | UNCHANGED |
| Photo viewer raw endpoint | UNCHANGED |
| Existing `corrected_on_site` and CAPA linkage | UNCHANGED · accountability read-shim still derives if `lifecycle_state` absent |
| Payroll variance row decisions | UNCHANGED · batch-level closure is the only new state |
| QA/QC v1 text-array consumers | Read-shim returns v2 shape · v1 clients can still parse `text` field |
| Cache invalidation | None needed · new fields are additive · no projection changes |

---

## 7 · MongoDB load expectations (post-deploy)

| Collection | Writes/week | Reads/week | Index footprint | Storage growth |
|---|---|---|---|---|
| `workflow_state_events` | ~50 | ~1500 (per-doc history reads) | ~12 MB | ~55 MB/year |
| `jha_acknowledgements` | ~500 | ~3000 | ~22 MB | ~550 MB/year |
| `incidents` (existing) | ~3 (unchanged) | unchanged | +3 MB (new index) | negligible |
| `daily_reports` (existing) | ~150 (unchanged) | unchanged | +5 MB (new index) | negligible |
| `payroll_variance_batches` | ~1 (unchanged) | unchanged | +0.5 MB | negligible |
| `qaqc_inspections` | ~5 (unchanged) | unchanged | +1 MB | negligible |
| `inspections` | ~10 (unchanged) | unchanged | +1 MB | negligible |

Total new storage: ~605 MB/year. Current `masci_safety` DB size on production: ~8 GB. **<7% growth/year. No infra impact.**

---

## 8 · OMEGA discipline

🟢 Design-only · 2 new collections specified · 5 modified collections enumerated · 9 new indexes · 5 idempotent startup migrations · 0 destructive changes · backward compatibility audited.

🛑 Continue to `PHASE1A_UI_IMPACT.md`.
