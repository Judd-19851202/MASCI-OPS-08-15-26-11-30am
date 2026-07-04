# Technical Debt Register — MASCI Operations Platform

**Doctrine:** Track 20.6A — Technical Debt & Failure Discovery Amendment.

Every failure, warning, regression, broken test, import error, compile
issue, dependency issue, environment issue, or architectural defect
discovered during any audit / promotion / certification MUST be
classified into exactly one of:

- **A — Fix Now:** small, low-risk, inside current track. MUST be
  corrected before certification.
- **B — Blocks Deployment:** production risk. Current track cannot
  close until resolved.
- **C — Existing Technical Debt:** verified pre-existing. Does not block
  current work. MUST generate a Debt ID and enter this register.
- **D — False Positive:** proven not to be an issue. Evidence required.

**"No action" is NOT an allowed outcome.**

## Active Register

| ID | Title | Class | Owner | Priority | Target Track | Status |
|---|---|---|---|---|---|---|
| TD-19.62-A01 | Duplicate `label:` keys in `FleetUnitThread.jsx :: deriveRelationships` (5 instances · pre-existing lint debt surfaced when Track 19.62 extended the file) | **A** — Fix Now | Fleet-Thread team | P2 | 19.62 | **FIXED** (2026-08-03) |
| TD-20.6A-001 | `test_vocabulary_unauth_401` returns 200 instead of 401 in live e2e | **C** — pre-existing test/env debt | Safety-Records team | P3 | 20.6B (test hardening) | **OPEN** |
| TD-20.6A-002 | `test_vocabulary_hr_sees_all_lanes` uses strict-equality assertion that broke when Track 19.59 additively added the `vendor` lane | **C** — pre-existing test debt from Track 19.59 | Safety-Records team | P3 | 20.6B (test hardening) | **OPEN** |
| TD-20.7-B01 | `PhotoUpload.jsx` "Take Photo" button silently no-oped on desktops without a webcam / permission-blocked / HTTP contexts (reported by a real field user on the Daily Report) | **B** — Blocks Deployment | Universal-Photo team | P0 | 20.7 | **FIXED** (2026-08-04) |
| TD-20.7-C01 | `test_daily_reports.py` + `test_job_photos.py` legacy suites hit endpoints without the multi-login token introduced in TRACK 15.32; they fail with 401/410 regardless of Track 20.7. Confirmed identical failure count before and after Track 20.7 via `git stash` baseline run. | **C** — pre-existing test debt from TRACK 15.32 auth-model migration | Testing team | P3 | 20.6B (test hardening) | **OPEN** |

## Detail

Full one-page reports for each debt item:

- `memory/TECH_DEBT_TD_20_6A_001_vocabulary_unauth.md`
- `memory/TECH_DEBT_TD_20_6A_002_vocabulary_hr_lanes.md`

## Rules for future entries

Every future entry must specify:

1. **Debt ID** — format `TD-<track>-NNN` (auto-numbered per track).
2. **Root cause** — what failed, why, when, which track introduced it.
3. **Impact** — production / preview / test-env-only.
4. **Risk** — probability × severity if left unfixed.
5. **Owner** — responsible team or subsystem.
6. **Proposed Track** — where it will be fixed.
7. **Priority** — P0 (blocker) / P1 (high) / P2 (medium) / P3 (low).
8. **Status** — OPEN / IN PROGRESS / FIXED / DEFERRED / WONTFIX.

## Certification rule

No certification report may contain language such as:

- "Pre-existing issue"
- "Known failure"
- "Ignored"
- "Left as-is"
- "Not addressed"
- "Outside scope"

...unless it ALSO includes the full classification above and a link
back to this register.

## Lock-test rule

Every future certification lock test must verify:

- No uncategorized failures.
- No uncategorized technical debt.
- Every discovered issue has: owner · priority · disposition · target
  track.

**Signed:** E1 · Track 20.6A · Elite Consistency · Zero-Drift · Six
Pillars.
