# PRE-DEPLOY-FINAL-001 · DEFECT REGISTER

Severity classification per directive: P0 (deploy blocker) · P1 (must-fix before deploy) · P2 (workaround exists) · P3 (cosmetic).

## P0 — DEPLOYMENT BLOCKERS
**(none)**

## P1 — MUST-FIX BEFORE DEPLOY

### HUMAN-QA-MOBILE-001
* **Title:** Multi-device UX certification cannot be executed from agent environment.
* **Detail:** Directive §2 requires iPhone Safari, iPad Safari portrait + landscape, Desktop Chrome, Desktop Safari across 7 viewports (390×844 → 1920×1080). Agent has only headless Chromium at one viewport. Per OMEGA "do not force a PASS," cannot be self-certified.
* **Required action:** 30–60 min hands-on QA per the screen list in §2 of the directive.
* **Owner:** Operator / designated tester.
* **Risk if skipped:** Mobile layout regression slips into production.

### HUMAN-QA-AUTH-MATRIX-001
* **Title:** Cross-role login matrix not exercisable from agent environment.
* **Detail:** Directive §5 requires Admin / PM / HR / Safety / Shop / Dispatch logins, cross-role portal blocking, expired-session behaviour, direct-URL access. `test_credentials.md` is the canonical source; existing JWT + brute-force tests pass at the unit level but a live end-to-end matrix needs human action.
* **Required action:** 20 min cross-role smoke per directive §5.
* **Owner:** Operator.
* **Risk if skipped:** Role escalation slips through.

## P2 — WORKAROUND EXISTS
**(none)**

## P3 — COSMETIC / NICE-TO-HAVE

### TEST-ODR-M1-OPTION-C-001
* **File:** `/app/backend/tests/odr/test_m1_option_c.py::test_operational_records_unified_list`
* **Detail:** Test expects `len(odr) >= 1` against a freshly created `_preview` test DB. The DB has 0 seed records, so the assertion fails. Endpoint behaviour is correct — preview DB has 170 ODR rows that flow through the same path. Same class of stale-fixture bug as the previously-fixed `test_trench_safety_phase2.py`.
* **Recommendation:** Seed the test DB with 1 ODR row in setup, OR change the assertion to `>= 0` and pin a separate "with ODR data" test.
* **Owner:** Backend.
* **Production impact:** None.

### DATA-TESTMARKER-001
* **Detail:** Production DB carries forensic artefacts:
  * 1 `daily_reports` row with a test marker.
  * 2 `employees` rows with test markers.
  * 4 `job_photos` project_numbers map to multiple distinct project_name spellings (typo variants, not duplicates — canonical resolver collapses display).
* **Production impact:** None visible to operators. The Canonical Project Identity Resolver hides duplicates at read time.
* **Recommendation:** One-shot cleanup script in a future sprint (NOT in this sprint per OMEGA).
* **Owner:** Operator decision.

### DATA-DR-ORPHAN-001
* **Detail:** 2 `daily_reports` carry a `project_number` not present in `jobs_master`. Tolerance threshold is set to 10 in this audit; 2/113 = 1.8% — within tolerance.
* **Production impact:** Reports may render under a placeholder folder until the matching `jobs_master` row is created.
* **Owner:** Operator decision.

## STATE OF PRIOR DEFECTS (rolled forward from earlier sprints)

| ID | Status |
|---|---|
| DR-QUEUE-RETRY-001 | ✅ FIXED — 7/7 tests pass; ships frontend-only on next deploy |
| WEBHOOK-2XX-ON-MISCONFIG-001 (= WEBHOOK-HARDEN-001) | ✅ FIXED — credentials-missing returns 503 |
| MOTIVE-PROD-CRED-MISSING-001 | ✅ REMEDIATED — prod credentials restored, monitor armed |
| MOTIVE-PROD-WEBHOOK-FLOOD-001 | ✅ MITIGATED — 0 open `production_incidents` |
| APP_ENV-LABEL-001 | ✅ FIXED — env chain aligned, default flipped to "production" |
| MOTIVE-CRED-VERIFY-002 | ✅ EXPLAINED — false-positive from preview validation; ALERT-ENV-001 prevents recurrence |
| ALERT-ENV-001 (subject + body env tags) | ✅ FIXED — 15/15 tests |
| POST-DEPLOY-001-MISCHARACTERISATION | 🟡 Process-level observation, no code action required |
