# TRACK 19.62 · Permission Certification

**No widening.** Every role sees exactly what it saw before, plus the
existing extinguisher data — which the same roles could already access
through the Safety Portal.

## Role matrix (Fire Protection · Phase A)

| Role | View extinguisher on Asset Thread | Inspect / edit | Add historical fire doc |
|---|---|---|---|
| Admin | ✅ | ❌ (via Safety Portal) | ✅ (asset lane) |
| HR/Admin | ✅ | ❌ | ✅ |
| Executive | ✅ | ❌ | ❌ |
| Safety | ✅ | ✅ (existing endpoints) | ❌ |
| Shop | ✅ (via parent asset lens) | ❌ | ❌ |
| Fleet | ✅ (via parent asset lens) | ❌ | ❌ |
| Dispatch | ✅ (via parent asset lens · DOT context) | ❌ | ❌ |
| Transportation | ✅ (own DOT units) | ❌ | ❌ |
| PM | ✅ (own project's linked units) | ❌ | ❌ |
| Field / Superintendent | ✅ (own crew's linked units) | ❌ | ❌ |
| Public | ❌ | ❌ | ❌ |

## Endpoint gates (unchanged)
| Endpoint | Gate |
|---|---|
| `GET /api/asset-spine/resolve` | `require_any_portal_dep` |
| `GET /api/safety/fire-extinguishers?assigned_target_ref=...` | `require_safety_token` (unchanged) |
| `GET /api/employee-records/records?entity_kind=asset&asset_id=...` | HR / Safety / Asset Admin / Admin (existing gate) |
| `POST /api/employee-records/records` (fire slug) | same asset-lane gate |
| `POST /api/employee-records/records/{id}/approve` (fire slug) | `LANE_APPROVERS["asset"] = {"asset_admin","hr","admin"}` |

## No new writes
- Asset Thread does not write to `db.fire_extinguishers`.
- Asset Thread does not gain a new POST/PATCH endpoint.
- No route added anywhere for Phase A.

## Cross-lane guards (Track 19.61 preserved · not touched)
- `entity_kind="vendor"` only in `vendor` lane.
- `entity_kind="asset"` only in `asset` lane.
- Fire-specific record_types are additive within the `asset` lane.

## Zero widening statement
Every role's capability set is byte-identical to pre-19.62. The thread
is a **view layer**; it does not open any endpoint that was not open
before.
