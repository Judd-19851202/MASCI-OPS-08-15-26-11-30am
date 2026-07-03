# TRACK 19.60 · Permission Certification

## Auth surface
- Route wrapped by `A(...)` = `RequireAdmin`. Same envelope as every other admin-owned page.
- Page-level: `isAdmin()` → `<AccessDenied attemptedPortal="admin" />` otherwise.
- HTTP requests carry the Admin token via `X-Admin-Token` for the employee-records call. The public `/api/suppliers` endpoint is name-only and safe to fetch without a token.

## What each role receives
| Role                | Vendor thread access | Vendor documents in this track |
|---------------------|:--------------------:|:------------------------------:|
| Admin (super)       | ✅ Full              | ✅ Full                        |
| HR                  | ❌ (Admin-only route)| ❌ (Track 20.4 doctrine — role-lens deferred) |
| PM                  | ❌                   | ❌                             |
| Safety              | ❌                   | ❌                             |
| Shop                | ❌                   | ❌                             |
| Fleet               | ❌                   | ❌                             |
| Dispatch            | ❌                   | ❌                             |
| Field / Public      | ❌                   | ❌                             |

**Rationale:** Track 20.4 explicitly instructed us to keep the initial route Admin-owned. Consumer-role lenses (PM / Safety / Shop / Fleet / Dispatch) are deferred to a later track. This track does not create any PM / Safety / Shop / Fleet / Dispatch route — asserted by `test_thread_never_exposes_pm_safety_shop_paths`.

## Zero permission widening
The thread strictly inherits the existing Admin gate. HR/Admin already have full read access to the vendor lane of Historical Records (Track 19.59). No new endpoint. No new gate. No new role.

## Anonymous / field / public
- No public route.
- No unauthenticated document link — every deep-link into `/employee-records/records/{id}/file` is gated server-side.
- No vendor self-service.
