# TRACK 22.1 · Module Extraction Report

## Extracted this session (2 modules · 58 lines moved)

### `backend/lib/health_probes.py` · 44 lines

- Contents: `_probe_health()`, `_probe_healthz()`, `attach_health_probes(app)`.
- Registration: `attach_health_probes(app)` replaces two inline `@app.get(...)` decorators in server.py.
- Parity: 2 whitelisted `endpoint_qualname` moves; every other route surface identical.
- Runtime probe: `curl http://localhost:8001/health` and `/healthz` return the exact same JSON before and after.

### `backend/lib/rate_limiting.py` · 96 lines

- Contents: `_RATE_LOCK`, `_PUBLIC_POST_BUCKETS`, `_LOGIN_FAIL_BUCKETS`, `PUBLIC_POST_LIMIT_PER_HOUR`, `LOGIN_MAX_FAILS_PER_WINDOW`, `LOGIN_LOCKOUT_SECONDS`, `_client_ip`, `rate_limit_public_post`, `_check_login_lockout`, `_record_login_fail`, `_reset_login_fails`.
- Registration: server.py `from lib.rate_limiting import (...)` re-exports every name.
- Parity: 0 diffs in any route's `dependency_chain` (proving all 5 `Depends(rate_limit_public_post)` sites still resolve to the same callable identity via the re-imported binding).

## Deferred candidates (with target track + parity gate)

| # | Candidate | Reason | Target Track | Parity Gate |
|---|---|---|---|---|
| 1 | `_dispatch_auto_email` + `recipients_for_record_async` + email helpers | Must not fire before the Resend SDK monkey-patch installs at server import time (Track 21.2E). Any reordering risks a live-email window. | 22.1b | Boot the app in a subprocess with an extracted dispatcher; assert `resend.Emails.send` was replaced by `_blocked_send` BEFORE the dispatcher's first send attempt. Add HTTP smoke that POSTs a `TEST_` daily report and asserts `id=blocked_by_email_safety_mode`. |
| 2 | Auth helpers (`require_admin_dep`, `_actor_dep`, portal-token helpers) | 355+ endpoints depend on these via `Depends()`. Any drift = silent permission drift. | 22.1e | HTTP fixture regression across all 7 portals + JSON dependency-chain diff = 0. |
| 3 | Scheduler bootstrap (51 startup handlers) | Registration order matters; some handlers require index initialisation before task start. | 22.1c | `startup_handlers` list byte-equal + successful boot with `SCHEDULER_ENABLED=true` in a sandbox. |
| 4 | `api_router.include_router(...)` calls (~158) | Order matters only where two routers claim the same path. Track 21.0 census showed 0 dupes today. | 22.1d | Full route set parity (already established by Track 22.1's harness). |
| 5 | JWT + MFA helpers | Closed over env-driven `JWT_SECRET`, `MFA_ENCRYPTION_KEY`, `db` globals. | 22.1e | HTTP login-flow smoke + JWT decode/encode round-trip parity. |
| 6 | Pydantic model definitions (~350) | Currently inline; low risk but touches many `response_model=` sites. | 22.1f | `route.response_model` parity (already captured by Track 22.1 harness). |
| 7 | Public-workflow entrypoints (Daily Report submitter, JHA submitter, Calculators) | Certified public surface with explicit projection allow-lists (Track OMEGA). Extraction requires re-verifying projection allow-list registration. | 22.1g | Live HTTP smoke against every public endpoint with 0-auth. |
| 8 | CORS middleware installation | One `add_middleware(...)` call; refactor-only, zero improvement. | Not scheduled | — |

## Extractions rejected (would violate a Zero-Drift rule)

| Candidate | Rejection reason |
|---|---|
| Merging `session_timeout.py` and `admin_hardening.py` | Both are pre-existing extracted modules with independent lifecycle. Merging is a cosmetic move with no operational benefit and risks losing pointer identity for `install_session_timeout_middleware`. |
| Rewriting `_dispatch_auto_email` to use `resend.Client(...)` | Would deviate from the SDK-level monkey-patch surface targeted by Track 21.2E. Any deviation puts the email-safety envelope at risk. |
| Auto-generating router registrations from a filesystem scan | Would eliminate the last-registered wins semantics currently in place for legacy compatibility. High risk, zero user-facing benefit. |
| Removing `app.state.ready` gate | The gate exists specifically to prevent the 2026-06-02 production cold-pod race. Removing without replacement would re-open that regression window. |

## Zero-drift verdict

🟢 **CERTIFIED for the two extractions made.** All others explicitly deferred with a documented target track and a documented parity gate.
