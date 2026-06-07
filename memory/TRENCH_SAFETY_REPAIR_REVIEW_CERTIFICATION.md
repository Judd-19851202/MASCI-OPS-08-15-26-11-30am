# Repair Review Certification

## Route
- `/safety/trench-safety/repair-review` (Safety Portal)
- `/admin/trench-safety/repair-review` (Admin Portal mirror)

## Component
`SafetyRepairReview` in `TrenchSafetyOpsCenter.jsx`.

## Required Views (per directive)
| View | Filter | Status |
|---|---|---|
| Open Repairs | `all` | ✅ |
| Awaiting Verification | `awaiting` (status=Completed + requires_reinspection=true) | ✅ |
| Critical Repairs | `critical` (severity_at_creation=Critical) | ✅ |
| Vendor Repairs | `vendor` (repair_kind=Vendor Repair) | ✅ |
| Completed Repairs | `completed` | ✅ |
| Closed Repairs | `closed` (include_closed=true) | ✅ |

## Required Actions
| Action | Implementation |
|---|---|
| Review Repair | Click row → opens Asset Detail in same portal |
| Approve Repair | `POST /repairs/{id}/verify` with `reinspection_passed=true` — releases Inspection Hold via existing engine |
| Reject Repair | Same endpoint with `reinspection_passed=false` — repair returns to Shop |
| Request Additional Repair | "Return to Shop" via Reject decision + notes |
| Return To Shop | Reject path |
| Require Reinspection | Inherited from repair model `requires_reinspection` |
| Release Inspection Hold | Approve path triggers `clear_hold` for the Inspection Hold (existing engine) |
| Maintain Safety Hold | Engine never auto-clears Safety Holds — they require manual Safety action on Asset Detail |
| Maintain Certification Hold | Same — engine driven by cert expiry, not by repair verification |

## Non-negotiable
The Verify dialog explicitly displays:
> "Repair Complete does not mean Safe To Use. Verification is what releases the Inspection Hold. Safety Holds and Certification Holds are never auto-cleared."

This is rendered every time a Safety user opens the dialog. There is no UI path that bypasses this banner.

## Audit
Every verify call writes an `audit_events` row via the existing engine. The notification fanout from Phase 7.5C fires `trench_safety.asset_returned_to_service` when the verify call clears the last active hold.

## Verdict
🟢 PASS — Production-ready.
