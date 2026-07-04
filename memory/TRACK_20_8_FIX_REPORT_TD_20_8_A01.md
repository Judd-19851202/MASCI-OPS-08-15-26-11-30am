# TRACK 20.8 · Fix Report · TD-20.8-A01 · Design-Branch Skip Investigation

**Debt ID:** TD-20.8-A01
**Title:** `test_approve_without_employee_linkage_blocked` was skipping via a permissive fallback branch that hid a payload bug — the certified employee-linkage gate was never actually exercised.
**Class:** **A · Fix Now** (small · safe · test-only)
**Priority:** P1 (deployment gate quality)
**Status:** ✅ **FIXED** (2026-08-04)

## Required proof

### 1. Exact test name
`test_approve_without_employee_linkage_blocked`

### 2. Exact file path
`/app/backend/tests/test_track_19_21_e2e_live.py` · line 230 (original) / line 230–276 (fixed).

### 3. Why it was skipped

**The one-line answer:** the skip was firing for the WRONG reason.

**The full answer:** the test's POST payload to `/api/employee-records/records` omitted the required `record_type` field. Pydantic validated the request and returned **HTTP 422 · `"Field required: record_type"`**. The test had a permissive fallback branch:

```python
if rc.status_code >= 400:
    pytest.skip("Backend refuses to create record without employee — acceptable")
```

That branch was intended to accept the case where the backend refuses upfront (a hypothetical stricter path). Instead it fired on a schema-validation error that had nothing to do with the employee-linkage gate. The certified business logic (the whole point of the test) was never touched.

**Evidence — live curl reproduction (2026-08-04):**

Missing `record_type` (what the old test did):
```
$ curl -X POST /api/employee-records/records ... (no record_type in payload)
HTTP=422 · {"detail":[{"type":"missing","loc":["body","record_type"],"msg":"Field required"}]}
```

With `record_type` (what the fixed test does):
```
$ curl -X POST /api/employee-records/records ... (with record_type="hr_document", no employee_id)
HTTP=200 · {"ok":true,"record":{"id":"...","employee_id":null,"approval_status":"pending_match",...}}

$ curl -X POST /api/employee-records/records/{id}/approve ...
HTTP=400 · {"detail":"Cannot approve — employee_id is required"}
```

### 4. What production behavior it represents

The certified two-step employee-linkage contract:

- **Step 1 — Quarantined creation.** An unlinked record (`employee_id=null`) IS accepted into a quarantine lane with `approval_status="pending_match"`. This is by design — HR can bulk-upload documents faster than they can identify each employee; the platform stages them until match is possible.
- **Step 2 — Blocked approval.** `POST /records/{id}/approve` on an unlinked record returns **HTTP 400** with `"Cannot approve — employee_id is required"`. Approval is impossible until `employee_id` is populated (via a follow-up match/link action).

This is a real, user-facing production behavior. HR staff hit it every time they upload a document set faster than they can link individuals. Losing test coverage on it was a real risk.

### 5. Whether it should remain skipped

**NO.** The skip was hiding a real test bug. The certified behavior IS testable end-to-end and MUST be locked. The fix removes the skip branch entirely and adds hard assertions on both halves of the contract:

```python
# Step 1: create MUST succeed and land in pending_match
assert rc.status_code in (200, 201)
assert rec.get("employee_id") in (None, "")
assert rec.get("approval_status") == "pending_match"

# Step 2: approve MUST be blocked with a clear reason
assert ar.status_code >= 400
assert "employee" in ar.text.lower()
```

### 6. Whether it needs a separate test path

**NO.** The single fixed test now covers both certified branches (quarantine + block-on-approve) with hard assertions. No additional test is needed. The contract is one atomic user flow.

### 7. Whether it creates any deployment risk

**BEFORE fix:** MEDIUM risk. The employee-linkage gate is a real HR workflow protection and was untested. A future refactor of `employee_records.py::approve` could silently regress this gate and no test would catch it.

**AFTER fix:** ZERO risk. The gate is now hard-locked. A regression in `approve` (or in `_gate_create` / `pending_match` semantics) would immediately trip this test in the CI envelope.

## Fix applied

Single-file, test-only edit to `/app/backend/tests/test_track_19_21_e2e_live.py`:

1. Added `"record_type": "hr_document"` to the create payload (missing before → 422).
2. Removed the `if rc.status_code >= 400: pytest.skip(...)` fallback branch.
3. Added a Step 1 assertion cluster: `status_code in (200, 201)` · `employee_id in (None, "")` · `approval_status == "pending_match"`.
4. Kept the Step 2 assertion (`approve` returns >= 400) and strengthened it: block reason must mention `employee`.
5. Added a docstring documenting the certified two-step contract and the Track 20.8 investigation.

## Verification

```
$ pytest backend/tests/test_track_19_21_e2e_live.py -v
================== 11 passed in 5.90s ==================
```

- Every test in the file passes.
- **Zero skips.**
- Live-verified against the preview backend.

## Regression envelope re-run

Combined Track 20.8 · 20.7 · 20.6B envelope:

```
$ pytest backend/tests/test_track_20_8_deployment_certification.py \
         backend/tests/test_track_20_6b_test_hardening.py \
         backend/tests/test_track_20_7_universal_photo_capture.py \
         backend/tests/test_track_19_62_fire_protection_phase_a.py \
         backend/tests/test_track_20_6_fire_protection_audit.py \
         backend/tests/test_track_20_5_asset_thread_audit.py \
         backend/tests/test_track_20_4_vendor_thread_audit.py \
         backend/tests/test_track_19_21_e2e_live.py \
         backend/tests/test_daily_reports.py \
         backend/tests/test_job_photos.py
========== 181 passed, 0 skipped, 0 failed, 0 errors ==========
```

**Full envelope: 181 passed · 0 skipped · 0 failed.**

Prior "1 legitimate skipped" is gone. **The Track 20.8 regression envelope is now 100% assertive coverage.**

## Zero-drift

- No production code touched.
- No permission gate changed.
- No API contract changed.
- The certified `employee_records.py::approve` behavior was already correct — the test was under-specified.

## Register entry

Filed as **TD-20.8-A01 · Class A · P1 · FIXED (2026-08-04)** in `memory/TECHNICAL_DEBT_REGISTER.md`.

## Deployment call

🟢 The Track 20.8 deployment gate can now proceed. The last remaining "skipped" test has been converted into a hard-locked certified-behavior assertion. Deployment risk delta: **from MEDIUM (uncovered gate) to ZERO (fully locked).**
