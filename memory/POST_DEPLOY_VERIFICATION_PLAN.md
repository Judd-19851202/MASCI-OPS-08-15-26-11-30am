# POST-DEPLOY VERIFICATION PLAN
## OMEGA Pre-Deploy Certification · Phase 11 of 11

**Date**: 2026-06-03
**Authority**: OMEGA Pre-Deploy Certification

## When to run this

Immediately after the deploy artifact is promoted to production, BEFORE inviting field operators to log in.

## Tier 1 — Identity & health (≤ 2 minutes)

| # | Check | Method | Expected |
|---|---|---|---|
| 1 | Production hash changed | `git rev-parse HEAD` on production | New SHA matches deploy artifact (≠ previous hash) |
| 2 | Backend `/api/health` | `curl https://<prod>/api/health` | HTTP 200 |
| 3 | Frontend bundle accessible | `curl https://<prod>/` | HTTP 200 · expected bundle size range |
| 4 | Supervisor / Kubernetes pods all green | platform dashboard or `kubectl get pods` | All `Running` |

## Tier 2 — OKCP / OER feature verification (≤ 5 minutes)

| # | Check | Method | Expected |
|---|---|---|---|
| 5 | New body_es content live | `curl https://<prod>/api/guidance/tips?form_key=fleet.rts` | JSON includes 5 tips (why · mistake · who · next · escalate) with both `body` AND `body_es` populated |
| 6 | Parent `mistake` tip serves on a parent form_key | `curl https://<prod>/api/guidance/tips?form_key=jha` | Response includes a tip with `kind=mistake` and a substantive `body` |
| 7 | Glossary `RTS` entry visible | Navigate to `/admin/operational-language` as admin and `Ctrl-F` for "Return to Service" | Entry visible with EN + ES + 5-section structure |
| 8 | Glossary `JHA / JHP` entry visible | Same | Visible |
| 9 | Glossary `EMR` entry visible | Same | Visible |
| 10 | Public JHP hub still loads in ES | Navigate to `/jha` and click `LangToggle → ES` | Page renders in Spanish; no console errors |

## Tier 3 — Existing-workflow regression sweep (≤ 10 minutes)

| # | Check | Expected |
|---|---|---|
| 11 | JHP acknowledge flow (`/jha` → acknowledge) | Acknowledgement succeeds; ledger entry appears in `/admin/jha-acknowledgements` |
| 12 | Recovery Stream loads | `/admin/recovery-stream` lists most-recent transition events |
| 13 | HR lifecycle (Reactivate vs Rehire) reads correctly | Open an archived employee in `/admin/hr/employees`; both Reactivate and Rehire actions visible |
| 14 | Daily Report sticky submit footer present | Open `/daily-reports/new`; sticky footer with submit button visible |
| 15 | Safety meeting topic library loads | Open `/safety-topic-library`; trade filter works; ES topic content visible |
| 16 | Spanish coaching renders | Open any form (Daily Report, JHP, Incident) in ES mode; HelpTip blocks render ES title + ES body |
| 17 | Photo viewer loads from an Incident detail | Open any Incident with photos; viewer opens; photos render |
| 18 | Scheduler routes responsive | `/api/admin/scheduler/state` (admin token) returns HTTP 200 |
| 19 | Resend webhook security in place | Attempt webhook POST without valid signature → expect 401/403 |

## Tier 4 — Blocker-fix verification (required if B-1 remediated)

| # | Check | Expected |
|---|---|---|
| 20 | `test_iter282_payroll_variance_coaching::test_all_pv_tips_have_hr_scope` re-runs PASS | All PV tips have HR scope |
| 21 | `test_iter224_employee_lifecycle_helptips::test_all_tips_hr_scoped_only` PASS | All employee-lifecycle tips HR-scoped |
| 22 | `test_iter224::test_anon_caller_sees_no_tips` PASS | Anonymous fetch of `employee-lifecycle` returns `count=0` |
| 23 | Anonymous public fetch on HR-only workflow returns nothing | `curl https://<prod>/api/guidance/tips?form_key=payroll-variance` (no auth) → JSON with `count=0` |
| 24 | Authenticated HR fetch returns the mistake tip | Same URL with HR token → `count` includes the OKCP mistake tip |

## Tier 5 — No-regression sentinel (≤ 2 minutes)

| # | Check | Expected |
|---|---|---|
| 25 | Sentry / log scan for first 15 min post-deploy | No new ERROR-level entries; warnings level matches pre-deploy baseline (passkeys index conflict + scheduled-backup respawn are pre-existing and expected to continue) |
| 26 | Mobile / iPad sanity (smoke) | `/` + `/jha` + `/daily-reports` open and render usably on iPad viewport |

## Rollback decision tree

| Symptom | Action |
|---|---|
| Any Tier 1 check fails | Rollback immediately. Operator paged. |
| Tier 2 check 5 / 6 / 7 / 8 / 9 fails (OKCP content not live) | Verify deploy artifact matches the OKCP commit. If yes, investigate ConfigMap / image build. NOT auto-rollback. |
| Tier 3 check fails (regression) | Manual triage: was the failure introduced by OKCP/OER? If yes, rollback. If no, file as separate issue. |
| Tier 4 check fails (remediation incomplete) | Confirm patch applied to deploy artifact. If patch IS in artifact but test fails, investigate scope-filter logic. |
| Tier 5 noise above baseline | Monitor for 30 min; rollback if error rate doesn't subside. |

## Deploy hash recording template

```
PRE-DEPLOY HASH:   <previous_production_sha>
NEW DEPLOY HASH:   a1949bb70623a9bb7479565965cbc1936dcfcdcd  (+ B-1 fix if applied)
DEPLOY START:      <UTC timestamp>
DEPLOY COMPLETE:   <UTC timestamp>
VERIFICATION PASS: <UTC timestamp>
APPROVER:          <operator name>
```

## Time budget

**~20 minutes total** for full Tier 1–5 verification by a single operator. **~5 minutes** for Tier 1+2 only (minimum acceptable).
