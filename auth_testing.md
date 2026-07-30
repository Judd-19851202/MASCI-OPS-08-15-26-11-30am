# Admin Auth Regression Notes

Step 1: Login through the directory-based multi-login flow
```
POST /api/auth/multi-login
{
  "email": "ops8-admin-only-preview@example.com",
  "password": "AdminOnlyOps8!"
}
```

Step 2: Extract the two values required for Admin API validation
- `portal_tokens.admin` → send as `X-Admin-Token`
- `session_token` → send as `X-Directory-Token`

Step 3: Validate the Admin-protected APIs
```
GET /api/admin/check
GET /api/qaqc-inspections
GET /api/admin/equipment-master/status
GET /api/meetings?limit=2
GET /api/trench-safety/excavations?limit=2
GET /api/job-photos?limit=2
```

Expected result: all Admin checks above return `200` when both headers are present.
