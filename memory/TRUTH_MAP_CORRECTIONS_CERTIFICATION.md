# TRUTH_MAP_CORRECTIONS_CERTIFICATION

**Date:** 2026-02-01 · Batch A · Step 1
**Authorized scope:** Apply documentation-only corrections surfaced in `TRUTH_MAP_VALIDATION_REPORT.md`. No code changes.

---

## Corrections applied

| Workflow | Doc | Correction |
|----------|-----|-----------|
| W2 Pre-Op | `WORKFLOW_LIFECYCLE_MAP.md` line 169 (Q8) | Add Dispatch to FAIL/OOS notification recipients |
| W3 Incident | `WORKFLOW_LIFECYCLE_MAP.md` lines 64–65 | Note idempotency wrapping via `Idempotency-Key` header (lib/idempotency.py) and clarify severe-CC source is per-record in `pm_routing.py` |
| W4 Safety Meeting | `WORKFLOW_LIFECYCLE_MAP.md` lines 39–45 | Collection name corrected: `meetings` (NOT `safety_meetings`); add bell/task fan-out gap (NEW-GAP-A) |
| W5 JHA | `WORKFLOW_LIFECYCLE_MAP.md` lines 49–58 | Submission collection corrected: `jhas`; `job_hazard_plans` is the SEPARATE master library |
| W10 Dispatch Event | `WORKFLOW_LIFECYCLE_MAP.md` lines 318–333 | Endpoint corrected: `POST /api/dispatch/assignments/{id}/transition` (not `/state-events`); `/state-events` is GET-only |

Also applied to: `API_DEPENDENCY_MAP.md`, `NOTIFICATION_DELIVERY_MAP.md`, `SYSTEM_TALK_MAP.md`, `DASHBOARD_DESTINATION_MAP.md` where the same identifiers appear.

---

## Certification statements

1. **No code was modified during this correction pass.** Only `/app/memory/*.md` documentation files were edited.
2. **Evidence backing**: every correction has file:line evidence in `TRUTH_MAP_VALIDATION_REPORT.md`.
3. **Truth Map scope discipline preserved**: corrections did not introduce new workflows, redesigns, or features — only restored accuracy.
4. **NEW-GAP-A** is documented in `GAP_REGISTER_UPDATE.md`; it surfaced during validation as a previously-undocumented gap with the same shape as GAP-3 (JHA bell/task missing).
5. **No production-side or preview-side behavior changed** as a result of the corrections.

---

## Verification

- ✅ `WORKFLOW_LIFECYCLE_MAP.md` corrected for W2, W3, W4, W5, W10
- ✅ `API_DEPENDENCY_MAP.md` Dispatch row corrected (`/assignments/{id}/transition`)
- ✅ `NOTIFICATION_DELIVERY_MAP.md` Meeting + JHA + Pre-Op rows confirmed accurate after correction
- ✅ `DASHBOARD_DESTINATION_MAP.md` no changes needed (destinations were correct)
- ✅ `SYSTEM_TALK_MAP.md` JHA row collection name corrected; Pre-Op Dispatch feed added

---

## Stop-condition compliance

- ✅ No Fleet DVIR implementation
- ✅ No notification wiring
- ✅ No gap closure
- ✅ No new features
- ✅ Read-only static-evidence-backed corrections
