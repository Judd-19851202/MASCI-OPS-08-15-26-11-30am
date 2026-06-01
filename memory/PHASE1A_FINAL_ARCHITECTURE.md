# Phase 1A · Final Architecture

**Program:** OMEGA · Platform Completion Program · Phase 1A · Final Build Package
**Scope:** 6 workflows (OC-001 · OC-002 · OC-003 · OC-004 · OC-005 elevated · OC-007)
**Mode:** Design-only · companion to `PHASE1A_WORKFLOW_DESIGN.md`
**Date:** 2026-06-01

---

## 1 · Architecture overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React · existing pages)             │
│                                                                  │
│  ViewIncident.jsx   ─→ <LifecyclePanel workflow="incident"/>     │
│  ViewDailyReport.jsx ─→ <LifecyclePanel workflow="daily_report"/>│
│  HrPayrollVariance.jsx ─→ <LifecyclePanel workflow="payroll..."/>│
│  ViewQaqcInspection.jsx ─→ <LifecyclePanel workflow="qaqc..."/>  │
│  ViewSiteInspection.jsx ─→ <LifecyclePanel workflow="site..."/>  │
│  JhaList.jsx        ─→ <JhaAcknowledgePanel/>  (OC-005)          │
│  SafetyJhaAcks.jsx  ─→ NEW page · coverage dashboard (OC-005)    │
└──────────────────┬──────────────────────────────────────────────┘
                   │ REST API (additive endpoints)
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI)                          │
│                                                                  │
│  routes/workflow_transitions.py    NEW · universal transition    │
│  routes/jha_acknowledgements.py    NEW · OC-005 ledger           │
│                                                                  │
│  Existing routes augmented (additive endpoints only):            │
│    routes/safety.py             ─→ /incidents/:id/transition     │
│    routes/daily_reports.py      ─→ /daily-reports/:id/transition │
│    routes/qaqc.py               ─→ /qaqc-inspections/:id/...     │
│    routes/safety.py             ─→ /inspections/:id/transition   │
│    routes/hr_portal.py          ─→ /payroll-variance/.../trans   │
│                                                                  │
│  lib/workflow_state_machine.py     NEW · transition validator    │
│  lib/workflow_state_events.py      NEW · audit writer            │
│  lib/lifecycle_read_shim.py        NEW · canonicalize on read    │
└──────────────────┬──────────────────────────────────────────────┘
                   │ MongoDB
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                          DATABASE                                │
│                                                                  │
│  workflow_state_events  NEW collection · audit · 7y TTL          │
│  jha_acknowledgements   NEW collection · OC-005 ledger · 7y TTL  │
│                                                                  │
│  Existing collections augmented (additive fields only):          │
│    incidents              + lifecycle_state, closed_at, ...      │
│    daily_reports          + lifecycle_state, approved_at, ...    │
│    payroll_variance_batches + lifecycle_state, finalized_at, ... │
│    qaqc_inspections       + lifecycle_state · deficiencies[] →   │
│                              object array (read-shim)            │
│    inspections            + lifecycle_state · findings[] (new)   │
└─────────────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DOWNSTREAM CONSUMERS                          │
│                                                                  │
│  accountability_projection.py  ← read-shim emits canonical state │
│  command_center.py             ← read-shim emits canonical state │
│  project_health.py             ← read-shim emits canonical state │
│  operations_center.py          ← read-shim emits canonical state │
│                                                                  │
│  (existing labels preserved during Phase 1A · Phase 1B replaces) │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2 · New backend modules (Build stage manifest)

| Module | Purpose | LOC est |
|---|---|---|
| `lib/workflow_state_machine.py` | Allowed-transition map + transition validator + role-gate resolver | ~250 |
| `lib/workflow_state_events.py` | Audit-row writer with idempotency · indexes ensured at startup | ~180 |
| `lib/lifecycle_read_shim.py` | `get_lifecycle_state(workflow_type, doc, db)` helper returning canonical 5-state | ~150 |
| `routes/workflow_transitions.py` | Cross-cutting admin route `GET /api/admin/workflow-state-events` | ~120 |
| `routes/jha_acknowledgements.py` | OC-005 collection · 6 endpoints · coverage calc | ~350 |
| New: `routes/safety.py` extensions | `POST /incidents/:id/transition` + `GET .../state-events` | ~80 |
| New: `routes/daily_reports.py` extensions | same shape | ~80 |
| New: `routes/qaqc.py` extensions | inspection + deficiency transition | ~120 |
| New: `routes/safety.py` extensions | site inspection + finding transition | ~120 |
| New: `routes/hr_portal.py` extensions | payroll variance batch transition | ~80 |
| Migration: `server.py` startup hook | ensure indexes + backfill lifecycle_state = OPEN on missing | ~50 |
| **Total backend LOC** | | **~1,580** |

---

## 3 · New frontend modules (Build stage manifest)

| Component / Page | Purpose | LOC est |
|---|---|---|
| `components/LifecyclePanel.jsx` | NEW shared component · renders state pill + role-gated buttons + history drawer | ~280 |
| `components/JhaAcknowledgePanel.jsx` | OC-005 · signature-capture modal + verbal-attestation path | ~220 |
| `pages/SafetyJhaAcks.jsx` | OC-005 · coverage dashboard + per-JHA drill | ~250 |
| `pages/PublicJhaAck.jsx` | OC-005 · public QR-token submission flow | ~180 |
| `pages/ViewIncident.jsx` | + LifecyclePanel integration | ~30 |
| `pages/ViewDailyReport.jsx` | + LifecyclePanel + return-to-field input | ~50 |
| `pages/HrPayrollVariance.jsx` | + LifecyclePanel for batch · Finalize button | ~60 |
| `pages/ViewQaqcInspection.jsx` | + LifecyclePanel + per-deficiency action menu | ~100 |
| `pages/ViewSiteInspection.jsx` | + LifecyclePanel + per-finding action menu | ~100 |
| `pages/JhaList.jsx` | + Acknowledge button per row | ~40 |
| `pages/FieldLeadershipHub.jsx` | + JHA today-coverage badge on existing tile | ~30 |
| Routing in `App.js` | new routes (`/safety/jha-acknowledgements` · `/public/jha-ack/:token`) | ~10 |
| **Total frontend LOC** | | **~1,350** |

---

## 4 · Endpoint inventory (NEW endpoints only)

| # | Method | Path | Workflow | Auth |
|---|---|---|---|---|
| 1 | POST | `/api/incidents/{id}/transition` | OC-001 | Safety · Admin · Super-Admin |
| 2 | GET | `/api/incidents/{id}/state-events` | OC-001 | per-doc read auth |
| 3 | POST | `/api/daily-reports/{id}/transition` | OC-002 | PM (assigned) · Admin · Super-Admin |
| 4 | GET | `/api/daily-reports/{id}/state-events` | OC-002 | per-doc read auth |
| 5 | POST | `/api/qaqc-inspections/{id}/transition` | OC-003 | PM (assigned) · Admin · Super-Admin |
| 6 | POST | `/api/qaqc-inspections/{id}/deficiencies/{def_id}/transition` | OC-003 | PM/FL/Admin |
| 7 | GET | `/api/qaqc-inspections/{id}/state-events` | OC-003 | per-doc read auth |
| 8 | POST | `/api/inspections/{id}/transition` | OC-004 | Safety · Admin · Super-Admin |
| 9 | POST | `/api/inspections/{id}/findings/{finding_id}/transition` | OC-004 | Safety/PM/FL/Admin |
| 10 | GET | `/api/inspections/{id}/state-events` | OC-004 | per-doc read auth |
| 11 | POST | `/api/hr/payroll-variance/batches/{id}/transition` | OC-007 | HR · Admin · Super-Admin |
| 12 | GET | `/api/hr/payroll-variance/batches/{id}/state-events` | OC-007 | HR · Admin |
| 13 | POST | `/api/jhas/{jha_id}/acknowledgements` | OC-005 | FL · Safety · Admin · public-token |
| 14 | GET | `/api/jhas/{jha_id}/acknowledgements` | OC-005 | FL/Safety/PM/Admin |
| 15 | GET | `/api/jobs/{job_id}/jha-acknowledgements` | OC-005 | same |
| 16 | GET | `/api/admin/jha-acknowledgements` | OC-005 | Safety · Admin |
| 17 | DELETE | `/api/jhas/{jha_id}/acknowledgements/{ack_id}` | OC-005 | Safety · Admin · Super-Admin |
| 18 | GET | `/api/jha-acknowledgements/coverage` | OC-005 | Safety · Admin |
| 19 | GET | `/api/admin/workflow-state-events` | cross-cutting | Admin · Super-Admin |

19 new endpoints. All additive. Existing endpoints unchanged.

---

## 5 · Per-workflow architecture answers

### OC-001 Incidents
* **Owner:** Safety (close authority) · Filing officer (initiator)
* **States:** OPEN → IN_PROGRESS → {PENDING_REVIEW, PENDING_CLOSURE} → CLOSED
* **Closes via:** PENDING_REVIEW → CLOSED with attestation + (OSHA gate if applicable)
* **Reopens via:** CLOSED → IN_PROGRESS with `reason`
* **Audit:** `workflow_state_events` row per transition
* **Notifications:** none for Phase 1A (deferred)
* **CC impact:** hardcoded label strings replaced with `lifecycle_state` rendering (read-shim sets canonical)
* **Accountability impact:** `_status_for_incident` updated to prefer `lifecycle_state`

### OC-002 Daily Reports
* **Owner:** PM (assigned to job)
* **States:** OPEN → IN_PROGRESS → CLOSED (+ return-to-field OPEN path)
* **Closes via:** IN_PROGRESS → CLOSED with hours-attest checkbox + incident-link guard
* **Reopens via:** CLOSED → IN_PROGRESS with `reason`
* **Audit:** `workflow_state_events`
* **Notifications:** return-to-field notifies original submitter via `notifications` collection (kind=`dr_returned_to_field`)
* **CC impact:** JOBS-DR-MISSING rule now consumes `lifecycle_state != "CLOSED"` (preserves current behavior; clarifies intent)
* **Accountability impact:** new derivation path

### OC-003 QA/QC Inspections
* **Owner:** PM (assigned)
* **States:** (inspection) OPEN → IN_PROGRESS → PENDING_REVIEW → CLOSED · (per-deficiency) same
* **Closes via:** all deficiencies CLOSED → inspection PENDING_REVIEW → CLOSED
* **Reopens via:** CLOSED → IN_PROGRESS with `reason` (cascades to children optionally)
* **Audit:** `workflow_state_events` for both levels
* **Notifications:** when deficiency assigned (kind=`qaqc_def_assigned`)
* **CC impact:** new card eligibility (deferred to Phase 1B observability)
* **Accountability impact:** new source

### OC-004 Site Inspections
* **Owner:** Safety
* Identical to OC-003 structure with Safety-officer roles

### OC-005 JHA Acknowledgement Ledger
* **Owner:** Safety (compliance) · FL (operational responsibility for daily ack)
* **States:** NONE (immutable evidence rows)
* **Closes via:** no closure (each row is permanent OSHA evidence)
* **Reopens via:** n/a
* **Audit:** the rows themselves are the audit; deletion writes `audit_events`
* **Notifications:** 4h-after-job-start coverage gap notification + daily 18:00 batch
* **CC impact:** NEW rule `SAF-JHA-ACK-MISSING` (job-day with no ack by 10:00 local · severity Yellow)
* **Accountability impact:** NEW source `JHA_ACK_MISSING` (owner = PM of job)

### OC-007 Payroll Variance Batches
* **Owner:** HR (Sandy)
* **States:** OPEN → IN_PROGRESS → PENDING_REVIEW → CLOSED (with auto-transitions)
* **Closes via:** PENDING_REVIEW → CLOSED with attestation
* **Reopens via:** CLOSED → IN_PROGRESS with `reason`
* **Audit:** `workflow_state_events` + existing per-row decision audit
* **Notifications:** none for Phase 1A
* **CC impact:** new rule eligibility (deferred to Phase 1B)
* **Accountability impact:** new derivation

---

## 6 · Cross-cutting architecture decisions (recap from PHASE1A_WORKFLOW_DESIGN.md §6)

* **One audit collection** `workflow_state_events` for all 5 lifecycle workflows
* **Separate collection** `jha_acknowledgements` for OC-005 (different shape)
* **One transition contract** `POST /api/<workflow>/{id}/transition`
* **Read-shim helper** `get_lifecycle_state()` returns canonical 5-state during Phase 1B migration
* **Shared `<LifecyclePanel>` frontend component** to keep UX consistent
* **7-year TTL** on both new collections (OSHA + IRS retention aligned)
* **Idempotency** via compound unique index on `(workflow, doc_id, to_state, actor, occurred_at_minute)`

---

## 7 · OMEGA discipline

🟢 Design-only · architecture finalized · 19 new endpoints catalogued · 2 new collections specified · LOC estimate ~3,000 across backend + frontend.

🛑 Continue to `PHASE1A_DATABASE_IMPACT.md`.
