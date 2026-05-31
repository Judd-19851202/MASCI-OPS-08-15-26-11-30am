# Incident Delete Remediation Plan · Critical Fix Sprint 1 · P0-3

**Batch:** OMEGA Critical Fix Sprint 1 · P0-3
**Date:** 2026-05-31
**Scope:** Remediation options for findings in `INCIDENT_DELETE_ROOT_CAUSE.md` + `INCIDENT_INTEGRITY_REPORT.md`. **NO CODE WRITTEN. NO DB MODIFIED.** Operator authorization required.

---

## 1 · Priority sequence

| # | Action | Severity | Risk if left alone | Effort estimate |
|---|---|---|---|---|
| D-1 | Dedupe `doc_id='INC-2026-00001'` in production | 🔴 P0 | Audit/report integrity | 1 hr (DB write only) |
| D-2 | Frontend: stop swallowing HTTP codes; expose error reason in toast | 🟡 P1 | Users cannot self-diagnose; support burden | 1-2 d |
| D-3 | Backend: migrate `DELETE /api/incidents/{id}` to soft-delete (`status="deleted"` + audit log) | 🟡 P1 | Orphans on 6 surfaces + no audit | 2-3 d |
| D-4 | Backend: extend cascade — delete linked notifications + tasks + R2 blobs | 🟡 P1 | Storage growth + orphan-data references | 2-3 d (if hard-delete kept) · 1 d (if soft-delete) |
| D-5 | Backend: accept Safety token on incident delete OR clarify the permission model | 🟡 P2 | Operational friction · Safety team escalates every delete | 1-2 d (depends on policy) |
| D-6 | DB: unique index on `incidents.doc_id` to prevent future dups | 🟡 P2 | recurrence prevention | <1 d |
| D-7 | Backfill `status="open"` and `resolution_status="open"` on the 7 incidents with null state | 🟡 P2 | Reporting accuracy | <1 d |
| D-8 | Investigate `doc_id_counters` atomic-increment logic | 🟡 P2 | dup-doc_id root cause | 1 d |

---

## 2 · D-1 · Dedupe `doc_id='INC-2026-00001'`

### 2.1 · Decision required

| Option | What changes | Reversibility |
|---|---|---|
| A · Promote `d9626eeb` (older record, has `incident_number`) to keep `INC-2026-00001`; rename `566a38dd` to next available `INC-2026-00012` | 1 doc updated | reversible (DB write only) |
| B · Same as A but reuse the gap (`INC-2026-00005` is unused) | 1 doc updated · uses historical gap | reversible |
| C · Merge: collapse `566a38dd` into `d9626eeb` (carry over photos · GPS · distribution_list) | 1 doc deleted · 1 doc enriched | non-reversible without backup |

**Recommendation:** **Option A** — preserves audit trail of both incidents.

### 2.2 · Exact write (operator authorization needed)

```javascript
// Production write — DO NOT EXECUTE WITHOUT AUTHORIZATION
db.incidents.update_one(
  {id: "566a38dd-c613-4989-a906-365cdf2114a9"},
  {$set: {doc_id: "INC-2026-00012", _deduped_at: ISODate(), _deduped_from: "INC-2026-00001"}}
)
```

### 2.3 · Verification

```javascript
db.incidents.aggregate([
  {$group: {_id: "$doc_id", n: {$sum: 1}}},
  {$match: {n: {$gt: 1}}}
])
// expected: 0 results
```

---

## 3 · D-2 · Frontend: surface error reasons

### 3.1 · Recommendation

Replace both `catch { toast.error("Delete failed"); }` blocks with HTTP-code aware variants:

```javascript
catch (err) {
  const code = err?.response?.status;
  if (code === 401) toast.error("Permission denied. Admin token required.");
  else if (code === 404) toast.error("Incident not found (may already be deleted).");
  else if (code >= 500) toast.error("Server error. Try again or contact support.");
  else toast.error(`Delete failed (HTTP ${code || "network"})`);
}
```

### 3.2 · Files touched

- `frontend/src/pages/IncidentsDashboard.jsx:50` (handleDelete catch)
- `frontend/src/pages/ViewIncident.jsx:209` (handleDelete catch)

### 3.3 · Effort

1-2 dev-days including pytest update.

---

## 4 · D-3 · Soft-delete migration

### 4.1 · Recommendation

Change `DELETE /api/incidents/{id}` behavior:

| Today | After soft-delete |
|---|---|
| `db.incidents.delete_one({"id": incident_id})` | `db.incidents.update_one({"id": incident_id}, {"$set": {"status": "deleted", "deleted_at": utcnow(), "deleted_by_user_id": actor.id}})` |
| 404 if not found | 404 if not found |
| no audit | `db.audit_events.insert_one({...incident_deleted...})` |
| orphan notifications/tasks/blobs | unchanged (soft-deleted incidents still referenced; reads filter out `status="deleted"`) |

### 4.2 · Read paths that need a filter

| Read path | Filter to add |
|---|---|
| `GET /api/incidents` list | `{$match: {status: {$ne: "deleted"}}}` |
| `GET /api/incidents/{id}` | return 404 if `status="deleted"` |
| Accountability projection `project_incident` | already filters resolved/closed; extend to exclude `deleted` |
| Command Center incident-related rules | filter `status: {$ne: "deleted"}` |

### 4.3 · Hard-delete path (operator-only)

Add a separate `DELETE /api/admin/incidents/{id}/purge` for operator-only hard delete with confirmation — used for true scrubbing only.

### 4.4 · Effort

2-3 dev-days including pytest update + accountability projection update.

---

## 5 · D-4 · Cascade or accept orphans

| Option | Effort | Risk |
|---|---|---|
| A · Hard-delete + cascade: also delete `notifications` (`subject_id=`), `tasks` (`source_record_id=`), R2 blob keys (`incidents/{id}/photo-*.jpg`) | 2-3 d | irreversible if scope creeps |
| B · Soft-delete + tombstone: leave linked records, but tombstone hides them | already covered in D-3 | clean |
| C · Skip cascade: accept orphans · live with R2 bloat | 0 d | growth · audit confusion |

**Recommendation:** B (soft-delete) makes D-4 unnecessary.

---

## 6 · D-5 · Safety token policy

### 6.1 · Decision required

| Option | Implication |
|---|---|
| A · Allow Safety token to soft-delete | Safety team owns their incidents · less escalation |
| B · Continue admin-only | Audit-trail integrity easier; admin gates every delete |
| C · Allow soft-delete (Safety can mark `status="deleted"`); only Admin can hard-purge | Best of both |

**Recommendation:** C if D-3 ships; B if D-3 doesn't ship.

---

## 7 · D-6 · Unique index on `doc_id`

```javascript
db.incidents.createIndex({doc_id: 1}, {unique: true, sparse: true, name: "uniq_doc_id"})
```

Must dedupe (D-1) first or the index creation will fail.

---

## 8 · D-7 · Backfill null status

```javascript
db.incidents.update_many(
  {status: null},
  {$set: {status: "open", resolution_status: "open", _backfilled_status_at: ISODate()}}
)
// Expected: matched_count=7, modified_count=7
```

---

## 9 · D-8 · `doc_id_counters` atomic-increment investigation

Read the counter doc:
```javascript
db.doc_id_counters.find({})
```

Verify the increment code uses `find_one_and_update({...}, {$inc: {seq: 1}}, returnDocument="after", upsert=True)` — the atomic Mongo pattern. If incident creation calls `find_one` then `update_one` separately, race conditions can produce duplicate `doc_id`s.

---

## 10 · Risk-if-left-alone summary

| Action | Risk | Severity |
|---|---|---|
| D-1 not done | Audit/report integrity ongoing | 🔴 |
| D-2 not done | User self-diagnosis blocked; support burden | 🟡 |
| D-3 not done | Orphans on 6 surfaces; no audit; storage growth | 🟡 |
| D-4 not done | (subsumed by D-3) | 🟡 |
| D-5 not done | Safety operational friction · admin bottleneck | 🟡 |
| D-6 not done | Future dup-doc_id recurrence | 🟡 |
| D-7 not done | Reporting null-status confusion | 🟡 |
| D-8 not done | Root cause of D-1 persists | 🟡 |

---

## 11 · Closeout

🟡 8 remediation actions ranked. **NO modifications made.** Operator authorization required for each.

🛑 STOP.
