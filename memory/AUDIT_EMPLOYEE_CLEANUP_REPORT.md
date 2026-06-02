# HOTFIX BUNDLE A · Part B · AUDIT EMPLOYEE CLEANUP REPORT

**Date**: 2026-06-02
**Authority**: OMEGA HOTFIX BUNDLE A · Part B · 2026-06-02.
**Mode**: Operator-runnable cleanup procedure. **No direct production DB access from this agent.**

---

## 1 · Target row

| Field | Value |
|---|---|
| Collection | `db.masci_safety.employees` (PRODUCTION) |
| `id` | `f5de1e78-f893-46d5-aa09-6369064e7906` |
| `name` | `"PROD AUDIT PROBE — DO NOT WRITE"` |
| `added_via` | `"field-form"` |
| `created_at` | `"2026-06-02T14:47:49.309019+00:00"` |
| Cause | OMEGA Post-Deploy Certification first G-1 probe; pod cold-start race produced 200 before Phase Alpha 410 route registration completed. Documented in `COMBINED_DEPLOY_PRODUCTION_REPORT.md §5`. |

## 2 · Verification (operator pre-cleanup)

The operator may verify the row before cleanup via the HR portal:

1. Log into `https://mascidocs.com/hr/login` as HR Manager.
2. Navigate to `/hr/employees`.
3. Filter / search for "PROD AUDIT PROBE".
4. Confirm exactly one matching row with id `f5de1e78-f893-46d5-aa09-6369064e7906`.

## 3 · Approved cleanup methods

### 3.1 Method A — HR portal soft-delete (recommended · doctrine-aligned)

1. Open the matched row's drawer.
2. Click the **Status** tab (now opens directly via REC-2 badge click).
3. Pick `Lifecycle Status = Terminated` + `Separation Type = involuntary` + `Rehire Eligibility = not_eligible` + `Reason = "OMEGA Post-Deploy Audit Probe — cold-pod-race residual cleanup per HOTFIX BUNDLE A Part B"`.
4. Click **"Save Status Change"**.
5. Result: `lifecycle_status=Terminated, is_active=false`; the row stays in `db.employees` for forensic audit but is excluded from active roster, FL routing, and dispatch driver picks (verified by `OFFBOARDING_CHAIN_CERTIFICATION.md §2`).

This is the canonical Phase Alpha lifecycle method — it preserves the `status_history[]` audit trail and the audit-probe row becomes part of the official forensic chain.

### 3.2 Method B — Direct Mongo soft-delete (if HR portal access unavailable)

Operator with prod DB shell access:

```javascript
db.employees.updateOne(
  { id: "f5de1e78-f893-46d5-aa09-6369064e7906" },
  { $set: {
      deleted_at: new Date().toISOString(),
      deleted_by: "OMEGA HOTFIX BUNDLE A Part B",
      deleted_reason: "Audit-probe row · cold-pod-race residual from 2026-06-02 post-deploy certification"
  }}
)
```

### 3.3 Method C — Hard delete (NOT recommended)

Hard deletion violates the append-only audit doctrine. Use Method A or B.

## 4 · Verification (operator post-cleanup)

After Method A or B, verify:

1. `GET /api/hr/employees?limit=300` (HR token) → row appears with `lifecycle_status=Terminated` (Method A) or does not appear in default active list (Methods A and B).
2. `GET /api/hr/employees?show_inactive=true&limit=300` (HR token) → row still queryable for audit; `is_active=false` (Method A) or `deleted_at` set (Method B).
3. `GET /api/field-leadership/employees` (FL token) → row excluded (FL filter is `is_active != False`).
4. No orphan references in `db.tasks` (cleanup probe did not generate offboarding tasks because `added_via=field-form` row never entered an `Active` state with a separation transition until the cleanup itself).

## 5 · Why this agent cannot perform the cleanup directly

* The agent's preview-environment HR token does not authenticate against the production API.
* No production admin token is available to this agent.
* No production Mongo shell access is available to this agent.
* The directive `READ ONLY unless authorized` is honored — Part B explicitly requires operator authorization to write to production.

The operator may perform Method A in ≤ 60 seconds via the HR portal UI.

## 6 · Risk closure

| Risk | Severity | Status after operator step |
|---|---|---|
| Cold-pod-race residual probe row | 🟢 LOW | 🟢 CLOSED after Method A |

## 7 · Forensic note

The audit-probe row will permanently remain in the `db.employees` collection (per append-only doctrine) with a `status_history[]` entry recording the OMEGA HOTFIX BUNDLE A Part B termination. This is the doctrinally correct outcome: the audit performed an unintentional write during pod warm-up, the chain captures both the original write and the corrective termination, and future audits can trace exactly what happened. Hard deletion would erase this evidence.
