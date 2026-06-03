# OKCP SCOPE-GATING REMEDIATION REPORT
## OMEGA Directive · P0 Security / Permission Remediation

**Date**: 2026-06-03
**Authority**: OMEGA AUTHORIZATION — P0 OKCP SCOPE-GATING REMEDIATION
**Operator authorization**: Option A (apply targeted scope fix)
**Scope**: Audit + correct OKCP-added tips in `backend/guidance/tips.py` whose `scopes=["public"]` violated doctrine.
**Files modified**: `/app/backend/guidance/tips.py` (1 file). `/app/backend/guidance/tips_es.py` not touched (no `scopes` field in ES merge — scope inherits from EN parent at lookup).

---

## 1 · Method

1. Identified the OKCP-added range in `tips.py` — `_TIPS.extend([...])` block beginning at line 6146 (header banner: *"OKCP — Operational Knowledge Completion Program (2026-06-03)"*), ending line 6504.
2. For each form_key OKCP touched, enumerated the **pre-existing sibling scopes** present in the original `_TIPS = [...]` literal (lines 34-6134). Authoritative table built in §2.
3. For each OKCP-added tip with `scopes=["public"]`, applied the **sibling-scope rule** ("Match the scope of sibling tips on the same form_key unless a stronger restriction is required").
4. Validation against §2 of the directive: HR / Safety / Leadership / Admin / Fleet / Recovery / Employee / Payroll / Operational guidance must NOT be public unless an existing same-form_key sibling proves public access is intended.

---

## 2 · Pre-existing sibling-scope canon (authoritative source)

| form_key | pre-existing siblings' scope |
|---|---|
| attendance | `["leadership", "admin"]` |
| checkout | `["public"]` |
| corrective | `["public"]` |
| crew_eval | `["leadership", "admin"]` |
| daily-report | `["public"]` |
| document-expirations | `["hr", "safety", "admin"]` |
| driver-qualification | `["hr", "admin"]` |
| employee-accountability | `["hr", "admin"]` |
| employee-lifecycle | `["hr", "admin"]` |
| equipment-issuance | `["public"]` |
| equipment-training | `["public"]` |
| fire-extinguisher | `["public"]` |
| fleet.repair | `["shop", "admin"]` |
| fleet.rts | `["dispatch", "admin"]` |
| fleet.visibility | `["shop", "dispatch", "safety", "admin"]` |
| incident | `["public"]` |
| inspection | `["public"]` |
| jha | `["public"]` |
| material-calculator | `["public"]` |
| meeting | `["public"]` |
| new_employee_eval | `["leadership", "admin"]` |
| payroll-variance | `["hr", "admin"]` |
| preop | `["public"]` |
| promotion_recommendation | `["leadership", "admin"]` |
| qaqc | `["public"]` |
| recognition | `["leadership", "admin"]` |
| safety-document | `["safety", "admin"]` |
| safety-training | `["safety", "admin"]` |
| supervisor_notes | `["leadership", "admin"]` |
| time-off-review | `["hr", "admin"]` |
| time-verification | `["hr", "admin"]` |
| topic-library | `["public"]` |
| training_deficiency | `["leadership", "admin"]` |
| verbal_coaching | `["leadership", "admin"]` |
| writeup | `["public"]` |

---

## 3 · Edits applied (36 tip dicts)

| # | form_key | kind | Before | After |
|---:|---|---|---|---|
| 1 | fleet.rts | who | `["public"]` | `["dispatch", "admin"]` |
| 2 | fleet.rts | next | `["public"]` | `["dispatch", "admin"]` |
| 3 | fleet.rts | escalate | `["public"]` | `["dispatch", "admin"]` |
| 4 | fleet.repair | mistake | `["public"]` | `["shop", "admin"]` |
| 5 | fleet.visibility | mistake | `["public"]` | `["shop", "dispatch", "safety", "admin"]` |
| 6 | attendance | mistake | `["public"]` | `["leadership", "admin"]` |
| 7 | attendance | who | `["public"]` | `["leadership", "admin"]` |
| 8 | attendance | next | `["public"]` | `["leadership", "admin"]` |
| 9 | crew_eval | mistake | `["public"]` | `["leadership", "admin"]` |
| 10 | document-expirations | mistake | `["public"]` | `["hr", "safety", "admin"]` |
| 11 | driver-qualification | mistake | `["public"]` | `["hr", "admin"]` |
| 12 | employee-accountability | mistake | `["public"]` | `["hr", "admin"]` |
| 13 | employee-lifecycle | mistake | `["public"]` | `["hr", "admin"]` |
| 14 | new_employee_eval | mistake | `["public"]` | `["leadership", "admin"]` |
| 15 | new_employee_eval | who | `["public"]` | `["leadership", "admin"]` |
| 16 | new_employee_eval | escalate | `["public"]` | `["leadership", "admin"]` |
| 17 | payroll-variance | mistake | `["public"]` | `["hr", "admin"]` |
| 18 | safety-document | mistake | `["public"]` | `["safety", "admin"]` |
| 19 | safety-training | mistake | `["public"]` | `["safety", "admin"]` |
| 20 | time-off-review | mistake | `["public"]` | `["hr", "admin"]` |
| 21 | time-verification | mistake | `["public"]` | `["hr", "admin"]` |
| 22 | training_deficiency | mistake | `["public"]` | `["leadership", "admin"]` |
| 23 | training_deficiency | who | `["public"]` | `["leadership", "admin"]` |
| 24 | training_deficiency | escalate | `["public"]` | `["leadership", "admin"]` |
| 25 | verbal_coaching | mistake | `["public"]` | `["leadership", "admin"]` |
| 26 | verbal_coaching | who | `["public"]` | `["leadership", "admin"]` |
| 27 | verbal_coaching | escalate | `["public"]` | `["leadership", "admin"]` |
| 28 | promotion_recommendation | who | `["public"]` | `["leadership", "admin"]` |
| 29 | promotion_recommendation | next | `["public"]` | `["leadership", "admin"]` |
| 30 | promotion_recommendation | escalate | `["public"]` | `["leadership", "admin"]` |
| 31 | recognition | who | `["public"]` | `["leadership", "admin"]` |
| 32 | recognition | next | `["public"]` | `["leadership", "admin"]` |
| 33 | recognition | escalate | `["public"]` | `["leadership", "admin"]` |
| 34 | supervisor_notes | who | `["public"]` | `["leadership", "admin"]` |
| 35 | supervisor_notes | next | `["public"]` | `["leadership", "admin"]` |
| 36 | supervisor_notes | escalate | `["public"]` | `["leadership", "admin"]` |

**Net**: 36 tip dicts had their `scopes` corrected. 33 were enumerated explicitly in `FINAL_PRE_DEPLOY_SECURITY_PERMISSION_REVIEW.md` §2.1. **3 additional violations** (supervisor_notes who/next/escalate) were detected during this remediation by running the sibling-scope rule across the entire OKCP block — supervisor_notes pre-existing siblings (lines 2229, 2243) are `["leadership", "admin"]`. These 3 were missed by the Phase-4 audit but are unambiguous violations under the directive's own rule. Fixing them is in-scope per the directive ("For each OKCP-added tip: 1. Identify form_key. 2. Identify sibling tips on same form_key. ...").

---

## 4 · Tips intentionally left at `["public"]`

These OKCP-added tips on form_keys whose existing siblings are already public — leaving these public is correct under the sibling-scope rule:

- `checkout/mistake` · `corrective/mistake` · `daily-report/mistake` · `equipment-issuance/mistake` · `equipment-training/mistake` · `fire-extinguisher/mistake` · `incident/mistake` · `inspection/mistake` · `jha/mistake` · `meeting/mistake` · `preop/mistake` · `qaqc/mistake` · `topic-library/mistake` · `writeup/mistake` · `material-calculator/next` · `material-calculator/escalate`

(16 tips remain public — matches sibling doctrine of the parent form_keys.)

---

## 5 · No-touch confirmation

- **No content deleted** — only `scopes` arrays modified. Title/body text unchanged.
- **No new tips added** — count remains the same (52 OKCP-added tips).
- **No new workflows / modules / glossary terms / UI changes / DB changes / migrations.**
- **Spanish parity (`tips_es.py`)** — file unchanged. Spanish merge keys by `(form_key, kind)` and does not contain `scopes` field. ES translations inherit gated scope from the EN parent at lookup time; ES coverage is unaffected, and scope-bypass is impossible.
- **No deployment performed.**

---

## 6 · Edit log (search_replace operations)

All 36 edits were performed via 36 unique `search_replace` calls. Each old_str was a full unique line of the form `{"form_key": "X", "kind": "Y", "scopes": ["public"],` and the new_str replaced only the `scopes` array. Edits are mechanical and reversible.

---

## 7 · Diff manifest

```
modified: backend/guidance/tips.py
  → 36 lines changed (scopes-array only)
  → 0 lines added
  → 0 lines removed
  → 0 tips removed
  → 0 tips added
```

No other backend/frontend files touched as part of this remediation.
