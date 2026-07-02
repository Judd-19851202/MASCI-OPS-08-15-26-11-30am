# Track 19.21 · Permission / Ownership Model

**Doctrine:** HR owns every lane. Safety and Asset Administrator each own one lane operationally.

## Roles

| Role | System role identifier | Lanes accessible | Approval authority |
|---|---|---|---|
| **HR** | `hr` | All 4 lanes | All 4 lanes |
| **Admin / Super Admin** | `admin` | All 4 lanes | All 4 lanes |
| **Safety** | `safety` | `safety` | `safety` |
| **Asset Administrator** | `asset_admin` | `asset` | `asset` |
| **Field / Foreman / PM** | field roles | ❌ None | ❌ None |

## Enforcement

Enforced in `/app/backend/routes/employee_records.py` by two pure functions with hard-coded tables:

```python
LANE_APPROVERS = {
    "hr":               {"hr", "admin"},
    "safety":           {"safety", "hr", "admin"},
    "asset":            {"asset_admin", "hr", "admin"},
    "corporate_import": {"hr", "admin"},
}

def _actor_can_read_lane(actor, lane):
    role = actor["_actor"]
    if role in {"hr", "admin"}:
        return True   # HR + admin read every lane
    if role == "safety" and lane == "safety":
        return True
    if role == "asset_admin" and lane == "asset":
        return True
    return False
```

Both functions covered by dedicated lock tests:
- `test_hr_can_approve_every_lane`
- `test_admin_can_approve_every_lane`
- `test_safety_can_approve_only_safety_lane`
- `test_asset_admin_can_approve_only_asset_lane`
- `test_field_role_cannot_approve_any_lane`
- `test_hr_can_read_every_lane`
- `test_safety_can_only_read_safety_lane`
- `test_asset_admin_can_only_read_asset_lane`

## Route-level enforcement

Every endpoint under `/api/employee-records/*` uses the shared `make_require_safety_admin_or_pm` gate (from `routes/safety_portal/_deps.py`) — the same gate that protects the Incident Intelligence Engine and Safety Case Workspace. Non-authenticated callers receive `401 Safety, Admin, or PM login required`.

## Sensitive data safety

- No public routes. No anonymous access. No API-key overrides.
- Medical restrictions and RTW documentation live in the Safety lane; only Safety + HR + Admin can read them.
- Personnel documents (I-9 · W-4 · direct deposit) live in the HR lane; only HR + Admin can read them.
- Asset acknowledgments (issue / return / damaged / lost) live in the Asset lane; Asset Admin + HR + Admin can read.

## HR authority reserve

Because HR is in every lane's approver set, HR always retains ultimate authority to:
- Read any record across every lane
- Approve/reject any record
- Reassign any record between employees, record_types, or lanes
- View the full audit trail on any record

## Non-goals for Track 19.21

- Field-facing read access to internal historical records
- PM read access to internal HR records
- Delegation / temporary access
- Break-glass emergency access
- Multi-tenant scoping (single-tenant assumption preserved from prior tracks)
