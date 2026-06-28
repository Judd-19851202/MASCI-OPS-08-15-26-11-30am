# TRACK 16.16 · Operations × Transportation Integration Layer

**Date:** 2026-02-10
**Status:** ✅ GO — full certification pass
**Type:** Thin operational integration layer (additive only)

---

## Mission

Surface Transportation intelligence inside existing Operations
workflows so Operations personnel never need to leave their normal
workspace to know whether Transportation is ready.

**Doctrine**

* Operations CONSUMES Transportation.
* Transportation never consumes Operations.
* Transportation remains the system of record.
* Operations displays read-only operational awareness.
* No duplicated business logic. No duplicated databases. No
  duplicated dashboards. No new scoring. No new audit kinds. No
  new emails. No new schedulers.

---

## Verdict

✅ **GO** — 15/15 new regression tests · 7/7 live RBAC + envelope +
performance tests · 134/134 combined Track 16.12 + 16.15 + 16.15A +
16.16 tests green. Endpoint cold latency **723 ms** (well under the
3 s gate). RBAC consistent across admin/pm/dispatch portal tokens.
Route is strictly read-only (zero write ops).

---

## What shipped

### Backend (one thin consumer endpoint)

* **`GET /api/operations/transportation/readiness`** —
  `/app/backend/routes/operations_transportation_integration.py`.
  Cross-portal read (`make_require_any_portal_token` — same gate as
  `/api/operations/events`). Returns a flat envelope assembled
  **only** from existing engines:

  * Count-based eligibility bands (mirrors Track 16.06 compliance
    score philosophy — `eligible / total`).
  * Phase-2 dashboard counters reused via inline collection queries
    (`transport_eligibility_state`, `carrier_documents`,
    `driver_documents`, `transport_persons`, `carriers`).
  * `transport_action_items` count for cleanup awareness.
  * `transportation_dashboard_hr_health()` for HR ↔ Transportation
    health.
  * Calm risk distillation that stays silent when fleet is healthy.

  Performance discipline: **does NOT** invoke
  `build_operational_health` or `build_cleanup_signals` — those
  heavy scans continue to power the Intelligence Center / Cleanup
  Companion. Operations consumers see materialized action counts
  instead.

### Frontend (four read-only awareness components, one module)

`/app/frontend/src/components/operations_transportation_integration.jsx`:

1. **`TransportationReadinessCard`** → 6-tile read-only summary
   with band chip, drivers/trucks/carriers/risks/cleanup/dispatch
   tiles, "View Transportation →" CTA.
2. **`TransportationRiskBanner`** → silent when no risks; renders
   only when ≥1 risk (blocked dispatch · cleanup `action_required`
   · HR mismatch · upcoming expirations).
3. **`OperationsTransportationHealthWidget`** → 4-tile compact
   widget (Blocked Dispatch · Pending Reviews · Expiring 30d ·
   Action Items) with band chip + Open Transportation link.
4. **`TransportationCloseoutAwareness`** → "Transportation
   Complete" calm badge OR unresolved-items list at the bottom of
   the project workspace.

Shared `useTransportationReadiness` hook with a 30 s in-memory
cache coalesces parallel fetches (three components on
`PmProjectDetail` share one request).

### Mounts (additive, no surface redesigned)

| Page | Mounted components | Anchor |
|---|---|---|
| `/app/frontend/src/pages/PmProjectDetail.jsx` | `TransportationRiskBanner` + `TransportationReadinessCard` (wrapper testid `pm-project-tx-integration`); `TransportationCloseoutAwareness` (wrapper testid `pm-project-tx-closeout`) | Right below `OperationalTimelineSidecar`; closeout below `TrenchSafetyOnProjectPanel` |
| `/app/frontend/src/pages/OperationsCenterCommand.jsx` | `OperationsTransportationHealthWidget` | Right after L2 Project Health section |
| `/app/frontend/src/pages/PmCommandCenter.jsx` | `OperationsTransportationHealthWidget` | Top of Overview tab content |

### Tests + Gate

* `/app/backend/tests/test_track_16_16_operations_transportation_integration.py`
  — 15 regression tests (route exists + cross-portal RBAC + no new
  scoring/cleanup engines + read-only contract + envelope shape +
  risks silence + band thresholds + frontend coverage + endpoint
  reuse + closeout shape + gate wiring + banner-null guarantee).
* `/app/scripts/deployment_gate.py` — wired in as the 23rd
  transport-track regression file.

---

## Operations Timeline Integration

The existing `OperationalTimelineSidecar` consumes
`GET /api/timeline?project_id=...` which is project-scoped via the
existing audit-events plumbing. Transportation lifecycle events
that carry a `project_number` (dispatch overrides, dispatch
acknowledgements) **already** flow into the timeline through the
existing Track 16.04 / 16.13 audit writers. **No new timeline
code was needed for this track** — verified by inspection.

---

## Project Closeout Awareness

No dedicated project-closeout surface exists for whole projects
today; the project workspace itself is the natural anchor. The
`TransportationCloseoutAwareness` component sits at the bottom of
`PmProjectDetail` and either:

* Renders a calm emerald *"Transportation Complete · No unresolved
  Transportation issues."* badge, **or**
* Renders an amber list of unresolved items
  (blocked dispatches · pending reviews · documents awaiting
  review · open action items · upcoming expirations).

---

## Hard guarantees (locked in regression)

1. **No new backend collections.** Route never writes (locked by
   `test_05_route_is_read_only`).
2. **No new scoring functions.** `build_operational_health` /
   `build_executive_dashboard` / `build_cleanup_signals` never
   called from this hot path (locked by
   `test_04_composes_existing_engines`).
3. **No new audit kinds.** Endpoint is pure read.
4. **Cross-portal read RBAC.** Verified live: admin=200, pm=200,
   dispatch=200, no-auth=401.
5. **Risk banner SILENT when healthy.** Locked by
   `test_07_risks_silent_when_healthy` and a source-level regex
   guard (`test_15_banner_silent_when_no_risks`).
6. **Cleanup awareness via materialized action items** — not via
   the heavy 7 s signal scan. Locked by an explicit forbidden
   marker in `test_04`.
7. **All four frontend components defined + mounted** in the three
   target pages with the required data-testid coverage
   (`test_10` / `test_11` / `test_12` / `test_13`).
8. **Gate wired** (`test_14`).

---

## Live verification (preview)

| Check | Evidence |
|---|---|
| Backend endpoint cross-portal | admin=200, pm=200, dispatch=200, no-auth=401 |
| Backend cold latency | **723 ms** (well under 3 s gate) |
| OC widget renders | band=`RED · 25.3` · Blocked Dispatch=71 · Pending=22 · Expiring 30d=0 · Action Items=89 · link=`/admin/transportation` |
| PmProjectDetail readiness card | band=`RED · 25.3` · drivers/trucks/carriers/risks/cleanup/dispatch tiles all present |
| PmProjectDetail risk banner | rendered (71 blocked dispatches → action_required) |
| PmProjectDetail closeout | `ops-tx-closeout-unresolved` rendered (multiple unresolved items on preview DB) |
| 15/15 new tests | `pytest tests/test_track_16_16_*` → 15 passed |
| 134/134 combined transport-track tests | green |

---

## Files changed / added

| File | Change |
|---|---|
| `/app/backend/routes/operations_transportation_integration.py` | NEW (~270 LOC) |
| `/app/backend/server.py` | +14 lines (router registration after Track 16.13) |
| `/app/frontend/src/components/operations_transportation_integration.jsx` | NEW (~410 LOC) |
| `/app/frontend/src/pages/PmProjectDetail.jsx` | +18 lines (3 mounts) |
| `/app/frontend/src/pages/OperationsCenterCommand.jsx` | +6 lines (1 mount) |
| `/app/frontend/src/pages/PmCommandCenter.jsx` | +6 lines (1 mount) |
| `/app/backend/tests/test_track_16_16_operations_transportation_integration.py` | NEW · 15 tests |
| `/app/scripts/deployment_gate.py` | +1 line |

No backend collection, audit kind, or scoring function touched.

---

## Deferrals (P2)

* Per-project Transportation filtering (carriers/drivers/trucks are
  fleet-wide today — the readiness card is intentionally a
  fleet-level mirror; per-job slicing would require a new
  project→carrier linkage which is out of scope).
* Inline drill-down from the closeout list (each row links to the
  Transportation workspace via the existing CTA; a deeper modal
  would duplicate the Cleanup Companion).
* Native widget on the master Operations Dashboard mobile/iPad
  layouts (the widget is responsive — grid collapses to 2 cols on
  small screens — but a dedicated mobile chrome is a future polish).

---

## Next recommended track

Wire the readiness widget testids into the Track 15.86 continuous
browser smoke gate so regressions on the Operations ↔
Transportation bridge are caught at deploy time.
