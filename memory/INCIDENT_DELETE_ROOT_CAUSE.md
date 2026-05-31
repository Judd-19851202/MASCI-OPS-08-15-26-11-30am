# Incident Delete Root Cause · Critical Fix Sprint 1 · P0-3

**Batch:** OMEGA Critical Fix Sprint 1 · P0-3
**Date:** 2026-05-31
**Scope:** Trace the entire DELETE-incident chain. Determine why deletion fails, what collections are touched, and the exact root cause.

---

## 1 · Root cause verdict

🟡 **Incident delete is NOT broken. It is permission-gated, identifier-strict, and lacks cascade.**

The operator-reported "incident delete failure" most likely stems from one of three reproducible code paths:

1. **(Most likely) Caller used a non-admin/non-PM token** → backend returns **HTTP 401**. Safety, HR, Dispatch, Shop, and Field Leadership tokens are ALL rejected by `require_admin`.
2. **(Likely) Caller passed `doc_id` (`INC-2026-00001`) instead of `id` (UUID)** → backend returns **HTTP 404** because the DELETE matches by `id` only.
3. **(Possible) Caller hit a deactivated/duplicate record** → backend correctly returns **HTTP 404** for any non-matching UUID.

**No structural defect in the DELETE route itself.** The code is short, correct, and idempotent.

---

## 2 · The DELETE route — full source

**Location:** `backend/routes/safety.py:810-815`

```python
@api_router.delete("/incidents/{incident_id}")
async def delete_incident(incident_id: str, _: bool = Depends(require_admin)):
    result = await db.incidents.delete_one({"id": incident_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"deleted": True, "id": incident_id}
```

| Aspect | Behavior |
|---|---|
| URL | `DELETE /api/incidents/{incident_id}` |
| Identifier matched | **`id` field only** (UUID) — NOT `doc_id`, NOT `incident_number`, NOT `incident_id` |
| Auth dependency | `require_admin` — accepts Admin token OR PM token; rejects all other portal tokens |
| DB action | `db.incidents.delete_one({"id": incident_id})` — single document removal |
| Cascade to other collections | **NONE** |
| Audit log | **NONE** in this route |
| Idempotency | None (subsequent identical DELETE → 404) |

---

## 3 · `require_admin` dependency — exact behavior

**Location:** `backend/server.py:273-300`

```python
async def require_admin(
    request: Request,
    x_admin_token: Optional[str] = Header(default=None),
    x_pm_token: Optional[str] = Header(default=None),
):
    """FastAPI dependency. Accepts an Admin OR a Project-Manager token —
    EXCEPT on routes whose path starts with /api/admin/, where PM
    tokens are rejected and only Admin tokens unlock."""
```

| Token | Behavior on `DELETE /api/incidents/{id}` |
|---|---|
| `X-Admin-Token: <valid admin>` | 🟢 Allowed |
| `X-PM-Token: <valid PM>` | 🟢 Allowed (route is NOT under `/api/admin/`) |
| `X-Safety-Token` | 🔴 Rejected → 401 |
| `X-HR-Token` | 🔴 Rejected → 401 |
| `X-Dispatch-Token` | 🔴 Rejected → 401 |
| `X-Shop-Token` | 🔴 Rejected → 401 |
| `X-FL-Token` | 🔴 Rejected → 401 |
| no token | 🔴 401 |

---

## 4 · Live production reproduction

Captured 2026-05-31 against `https://mascidocs.com`:

| Test | URL | Token | HTTP code | Verdict |
|---|---|---|---|---|
| 4.1 | `DELETE /api/incidents/00000000-0000-0000-0000-000000000000` | valid Admin | **404** | ✅ "not found" path works |
| 4.2 | `DELETE /api/incidents/INC-2026-00099` (doc_id format) | valid Admin | **404** | ✅ confirms `id` (not `doc_id`) is the match key — passing a doc_id always 404s |
| 4.3 | `DELETE /api/incidents/00000000-...` | no token | **401** | ✅ auth gate fires |
| 4.4 | `DELETE /api/incidents/00000000-...` | valid **Safety** token | **401** | 🔴 **Safety token rejected** — this is the likely operator-reported failure mode |

Result 4.4 is critical: a Safety-portal user attempting to delete an incident from the Safety Portal UI will see "Delete failed" because the backend returns 401 to Safety tokens.

---

## 5 · Frontend callers — who tries to delete?

| Frontend file | Call site | Argument |
|---|---|---|
| `frontend/src/pages/IncidentsDashboard.jsx:50` | `await api.delete(\`/incidents/${id}\`)` | `it.id` (UUID — correct) |
| `frontend/src/pages/ViewIncident.jsx:209` | `await api.delete(\`/incidents/${id}\`)` | `useParams().id` — depends on the route definition |

**Both call sites use the UUID `id` correctly.** No frontend caller passes `doc_id`.

### 5.1 · IncidentsDashboard.jsx exception handler

```javascript
const handleDelete = async (id, e) => {
  e.stopPropagation();
  if (!window.confirm("Delete this incident report? This cannot be undone."))
    return;
  try {
    await api.delete(`/incidents/${id}`);
    toast.success("Incident deleted");
    setItems((p) => p.filter((i) => i.id !== id));
  } catch {
    toast.error("Delete failed");
  }
};
```

🟡 **The `catch` block swallows the HTTP status code.** All failure modes (401, 404, 500, network) collapse to a single "Delete failed" toast. **This is the proximate cause of the operator-reported "incident delete failure" being unactionable** — the user sees a generic error with no signal about whether it's auth, missing record, or server fault.

### 5.2 · ViewIncident.jsx — identical pattern

```javascript
const handleDelete = async () => {
  if (!window.confirm("Delete this incident report? This cannot be undone."))
    return;
  try {
    await api.delete(`/incidents/${id}`);
    toast.success("Deleted");
    navigate(listUrl);
  } catch {
    toast.error("Delete failed");
  }
};
```

Same swallow.

---

## 6 · Collections touched by a successful delete

| Collection | Touched? | Behavior |
|---|---|---|
| `db.incidents` | ✅ | row removed |
| `db.notifications` (incident-type) | ❌ NOT cascaded | becomes orphan-referencing |
| `db.tasks` (incident-derived) | ❌ NOT cascaded | becomes orphan-referencing |
| `db.audit_events` | ❌ no audit log entry written | irreversible without external log |
| `db.admin_audit` | ❌ no admin-action audit | |
| `db.corrective_actions` (links via `source_id`) | ❌ NOT cascaded | orphan |
| `db.command_center_thresholds` snapshot | n/a | next snapshot reflects deletion |
| `db.accountability_*` (Pillar 1 projection) | n/a | read-only · next snapshot reflects deletion |
| Embedded `photos[]` array | ✅ removed with parent | clean |
| Embedded `corrective_actions[]` array | ✅ removed with parent | clean |
| R2 photo blobs | ❌ NOT cascaded | orphan blobs remain in R2 |

🟡 **No cascade. No audit. No soft-delete option.** This is the architectural weakness — even a "successful" delete leaves orphans across 6 surfaces.

---

## 7 · Reproduction matrix (operator-side)

| Repro | Expected response | Cause |
|---|---|---|
| Hit "Delete" from Safety Portal incident page | "Delete failed" toast (401 swallowed) | Safety token rejected by `require_admin` |
| Hit "Delete" from Admin Incident Dashboard | "Incident deleted" toast | Admin token accepted · UUID passed |
| Hit "Delete" via API with `doc_id` instead of `id` | 404 (caller-side error) | wrong identifier |
| Hit "Delete" while another portal page has the same incident open | UI inconsistency; both pages see "Delete failed" or stale data | no cross-tab signaling |

---

## 8 · Risk if left alone

🟡 IMPORTANT:
- Safety team cannot delete incidents from the Safety Portal — only Admin or PM can. Operationally, this means every delete becomes an escalation to Admin · slow + audit-untraceable.
- Successful deletes leave **orphan notifications, orphan tasks, orphan R2 photo blobs, and no audit trail** of who deleted what. **Compliance / regulatory risk** if a delete is later questioned.
- Frontend swallows all error codes → users have no path to self-diagnose.

🟢 NOT a blocker for Pillar 1 production deployment (already certified) — Pillar 1 reads incidents, never deletes.

---

## 9 · Closeout

🟡 **Incident delete is NOT broken.** It is permission-gated to Admin/PM, identifier-strict on `id`, lacks cascade to 6 surfaces, lacks audit, and the frontend swallows error codes.

🛑 STOP. Remediation plan in `INCIDENT_DELETE_REMEDIATION_PLAN.md`.
