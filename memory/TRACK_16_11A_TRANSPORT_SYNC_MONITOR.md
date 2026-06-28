# TRACK 16.11A — HR VISIBILITY + TRANSPORTATION CONSISTENCY ENGINE

**Status:** ✅ GO — merged · 45/45 new regression tests · 407 transport-track tests green.
**Date:** 2026-02-10
**Scope:** Final hardening pass before Track 16.12 (Intelligence). HR-safe, additive only — HR remains the absolute source of truth.

---

## Mission

Connect HR and Transportation by giving HR immediate visibility into Transportation readiness while continuously proving the two systems remain synchronized.

When complete:

* HR remains authoritative.
* Transportation always reflects HR.
* Leadership sees synchronization health at a glance.
* Dispatch never operates on stale HR data.
* Every mismatch becomes an action item before it becomes a problem.

## What shipped

### Backend

* `lib/transport_sync_monitor.py` — read-only consistency engine:
  - `classify_mismatch(...)` — pure classifier covering 10+ mismatch codes (severity-tagged).
  - `scan_hr_transport_consistency(db)` — full HR ↔ Transportation reconciliation, persists a run summary into `transport_hr_sync_runs`, emits audit + action items, never mutates HR.
  - `derive_employee_transport_status(db, employee_id)` — single-employee snapshot for the HR profile chip.
  - `hr_dashboard_transport_readiness(db)` — KPI bag for the HR Hub widget.
  - `transportation_dashboard_hr_health(db)` — KPI bag for the Transportation Dashboard / Command Queue widgets.
* `routes/transportation_automation.py`:
  - New **read-only** GET endpoints:
    - `/api/admin/transportation/hr-sync`
    - `/api/admin/transportation/hr-sync/report` (supports `?run=true&stale_days=N`)
    - `/api/admin/hr/transportation-status?employee_id=...`
    - `/api/admin/hr/transportation-readiness`
  - Existing `transport_automation_scheduler_loop` extended to also fire `scan_hr_transport_consistency` once per 24h. **No new scheduler created.**
  - New `TRANSPORT_HR_SYNC_MONITOR_ALERT` route key bootstrapped `internal_only=True`, `pilot_safe=True`, `enabled=False`.

### Frontend

* `pages/HrHub.jsx` — **Transportation Readiness** widget (test ID `hr-transportation-readiness-widget`) with 5 KPI tiles (eligible / pending review / suspended / needs correction / not dispatchable) + link to Transportation. Read-only.
* `pages/HrEmployees.jsx` — new **Transportation** tab in the Employee Drawer (`hremp-tab-transportation`). Renders `TransportationStatusPanel` — chip + identity rows + sync timestamps + active override + reasons. Strictly read-only; HR UI never writes Transportation.
* `pages/transportation/_views.jsx` — TransportationDashboard now renders `HrHealthWidget` (`tx-dashboard-hr-health`) showing health chip + mismatches + dispatch risks + sync ages.
* `pages/transportation/_command_queue.jsx` — Automation Health tab now renders `HrSyncHealthCard` (`tx-cq-hr-sync-card`) with run-on-demand "View synchronization report" button + mismatch list.

### Tests

* `backend/tests/test_track_16_11A_transport_sync_monitor.py` — **45 tests**, covering:
  - Pure classifier (cases 2–8): linkage / projection / stale / termination / leave / role / unknown / failure mismatches.
  - End-to-end scanner (9–15): healthy / mismatch detection / idempotent action items / no HR mutation / audit row / run-summary persistence.
  - HR profile chip (16–19): missing / not-linked / linked / read-only contract.
  - Dashboard aggregations (20–21).
  - Severity classifier coverage (22).
  - Recommended actions (23).
  - Duplicate linkage + HR active no linkage (24–25).
  - Projection failure detection (26).
  - API surface (27–28): 4 GET endpoints, zero writes.
  - Scheduler integration (29–30): scan runs inside existing automation loop, no new scheduler.
  - Route-key bootstrap (31–32) preserves 16.10A invariants.
  - UI contracts (33–36): widgets exist with expected test IDs.
  - HR UI read-only (37).
  - No SMS / push (38).
  - No punitive vocabulary (39).
  - Deployment gate wiring (40–41–45).
  - HR routes preserved (42).
  - No destructive Mongo ops (43).
  - Action items keyed by `related_event_key` (44).
* Wired into `scripts/deployment_gate.py`.

## HR-Safe Guarantees

* HR data models, routes, vocabulary, indexes — **untouched** in this track.
* No new collection holds HR identity. The monitor walks `db.employees` (HR's collection) read-only.
* No transport_person is auto-created or auto-deleted. Operators link explicitly via Transportation admin (Track 16.04+ flow).
* All sync work is wrapped in try/except — HR write paths cannot regress.
* Daily scan runs inside the **existing** Track 16.10 automation loop. No duplicate scheduler.

## Action Queue

The monitor emits idempotent rows in `transport_action_items` (deduped by `related_event_key`) for:

| Code                   | Severity  |
|------------------------|-----------|
| termination_mismatch   | critical  |
| dispatch_conflict      | critical  |
| duplicate_linkage      | critical  |
| duplicate_employee     | critical  |
| leave_mismatch         | block     |
| role_mismatch          | block     |
| projection_failed      | block     |
| linkage_missing        | block     |
| hr_status_unknown      | block     |
| projection_stale       | warn      |
| projection_missing     | warn      |
| hr_active_no_linkage   | info      |

## Audit

* `transport_hr_sync_scanner_completed` — per-run audit row with health + counts.
* `transport_hr_sync_runs` collection — full run history with mismatches sample (top 50).
* Per-mismatch audit context surfaces in `audit_events` via Track 16.11 sync helper.

## Email / Notifications

* `TRANSPORT_HR_SYNC_MONITOR_ALERT` route key bootstrapped `internal_only=True`, `enabled=False`. No external send is wired.
* No SMS / Twilio / push references.

## Six-Pillar Score

| Pillar      | Score | Notes |
|-------------|-------|-------|
| Powerful    | 9/10  | Continuous HR ↔ Transportation reconciliation with severity-graded mismatches. |
| Simple      | 10/10 | Single new module + 4 new GET endpoints + 4 UI mounts. No new scheduler. |
| Beautiful   | 9/10  | Reuses PortalShell + HR/Tx chips; calm tile palette; zero design drift. |
| Trusted     | 10/10 | Every scan + mismatch + action item audited. HR untouchable. |
| Proven      | 10/10 | 45 new tests · 407 transport-track tests green · all 16.04–16.10A preserved. |
| Deployable  | 10/10 | Additive only. No schema migration. No removed/renamed routes. |
| **Overall** | **9.7 / 10 · GO.** | |

## Risks / Deferrals

* Stale-sync threshold is a single env var (`TRANSPORT_HR_SYNC_STALE_DAYS`, default 7). Per-route thresholds deferred.
* Auto-resync on detected stale projections is intentionally **not** wired — the human (Transportation admin) closes the loop. The action item points to the right path.
* Predictive analytics, carrier scorecards, payment calculator → Track 16.12+ (P2).

## Next Recommended Track

**Track 16.12 — Transportation Intelligence.** With HR ↔ Transportation now provably synchronized, the platform can layer predictive carrier scorecards / driver risk indices without first having to babysit data hygiene.
