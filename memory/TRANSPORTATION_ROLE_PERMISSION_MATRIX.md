# TRANSPORTATION ROLE PERMISSION MATRIX

Date: 2026-08-11

| Surface | Role posture | Rule |
|---|---|---|
| `/api/admin/transportation/audit-timeline` | ADMIN-STRICT | Admin-only governance timeline. Not operator-visible authority. |
| `/api/admin/transportation/hr-sync` | ADMIN-STRICT | Admin-only HR sync control. No dispatch/operator write access. |
| `/api/admin/transportation/email-routes` | ADMIN-STRICT | Admin-only route governance and notification control. |
| Transportation operator views | ROLE-SCOPED | Visible operator workflows must be usable from their intended portal surface. |
| Hidden admin-only controls | NOT ACCEPTANCE EVIDENCE | Hidden does not satisfy transportation acceptance. |

## Doctrine

- VISIBLE = USABLE
- ADMIN-STRICT endpoints are governance-owned and may not be presented as operator-ready.
- Role scope remains bounded; no auth/RBAC weakening is permitted under release freeze.