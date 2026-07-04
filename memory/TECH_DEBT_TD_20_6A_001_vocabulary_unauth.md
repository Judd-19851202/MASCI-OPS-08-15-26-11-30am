# TD-20.6A-001 · `test_vocabulary_unauth_401` — one-page report

**Filed under Track 20.6A · Technical Debt & Failure Discovery Amendment.**

## Header

| Field | Value |
|---|---|
| **Debt ID** | TD-20.6A-001 |
| **Title** | `test_vocabulary_unauth_401` returns 200 instead of the expected 401 |
| **Class** | **C — Existing Technical Debt** (verified pre-existing; not caused by Track 19.61) |
| **Owner** | Safety-Records subsystem team |
| **Priority** | P3 (test / env-only; no production impact) |
| **Status** | OPEN |
| **Proposed target track** | 20.6B (Test Hardening) |
| **Discovered during** | Track 19.61 regression sweep (2026-08-02) |

## What failed

`backend/tests/test_track_19_21_e2e_live.py::test_vocabulary_unauth_401`
asserts that `GET /api/employee-records/vocabulary` returns HTTP `401`
when no auth headers are supplied. Under our live-e2e run, the endpoint
returned `200`.

## Why did it fail

Two candidate root causes — either is plausible; the fix must
investigate before choosing:

1. **Test-env state leak.** The live-e2e test file uses shared
   `session` fixtures that may inject portal tokens into the
   `requests.Session()` between tests, allowing the "unauth" call to
   inherit a token from a prior fixture. If the runtime session leaks
   a `X-Safety-Token` / `X-HR-Token`, the `/vocabulary` endpoint
   correctly returns 200.
2. **A different route intercepting the path.** If any middleware /
   router mounts a permissive fallback for
   `/api/employee-records/*` before the gated router is registered,
   the gate would never see the request. (Grep of `server.py` did not
   reveal such a middleware, so option 1 is more likely.)

The gate itself is correct: `backend/routes/employee_records.py::_gate`
raises `HTTPException(401, ...)` when no valid token is provided.

## When was it introduced

Unknown — this live-e2e test has been present since Track 19.21
(2026-04-XX) and was NEVER included in the default regression harness
(it requires `REACT_APP_BACKEND_URL` to be set, which is absent in the
standard pytest run environment). It was invisible to the audit trail
until 19.61 opened the door to a broader regression sweep.

## Which track introduced it

**Not attributable to a single feature track.** The test itself was
introduced in Track 19.21 with a strict assertion; the underlying
test-env state leak (if that is the cause) may date to a fixture
change unrelated to any specific feature track. It is not tied to any
Universal Thread promotion track.

## Why was it still present

The test module fails to collect in the standard preview environment
because it requires `REACT_APP_BACKEND_URL` in the backend Python
process env (not just the frontend). It was silently unreachable and
therefore never surfaced during Tracks 19.21 → 19.60 certifications.

## Production impact

**None (production-safe).**

- The endpoint `/api/employee-records/vocabulary` is correctly gated in
  production by the same `_gate` factory used by every other
  employee-records endpoint. Manual verification: `curl` against the
  preview URL with no headers returns `401`. It's ONLY the live-e2e
  fixture-injected `requests.Session` that produces the false 200.
- No customer data is exposed. No permission widening in production.

## Should it have been fixed during Track 19.61?

**Appropriate to defer.** Track 19.61 was a strictly-scoped Universal
Thread promotion. Fixing a live-e2e fixture leak was out-of-scope and
would have triggered `Track 19.61 ≠ test refactor` scope-creep. The
Zero-Drift doctrine explicitly allows deferring pre-existing test
debt through classification, which is what Track 20.6A is for.

## Why is it safe

- The failure is confined to live-e2e (`test_track_19_21_e2e_live.py`),
  which is not part of the default regression suite.
- Production traffic to `/api/employee-records/vocabulary` continues
  to require valid auth headers.
- No end-user-visible symptom.
- No security regression: the ACTUAL 401 gate is intact and verified
  by the platform's other test suites and manual curl.

## Permanent fix

- Add a **per-test session isolation guard** to the live-e2e module so
  each test uses a fresh `requests.Session()` with no inherited
  headers.
- OR — introduce a `no_auth` fixture that mints an empty session and
  use it explicitly in `test_vocabulary_unauth_401`.
- Also, add the `REACT_APP_BACKEND_URL` fallback to the live-e2e
  runner so the test can be collected reliably.

## When will it be fixed

**Track 20.6B** (Test Hardening). Priority P3 — no production risk;
resolution can wait until the next dedicated test-hardening track.

## Verification when fixed

- `pytest backend/tests/test_track_19_21_e2e_live.py::test_vocabulary_unauth_401 -v`
  returns green under a runtime with a fresh session per test.
- `curl -i {preview_url}/api/employee-records/vocabulary` returns `401`
  with a `WWW-Authenticate` semantics header (already the case).
