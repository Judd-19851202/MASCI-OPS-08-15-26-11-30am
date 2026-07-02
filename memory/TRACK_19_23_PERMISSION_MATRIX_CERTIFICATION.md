# TRACK 19.23 · Permission Matrix Certification

## Gate: `make_employee_records_actor_gate` (Track 19.21b)

| Header | Role bound | Reader lanes | Approver lanes |
|---|---|---|---|
| `X-HR-Token` | `hr` | all 4 | all 4 |
| `X-Safety-Token` | `safety` | safety only | safety only |
| `X-Shop-Token` (with `is_asset_admin`) | `asset_admin` | asset only | asset only |
| `X-Admin-Token` | `admin` | all 4 | all 4 |
| (none) | — | 401 | 401 |

## Live-preview curl verification (Safety token, live)

| Endpoint | Expected | Actual |
|---|---|---|
| `GET /vocabulary` | 200, `allowed_lanes_for_actor=["safety"]` | ✅ |
| `GET /queues/hr` | 403 | ✅ |
| `GET /queues/safety` | 200 | ✅ |
| `GET /vocabulary` no auth | 401 | ✅ |

## Export package RBAC (PACKAGE_LANE_GATE · live curl)

| Role | complete_file | training | discipline | safety | ppe_asset | historical_records |
|---|---|---|---|---|---|---|
| HR | 200 | 200 | 200 | 200 | 200 | 200 |
| Safety | 403 | 403 | 403 | 200 | 403 | 200 |
| Asset admin | 403 | 403 | 403 | 403 | 200 | 200 |
| Admin | 200 | 200 | 200 | 200 | 200 | 200 |
| Field/Public | n/a (no token) → 401 | | | | | |

## Employee 360 access
Protected by `RequireHR` React gate (frontend) — Field/Public/PM tokens cannot open the page. Verified via routing:
```
Route path="/hr/employees/:empId/profile" element={H(<EmployeeProfile />)}
```
`H(...)` = `<RequireHR>` wrapper.

## Approver matrix (`LANE_APPROVERS`)

| Lane | Approvers |
|---|---|
| `hr` | HR + Admin only |
| `safety` | HR + Admin + Safety |
| `asset` | HR + Admin + Asset Admin |
| `corporate_import` | HR + Admin only |

Server-enforced via `_actor_can_approve(actor, lane)` on both single-record and bulk approve.

## Ownership doctrine
- HR is ultimate system owner.
- Safety owns Safety lane operationally (approve safety-lane records + upload).
- Asset Administrator owns Asset lane operationally.
- Corporate Import lane is HR-only.
- **No permission leaks detected in this certification pass.**

**Verdict:** GO. No leaks. Matrix airtight.
