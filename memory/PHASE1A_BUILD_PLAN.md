# Phase 1A · Build Plan

**Program:** OMEGA · PCP · Phase 1A · Final Build Package
**Scope:** 6 workflows · ~12.5 engineer-days · ~3,000 LOC across backend + frontend
**Date:** 2026-06-01

---

## 1 · Build sequencing (sprint-by-sprint)

### Sprint B1 · Foundation (Days 1-3 · ~3 days)

| Day | Module | Deliverable |
|---|---|---|
| 1 | `lib/workflow_state_machine.py` | ALLOWED_TRANSITIONS map + validator + role-gate resolver + unit tests |
| 1 | `lib/workflow_state_events.py` | Audit writer + idempotency guard + index ensurer |
| 2 | `lib/lifecycle_read_shim.py` | `get_lifecycle_state()` helper + per-workflow derivation fallback |
| 2 | `server.py` startup hook | 5 idempotent migrations · `workflow_state_events` collection bootstrap |
| 3 | `routes/workflow_transitions.py` | Cross-cutting admin endpoint `GET /api/admin/workflow-state-events` |
| 3 | Unit tests | `test_state_machine_transitions.py`, `test_role_gates.py`, `test_workflow_state_events_audit.py`, `test_read_shim.py` |

**Exit gate B1:** Foundation libraries 100% covered by unit tests · server boots clean · `/api/admin/workflow-state-events` returns empty envelope.

### Sprint B2 · Lifecycle endpoints (Days 4-6 · ~3 days)

| Day | Workflow | Deliverable |
|---|---|---|
| 4 | OC-001 Incidents | `POST /api/incidents/{id}/transition` · OSHA closure gate · CAPA-linked auto-transitions · per-doc state-events |
| 4 | OC-007 Payroll Variance | `POST /api/hr/payroll-variance/batches/{id}/transition` · finalize attestation · auto-transitions on row decisions |
| 5 | OC-002 Daily Reports | `POST /api/daily-reports/{id}/transition` · return-to-field notification · revision count |
| 5 | OC-003 QA/QC | Inspection-level + deficiency-level transitions · auto-cascading · deficiency text→object read-shim |
| 6 | OC-004 Site Inspections | Inspection-level + finding-level (mirror QA/QC) |
| 6 | Integration tests | `test_incident_full_lifecycle.py`, `test_dr_review_cycle.py`, `test_payroll_full_batch.py`, `test_qaqc_remediation_cycle.py`, `test_site_inspection_walk.py` |

**Exit gate B2:** All 5 lifecycle workflows transitionable end-to-end via curl · integration tests green.

### Sprint B3 · JHA Acknowledgement Ledger (OC-005) · (Days 7-9 · ~3 days)

| Day | Module | Deliverable |
|---|---|---|
| 7 | `routes/jha_acknowledgements.py` | 6 endpoints (POST · GET per-jha · GET per-job · GET admin · DELETE · GET coverage) |
| 7 | Coverage computation | per-day per-job rollup logic · "active crews" derived from `dispatch_assignments` |
| 8 | Public token endpoint | `/api/public/jha-ack/{token}` · JWT mint at JHA creation |
| 8 | Notifications | 4h-after-job-start coverage gap + daily 18:00 batch (reuses notifications collection) |
| 9 | Accountability + CC integration | `JHA_ACK_MISSING` source + `SAF-JHA-ACK-MISSING` rule |
| 9 | Unit tests | `test_jha_acknowledgement_ledger.py` (10 sub-tests) |

**Exit gate B3:** OC-005 endpoints curlable · coverage dashboard math verified · notifications fire on test fixtures.

### Sprint B4 · Frontend integration (Days 10-12 · ~3 days)

| Day | Surface | Deliverable |
|---|---|---|
| 10 | `components/LifecyclePanel.jsx` | Shared component · 5 state pills · role-gated buttons · history drawer · OSHA closure modal · reopen modal |
| 10 | `components/JhaAcknowledgePanel.jsx` | Signature pad · verbal attestation · submit flow |
| 11 | Page integrations | ViewIncident · ViewDailyReport · HrPayrollVariance · ViewQaqcInspection · ViewSiteInspection · JhaList · FieldLeadershipHub |
| 11 | NEW pages | `SafetyJhaAcks.jsx` (coverage dashboard) · `PublicJhaAck.jsx` (QR submission) · `App.js` routes |
| 12 | AdminHub tile | JHA coverage link |
| 12 | Frontend smoke tests | each modified page renders · transitions complete e2e via Playwright (testing_agent_v3_fork) |

**Exit gate B4:** All 7 modified pages render · LifecyclePanel functional on all 5 lifecycle workflows · JHA panel signature capture works · public QR flow works.

### Sprint B5 · Hardening + Certification (Days 12.5 · ~0.5 days)

| Activity | Deliverable |
|---|---|
| Coverage audit | Confirm ≥95% on new code via coverage.py |
| Lint pass | Ruff + ESLint zero errors |
| Backwards-compat regression | All Sprint 1F/1G/iter445/iter446 tests still pass |
| Migration dry-run on prod-mirror DB | 0 errors |
| Preview deploy + certification probes (per `PHASE1A_CERTIFICATION_PLAN.md` §4) | 14 probes pass |

**Exit gate B5:** `PHASE1A_PREVIEW_CERTIFICATION.md` produced · operator sign-off package ready.

---

## 2 · Build dependencies (directed acyclic graph)

```
B1 Foundation ─┬──→ B2 Lifecycle endpoints ─┬──→ B4 Frontend
               │                              │
               └──→ B3 OC-005 JHA ───────────┤
                                              │
                                              └──→ B5 Hardening + Cert
```

* B1 must complete before B2/B3 (libs are dependencies)
* B2 and B3 are independent (could parallelize if 2 engineers)
* B4 depends on B2 + B3
* B5 depends on B4

---

## 3 · Engineer-day estimate (one engineer)

| Sprint | Days | Cumulative |
|---|---|---|
| B1 · Foundation | 3 | 3 |
| B2 · Lifecycle (5 workflows) | 3 | 6 |
| B3 · OC-005 JHA | 3 | 9 |
| B4 · Frontend | 3 | 12 |
| B5 · Hardening + cert | 0.5 | 12.5 |

**Total: ~12.5 engineer-days. With 2 engineers parallelizing B2 and B3, achievable in ~9-10 calendar days.**

---

## 4 · Risk-flagged work items (operator awareness)

| Item | Risk | Mitigation |
|---|---|---|
| QA/QC deficiencies text→object reshape (read-shim) | 🟡 schema concern | Comprehensive read-shim tests; one-shot migration deferred |
| Public JHA token JWT mint pattern | 🟡 reuses existing pattern but new use-case | Reuses existing `lib/public_token.py`; security review on the token claims |
| OSHA closure gate · Super-Admin override path | 🟡 audit-critical | Override path logs to BOTH `workflow_state_events` and `audit_events` with elevated marker |
| Auto-transition idempotency under concurrent writes (e.g., 2 PMs decide last payroll row simultaneously) | 🟡 race condition | Unique compound index + transition-attempt log; second writer hits 409 cleanly |
| LifecyclePanel renders correctly across all 7 pages | 🟢 standard component | Shared component; tested once, used everywhere |

---

## 5 · Out-of-scope (Build stage will NOT touch)

* CAPA workflow (Phase 1B vocab canonicalization)
* Asset Transfers, PO Requests, Tasks, Fleet Defects (already 🟢)
* PPE Return, Photo Janitor, Onboarding/Offboarding multi-step (Phase 2)
* Status vocab consolidation across 13 other workflows (Phase 1B)
* White Label / ForgedOps Operations Center (FROZEN)

---

## 6 · Definition of Done (per workflow)

A workflow is "Phase 1A Done" when:

* ✅ Lifecycle endpoints implemented + tested
* ✅ Role gates enforced + tested
* ✅ Audit row written per transition
* ✅ Read-shim returns canonical state
* ✅ Frontend LifecyclePanel renders correctly
* ✅ Accountability projection updated (read-shim respected)
* ✅ Command Center continues rendering cards (no regression)
* ✅ Preview cert probes pass
* ✅ Backwards-compat regression battery passes
* ✅ Migration is idempotent

---

## 7 · OMEGA discipline

🟢 Day-by-day plan · 5 sprints · ~12.5 engineer-days · 6 workflows · exit gates per sprint.

🛑 Continue to `PHASE1A_TEST_PLAN.md`.
