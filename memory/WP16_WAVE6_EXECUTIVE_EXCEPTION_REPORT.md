# WP16 Wave 6 — Executive Exception Report

Date: 2026-07-31
Wave: 6 — Dispatch & Transportation
Status: RESOLVED / CLOSED

## Exception trigger

Continuous certification stop condition was triggered by `WP16-W6-001` during Wave 6 inspection.

That stop condition is now cleared.

## Blocking issue

- **Issue ID:** `WP16-W6-001`
- **Surface:** `W6-008` Transportation wrapper → dispatch cleanup branch
- **Final classification:** **Shared mixed-session auth gate defect**

## Exact failure point

The failing browser path was not the cleanup data composer itself. The blocker was the shared session-timeout/auth lifecycle when multiple portal tokens were present on the same request.

### Verified failure chain

1. A valid Dispatch user reached `/transportation-operations/intelligence/cleanup`.
2. The browser also carried stale `X-Admin-Token` / `X-Directory-Token` values from prior portal activity.
3. The pre-route session-timeout middleware selected the stale higher-precedence admin token first.
4. Middleware returned `401 session_not_active` before the shared Dispatch-or-Admin route guard could fall back to the still-valid Dispatch token.
5. Cleanup data never reached a successful settled render path for the mixed-session browser case.

## Smallest safe repair applied

### Backend

- `backend/session_timeout.py`
  - preserved precedence ordering
  - changed middleware validation to iterate all presented known portal tokens in order
  - request now proceeds when **any** supplied portal token is active
  - route-level authorization still remains the final authority
- `backend/server.py`
  - removed temporary Wave 6 forensic trace logging from `_require_dispatch_or_admin`

### Test coverage

- `backend/tests/test_iter186b_session_timeout_middleware.py`
  - added regression coverage for: stale higher-tier token + active lower-tier Dispatch token

## Verification evidence

### Positive / blocker-case verification

Live backend verification on preview:

1. valid Dispatch token only → `200`
2. valid Dispatch token + stale invalid `X-Admin-Token` → `200`
3. valid Dispatch token + stale invalid `X-Admin-Token` + stale invalid `X-Directory-Token` → `200`

### Negative / regression verification

4. no auth token → `401`
5. Dispatch token on stricter admin-only route `/api/admin/transportation/intelligence/recommendations` → `401`

### Direct browser verification

Seeded browser session with:

- valid Dispatch token
- stale invalid admin token
- stale invalid directory token

Result:

- `/transportation-operations/intelligence/cleanup` rendered successfully
- cleanup experience settled successfully in `29.1s`
- top cleanup card rendered with title: `Carrier packet needs correction`

## Disposition

- `WP16-W6-001` → **VERIFIED_CLOSED**
- Wave 6 stop condition → **removed**
- Wave 6 → **EXECUTIVE LOCKED**

## Continuation decision

Wave 6 no longer blocks the program. Continuous certification resumed immediately after closure and Wave 7 inventory kickoff has started.