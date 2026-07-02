# TRACK 19.25 · Asset Administrator Navigation Certification

## Asset Administrator surface
The Asset Administrator role is a **Shop portal user** with the `is_asset_admin` flag on their `shop_users` row. This is the actual role — not a generic "Shop user."

## Where Asset Admin naturally works
Shop Hub V2 at `/shop/hub_v2` (default `/shop` landing).

## New section (post-19.25) · "09 · Asset Administrator · Historical Records"
Three HubCard tiles:
1. **Asset Records Intake** → `/hr/historical-records/intake` (backend gate confines to Asset lane for shop tokens)
2. **Asset Records Queue** → `/hr/historical-records/queue`
3. **Bulk Historical Intake** → `/hr/historical-records/batches`

## Asset Administrator authority verified
- Backend gate: `make_employee_records_actor_gate` promotes to `asset_admin` role only when Shop token has `is_asset_admin=true` OR `"asset_admin" in u.get("roles", [])`
- `allowed_lanes_for_actor` returns `["asset"]` for Asset Admin
- Can intake / approve / reject / reassign Asset-lane records
- Can link employee + related_asset_id via existing intake fields
- Cannot mutate HR-lane or Safety-lane records
- Cannot generate HR-only or Safety-only export packages (`PACKAGE_LANE_GATE`)

## Record types available in Asset lane (from `LANE_RECORD_TYPES["asset"]`)
- ppe_issued · ppe_returned
- tool_issued · tool_returned
- phone_issued · tablet_issued · ipad_issued
- survey_equipment_issued · pipe_laser_issued · rotating_laser_issued
- asset_acknowledgement
- damaged_asset · lost_asset · replacement_record

The intake page dropdown swaps to these when Asset lane is picked (existing behavior — retained).

**Verdict:** GO. Asset Administrator has a first-class section on the Shop hub. Server gate prevents cross-lane leaks even if a non-admin shop user clicks through.
