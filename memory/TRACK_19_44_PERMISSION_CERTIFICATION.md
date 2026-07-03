# TRACK 19.44 · Permission Certification

| Product | Permission | Rationale |
|---|---|---|
| `training_intelligence` | `admin_only` | Training data mixes HR-sensitive certifications with employee records. Admin gate only. |
| `project_intelligence` | `admin_only` | Company-wide project rollup — executive visibility only. Future PM-scoped variant possible under a separate product ID. |

Both flow through the Track 19.41 auth-fixed dependency:
- Safety token (`X-Safety-Token`) → HTTP 403 (both admin_only).
- Admin token (`X-Admin-Token`) → HTTP 200.
- Missing / invalid → HTTP 401.

## Future

- PM-scoped Project Intelligence — could be added as `project_intelligence_pm_scoped` with `safety_or_admin` gate, filtering the aggregator by the caller's project scope. Not required for Track 19.44 · deferred.
