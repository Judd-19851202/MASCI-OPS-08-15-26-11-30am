# OA-1 · Operations Actions Constitution

Date: 2026-07-25

## Canonical Owner

- Backend route owner: `/app/backend/routes/operations_actions/api.py`
- Route gate support: `_require_oa_actor` in `backend/server.py`
- Frontend direct consumers:
  - `/app/frontend/src/lib/oa.js`
  - `/app/frontend/src/pages/operations_actions/OperationsActions.jsx`
  - `/app/frontend/src/pages/operations_actions/OperationsActionNew.jsx`
  - `/app/frontend/src/pages/operations_actions/OperationsActionDetail.jsx`
  - `/app/frontend/src/components/oa/*`

## Owned Truth

Family 3B directly owns the canonical `operations_actions` coordination record and its lifecycle:

- create
- read
- patch core fields
- assign / reassign owner
- change status
- append note
- add / remove photo evidence
- append immutable in-record history

## Canonical Authentication Contract

Every Family 3B request MUST include:

1. exactly one valid acting-portal token
2. the bound `X-Directory-Token` for the same logical session

Allowed portal lanes:

- `X-Admin-Token`
- `X-PM-Token`
- `X-HR-Token`
- `X-Safety-Token`
- `X-Dispatch-Token`
- `X-Shop-Token`
- `X-FL-Token`

Token-only requests are not valid for Family 3B.

## Trust + Audit Contract

- canonical persistence succeeds before notification fanout
- every mutation appends in-record `history`
- every mutation emits bounded Trust Spine lifecycle evidence under workflow `operations-action`
- assignment notification remains best-effort and never blocks canonical persistence

## Performance Ownership

Family 3B owns:

- summary aggregation shape
- list query shape and payload size
- owner-search fan-out strategy
- per-mutation duplicate query reduction
- photo metadata persistence ordering

Shared infrastructure owns:

- directory/session auth validation
- notification fanout internals
- object storage service internals