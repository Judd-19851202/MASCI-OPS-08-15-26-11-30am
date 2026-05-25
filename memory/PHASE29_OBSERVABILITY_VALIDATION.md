# PHASE 29 · Observability Validation Plan (OPERATOR-OWNED)
## iter431 · 2026-05-25

## What's already in place (verified by Phase 28.2)
- Sentry SDK initialised (`backend/sentry_init.py`, `frontend/src/lib/sentryInit.js`)
- DSN-gated · PII scrubber drops every `*-Token` header + password fields
- `SentryOperationalTagsMiddleware` (`backend/sentry_tags.py`) auto-tags
  every event with: `portal · role · route · device · browser · language · tenant`
- Coarse UA classifier · no fingerprinting

## What this phase needs from the OPERATOR
Sentry tag validation requires a real production Sentry inbox + the
ability to trigger controlled failures. The agent cannot do either.

### 1. Backend controlled-failure tests
Run from a desktop browser, signed in as admin:

```bash
API_URL="https://mascidocs.com"
TOKEN=$(curl -s -X POST "$API_URL/api/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"password":"<admin-password>"}' | jq -r '.token')

# (a) intentional handled 500 — backend handler raises
curl -i -X GET "$API_URL/api/operational-attachments/_does_not_exist" \
  -H "X-Admin-Token: $TOKEN"

# (b) attachment fetch failure on a fake ID
curl -i -X GET "$API_URL/api/operational-attachments/00000000-0000-0000-0000-000000000000/file" \
  -H "X-Admin-Token: $TOKEN"

# (c) auth rejection
curl -i -X GET "$API_URL/api/admin/legacy-imports/audit"

# (d) malformed payload (4xx surface)
curl -i -X POST "$API_URL/api/admin/dls/day-1-debrief" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: $TOKEN" \
  -d '{"answers": "not-an-object"}'
```

### 2. Frontend controlled-failure tests
- Open DevTools console on `/admin` while signed in. Run:
  `throw new Error("PHASE29_OBSERVABILITY_TEST")` → Sentry frontend
  must capture it with the configured tags.
- On a phone, intentionally upload an oversized file (> 5 MB) — the
  attachment endpoint returns 4xx; Sentry frontend should attach the
  error with `device=ios|android`, `route=/api/operational-attachments/upload`.
- Force a passkey ceremony failure (cancel the WebAuthn prompt) — the
  frontend `lib/passkeys.js` rejects; Sentry should capture with
  `route=/api/passkeys/login/begin` or similar.

### 3. Verify EVERY event in Sentry carries:
- ☐ `portal`   (admin / dispatch / pm / shop / safety / hr / field / driver / public)
- ☐ `role`     (mirror of portal)
- ☐ `route`    (FastAPI route template · `/api/...` with `{import_id}` etc.)
- ☐ `device`   (ios / android / mac / windows / linux / unknown)
- ☐ `browser`  (safari / chrome / edge / firefox / unknown)
- ☐ `language` (en / es)
- ☐ `tenant`   (masci)

### 4. Verify NO PII appears:
- ☐ no admin token visible in any captured event body
- ☐ no MFA secret in any captured event
- ☐ no user email surfaced via Sentry user.id
- ☐ no raw password anywhere
- ☐ no R2 presigned URL captured in payload

## Pass / fail rule
- Any missing tag on any event → fix `sentry_tags.py` middleware in
  next phase before further work lands.
- Any PII leak → freeze production until the scrubber is patched.

## Output (operator-filled)
| Test            | Sentry event link | Tags OK? | PII OK? |
|-----------------|-------------------|----------|---------|
| handled 500     |                   | ☐        | ☐       |
| attachment 404  |                   | ☐        | ☐       |
| auth 401        |                   | ☐        | ☐       |
| body 422        |                   | ☐        | ☐       |
| frontend throw  |                   | ☐        | ☐       |
| upload too big  |                   | ☐        | ☐       |
| passkey cancel  |                   | ☐        | ☐       |
