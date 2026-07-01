# Track 19.05 · Daily Report Validation Audit

## Required fields (frontend + backend)

| Field | Frontend enforce | Backend enforce | Notes |
| --- | --- | --- | --- |
| `project_name` | via `DailyReportCreate` model | Pydantic `str` (no default) | REQ |
| `location` | Pydantic `str` (no default) | REQ |
| `report_date` | Pydantic `str` (no default) | REQ, `YYYY-MM-DD` |
| `prepared_by` | Pydantic `str` (no default) | REQ |
| `photos[]` | Submit gate requires `len >= photo_min (6)` | Not enforced server-side; UI-only | Field-friendly soft gate |
| `prepared_by_signature` | Submit gate — signature required | Pydantic `Optional[str] = ""` | Field-friendly; UI-only |
| Excavation gate | Server 422 if `excavation_activity_today == "Yes"` and no `linked_excavation_ids[]` | HARD server-side | See Trigger Audit |

## Conditional required-when-active

| Trigger | Then required |
| --- | --- |
| `weather_impact = Yes` | `weather_impact_notes` (soft, UI hint only) |
| `injuries_reported = Yes` and `safety_notified = Yes` | `safety_contact_person`, `safety_contact_time` (soft) |
| `injuries_reported = Yes` and `incident_report_filled = Yes` | `incident_report_time` (soft) |
| Row added to `masci_crews[]` | crew name (via EmployeeCombo) — enforced by row UI |
| Row added to `equipment[]` | description — enforced by EquipmentCombo |
| Row added to `materials[]` | material, quantity, unit — soft UI hint |
| Row added to `outbound_materials[]` | material, quantity, unit — soft UI hint |

## Frontend-only submit gate

`NewDailyReport.jsx` blocks submit when:
* `data.photos.length < 6`
* `!data.prepared_by_signature`
* Any REQ Pydantic field is empty client-side (guards a 422)

## Backend validation

* `DailyReportCreate` Pydantic model — rejects missing REQ fields with HTTP 422.
* Idempotency key from request headers — duplicate submits collapse to same record.
* Rate limiter `rate_limit_public_post` — throttles public POSTs.
* Excavation gate — HTTP 422 with structured `detail.error = excavation_record_required`.

## Non-blocking warnings (calm affordances)

* `safety-not-notified-warning` — reminder, does not block submit.
* `incident-report-required-warning` — deep link to `/safety/incident/new`, non-blocking.
* Prior-usage banner — reassurance only.
* Draft cross-token pill — informational.

## What is NOT validated

* Row content sanity (crew hours can be 0, equipment description can be empty on save-as-draft).
* Free-text notes have no XSS/HTML stripping — sanitised at render time only.
* Photo captions parallel array can drift from `photos[]` length — tolerated.

## Redesign protection

* HIGH — Pydantic REQ fields. Renaming or removing breaks every existing submitter.
* HIGH — 6-photo minimum. Cultural expectation; PM relies on visual proof.
* HIGH — Excavation gate 422 contract. Field teams rely on the exact `detail.error` code for toasts.
* MEDIUM — Idempotency key header. Redesign must preserve `X-Idempotency-Key` semantics.
