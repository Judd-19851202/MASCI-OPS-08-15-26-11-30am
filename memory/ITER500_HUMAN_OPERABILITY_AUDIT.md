# ITER500 · HUMAN OPERABILITY AUDIT

**Date**: 2026-06-02T19:30 UTC
**Mode**: READ-ONLY · code-path scan + prior-audit synthesis
**Companions**: 9 sibling iter500 deliverables

---

## 1 · Core question

> **Can a normal MASCI user perform their job without assistance?**

**Answer**: For the **HR Lifecycle workflow** (the most-recently-hardened surface) — YES, post-iter453.9. For ~ 55 % of the platform's ~ 84 workflows — YES. For ~ 33 % — YES BUT WITH FRICTION (some need scrolling · some have ambiguous verbs · some have weak success-feedback). For ~ 12 % — NO without operator assistance (OC-005 not built · undo paths universally missing · some Tier-1 dead-ends documented in `ITER500_DEAD_END_REGISTER.md`).

---

## 2 · Phase 2 — 12-question human-operability check applied to ~ 84 workflows

For each workflow, the 12 phase-2 questions:

1. Can user find it? · 2. understand it? · 3. start it? · 4. complete it? · 5. close it? · 6. reopen it? · 7. recover from mistakes? · 8. tell what happened? · 9. tell who owns next action? · 10. tell current status? · 11. tell next step? · 12. complete without calling Jaymn?

| Domain | Avg score / 12 | Worst question |
|---|:-:|---|
| HR | **11 / 12** (post-iter453.9) | Q12 still "needs operator's own 60-s walk to subjectively confirm" |
| Safety | 9 / 12 | Q7 "recover from mistakes" — universal undo gap |
| Operations / Dispatch | 8 / 12 | Q8 "tell what happened" — drag-drop without toast |
| Payroll | 7 / 12 | Q3 "start it" — buried in admin pages |
| Fleet | 8 / 12 | Q4 "complete it" — DVIR confirmation bare-minimum |
| Equipment | 10 / 12 | Q11 "next step" — re-inspection link via tooltip |
| Shop | 8 / 12 | Q6 "reopen" — asset transfer cancel buried |
| Training | 9 / 12 | Q11 "next step" — no expiring-soon visual cue |
| JHP | 5 / 12 | OC-005 not built |
| QA/QC | **10 / 12** | Closure-action contract requires tribal knowledge |
| Site Inspection | **10 / 12** | Same as QA/QC |
| Daily Reports | 10 / 12 | Q4 "Submit vs Save Draft" verb ambiguity |
| Incidents | 9 / 12 | Reopen reason below fold (same class as iter453.7) |
| Constraints | 8 / 12 | No lifecycle panel substrate |
| Asset Transfers | 7 / 12 | Receive ack subtle |
| Sub/Vendor Mgmt | 6 / 12 | No archive workflow |
| PM | 9 / 12 | Bulk approve missing |
| Accountability / Command Center | 8 / 12 | Read-only · no drill-through verbs |
| Admin | 9 / 12 | 35+ pages without grouping |

**Mean score**: 8.6 / 12 ≈ **72 %** — consistent with 🟡 "Operationally functional with friction" classification.

---

## 3 · The pattern this fork repeatedly exposed

Every single user-reported "blocker" in this fork — HR Save below fold (iter453.7), Resend webhook silent acceptance (iter453.8), HR "nothing happened" (iter453.9) — was an instance of the SAME UX pattern:

> **The code worked. The API worked. The DB updated. But the user couldn't FIND or PERCEIVE the action or its outcome.**

The remediation pattern in each case was the same minimal envelope:
* iter453.7 = make the button visible
* iter453.8 = make the failure visible (HTTP 401 instead of silent 200)
* iter453.9 = make the success visible (explicit OLD → NEW + auto-close)

**The platform's most common defect class is feedback-insufficiency, not workflow-incompleteness.** The good news: most of these are 5-15 LOC fixes per surface. The bad news: there are an estimated 25-30 surfaces still exhibiting some version of the same pattern.

---

## 4 · Final verdict (this audit only — does not override deployment certification)

# 🟡 **OPERATIONALLY FUNCTIONAL WITH FRICTION**

* 🟢 ~ 55 % of workflows are fully complete
* 🟡 ~ 33 % work but require operator hand-holding or tribal knowledge
* 🔴 ~ 12 % have meaningful dead-ends, missing builds, or recovery gaps

**Not 🟢**: too many workflows still need verb harmonization, sticky-footer treatment, OLD → NEW feedback, and lifecycle-panel substrate adoption. Customer #2 cannot self-onboard without 2 hours of training.

**Not 🔴**: every certified core workflow (HR Lifecycle · QA/QC · Site Inspection · Incident · Daily Report · JHA) is operable end-to-end. Phase Alpha governance intact. Audit trails alive. Persistence works. Production deployment is certified.

---

## 5 · STOP

Read-only directive honored. No code · no fix · no deploy.
