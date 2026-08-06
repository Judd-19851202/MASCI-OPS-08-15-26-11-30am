# WP18DB Incident 401 Root Cause

## Reopened blocker

- **Source evidence:** legitimate field user complaint during Accident / Incident Report submission.
- **Blocking symptom:** a real field identity reached Incident Report submit and received `401 Unauthorized`.
- **Constraint:** repair the exact auth/session contract without widening permissions, bypassing project scope, or disabling expiry.

## Exact reproduction

Using the existing governed preview field identity from `/app/memory/test_credentials.md`:

- login endpoint: `/api/auth/multi-login`
- identity: `cert.foreman@example.com`
- returned tokens: directory session + `field_leadership` portal token

### Pre-fix failing call

`POST /api/incident-cases`

Headers supplied during reproduction:

- `X-Directory-Token`
- `X-FL-Token`

Observed result:

- HTTP `401`
- detail: `Safety, Admin, or PM login required`

Backend log correlation during the same proof window recorded:

- `POST /api/incident-cases HTTP/1.1" 401 Unauthorized`

## First failing layer

The first failing layer was the **outer backend dependency gate**, with a second confirming client-side contract gap.

### Backend gate mismatch

Before repair, the Incident engine/report routes were registered behind `make_require_safety_admin_or_pm(...)`.

That meant:

- Safety users were accepted.
- Admin users were accepted.
- PM users were accepted.
- Legitimate Field Leadership users were rejected **before** the incident capability matrix could run.

So the field actor never reached the governed `role_can(...)` checks for create / patch / evidence / submit.

### Frontend client mismatch

File: `frontend/src/lib/incidentReportApi.js`

Before repair, the Incident Report client:

- used its own standalone axios client
- scoped auth headers to `safety`, `admin`, and `pm`
- omitted `field_leadership`
- bypassed the shared session-status / auth-failure handling stack in `frontend/src/lib/api.js`

So the frontend and backend were both enforcing the wrong outer contract for a legitimate field reporter.

## Smallest safe repair

### Narrow backend field gate

File: `backend/routes/safety_portal/_deps.py`

Added a dedicated dependency:

- `make_require_safety_admin_pm_or_field(...)`

Behavior:

- preserves existing Safety/Admin/PM acceptance
- accepts a legitimate `X-FL-Token` after the existing async Field Leadership token + session-activity validation
- normalizes the accepted actor to `role="field"`, so the existing incident capability matrix remains the single source of truth

### Narrow route wiring only where field submission actually needs it

Files:

- `backend/incident_engine/routes.py`
- `backend/incident_engine/report_routes.py`
- `backend/server.py`

The new field-capable gate was applied only to:

- incident vocabulary
- create case
- patch field block
- add evidence
- transition submit path
- weather lookup
- project-context lookup

The broader Safety/Admin/PM workspace gate was left intact for the rest of the incident workspace.

### Frontend contract repair

File: `frontend/src/lib/incidentReportApi.js`

- switched from the standalone axios client to the governed shared `api` client
- expanded scoped auth headers to include `field_leadership`
- preserved directory-token forwarding
- restored shared auth/session handling on 401s instead of a silent client-side side path

## Runtime proof after repair

Using the same legitimate field identity:

- `POST /api/incident-cases` → `200`
- `PATCH /api/incident-cases/{id}/field-block` → `200`
- `POST /api/incident-cases/{id}/evidence` → `200`
- `POST /api/incident-cases/{id}/transitions` to `FIELD_SUBMITTED` → `200`

Observed filed result during proof:

- case state advanced to `FIELD_SUBMITTED`
- case number was issued (`2026-00009` in the direct proof run)

### Negative controls still denied

- no auth → `401`
- directory token only → `401`
- PM directory + PM token only → `403` on create

## Why this is the precise fix

The repair did **not** widen authority to all field routes.

It only restored the intended field-submission path by:

1. accepting the legitimate field token family on the exact incident-report surfaces that need it
2. preserving the existing incident capability matrix as the write authority
3. keeping unauthorized and PM-only create attempts denied
4. restoring shared session/error handling in the Incident frontend client

## Conclusion

The legitimate field-user 401 was not caused by expired tokens, missing session activity, or a failing permission matrix. It was caused by a **mismatched outer auth contract**: the field reporter path used the Field Leadership token family, but both the frontend client and backend route gate were limited to Safety/Admin/PM. The reopened repair restored the governed field-report contract without weakening authorization.