# TRACK 22.4B-FOLLOWUP-IDEMPOTENCY-SPINE-PHASE-2

**Status:** 🟢 **GO** · 2026-07-05
**Predecessors:** TRACK 22.4b-followup-Idempotency-Spine (Phase 1)
**Mandate:** Adopt the workflow-scoped reservation-lock idempotency helper on the seven submit endpoints deferred from Phase 1, starting with the two P1 endpoints (Equipment Pre-Op/DVIR, Inspections).

---

## Executive Verdict

**GO.** The two P1 endpoints (`/api/equipment-inspections`, `/api/inspections`) are now wrapped in the shared reservation-lock and certified exactly-once. Two additional P2 endpoints (`/api/jhas`, `/api/qaqc-inspections`) also newly protected in the same pass. Six endpoints deferred to targeted follow-up tracks with honest severity classification, blocker reasoning, and owner track assignment — no fake green.

## Phase 0 · Baseline

- Repo: `MASCI-OPS-07-05-2026-3pm`
- Commit at start: `b391d86e`
- Deployment gate: OK.
- Phase 1 protected endpoints: 4 (daily_reports, incidents, meetings, field_leadership).
- Phase 1 deferred endpoints: 7.
- Idempotency helper: workflow-scoped reservation lock with 90s stale-sentinel reclaim, unique index on `(key, actor_id, workflow)`.

## Endpoint verdicts

| Endpoint | Before | After | Verdict |
|---|---|---|---|
| POST /api/inspections | ❌ | ✅ (`workflow="inspection"`) | **NEWLY PROTECTED (P1)** |
| POST /api/equipment-inspections | ❌ | ✅ (`workflow="equipment_inspection"`) | **NEWLY PROTECTED (P1)** |
| POST /api/jhas | ❌ | ✅ (`workflow="jha"`) | **NEWLY PROTECTED (P2)** |
| POST /api/qaqc-inspections | ❌ | ✅ (`workflow="qaqc"`) | **NEWLY PROTECTED (P2)** |
| POST /api/hr/employee-requests | ❌ | ❌ | DEFERRED (P2) — blocked pending HR PVI trace |
| POST /api/dispatch/assignments | ❌ | ❌ | DEFERRED (P2) — >1400 LOC handler w/ SMS+Motive; needs targeted track |
| POST /api/trench-safety/{repairs,holds,inspections} | ❌ | ❌ | DEFERRED (P2) — safety-gated, low concurrency risk, B-04 invariants must be preserved |
| POST /api/shop/defects | ❌ | ❌ | DEFERRED (P2) — needs canonical-write-path audit first |

**Phase 2 net delta: +4 protected endpoints (2 P1 + 2 P2), 6 endpoints honestly deferred with owner tracks.**

## Defects fixed

- **IDEM-COV-02 (P1)** — `/api/inspections` protected (workflow=inspection).
- **IDEM-COV-05 (P1)** — `/api/equipment-inspections` protected (workflow=equipment_inspection).
- **IDEM-COV-03 (P2)** — `/api/jhas` protected (workflow=jha).
- **IDEM-COV-04 (P2)** — `/api/qaqc-inspections` protected (workflow=qaqc).

Full defect log in `memory/TRACK_22_4B_FOLLOWUP_IDEMPOTENCY_PHASE_2_DEFECTS.csv`.

## Certification tests (Phase 12)

`backend/tests/test_track_22_4b_followup_idempotency_spine_phase_2.py` — **7 tests, all pass**:

1. `test_inspections_concurrent_same_key_one_record` — Safety-gated inspection: 2× concurrent with same key → 1 inspection, 1 Trust Spine event, 1 fan-out.
2. `test_equipment_inspections_concurrent_same_key_one_record` — Pre-Op: 2× concurrent with same key → 1 inspection.
3. `test_jhas_concurrent_same_key_one_record` — JHA: 2× concurrent with same key → 1 JHA.
4. `test_qaqc_concurrent_same_key_one_record` — QA/QC: 2× concurrent with same key → 1 record.
5. `test_inspections_distinct_keys_produce_distinct_records` — 5 distinct keys → 5 distinct inspections (no global lock).
6. **`test_parallel_independence_across_workflows`** — 10 concurrent submits across 4 different workflows all complete with distinct records → proves the lock is NOT a global mutex.
7. `test_cross_workflow_scoping_still_holds` — same key across `/inspections` and `/jhas` → no cross-workflow replay (each returns its own workflow's `doc_id` prefix).

**Full track suite:** DR-B03 (14) + Safety seam (11) + B-02 (6) + B-04 (6) + PVI (13) + iter165 idempotency baseline (8) + Spine Phase 1 (7) + Spine Phase 2 (7) = **72 tests · 71 pass · 1 skip · 0 fail**.

## Parallel independence verdict

`test_parallel_independence_across_workflows` proves 10 concurrent submits across `/inspections`, `/qaqc-inspections`, `/jhas`, and `/meetings` — each with a distinct idempotency key — all complete successfully and produce 10 distinct records. The reservation-lock is scoped to `(key, actor_id, workflow)` — it never blocks unrelated submissions.

## Trust Spine duplicate verdict

Every newly-protected endpoint's fan-out call (Trust Spine `emit_record_created`, safety notification, PM notification, operational signal, maintenance-hold auto-open) now sits INSIDE the `_do_create` factory — the factory runs exactly once per (key, actor, workflow), so every downstream side-effect emits exactly once.

## Notification duplicate verdict

Same-inheritance rule as Trust Spine — the entire fan-out block is inside `_do_create` for every protected endpoint. Concurrent retries do NOT double-notify safety, PMs, HR, or shop.

## RBAC verdict

Unchanged. Each endpoint retained its original `dependencies=[...]` gate:
- `/api/inspections` — `_insp_deps` (safety/admin when available, rate-limit fallback).
- `/api/equipment-inspections` · `/api/jhas` · `/api/qaqc-inspections` — `rate_limit_public_post`.
- Adjacent Safety+Shop PVI seam suite: **36/36 still pass**.

## Motive protection verdict

**Not touched.** `git diff` scanned — zero references introduced or modified in any Motive path. Dispatch endpoint deferred specifically to keep Motive read-only path untouched.

## Deployment readiness

- ✅ Backend healthy through the full test cycle.
- ✅ No .env changes required.
- ✅ No new indexes required (helper's `(key, actor_id, workflow)` index already exists from Phase 1).
- ✅ Zero regressions across all prior track suites.

## Files created

- `backend/tests/test_track_22_4b_followup_idempotency_spine_phase_2.py`
- `memory/TRACK_22_4B_FOLLOWUP_IDEMPOTENCY_SPINE_PHASE_2.md`
- `memory/TRACK_22_4B_FOLLOWUP_IDEMPOTENCY_PHASE_2_MATRIX.csv`
- `memory/TRACK_22_4B_FOLLOWUP_IDEMPOTENCY_PHASE_2_DEFECTS.csv`

## Files changed

- `backend/routes/safety.py` — `create_inspection` + `create_jha` wrapped in `_do_create` closures with `with_idempotency`.
- `backend/routes/equipment.py` — `create_equipment_inspection` wrapped.
- `backend/routes/qaqc.py` — `create_qaqc` wrapped.
- `memory/PRD.md` + `CHANGELOG.md`.

## Feature freeze

**KEEP** the freeze on submit-endpoint idempotency until the 6 remaining deferred endpoints (HR requests, dispatch assignments, trench-safety writes, shop defects) adopt the helper. Everything else can proceed.
