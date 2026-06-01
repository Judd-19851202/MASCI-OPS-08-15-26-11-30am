# Incident Lifecycle Audit · OMEGA Forensic Report

**Batch:** OMEGA · Forensic Audit · Incident Lifecycle Status
**Mode:** READ-ONLY · evidence-first · zero code changes
**Target:** preview + production code, production DB sample
**Date:** 2026-06-01

---

## 1 · Final classification

# 🟡 E · LIFECYCLE PARTIALLY IMPLEMENTED

A `status` field physically exists on every incident document (a hygiene artifact from Sprint 1B's backfill of 2026-06-01 00:09 UTC), but **no write path, no editor UI, and no closure workflow has ever been built around it**. Multiple downstream consumers ignore the field entirely and derive their own lifecycle states from `corrected_on_site` + linked CAPA — and even those derivations use four different incompatible vocabularies.

The operator's named four-state lifecycle (Under Investigation · Corrective Action Required · Pending Closure · Closed) **does not exist in any layer of the platform**.

---

## 2 · Plain answer to the 10 audit objectives

| # | Objective | Answer | Evidence |
|---|---|---|---|
| 1 | Do incident lifecycle statuses currently exist? | **Partial.** A status field exists on every doc but only as a Sprint 1B hygiene backfill ("open"). No four-state lifecycle exists. | §3.1 |
| 2 | Does `incident.status` exist in the database? | **Yes** — on every doc. Sprint 1B backfilled 6 nulls to `"open"` on 2026-06-01 00:09 UTC. Also a parallel `resolution_status` field. | §3.1, §3.2 |
| 3 | Does incident status exist in API payloads? | **Yes** — `GET /api/incidents/{id}` returns the field. But no PATCH/PUT exists to mutate it. | §3.3 |
| 4 | Does it exist in Accountability projections? | **Yes, but derived** — `_status_for_incident()` computes `open / in_progress / resolved` from `corrected_on_site` + CAPA linkage. The DB `status` field is **ignored**. | §3.4 |
| 5 | Does it exist in Command Center logic? | **Yes, but derived** — `_incident_is_resolved()` checks `corrected_on_site == "Yes"` or linked CAPA in closure state. "current_status" labels are hardcoded strings ("Open · no resolution path", etc.). DB `status` is **ignored**. | §3.5 |
| 6 | Is the status editable? | **No.** No PATCH/PUT endpoint on `/api/incidents/*`. No frontend edit form. | §3.3, §4.2 |
| 7 | Who can edit status? | **No one** — there is no path to edit it. The only write is the Sprint 1B one-off backfill (executed offline by an operator script). | §3.3 |
| 8 | Does a closure workflow exist? | **No.** No `mark_under_investigation`, `mark_corrective_action_required`, `mark_pending_closure`, `mark_closed` endpoints. No state-machine, no transitions, no audit. | §3.3 |
| 9 | Does CAPA completion affect status? | **Indirectly only.** Accountability projection + Command Center derive "resolved/closed" from CAPA closure state. The DB `incident.status` field is **never updated** when a CAPA closes. | §3.4, §3.5 |
| 10 | Do OSHA-related incidents have special status handling? | **No closure-status special-handling.** OSHA-recordable incidents get a Command Center rule (`SAF-OSHA-OPEN`) that warns after 24 h — but the rule reads `osha_recordable == "Yes"` + `created_at`, not status. The status field plays no role. | §3.5 |

---

## 3 · Detailed findings

### 3.1 · The status field exists — as a hygiene artifact

**Evidence:** Production `GET /api/incidents/87c8535b-ec64-4c06-aca0-01d5ebf9b3ec` (INC-2026-00011) returns:

```
status                                   : str  = "open"
resolution_status                        : str  = "open"
_backfilled_status_at                    : str  = "2026-06-01T00:10:54.210000+00:00"
_backfilled_status_reason                : str  = "Sprint 1B · OMEGA status backfill"
```

The two markers `_backfilled_status_at` + `_backfilled_status_reason` trace directly to `CLEANUP_EXECUTION_REPORT.md:23, 56`:

> Step 6 · UPDATE_MANY · `incidents` (status=null backfill) · 6 docs with `status=null` → 0 · modified=6

This was a one-shot data-hygiene write executed via `/tmp/sprint1b_phase3.py --execute`. It did NOT install a write path; it only normalized values that had drifted to null.

### 3.2 · Field is undeclared in the Pydantic model

**Evidence:** `routes/safety.py:202-254` — `IncidentCreate` model:

```python
class IncidentCreate(BaseModel):
    model_config = ConfigDict(extra="allow")    # ← extra fields tolerated, not declared

    project_name: str
    project_number: Optional[str] = ""
    # ... 50+ declared fields ...
    incident_type: str
    severity: str
    osha_recordable: Optional[str] = "No"
    # ... no `status` field anywhere ...
    distribution_list: Optional[List[str]] = Field(default=None, max_length=20)


class Incident(IncidentCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: Optional[str] = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

No `status` field. No `resolution_status` field. No `closed_at`. No `closed_by`. The fields exist in production data only because `extra="allow"` and a one-off `update_many` was executed.

### 3.3 · No mutation endpoint exists

**Evidence:** `routes/safety.py` exposes exactly four incident routes:

| Method | Path | Purpose | Body / Mutation |
|---|---|---|---|
| POST | `/api/incidents` | create new incident | full `IncidentCreate` body — no `status` field declared, so even if a client sent one the schema would silently drop it |
| GET | `/api/incidents` | list (with `IncidentSummary` projection — `status` not in projection) | read-only |
| GET | `/api/incidents/{id}` | detail (raw doc minus _id) | read-only |
| GET | `/api/incidents.csv` | CSV export | read-only |
| DELETE | `/api/incidents/{id}` | hard-delete · admin-only · blocks on linked CAPAs | no field mutation |

`grep -E "(patch|put).*incident" /app/backend/routes/safety.py` returns **0 hits**. There is no `/api/incidents/{id}/status`, `/api/incidents/{id}/close`, `/api/incidents/{id}/investigate`, or any other state-transition endpoint.

### 3.4 · Accountability projection derives its own status — ignores DB field

**Evidence:** `lib/accountability_projection.py:596-605`:

```python
async def _status_for_incident(db: Any, row: Dict[str, Any]) -> str:
    """Per Lifecycle §4.5 — derived from corrected_on_site + linked CA."""
    if str(row.get("corrected_on_site") or "").strip().lower() == "yes":
        return "resolved"
    inc_id = row.get("id")
    if await _incident_is_resolved_via_ca(db, inc_id):
        return "resolved"
    if await _incident_has_open_ca(db, inc_id):
        return "in_progress"
    return "open"
```

Note: `row.get("status")` is **never consulted**. The DB-stored `status` field is invisible to Accountability. The projection vocabulary is `open / in_progress / resolved` — three states, not the operator's four states.

### 3.5 · Command Center derives its own status — also ignores DB field

**Evidence:** `routes/command_center.py:484, 522, 536` — all checks gate on `_incident_is_resolved()`:

```python
# routes/command_center.py:484 (SAF-CRITICAL-UNRESOLVED)
if await _incident_is_resolved(db, inc):
    continue
```

Hardcoded `current_status` strings (lines 422, 497, 554):

```python
"current_status": "Open · no resolution path",
"current_status": "Open · unresolved",
"current_status": "Open · OSHA notification clock active",
```

These are emitted as labels for the Command Center pill. They are template strings, not lookups against `incident.status`. The OSHA-recordable rule (`SAF-OSHA-OPEN`, lines 524-531) reads `osha_recordable: "Yes"` and `created_at`, not `status`. The DB status field is **never** read in `command_center.py`.

### 3.6 · Project Health and Operations Center DO read `resolution_status`

**Evidence:** `routes/project_health.py:184-189`:

```python
db.incidents.count_documents({"resolution_status": {"$ne": "Closed"}})
db.incidents.count_documents({"resolution_status": {"$ne": "Closed"},
                              "severity": {"$in": ["High", "Critical"]}})
```

`routes/operations_center.py:180`:

```python
clauses = [{"resolution_status": {"$ne": "Closed"}}]
```

These read the parallel `resolution_status` field (which Sprint 1B also backfilled to "open"). They check for `!= "Closed"` only. They never write — but they expect "Closed" as a sentinel value that **the platform never sets**.

### 3.7 · Governance anticipates closure vocab but cannot enforce it

**Evidence:** `routes/governance.py:332-367`:

```python
async def _detect_incident_closed_capa_open(db) -> List[Dict[str, Any]]:
    """INC_CLOSED_CAPA_OPEN — incident with status closed but at least one open CAPA linked."""
    cursor = db.incidents.find(
        {"status": {"$in": ["closed", "completed", "resolved"]}}, ...
    )
```

This rule scans for incidents in any of three closure states (`closed / completed / resolved`) that still have open CAPAs — an integrity violation. The query language anticipates the lifecycle exists. But because no write path sets these states, the cursor returns 0 rows in production today (verified by inspection — every production incident has `status: "open"`).

---

## 4 · Vocabulary fragmentation table

The status concept is referenced in 5 different layers with **5 incompatible vocabularies**:

| Layer | Vocabulary | Source | Used for |
|---|---|---|---|
| Operator's stated intent | `Under Investigation · Corrective Action Required · Pending Closure · Closed` | This audit's authorization message | requirement |
| DB `status` field (post-Sprint 1B) | `open` (only value used in prod) | `CLEANUP_EXECUTION_REPORT.md:23` | hygiene placeholder |
| Frontend `SafetyIncidents.jsx` filter | `Open · Investigating · Closed` | `pages/SafetyIncidents.jsx:38-42, 125-129` | client-side filter (no submit) |
| Frontend `ViewIncident.jsx` derivation | `Follow-Up Required · Investigation Open · Operationally Complete` (3 tones rose/amber/emerald) | `pages/ViewIncident.jsx:68-110` | banner only |
| Accountability projection | `open · in_progress · resolved` | `lib/accountability_projection.py:596-605` | accountability lifecycle |
| Project Health / Operations Center | `Closed` vs everything-else | `project_health.py:184, operations_center.py:180` | unresolved counts |
| Governance probe | `closed · completed · resolved` | `governance.py:336` | integrity rule (returns 0) |

**None of these five active vocabularies match the operator's stated four-state vocabulary.** A future remediation must reconcile the model before any UI is added.

---

## 5 · Conclusion

The incident lifecycle is best described as **a present-tense field with an absent-tense workflow**:

* The field exists. It is queryable. It is even surfaced in a frontend filter dropdown.
* But the platform never moves it. Sprint 1B's backfill set it to "open" once; nothing has changed it since, and nothing in the codebase can.
* Two of the platform's most operationally critical consumers (Command Center, Accountability projection) bypass it entirely and re-derive lifecycle from `corrected_on_site` + CAPA linkage.
* The vocabulary is fragmented across five layers and none match the operator's stated four-state intent.

The Super-Admin's observation — "no obvious method to Mark Under Investigation / Mark Corrective Action Required / Mark Pending Closure / Mark Closed" — is correct, complete, and traces to a single root: **the closure workflow was never built; only the closure field was provisioned, and that only as a hygiene artifact**.

---

## 6 · OMEGA discipline

| Rule | Observed |
|---|---|
| Read-only audit | ✅ — only DB GET probes and file reads |
| Evidence-first | ✅ — every claim cites a file + line |
| No code changes | ✅ |
| No remediation proposed in this report | ✅ — see `INCIDENT_STATUS_DATA_MODEL.md` for the design surface and `INCIDENT_STATUS_UI_AUDIT.md` for the UI inventory |
| Stop after lifecycle assessment | ✅ |

🛑 Audit complete. Continue to `INCIDENT_STATUS_DATA_MODEL.md` for the schema surface and `INCIDENT_STATUS_UI_AUDIT.md` for the UI inventory.
