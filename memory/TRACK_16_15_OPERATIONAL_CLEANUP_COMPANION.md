# TRACK 16.15 — OPERATIONAL CLEANUP COMPANION

**Status:** ✅ GO · merged · 40/40 new tests · 578/578 transport-track tests green.
**Date:** 2026-02-10
**Scope:** Turn the highest-value Track 16.12 intelligence + Track 16.14 learning signals into focused, source-counted cleanup action lists. Read-only against source records; only `transport_action_items` are created.

---

## Purpose

Close the operator loop: HR → Sync → Intelligence → Decision Surface → Learning Loop → **Action**. Operators see *what* needs cleanup, *why*, *which records*, and click once to create work items in the existing Command Queue.

## Cleanup Signals (12)

Each entry maps to an existing data source — no new scoring, no duplicate intelligence.

| Signal key                  | Source                                | Severity         |
|-----------------------------|---------------------------------------|------------------|
| `insurance_expiring_soon`   | intelligence (driver documents)       | action_required  |
| `inspection_overdue`        | intelligence (truck inspections)      | action_required  |
| `orientation_expiring`      | intelligence (transport certificates) | watch            |
| `orientation_incomplete`    | intelligence (transport persons)      | action_required  |
| `missing_driver_docs`       | intelligence (driver documents)       | action_required  |
| `packet_needs_correction`   | intelligence (carrier packets)        | action_required  |
| `hr_sync_mismatch`          | sync monitor (HR projection)          | action_required  |
| `route_needs_configuration` | automation (email routes)             | watch            |
| `truck_readiness_gap`       | intelligence (truck eligibility)      | action_required  |
| `carrier_document_gap`      | intelligence (carrier eligibility)    | watch            |
| `repeated_watch_item`       | dispatcher learning (watch items)     | watch            |
| `frequent_excluded_reason`  | dispatcher learning (excluded labels) | watch            |

Each signal carries `affected_count`, `source_count` (1:1 with affected entities), `recommended_action`, and a `schema_version` stamp of `16.15.0`.

## Affected Records

Detail rows include `entity_type`, `entity_id`, `display_name`, `current_state`, `reason`, `due_date`, `severity`, `direct_link`, `existing_action_item_id`, `action_status`, `last_activity_at` — only human labels in default UI.

## Action Materialization

`materialize_cleanup_actions(db, signal_key, ...)` reuses `transport_action_items` with:
- `source = "intelligence_cleanup"`
- `related_event_key = "cleanup::<signal_key>::<entity_id>"` (idempotent dedupe)
- `related_signal_key` stamped for traceability
- `status = "open"`, `assigned_role = "transportation_admin"`
- Audit row `transport_cleanup_actions_materialized` written

NEVER mutates source compliance records (proven by test 13).

## Command Queue Integration

Cleanup actions appear in the existing Morning Command Queue via the same `transport_action_items` collection — no new action queue, no new schema. Action types:

```
cleanup_insurance_expiring · cleanup_inspection_overdue · cleanup_orientation_expiring
· cleanup_orientation_incomplete · cleanup_document_gap · cleanup_packet_needs_correction
· cleanup_hr_sync_mismatch · cleanup_route_needs_configuration · cleanup_truck_readiness_gap
· cleanup_carrier_document_gap · cleanup_repeated_watch_item · cleanup_frequent_excluded_reason
```

## API

```
GET  /api/admin/transportation/intelligence/cleanup-signals
GET  /api/admin/transportation/intelligence/cleanup-signals/{signal_key}
POST /api/admin/transportation/intelligence/cleanup-signals/{signal_key}/materialize-actions
```

All three endpoints **admin-only** (`require_admin_dep`). The single POST writes only to `transport_action_items` — no source mutation. Range `days` capped at 365.

## UI

* New tab in `/admin/transportation/intelligence` — **Cleanup Companion** (`tx-intel-tab-cleanup`).
* `tx-intel-cleanup-top-card` — top signal card with title, affected count, severity, recommended action, "View affected records" button.
* `tx-intel-cleanup-list` — grid of all open signals with severity chips.
* `tx-intel-cleanup-affected-drawer` — right-side drawer showing affected records, action status annotations, recommended action, and a single "**Create cleanup actions**" button (`tx-intel-cleanup-materialize-btn`).
* `tx-intel-cleanup-materialized-result` — confirmation banner: created · reused · skipped duplicates.
* Empty state when no signals detected.
* Native MASCI Intelligence styling — no visual drift.

## Audit

`transport_intelligence_audit` rows added (Track 16.12 collection reused):
* `transport_cleanup_signal_viewed`
* `transport_cleanup_detail_viewed`
* `transport_cleanup_actions_materialized`

Every audit row carries `schema_version="16.15.0"` and `subject_id=signal_key`.

## RBAC

Admin-only. Dispatch users do not see this surface in this track. Materialization route is gated by the same admin dep — no token elevation paths.

## Performance

* Default 30 days, capped at 365.
* Each signal loader is bounded (`to_list(2000)`).
* Graceful empty state when source intelligence is unavailable.
* No new scheduler; signals are computed on demand.

## Tests

`backend/tests/test_track_16_15_operational_cleanup_companion.py` · **40/40 pass.**

Coverage:
* Library structure + public function surface (1–4).
* No new scoring functions; reads existing collections + learning builders (5–6).
* Schema version locked (7).
* Signal output includes source_count + recommended_action (8–9).
* Detail records include direct_link (10).
* Materialize creates action items, dedupes by event_key, never mutates source records (11–13).
* Source = `intelligence_cleanup`; signal key stamped (14).
* Audit on materialize / signal view / detail view (15–17).
* API endpoints + admin-gated + no dispatch token path on cleanup block (18–23).
* UI tab + top card + affected drawer + materialize button + empty state (24–28).
* Uses existing transport_action_items schema fields (29).
* No emails / SMS / push / punitive labels / dispatch behavior / HR changes (30–34).
* Track 16.14 preserved + deployment gate wired (35–36).
* Multiple signals surfaced from different sources (37).
* Unknown signal returns ok=false (38).
* Range cap honoured (39).
* hr_sync_mismatch picks up needs_correction projections (40).

Full transport-track regression: **578/578 passing** (Tracks 16.04 → 16.15). Backend lints clean. Frontend lints clean. Live endpoint returns 401 unauthenticated as expected.

## Six-Pillar Score

| Pillar      | Score | Notes |
|-------------|-------|-------|
| Powerful    | 10/10 | Closes the operator loop — insight becomes action with one click. |
| Simple      | 10/10 | One lib · three endpoints · one UI tab · zero new schedulers. |
| Beautiful   | 9/10  | Native Intelligence styling; calm amber/rose chips; minimalist drawer. |
| Trusted     | 10/10 | Source-counted, audit-stamped, idempotent. No source mutation. |
| Proven      | 10/10 | 40 new tests + 578 transport-track regression green. |
| Deployable  | 10/10 | Additive only · admin-only · no schema migration · no removed routes. |
| **Overall** | **9.8 / 10 · GO.** | |

## Deferrals

* Automatic source-record remediation.
* Auto-email from cleanup signals.
* Per-dispatcher feedback.
* Predictive carrier replacement.
* Payment optimization / GPS proximity ranking / advanced scheduling.

## Risks

None. The single POST endpoint writes only to `transport_action_items` (existing collection, existing schema) and is admin-gated. All other writes are forbidden by regression tests.

## Next Recommended Track

**Track 16.16 — Cleanup Action Lifecycle Surface.** Surface created cleanup actions as a discoverable filter inside the existing Command Queue (e.g., "Filter → Source: intelligence_cleanup") with one-click resolution → audit row → recompute affected signal counts. Pure UX of existing data; zero new business logic.

Done means done.
