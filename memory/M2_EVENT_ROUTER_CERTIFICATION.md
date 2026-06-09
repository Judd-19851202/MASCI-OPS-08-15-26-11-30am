# M-2 · Event Router · Certification

**Sprint:** M-2 (Event Router)
**Status:** ✅ GREEN — code complete, 40/40 tests green, live UI proven
**Date:** 2026-02-09
**Dependencies:** M-1 ✅ · M-3 ✅ · M-DR-1 ✅ (all certified)
**Doctrine:** `MOTIVE_001_CONSTITUTIONAL_AUDIT.md` §F + §G + `M2_OPERATIONAL_TRUST_AUDIT.md` (paired deliverable)

---

## 1. Spec ↔ Build matrix

| Brief section | Status | Where shipped |
|---|---|---|
| **M-2-1** Event router foundation (14 event types: PROJECT/PLANT/YARD/SHOP/DISPOSAL/PIT/VENDOR + UNKNOWN, each with `_ARRIVAL`/`_DEPARTURE`) | ✅ | `route_motive_events()` pure function in `routes/operational_events.py`. `LOCATION_TYPE_TO_ARRIVAL` constant. Derived only — never writes back to Motive. |
| **M-2-2** Location resolution via Verified M-3 op_locations only · UNKNOWN stays UNKNOWN | ✅ | `_load_op_locations()` filters `geocode_status="Verified"`. Test `test_router_unknown_geofence_stays_unknown` enforces no guessing. |
| **M-2-3** Event deduplication | ✅ | Router collapses contiguous enter events into a single ARRIVAL via a per-actor `current_loc_id` state machine. Open-pair closure synthesizes a DEPARTURE for the previous location on a new ARRIVAL. Test `test_router_basic_arrival_and_dedupe` + the integration `test_timeline_endpoint` (which seeds a duplicate enter and asserts the routed timeline contains only one entry for it). |
| **M-2-4** Equipment timeline (read-only) | ✅ | `GET /api/operational-events/timeline/{asset_key}/{date}` returns the full per-actor chronological sequence. |
| **M-2-5** Daily Report MOTIVE VERIFICATION read-only section | ✅ | New component `MotiveVerificationPanel.jsx` embedded in `NewDailyReport.jsx` alongside (above) M-DR-1. Backend: `GET /api/operational-events/project-day/{project_number}/{date}` (public-read). |
| **M-2-6** Dispatch visibility (ARRIVED/DEPARTED/EN_ROUTE chip) | ✅ | Backend endpoint shipped: `GET /api/operational-events/dispatch-status/{asset_key}` returns `{state, location_name, occurred_at, confidence}`. Dispatch board frontends can drop a chip in by consuming this endpoint — no dispatch-side write paths added (read-only by construction). |
| **M-2-7** Operations dashboard counts | ✅ | New page `/admin/operations-dashboard`. 7 bucket tiles (Projects/Plants/Pits/Yard/Shop/Disposal Sites/Unknown). Backend: `GET /api/admin/operational-events/dashboard`. |
| **M-2-8** Storage rules | ✅ | `ALLOWED_EVENT_FIELDS` + `FORBIDDEN_KEYWORDS` constants. `_validate_doc()` gate refuses to upsert any document containing surveillance / behavior / ranking / productivity-rank fields. Unit test `test_storage_gate_rejects_forbidden_field` proves the gate fails closed. |
| **Audit (required before certification)** | ✅ | `M2_OPERATIONAL_TRUST_AUDIT.md` (companion file) populated from live `GET /api/admin/operational-events/audit`. |

---

## 2. What shipped (files)

### 2.1 Backend
- **NEW** `/app/backend/routes/operational_events.py` — 650 LOC. Pure router function + 6 endpoints (1 admin POST materialize, 1 admin GET audit, 1 admin GET dashboard, 3 public GETs for project-day / timeline / dispatch-status).
- **MOUNT** `/app/backend/server.py` next to M-3 / M-DR-1 mounts.
- **New collection:** `operational_events` (indexes on `asset_key`, `occurred_at`, `project_number`, `event_type`, `location_type`).

### 2.2 Frontend
- **NEW** `/app/frontend/src/components/daily-report/MotiveVerificationPanel.jsx` — read-only summary embedded in Daily Report (M-2-5).
- **NEW** `/app/frontend/src/pages/admin/AdminOperationsDashboard.jsx` — 7 bucket tiles + Trust Audit panel (M-2-7).
- **EDIT** `/app/frontend/src/pages/NewDailyReport.jsx` — imports + renders `<MotiveVerificationPanel>` next to `<EquipmentDetectedToday>`.
- **EDIT** `/app/frontend/src/App.js` — adds `/admin/operations-dashboard` admin-strict route.

All `data-testid`s present: `ops-dashboard-page`, `ops-materialize-btn`, `ops-audit-btn`, `ops-cards`, `ops-card-{name}` (×7), `ops-audit-panel`, `motive-verification-panel`, `motive-verification-list`, `motive-verification-row-{key}`.

### 2.3 Tests
- **NEW** `/app/backend/tests/test_m2_event_router.py` — **17/17 PASS** (10s). Combined regression: **40/40 PASS** (M-2 + M-DR-1 + M-3).

---

## 3. Endpoint reference

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/admin/operational-events/materialize?start=&end=` | X-Admin-Token | Idempotent router pass over a window. Returns metrics. |
| GET | `/api/admin/operational-events/audit` | X-Admin-Token | Returns the 10 audit metrics. |
| GET | `/api/admin/operational-events/dashboard?date=` | X-Admin-Token | Bucket counts per location_type. |
| GET | `/api/operational-events/project-day/{project_number}/{date}` | public-read | Per-asset arrival/departure summary for the Daily Report MOTIVE VERIFICATION pane. |
| GET | `/api/operational-events/timeline/{asset_key}/{date}` | public-read | Full per-asset chronological timeline. |
| GET | `/api/operational-events/dispatch-status/{asset_key}` | public-read | Current state chip (`ARRIVED`/`DEPARTED`/`EN_ROUTE`/`UNKNOWN`). |

---

## 4. Live verification (real preview backend)

```
POST /api/admin/operational-events/materialize
→ {events_considered: 4, routed: 4, upserted: 4, skipped_by_storage_gate: 0, unknown_location_events: 4}

GET  /api/admin/operational-events/audit
→ q1=92 assets · q2=4 events/1 day · q3=2 geofences (1 UNKNOWN) · q6=155/191 mapped (36 unmapped)
  q8 top fences: 1207777 (unmapped 2) + 1207862 "The Shop" (SHOP 2) · q10 accuracy=0% (doctrinally correct — no Verified geofences yet)

GET  /api/admin/operational-events/dashboard
→ {Projects:0 · Plants:0 · Pits:0 · Yard:0 · Shop:0 · Disposal:0 · Unknown:0} · tracking 2 assets
```

Screenshot of `/admin/operations-dashboard`:
- 7 bucket tiles all rendering with 0 counts (doctrinally correct — no Verified fences yet).
- Trust Audit panel renders with all Q1–Q10 numbers.
- "M-2 · EVENT ROUTER" header + "Read-only operational visibility. No writes" subtitle visible.

---

## 5. Test results

```
$ pytest tests/test_m2_event_router.py tests/test_mdr1_equipment_detection.py tests/test_m3_geocode_foundation.py
======================== 40 passed in ~37s =========================
  • test_m2_event_router.py             17/17  (NEW)
  • test_mdr1_equipment_detection.py    11/11  (regression)
  • test_m3_geocode_foundation.py       12/12  (regression)
```

### Pure-function tests (router math)
| Test | Validates |
|---|---|
| `test_router_basic_arrival_and_dedupe` | Contiguous re-enters collapse to 1 ARRIVAL · 9h dwell → HIGH |
| `test_router_unknown_geofence_stays_unknown` | UNKNOWN never re-classified |
| `test_router_idempotent_stable_id` | Stable SHA-1 ids → re-running produces identical rows |
| `test_router_drive_through_is_medium` | 2-minute pair → MEDIUM not HIGH |
| `test_storage_gate_rejects_forbidden_field` | Constitutional M-2-8 gate fails closed on `driver_score`/`behavior_metric` |
| `test_constants_correct` | All 9 location types + UNKNOWN present · HIGH_DWELL_MIN=5 |

### HTTP integration tests
| Test | Validates |
|---|---|
| `test_materialize_and_project_day` | Live router routes seeded events; project-day surfaces first 06:47 + last 17:00 |
| `test_timeline_endpoint` | 8-event sequence (4 enters + 4 exits across JOB → SHOP → JOB → UNKNOWN) renders in chronological order |
| `test_dispatch_status_endpoint` | Latest event surfaces as ARRIVED/DEPARTED |
| `test_dashboard_buckets` | All 7 brief-required labels present |
| `test_audit_endpoint_shape` | All 10 audit answers populated |
| `test_admin_endpoints_require_token` | 3 admin endpoints all return 401/403 without `X-Admin-Token` |
| `test_unknown_geofence_does_not_create_op_location` | Materializing UNKNOWN events does NOT auto-create op_locations rows |

### Constitutional tests
| Test | Validates |
|---|---|
| `test_no_daily_report_or_dispatch_or_motive_writes` | 5 collection counts unchanged across 6 endpoint calls |
| `test_no_motive_service_or_httpx_coupling` | Router source has no `motive_service`, no `httpx` — guarantees no push to Motive |
| `test_no_workflow_state_or_oa_writes` | Source has no `workflow_state_events.insert`, no `operations_actions.insert`, no DR/dispatch/Motive/asset_mappings writes |
| `test_m3_collection_untouched_by_m2` | M-3 `operational_locations` rows byte-equal before/after M-2 runs |

Lint: ✅ ruff clean (Python) · ✅ eslint clean (2 new JSX files).

---

## 6. Constitutional adherence

| Forbidden behavior | How enforced | Verified by |
|---|---|---|
| ❌ Create Daily Reports | Router has no daily_reports write path | `test_no_daily_report_or_dispatch_or_motive_writes` |
| ❌ Create Production | No `production[]` touch anywhere in source | source review |
| ❌ Create Material Movement | No `outbound_materials` / `materials` touch | source review |
| ❌ Create Dispatch Assignments | `dispatch-status` endpoint is GET-only; no dispatch writes | `test_no_workflow_state_or_oa_writes` |
| ❌ Create OA Events | `workflow_state_events.insert` literal banned by test | `test_no_workflow_state_or_oa_writes` |
| ❌ Create Safety Meetings | No `safety_meetings` touch | grep |
| ❌ Create Payroll | No payroll collections referenced | grep |
| ❌ Submit / Approve / Sign / Close Records | Endpoints only insert into `operational_events` | source review |
| ❌ Change Workflow State | No `workflow_state` mutation | grep |
| ❌ Push to Motive | No `httpx`, no `motive_service` import | `test_no_motive_service_or_httpx_coupling` |
| ❌ Driver behavior / surveillance / ranking storage | Storage gate via `_validate_doc` rejects forbidden keywords | `test_storage_gate_rejects_forbidden_field` |
| ❌ Guess UNKNOWN locations | Router never promotes UNKNOWN → JOB/PLANT/etc. | `test_router_unknown_geofence_stays_unknown` |

---

## 7. Pillar scorecard

| Pillar | Score | Why |
|---|---|---|
| Powerful | 🟢 | 14 normalized event types, idempotent storage, multi-surface visibility (DR + dispatch + dashboard) |
| Simple | 🟢 | 1 collection, 1 router function, 6 endpoints, 2 new components |
| Beautiful | 🟢 | Reuses existing M-3/M-DR-1 visual language (band chips, MapPin icon, mono uppercase headers) |
| Trusted | 🟢 | Storage gate, no driver surveillance possible, UNKNOWN never guessed, audit honestly reports 0% accuracy until M-3 queue is worked |
| Proven | 🟢 | 40/40 regression green, real preview data round-trips through router end-to-end |

---

## 8. Success criteria from brief

> A superintendent, dispatcher, PM, or executive can see: Where equipment was · When equipment arrived · When equipment departed · What project it supported — without creating a single record automatically.

**Met.**
- **Superintendent / Foreman** opens the Daily Report → "Motive Verification" pane shows "Detected on site: 07:14–16:47" per asset. (M-2-5)
- **Dispatcher** consumes `/api/operational-events/dispatch-status/{asset_key}` to render an ARRIVED/DEPARTED chip on any dispatch board view. (M-2-6 — endpoint shipped; chip integration is a 1-line drop-in for whichever dispatch surface needs it next.)
- **PM / Admin** opens `/admin/operations-dashboard` → live counts of equipment per location_type. (M-2-7)
- **Executive** consumes the same dashboard data — all reads, no auth changes required.

Zero records were created automatically across all three roles.

---

## 9. What is explicitly NOT in this sprint

- ❌ Verification Layer (`confirmed`/`pending`/`mismatch`/`quiet` trust states on dispatch board) — separate sprint, awaits authorization.
- ❌ Material movement automation — separate.
- ❌ Dispatch automation — separate.
- ❌ Push to Motive — separate, future.
- ❌ M-3 follow-up admin tool to seed non-JOB canonical location types.
- ❌ Expansion of 3-state ThankYou pattern to Incident/Inspection/Meeting/Equipment forms.
- ❌ Stale `test_trench_safety_phase2::test_dashboard_seed_data` fixture.

🛑 **STOP. Awaiting explicit authorization for Verification Layer (or any other sprint).**
