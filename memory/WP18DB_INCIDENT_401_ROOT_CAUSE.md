# WP18DB Incident 401 Root Cause

## Reopened blocker

- **Source evidence:** supervisor field complaint during Accident / Incident Report submission.
- **Blocking symptom:** the public Incident Report flow reached submit and hit `401 Unauthorized`.
- **Corrected constitutional truth:** Incident / Accident Report from the public Field/Safety tiles is a **no-login** form. Only designated portal workspace routes require authentication.

## Exact reproduction

### Pre-fix failing call

The public page was ultimately wired into the authenticated internal incident workspace submit path:

- frontend submit path attempted the authenticated incident engine helpers
- internal write surface: `POST /api/incident-cases`

Observed result without portal auth:

- HTTP `401`
- detail: `Safety, Admin, or PM login required`

Backend log correlation during proof recorded:

- `POST /api/incident-cases HTTP/1.1" 401 Unauthorized`

## First failing layer

The first failing layer was the **public/private route-boundary mismatch**, with auth only appearing as the symptom.

### Backend boundary mismatch

Before repair, the page submit path targeted the **internal incident workspace** route family (`/api/incident-cases/*`), which is correctly auth-gated for portal operations.

That internal route family is not the constitutional contract for the public Field/Safety tile form.

### Frontend client mismatch

File: `frontend/src/lib/incidentReportApi.js`

Before repair, the Incident Report client submitted through the internal incident-engine helper set instead of a public rate-limited endpoint.

So the page contract and the route contract disagreed:

- UI surface = public tile form
- submit route = authenticated workspace route

## Smallest safe repair

### Public submit route added for the public form

File: `backend/incident_engine/public_gate.py`

Added a dedicated public endpoint:

- `POST /api/public/incident-cases`

Behavior:

- accepts no-login public Incident Report submissions
- reuses the governed incident engine to create the canonical case
- records evidence items best-effort
- transitions the case to `FIELD_SUBMITTED`
- preserves idempotency through the public-submission register

### Public helper route correction

File: `backend/incident_engine/report_routes.py`

The public Incident Report helpers were returned to public access:

- `/api/incident-intelligence/weather`
- `/api/incident-intelligence/project-context/{project_number}`

These are form-assist endpoints for the public reporting surface and should not demand portal auth.

### Frontend contract repair

File: `frontend/src/lib/incidentReportApi.js`

- final submit now uses the dedicated public endpoint through `submitPublicIncident(...)`
- public incident helpers no longer depend on login
- internal authenticated workspace helpers remain separate and protected

## Runtime proof after repair

Unauthenticated public proof passed:

- `POST /api/public/incident-cases` → `200`
- canonical case returned with `case_id` and `case_number`
- filed state returned as `FIELD_SUBMITTED`
- replay with the same idempotency key returns `duplicate=true` with the same case id

### Negative controls still correct

- unauthenticated `POST /api/incident-cases` → `401`
- internal authenticated incident workspace remains protected

## Why this is the precise fix

The repair did **not** weaken the internal incident workspace.

It restored the correct public/private split by:

1. keeping the internal `/api/incident-cases/*` workspace auth-gated
2. moving the public form back onto a dedicated no-login endpoint
3. keeping public helper endpoints public
4. preserving canonical incident creation, evidence handling, filing, and idempotency

## Conclusion

The incident 401 was not truly a field-user authorization defect. It was a **surface-boundary defect**: a public tile form was routed into an authenticated internal workspace API. The reopened repair restored the governed public-form contract without opening the protected incident workspace.