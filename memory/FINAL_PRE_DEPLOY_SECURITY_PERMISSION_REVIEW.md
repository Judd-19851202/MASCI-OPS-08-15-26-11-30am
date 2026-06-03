# FINAL PRE-DEPLOY · SECURITY / PERMISSIONS REVIEW
## OMEGA Pre-Deploy Certification · Phase 4 of 11

**Date**: 2026-06-03

## 1 · Baseline security posture (unchanged from last production deploy)

| Check | Source | Status |
|---|---|:-:|
| HR-only employee lifecycle routes | `routes/hr_*`, `routes/employee_lifecycle.py` | 🟢 (no edits this cycle) |
| Admin-only Recovery Stream / Universal Undo | `routes/workflow_undo.py`, FOCP R2 | 🟢 (no edits this cycle) |
| Admin-only sensitive routes | `routes/admin_*`, lifecycle files | 🟢 (no edits this cycle) |
| Public-gate routes (`/jha`, `/time-off`, `/api/guidance/tips`) | Source-direct review | 🟢 by design intent; ⚠️ contaminated by §2 below |
| No public employee creation | `routes/employees.py` returns 410 on `/api/employees/add` | 🟢 (test failures here are env-related, not code-related) |
| Sub/vendor contamination guard | TR-0003 doctrine | 🟢 unchanged |
| Workflow lifecycle transitions auth-gated | `routes/*lifecycle*.py` | 🟢 unchanged |
| Webhook posture (`RESEND_WEBHOOK_SECRET`) | `test_hotfix_bundle_a_webhook_secret.py` — PASS | 🟢 |
| CORS for mascidocs.com | `server.py` CORS middleware | 🟢 unchanged |
| Secrets exposed in source | grep finds no `sk_*` / API key literals introduced this cycle | 🟢 |

## 2 · 🔴 BLOCKER · OKCP scope-doctrine violation (33 tips)

OKCP's Wave 1 + Wave 2 edits added 52 new tip dicts to `tips.py`. **33 of them used `scopes=["public"]` on form_keys whose existing siblings are scoped to HR / leadership / admin-shop / admin-dispatch / admin-safety.** Result: anonymous callers to `/api/guidance/tips?form_key=<HR-workflow>` now receive operational guidance intended for HR / Admin / Leadership only.

### 2.1 · Full violation list

| Form_key | OKCP-added kind | Expected scope (existing siblings) | Got |
|---|---|---|---|
| fleet.rts | who | `['admin', 'dispatch']` | `['public']` |
| fleet.rts | next | `['admin', 'dispatch']` | `['public']` |
| fleet.rts | escalate | `['admin', 'dispatch']` | `['public']` |
| fleet.repair | mistake | `['admin', 'shop']` | `['public']` |
| fleet.visibility | mistake | `['admin', 'dispatch', 'safety', 'shop']` | `['public']` |
| attendance | mistake | `['admin', 'leadership']` | `['public']` |
| attendance | who | `['admin', 'leadership']` | `['public']` |
| attendance | next | `['admin', 'leadership']` | `['public']` |
| crew_eval | mistake | `['admin', 'leadership']` | `['public']` |
| document-expirations | mistake | `['admin', 'hr', 'safety']` | `['public']` |
| driver-qualification | mistake | `['admin', 'hr']` | `['public']` |
| employee-accountability | mistake | `['admin', 'hr']` | `['public']` |
| employee-lifecycle | mistake | `['admin', 'hr']` | `['public']` |
| new_employee_eval | mistake | `['admin', 'leadership']` | `['public']` |
| new_employee_eval | who | `['admin', 'leadership']` | `['public']` |
| new_employee_eval | escalate | `['admin', 'leadership']` | `['public']` |
| payroll-variance | mistake | `['admin', 'hr']` | `['public']` |
| safety-document | mistake | `['admin', 'safety']` | `['public']` |
| safety-training | mistake | `['admin', 'safety']` | `['public']` |
| time-off-review | mistake | `['admin', 'hr']` | `['public']` |
| time-verification | mistake | `['admin', 'hr']` | `['public']` |
| training_deficiency | mistake | `['admin', 'leadership']` | `['public']` |
| training_deficiency | who | `['admin', 'leadership']` | `['public']` |
| training_deficiency | escalate | `['admin', 'leadership']` | `['public']` |
| verbal_coaching | mistake | `['admin', 'leadership']` | `['public']` |
| verbal_coaching | who | `['admin', 'leadership']` | `['public']` |
| verbal_coaching | escalate | `['admin', 'leadership']` | `['public']` |
| promotion_recommendation | who | `['admin', 'leadership']` | `['public']` |
| promotion_recommendation | next | `['admin', 'leadership']` | `['public']` |
| promotion_recommendation | escalate | `['admin', 'leadership']` | `['public']` |
| recognition | who | `['admin', 'leadership']` | `['public']` |
| recognition | next | `['admin', 'leadership']` | `['public']` |
| recognition | escalate | `['admin', 'leadership']` | `['public']` |

### 2.2 · Blast radius

- Anonymous-token API consumers (the `/api/guidance/tips` endpoint is public by design for `daily-report`, `incident`, `inspection`, `jha`, etc.) can today read HR / leadership / shop / dispatch / safety operational guidance — e.g., **how to recommend a promotion, how to issue verbal coaching, when to refuse a Time-Off, how to handle Payroll Variance attestation**.
- This is doctrinal data exposure — the content is operationally sensitive (HR / leadership coaching) but not strictly PII or secrets. Severity is below "credential exposure" but above "cosmetic".

### 2.3 · Likelihood of harm

- Public endpoint already widely served by the platform — any third-party / scraping client could trivially enumerate all 33.
- Likelihood: 100% if the platform ships in current state.

### 2.4 · Mechanical remediation (available, NOT authorized in this directive)

For each of the 33 OKCP-added tips, replace `"scopes": ["public"]` with the intended scope tuple from the existing siblings (already documented above). All edits would be in `backend/guidance/tips.py` lines 6160-6360 (the OKCP-added range). Estimated edit: ~33 targeted string replacements; ~5 minutes. No new code; no new tests; would re-pass `test_iter282_*`, `test_iter224_*`, plus reflect correct doctrine.

**Per OMEGA Pre-Deploy directive STOP rule, remediation is NOT performed in this certification phase. Operator authorization required.**

## 3 · Security verdict

🔴 **NO GO** — Phase 4 cannot certify with 33 active scope-doctrine violations on a public-facing endpoint. Remediation path is known, low-risk, and mechanical. Awaiting operator authorization.
