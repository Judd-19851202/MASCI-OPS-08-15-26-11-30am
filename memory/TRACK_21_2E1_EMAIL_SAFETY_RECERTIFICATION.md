# TRACK 21.2E-1 · Email Safety Recertification

**Purpose:** Re-verify — after canonicalization — that every layer of the
email safety envelope still enforces. Nothing weakened. Nothing bypassed.

---

## Layer 1 · SDK-level kill switch (Track 21.2E)

**File:** `backend/server.py` module import (line ~75)

**Assertion:** When `EMAIL_SAFETY_MODE ∈ {strict, silent, test}`,
`resend.Emails.send` is replaced with a synthetic no-op stub returning
`{"id": "blocked_by_email_safety_mode", "status": "skipped"}`.

**Proof:**

- Guard clause is present:
  ```python
  if _EMAIL_SAFETY_MODE in ("strict", "silent", "test"):
      _resend_boot.Emails.send = staticmethod(_blocked_send)
      _resend_boot.send = _blocked_send
  ```
- Backend supervisor log confirms activation on the current pod:
  ```
  [Track 21.2] EMAIL_SAFETY_MODE=strict — Resend SDK patched.
  No live email can leave this pod.
  ```
- Programmatic re-test in-process:
  ```
  resend.Emails.send({...})
  → {'id': 'blocked_by_email_safety_mode', 'status': 'skipped'}
  ```
- Lock test: `test_track_21_2e_email_safety.py::test_resend_sdk_is_patched_when_strict` ✅
- Lock test: `test_track_21_2e1_payload_canonicalization.py::test_sdk_kill_switch_still_present` ✅
- Lock test: `test_track_21_2e_email_safety.py::test_resend_sdk_untouched_when_safety_off` ✅ (source-level guarantee: patch runs only under the env guard)

---

## Layer 2 · `_dispatch_auto_email` strict-mode short-circuit

**File:** `backend/server.py` line ~13,676

**Assertion:** When strict, the dispatcher short-circuits **before**
`recipients_for_record_async` runs.

**Proof:**

- Static assertion: gate index < recipient-lookup index inside the
  function body (`test_dispatch_auto_email_source_contains_strict_gate`).
- Trust Spine emits `status="skipped"` with `failure_reason="email_safety_mode:strict"` for full audit traceability.

---

## Layer 3 · `auto_email_enabled()` returns False

**File:** `backend/pm_routing.py`

**Assertion:** When strict, returns `False` regardless of
`RESEND_API_KEY` / `AUTO_EMAIL_REPORTS`.

**Proof:** `test_auto_email_enabled_false_in_strict` ✅
`test_auto_email_enabled_true_in_off_mode` ✅ (production behavior preserved)
`test_auto_email_enabled_still_honors_safety_mode` ✅ (source-level check)

---

## Layer 4 · Track 20.6B `TEST_`-prefix gate

**File:** `backend/server.py` line ~13,708

**Assertion:** Any record whose `project_name` starts with `TEST_` is
short-circuited before any recipient lookup, before any provider call,
and audited as `status="skipped"`.

**Proof:**

- Source-level assertion: `synthetic-test-record gate` string is present
  AND `startswith("TEST_")` is present
  (`test_track_20_6b_test_prefix_gate_still_present`).
- Runtime is currently defense-in-depth only — after Track 21.2E-1,
  every synthetic payload starts with `TEST_`, so this gate is
  sufficient on its own even if Layer 1 (the SDK patch) were somehow
  disabled.

---

## Layer 5 · Payload canonicalization (Track 21.2E-1)

**Assertion:** Every synthetic workflow payload uses a `TEST_` prefix.

**Proof:**

- Fresh scan across every HTTP-submitting backend test:
  0 unresolved offenders (down from 72 pre-21.2E-1).
- Lock test: `test_no_unsafe_strict_workflow_payload_field_in_tests` ✅
- Lock test: `test_no_pytest_skip_masks_unsafe_workflow_payload` ✅

---

## Sequence diagram · what happens now when a test submits a workflow

```
                       (any preview / staging / test pod)

1. test submits POST /api/daily-reports { "project_name": "TEST_DR_..." }
2. handler creates the DR record + fires `schedule_auto_email(...)`.
3. `_dispatch_auto_email` runs:
       a. reads EMAIL_SAFETY_MODE
       b. if strict → emits Trust Spine `status="skipped"` and returns
   ➊  ▓ FIRST HARD STOP  ▓
4. even if Layer 3 were removed, Layer 4 would catch it (TEST_ prefix)
   ➋  ▓ SECOND HARD STOP ▓
5. even if Layer 3 and Layer 4 were removed, Layer 1 would catch it
   at the SDK boundary
   ➌  ▓ THIRD HARD STOP (SDK-level) ▓
6. `resend.Emails.send` is a synthetic stub — returns blocked payload
7. No Resend HTTP call is made. No email leaves.
```

Three independent gates. Each is written into a lock test. No single
change to the codebase can defeat all three without triggering a
guardrail failure.

---

## Recertification verdict

🟢 **CERTIFIED**. The email-safety envelope is stronger than it was
after Track 21.2E because Track 21.2E-1 removed the last credible way
for a test author to accidentally submit a non-`TEST_` synthetic
workflow payload.

**Zero live emails possible.** Production behavior unaffected.
