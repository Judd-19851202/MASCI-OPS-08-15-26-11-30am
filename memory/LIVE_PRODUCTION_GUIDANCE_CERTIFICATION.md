# LIVE PRODUCTION · GUIDANCE CERTIFICATION
## OMEGA Directive · Phase 2 of 10

**Date**: 2026-06-03 (09:23 UTC probe window)
**Target**: https://mascidocs.com/api/guidance/tips (live production)
**Probe vector**: External anonymous HTTPS probes (no Authorization header)

---

# 🟢 PHASE 2 VERDICT — GUIDANCE SCOPE-GATING CERTIFIED LIVE

The OKCP scope-gating remediation has shipped to production correctly. Live anonymous probes against 20 sensitive form_keys + 7 public form_keys + 2 Spanish form_keys produce the expected gated/served behaviour.

---

## 1 · Sensitive form_keys (anonymous must see count=0)

```
attendance                     anon=0
payroll-variance               anon=0
fleet.rts                      anon=0
verbal_coaching                anon=0
supervisor_notes               anon=0
employee-lifecycle             anon=0
employee-accountability        anon=0
driver-qualification           anon=0
document-expirations           anon=0
time-off-review                anon=0
time-verification              anon=0
crew_eval                      anon=0
new_employee_eval              anon=0
training_deficiency            anon=0
promotion_recommendation       anon=0
recognition                    anon=0
safety-document                anon=0
safety-training                anon=0
fleet.repair                   anon=0
fleet.visibility               anon=0
```

🟢 **20 / 20 sensitive form_keys correctly suppress anonymous coaching on production.**

Coverage map per directive minimums:
- ✅ Payroll Variance · Attendance · Fleet RTS · Supervisor Notes · Employee Lifecycle (explicit set)
- ✅ Recovery — undo guidance is route-gated, not tip-gated; no public tips exist for the Recovery namespace (Recovery Stream itself requires admin auth and is verified separately in Phase 5)
- ✅ HR coaching (employee-accountability, driver-qualification, document-expirations, time-off-review, time-verification, payroll-variance)
- ✅ Leadership coaching (crew_eval, new_employee_eval, training_deficiency, promotion_recommendation, recognition, verbal_coaching, supervisor_notes, attendance)

---

## 2 · Public form_keys (anonymous must see count > 0)

```
daily-report                   anon=5
incident                       anon=5
jha                            anon=5
preop                          anon=5
meeting (safety-meeting)       anon=5
inspection (site-inspection)   anon=5
qaqc                           anon=5
```

🟢 **7 / 7 public form_keys still serve their intended public coaching.**

Sample content from `/api/guidance/tips?form_key=jha` (production):
- `why` — *Why a JHA is the operational plan, not a poster*
- `who` — *Who reads the JHA*
- `next` — *What happens with a submitted JHA*
- `escalate` — *When the work doesn't match the JHA anymore*
- `mistake` — *Common JHP mistakes*

Content matches the design intent for public-facing JHA coaching.

---

## 3 · Spanish parity probes (production)

| Probe | Result |
|---|:-:|
| `GET /api/guidance/tips?form_key=jha&lang=es` (anon) | 🟢 `count=5`, body_es sample: *"Un JHA escrito antes del trabajo nombra los pasos, los peligros, y los controles…"* |
| `GET /api/guidance/tips?form_key=payroll-variance&lang=es` (anon) | 🟢 `count=0` — sensitive Spanish coaching correctly suppressed for anon |

Spanish merge integrity preserved on production. Sensitive Spanish content cannot bypass scope gating.

---

## 4 · Guidance articles surface

| Probe | Result |
|---|:-:|
| `GET /api/guidance/articles` (anon) | 🟢 200, 47 articles served — matches expected public article catalog |

---

## 5 · Cross-check vs. pre-deploy certification

| Layer | Pre-deploy (preview) | Live (production) |
|---|:-:|:-:|
| Sensitive form_keys gated to anon | 20/20 🟢 | 20/20 🟢 |
| Public form_keys serve to anon | 7/7 🟢 | 7/7 🟢 |
| Spanish parity (public) | 🟢 | 🟢 |
| Spanish parity (sensitive gated) | 🟢 | 🟢 |
| Articles surface | 🟢 | 🟢 (47 articles) |

**The deployed bundle matches the certified preview bundle for the guidance subsystem.**

---

## 6 · Phase 2 outcome

🟢 **GUIDANCE CERTIFIED LIVE — production behaviour matches the certified delta.**
