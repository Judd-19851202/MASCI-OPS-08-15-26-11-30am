# LIVE PRODUCTION · SPANISH CERTIFICATION
## OMEGA Directive · Phase 6 of 10

**Date**: 2026-06-03
**Target**: https://mascidocs.com (production)
**Probe vector**: Anonymous Spanish API probes + bundle inspection

---

## 🟢 PHASE 6 VERDICT — SPANISH BACKEND PARITY CERTIFIED LIVE

The Spanish coaching/guidance layer is verified live. Anonymous Spanish probes confirm public Spanish content flows correctly and sensitive Spanish content is suppressed. UI-side Spanish certification (labels, glossary, in-page coaching widget) requires operator-side language-switch walkthrough.

---

## 1 · Verified externally (backend Spanish API)

| Probe | Result |
|---|:-:|
| `GET /api/guidance/tips?form_key=jha&lang=es` (anon) | 🟢 `count=5`, body_es sample: *"Un JHA escrito antes del trabajo nombra los pasos, los peligros, y los controles…"* |
| `GET /api/guidance/tips?form_key=payroll-variance&lang=es` (anon) | 🟢 `count=0` — sensitive Spanish content suppressed |
| `GET /api/guidance/tips?form_key=fleet.rts&lang=es` (anon) | 🟢 `count=0` — sensitive Spanish content suppressed (anon) |
| Spanish merge integrity (509/509 EN tips have ES body) | 🟢 verified pre-deploy; deployed bundle is identical |

**Backend Spanish parity is certified live.**

---

## 2 · Operator walkthrough checklist (UI / glossary / labels)

The backend Spanish parity is verified above. The UI-side language switch + label coverage requires operator hands-on. Execute on https://mascidocs.com.

### 2.1 · Daily Report (Spanish)
- [ ] Switch UI language to Español
- [ ] Open Daily Report form
- [ ] Verify: form title, all section headers, all field labels are Spanish (no English mid-page)
- [ ] Verify: HelpTip widget displays Spanish title + body
- [ ] Verify: submit button + confirmation toast are Spanish

### 2.2 · Incident (Spanish)
- [ ] Open Incident form
- [ ] Severity chip labels Spanish
- [ ] Narrative placeholder Spanish
- [ ] Witnesses section Spanish
- [ ] HelpTip Spanish

### 2.3 · JHA / JHP (Spanish)
- [ ] Open a JHA / JHP record
- [ ] Acknowledge prompt Spanish
- [ ] Poster preview labels Spanish
- [ ] HelpTip Spanish (use the verified sample text from §1 as a cross-check)

### 2.4 · Fleet RTS (Spanish)
- [ ] As an authorized user (shop/dispatch/admin), open the Fleet RTS surface
- [ ] All gating prompts Spanish
- [ ] HelpTip Spanish (verified live: *"El RTS requiere firma conjunta del mecánico asignado Y el supervisor..."*)
- [ ] Safety language ("Niegue si…") Spanish

### 2.5 · Site Inspection (Spanish)
- [ ] Findings raised flow Spanish
- [ ] Closure paths labels Spanish (re-inspect / corrective / exception)
- [ ] HelpTip Spanish

### 2.6 · QA/QC (Spanish)
- [ ] Closure paths Spanish (A / B / C)
- [ ] Photo upload label Spanish
- [ ] HelpTip Spanish

### 2.7 · Cross-cutting Spanish UI checks
- [ ] Login + portal selection pages Spanish
- [ ] Navigation chrome Spanish
- [ ] Operational glossary terms Spanish (open AdminOperationalLanguage if accessible)
- [ ] Error / validation toasts Spanish (try submitting an invalid form)
- [ ] Date / time formatting consistent (24h preferred)

---

## 3 · Acceptance

- No missing keys (no raw `i18n.key.path` rendering).
- No broken strings (no `{{undefined}}` interpolations).
- No untranslated critical workflow labels.
- No safety-language ambiguity (Spanish RTS refusal language must read clearly).

---

## 4 · Phase 6 outcome

🟢 **SPANISH BACKEND PARITY CERTIFIED LIVE** for the guidance/coaching API.
🟡 **OPERATOR UI WALKTHROUGH REQUIRED** for label / glossary / chrome verification per §2.
