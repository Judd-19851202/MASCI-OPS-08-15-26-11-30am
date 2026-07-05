# TRACK 22.4b-followup · Preview Validation Identities

**Status**: 🟢 GO · 2026-07-05
**Branch/Commit**: `main` · `5af88fdf`
**Environment**: PREVIEW · `APP_ENV=preview` · `ENABLE_PREVIEW_VALIDATION_IDENTITIES=true`
**Motive protection**: 🛡️ UNCHANGED · zero Motive touch.

---

## What was built

A **preview-only** control plane for minting short-lived role tokens
used to unblock role-scoped workflow verification without weakening
production RBAC.

### Backend

- `/app/backend/routes/preview_validation_identities.py` — new
  module. Endpoints under `/api/admin/preview-validation-identities/*`:
  - `GET  /env` — env marker + availability
  - `GET  /` — list active (or all with `include_inactive=true`)
  - `POST /mint` — mint a short-lived token
  - `POST /{id}/revoke` — instant revoke
  - `POST /introspect` — verify a token (never returns raw jti)
  - `GET  /audit` — audit log
- Token format: `PVI.<jti>.<hmac_sha256(jti|role, ADMIN_HMAC_SECRET)>`.
  The `PVI.` prefix is reserved — existing role guards look up their
  tokens in per-role user tables and simply do not find `PVI.*` jtis,
  so the format is inherently isolated.
- Signing uses the existing `ADMIN_HMAC_SECRET`. Bumping
  `ADMIN_SESSION_EPOCH` invalidates every validation token in one move
  (no new key rotation surface introduced).
- Collections:
  - `preview_validation_identities` — metadata (never token values)
  - `preview_validation_identity_audit` — mint/revoke event log

### Frontend

- `/app/frontend/src/pages/admin/PreviewValidationIdentities.jsx` —
  new admin page at `/admin/preview-validation-identities`.
- Big red banner: *"PREVIEW VALIDATION IDENTITIES — NOT PRODUCTION
  CREDENTIALS."*
- Mint form (role picker, purpose text field, TTL numeric input capped
  at 1440 min).
- Post-mint modal shows the token **once** with Copy + Close.
- Active identities table with per-row Revoke button.
- Live audit log.
- If backend returns 404 (production or flag missing), the page
  renders a `ShieldOff` "disabled in this environment" panel instead of
  a form.
- Sidebar entry added to `AdminShell.jsx`.

### Env

- `/app/backend/.env` gained `ENABLE_PREVIEW_VALIDATION_IDENTITIES=true`.
- Production is protected by BOTH conditions (env-marker must be one of
  `preview/staging/development/dev/test` AND flag must be true).

### Tests

- `/app/backend/tests/test_track_22_4b_followup_validation_identities.py` — **13/13 pass**
  - env endpoint reports preview available
  - production marker hard-disables module (monkeypatch)
  - anonymous rejected on 5 endpoints (parametrized)
  - mint→introspect→revoke→post-revoke-introspect lifecycle
  - invalid role rejected (400)
  - TTL > 24 h rejected (400)
  - list never returns raw token
  - audit never returns raw token
  - forged signature rejected (HMAC integrity)

---

## Production safety

| Guard | Status | Evidence |
|---|---|---|
| Hard-disabled in production | ✅ | `_is_production()` returns True on `APP_ENV=production` → `is_preview_validation_available()` returns False → endpoints return 404 |
| Enable flag required | ✅ | Missing `ENABLE_PREVIEW_VALIDATION_IDENTITIES=true` returns 404 |
| Super-admin only | ✅ | All endpoints use `require_admin_strict` |
| Token expiry | ✅ | Max TTL 24h · default 4h · rejected on submission |
| Instant revoke | ✅ | `revoked_at` timestamp + status transition |
| Audit trail | ✅ | Every mint/revoke row in `preview_validation_identity_audit` |
| Raw token logging | ✅ | Token returned **only once** at mint; never in list, audit, or introspect responses |
| Motive touched | ✅ | Zero Motive code paths touched |

---

## Role token support

| Role | Mint | Verify | Notes |
|---|---|---|---|
| admin | ✅ | ✅ | infrastructure works |
| pm | ✅ | ✅ | infrastructure works |
| safety | ✅ | ✅ | infrastructure works |
| hr | ✅ | ✅ | infrastructure works |
| shop | ✅ | ✅ | infrastructure works |
| dispatch | ✅ | ✅ | infrastructure works |
| driver | ✅ | ✅ | infrastructure works |
| field_leadership | ✅ | ✅ | infrastructure works |

**All 8 roles supported at the control-plane level.** Each mint returns
a valid signed token, and `POST /introspect` verifies it with
`expected_role` matching.

### Deferred: guard wiring

This track ships the CONTROL PLANE (mint / verify / revoke / audit).
Wiring `verify_validation_token(...)` into each per-role guard so a
Safety validation token actually reaches `@require_safety` endpoints
is a follow-up track (Safety / HR / Driver / etc.). That work touches
7 different auth modules and is out of scope for this control-plane
delivery. Documented honestly.

---

## Workflow blockers status

| Blocker | Before | After | Notes |
|---|---|---|---|
| B-01 HR identity | BLOCKED (no HR token) | READY (mint) · WAITING (guard wire) | Track 22.4b-followup-HR needs to plumb `verify_validation_token` into `require_hr` |
| B-02 Safety Meeting subject/company | BLOCKED (no Safety token) | READY (mint) · WAITING (guard wire) | Track 22.4b-followup-Safety |
| B-04 Trench Repair role guards | BLOCKED (no Safety+Shop tokens) | READY (mint) · WAITING (guard wire) | Track 22.4b-followup-Safety |
| B-06 Driver / DVIR | BLOCKED (no Driver token) | READY (mint) · WAITING (guard wire) | Track 22.4b-followup-Driver |

---

## Deployment verdict

**READY**. Production guard is hard-locked: the endpoints return 404
unless BOTH the env-marker is preview-class AND the enable flag is
true. Test proves the guard cannot be bypassed even with the flag set.

## Feature freeze

**LIFT for validation infrastructure**. Track 22.4b's freeze was on new
dashboards and portals; this is a control-plane admin utility scoped
strictly to preview and hard-disabled in production, not a product
feature. It is exactly the kind of tool the freeze allowed.

## Next tracks

1. **Track 22.4b-followup-Safety** — plumb `verify_validation_token` into
   `require_safety` and exercise B-02 + B-04.
2. **Track 22.4b-followup-Driver** — plumb into `require_driver` (or
   `driver_sessions.py`) and exercise B-06.
3. **Track 22.4b-followup-HR** — plumb into `require_hr` and exercise B-01.
4. **Track 22.4c** — Mobile Responsiveness Sweep.
