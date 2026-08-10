# Authentication Testing Playbook

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

## PRE-C10 current logout closure scope

- Verify compact authenticated home-session treatment on `/` when a portal session exists.
- Verify logout sends the operator to public home `/`, not a login form.
- Verify tokens are cleared and browser back/refresh do not resurrect privileged state.
- Active role denominator in this batch: Admin, PM, HR, Dispatch, Safety, Shop, Leadership.

## PRE-C10 public/protected boundary scope

- Public field and safety workflows must stay signed-out with zero session-expired UI.
- `/api/training/packet.pdf?track=hr` must require `X-HR-Token` or `X-Admin-Token`.
- Field Leadership training sign-in CTAs must route to `/field-leadership/portal/login`.
- Unsupported packet tracks (for example `leadership`) must not expose a broken download path.
- Anonymous-safe lookup retries must preserve the public lookup endpoint contract.