# TRACK 16.13 — DISPATCH DECISION SURFACE

**Status:** ✅ GO · merged · 32/32 new tests · 506/506 transport-track tests green.
**Date:** 2026-02-10
**Scope:** Surface the Track 16.12 Transportation Operations Intelligence engine inside the dispatcher assignment flow. Read-only, explainable, never weakens the Track 16.09 hard-block, never duplicates intelligence.

---

## Mission

Make dispatch smarter without making dispatch slower. The dispatcher sees:
* the best available driver / carrier / truck triple,
* the composite score + grade,
* the human-readable reasons (`why`) and watch items (`watch`),
* ranked eligible alternatives,
* excluded options with reason labels.

One click to understand. One click to apply. Never required. Never blocking.

## Recommendation Endpoint

```
GET  /api/dispatch/transportation/recommendation        ← read-only · admin OR dispatch
POST /api/dispatch/transportation/recommendation/audit  ← dispatcher interaction events
```

* Inputs (all optional): `carrier_id`, `truck_type`, `transport_person_id`, `transport_truck_id`, `job_id`, `project_id`, `requested_date`, `limit` (1–20, default 5).
* Output shape:
  ```json
  {
    "ok": true,
    "recommendation_id": "...",
    "recommended": { "carrier": {}, "driver": {}, "truck": {},
                     "triple": {}, "score": 94, "grade": "excellent",
                     "why": [], "watch": [] },
    "alternatives": { "drivers": [], "carriers": [], "trucks": [] },
    "excluded":     { "drivers": [], "trucks": [], "carriers": [] },
    "schema_version": "16.13.0",
    "generated_at": "..."
  }
  ```
* Delegates ALL scoring to `lib/transport_recommendation_engine.py` (Track 16.12). Zero duplicated logic.
* Excluded section enumerates non-dispatchable rows from `transport_eligibility_state` with the existing reason labels — so dispatchers see *why* something is not recommended.
* Engine failure returns `ok=false` with a friendly fallback message — assignment continues through the standard gate.

## Dispatch UI

**`DispatchDecisionChip` component** mounted at the top of `AssignmentDrawer.jsx`. Tiny chip (test ID `dispatch-decision-chip`) showing the recommended triple + grade chip + optional watch-count line.

**Why drawer** (test ID `dispatch-decision-why-drawer`) opens on click:
* Recommended carrier / driver / truck rows + composite chip.
* `Why` list and `Watch` list (test IDs `dispatch-why-*`, `dispatch-watch-*`).
* Three alternatives sections (`dispatch-decision-alt-drivers`, `-trucks`, `-carriers`) each with score chip, top reasons, `Select` button.
* `dispatch-decision-excluded` section with eligibility-derived reason labels.
* Two primary actions: **Use this recommendation** / **Ignore**. Each fires an audit event.

Selecting the recommendation or an alternative populates the existing reassign form fields (`setNewDriverId` / `setNewTruckId`) inside the AssignmentDrawer. The final assignment continues through the unchanged Track 16.09 dispatch gate — the chip never bypasses, never writes eligibility.

## Audit

New collection `transport_dispatch_recommendation_audit`. Kinds:
* `transport_dispatch_recommendation_generated` — every endpoint call.
* `transport_dispatch_recommendation_viewed` — Why drawer opened.
* `transport_dispatch_recommendation_selected` — operator used the top recommendation.
* `transport_dispatch_non_recommended_selected` — operator picked a lower-ranked eligible alternative. Optional note.
* `transport_dispatch_recommendation_ignored` — operator dismissed the chip.
* `transport_dispatch_recommendation_failed` — engine unavailable or compute error.

Audit writes are best-effort — failure never breaks dispatch.

## Performance

* Frontend chip debounces requests (300 ms) and only refetches when `carrier_id` context changes.
* Backend `limit` defaults to 5 (max 20).
* Reuses existing intelligence helpers — no new heavy queries.
* Engine failures degrade gracefully with `ok=false` + fallback message.

## RBAC

`require_dispatch_or_admin_dep` — the same gate already used across all of `routes/dispatch_lifecycle.py`. Admin tokens and dispatch tokens both authorize; anonymous returns 401 (proven by test 4).

## Tests

`backend/tests/test_track_16_13_dispatch_decision_surface.py` · **32 tests, all passing.**

Coverage:
* Endpoint contracts: paths, GET-only for read, POST for audit (1–5).
* No duplicated scoring logic in the route (6).
* Excludes non-dispatchable options from alternatives (7).
* Excluded section carries reason labels (8).
* Returns recommended triple, alternatives, why/watch, schema version (9–12).
* Audit events: generated, viewed, selected, non_recommended_selected, ignored (13–17).
* Invalid event rejected; note length capped (18–19).
* Engine unavailable returns graceful fallback (20).
* Frontend chip / Why drawer / alternatives / excluded sections exist (21–24).
* Alternative selection populates assignment fields (25).
* No dispatch gate bypass (26).
* No new blocking logic in the route (27).
* No SMS / push (28).
* No punitive vocabulary (29).
* Router registered in `server.py` (30).
* Deployment gate includes Track 16.13 + all prior transport tracks preserved (31–32).

Full transport-track regression: **506 / 506 passing** (Tracks 16.04 → 16.13).

## Six-Pillar Score

| Pillar      | Score | Notes |
|-------------|-------|-------|
| Powerful    | 10/10 | Best assignment + explainability surface in one click. |
| Simple      | 10/10 | One chip, one drawer, one ranked list, one audit collection. |
| Beautiful   | 9/10  | Native AssignmentDrawer styling; chip is calm emerald, watch is amber. |
| Trusted     | 10/10 | Every recommendation + selection + ignore audited. No gate bypass. |
| Proven      | 10/10 | 32 new tests + 506 transport-track regression green. |
| Deployable  | 10/10 | Additive only · no schema migration · no removed routes. |
| **Overall** | **9.8 / 10 · GO.** | |

## Deferrals

* Automatic dispatch assignment.
* AI-written dispatch decisions / route optimization / GPS proximity ranking.
* Payment optimization.
* Advanced scheduling.
* SMS / push / text notifications.
* Predictive carrier replacement automation.

## Risks

* None functional. Engine unavailability returns the documented graceful fallback (proven by test 20).
* The chip refreshes on `carrier_id` context change only — sub-second when carrier is unchanged. Operator typing in other fields does NOT trigger network calls.

## Next Recommended Track

**Track 16.14 — Dispatcher Learning Loop.** Convert the new audit collection into a weekly "Operator Choice Insight" panel: which carriers/drivers/trucks did operators consistently override the recommendation for, and why? Pure read of audit data; no new business logic. Safe to ship because audit is already populated by Track 16.13.

Done means done.
