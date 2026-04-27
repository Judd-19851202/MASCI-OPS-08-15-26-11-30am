# Auth Testing Playbook — MASCI Safety Hub

Phase 1 of the Basecamp-style `/app` section ships per-user JWT auth. This file is the testing playbook for that system.

## Seeded Users (on first backend boot)

| Email | Password | Role | must_change_password |
|---|---|---|---|
| david.jewett@mascigc.com | Welcome2MASCI! | owner | true |
| chris.wright@mascigc.com | Welcome2MASCI! | owner | true |
| ramon.rodriguez@mascigc.com | Welcome2MASCI! | owner | true |
| jaymn.judd@mascigc.com | Welcome2MASCI! | owner | true |
| safety@mascigc.com | Welcome2MASCI! | admin | true |

After first login each user is prompted to change their password. Passwords must be ≥ 10 chars.

## Auth endpoints

- `POST /api/auth/login` — body `{email, password}` → sets httpOnly `access_token` + `refresh_token` cookies, returns `{user}`.
- `POST /api/auth/logout` — clears cookies.
- `GET /api/auth/me` — returns current user (requires valid access token cookie or `Authorization: Bearer <jwt>` header).
- `POST /api/auth/change-password` — body `{current_password, new_password}`, auth required. Clears `must_change_password` flag.
- `POST /api/auth/refresh` — reads refresh cookie, issues new access cookie.

## Admin user management

- `GET /api/users` — list all users (admin/owner role).
- `POST /api/users` — create new user (admin/owner role). Body `{email, name, role, password}`. Role must be one of `owner`, `admin`, `member`. New users are created with `must_change_password=true`.
- `PUT /api/users/{user_id}` — update user (admin/owner role).
- `DELETE /api/users/{user_id}` — deactivate user (soft delete, sets `is_active=false`).
- `POST /api/users/{user_id}/reset-password` — admin generates a new temp password and forces change on next login.

## Projects endpoints (read-only in Phase 1)

- `GET /api/projects` — list projects current user is a member of.
- `GET /api/projects/{project_id}` — project details + member list.

## Legacy Admin Coexistence

During the 30-day migration window, the existing `X-Admin-Token` header (from `ADMIN_PASSWORD`) continues to work on all endpoints that use `require_admin_or_jwt`. JWT tokens from users with role `owner` or `admin` also satisfy `require_admin_or_jwt`. Plain members can access `/api/users/me` and `/api/projects/*` only.

## Quick curl tests

```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)

# 1. Login (sets cookies.txt)
curl -c /tmp/cookies.txt -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"jaymn.judd@mascigc.com","password":"Welcome2MASCI!"}'

# 2. Me with cookie
curl -b /tmp/cookies.txt "$API_URL/api/auth/me"

# 3. List projects
curl -b /tmp/cookies.txt "$API_URL/api/projects"

# 4. Change password (first login flow)
curl -b /tmp/cookies.txt -X POST "$API_URL/api/auth/change-password" \
  -H "Content-Type: application/json" \
  -d '{"current_password":"Welcome2MASCI!","new_password":"NewLongerPassword123"}'
```
