# TRACK 19.59 · Permission Certification

## Auth surfaces (unchanged)
- Actor gate: `make_employee_records_actor_gate` — HR / Safety / Asset Administrator / Admin token headers.
- Read gate: `_actor_can_read_lane` — HR + Admin read every lane; Safety reads Safety lane; Asset Admin reads Asset lane. **No case for the `vendor` lane** — meaning non-HR/Admin actors receive HTTP 403 on any vendor-lane call.
- Approve gate: `_actor_can_approve` — flows through `LANE_APPROVERS["vendor"] = {"hr", "admin"}`.

## Role matrix for the vendor lane
| Role                | Read vendor lane? | Upload vendor doc? | Approve vendor doc? | Reject vendor doc? |
|---------------------|:-----------------:|:------------------:|:-------------------:|:------------------:|
| HR                  | ✅                | ✅                 | ✅                  | ✅                 |
| Admin (super)       | ✅                | ✅                 | ✅                  | ✅                 |
| Safety              | ❌                | ❌                 | ❌                  | ❌                 |
| Asset Administrator | ❌                | ❌                 | ❌                  | ❌                 |
| PM                  | ❌                | ❌                 | ❌                  | ❌                 |
| Field / Public      | ❌                | ❌                 | ❌                  | ❌                 |

## Zero permission widening
Every role's authority for vendor documents inherits from the same `_actor_can_read_lane` / `_actor_can_approve` decision points that guard the employee lanes. **No new permission surface introduced. No role gains new access.** Non-HR/Admin roles automatically receive HTTP 403 on vendor-lane endpoints because the read gate does not enumerate a case for them.

## Guard behaviour
1. `POST /api/employee-records/records` with `ownership_lane="vendor"` from a non-HR/Admin actor → 403.
2. `POST /api/employee-records/records/{id}/approve` on a vendor record from a non-HR/Admin actor → 403.
3. `POST /api/employee-records/records/{id}/reject` on a vendor record from a non-HR/Admin actor → 403.
4. `GET /api/employee-records/records?entity_kind=vendor` from a non-HR/Admin actor → 403 (falls through to non-HR/Admin lane restriction).

## PM / Safety / Shop / Fleet consumption path (future)
Track 19.60 will render a role-lensed Vendor Thread that consumes the vendor lane through **role-appropriate** read paths (e.g., PM sees documents scoped to their projects; Safety sees COI / prequalification only). Track 19.59 does **not** open any consumer read paths — that is the job of the next track.
