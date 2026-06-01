# Phase 1A · Certification Plan

**Program:** OMEGA · Platform Completion Program · Phase 1A · DESIGN
**Companion:** `PHASE1A_WORKFLOW_DESIGN.md` · `PHASE1A_STATE_MACHINE.md` · `PHASE1A_ROLE_MATRIX.md`
**Mode:** Design-only · no code
**Date:** 2026-06-01

---

## 0 · Certification objective

Define exactly what must be tested, observed, and signed off before Phase 1A code is allowed to deploy to production.

**Certification is a gate before each of three checkpoints:**
1. **DESIGN → BUILD** (this document is the gate; operator certification of `PHASE1A_*.md` set unlocks Build)
2. **BUILD → PREVIEW DEPLOY** (full preview certification battery passes)
3. **PREVIEW → PRODUCTION DEPLOY** (operator approval + smoke tests post-deploy)

---

## 1 · Design certification (gate #1 · happening NOW)

Operator must affirm:

| # | Gate | Confirmation needed |
|---|---|---|
| 1 | State machine vocab is `OPEN · IN_PROGRESS · PENDING_REVIEW · PENDING_CLOSURE · CLOSED` | ☐ yes / ☐ changes requested |
| 2 | All 5 workflows map to this vocab (no extension states authorized in Phase 1A) | ☐ |
| 3 | Universal transition contract: `POST /api/<workflow>/{id}/transition` | ☐ |
| 4 | `workflow_state_events` is the canonical audit collection (sibling to all 5 workflows) | ☐ |
| 5 | Role matrix as documented in `PHASE1A_ROLE_MATRIX.md` | ☐ |
| 6 | Read-shim contract: `get_lifecycle_state()` helper used during Phase 1B migration | ☐ |
| 7 | OSHA closure attestation policy: attestation suffices, Super-Admin can override | ☐ |
| 8 | DR return-to-field notifies submitter via `notifications` collection | ☐ |
| 9 | Payroll Variance always requires explicit Sandy finalize (no auto-close after 24h) | ☐ |
| 10 | QA/QC + Site Inspection `assigned_to` is free-text in Phase 1A (FK migration → Phase 3) | ☐ |
| 11 | Reopen authority = same role tier that closed it OR Admin OR Super-Admin | ☐ |
| 12 | No Phase 1A scope leakage into Phase 1B/2/3/4 boundaries listed in `PHASE1A_WORKFLOW_DESIGN.md` §7 | ☐ |

**Once all 12 gates are affirmed, operator issues the BUILD authorization.**

---

## 2 · Build-stage tests (gate #2 · before preview deploy)

### 2.1 · Unit tests

| Test class | Coverage target |
|---|---|
| `test_state_machine_transitions.py` | Every allowed transition succeeds · every forbidden transition returns 409 · idempotency (same transition twice → 409) |
| `test_role_gates.py` | For each (workflow, transition, role) cell in `PHASE1A_ROLE_MATRIX.md`: assert authorized → 200, unauthorized → 403 |
| `test_workflow_state_events_audit.py` | Every transition writes exactly 1 row · TTL index in place · history endpoint returns chronologically |
| `test_auto_transitions.py` | DR/Payroll/QA-QC/Site auto-transitions fire on correct triggers · idempotent under concurrent writes |
| `test_incident_capa_pending_closure.py` | First CAPA link → PENDING_CLOSURE · last CAPA close → PENDING_REVIEW · interim CAPA close ≠ transition |
| `test_dr_return_to_field.py` | Return-to-field sets `return_reason` and notifies submitter |
| `test_payroll_finalize.py` | Cannot finalize with null decisions · finalize attestation required · CLOSED batch immutable until reopen |
| `test_qaqc_deficiency_propagation.py` | Inspection-level state mirrors aggregate of deficiency states |
| `test_read_shim.py` | Legacy records without `lifecycle_state` return correct derived state · once `lifecycle_state` set, derivation skipped |
| `test_osha_closure_gate.py` | OSHA-recordable incident requires attestation · Super-Admin override path works |
| `test_reopen_paths.py` | Every workflow's reopen path requires `reason` · reopen increments counter · reopen does not zero out previous closure metadata |
| `test_super_admin_overrides.py` | Super-Admin can perform any transition with `reason` · audit row marks `actor_role="super-admin-override"` |

**Target coverage: ≥ 95 % of new code · 100 % of state machine paths.**

### 2.2 · Integration tests

| Test | Coverage |
|---|---|
| `test_incident_full_lifecycle.py` | Create → IN_PROGRESS → link CAPA → PENDING_CLOSURE → close CAPA → PENDING_REVIEW → CLOSED → reopen → CLOSED again. Assert all 7 state events recorded. |
| `test_dr_review_cycle.py` | Submit DR → PM reviews → returns to field → field resubmits → PM approves. Assert notifications sent. |
| `test_payroll_full_batch.py` | Upload CSV → 50 rows → decide each → auto-PENDING_REVIEW → finalize → assert downstream consumers read CLOSED |
| `test_qaqc_remediation_cycle.py` | Submit inspection with 3 deficiencies → assign each → crew claims → PM verifies 2 → reject 1 → re-claim → verify → close inspection |
| `test_site_inspection_walk.py` | Same shape as QA/QC for site inspection |
| `test_accountability_alignment.py` | Phase 1B read-shim consumed by accountability_projection returns canonical state |

### 2.3 · Backwards-compatibility tests

| Test | Asserts |
|---|---|
| Existing `POST /incidents` (create) | unchanged payload contract |
| Existing `GET /incidents` list response | does NOT include `lifecycle_state` in `IncidentSummary` (preserved API shape) |
| Existing `GET /incidents/{id}` detail | INCLUDES new fields (`lifecycle_state`, `state_changed_at`, `closed_at`, `closed_by`, `reopened_count`) — additive, won't break clients ignoring unknown fields |
| Existing `DELETE /incidents/{id}` | unchanged · CAPA-link guard still works |
| All existing CAPA, Asset Transfer, Task, Fleet Defect endpoints | untouched · no diff in those tests |

### 2.4 · Data migration tests

| Test | Asserts |
|---|---|
| Startup migration on `incidents` | every doc without `lifecycle_state` gets it set to `OPEN` · `_lifecycle_migrated_at` marker stamped · idempotent (running twice is no-op) |
| Startup migration on `daily_reports` | same |
| Startup migration on `payroll_variance_batches` | same |
| Startup migration on `qaqc_inspections` | inspection-level set to `OPEN` · existing text-array deficiencies converted to object-array on first read via shim |
| Startup migration on `inspections` (site) | same as QA/QC |

### 2.5 · Frontend tests

| Test | Asserts |
|---|---|
| `LifecyclePanel` component renders correct buttons for each (workflow, role, state) | per `PHASE1A_ROLE_MATRIX.md` |
| Lifecycle history drawer paginates correctly | TTL records >100 |
| `ViewIncident.jsx` integration | Lifecycle panel replaces / augments derived banner |
| `ViewDailyReport.jsx` integration | Returns-to-field text input present |
| `HrPayrollVariance.jsx` integration | Finalize button appears on PENDING_REVIEW |
| QA/QC + Site Inspection deficiency action menus | Assign / Claim / Verify / Reject buttons gated correctly |

### 2.6 · Regression tests (existing battery)

* All Sprint 1F accountability projection tests (5)
* All Sprint 1G photo viewer tests (6)
* All iter445 scheduler hardening tests (7)
* All iter446 production certification probes
* Photo viewer (`/api/job-photos/{id}/raw`) presigned-URL contract preserved
* Accountability snapshot envelope shape preserved
* Command Center cards continue to render

### 2.7 · Performance tests

| Test | Asserts |
|---|---|
| Concurrent transition (10 workers, same doc) | Exactly 1 succeeds, 9 get 409 · audit table records 1 row + 9 attempts |
| Bulk-load 1000 historical transitions | Index latency < 100ms p99 |
| `GET /api/admin/workflow-state-events?workflow=incident` filter | < 500ms with index |

---

## 3 · Preview-deploy gate (gate #2 · between Build and Preview)

Before issuing the preview-deploy authorization:

| Gate | Required outcome |
|---|---|
| All unit tests pass | ≥ 95 % coverage on new code |
| All integration tests pass | 100 % of state machine paths |
| All backwards-compatibility tests pass | 0 regressions |
| Migration scripts dry-run on production-mirror DB | 0 errors |
| Lint clean (ruff + eslint) | 0 errors |
| Frontend smoke test of all 5 detail pages | LifecyclePanel renders correctly |
| Audit collection indexes created on backend startup | confirmed in logs |

**Total expected effort:** ~8-12 engineer days (4-6 sprints if 1-2 engineers).

---

## 4 · Preview-certification gate (gate #2.5)

Once preview deploy is live:

| Probe | Expected outcome |
|---|---|
| `POST /api/incidents/{id}/transition {to_state: "IN_PROGRESS"}` (Safety token) | 200 · state event written |
| `POST /api/incidents/{id}/transition {to_state: "CLOSED"}` (HR token) | 403 (role gate) |
| `POST /api/incidents/{id}/transition` with invalid to_state | 422 |
| `POST .../transition` twice rapidly | second returns 409 |
| Frontend: Mark Closed button disappears when state is OPEN | confirmed by screenshot |
| Frontend: Reopen button appears when state is CLOSED | confirmed |
| `/api/admin/workflow-state-events` returns paginated history | confirmed |
| Migration: every existing incident has `lifecycle_state="OPEN"` post-startup | DB query |
| OSHA-recordable closure without attestation | 422 with helpful error |
| Super-Admin override path with reason | 200 · audit row marks override |
| DR return-to-field triggers notification | notification row created |
| Accountability projection still returns correct envelope | regression battery passes |
| Command Center still renders all cards | regression battery passes |
| Photo Viewer still returns presigned R2 | unchanged |

**All 14 probes pass → operator authorizes production deploy.**

---

## 5 · Production-deploy gate (gate #3)

Per the iter446 pattern:
1. Operator clicks Deploy via Emergent button
2. Agent re-probes `/api/version` for new `source_hash`
3. Agent runs production probe battery (same as preview-cert §4)
4. Agent produces `PHASE1A_PRODUCTION_CERTIFICATION.md`
5. Operator monitors first 24h for unexpected state-event rows

---

## 6 · Rollback contract

If any 🔴 issue surfaces post-production deploy:

| Layer | Rollback | RTO |
|---|---|---|
| Backend | Redeploy previous backend commit | < 5 min |
| Frontend | Redeploy previous frontend bundle | < 5 min |
| `workflow_state_events` collection | Leave (TTL prunes in 7 years; operator-side `db.collection.drop()` available) | < 1 min |
| `lifecycle_state` fields on workflow records | Leave (additive; no consumer breaks if it stays) | n/a |
| Migration `_lifecycle_migrated_at` markers | Leave | n/a |

**Full rollback wall-clock: < 10 min.** Lossless (audit rows survive).

---

## 7 · Success metrics (Phase 1A complete certifies when)

| Metric | Target |
|---|---|
| 5 workflows transition from 🔴 INCOMPLETE → 🟢 COMPLETE | yes |
| Operational Completeness Audit re-run | 56 % → ≥ 65 % |
| User Task Completion: 6 dead-ends closed | 0 dead-ends in Phase 1A scope |
| Audit Trail Coverage: 5 workflows graduate from 🔴 NONE → 🟢 dedicated | yes |
| Status Vocabulary Consistency (within Phase 1A scope) | 100 % (one vocab) |
| Source-of-Truth Confidence | rises from 56 % → ≥ 65 % |
| No regressions in adjacent surfaces | ≥ 0 (target: 0) |

When all 7 metrics hit target, Phase 1A is certified complete. Phase 1B authorization can be issued.

---

## 8 · OMEGA discipline

🟢 Design-only · certification gates defined · test inventory enumerated · success metrics quantified.

🛑 **AWAITING OPERATOR DESIGN CERTIFICATION (§1 gates 1-12).** Build stage is NOT authorized until operator signs off on this document plus the design + state machine + role matrix.

---

## 9 · Operator certification block (sign here)

```
PHASE 1A DESIGN CERTIFICATION

[ ] All 12 design gates affirmed in §1
[ ] All 5 open design questions answered (PHASE1A_WORKFLOW_DESIGN.md §9)
[ ] No scope leakage into Phase 1B/2/3/4
[ ] Build stage authorized

OPERATOR:  ___________________________
DATE:      ___________________________
NEXT STEP: [ ] Issue OMEGA BUILD authorization
           [ ] Request design revisions: _______________________________________
```
