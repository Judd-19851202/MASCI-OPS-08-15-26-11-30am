# Security Census

## Secrets
- Public-repo `git ls-files` grep for `.env` / `credentials.json` / `.pem` / `SEALED*` / `SECRETS_*`: **only match is the secret-scanner test file itself.** Zero real secrets committed.
- Track 15.80 secret-file pattern lock: **ACTIVE** and preserved in Track 20.9 `.gitignore` rewrite.

## Environment variables
- Backend: all read via `os.environ.get(...)`, no defaults baked in for auth/URLs.
- Frontend: all via `process.env.REACT_APP_BACKEND_URL`.

## CORS
- `allow_credentials=True` + regex `^https://((www\.)?mascidocs\.com|.*\.emergent(agent\.com|\.host)|.*\.preview\.emergentagent\.com)$` + prod explicit list.
- `allow_methods=["*"]` / `allow_headers=["*"]` — intentional (7 portal-token headers, 6+ HTTP methods across 400+ routes). Phase-2 tightening plan documented (Track 20.9).

## Rate limits
- `rate_limit_public_post` on `/api/daily-reports`, `/api/employee-records/uploads`, `/api/auth/multi-login`, etc.

## Tokens
- Opaque directory session tokens (not JWT), revocable via `user_directory_sessions`.
- MFA (TOTP) for super-admin (Track iter375). Passkeys (WebAuthn) for optional cohort (Track iter422).

## Audit logs
- Trust-spine (`trust_spine_events`) — universal event backbone.
- `audit_events` — login events.
- `admin_operations_audit` — mutation events.

## Classification
- **KEEP** — every security surface.
- **FIX** — 0.

## Zero drift
Zero permission or gate change in current release cluster (20.6B → 21.0).
