# TRACK 19.61 · Permission Certification — Asset Thread

**Doctrine:** The Asset Thread is a **view layer**. It does not grant
any role access it did not already have on the underlying certified
surfaces.

## Route auth

`/admin/assets/:assetRef/thread` is registered under the `A(...)`
Admin-portal gate in `App.js`. Access is checked in the page itself via
`isAdmin()`; when false, `AccessDenied` renders.

## Backend gate summary

| Endpoint consumed | Gate | Widened by 19.61? |
|---|---|---|
| `GET /api/asset-spine/resolve` | `require_any_portal_dep` (any portal token) | ❌ |
| `GET /api/asset-spine/assets/{asset_id}/profile` | `require_any_portal_dep` | ❌ |
| `GET /api/assets/{unit_number}/timeline` | `require_any_fleet_portal_dep` | ❌ |
| `GET /api/operational-intelligence/summary` | existing OI gate | ❌ |
| `GET /api/employee-records/records?entity_kind=asset&…` | HR / Safety / Asset Admin / Admin (existing gate) | ❌ |
| `POST /api/employee-records/records` (with `entity_kind=asset`) | same HR / Admin gate as employee/vendor records | ❌ |
| `POST /api/employee-records/records/{id}/approve` (asset) | `LANE_APPROVERS["asset"] = {"asset_admin","hr","admin"}` (existing set) | ❌ |

## Role lens (thread page)

| Role | Can open the thread? | Notes |
|---|---|---|
| HR/Admin | ✅ | Full read; edit paths go through existing HR flows. |
| Admin | ✅ | Full read; asset master edits go through Admin Equipment. |
| Executive | via Admin token | Read-only. |
| Shop | Fleet lens (`/fleet/unit/:unit_number`) | Existing shop-portal token. |
| Fleet | Fleet lens (`/fleet/unit/:unit_number`) | Existing fleet-portal token. |
| Dispatch | Fleet lens (`/fleet/unit/:unit_number`) | Read-only. |
| Trans / Transportation | Fleet lens for DOT-relevant units | Read-only. |
| Safety | Fleet lens + Historical Records asset queue | Read-only. |
| PM | Deep-link to Asset Thread through project relationship graph (existing edges); scoped to own project's assigned assets. | Read-only. |
| Field / Superintendent | Deep-link through daily-report equipment usage; scoped to own crew. | Read-only. |
| Public | ❌ | No public route. |

## Cross-lane guards enforced by backend

- `entity_kind="vendor"` only permitted in the `vendor` ownership lane
  (Track 19.59 rule).
- `entity_kind="asset"` only permitted in the `asset` ownership lane
  (Track 19.61 rule).
- Missing `entity_kind` continues to default to `"employee"` —
  backwards-compatible.
- Approval of an `entity_kind="asset"` record requires
  `asset_id | asset_unit_number | related_asset_id` **plus**
  `record_type`.

## What Track 19.61 explicitly does NOT do

- Does not grant any new field to any role.
- Does not expose vendor documents inside the asset view or vice
  versa (safety sentinel — the `entity_kind` filter enforces
  separation).
- Does not open a write path from the thread page.
- Does not create a "share this asset thread" public link.
- Does not lower the auth gate on any existing endpoint.

**Certification:** No permission widening. Zero drift.
