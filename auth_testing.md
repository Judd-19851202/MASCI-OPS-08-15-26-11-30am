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
GET /api/equipment-inspections
GET /api/meetings?limit=2
GET /api/trench-safety/excavations?limit=2
GET /api/job-photos?limit=2
```

Expected result: all Admin checks above return `200` when both headers are present.

## Generic Auth Testing Playbook

Step 1: MongoDB Verification
```
mongosh
use <database_name>
db.users.find({role: "admin"}).pretty()
db.users.findOne({role: "admin"}, {password_hash: 1})
```
Verify: bcrypt hash starts with `$2b$`, indexes exist on users.email (unique), login_attempts.identifier, password_reset_tokens.expires_at (TTL).

Step 2: API Testing
```
curl -c cookies.txt -X POST http://localhost:8001/api/auth/login -H "Content-Type: application/json" -d '{"email":"admin@example.com","password":"admin123"}'
cat cookies.txt
curl -b cookies.txt http://localhost:8001/api/auth/me
```

Login should return the user object and set `access_token` + `refresh_token` cookies. The `/me` call should return the same user using those cookies.
