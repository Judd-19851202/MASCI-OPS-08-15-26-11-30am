# Phase 1A · Test Plan

**Program:** OMEGA · PCP · Phase 1A · Final Build Package
**Authoritative source:** `PHASE1A_CERTIFICATION_PLAN.md` §2 (re-presented here in test-execution order)
**Mode:** Design-only
**Date:** 2026-06-01

---

## 1 · Test inventory (5 categories)

| Category | Tests | Estimated runtime |
|---|---|---|
| **A · Unit (foundation libs)** | 12 test files | ~10 seconds |
| **B · Integration (per-workflow lifecycle)** | 6 test files (one per workflow) | ~60 seconds |
| **C · Backwards-compat regression** | reuse iter445/446 + Sprint 1F/1G batteries | ~120 seconds |
| **D · Migration + data shape** | 5 test files | ~30 seconds |
| **E · Frontend (Playwright via testing_agent_v3_fork)** | 7 page integrations | ~5 minutes |

---

## 2 · Category A · Unit tests (foundation)

| File | Tests |
|---|---|
| `tests/test_state_machine_transitions.py` | (1) every allowed transition succeeds · (2) every forbidden transition returns 409 · (3) idempotency · (4) reason required on REOPEN · (5) OSHA gate triggers · (6) Super-Admin override path |
| `tests/test_role_gates.py` | For each of 60 (workflow, transition, role) cells in `PHASE1A_ROLE_PERMISSION_MATRIX.md`: assert authorized=200, unauthorized=403 |
| `tests/test_workflow_state_events_audit.py` | (1) every transition writes 1 row · (2) TTL index present · (3) unique compound index enforces idempotency · (4) per-doc history endpoint paginates · (5) admin filter endpoint returns expected |
| `tests/test_auto_transitions.py` | (1) DR auto-transition · (2) Payroll auto-transition · (3) QA/QC auto-transition · (4) Site auto-transition · (5) concurrent writes idempotent |
| `tests/test_lifecycle_read_shim.py` | (1) legacy record without `lifecycle_state` derives correctly · (2) once `lifecycle_state` set, derivation skipped · (3) all 5 workflows tested |
| `tests/test_incident_capa_pending_closure.py` | (1) first CAPA link → PENDING_CLOSURE · (2) last CAPA close → PENDING_REVIEW · (3) interim CAPA close ≠ transition · (4) reopen restores closure metadata |
| `tests/test_dr_return_to_field.py` | (1) return-to-field sets `return_reason` · (2) notification fires · (3) submitter can resubmit · (4) resubmit clears `return_reason` |
| `tests/test_payroll_finalize.py` | (1) cannot finalize with null decisions · (2) attestation required · (3) CLOSED batch immutable · (4) reopen clears finalization |
| `tests/test_qaqc_deficiency_propagation.py` | (1) inspection-level state mirrors deficiency aggregate · (2) reverting a deficiency reverts inspection · (3) closing all deficiencies auto-transitions inspection to PENDING_REVIEW |
| `tests/test_osha_closure_gate.py` | (1) OSHA-recordable requires attestation · (2) Super-Admin override path with reason succeeds · (3) audit row marks override |
| `tests/test_reopen_paths.py` | All 5 workflows: reopen requires reason, increments counter, preserves prior closure metadata |
| `tests/test_jha_acknowledgement_ledger.py` | (1) submit ack with signature · (2) 7y TTL on row · (3) per-JHA/per-job filter · (4) coverage math · (5) soft-delete by Safety · (6) audit row written on delete · (7) public QR-token submission · (8) duplicate ack rejected · (9) 4h gap notification fires · (10) Super-Admin restore |

**Coverage target: ≥95% on new code · 100% of state machine paths · 100% of OC-005 endpoints.**

---

## 3 · Category B · Integration tests (per-workflow lifecycle)

| File | Scenario |
|---|---|
| `tests/test_incident_full_lifecycle.py` | Create → IN_PROGRESS → link CAPA → PENDING_CLOSURE → close CAPA → PENDING_REVIEW → CLOSED → reopen → CLOSED. Assert 7 audit rows. |
| `tests/test_dr_review_cycle.py` | Submit DR → PM reviews → returns to field → field resubmits → PM approves. Assert notification fired. |
| `tests/test_payroll_full_batch.py` | Upload CSV (50 rows) → decide each → auto-PENDING_REVIEW → finalize → assert downstream consumers read CLOSED |
| `tests/test_qaqc_remediation_cycle.py` | Submit with 3 deficiencies → assign each → crew claims → PM verifies 2 → reject 1 → re-claim → verify → close inspection |
| `tests/test_site_inspection_walk.py` | Same shape as QA/QC for site inspection |
| `tests/test_jha_full_acknowledgement_flow.py` | Create JHA → 3 crews ack via signature → 1 crew via verbal attest → coverage dashboard shows 100% → soft-delete one ack → coverage drops |

---

## 4 · Category C · Backwards-compat regression

Reuse existing test batteries · zero regressions allowed:

| Battery | Scope |
|---|---|
| Sprint 1F (5 tests) | Accountability projection owner resolution |
| Sprint 1G (6 tests) | Photo viewer raw endpoint + R2 presigned URL |
| iter445 (7 tests) | Scheduler hardening + dedup |
| iter446 (probes) | Production certification battery (preview-side equivalent) |
| Existing safety/po/asset/dispatch/fleet endpoint suites | per `routes/test_*.py` files (~200 tests) |

Total regression battery: ~225 tests. **Must pass with zero failures.**

---

## 5 · Category D · Migration + data shape

| File | Asserts |
|---|---|
| `tests/test_lifecycle_state_migration.py` | All 5 modified collections gain `lifecycle_state="OPEN"` on missing · idempotent re-run · `_lifecycle_migrated_at` stamped |
| `tests/test_qaqc_deficiency_format_v1_to_v2.py` | v1 text-array reads return v2 object-array shape · v2 writes use object shape · `deficiencies_format_version` field set |
| `tests/test_inspections_findings_initialization.py` | Legacy `inspections` records get `findings: []` on migration · new findings collected in v1 shape |
| `tests/test_indexes_created.py` | All 9 new indexes exist with expected keys |
| `tests/test_migration_audit_events.py` | Migration writes 5 rows to `audit_events` with `kind="phase1a_migration"` |

---

## 6 · Category E · Frontend tests (via testing_agent_v3_fork)

A single `testing_agent_v3_fork` invocation covers all 7 page integrations:

```json
{
  "original_problem_statement_and_user_choices_inputs": "OMEGA Phase 1A · 6-workflow lifecycle remediation",
  "features_or_bugs_to_test": [
    "ViewIncident · LifecyclePanel renders + role-gated buttons + OSHA closure modal",
    "ViewDailyReport · LifecyclePanel + return-to-field flow + notification side-effect",
    "HrPayrollVariance · batch LifecyclePanel + Finalize button + attestation modal",
    "ViewQaqcInspection · inspection LifecyclePanel + per-deficiency action menu",
    "ViewSiteInspection · same pattern for safety domain",
    "JhaList · Acknowledge button opens JhaAcknowledgePanel · signature pad works",
    "SafetyJhaAcks · coverage dashboard renders per-job grid + drill-in",
    "PublicJhaAck · QR-token flow accepts signature + records ack"
  ],
  "files_of_reference": [
    "frontend/src/components/LifecyclePanel.jsx",
    "frontend/src/pages/ViewIncident.jsx",
    "frontend/src/pages/SafetyJhaAcks.jsx",
    ...
  ],
  "required_credentials": "[from /app/memory/test_credentials.md]",
  "testing_type": "frontend only",
  "agent_to_agent_context_note": "Phase 1A · 6-workflow lifecycle remediation · OC-005 elevated"
}
```

---

## 7 · Test execution order (CI/CD pipeline)

```
1. Ruff + ESLint        (~5 sec)        → fail fast on syntax
2. Category A unit       (~10 sec)       → foundation libs
3. Category D migration  (~30 sec)       → data shape correct
4. Category B integration(~60 sec)       → per-workflow E2E
5. Category C regression (~120 sec)      → no regressions
6. Coverage report       (~5 sec)        → ≥95%
7. Backend supervisor restart            → preview deploy
8. Category E frontend (testing_agent)   (~5 min) → UI works
9. Preview-cert probe battery            → final gate
```

Total CI time: **~10 minutes**. Acceptable for build velocity.

---

## 8 · Defect threshold

| Severity | Allowed before merge |
|---|---|
| 🔴 Critical (any test fails) | 0 |
| 🟡 Important (warnings · skipped tests) | 0 |
| 🟢 Minor (lint warnings) | ≤ 5 |

Any 🔴 defect blocks merge. Any 🟡 defect requires operator override.

---

## 9 · OMEGA discipline

🟢 Test inventory exhaustive · ~38 new test files · regression battery preserved · frontend coverage via testing_agent_v3_fork · execution order documented.

🛑 Continue to `PHASE1A_DEPLOYMENT_PLAN.md`.
