# TRACK 16.14 — DISPATCHER LEARNING LOOP

**Status:** ✅ GO · merged · 40/40 new tests · 546/546 transport-track tests green.
**Date:** 2026-02-10
**Scope:** Convert the Track 16.13 recommendation audit collection into team-level operational learning. Strictly admin-only. No individual scorekeeping. No emails. No SMS. Zero dispatch behavior changes.

---

## Purpose

Answer the questions leadership actually has:

* How often are recommendations used?
* How often are eligible alternatives selected?
* What watch items appear most often?
* Which excluded-option reasons dominate?
* Where does the recommendation engine need tuning?
* Where do transportation records need cleanup?

…without grading dispatchers, ranking individuals, or framing anyone as a low performer.

## Team-Level Design

* Every metric is an aggregate. No `per-dispatcher`, `dispatcher_rank`, `leaderboard`, or individual-score field exists in the library or UI (proven by test 22).
* No performance-review framing in user-facing strings (proven by test 23).
* No emails / SMS / push (proven by tests 24–25).
* Non-punitive vocabulary only: `Opportunity / Pattern / Watch / Improve data quality`.

## Data Source

`transport_dispatch_recommendation_audit` (created by Track 16.13). The library reads only — never mutates audit rows, never writes new scoring rows, never recomputes recommendations (proven by tests 4 + 26).

Excluded-pattern aggregation is sourced from the canonical `transport_eligibility_state` rows that are already in non-dispatchable states — no new eligibility logic.

## Backend

`lib/transport_dispatch_learning.py` with six pure async builders + one audit recorder:

* `build_dispatch_learning_summary(db, *, start, end, days)` — top-line counts.
* `build_recommendation_adoption_trends(db, *, days)` — day-bucketed trend with adoption %.
* `build_common_alternative_reasons(db, *, days)` — notes attached to `non_recommended_selected`.
* `build_common_watch_items(db, *, days)` — most-common watch labels from generated payloads.
* `build_excluded_reason_patterns(db, *, days)` — most-common reason labels on non-dispatchable eligibility rows.
* `build_engine_tuning_signals(db, *, days)` — system-level Opportunity / Pattern / Improve-data-quality signals with underlying counts.
* `record_learning_view(db, ...)` — audit hook for view events.

Range guard: default 30 days, max 365 days, floor 1 day (proven by tests 39–40).

## API

```
GET /api/admin/transportation/intelligence/dispatch-learning
    ?days=30&start=ISO&end=ISO
```

* Admin-only via `require_admin_dep` (proven by test 7).
* GET-only (proven by test 6).
* Returns: `summary`, `adoption`, `alternative_reasons`, `watch_items`, `excluded_patterns`, `tuning_signals`, `notes`, `schema_version="16.14.0"`.
* Writes a `transport_dispatch_learning_viewed` audit row per view.

## UI

New tab inside `/admin/transportation/intelligence` — **Learning Loop** (`tx-intel-tab-learning`).

Sections:
* `tx-intel-learning-disclaimer` — "Team-level operational learning · no individual scorekeeping" (proven by test 35).
* `tx-intel-learning-summary` — six summary cards (generated / viewed / recommended selected / eligible alternative / ignored / unavailable).
* `tx-intel-learning-adoption` — day-bucketed trend list with adoption %.
* `tx-intel-learning-alt-reasons` — top 10 dispatcher-supplied notes when picking an alternative.
* `tx-intel-learning-watch` — top 15 watch labels appearing on generated recommendations.
* `tx-intel-learning-excluded` — top 15 reason labels for non-dispatchable entities.
* `tx-intel-learning-tuning` — system-level Opportunity / Pattern signals with counts.
* Window selector: 7 / 30 / 90 days.
* Empty state when no audit data exists (proven by test 20).

Reuses existing MASCI Intelligence styling — no visual drift.

## Audit

`db.transport_intelligence_audit` rows of kind `transport_dispatch_learning_viewed` (Track 16.12 collection, reused). Snapshot includes `range`, `counts`, viewer role, viewer id, schema version.

## RBAC

Admin only. Dispatch tokens cannot reach the endpoint — the existing Track 16.12 `require_admin_dep` gate is shared.

## Performance

* Single Mongo query per builder against the audit collection within the requested time window.
* Range capped at 365 days; default 30.
* All builders return safely on empty audit (proven by test 20).

## Tests

`backend/tests/test_track_16_14_dispatcher_learning_loop.py` · **40/40 pass.**

Coverage:
* Library structure + function surface (1–2).
* Read-only against business collections (4).
* API surface + GET-only + admin gating + default/max days (5–9).
* Schema version locked (10).
* Summary / adoption / alternative reasons / watch items / excluded patterns / tuning signals (11–15).
* Each tuning signal triggers correctly (16–19).
* Empty state, view audit (20–21).
* Hard guarantees: no per-dispatcher ranking, no performance vocab, no emails, no SMS, no scoring duplication, no assignment gate changes, no HR changes (22–28).
* UI tab + summary cards + adoption / watch / excluded / tuning sections + team-level disclaimer (29–35).
* No punitive vocabulary (36).
* Track 16.13 preserved + deployment gate wired (37–38).
* Range cap + floor (39–40).

Full transport-track regression: **546/546 passing** (Tracks 16.04 → 16.14). Backend lints clean. Frontend lints clean. Live endpoint returns 401 unauthenticated as expected.

## Six-Pillar Score

| Pillar      | Score | Notes |
|-------------|-------|-------|
| Powerful    | 9/10  | Converts audit data into actionable Opportunity/Pattern signals. |
| Simple      | 10/10 | One library, one endpoint, one UI tab. No new scheduler, no email, no SMS. |
| Beautiful   | 9/10  | Native MASCI Intelligence UI. Calm chips. Window selector. |
| Trusted     | 10/10 | Team-level only. Every signal has its source count. No black boxes. |
| Proven      | 10/10 | 40 new tests + 546 transport-track regression green. |
| Deployable  | 10/10 | Additive only · admin-only · read-only · no schema migration. |
| **Overall** | **9.7 / 10 · GO.** | |

## Deferrals

* Per-dispatcher weekly email.
* Per-dispatcher scorecards / performance-review tooling.
* Auto-tuning recommendation weights.
* GPS proximity ranking / payment optimization.
* Advanced dispatch scheduling.
* Predictive carrier replacement automation.

## Risks

None. All vocabulary, scope, and access guards are locked by regression tests. Library is purely additive.

## Next Recommended Track

**Track 16.15 — Operational Cleanup Companion.** Surface the top "Improve data quality" tuning signal as a one-click action list inside the Command Queue (e.g. "Targeting 'Insurance expires in 14 days' would unblock 8 entities"). Pure UX of existing data — no new business logic. Closes the loop: HR → Sync → Intelligence → Decision → Learning → Action.

Done means done.
