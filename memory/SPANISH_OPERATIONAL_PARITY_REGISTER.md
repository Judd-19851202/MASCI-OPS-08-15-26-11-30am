# SPANISH OPERATIONAL PARITY REGISTER
## OCEP · Operational Coaching & Spanish Parity Completion Program (OCSPCP) · 2 of 7

**Date**: 2026-06-03
**Authority**: OMEGA / FOCP DIRECTIVE — OCSPCP
**Mode**: READ-ONLY · source-direct · NO translation · NO engineering
**Evidence rule**: Spanish operational parity is defined as **same decisions, same risks, same workflows** — not literal translation. This register measures parity by layer.

---

## 1 · The three-layer parity model (single source of truth)

| Layer | Source | Function | Coverage |
|---|---|---|---|
| **A — UI strings** | `frontend/src/lib/i18n.js` (4902 LOC · ~3218 ES keys) | Page titles, labels, buttons, toast errors | 🟢 **Comprehensive** — every platform page surfaces ES copy via `useT()` |
| **B — Coaching bodies** | `backend/guidance/tips.py` `body_es` field per tip | The `why / who / when / mistake / example / next / escalate` content inside `HelpTip` blocks | 🔴 **≈ 0.24%** — 1 of ~412 tips populates `body_es` (sole instance: `jha.poster`) |
| **C — Topic library content** | `frontend/src/lib/topics/*.es.js` (23 files · 1579 LOC) | Safety Meeting topic prose (`incident_pattern`, `hazards_reviewed`, etc.) | 🟢 **Decision-grade**, sample-verified (`excavation.es.js` SOCP §2.3, §7.2) |
| **D — Glossary** | `AdminOperationalLanguage.jsx` (509 LOC, ~50 EN+ES entries) | Operational vocabulary | 🟢 **Canonical**; admin-route-only (in-flow wiring unimplemented per AdminOperationalLanguage line 5) |
| **E — Training content** | `frontend/src/data/training_es.js` (1093 LOC) | Training track curriculum | 🟢 Present |
| **F — Backend Spanish-aware routes/PDFs** | 13 files (PDFs, sentry tags, dispatch continuity, JHP acks, etc.) | Bilingual artifacts | 🟢 Coverage exists for the artifacts surveyed |

**Aggregate verdict**: 5 of 6 Spanish layers are 🟢. **Layer B is the single non-🟢 layer.** Per the directive's parity definition, the Spanish operator can:
- Read every page (Layer A ✅)
- Read every safety topic (Layer C ✅)
- Look up every glossary term (Layer D ✅ — though admin-only)
- Read training content (Layer E ✅)
- Read every PDF (Layer F ✅)

…but cannot read the inline coaching that explains **why** / **common mistakes** / **what happens next** in their primary language (Layer B 🔴). Under a Spanish locale, the `HelpTip` block renders ES labels (`"Por qué importa"`, `"Errores comunes"`) above EN bodies. This is functional but defeats coaching purpose.

---

## 2 · Per-workflow Spanish parity (36 inventoried workflows)

Composite verdict = WORST of (Layer A · Layer B · per-workflow-applicable layers C/D/E/F).

| # | Workflow | Layer A (UI) | Layer B (Coach) | Layers C/D/E/F | Composite |
|---|---|:-:|:-:|:-:|:-:|
| 1 | JHP + Ack | 🟢 | 🟡 (1 of 8 tips ES) | D · F | 🟡 |
| 2 | Safety Meeting | 🟢 | 🔴 | C · D | 🔴 |
| 3 | Incident Report | 🟢 | 🔴 | D · F | 🔴 |
| 4 | Site Inspection | 🟢 | 🔴 | D | 🔴 |
| 5 | QA/QC Inspection | 🟢 | 🔴 | D | 🔴 |
| 6 | CAPA | 🟢 | 🔴 | D | 🔴 |
| 7 | Equipment Pre-op | 🟢 | 🔴 | — | 🔴 |
| 8 | Equipment Issuance | 🟢 | 🔴 | — | 🔴 |
| 9 | Equipment Training | 🟢 | 🔴 | E | 🔴 |
| 10 | **Fleet Repair/RTS** | 🟢 | 🔴 (Fleet RTS has 2 tips with body_es=0) | D (RTS partial) | 🔴 (highest risk) |
| 11 | Fire Extinguisher | 🟢 | 🔴 | — | 🔴 |
| 12 | Safety Topic Library | 🟢 | 🔴 (4 library tips) | C 🟢 23 ES files | 🟡 (topic content rich; library-meta tips lack ES) |
| 13 | Safety Document | 🟢 | 🔴 | — | 🔴 |
| 14 | Safety Training record | 🟢 | 🔴 | E 🟢 (training_es.js 1093 LOC) | 🟡 |
| 15 | Daily Report | 🟢 | 🔴 | F (PDF) | 🔴 |
| 16 | Dispatch | 🟢 | 🔴 | F (continuity, debrief) | 🔴 |
| 17 | Document Expirations | 🟢 | 🔴 | — | 🔴 |
| 18 | Driver Qualification | 🟢 | 🔴 | — | 🔴 |
| 19 | Employee Accountability | 🟢 | 🔴 | — | 🔴 |
| 20 | Employee Lifecycle | 🟢 | 🔴 | D 🟢 | 🟡 |
| 21 | Payroll Variance | 🟢 | 🔴 | D | 🔴 |
| 22 | Field Leadership Portal | 🟢 | 🔴 | F | 🔴 |
| 23 | Time-Off Review | 🟢 | 🔴 | — | 🔴 |
| 24 | Time Verification | 🟢 | 🔴 | — | 🔴 |
| 25 | Discipline cluster | 🟢 | 🔴 | — | 🔴 |
| 26 | Equipment Checkout/Return | 🟢 | 🔴 | — | 🔴 |
| 27 | Material Calculator | 🟢 | 🔴 | — | 🔴 |
| 28 | Attendance | 🟢 | 🔴 (2 tips, no ES) | — | 🔴 |
| 29 | Asset Transfer | 🟢 | n/a (no tips) | — | 🟡 (UI only) |
| 30 | Operational Constraints | 🟢 | n/a | — | 🟡 |
| 31 | Vendor Management | 🟢 | n/a | — | 🟡 |
| 32 | PM Hub | 🟢 | n/a | — | 🟢 |
| 33 | HR Hub | 🟢 | n/a | — | 🟢 |
| 34 | Public Time-Off | 🟢 | n/a | — | 🟢 |
| 35 | Universal Undo / Recovery Stream | 🟡 (FOCP R2 § 8 EN-canonical doctrine) | n/a | — | 🟡 (DOCTRINE-EXEMPT) |
| 36 | Submittals | ⛔ NOT-IMPLEMENTED | n/a | n/a | n/a |

**Verdict distribution**: 🟢 3 · 🟡 8 · 🔴 24 · n/a 1.

**Aggregate composite Spanish parity**: **3 / 35 = 8.5% GREEN · 23% YELLOW · 68.5% RED**.

---

## 3 · Operational-intent parity (Phase 2 of directive)

The directive requires translation of **operational intent, not literal text**. This means the ES tip body must answer the same 10 questions as the EN tip body for the operator's job context. Source-direct evidence on existing ES tips:

| Sample tip with body_es | Operational intent verdict |
|---|---|
| `jha.poster` (the sole tip with body_es) | Verified to anchor the same operational intent as the EN body — confirms infrastructure works end-to-end. The single-instance proof point exists. |

**No other safety-or-non-safety tip has been written with body_es.** This means there is no further evidence to evaluate — the gap is content authoring, not infrastructure.

---

## 4 · What 95%+ ES GREEN requires (informational, not authorizing)

To reach the directive's target state (95%+ GREEN at Spanish parity composite):

| Step | Scope | Type |
|---|---|---|
| Lift `body_es` content to all 92 tips that have `mistake` kind | 92 ES tips | Content authoring |
| Lift `body_es` content to all 155 tips that have `why` kind | 155 ES tips | Content authoring |
| Lift `body_es` content to all 74 tips that have `next` kind | 74 ES tips | Content authoring |
| Lift `body_es` to remaining 90 tips (escalate/example/who/when/etc.) | 90 ES tips | Content authoring |
| Wire AdminOperationalLanguage glossary in-flow (Layer D from admin-only to in-flow tooltip / link) | 0 new content, all 36 workflows | UI wiring |
| Wire LifecycleGuide on 8 unwired workflows + ES strings | 8 LifecycleGuide instances | Component wiring + ES copy via i18n.js |

**Net authoring scope**: ~412 ES tip bodies. None requires a new workflow, new module, new component, or new registry. Every one targets an existing `body_es` field on an existing tip record. Per FOCP Final Directive, each batch requires 7-test + 4-proof clearance — operator decides authorization.

Once the content batch ships, ES Composite GREEN rises to ~88% mechanically (every 🔴 row in Section 2 whose ES Layer B 🔴 closes flips to at least 🟡 — and most flip to 🟢 because Layers A, C/D/E/F are already GREEN). The remaining gap is the LifecycleGuide / glossary wiring (Layer A side), which lifts the residual 🟡 rows to 🟢.

---

## 5 · Retired false findings (Spanish parity)

| Inherited claim | Verdict | Disposition |
|---|---|---|
| "Spanish parity is ~52%" | Bimodal evidence: Layer A ≈ 100%, Layer B ≈ 0.24%. | **RETIRED** — replaced with two-layer model. |
| "Translation is needed" | The directive itself disclaims literal translation; what is needed is operational-intent ES authoring (Phase 2). Infrastructure exists; content does not. | **REFINED.** |
| "Spanish topic library is machine-translated" | `excavation.es.js` end-to-end sample (SOCP §2.3, §7.2): idiomatic field prose with concrete weights, OSHA citations, regional idioms. | **RETIRED.** |
| "Glossary covers all workflows" | Glossary entries exist (~50). They are admin-route-only and not linked from in-flow. | **REFINED.** |

---

## 6 · Per-role Spanish operational parity (directive's roles)

The directive names 7 roles that must achieve Spanish operational parity:

| Role | EN can do today | ES can do today (with Layer A only, no Layer B coaching) | Verdict |
|---|:-:|:-:|---|
| Spanish Superintendent | ✅ | 🟡 PARTIAL — can navigate, submit, and read records; cannot read inline coaching/mistakes content in ES | 🟡 PARTIAL |
| Spanish Foreman | ✅ | 🟡 PARTIAL — same as above; DR + JHP roster + Meeting facilitation operable; mistakes guidance EN-only | 🟡 PARTIAL |
| Spanish Safety Representative | ✅ | 🟡 PARTIAL — JHP/Meeting/Incident/Site/QAQC operable via Layer A + Layer C topic content; coaching depth EN-only | 🟡 PARTIAL |
| Spanish Equipment Manager | ✅ | 🔴 INSUFFICIENT — Fleet RTS Layer B coverage is 2 tips with body_es=0; SOCP §8.2 confirmed highest single-decision risk | 🔴 |
| Spanish Dispatcher | ✅ | 🟡 PARTIAL — 25 dispatch tips in EN; 0 in ES; backend dispatch_continuity has ES strings | 🟡 PARTIAL |
| Spanish PM | ✅ | 🟡 PARTIAL — Constraints, QA/QC, PM Hub operable in Layer A; coaching EN-only; Vendor archive missing (TR-0003) | 🟡 PARTIAL |
| Spanish Laborer | ✅ | 🟡 PARTIAL — JHP ack works for emailed laborers; ES-only-no-email laborer excluded (FOCP R2 § C2-0014) | 🟡 PARTIAL |

**Aggregate role parity verdict**: 🟡 PARTIAL for 6 of 7 roles · 🔴 for 1 (Equipment Manager via Fleet RTS).

---

**End of SPANISH OPERATIONAL PARITY REGISTER · OCSPCP 2 of 7**
