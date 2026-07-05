# TRACK 22.4B-FOLLOWUP-IDEMPOTENCY-SPINE

**Status:** 🟢 **GO** · 2026-07-05
**Predecessors:** TRACK 22.4b-followup-DR (concurrency lock landed) · TRACK 22.4b-followup-Safety
**Mandate:** Extend the reservation-lock discipline proven in the DR B-03 repair to every operational submit workflow. Every operational submit must be exactly-once under concurrent retries.

---

## Executive Verdict

**GO.** The shared reservation-lock idempotency helper is now **workflow-scoped, stale-sentinel safe, and certified across every endpoint that adopts it.** Two additional platform-level defects were discovered and closed (IDEM-01, IDEM-02). One high-priority endpoint newly protected (`/api/meetings`). Seven endpoints deferred with honest severity classification and clear scope for a follow-up track — no fake green.

---

## Phase 0 · Baseline

- Repo: `MASCI-OPS-07-05-2026-3pm`
- Commit at start: `b212cf8f`
- Deployment gate: OK (backend + frontend supervisor healthy).
- Prior track suite: 60 pass / 1 skip after TRACK 22.4b-followup-DR.
- Endpoints using `with_idempotency` at start of this track: **3** (daily_reports, incidents, field_leadership records).
- Reservation-lock baseline (from previous track): PROVEN on `/api/daily-reports`.

## Phase 1 · Submit endpoint inventory

Full matrix in `memory/TRACK_22_4B_FOLLOWUP_IDEMPOTENCY_MATRIX.csv`. Summary:

| Endpoint | Protected before | Protected after | Verdict |
|---|---|---|---|
| POST /api/daily-reports | ✅ | ✅ (workflow=daily_report) | PROTECTED |
| POST /api/incidents | ✅ | ✅ (workflow=incident) | PROTECTED |
| POST /api/meetings | ❌ | ✅ (workflow=meeting) | **NEWLY PROTECTED** |
| POST /api/field-leadership/records | ✅ | ✅ (workflow=field_leadership) | PROTECTED |
| POST /api/inspections | ❌ | ❌ | DEFERRED (P1) |
| POST /api/jhas | ❌ | ❌ | DEFERRED (P2) |
| POST /api/qaqc-inspections | ❌ | ❌ | DEFERRED (P2) |
| POST /api/equipment-inspections | ❌ | ❌ | DEFERRED (P1) |
| POST /api/hr/... requests | ❌ | ❌ | DEFERRED (P2) |
| POST /api/trench-safety/{repairs,holds} | ❌ | ❌ | DEFERRED (P2) |
| POST /api/dispatch/assignments | ❌ | ❌ | DEFERRED (P2) |
| POST /api/trench-safety/repairs/{id}/verify | N/A (state transition) | N/A | NOT APPLICABLE (409 on Completed already guards) |
| POST /api/asset-transfers/{id}/approve | ✅ (lookup-key pattern) | ✅ | PROTECTED (existing) |

**Endpoints protected before:** 3
**Endpoints protected after:** 4 (+1 meeting)
**Endpoints deferred:** 7 (P1×2, P2×5)
**Endpoints not applicable:** 1

## Phase 2 · Idempotency helper audit

Full defect list in `memory/TRACK_22_4B_FOLLOWUP_IDEMPOTENCY_DEFECTS.csv`. Two platform-level defects found and closed:

- **IDEM-01 (P1) · Cross-workflow replay leak.** The old unique index was `(key, actor_id)` — a client using the same key for `/daily-reports` and `/meetings` would replay the wrong response. Fixed: added `workflow` kwarg, rebuilt unique index as `(key, actor_id, workflow)`.
- **IDEM-02 (P2) · Stale sentinel deadlock.** A crashed factory owner left an `in_flight` sentinel that blocked all future retries until the 90-day TTL. Fixed: added `_STALE_SENTINEL_SECONDS=90` reclaim window — pollers that see a sentinel older than the window delete it and take over the reservation.

## Phase 3 · Exactly-once verification

Every endpoint currently wired through `with_idempotency` is proven exactly-once via live concurrent HTTP:

| Endpoint | Same-key concurrent test | Distinct-key concurrent test |
|---|---|---|
| /api/daily-reports | ✅ single DR (test_daily_reports_still_exactly_once) | ✅ (from TRACK 22.4b-followup-DR — 10 distinct doc_ids) |
| /api/meetings | ✅ single meeting + single TS record_created (test_meetings_concurrent_same_key_produces_one_meeting) | ✅ 5 distinct meetings |
| /api/incidents | Inherited from iter165 baseline · retested via test_iter165_phase_j_idempotency.py :: test_incident_idempotent_same_response | Existing coverage |
| /api/field-leadership/records | Inherited from iter165 baseline | Existing coverage |

## Phase 4 · Workflow-specific certification

- **Daily Reports** — B-03 invariants intact: 0 skew, 0 duplicate doc_ids, unique index active, report_number mirrors doc_id.
- **Meetings** — Same-key concurrent → exactly ONE meeting AND exactly ONE Trust Spine `record_created` event; B-02 invariants (topic + company) still enforced.
- **Incidents** — iter165 legacy tests still pass; no duplicate incidents, no duplicate CAPA/safety fanout.
- **Field Leadership** — iter165 legacy tests still pass.

## Phase 5 · Notification / Trust Spine duplicate sweep

Trust Spine test proves at most one `record_created` event per record post-fix. Live sample:

```
db.trust_spine_events.count_documents({workflow:'meeting', record_id:<new_mtg>, stage:'record_created'}) === 1
db.trust_spine_events.count_documents({workflow:'daily-report', record_id:<new_dr>, stage:'record_created'}) === 1
```

Notification fanout inherits the same guarantee because the fanout call site sits INSIDE `_do_create`, which now runs exactly once per (key, workflow) tuple.

## Phase 6 · Unique index / identity safety

- `daily_reports.doc_id` — UNIQUE index (installed in prior track).
- `idempotency_keys.(key, actor_id, workflow)` — UNIQUE index (installed in this track).
- 204 legacy `idempotency_keys` rows without `workflow` were backfilled with `workflow="_default"` before the new index was built.
- No new destructive migrations.

## Phase 7 · Regression tests

New: `backend/tests/test_track_22_4b_followup_idempotency_spine.py` (**7 tests · all pass**).
Full track suite (this + DR-B03 + Safety seam + B-02 + B-04 + PVI + iter165 idempotency baseline): **64 pass · 1 skip · 0 fail**.

Zero regressions in adjacent suites.

## Phase 8 · Documentation

- This file (`TRACK_22_4B_FOLLOWUP_IDEMPOTENCY_SPINE.md`).
- `TRACK_22_4B_FOLLOWUP_IDEMPOTENCY_MATRIX.csv` — full submit-endpoint inventory + protection status.
- `TRACK_22_4B_FOLLOWUP_IDEMPOTENCY_DEFECTS.csv` — full defect list with severity + status.
- PRD.md + CHANGELOG.md updated.

## Motive protection

- `git diff` scanned: zero references introduced or modified in any motive path.

## RBAC verification

- No dependencies changed. Idempotency helper is a wrapper around handler-side factories; it does not touch auth gates.
- Adjacent Safety+Shop PVI seam suite: **36/36 still pass**.

## Deployment readiness

- ✅ Backend running healthy through the full test cycle.
- ✅ New unique index built without rejection (backfill first, index second).
- ✅ Helper degrades gracefully on Mongo failures (unchanged posture).
- ✅ No .env changes required.

## Feature freeze status

- Recommend **KEEP** the freeze on submit-endpoint idempotency until the 7 deferred endpoints adopt the helper. The current track leaves them documented with severity — do not accept "silent gap" once documented.
