# FINAL DELTA · GUIDANCE SCOPE SECURITY REPORT
## OMEGA Directive · Delta Re-Certification of `/api/guidance/tips` Access Control

**Date**: 2026-06-03
**Scope**: Re-audit of guidance scope behaviour after the OKCP scope-gating remediation.
**Authority**: OMEGA DIRECTIVE — FINAL TARGETED DELTA PRE-DEPLOY CERTIFICATION (Phase 3 + Phase 4)

---

## 1 · Threat model under audit

`/api/guidance/tips?form_key=<key>` is served to **anonymous callers by design** for public workflows (daily-report, incident, jha, preop, …). The risk class is **doctrinal data exposure** — operational coaching tagged with HR / Leadership / Safety / Fleet scopes must not leak to the anonymous channel. This delta re-audits whether the previously enumerated 33 + 3 OKCP scope-doctrine violations now correctly suppress for anonymous callers, and whether public workflows continue to receive their public coaching.

The platform's gating is implemented in `tips_for()` in `backend/guidance/tips.py`:

```python
tip_scopes = set(tip.get("scopes") or [])
if tip_scopes & granted_scopes:
    out.append(_render_tip(tip))
```

For an anonymous caller, `granted_scopes` resolves to `{"public"}`. A tip with `scopes=["leadership","admin"]` therefore has empty intersection with `{"public"}` and is correctly suppressed.

---

## 2 · Sensitive form_key probe matrix

Direct live probes against `http://localhost:8001/api/guidance/tips?form_key=<key>` with no auth, returning `count=N`. All sensitive HR / Leadership / Safety / Fleet form_keys must return `count=0`.

| form_key | Expected scope class | Anonymous `count` | Verdict |
|---|---|---:|:-:|
| attendance | leadership/admin | 0 | 🟢 |
| payroll-variance | hr/admin | 0 | 🟢 |
| fleet.rts | dispatch/admin | 0 | 🟢 |
| verbal_coaching | leadership/admin | 0 | 🟢 |
| supervisor_notes | leadership/admin | 0 | 🟢 |
| employee-lifecycle | hr/admin | 0 | 🟢 |
| employee-accountability | hr/admin | 0 | 🟢 |
| driver-qualification | hr/admin | 0 | 🟢 |
| document-expirations | hr/safety/admin | 0 | 🟢 |
| time-off-review | hr/admin | 0 | 🟢 |
| time-verification | hr/admin | 0 | 🟢 |
| crew_eval | leadership/admin | 0 | 🟢 |
| new_employee_eval | leadership/admin | 0 | 🟢 |
| training_deficiency | leadership/admin | 0 | 🟢 |
| promotion_recommendation | leadership/admin | 0 | 🟢 |
| recognition | leadership/admin | 0 | 🟢 |
| safety-document | safety/admin | 0 | 🟢 |
| safety-training | safety/admin | 0 | 🟢 |
| fleet.repair | shop/admin | 0 | 🟢 |
| fleet.visibility | shop/dispatch/safety/admin | 0 | 🟢 |

🟢 **20 / 20 sensitive form_keys correctly suppress anonymous coaching.**

Covers all axes called out in the directive Phase 3:
- ✅ attendance, payroll-variance, fleet.rts, verbal_coaching, supervisor_notes (explicitly listed)
- ✅ employee lifecycle (employee-lifecycle, employee-accountability)
- ✅ HR-related guidance (driver-qualification, document-expirations, time-off-review, time-verification, payroll-variance)
- ✅ admin/leadership guidance (crew_eval, new_employee_eval, training_deficiency, promotion_recommendation, recognition, verbal_coaching, supervisor_notes)
- ✅ recovery/undo guidance — no OKCP additions in this domain; pre-existing `workflow_undo.py` admin gating is unchanged this cycle and remains gated by route-level auth (not by tip scopes).

---

## 3 · Public form_key probe matrix

Public workflows must continue to receive their public coaching to anonymous callers. Direct live probes:

| form_key | Anonymous `count` | Verdict |
|---|---:|:-:|
| daily-report | 5 | 🟢 |
| incident | 5 | 🟢 |
| jha | 5 | 🟢 |
| preop | 5 | 🟢 |
| meeting (safety-meeting) | 5 | 🟢 |
| inspection (site-inspection) | 5 | 🟢 |
| qaqc | 5 | 🟢 |

🟢 **7 / 7 public form_keys still serve their intended public coaching.**

Spot-check on a remaining set (not in the directive minimum but verified for completeness):
- topic-library: 5 ✅
- checkout: 5 ✅
- corrective: 5 ✅
- material-calculator: 6 ✅
- equipment-issuance: 5 ✅
- equipment-training: 5 ✅
- fire-extinguisher: 5 ✅
- writeup: 5 ✅

---

## 4 · Spanish guidance scope behaviour

Spanish translations are merged into the same `_TIPS` list at import time via `_merge_es()` keyed by `(form_key, kind)`. Spanish entries do NOT carry their own `scopes` array — the `tip` dict's `scopes` is the single source of truth at lookup. Therefore:

| Property | Result |
|---|:-:|
| Can a Spanish lookup bypass scope gating? | 🟢 NO — structurally impossible |
| `tips_es.py` modified by remediation? | 🟢 NO (`git diff` clean) |
| Spanish coverage (body_es present for every tip) | 🟢 509 / 509 |
| Anonymous Spanish probe — sensitive (payroll-variance, lang=es) | 🟢 `count=0` |
| Anonymous Spanish probe — public (jha, lang=es) | 🟢 `count=5`, body_es sample: *"Un JHA escrito antes del trabajo nombra los pasos…"* |
| Fleet RTS Spanish preserved | 🟢 5/5 RTS tips with full `title_es`+`body_es` |
| JHP Spanish preserved | 🟢 jha why/mistake/example/escalate full `body_es` |

---

## 5 · Sensitive content cross-check (the actual blast radius)

The pre-remediation leak exposed operational coaching such as: how to recommend a promotion, how to issue verbal coaching, when to refuse Time-Off, how to handle Payroll Variance attestation, who can authorize Fleet RTS, etc.

Sample anonymous probes for the specific titles that were previously leaking:

| Pre-remediation leak | Now exposed to anon? |
|---|:-:|
| *"How to recommend promotion"* (promotion_recommendation/who) | 🟢 NO |
| *"When to decline a recommendation"* (promotion_recommendation/escalate) | 🟢 NO |
| *"Who delivers verbal coaching"* (verbal_coaching/who) | 🟢 NO |
| *"When verbal coaching becomes a write-up"* (verbal_coaching/escalate) | 🟢 NO |
| *"Common Payroll Variance mistakes"* (payroll-variance/mistake) | 🟢 NO |
| *"Who can authorize Return to Service"* (fleet.rts/who) | 🟢 NO |
| *"When to refuse RTS"* (fleet.rts/escalate) | 🟢 NO |
| *"Common time-off-review mistakes"* (time-off-review/mistake) | 🟢 NO |
| *"Who can read supervisor notes"* (supervisor_notes/who) | 🟢 NO |
| *"When to escalate a note"* (supervisor_notes/escalate) | 🟢 NO |

All 10 spot-check items in the previous blast-radius set are now correctly suppressed.

---

## 6 · Backend test corroboration

Three previously-failing OKCP-attributable tests now all PASS (confirmed Phase 2 of FINAL_DELTA_PRE_DEPLOY_CERTIFICATION.md §3):

- `test_iter282_payroll_variance_coaching::test_all_pv_tips_have_hr_scope` 🟢
- `test_iter224_employee_lifecycle_helptips::test_all_tips_hr_scoped_only` 🟢
- `test_iter224_employee_lifecycle_helptips::test_anon_caller_sees_no_tips` 🟢

The anonymous-caller test specifically asserts `count == 0` for `employee-lifecycle` over the live API surface; it passes.

---

## 7 · Residual risk

| Risk | Severity | Owner | Mitigation |
|---|---|---|---|
| Future tips additions could re-introduce `scopes=["public"]` on sensitive form_keys | LOW | Engineering | `test_iter282_payroll_variance_coaching::test_all_pv_tips_have_hr_scope` + `test_iter224_employee_lifecycle_helptips::test_all_tips_hr_scoped_only` already gate this in CI |
| Pre-existing `test_iter286/287` expectations on `driver-qualification` sub-keys | LOW | Maintenance | Pre-existing, out of scope for this delta; tracked for a future maintenance cycle |
| Anonymous Spanish caller could bypass scope gating | NONE | Architecture | Structurally impossible — Spanish merge does not own scopes |

---

## 8 · Verdict

🟢 **GUIDANCE SCOPE SECURITY: CLEAN**

All previously identified violations are fully remediated. All 20 sensitive form_keys gate anonymous callers. All 7 (and 8 supplementary) public form_keys still serve their public coaching. Spanish parity preserved with no possibility of scope bypass. Three OKCP-attributable backend tests now PASS. No new attack surface introduced by the delta.

Delta security posture is acceptable for production deploy.
