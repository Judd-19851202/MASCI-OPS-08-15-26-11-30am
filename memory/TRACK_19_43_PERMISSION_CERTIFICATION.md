# TRACK 19.43 · Permission Certification

| Product | Permission | Rationale |
|---|---|---|
| `fleet_intelligence` | `safety_or_admin` | Safety + Fleet Admin + Directory Admin |
| `hr_intelligence` | `admin_only` | HR data sensitivity — admin gate only |

Both products flow through the Track 19.41 auth-fixed dependency:
- Safety token (`X-Safety-Token`) — validates via `safety_users.is_valid_safety_user_token_async`.
- Admin token (`X-Admin-Token`) — validates via `_is_valid_directory_admin_token_async`.
- Missing / invalid → HTTP 401.
- Safety on admin_only → HTTP 403.
- Unimplemented product dispatch → HTTP 501.
- Unknown product → HTTP 404.

## Broader HR access (deferred)

Group-based ACL (e.g., specific HR users viewing `hr_intelligence` without directory-admin token) is deferred to a later track. Today only directory admins can preview/dispatch HR Intelligence. Add HR users into the directory admin roster (Track 15.32+) if they need engine access.
