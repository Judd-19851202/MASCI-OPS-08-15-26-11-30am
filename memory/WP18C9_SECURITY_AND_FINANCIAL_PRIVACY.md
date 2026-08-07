# WP18C9 Security and Financial Privacy

Date: 2026-08-07  
Status: PASS

## Privacy Controls
- Admin/executive portfolio view uses admin/directory tokens and returns the governed full portfolio only to authorized users.
- PM portfolio view uses PM tokens and returns only governed PM scope.
- Unauthenticated access to admin and PM C9 routes is denied or redirected.

## Financial Boundaries
- Admin/executive users can see full scoped financial rollups.
- PM users can see only the assigned-project financial view delivered by their scope key.
- CSV exports follow the same route-level authorization as the screen and API responses.

## Sensitive Data Handling
- No secrets are exposed by the C9 UI or CSV output.
- Portfolio delivery excludes Mongo `_id` values from responses.
- Raw internal supporting-record IDs were removed from visible operator-facing copy and replaced by plain-language timestamps.
