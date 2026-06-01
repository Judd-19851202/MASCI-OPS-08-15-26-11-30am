# Phase 1A · API Impact

**Program:** OMEGA · PCP · Phase 1A · Final Build Package
**Mode:** Design-only
**Date:** 2026-06-01

---

## 1 · Summary

* **19 new endpoints** (all additive)
* **0 modified endpoints** (existing payloads unchanged · new fields appear in detail responses where the underlying doc gains fields)
* **0 deprecated endpoints**
* **1 modified response shape** (incident DETAIL · adds new fields; LIST `IncidentSummary` shape unchanged)

---

## 2 · Universal transition endpoint contract

All 11 transition endpoints follow the same shape:

```
POST /api/<workflow_family>/{id}/transition

Request body:
{
  "to_state": "OPEN" | "IN_PROGRESS" | "PENDING_REVIEW" | "PENDING_CLOSURE" | "CLOSED",
  "reason": "string (required on REOPEN paths)",
  "metadata": { /* arbitrary */ }
}

Response 200:
{
  "id": "<doc id>",
  "lifecycle_state": "<new state>",
  "state_changed_at": "ISO ts",
  "state_changed_by": "<actor>",
  "transition_event_id": "<workflow_state_events id>"
}

Response 422: validation error (invalid to_state, missing reason, etc.)
Response 403: role gate failed
Response 409: idempotency collision (same transition by same actor in same minute)
Response 410: doc soft-deleted
```

---

## 3 · Per-workflow endpoint specifications

### 3.1 · Incidents (OC-001)

| # | Method | Path | Body | Returns | Auth |
|---|---|---|---|---|---|
| 1 | POST | `/api/incidents/{id}/transition` | `{to_state, reason?, metadata?}` | updated doc + event_id | Safety · Admin · Super-Admin |
| 2 | GET | `/api/incidents/{id}/state-events?limit=&offset=` | n/a | paginated list of `workflow_state_events` | per-doc read auth (Safety · Admin · PM scoped · HR read) |

**Incident-specific metadata schema:**
```json
"metadata": {
  "closer_attestation": "string (optional · recorded with closure)",
  "osha_attested": true | false,
  "osha_form_link": "string (required if osha_recordable=Yes and not Super-Admin override)",
  "super_admin_override": true | false,
  "override_reason": "string (required when super_admin_override=true)"
}
```

### 3.2 · Daily Reports (OC-002)

| # | Method | Path | Body | Returns | Auth |
|---|---|---|---|---|---|
| 3 | POST | `/api/daily-reports/{id}/transition` | `{to_state, reason?, return_reason?, metadata?}` | updated doc | PM (assigned) · Admin · Super-Admin |
| 4 | GET | `/api/daily-reports/{id}/state-events` | n/a | paginated | per-doc read auth |

**DR-specific metadata:**
```json
"metadata": {
  "closer_attestation_hours_aligned": true,   // required on IN_PROGRESS → CLOSED
  "incident_link_verified": true,             // required if accident=Yes on DR
  "return_reason": "string"                   // required on IN_PROGRESS → OPEN
}
```

Return-to-field notification: server triggers `notifications.insert_one({kind:"dr_returned_to_field", recipient_id: <submitter>, ...})` synchronously.

### 3.3 · QA/QC (OC-003)

| # | Method | Path | Body | Returns | Auth |
|---|---|---|---|---|---|
| 5 | POST | `/api/qaqc-inspections/{id}/transition` | `{to_state, reason?, metadata?}` | inspection-level transition | PM (assigned) · Admin · Super-Admin |
| 6 | POST | `/api/qaqc-inspections/{id}/deficiencies/{def_id}/transition` | `{to_state, reason?, assigned_to?, resolution_notes?, metadata?}` | deficiency-level transition | PM · FL (crew-scoped) · Admin |
| 7 | GET | `/api/qaqc-inspections/{id}/state-events` | n/a | combined inspection + deficiency events | per-doc read auth |

Deficiency-level body fields:
* `assigned_to`: required on OPEN → IN_PROGRESS
* `resolution_notes`: optional on IN_PROGRESS → PENDING_REVIEW

### 3.4 · Site Inspections (OC-004)

| # | Method | Path | Body | Returns | Auth |
|---|---|---|---|---|---|
| 8 | POST | `/api/inspections/{id}/transition` | `{to_state, reason?, metadata?}` | inspection transition | Safety · Admin · Super-Admin |
| 9 | POST | `/api/inspections/{id}/findings/{finding_id}/transition` | same shape as QA/QC deficiency | finding transition | Safety · PM (job) · FL (crew) · Admin |
| 10 | GET | `/api/inspections/{id}/state-events` | n/a | combined events | per-doc read auth |

### 3.5 · Payroll Variance (OC-007)

| # | Method | Path | Body | Returns | Auth |
|---|---|---|---|---|---|
| 11 | POST | `/api/hr/payroll-variance/batches/{id}/transition` | `{to_state, reason?, metadata?}` | batch transition | HR · Admin · Super-Admin |
| 12 | GET | `/api/hr/payroll-variance/batches/{id}/state-events` | n/a | paginated | HR · Admin |

**Payroll-specific metadata:**
```json
"metadata": {
  "finalization_attestation": "string (required on PENDING_REVIEW → CLOSED)"
}
```

### 3.6 · JHA Acknowledgement (OC-005)

| # | Method | Path | Body | Returns | Auth |
|---|---|---|---|---|---|
| 13 | POST | `/api/jhas/{jha_id}/acknowledgements` | `{shift_date, shift?, crew_label, acknowledged_by:{display_name, role, employee_id?}, signature?, attested_by?}` | created row | FL · Safety · Admin · public-token |
| 14 | GET | `/api/jhas/{jha_id}/acknowledgements?shift_date=&shift=` | n/a | per-JHA list | FL/Safety/PM/Admin |
| 15 | GET | `/api/jobs/{job_id}/jha-acknowledgements?date_from=&date_to=` | n/a | per-job daily rollup | FL (crew-scoped) · PM (job-scoped) · Safety · Admin |
| 16 | GET | `/api/admin/jha-acknowledgements?date_from=&date_to=&job_id=&jha_id=` | n/a | global filterable list | Safety · Admin |
| 17 | DELETE | `/api/jhas/{jha_id}/acknowledgements/{ack_id}` | `{deletion_reason}` | soft-delete | Safety · Admin · Super-Admin |
| 18 | GET | `/api/jha-acknowledgements/coverage?date=&job_id?=&jha_id?=` | n/a | coverage envelope | Safety · Admin |

**Coverage envelope:**
```json
{
  "date": "2026-06-08",
  "total_jhas_active": 4,
  "total_acks_today": 12,
  "coverage_percent": 75.0,
  "per_jha": [
    {
      "jha_id": "...",
      "jha_doc_id": "JHA-2026-00042",
      "job_doc_id": "T5860",
      "crews_expected": 3,
      "crews_acknowledged": 2,
      "coverage_percent": 66.7,
      "missing_crews": ["Crew 4 - Trenching"]
    }
  ]
}
```

### 3.7 · Cross-cutting admin

| # | Method | Path | Body | Returns | Auth |
|---|---|---|---|---|---|
| 19 | GET | `/api/admin/workflow-state-events?workflow=&from_state=&to_state=&date_from=&date_to=` | n/a | global filterable list | Admin · Super-Admin |

---

## 4 · Public token endpoint (OC-005 sub-pattern)

A separate endpoint pattern for QR-token acknowledgement submissions:

```
POST /api/public/jha-ack/{token}

Request body:
{
  "acknowledged_by": { "display_name": "...", "role": "operator" },
  "signature": "base64..."
}

Response 200:
{ "ack_id": "...", "jha_doc_id": "JHA-2026-00042", "timestamp": "..." }

Response 404: token invalid/expired
Response 410: JHA superseded
```

Token pattern mirrors existing `/daily/submit?token=...` flow. Tokens are pre-minted at JHA creation time + shipped as QR codes via the existing JHA PDF render.

---

## 5 · Idempotency contract

Each transition write computes:
```
idempotency_key = (workflow_type, doc_id, to_state, actor_user_id, occurred_at_minute)
```
where `occurred_at_minute = floor(ts to nearest minute)`. Unique compound index enforces. Duplicate → 409 with body:
```json
{
  "detail": "Duplicate transition in same minute window",
  "existing_event_id": "...",
  "existing_occurred_at": "..."
}
```

Client UI handles 409 by refreshing the LifecyclePanel (state is already correct).

---

## 6 · Auth headers per role

| Role | Header | Existing? |
|---|---|---|
| Super-Admin · Admin | `X-Admin-Token: ...` | ✅ |
| Safety | `X-Safety-Token: ...` | ✅ |
| HR | `X-HR-Token: ...` | ✅ |
| PM | `X-PM-Token: ...` | ✅ |
| FL | `X-FL-Token: ...` | ✅ |
| Public submission (JHA QR) | `?token=<JWT>` | new minting required |

No new authentication mechanism. Token-based JHA submissions reuse the existing public-submission JWT pattern (`lib/public_token.py`).

---

## 7 · Rate limiting

* Transition endpoints: 30/min per actor (sufficient; transitions are rare events)
* JHA acknowledgement endpoints: 60/min per actor (crew acks may burst at shift start)
* Public JHA token endpoint: 5/min per token (1 ack per crew member typical)

Reuses existing `lib/rate_limit.py` decorators.

---

## 8 · Audit cross-emission

In addition to `workflow_state_events`, every transition emits a row to `audit_events` (existing collection) with `kind="workflow_transition"` for the catch-all audit search. This is for backwards compatibility with existing audit consumers.

---

## 9 · OpenAPI / Swagger documentation

All 19 new endpoints declare Pydantic request/response models. Auto-generated OpenAPI spec available at `/api/openapi.json` (existing FastAPI behavior). Swagger UI at `/api/docs` (admin-gated).

---

## 10 · OMEGA discipline

🟢 Design-only · 19 endpoints fully specified · request/response shapes documented · idempotency contract explicit · 0 breaking changes.

🛑 Continue to `PHASE1A_ROLE_PERMISSION_MATRIX.md`.
