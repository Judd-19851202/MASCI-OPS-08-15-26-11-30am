# TRACK 19.40 · PERMISSION CERTIFICATION

Every product declares `permission_role` at registration. The route layer enforces:
- `safety_or_admin` — passes the existing `make_require_safety_or_admin` gate.
- `admin_only` — same gate, but additionally requires `actor is True` (admin bypass) at route time; Safety-only callers get 403.

Live 401 verified for both `/products` and `/{id}/preview` endpoints without any token.

## Enforcement summary
| Product | Route | Actor | Result |
|---|---|---|---|
| safety_morning_digest | preview / dispatch | Safety | ✅ allowed |
| safety_morning_digest | preview / dispatch | Admin | ✅ allowed |
| executive_operations_brief | preview / dispatch | Safety | ❌ 403 |
| executive_operations_brief | preview / dispatch | Admin | ✅ allowed |
| any product | any route | PM / Field / Public | ❌ 401 |

Contract-registered products refuse dispatch with 501 (`aggregator_not_implemented`) before any permission-sensitive code runs — the check is defense in depth.
