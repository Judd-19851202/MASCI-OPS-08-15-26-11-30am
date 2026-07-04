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
| TD-20.6A-001 | `test_vocabulary_unauth_401` returns 200 instead of 401 in live e2e | **C** — pre-existing test/env debt | Safety-Records team | P3 | 20.6B (test hardening) | **CLOSED** (2026-08-04 · fresh session isolation + live 401 verified · see `TRACK_20_6B_FIX_REPORT_TD_20_6A_001.md`) |
| TD-20.6A-002 | `test_vocabulary_hr_sees_all_lanes` uses strict-equality assertion that broke when Track 19.59 additively added the `vendor` lane | **C** — pre-existing test debt from Track 19.59 | Safety-Records team | P3 | 20.6B (test hardening) | **CLOSED** (2026-08-04 · superset assertion + certified-set guardrail · see `TRACK_20_6B_FIX_REPORT_TD_20_6A_002.md`) |
| TD-20.7-B01 | `PhotoUpload.jsx` "Take Photo" button silently no-oped on desktops without a webcam / permission-blocked / HTTP contexts (reported by a real field user on the Daily Report) | **B** — Blocks Deployment | Universal-Photo team | P0 | 20.7 | **FIXED** (2026-08-04) |
| TD-20.7-C01 | `test_daily_reports.py` + `test_job_photos.py` legacy suites hit endpoints without the multi-login token introduced in TRACK 15.32; they fail with 401/410 regardless of Track 20.7. Confirmed identical failure count before and after Track 20.7 via `git stash` baseline run. | **C** — pre-existing test debt from TRACK 15.32 auth-model migration | Testing team | P3 | 20.6B (test hardening) | **CLOSED** (2026-08-04 · migrated to `/api/auth/multi-login` + admin/hr/safety triple-token fixture · additive R2/data URL accept-list · see `TRACK_20_6B_FIX_REPORT_TD_20_7_C01.md`) |
| TD-20.6B-A01 | Auto-email dispatcher (`_dispatch_auto_email`) had no synthetic-test-record short-circuit, allowing any preview-environment test run against `POST /api/daily-reports` (or any workflow submit) to trigger real Resend emails to the assigned PM + always-CC list | **A** — Fix Now | Operations Trust team | P1 | 20.6B | **FIXED** (2026-08-04 · added `project_name.startswith("TEST_")` short-circuit with trust-spine `status="skipped"` audit) |
| TD-20.8-D01 | Track 20.8 human-walkthrough smoke script initially probed `/dispatch` and observed 404. Investigation showed the canonical dispatch portal route is `/dispatch-portal` (per `frontend/src/App.js:1076`). Live curl of `/dispatch-portal` returns 200. | **D** — False Positive | Testing team | P3 | 20.8 | **CLOSED** (2026-08-04 · evidence: `curl -s -o /dev/null -w "%{http_code}\n" https://safety-audit-mobile-1.preview.emergentagent.com/dispatch-portal` → 200) |
| TD-20.8-A01 | `test_approve_without_employee_linkage_blocked` was skipping via a permissive `pytest.skip` branch that hid a payload bug (missing `record_type` field → 422 validation → skip fired) — the certified employee-linkage gate was never actually exercised. | **A** — Fix Now | Testing team | P1 | 20.8 | **FIXED** (2026-08-04 · added `record_type` to payload · removed the skip branch · added hard assertions on both halves of the certified contract [pending_match creation + blocked approval] · live-verified via preview curl · see `TRACK_20_8_FIX_REPORT_TD_20_8_A01.md`) |
| TD-20.9-A01 | `MasterListPanel.jsx::restoreRow` was called from the archive-tab restore button but never defined. Every restore click threw `ReferenceError: restoreRow is not defined`. Caught by the real ESLint 9 gate introduced in Track 20.9. | **A** — Fix Now | Frontend team | P1 | 20.9 | **FIXED** (2026-08-04 · added missing `restoreRow` async function using the same pattern as other row mutations in the file · lint clean · see `TRACK_20_9_CLEANUP_REPORT.md`) |
| TD-20.9-A02 | `TrenchBoxPosterCard.jsx` imported `useBranding` at top of file but never called it, then referenced `branding.safety_email` / `branding.support_email` / `branding.platform_display_name` in JSX. Every render threw `ReferenceError: branding is not defined`. Caught by real ESLint 9. | **A** — Fix Now | Frontend team | P1 | 20.9 | **FIXED** (2026-08-04 · added `const branding = useBranding();` inside component body before any `branding.*` reference · see `TRACK_20_9_CLEANUP_REPORT.md`) |
| TD-20.9-C01 | 708 duplicate keys in `frontend/src/lib/i18n.js` bilingual dictionary (silent last-write-wins on translations). Batch-fixing 700+ dedupes pre-deploy is high-risk to actual translations. | **C** — Existing Tech Debt | i18n team | P2 | 21.x (bilingual cleanup) | **OPEN** |
| TD-20.9-C02 | 188 `react/no-unescaped-entities` errors across ~80 frontend files (cosmetic quote-escape). Auto-fixable via `eslint --fix`, but touching 188 files pre-deploy is unnecessary risk. | **C** — Existing Tech Debt | Frontend team | P3 | 21.x (lint polish) | **OPEN** |
| TD-20.9-C03 | 78 unused `eslint-disable` directive warnings — legacy comments no longer suppressing anything. | **C** — Existing Tech Debt | Frontend team | P3 | 21.x | **OPEN** |
| TD-20.9-C04 | 6 `react/no-unstable-nested-components` errors (in-render component defs cause re-mount + state loss on every parent render). Real render-perf bugs but not runtime crashes. | **C** — Existing Tech Debt | Frontend team | P2 | 21.x (careful refactor) | **OPEN** |
| TD-20.9-C05 | 5 `no-empty` in `GlobalSearch.jsx` — intentional `catch {}` around `localStorage` for private-browsing safety. Rewrite to `catch { /* storage unavailable */ }`. | **C** — Existing Tech Debt | Frontend team | P3 | 21.x | **OPEN** |
| TD-20.9-C06 | 6 misc lint findings (3× `no-console`, 2× `no-await-in-loop`, 1× `no-unused-vars`, 1× `no-regex-spaces`, 1× `react/no-unknown-property`). | **C** — Existing Tech Debt | Frontend team | P3 | 21.x | **OPEN** |

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
