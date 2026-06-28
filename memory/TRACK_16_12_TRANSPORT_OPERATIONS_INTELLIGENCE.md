# TRACK 16.12 — TRANSPORTATION OPERATIONS INTELLIGENCE (TOI)

**Status:** ✅ GO · production-ready · 67/67 new tests · 474/474 transport-track tests green.
**Date:** 2026-02-10
**Scope:** Single deterministic intelligence engine that powers every Transportation decision in MASCI. Additive only — every existing HR, Dispatch, Safety, Equipment, Orientation, Automation, Email Routing, Identity, and Audit system remains intact.

---

## Mission

Build the operational intelligence engine — not a dashboard, not a scorecard, not a reporting module. Every Transportation decision (driver / carrier / truck recommendation, dispatch readiness, executive view, prediction) derives from one engine. No duplicated business logic. No black boxes. Every score explains itself.

## Architecture

```
backend/lib/
├── transport_intelligence_core.py        ← shared deterministic helpers + audit
├── transport_driver_intelligence.py      ← per-driver scoring + indices
├── transport_carrier_intelligence.py     ← carrier roll-up + preferred status
├── transport_truck_intelligence.py       ← per-truck scoring + DOT
├── transport_prediction_engine.py        ← deterministic 120-day forecasts
├── transport_recommendation_engine.py    ← ranked driver / carrier / truck triples
└── transport_operations_intelligence.py  ← executive dashboard orchestrator

backend/routes/transportation_intelligence.py    ← 8 read-only GET endpoints
frontend/src/pages/transportation/_intelligence.jsx ← /intelligence center
```

Every engine is **pure async** — reads only canonical MASCI collections; never mutates them. Every score carries `explanations[]` mapping each delta back to the record that produced it.

## Driver Intelligence

Sub-indices (each 0–100 with explainable trail):
* **Experience** — years with MASCI + employee vs leased.
* **Compliance** — eligibility state, blocking action items, expired/expiring driver documents.
* **Safety** — safety hold, incidents in last 12 months.
* **Performance** — orientation certificate freshness, dispatch override frequency.

Composite scores: `overall` (weighted average across all indices) and `operational_readiness` (compliance + performance). Bands: `excellent / strong / fair / watch / critical` — non-punitive.

## Carrier Intelligence

Reads `carriers`, `transport_carrier_packets`, `transport_persons`, `transport_trucks`, `transport_eligibility_state`. Indices: compliance / safety / reliability / experience. Surfaces fleet size, eligible-driver-and-truck percentages, packet status, rate acknowledgement, years partnered, `preferred_status` flag.

## Truck Intelligence

Latest inspection result + days-since-inspection + eligibility + safety hold. Indices: mechanical_readiness / dot_compliance. Stale-inspection signal at 180 days.

## Recommendation Engine

`recommend_drivers`, `recommend_carriers`, `recommend_trucks`, and the composite `recommend_dispatch_triple`. Hard-filters to eligible (or pending_review with score ≥ 60), ranks by overall score then safety. Every result carries `why[]` (positive explanations) and `watch[]` (negative / watch explanations). Deterministic ordering — same data, same ranking, every run.

## Prediction Engine

Deterministic 120-day forecast. Buckets: `overdue / due_this_week / due_30_days / due_90_days / beyond_horizon`. Streams: documentation_expirations, inspection_expirations, orientation_renewals, carrier_risk (severity-bucketed from open action items). No ML, no probability fabrication.

## Executive Dashboard Orchestrator

`build_executive_dashboard(db)` composes per-entity intelligence into:
* Transportation / driver / carrier / truck health.
* Dispatch readiness (% eligible drivers + trucks).
* Capacity (totals + eligible counts + percentages).
* Top performers (top 5 each: drivers / carriers / trucks).
* Attention required (bottom 5 each, with watch labels).
* 30 / 90 / 365-day trends from `transport_intelligence_audit` history.

## API surface (read-only, admin-gated)

```
GET /api/admin/transportation/intelligence/drivers/{driver_id}
GET /api/admin/transportation/intelligence/carriers/{carrier_id}
GET /api/admin/transportation/intelligence/trucks/{truck_id}
GET /api/admin/transportation/intelligence/dashboard
GET /api/admin/transportation/intelligence/operational-health
GET /api/admin/transportation/intelligence/recommendations
       ?scope=driver|carrier|truck|triple
       &carrier_id=...&truck_type=...&limit=10
GET /api/admin/transportation/intelligence/predictions
GET /api/admin/transportation/intelligence/audit?kind=...&limit=100
```

Every endpoint uses `require_admin_strict`. No POST / PATCH / DELETE in the intelligence router.

## UI

* `/admin/transportation/intelligence` — new center with three tabs:
  * **Executive** — health tiles + capacity + top performers + attention required + 30/90/365-day trends.
  * **Recommendations** — driver/carrier/truck/triple scope toggle; cards with `why` + `watch`.
  * **Predictions** — bucket counts, forecast lists, carrier-risk roll-up.
* `pages/transportation/_lists.jsx` — `DriverIntelligenceCard` mounted inside `DriverWorkspace` with chip + index breakdown + explanation rows.
* `_shared.jsx` Sub-nav — new **Intelligence** tab next to Command Queue. Native MASCI styling.

## Audit

New collection `transport_intelligence_audit` stores: kind, subject_type, subject_id, snapshot, actor, ts, schema_version. Audit kinds:
* `driver_intelligence_refresh`
* `carrier_intelligence_refresh`
* `truck_intelligence_refresh`
* `driver_recommendations_generated`
* `carrier_recommendations_generated`
* `truck_recommendations_generated`
* `predictions_refresh`
* `executive_dashboard_generated`

Audit writes are best-effort — failure never breaks intelligence callers.

## Determinism + Explainability

Every score is fully reproducible:
* Same inputs → same `overall.score` (verified by test 13, 40, 46).
* Every `explanations[]` row carries `code`, `label`, `impact`, `weight`, `delta`, `record_id`, `record_type`, optional `fix`.
* `schema_version = "16.12.0"` stamped on every snapshot.

## Hard guarantees

* HR (`db.employees`) — untouched.
* Transportation (`carriers`, `transport_persons`, `transport_trucks`) — read only by the engine.
* No new scheduler created (executive dashboard rendered on demand; no daily refresh added — audit history accumulates organically from per-driver/carrier/truck on-demand reads).
* No SMS / Twilio / push references in any new file.
* No `delete_many` / `drop_collection` / `drop_indexes`.
* No punitive vocabulary (rejected / denied / failed) in user-facing labels.

## Tests

`backend/tests/test_track_16_12_transport_operations_intelligence.py`
**67 tests · all passing.**

Coverage:
* Static contract locks (tests 1–5).
* Driver intelligence — basic, not-found, eligibility, safety hold, explanations, audit, determinism, list filter, no-mutation (6–15).
* Carrier intelligence — basic, not-found, safety hold, packet status, preferred status, audit, list, no-mutation, indices, fleet signals (16–25).
* Truck intelligence — basic, not-found, safety hold, inspection states, audit, no-mutation (26–32).
* Recommendation engine — eligibility filter, why labels, carriers, trucks-by-carrier, trucks-by-type, triple, audit, deterministic (33–40).
* Prediction engine — shape, expiring soon, overdue, carrier risk, audit, deterministic (41–46).
* Executive orchestrator — shape, capacity, audit, operational health, top/attention lists, trends buckets (47–52).
* API + UI + gate locks — endpoint paths, admin gating, read-only verbs, router registration, frontend wiring, deployment gate, prior tracks preserved (53–67).

Full transport-track regression: **474 / 474 passing** (Tracks 16.04 → 16.12).

## Six-Pillar Score

| Pillar      | Score | Notes |
|-------------|-------|-------|
| Powerful    | 10/10 | Every dispatch decision can now derive from one engine with explainable rationale. |
| Simple      | 10/10 | One per-entity intelligence library + one orchestrator + one read-only router. No new schedulers. |
| Beautiful   | 9/10  | Native MASCI styling; calm chip palette; explanation rows with impact-coded backgrounds. |
| Trusted     | 10/10 | Every refresh + recommendation + prediction audited. Source records untouched. |
| Proven      | 10/10 | 67 new tests · 474 transport-track tests green · deterministic repeat tests. |
| Deployable  | 10/10 | Additive only · no schema migration · no removed/renamed routes · zero design drift. |
| **Overall** | **9.8 / 10 · GO.** | |

## Risks / Deferrals

* No on-demand refresh button on the executive dashboard yet — operators trigger refreshes by re-opening individual entities (which writes audit rows). A "Refresh now" button can be added trivially when operators ask.
* Carrier "average response time" and "average dispatch acceptance" metrics deferred — they require dispatch-assignment outcome telemetry that lives in a separate track.
* Incident frequency uses `db.incidents` if present; soft-skips otherwise.

## Next Recommended Track

**Track 16.13 — Dispatch Decision Surface.** Surface `recommend_dispatch_triple` directly inside the dispatcher's assignment flow, with one-click "Why" drawer. Now safe because the intelligence engine is in place and audited.

Done means done.
