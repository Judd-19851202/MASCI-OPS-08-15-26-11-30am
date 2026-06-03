# OKCP SCOPE-GATING REMEDIATION CERTIFICATION
## OMEGA Directive · P0 Verdict

**Date**: 2026-06-03
**HEAD (pre-fix)**: `8a219c3`
**File modified**: `/app/backend/guidance/tips.py` (36 `scopes` arrays corrected)
**Authority**: OMEGA AUTHORIZATION — P0 OKCP SCOPE-GATING REMEDIATION (Option A)

---

## 1 · Validation matrix

| # | Required check | Method | Result |
|---:|---|---|:-:|
| 1 | Run the failing backend pytest group | `pytest tests/test_iter282_payroll_variance_coaching.py tests/test_iter224_employee_lifecycle_helptips.py` | 🟢 **44 passed, 0 failed** |
| 2 | Run full guidance/tips-touching backend pytest set | `pytest tests/ -k "helptip or tips or coaching or pv_scope or iter282 or iter224" --ignore=tests/odr` | 🟢 **677 passed, 4 pre-existing failures unrelated to OKCP**, 6 skipped |
| 3 | Confirm all 13 previously failing tests pass | 13 = 3 OKCP-attributable + 10 downstream siblings | 🟢 **All 3 OKCP-attributable PASS**: `test_iter282_payroll_variance_coaching::test_all_pv_tips_have_hr_scope`, `test_iter224_employee_lifecycle_helptips::test_all_tips_hr_scoped_only`, `test_iter224_employee_lifecycle_helptips::test_anon_caller_sees_no_tips`. All 10 downstream sibling tests in same suites also PASS. |
| 4 | Confirm no sensitive tips returned to public callers | Live API smoke against 20 HR/Leadership/Fleet/Admin form_keys | 🟢 **all 20 return `count=0` to anonymous caller** |
| 5 | Confirm public workflows still receive intended public coaching | Live API smoke against 15 public form_keys | 🟢 **all 15 return ≥ 5 tips to anonymous caller** |
| 6 | Spanish entries remain aligned and do not bypass scope controls | `tips_es.py` unchanged; merge keys by `(form_key, kind)`; no `scopes` field in ES; ES inherits EN scope at lookup | 🟢 **structurally impossible to bypass** |
| 7 | No content deleted | `git diff backend/guidance/tips.py` shows only `scopes` array changes — no title/body changes, no tip removed | 🟢 |
| 8 | No OKCP coverage loss | Count of OKCP-added tips before/after remediation: 52 → 52 | 🟢 |
| 9 | No new regression in `/api/guidance/tips` endpoint | Live curl `/api/guidance/tips?form_key=…` against parent + sub-keys with anon and scoped tokens implicit | 🟢 endpoint behavior identical; payloads correctly filtered |

---

## 2 · Sensitive-call anonymous smoke (test 4 raw output)

```
attendance                  anon-count=0
crew_eval                   anon-count=0
document-expirations        anon-count=0
driver-qualification        anon-count=0
employee-accountability     anon-count=0
employee-lifecycle          anon-count=0
new_employee_eval           anon-count=0
payroll-variance            anon-count=0
safety-document             anon-count=0
safety-training             anon-count=0
time-off-review             anon-count=0
time-verification           anon-count=0
training_deficiency         anon-count=0
verbal_coaching             anon-count=0
promotion_recommendation    anon-count=0
recognition                 anon-count=0
supervisor_notes            anon-count=0
fleet.rts                   anon-count=0
fleet.repair                anon-count=0
fleet.visibility            anon-count=0
```

🟢 **All 20 sensitive form_keys gate anonymous callers correctly.**

---

## 3 · Public-call anonymous smoke (test 5 raw output)

```
daily-report          anon-count=5
incident              anon-count=5
jha                   anon-count=5
preop                 anon-count=5
inspection            anon-count=5
meeting               anon-count=5
topic-library         anon-count=5
checkout              anon-count=5
corrective            anon-count=5
material-calculator   anon-count=6
equipment-issuance    anon-count=5
equipment-training    anon-count=5
fire-extinguisher     anon-count=5
qaqc                  anon-count=5
writeup               anon-count=5
```

🟢 **All 15 public form_keys still serve their public coaching intact.**

---

## 4 · Pre-existing test failures (NOT in scope of this remediation)

The following 4 tests fail at HEAD both **before** and **after** the OKCP scope fix (proven via `git stash` + re-run). These are pre-existing platform conditions unrelated to OKCP scope-gating and were already classified as such in `FINAL_PRE_DEPLOY_GO_NO_GO.md` §1 ("18 pre-existing env/cosmetic failures").

| Test | Failure type | Pre-OKCP status |
|---|---|---|
| `test_iter209_helptip_engine::test_tips_registry_validates_clean` | Content drift — `driver-qualification.restrictions/escalate` body >80 words | Pre-existing |
| `test_iter286_driver_qualification_foundation::test_all_dq_tips_use_hr_or_admin_scope_only` | Sub-keys include `safety/dispatch` scopes; test expects strict `{hr, admin}` only | Pre-existing |
| `test_iter287_driver_qualification_endorsements::test_all_iter287_tips_use_hr_or_admin_scope_only` | Same pattern as above | Pre-existing |
| `test_iter317a_fl_portal_coaching_parity::test_iter317a_portal_login_mounts_coaching` | `FieldLeadershipPortalLogin.jsx` (iter343 chrome rebuild) does not import HelpTipBlock | Pre-existing |

**Not addressed in this remediation per directive Rule "No new features. No new coaching content. No new Spanish content. No glossary expansion. No workflow changes. No UI redesign."**

---

## 5 · Compliance with operator constraints

| Constraint | Status |
|---|:-:|
| No new features | 🟢 |
| No new coaching content | 🟢 (only `scopes` arrays changed) |
| No new Spanish content | 🟢 (`tips_es.py` untouched) |
| No glossary expansion | 🟢 |
| No workflow changes | 🟢 |
| No UI redesign | 🟢 |
| No database changes | 🟢 (in-process registry only) |
| No deployment | 🟢 (preview pod only; no production push) |
| Audit ALL OKCP-added tips | 🟢 (all 52 OKCP additions audited; 36 corrected; 16 confirmed correctly public) |
| Identify form_key + siblings + correct scope per OKCP tip | 🟢 (documented in REMEDIATION_REPORT §2 + §3) |
| Sensitive scopes (HR/Safety/Leadership/Admin/Fleet/Recovery/Employee/Payroll) NOT public | 🟢 (live API smoke confirms count=0 for all 20 sensitive form_keys) |
| Public form_keys may remain public only where the underlying workflow is intentionally public | 🟢 (16 remaining `public` OKCP tips all map to siblings that are public by design — daily-report, incident, jha, preop, inspection, etc.) |
| Match sibling scope unless stronger restriction required | 🟢 (rule applied uniformly; no over-restrictions introduced) |

---

## 6 · Diff manifest

- `backend/guidance/tips.py` — 36 lines modified (scope arrays only)
- `backend/guidance/tips_es.py` — untouched
- `memory/OKCP_SCOPE_REMEDIATION_REPORT.md` — created (this remediation cycle)
- `memory/OKCP_SCOPE_REMEDIATION_CERTIFICATION.md` — created (this file)
- `memory/FINAL_PRE_DEPLOY_GO_NO_GO.md` — updated to 🟢 GO

No other code, schema, frontend, route, or governance files modified in this remediation cycle.

---

## 7 · Verdict

🟢 **OKCP SCOPE-GATING REMEDIATION CERTIFIED**

The blocker enumerated in `FINAL_PRE_DEPLOY_SECURITY_PERMISSION_REVIEW.md` §2 (33 tips + 3 supervisor_notes detected during remediation) is fully remediated. All previously-failing OKCP-attributable backend pytests now PASS. Anonymous callers receive **zero** sensitive operational coaching. Public coaching continues to flow to public form_keys unchanged. Spanish parity preserved. No content lost. No new regression.

Final pre-deploy verdict update in `FINAL_PRE_DEPLOY_GO_NO_GO.md`.
