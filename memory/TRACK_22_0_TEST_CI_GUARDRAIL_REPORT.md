# TRACK 22.0 · Test / CI / Guardrail Report

## Current lock envelope (Track 20.6B → 22.0)

| Track | Suite | Count |
|---|---|---|
| 20.6B | Test hardening | 6 |
| 20.7 | Universal photo capture | 26 |
| 20.8 | Deployment certification | 12 |
| 20.9 | P1 cleanup | 8 |
| 21.0 | Platform census | 28 |
| 21.1 | Zero-defect remediation | 8 |
| 21.2E | Email safety incident closeout | 11 |
| 21.2E-1 | First-pass canonicalization | 6 |
| 21.2E-1 | Permanent payload guardrail | 15 |
| 21.3 | Remaining Class-C remediation | 12 |
| 22.0 | Platform excellence lock | 13 |
| **Total** | | **146** (Track 20.6B → 22.0, verified by pytest run) |

## Guardrails in place

| Guardrail | Trigger |
|---|---|
| ESLint 0-errors gate | Any React re-introduction of unescaped entities, unstable nested components, duplicate i18n keys, or empty catch blocks |
| Frontend build gate | Any webpack parse error (Track 21.1 caught this in the wild) |
| Email SDK-patch presence | Any deletion of the `if _EMAIL_SAFETY_MODE in (...)` branch |
| `_dispatch_auto_email` gate ordering | Any refactor that moves the strict-mode short-circuit after recipient lookup |
| TEST_ payload guardrail | Any commit that introduces a non-`TEST_` `project_name` / `job_name` literal in an HTTP-submitting test |
| No pytest.skip smuggling | Any pytest.skip within 600 chars of a non-TEST_ payload literal |
| No direct `import resend` in tests | Except the certified safety-mode unit test |
| CORS wildcard reintroduction | Any `allow_methods=["*"]` or `allow_headers=["*"]` in server.py |
| Preview `.env` retains `EMAIL_SAFETY_MODE=strict` | Any preview `.env` change that removes the safety mode |
| Non-`TEST_` payload inventory stays at 0 | Any regression that repopulates the inventory |

## New Track 22.0 assertions (13)

See `backend/tests/test_track_22_0_platform_excellence.py`:

1. Every prior track's lock-test file still committed.
2. `PLATFORM_MANIFEST.json` still committed with counts snapshot.
3. Track 22.0 executive summary + 12 sub-deliverables committed (13 total) and non-empty.
4. `TECHNICAL_DEBT_REGISTER.md` records TD-22.1-* and TD-22.2-* deferrals.
5. `PRD.md` and `CHANGELOG.md` contain Track 22.0 entries.
6. Six Pillars scorecard file exists with platform average ≥ 9.7.
7. `EMAIL_SAFETY_MODE=strict` preserved in preview `.env`.
8. `resend.Emails.send` monkey-patch source lines preserved.
9. Dispatcher strict-mode gate source lines preserved.
10. Payload guardrail (`test_track_21_2e1_payload_canonicalization.py`) still committed.
11. CORS explicit allow-lists still present (no wildcard regression).
12. Executive Summary explicitly defers server.py to Track 22.1 with Backend owner + parity gate.
13. Executive Summary explicitly defers App.js to Track 22.2 with Frontend owner + parity gate.

## CI recommendations (documented, not executed)

- Wire `yarn lint --max-warnings 0` into a pre-commit hook.
- Wire the Track 21.2E-1 guardrail into a required GH check.
- Add nightly manifest regeneration (offered in prior tracks; Ops decision).
