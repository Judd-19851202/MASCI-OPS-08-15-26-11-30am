# Sprint 1C · Incident Delete Workflow Patch Report

**Batch:** OMEGA Critical Fix Sprint 1C/1D · Stage 2
**Date:** 2026-02-27
**Environment:** Preview only (`*.preview.emergentagent.com`). No production write.
**Scope:** Remediate `DELETE /api/incidents/{id}` per the operator authorization — workflow safety preserved, CAPA dependency check, clear HTTP error contract, id-vs-doc_id robust, audit log on success. Frontend wiring already covered in `SPRINT1D_UI_HYGIENE_PATCH_REPORT.md` §2.2-2.3.

---

## 1 · Root cause material carried into this patch

* `INCIDENT_DELETE_ROOT_CAUSE.md` §2 — the legacy route was 5 lines of code: `delete_one({"id": ...})` with no cascade, no audit, no soft-delete, no doc_id resolution, no CAPA dependency check.
* `INCIDENT_DELETE_ROOT_CAUSE.md` §6 — successful deletes left orphan `corrective_actions` (linked via `source_id`), orphan tasks, orphan notifications, and orphan R2 photo blobs.
* `INCIDENT_DELETE_REMEDIATION_PLAN.md` D-3, D-4 — soft-delete migration + cascade. **Both explicitly out of scope for this batch.** The operator authorized only the safety-of-delete remediation, not a behavioural soft-delete shift.

The narrow remediation authorized:

> "implement safe backend route behavior for DELETE /api/incidents/{id} · preserve workflow safety · prevent deletion when linked CAPA/workflow dependencies exist · return clear HTTP error messages explaining why deletion is blocked"

---

## 2 · Backend patch · `backend/routes/safety.py:810`

The 5-line route was rewritten to a four-phase safe delete. Old code:

```python
@api_router.delete("/incidents/{incident_id}")
async def delete_incident(incident_id: str, _: bool = Depends(require_admin)):
    result = await db.incidents.delete_one({"id": incident_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"deleted": True, "id": incident_id}
```

New behaviour (full source in commit):

| Phase | Action | Failure mode |
|---|---|---|
| 1 | Resolve identifier · `find_one({"id": <arg>})` then fallback `find_one({"doc_id": <arg>})` | 404 if neither match |
| 2 | CAPA dependency check · `corrective_actions.find({"source_kind":"incident","source_id":canonical_id})` | 409 with structured detail if ≥ 1 linked CAPA |
| 3 | Execute deletion against the resolved canonical UUID | 404 if race lost (defensive) |
| 4 | Insert audit_events row · `kind=incident_deleted`, actor_role, ip, ua, incident_id, doc_id, project_number | Errors swallowed — never blocks contract |

### 2.1 · Auth gate (unchanged, intentionally)

`require_admin` continues to gate the route. Admin tokens and PM tokens succeed; Safety, HR, Dispatch, Shop, and Field-Leadership tokens are rejected with HTTP 401. This is the operator's explicit "workflow safety preserved" requirement — incident delete remains a high-privilege action.

### 2.2 · 409 response shape (new contract)

```json
{
  "detail": {
    "code": "incident_has_linked_capas",
    "message": "Cannot delete incident — 1 corrective action(s) still reference it. Close or relink the CAPAs before deleting.",
    "linked_capa_count": 1,
    "linked_capas": [
      {"id": "<uuid>", "title": "<first 120 chars>", "status": "Open"}
    ]
  }
}
```

The frontend handlers (`IncidentsDashboard.jsx`, `ViewIncident.jsx`) extract `detail.message` and surface it directly in the toast. Operators see the exact reason the delete is blocked.

### 2.3 · Audit event shape (new)

```json
{
  "at": "<ISO8601 utc>",
  "kind": "incident_deleted",
  "actor_role": "admin" | "pm" | "unknown",
  "actor_id": "<pm id or email when PM-token>",
  "incident_id": "<canonical UUID>",
  "incident_doc_id": "<INC-YYYY-NNNNN>",
  "project_number": "<job number>",
  "ip": "<client ip>",
  "user_agent": "<truncated UA string>"
}
```

Writes to `db.audit_events`. Same collection the rest of the platform already uses (admin_logout, pm-impersonate, etc.) so existing admin audit dashboards observe the new event kind without schema migration.

---

## 3 · Test coverage · `backend/tests/test_sprint1c_incident_delete.py`

Seven pytest cases — every operator-required behaviour is explicitly asserted.

| # | Test | What it proves |
|---|---|---|
| 1 | `test_super_admin_can_delete_incident_by_uuid` | Super-admin (`X-Admin-Token`) deletes by canonical UUID · returns 200 · row gone from DB |
| 2 | `test_super_admin_can_delete_incident_by_doc_id` | Same super-admin can pass the `doc_id` (`INC-SPRINT1C-doc-id`) instead of UUID · backend resolves to UUID · returns 200 with both ids in body |
| 3 | `test_unknown_identifier_returns_404` | Junk identifier → HTTP 404 · clean failure mode |
| 4 | `test_safety_role_token_is_rejected` | `X-Safety-Token` set, admin token explicitly blanked → HTTP 401 · row survives intact · workflow safety preserved |
| 5 | `test_no_token_is_rejected` | No token at all → HTTP 401 · row survives intact |
| 6 | `test_incident_with_linked_capa_returns_409` | CAPA with `source_kind=incident, source_id=<uuid>` blocks delete · HTTP 409 · detail body lists the blocking CAPA · row survives |
| 7 | `test_delete_writes_audit_event` | Successful delete writes one new `audit_events` row with `kind=incident_deleted`, `incident_doc_id` matches synthetic doc id |

### 3.1 · Test run · 2026-02-27

```
$ cd /app/backend && python -m pytest tests/test_sprint1c_incident_delete.py -v
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0
collected 7 items

tests/test_sprint1c_incident_delete.py::test_super_admin_can_delete_incident_by_uuid PASSED [ 14%]
tests/test_sprint1c_incident_delete.py::test_super_admin_can_delete_incident_by_doc_id PASSED [ 28%]
tests/test_sprint1c_incident_delete.py::test_unknown_identifier_returns_404 PASSED [ 42%]
tests/test_sprint1c_incident_delete.py::test_safety_role_token_is_rejected PASSED [ 57%]
tests/test_sprint1c_incident_delete.py::test_no_token_is_rejected PASSED [ 71%]
tests/test_sprint1c_incident_delete.py::test_incident_with_linked_capa_returns_409 PASSED [ 85%]
tests/test_sprint1c_incident_delete.py::test_delete_writes_audit_event PASSED [100%]

============================== 7 passed in 7.78s ===============================
```

🟢 7/7 pass · Preview DB only.

### 3.2 · Synthetic data hygiene

Every test uses fixtures with `_sprint1c_test=True` + `doc_id` prefixed `INC-SPRINT1C-` so they are unmistakably non-production. Post-run sweep confirmed zero leftover incidents and zero leftover CAPAs in `masci_safety_preview`:

```
leftover incidents: 0
leftover capas: 0
leftover audits (stale): 4 → cleaned with one-shot delete_many({"incident_doc_id": /^INC-SPRINT1C-/}) → 0
```

Cleanup ran against the preview database only (`DB_NAME=masci_safety_preview`). Production database (`masci_safety` on `mascidocs.com`) was never touched.

---

## 4 · Regression probes (read-only)

Smoke probes against the live preview backend at `https://safety-audit-mobile-1.preview.emergentagent.com`:

| Surface | HTTP code | Verdict |
|---|---|---|
| `GET /api/incidents` (admin) | 200 | 🟢 incidents list unaffected |
| `GET /api/admin/accountability/sources` | 200 | 🟢 accountability projection healthy |
| `GET /api/admin/accountability/snapshot` | 200 | 🟢 command center inputs intact |
| `GET /api/admin/backups` | 200 | 🟢 backup surface untouched |
| `DELETE /api/incidents/<bogus>` (no token) | 401 | 🟢 auth gate intact |
| `DELETE /api/incidents/<bogus>` (admin) | 404 | 🟢 not-found path intact (see test #3) |

---

## 5 · Scope boundaries observed (OMEGA discipline)

| Item flagged in `INCIDENT_DELETE_REMEDIATION_PLAN.md` | Action |
|---|---|
| D-1 dedupe `doc_id='INC-2026-00001'` in production | **NOT EXECUTED** — production-data write; OMEGA freeze rule "NO production DB writes". |
| D-3 hard → soft delete migration | **NOT EXECUTED** — behavioural shift; out of authorized scope. |
| D-4 cascade to notifications / tasks / R2 blobs | **NOT EXECUTED** — relies on D-3 design. |
| D-5 allow Safety token to delete | **NOT EXECUTED** — operator explicitly preserved current admin/PM gate. |
| D-6 unique index on `doc_id` | **NOT EXECUTED** — DB schema change; out of scope. |
| D-7 backfill null `status` | **NOT EXECUTED** — data-cleanup; out of scope. |
| D-8 `doc_id_counters` atomic-increment investigation | **NOT EXECUTED** — investigation only; deferred. |
| **CAPA dependency block (D-2 implicit / new requirement)** | **EXECUTED.** Backend now returns 409 with explanatory detail. |
| **Frontend error-code surfacing (D-2)** | **EXECUTED.** Both delete handlers updated. |
| **id-vs-doc_id robustness** | **EXECUTED.** Backend resolves either identifier shape. |
| **Audit on delete** | **EXECUTED.** `audit_events` row written. |

---

## 6 · Risk-if-left-alone reduction

Original `INCIDENT_DELETE_ROOT_CAUSE.md` §8 listed three risks:

1. ~~Safety team cannot self-diagnose delete failures (generic toast)~~ → **closed.** Five-branch HTTP-aware toast now exposes 401 / 404 / 409 / 5xx / unknown to the operator.
2. ~~Successful deletes leave orphan CAPAs / tasks / R2 blobs without audit~~ → **partially closed.** Audit trail is now written; CAPA dependency is now enforced as a precondition. Tasks/R2 cascade remains a deferred item (D-4) per OMEGA scope.
3. ~~Compliance risk if a delete is later questioned~~ → **closed for incidents.** `audit_events` row pins actor role, ip, ua, doc_id, and project_number at delete time.

---

## 7 · Closeout

🟢 **Stage 2 complete.** Backend route safer, observable, and integrity-preserving. 7/7 pytest cases pass. Five regression probes 🟢.

🛑 STOP. Hand off to Stage 3 certification (`CRITICAL_FIX_SPRINT1C1D_CERTIFICATION.md`).
