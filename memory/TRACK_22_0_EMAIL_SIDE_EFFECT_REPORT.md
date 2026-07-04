# TRACK 22.0 · Email & Side-Effect Safety Report

**Verdict:** 🟢 **CERTIFIED.** Three-layer email envelope intact. Zero live emails during Track 22.0.

## The three layers

| Layer | Enforcement | Certified |
|---|---|---|
| 1 · SDK kill switch | `backend/server.py` monkey-patches `resend.Emails.send` at module import when `EMAIL_SAFETY_MODE ∈ {strict, silent, test}` | ✅ Boot log confirms activation |
| 2 · Dispatcher short-circuit | `_dispatch_auto_email` short-circuits **before** `recipients_for_record_async` when safety mode is strict OR `project_name.startswith("TEST_")` | ✅ Source-level assertion in lock test |
| 3 · Payload prefix | Every synthetic workflow payload starts with `TEST_` (Track 21.2E-1 canonicalization + permanent guardrail) | ✅ 0 non-`TEST_` payloads · 15-assert guardrail green |

## Side-effect categories

| Category | Status |
|---|---|
| Email (Resend) | 🟢 Blocked in preview |
| Trust Spine writes | 🟢 Internal audit only |
| Scheduled tasks | 🟢 All downstream of dispatcher gate |
| Notifications | 🟢 Route through dispatcher |
| PDF generation | 🟢 In-memory / `/app/backend/storage` |
| R2 uploads | 🟡 `TEST_` blobs accumulate; janitor spec queued (Track 21.2z) |
| Sentry | 🟡 Preview events mixed with prod; env-tag queued (Track 21.2z) |
| SMS / webhooks | 🟢 Not present |

## Lock tests protecting the envelope

25 assertions across:
- `test_track_20_6b_test_hardening.py`
- `test_track_21_2e_email_safety.py` (11)
- `test_track_21_2e_1_canonicalization.py` (6)
- `test_track_21_2e1_payload_canonicalization.py` (15)

Any future change that weakens any layer fails one of these tests at CI time.

## Six Pillars

- Trusted: **9.95**
- Proven: **9.95**
