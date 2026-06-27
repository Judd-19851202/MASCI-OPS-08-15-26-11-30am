# TRACK 16.05 · MASCI Transportation Onboarding & Compliance Center · Phase 2

**Date:** 2026-06-27
**Status:** ✅ GO
**Scope:** rate schedules · carrier+driver documents (R2-backed) · packet workflow · MASCI Hauler Truck Readiness Inspection · dashboard endpoints.
**Built on:** Track 16.04 foundation (`carriers`, `transport_persons`, `transport_trucks`, `transport_eligibility_state`).

---

## Mission

Convert the existing MASCI hauler packet into a native digital workflow. Preserve every current MASCI requirement verbatim. Add modern compliance gates (Clearinghouse, CDL/medical, MASCI Hauler Truck Readiness Inspection) and wire them into Phase-1 eligibility. **No orientation engine yet. No public invite. No carrier portal. No external carrier emails. No dispatch hard-block enforcement.** All explicitly deferred to Track 16.06+.

---

## What shipped

### Backend
| Path | Purpose |
|---|---|
| `lib/transport_phase2.py` | Constants (rate text, document types, packet statuses, inspection checklist, disclaimer) + `bootstrap_track_16_05(db)` idempotent helper + result derivation. |
| `lib/transport_eligibility.py` | Extended Phase-2 truth table — packet status · rate ack · doc rollup · inspection result · driver PPE. |
| `routes/transportation_phase2.py` | All Phase 2 endpoints. Self-contained admin+dispatch gate (canonical per-user admin token validator). |
| `server.py` | `register_transportation_phase2_routes` + `@app.on_event("startup")` calling `bootstrap_track_16_05(db)`. |

### Frontend
The existing `/admin/transportation` page (Track 16.04) is preserved unchanged in Phase 2. Phase 2 endpoints are available for the next UI track to surface (rate-schedule banner, packet-status checklist drawer, document upload widget, inspection wizard). No fake buttons added — every action surface ships when its UI does.

### Tests
| Path | Purpose |
|---|---|
| `backend/tests/test_track_16_05_transportation_onboarding_compliance_center.py` | 50 regression tests · all green in 0.15 s. Covers 47 directive scenarios + 3 bonus checks. |
| `scripts/deployment_gate.py` | Wired into `REGRESSION_FILES`. |

---

## Rate schedule

* Default seeded by `bootstrap_track_16_05`: $85.00/hour USD · version 1 · active. Idempotent (does not overwrite existing active row).
* Versioned. Admin creates a new row (status=draft), then `/activate` retires the prior active row and activates the new one. Retired rows are read-only.
* Each `transport_packet_submissions` row records the `rate_schedule_id` that was active at packet creation. Future rate changes never rewrite old packet history.
* Audit on create/update/activate.
* Bell notification on activation: `transport_rate_activated`.

Default `payment_rules_text`, `ticket_rules_text`, and `deduction_rules_text` preserve the exact MASCI language (0:15→2h / 2:01→4h / 4:01→6h / 6:01+ pays actual + 1h travel · standby 2h · ticket due 5 PM Tuesday · FleetWatcher-verified or no pay · 0.15h unauthorized stop / 1h hot-asphalt penalty / loss-of-asphalt chargeback).

---

## Packet workflow

Collection: `transport_packet_submissions` per carrier.

Status machine (closed-set transitions):

```
draft  →  sent / in_progress / submitted
sent   →  opened / in_progress / submitted / draft
opened →  in_progress / submitted
in_progress     → submitted / draft
submitted       → pending_review / in_progress
pending_review  → needs_correction / approved / suspended
needs_correction→ in_progress / submitted / suspended
approved        → suspended / pending_review
suspended       → pending_review / approved
```

Approval guards (enforced on every approve attempt):
1. `rate_schedule_id` must be recorded.
2. Every required carrier-level document type accepted (no missing).
3. No required document in `expired` status.
4. No required document in `needs_correction` status.

Bell notifications fire on `submitted` and `needs_correction`.

---

## Carrier + driver documents

`carrier_documents` and `driver_documents` collections. Every row stores the R2 file_key + reference, mime type, original filename, expires_at, review status (`pending_review` / `accepted` / `needs_correction` / `expired` / `not_applicable`), reviewer + timestamp, audit_version.

**File bytes are never stored in Mongo.** Direct multipart upload to backend → backend streams to R2 via `photo_storage.upload_photo_bytes` (the same canonical R2 wrapper used by safety/jobsite photos). Audit on upload and review.

Document types — carrier: `sunbiz_certificate`, `mcs_company_snapshot`, `w9`, `insurance_certificate`, `hauling_agreement`, `vehicle_registration`, `lien_release_authorization`, `payment_pickup_authorization`, `other`. Driver: `cdl`, `medical_card`, `clearinghouse`, `driver_license`, `dot_certification`, `drug_alcohol_acknowledgement`, `orientation_acknowledgement_placeholder`, `other`.

Requirements catalog seeded by `bootstrap_track_16_05` into `transport_packet_requirements` (15 default entries covering every MASCI baseline item + modern Clearinghouse / CDL / medical / readiness inspection).

---

## MASCI Hauler Truck Readiness Inspection

Collection: `transport_truck_inspections`.

**Disclaimer (stamped on every record + exposed on every dispatch readiness response):**

> MASCI Hauler Truck Readiness Inspection is an operational readiness check only. It does not replace the carrier's required DOT/FMCSA inspections, driver pre-trip inspection, maintenance obligations, insurance obligations, or legal responsibility for safe operation.

Checklist categories (40 items total · 26 critical):
* **Exterior / Road Readiness** — tires · lug nuts · doors · tailgate · bed · side boards · tarp system · tarp covers bed · fluid leaks · body damage · mirrors · windshield · wipers
* **Lights / Warning Equipment** — headlights · taillights · brake lights · turn signals · four-way flashers · reverse lights · backup alarm · beacons / strobes · reflective tape
* **Identification / Markings** — company logo · DOT number · truck number · MASCI sticker · license plate · registration
* **Safety / Cab** — seatbelt · loose objects · fire extinguisher · CB radio · FleetWatcher ready
* **Driver PPE** — hard hat · high-vis · safety glasses · work boots · long pants · shirt · gloves · hearing protection · PPE acknowledgement

Item statuses: `pass` · `needs_correction` · `not_applicable` · `not_observed`.
Result statuses: `ready` · `pending_correction` · `not_ready` · `expired`.
**Never used:** `failed`, `rejected`, `denied` (locked by regression).

Inspection triggers (first-class field on every record): `initial_onboarding`, `annual_recertification`, `random`, `safety_concern`, `customer_complaint`, `incident_or_accident`, `vehicle_replacement`, `major_modification`, `management_requested`, `dispatch_requested`, `safety_requested`.

Expiration: default 12 months from `inspected_at`; configurable via `expires_in_months` on `/complete`.

Photo evidence: each checklist item carries `photo_keys: []`. Photos are uploaded via the document endpoints (R2 keys only — never bytes).

Eligibility integration:
* Leased truck WITHOUT a ready inspection → `not_dispatchable` (reason: `inspection_missing`).
* Leased truck with `result=not_ready` (critical correction outstanding) → `not_dispatchable`.
* Leased truck with `result=expired` → `expired`.
* Leased truck with `result=pending_correction` → `needs_correction`.
* `masci_owned` trucks are NOT required to have this inspection (Equipment Master / DVIR / Pre-Op remain primary).
* Driver PPE `needs_correction` on `ppe_long_pants` / `ppe_shirt_required` / `ppe_work_boots` / `ppe_acknowledged` → driver computes `not_dispatchable`.

---

## API surface (added by Track 16.05)

### Admin (require admin-strict)
* `GET/POST /api/admin/transportation/rate-schedules`
* `PATCH /api/admin/transportation/rate-schedules/{id}`
* `POST /api/admin/transportation/rate-schedules/{id}/activate`
* `GET/POST /api/admin/transportation/carriers/{id}/packet`
* `PATCH /api/admin/transportation/packets/{id}`
* `POST /api/admin/transportation/packets/{id}/submit`
* `POST /api/admin/transportation/packets/{id}/approve`
* `POST /api/admin/transportation/packets/{id}/needs-correction`
* `GET/POST /api/admin/transportation/carriers/{id}/documents` (multipart upload)
* `PATCH /api/admin/transportation/documents/{id}/review`
* `GET/POST /api/admin/transportation/persons/{id}/documents` (multipart upload)
* `PATCH /api/admin/transportation/driver-documents/{id}/review`
* `GET/POST /api/admin/transportation/trucks/{id}/inspections`
* `GET/PATCH /api/admin/transportation/inspections/{id}`
* `POST /api/admin/transportation/inspections/{id}/complete`
* `GET /api/admin/transportation/eligibility/v2/{target_type}/{target_id}` (Phase 2 truth-table)

### Dispatch (admin or dispatch · READ-ONLY)
* `GET /api/dispatch/transportation/carriers/{id}/packet-status`
* `GET /api/dispatch/transportation/trucks/{id}/readiness`
* `GET /api/dispatch/transportation/readiness-summary` (real-time dashboard — counts by target × state · inspection due/overdue buckets · document expiration buckets · policy_default_months · disclaimer)

---

## Audit + notifications

Every write fires `db.audit_events.insert_one(...)` with:
`kind ∈ {transport_rate_schedule_create / _update / _activate, transport_packet_create / _submitted / _approved / _needs_correction / _suspended, transport_carrier_documents_review, transport_driver_documents_review, transport_carrier_document_upload, transport_driver_document_upload, transport_inspection_started / _item_updated / _completed}` · entity_type · entity_id · actor · old · new · ts · tenant · route · ip · ua.

Bell notifications (admin audience, internal only): `transport_rate_activated`, `TRANSPORT_PACKET_SUBMITTED`, `TRANSPORT_DOC_NEEDS_CORRECTION`, `TRANSPORT_INSPECTION_COMPLETED`.

**Future external email routes (documented · NOT fired in Phase 2):**
* `TRANSPORT_PACKET_SUBMITTED`
* `TRANSPORT_DOC_NEEDS_CORRECTION`
* `TRANSPORT_DRIVER_APPROVED`
* `TRANSPORT_DRIVER_SUSPENDED`
* `TRANSPORT_DOC_EXPIRING`

Wiring through Email Routing v2 ships in Track 16.06.

---

## Eligibility (Phase 2 truth table)

The `compute_transport_eligibility(record_type, record, context)` function now honors a richer `context` bag:

| Context key | Effect |
|---|---|
| `packet_status="needs_correction"` | blocks (state=needs_correction) |
| `packet_status="suspended"` | blocks (state=suspended) |
| `rate_acknowledged=False` | blocks via `rate_not_acknowledged` (state=pending_review) |
| `missing_required_docs > 0` | blocks (state=needs_correction) |
| `expired_required_docs > 0` | blocks (state=expired) |
| `docs_needs_correction > 0` | blocks (state=needs_correction) |
| `inspection_required=True && inspection_result=None` | blocks via `inspection_missing` (state=not_dispatchable) |
| `inspection_result="not_ready"` | blocks (state=not_dispatchable) |
| `inspection_result="expired"` | blocks (state=expired) |
| `inspection_result="pending_correction"` | blocks (state=needs_correction) |
| `ppe_issue=True` (person) | blocks (state=not_dispatchable) |

Phase 1 reasons (status enum, safety_hold, HR lifecycle) remain in effect and take precedence.

---

## Tests · 74 / 74 green (24 from Track 16.04 · 50 from Track 16.05)

Covers all 47 directive scenarios + 3 bonus structural checks. Runs in 0.15 s. Wired into `scripts/deployment_gate.py`.

Live happy-path verified end-to-end:
* Bootstrap on startup creates default $85/hr active rate.
* `/api/admin/transportation/rate-schedules` lists the bootstrapped row.
* Create draft v2 ($95) → activate → v1 retires, v2 active.
* Create truck readiness inspection → complete with all pass → `result=ready` · `expires_at=+12 months`.
* `/api/admin/transportation/eligibility/v2/truck/{id}` reports `state=pending_review · reason=rate_not_acknowledged` (rate ack flows through packet approval — exactly the Phase 2 contract).
* `/api/dispatch/transportation/readiness-summary` returns dashboard with `inspections.policy_default_months=12` and full counts buckets.
* Forbidden paths (`/invite/`, `/public/`) return 404 — no public surface introduced.

---

## Deferrals (do NOT ship in Phase 2)

* No-skip orientation video engine · orientation module player · checkpoints
* Quizzes · certificates
* Public invite link · carrier self-service portal · external carrier emails
* Dispatch hard-block enforcement (eligibility computed; not yet gating assignment)
* Payment calculator · payroll integration
* Scorecards / intelligence dashboards (advisory dashboard is included; carrier scorecard is not)

---

## Risks / unknowns

* `_local_dispatch_or_admin` gate duplicated in `routes/transportation.py` and `routes/transportation_phase2.py`. Both work around the pre-existing `_require_dispatch_or_admin` wrapper bug. Phase 3 should consolidate by fixing the platform wrapper.
* R2 upload requires R2 env vars; the fallback path stores only the synthetic file_key (no bytes). The test suite locks the no-bytes-in-Mongo invariant.
* Eligibility is recomputed on read in this phase to guarantee freshness; future phases may move to event-driven invalidation if traffic warrants.

---

## Next recommended track

**Track 16.06 — Phase 3 Orientation Engine + UI Surface**:
1. Native MASCI orientation video player (no-skip) + quiz engine + certificate generator.
2. Carrier portal login (invite-link based · expiring · scoped read-only) so leased haulers can self-serve packet upload.
3. External Email Routing v2 wiring for the 5 documented future routes.
4. Optional dispatch hard-block toggle (config flag · per-tenant).
5. UI extension on `/admin/transportation` to expose Packet · Documents · Inspection wizard · Rate schedule (currently API-only).
