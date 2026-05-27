# Driver Magic-Link Security Hardening — Certification

**Phase**: SIGMA-III · P0
**Iteration**: iter437
**Date**: 2026-02 (resumed under fork)
**Status**: 🟢 SHIPPED · CERTIFIED · PREVIEW VERIFIED

---

## Vulnerability Closed

Before this patch, `POST /api/dispatch/driver/magic-link` minted a usable
single-use driver magic token for **any string** the dispatch UI submitted
as `driver_id` — including:

- driver IDs that did not match any row in `employees`
- driver IDs of employees that had been disabled (`disabled=true`)
- driver IDs of employees flagged `active=false` (legacy roster purge)

A leaked or compromised dispatcher session could therefore have issued
valid driver sessions for **fictional** drivers — sessions which would
then be operationally indistinguishable from a real driver's mobile
device, capable of starting shifts, posting haul cycles, and writing to
the dispatch lifecycle collections.

---

## Patch Applied

### `/app/backend/driver_sessions.py`

- New exception `DriverIneligibleError(code, message)` (subclass of
  `ValueError`) — structured failure surface for the route to translate.
- New private helper `_validate_driver_eligibility(db, driver_id)`:
  - Returns the employee doc on success.
  - Raises `DriverIneligibleError("missing_driver_id", …)` if blank.
  - Raises `DriverIneligibleError("driver_not_found", …)` if no
    matching employee.
  - Raises `DriverIneligibleError("driver_disabled", …)` if
    `disabled=True`.
  - Raises `DriverIneligibleError("driver_inactive", …)` if
    `active=False`.
  - Does **NOT** require `is_driver=true` (intentional — the flag is
    inconsistently set on legacy employee rows and dispatch workflows
    legitimately issue magic links to non-CDL roles such as crew
    foremen).
- `issue_magic_link(...)` now calls `_validate_driver_eligibility`
  **before** any insert. No magic token is ever generated for an
  ineligible employee — the side-effect happens strictly after the
  gate passes.

### `/app/backend/routes/dispatch_driver.py`

- `issue_magic_link_route` catches `DriverIneligibleError` and
  translates to `HTTPException`:
  - `code == "driver_not_found"` → `404`
  - everything else (`missing_driver_id`, `driver_disabled`,
    `driver_inactive`) → `400`
  - Response body: `{"detail": {"code": "<code>", "message": "<…>"}}`
- Existing `MagicLinkRequest` Pydantic model already enforces
  `min_length=1` on `driver_id`, so blank payloads short-circuit at
  `422` before the helper runs (defense-in-depth).

### Strictness (operator-confirmed)

> Moderate — driver **MUST exist** AND **MUST NOT be disabled**.
> No `is_driver` flag check (legacy data uneven).

---

## Verification

### Unit + integration tests
`/app/backend/tests/test_iter437_magic_link_hardening.py` — **7/7 passed**
in 2.64s.

```
test_validate_rejects_missing_driver_id            PASSED
test_validate_rejects_unknown_driver               PASSED
test_validate_rejects_disabled_employee            PASSED
test_validate_accepts_real_employee                PASSED
test_magic_link_route_rejects_unknown_driver       PASSED
test_magic_link_route_rejects_empty_driver_id      PASSED
test_magic_link_route_accepts_real_employee        PASSED
```

### Live curl probes (preview backend)

```bash
# 1. Unknown driver_id → 404 with structured code
$ curl -X POST .../api/dispatch/driver/magic-link \
    -H "X-Dispatch-Token: <…>" \
    -d '{"driver_id":"definitely-not-real-id"}'
HTTP 404
{"detail":{"code":"driver_not_found","message":"no employee with id='definitely-not-real-id'"}}

# 2. Empty driver_id → 422 (pydantic boundary, never reaches helper)
$ curl … -d '{"driver_id":""}'
HTTP 422
{"detail":[{"type":"string_too_short","loc":["body","driver_id"],"msg":"String should have at least 1 character",…}]}

# 3. Disabled employee seeded with `disabled=true` → 400 with structured code
$ curl … -d '{"driver_id":"sigma3-curl-disabled"}'
HTTP 400
{"detail":{"code":"driver_disabled","message":"employee 'sigma3-curl-disabled' is disabled"}}

# 4. Real, enabled employee → 200 with magic_token
$ curl … -d '{"driver_id":"<real-id>"}'
HTTP 200
{"ok":true,"link_id":"…","magic_token":"…","expires_at":"…","url":"…"}
```

All four scenarios behave exactly as designed.

### Doctrine reaffirmed
- Zero new collections.
- Zero new env vars.
- Zero schema change on `employees`.
- Structured error codes (not stringly-typed messages) so the dispatch
  UI can distinguish failure modes without parsing English text.
- Negative gate runs BEFORE any DB write, so a probing attacker cannot
  use this endpoint to enumerate which `driver_id` strings produced
  side-effects vs which didn't.

---

## Files of reference

| File | Change |
| --- | --- |
| `/app/backend/driver_sessions.py` | `DriverIneligibleError` + `_validate_driver_eligibility` + gate in `issue_magic_link` |
| `/app/backend/routes/dispatch_driver.py` | Catch + translate to 404/400 with structured body |
| `/app/backend/tests/test_iter437_magic_link_hardening.py` | 4 unit + 3 HTTP integration tests |

---

## Threat surface remaining (informational, not blocking)

The patch closes the **issuance** path. The downstream paths
(`/session/exchange`, `validate_driver_session_token`,
`revoke_driver_session`) were already safe — they verify the session
row exists, HMAC matches, and `revoked_at` is null. A token issued for
a driver who is **later** disabled remains valid for the rest of its
TTL (default 14 h) by design (a foreman mid-shift should not be cut off
mid-cycle). If the operator wants live revocation on disable, that is a
**separate** Phase Sigma-III follow-up that we have **not** committed
to in this iteration.

# 🟢 P0 — Driver Magic-Link Security Hardening · CLOSED
