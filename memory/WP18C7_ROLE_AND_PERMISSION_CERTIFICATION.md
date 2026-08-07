# WP18C7 Role and Permission Certification

## PM
- Auth flow: `/api/pm/login`
- Can read scoped workspace.
- Can create/update manual commitments.
- Can capture forecast snapshots.

## Executive/Admin
- Auth flow: `/api/auth/multi-login` with `portal=admin`
- Requires `X-Admin-Token` and `X-Directory-Token`.
- Read-only governed workspace.

## Field Leadership
- Auth flow: `/api/field-leadership/portal/login`
- Route additionally enforces rostered project membership before returning workspace.

## Runtime proof
- PM/Admin/FL endpoint PASS results: `/app/test_reports/iteration_155.json`
