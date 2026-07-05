# DR-ROI-001E · RBAC Matrix

| Endpoint / Route                                              | Role scope (Phase E · additive read-only) |
|---------------------------------------------------------------|-------------------------------------------|
| `GET /api/ods/pm/dashboard`                                   | PM / Admin (inherits router-level guard)  |
| `GET /api/ods/pm/attention`                                   | PM / Admin                                |
| `GET /api/ods/pm/projects/{project_id}/kpis`                  | PM (own projects) / Admin                 |
| `GET /api/ods/pm/projects/{project_id}/intelligence`          | PM (own projects) / Admin                 |
| `GET /api/ods/pm/projects/{project_id}/brief`                 | PM (own projects) / Admin                 |
| `GET /api/ods/pm/projects/{project_id}/attention`             | PM (own projects) / Admin                 |
| `GET /api/ods/admin/dashboard`                                | Admin                                     |
| `GET /api/ods/admin/delays`                                   | Admin                                     |
| `GET /api/ods/admin/attention`                                | Admin                                     |
| `GET /api/ods/executive/brief`                                | Admin / Executive                         |
| `GET /api/ods/executive/health`                               | Admin / Executive                         |
| SPA `/pm/operational-intelligence`                            | Inherits `/pm/*` outer guard chain        |
| SPA `/admin/ods-intelligence`                                 | Inherits `/admin/*` outer guard chain     |
| SPA `/executive/ods-intelligence`                             | Inherits `/executive/*` guard chain       |

## Phase E Additive Contract
Phase E ships an **additive read surface**. No permission widening.
No new tokens or roles. Existing route-tree guards in `AppRoutes.jsx`
continue to govern outer-tree access. Backend endpoints inherit the
project-scoping conventions used by the surrounding `/api/ods/*` router
in `server.py` (already registered by the `register_ods_intelligence_routes`
callback).

## What's Explicitly NOT in this phase
- No new bespoke tokens (X-*-Token) — none required.
- No writes.
- No user-facing configuration surface.
- No cross-tenant reads; every query filters by `tenant_id="masci"`.

## Future (Phase G · Deployment Certification)
- Confirm the outer `/pm/*`, `/admin/*`, `/executive/*` guard chain is
  fronting each SPA route in the RC-1 bundle.
- Add per-project PM scoping to the `/api/ods/pm/*` endpoints if PMs
  become the primary caller (currently routed through the admin token
  in preview).
