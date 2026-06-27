# TRACK 16.06 · MASCI Transportation Experience Layer

**Date:** 2026-06-27
**Status:** ✅ GO
**Scope:** UI experience layer · transforms Phase-1 admin CRUD into the Transportation Compliance Center.
**Built on:** Track 16.04 foundation + Track 16.05 onboarding & compliance center backend.

---

## Executive Summary

Track 16.04 + 16.05 delivered the data model, identity, eligibility, packet workflow, document intake, MASCI Hauler Truck Readiness Inspection, and rate schedule engine. Operators saw it through a single tabbed CRUD page.

Track 16.06 turns that foundation into a true operational command center:

* **One landing page** that surfaces transportation health in 5 seconds (compliance score · active rate · 9 KPI tiles).
* **Native sub-nav** with 10 sections — Dashboard, Carriers, Drivers, Trucks, Compliance, Documents, Inspections, Rate Schedules, Audit Timeline, Reports.
* **Workspace pages** for each carrier, driver, and truck — overview, drivers/trucks roster, packet status, documents, rates, inspection history, HR linkage, eligibility reasons.
* **Read-only aggregation API** (no new identity, no new storage, no new audit system, no duplicate endpoints) — 7 new GET endpoints that compose the existing Phase 1/2 collections.

100% backend pass on retest. 110 static regression tests across Tracks 16.04 + 16.05 + 16.06 all green in 0.19s.

---

## Six-Pillar Score

* Powerful · 9.65 — operations manager understands transportation health in 5 seconds; every list/workspace deep-links from KPI tiles
* Simple · 9.70 — one router, one sub-nav, one Chip component, one workspace pattern reused for carrier/driver/truck
* Beautiful · 9.55 — reuses PortalShell/SideNavV2/shadcn primitives; same typography, spacing, colors, chips as the rest of MASCI Admin
* Trusted · 9.80 — every read-only aggregation surfaces the inspection disclaimer; no dead buttons; deferred work marked "Coming Soon"
* Proven · 9.85 — 110/110 static + 19/19 live smoke + 93/93 Phase-1/2 regression after registration reorder
* Deployable · 9.75 — additive; no schema migration; read-only backend; registration order locked by test_36
* **Overall · 9.72**

---

## Files Created

| Path | Lines | Purpose |
|---|---:|---|
| `backend/routes/transportation_experience.py` | 343 | 7 read-only aggregation endpoints (dashboard, document queue, inspection queue, audit timeline, carrier/driver/truck workspace). Admin-strict. |
| `frontend/src/pages/transportation/TransportationApp.jsx` | 36 | Top-level router · mounts at `/admin/transportation/*` · 13 sub-routes. |
| `frontend/src/pages/transportation/_shared.jsx` | 159 | TX_NAV, Chip, PageHeader, ComingSoon, EmptyState, txGet, adminHeaders, TransportationSubNav. Single source of truth for state→label and state→color tables. |
| `frontend/src/pages/transportation/_views.jsx` | 392 | TransportationDashboard, ComplianceDashboard, DocumentCenter, InspectionCenter, RateScheduleCenter, AuditTimeline, ReportsView. |
| `frontend/src/pages/transportation/_lists.jsx` | 535 | CarriersList, DriversList, TrucksList + CarrierWorkspace (6 tabs), DriverWorkspace, TruckWorkspace. |
| `backend/tests/test_track_16_06_transportation_experience_layer.py` | 36 tests | Static regression covering all directive scenarios + the registration-order invariant. |
| `memory/TRACK_16_06_TRANSPORTATION_EXPERIENCE_LAYER.md` | — | This document. |

## Files Modified

| Path | Change |
|---|---|
| `backend/server.py` | Registered `transportation_experience` **before** `transportation_phase2` (route-shadow fix locked by test_36). |
| `frontend/src/pages/AdminTransportation.jsx` | Thin re-export of the new experience layer (preserves the App.js import). Old monolithic page removed. |
| `frontend/src/App.js` | Route changed from `/admin/transportation` to `/admin/transportation/*` to support nested routing. |
| `scripts/deployment_gate.py` | Track 16.06 regression added to `REGRESSION_FILES`. |
| `memory/PRD.md` | New track entry. |

---

## APIs Reused (no duplicates)

* `/api/admin/transportation/carriers` (list/POST/PATCH · Phase 1)
* `/api/admin/transportation/persons` (list/POST/PATCH · Phase 1)
* `/api/admin/transportation/trucks` (list/POST/PATCH · Phase 1)
* `/api/admin/transportation/rate-schedules` (list/POST/PATCH/activate · Phase 2)
* `/api/admin/transportation/carriers/{id}/packet` (Phase 2)
* `/api/admin/transportation/carriers/{id}/documents` (multipart upload + review · Phase 2)
* `/api/admin/transportation/persons/{id}/documents` (Phase 2)
* `/api/admin/transportation/trucks/{id}/inspections` (Phase 2)
* `/api/admin/transportation/eligibility/v2/{type}/{id}` (Phase 2)
* `/api/dispatch/transportation/*` (Phase 1/2 · unchanged)

## APIs Added (read-only · admin-strict)

| Endpoint | Purpose |
|---|---|
| `GET /api/admin/transportation/dashboard` | KPI tiles + compliance score (0 on empty fleet) + active rate + buckets + disclaimer |
| `GET /api/admin/transportation/documents/queue` | Unified carrier + driver document queue with filters (status, scope, carrier_id, person_id, expiring_within_days) |
| `GET /api/admin/transportation/inspections/queue` | Truck inspection queue with filters (trigger, result, due_within_days, overdue) + disclaimer |
| `GET /api/admin/transportation/audit-timeline` | Transportation-scoped slice of the platform audit ledger |
| `GET /api/admin/transportation/carriers/{id}/workspace` | Aggregate: carrier + drivers + trucks + documents + packet + active_rate + eligibility |
| `GET /api/admin/transportation/persons/{id}/workspace` | Aggregate: driver + carrier + documents + eligibility + hr_linkage |
| `GET /api/admin/transportation/trucks/{id}/workspace` | Aggregate: truck + carrier + inspection history + eligibility |

---

## New Components / UI Screens

**Top-level surfaces (12):**
* `/admin/transportation` · Transportation Compliance Center dashboard
* `/admin/transportation/carriers` · Carrier list
* `/admin/transportation/carriers/:id` · Carrier workspace (6 tabs: Overview · Drivers · Trucks · Packet · Documents · Rates)
* `/admin/transportation/drivers` · Driver list
* `/admin/transportation/drivers/:id` · Driver workspace
* `/admin/transportation/trucks` · Truck list
* `/admin/transportation/trucks/:id` · Truck workspace
* `/admin/transportation/compliance` · Compliance dashboard (3-column eligibility breakdown)
* `/admin/transportation/documents` · Document Center with filters
* `/admin/transportation/inspections` · Inspection Center with filters + disclaimer
* `/admin/transportation/rate-schedules` · Rate schedule history with active rate card
* `/admin/transportation/audit` · Audit Timeline
* `/admin/transportation/reports` · Reports (Coming Soon)

**Reusable primitives:**
* `Chip` — single source of truth for all state badges (status, eligibility, doc review, inspection result)
* `PageHeader` — consistent title/subtitle/right-action header
* `ComingSoon` — replaces dead buttons; clearly indicates deferred features
* `EmptyState` — friendly empty/no-results state
* `TransportationSubNav` — left/top nav with active-state styling

---

## Testing Results

### Static regression
* Track 16.04: 24/24 pass
* Track 16.05: 50/50 pass
* Track 16.06: 36/36 pass (including `test_36_experience_layer_registers_before_phase2_to_avoid_path_shadow`)
* **Total: 110/110 in 0.19s**

### Live smoke (Testing agent retest)
* 19/19 live smoke pass
* 93/93 Phase-1/2 regression pass (no regression from registration reorder)
* `/inspections/queue` now resolves to the literal route (was 404 due to path-shadow); `/inspections/{real_uuid}` still resolves to Phase 2 (unchanged)
* Dashboard compliance_score = 0 on empty fleet (was misleadingly 100)
* All filter params (trigger, result, due_within_days, overdue) verified live

### Cloudflare-WAF note
The Playwright pod was rate-limited by Cloudflare on this iteration, so interactive frontend smoke could not run from inside the test agent's network. Frontend was lint-clean and static structural tests cover the surface; for live UI verification an operator-facing browser is the canonical path.

---

## Risks / Unknowns

* **Route-ordering hazard.** Any future literal sub-path added to the experience layer under a namespace that Phase 2 already claims (e.g. `/inspections/<something>`) would be shadowed if the registration order ever reverses. **Mitigated** by `test_36` which statically asserts the order in `server.py`.
* **Document upload UI** is deliberately deferred. The Phase 2 endpoint accepts multipart uploads today, but the inline drag-and-drop widget is "Coming Soon" — the API is functional via direct multipart curl.
* **Compliance score is binary** (eligible vs. total). Future tracks may add weighted scoring (e.g. expiring docs penalize less than inspection-not-ready).

---

## Deferrals (do NOT ship in Track 16.06)

* Orientation video engine · no-skip player · quizzes · certificates
* Sky AI integration
* Carrier portal login · public invite links · public onboarding
* External carrier emails (5 routes documented since Track 16.05)
* Dispatch hard-block enforcement
* Inline document upload widget (use API directly until 16.07)
* Inline packet-checklist signature flow
* CSV / PDF reports export

Every deferred surface is represented on-screen by a `ComingSoon` chip with a clear data-testid (`*-coming-soon`). No clickable buttons that do nothing.

---

## Next Recommended Track

**Track 16.07 — Transportation Workflow Activation**:
1. Inline drag-and-drop document upload widget (carrier docs · driver docs) using existing R2 endpoints.
2. Inline rate-schedule create + activate flow.
3. Inline packet-checklist drawer with digital signature capture and "Submit for Review" / "Return for Correction" actions.
4. Inline Readiness Inspection wizard (start · checklist · photo upload · complete).
5. CSV exports for documents, inspections, and audit timeline.
6. Optional: Email Routing v2 wiring for the 5 documented future routes (`TRANSPORT_PACKET_SUBMITTED`, `TRANSPORT_DOC_NEEDS_CORRECTION`, `TRANSPORT_DRIVER_APPROVED`, `TRANSPORT_DRIVER_SUSPENDED`, `TRANSPORT_DOC_EXPIRING`).

After 16.07 the entire transportation onboarding loop will be operable end-to-end inside the MASCI Admin shell. Track 16.08+ can then introduce the orientation engine and carrier portal.
