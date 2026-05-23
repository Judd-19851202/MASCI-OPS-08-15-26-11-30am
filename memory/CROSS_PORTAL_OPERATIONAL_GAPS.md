# CROSS-PORTAL OPERATIONAL GAPS
**Audit date:** 2026-05-23
**Method:** Live multi-token RBAC probing via curl (every probe captured `X-Admin-Token: ""` to defeat conftest fallback).

---

## Live RBAC matrix (preview)
HTTP code observed when each portal token GET-probes the endpoint. Read-only paths only — write paths follow each portal's documented owner policy.

| Endpoint | Safety | HR | PM | FL | Dispatch | Shop | Anon |
|---|---|---|---|---|---|---|---|
| `/api/incidents` | 200 | **401** ❌ | 200 | **401** ❌ | **401** ❌ | **401** | 401 |
| `/api/corrective-actions` | 404 ⚠️ | 404 | 404 | 404 | 404 | 404 | 404 |
| `/api/daily-reports` | **401** ❌ | **401** ❌ | 200 | **401** ❌ | **401** ❌ | **401** | 401 |
| `/api/safety/training-records` | 200 | 200 | **401** ❌ | **401** ❌ | — | — | 401 |
| `/api/safety/documents` | 200 | 200 | **401** | **401** | — | — | 401 |
| `/api/safety-forms/equipment-issuances` | 200 | 200 | **401** ❌ | **401** ❌ | — | — | 401 |
| `/api/equipment-inspections` | 401 | 401 | 200 | **401** ⚠️ | 401 | 200 | 401 |
| `/api/tasks` | 200 | 200 | 200 | **401** ❌ | — | — | 401 |
| `/api/notifications` | 200 | 200 | — | **401** ❌ | — | — | 401 |
| `/api/hr/employees/{id}/accountability/timeline` 🆕 | 200 | 200 | 401 ✓ | 401 ⚠ | 401 ✓ | 401 ✓ | 401 |
| `/api/hr/driver-qualification/dashboard` | 401 | 200 | 401 | 401 | 401 | — | 401 |
| `/api/dispatch/driver-qualification` 🆕 | 401 ✓ | 401 ✓ | 401 ✓ | 401 ✓ | 200 | 401 ✓ | 401 ✓ |
| `/api/field-leadership/portal/driver-qualification` | 401 ✓ | 401 ✓ | 401 ✓ | 200 | 401 ✓ | 401 ✓ | 401 ✓ |

❌ = operational gap (token SHOULD see this) · ✓ = boundary correctly enforced · ⚠️ = ambiguous (operator policy TBD)

---

## Gap inventory

### 🔴 GAP-CP-1 · HR cannot list incidents
- **Endpoint:** `GET /api/incidents`
- **Current:** HR token → 401
- **Should:** HR token → 200 (read-only; embedded in iter353c timeline but no HR-wide list page exists)
- **Operational impact:** HR cannot answer "all incidents this quarter for OSHA 300 prep" from inside HR portal. Must escalate to Safety or Admin.
- **Fix sketch:** Mount HR-namespace proxy `/api/hr/incidents` that calls a shared safety helper with HR token. Strictly read; no edit/closeout authority.

### 🔴 GAP-CP-2 · FL is incident-blind
- **Endpoint:** `GET /api/incidents`
- **Current:** FL token → 401
- **Should:** FL token → 200 read-only, scoped to FL's own assignments
- **Operational impact:** FL is in the field where incidents OCCUR. They cannot review what happened on their own job site yesterday from their portal.
- **Fix sketch:** `/api/field-leadership/portal/incidents-recent` read-only proxy, scoped 14d window.

### 🔴 GAP-CP-3 · FL has no training currency view
- **Endpoint:** `GET /api/safety/training-records`
- **Current:** FL → 401
- **Should:** FL → 200 read-only (FL just got DQ visibility in iter353b — training is the same employee-readiness signal)
- **Operational impact:** A foreman about to send a crew to confined-space work CANNOT verify their OSHA confined-space cert from the FL portal.

### 🔴 GAP-CP-4 · FL has no PPE issuance view
- **Endpoint:** `GET /api/safety-forms/equipment-issuances`
- **Current:** FL → 401
- **Should:** FL → 200 read-only
- **Operational impact:** Same as GAP-CP-3 but for hard hat / fall harness / respirator issuance currency.

### 🔴 GAP-CP-5 · PM has no training or PPE visibility for crew
- **Endpoints:** `/api/safety/training-records`, `/api/safety-forms/equipment-issuances`
- **Current:** PM → 401 on both
- **Should:** PM → 200 scoped to crews on PM's assigned jobs
- **Operational impact:** PM cannot verify whether an operator they're about to assign to a trench job has OSHA Excavation cert or current respirator fit-test.

### 🔴 GAP-CP-6 · FL receives ZERO notifications
- **Observed `recipient_role` distribution:** `safety`, `pm`. No FL, HR, Dispatch, or Shop entries.
- **Operational impact:** Field-level escalations never reach the field. A failed QA/QC on FL's project surfaces in Safety + PM inboxes but the foreman who oversees that crew is never notified.
- **Fix sketch:** Add `fl` to `recipient_role` enum + fan-out logic on QA/QC fail · Pre-Op fail · daily report missing · incident reported · training expiring within 30d.

### 🟡 GAP-CP-7 · Dispatch cannot list daily reports
- **Endpoint:** `GET /api/daily-reports`
- **Current:** Dispatch → 401
- **Should:** Dispatch → 200 read-only, last 7 days, to reconcile "where was the asset/crew yesterday?" when an audit comes in.
- **Operational impact:** Asset transfer audits and crew movement reconciliation require admin escalation.

### 🟡 GAP-CP-8 · `/api/corrective-actions` discoverability
- **Endpoint:** Mounted at safety_exports router; returns 404 even to Safety token in this audit.
- **Likely root cause:** Endpoint exists (`safety_exports.py:116`) but is gated by `Depends(require_token)` whose token type is unclear from probing.
- **Fix sketch:** Verify gate matches the `require_safety_or_hr_or_admin` shared gate; add to RBAC matrix tests.

### 🟢 BOUNDARY ENFORCED CORRECTLY (no action needed)
- iter353c accountability timeline rejects PM / Shop / Dispatch / FL / anon (✓).
- iter353b Dispatch DQ rejects everyone except Dispatch + Admin (✓).
- iter353b FL DQ rejects everyone except FL (✓).
- HR DQ dashboard still HR/Admin exclusive (✓).

---

## Write-path gap (operator policy)
| Write target | Allowed today | Operator says should be |
|---|---|---|
| `incidents` POST | public + safety + admin | OK |
| `incidents` PATCH/closeout | safety + admin | OK |
| `safety_training_records` POST | safety + HR + admin 🆕 (iter353a) | OK |
| `safety_training_records` DELETE | safety + admin (HR archive-only) | OK (HR NO hard-delete enforced) |
| `safety_documents` POST | safety + HR + admin 🆕 | OK |
| `safety_documents` DELETE | safety + admin (HR archive-only) | OK |
| `employees` PATCH (CDL fields) | HR + admin | OK |
| `employees` PATCH (lifecycle) | HR + admin | OK |
| `employees` DELETE | admin (soft) | OK (no per-portal hard delete) |
| `field_leadership_records` POST | FL portal + admin | OK |
| Driver Qualification import | HR + admin | OK |
