# TRACK 20.6B · Test Hardening + Tech-Debt Closeout · Executive Summary

**Status:** ✅ **CLOSED** · GO for deployment.

## What this track did

Track 20.6B is the pre-deployment test-hardening pass mandated by the Track 20.6A tech-debt doctrine. It closed the three classified debt items that were open coming into the release:

| Debt ID | Title | Class | Outcome |
|---|---|---|---|
| TD-20.6A-001 | `test_vocabulary_unauth_401` returns 200 in live e2e (fixture leak) | C | ✅ **CLOSED** — fresh `requests.Session()` isolation guard; live 401 verified end-to-end. |
| TD-20.6A-002 | `test_vocabulary_hr_sees_all_lanes` strict-equality broke after Track 19.59 vendor lane | C | ✅ **CLOSED** — replaced with additive-safe superset assertion + certified-vocabulary guardrail. |
| TD-20.7-C01 | `test_daily_reports.py` + `test_job_photos.py` legacy admin-login from Track 15.32 | C | ✅ **CLOSED** — migrated to canonical `POST /api/auth/multi-login`; triple-token fixture (admin+HR+safety); additive R2/data-URL accept-list. |
| **TD-20.6B-A01** (new) | Auto-email dispatcher had no synthetic-test-record short-circuit; every preview-env test run risked live Resend delivery | **A** | ✅ **FIXED IN-TRACK** — added `TEST_`-prefix short-circuit in `_dispatch_auto_email` with trust-spine `status="skipped"` audit. |

## Why the new "A" debt was fixed inline

Before Track 20.6B, running `test_daily_reports.py` (or any workflow-submit test) against the preview environment where `AUTO_EMAIL_REPORTS=true` and `RESEND_API_KEY` is populated would fire real emails to the assigned PM + always-CC list on every test iteration. That was a Class-A operational-hygiene defect discovered during Track 20.6B execution and — per Track 20.6A doctrine — must be fixed inside the current track (not deferred).

The fix is a **surgical additive guardrail** at the top of `_dispatch_auto_email`: when `record["project_name"]` starts with `TEST_` (the reserved test prefix), the dispatcher short-circuits before any Resend call and emits a `status="skipped"` trust-spine event with `failure_reason="synthetic_test_record"`. Real production records (which never use a `TEST_` prefix) are byte-identical. Zero drift.

## Six pillars alignment

- **Powerful** — the test suite now protects real production behavior end-to-end (auth, permissions, contract, immutability) instead of drowning in false 401/410/legacy noise.
- **Simple** — one canonical auth path (`POST /api/auth/multi-login`) with a triple-token fixture; assertions use additive-safe superset semantics; the email guard is one `if` at the top of a well-audited function.
- **Beautiful** — every hardened test has a docstring explaining the doctrine that governs it (Track 20.6B). Every fix is intentional, named, and traceable.
- **Trusted** — no false green: every previously-failing test is now really passing against the live preview backend. No skip added to hide a target failure.
- **Proven** — the entire regression envelope (Track 19.59 vendor lane · Track 19.60 vendor thread · Track 19.61 asset thread · Track 19.62 fire protection · Track 20.6 fire audit · Track 20.7 photo capture) still passes.
- **Operational** — deployment is no longer blocked by classified test debt; the email safety mandate is enforced structurally at the code level (not just doctrinally in tests).

## Files changed

**Production code (surgical, additive):**
- `backend/server.py` — `_dispatch_auto_email` gained a `TEST_`-prefix short-circuit (~30 lines added, no lines removed).

**Test code (test-only, hardening):**
- `backend/tests/test_track_19_21_e2e_live.py` — `test_vocabulary_unauth_401` now uses fresh `requests.Session()`; `test_vocabulary_hr_sees_all_lanes` uses superset assertion + certified-set guardrail.
- `backend/tests/test_daily_reports.py` — migrated to `POST /api/auth/multi-login` triple-token fixture.
- `backend/tests/test_job_photos.py` — migrated to `POST /api/auth/multi-login`; additive R2/data URL accept-list; conftest-drift note removed.

**Docs + register:**
- `memory/TECHNICAL_DEBT_REGISTER.md` — TD-20.6A-001, TD-20.6A-002, TD-20.7-C01 marked CLOSED; TD-20.6B-A01 added and marked FIXED.
- 9 Track 20.6B markdown deliverables under `memory/TRACK_20_6B_*.md`.
- `memory/PRD.md` + `memory/CHANGELOG.md` — Track 20.6B entry.
- `backend/tests/test_track_20_6b_test_hardening.py` — lock test.

## Deployment call

**Ship.** All classified test debt closed with evidence. All prior track lock tests still green. Email safety mandate honored (zero live emails triggered by this track OR by future test runs). Zero drift on production behavior for real (non-TEST_) records.
