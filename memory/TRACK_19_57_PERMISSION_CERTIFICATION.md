# TRACK 19.57 · Permission Certification

## Auth surfaces
- App.js route wrapper: `P(<PmProjectThread />)` → `RequirePm` guard.
  Identical to `/pm/project/:projectNumber` (`P(<PmProjectDetail />)`).
- Page-level guard: `if (!(isPm() || isAdmin())) return <AccessDenied attemptedPortal="pm" />;`
- Request headers: `X-PM-Token` (PM portal) + `X-Admin-Token` (Admin fallback).
  Public endpoints (`/api/jobs/{pn}/recent-context`, `/api/operational-events/*`,
  `/api/material-movement/*`, `/api/job-hazard-files/by-project/*`) are called
  without tokens — matching what `PmProjectDetail` already does today.

## What the thread cannot expose
| Attempted leak                   | Guardrail                                                                 |
|----------------------------------|---------------------------------------------------------------------------|
| HR-private employee data         | Not fetched. Crew relationships surface names ALREADY visible on `/api/jobs/{pn}/recent-context`, which is the same source the daily-report flow uses. |
| Restricted safety internals      | Not fetched. Only `job-hazard-files/by-project/{pn}` is called — the same public endpoint the crew already uses to pull JHPs offline. |
| Admin-only recipient / audit rows| Not fetched. No `/api/admin/*` calls originate from this page.            |
| Unauthorised financial data      | Not fetched. No P&L, contract value, or invoice endpoints are touched.    |
| Hidden documents                 | Not fetched. Only documents already published to `job-hazard-files` surface. |

## No permission widening
The Track 19.57 promotion consumes only endpoints already reachable by
`PmProjectDetail`, `PmJobsRead`, and any other PM-portal-accessible
page. It grants zero additional read access, and grants no write access.
