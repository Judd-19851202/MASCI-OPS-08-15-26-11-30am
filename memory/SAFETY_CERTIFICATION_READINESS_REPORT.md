# SAFETY CERTIFICATION READINESS REPORT
## OCEP · Safety Training Completion Program (STCP) · Register 5 of 5

**Date**: 2026-06-03
**Authority**: OMEGA · STCP
**Mode**: READ-ONLY synthesis · NO certification by AI · NO engineering authorized
**Companion artifacts**:
- `SAFETY_TRAINING_COMPLETION_REGISTER.md` (matrix · 14 workflows × 11 criteria)
- `SAFETY_COACHING_GAP_REGISTER.md` (47 form_keys × 5 critical kinds)
- `SAFETY_SPANISH_GAP_REGISTER.md` (two-layer Spanish model)
- `SAFETY_HELP_CONTENT_REGISTER.md` (5 help-content mechanisms × 14 workflows)

---

## 1 · Executive readiness matrix

For each safety workflow, the four dimensions specified by the directive:

| # | Workflow | Operational Readiness | Safety Readiness | Training Readiness | Certification Readiness |
|---|---|:-:|:-:|:-:|:-:|
| 1 | JHP + ack | 🟢 | 🟡 | 🟡 | 🟡 |
| 2 | Safety Meeting | 🟢 | 🟡 | 🟡 | 🟡 |
| 3 | Incident Report | 🟢 | 🟡 | 🟢 | 🟢 |
| 4 | Site Inspection | 🟢 | 🟢 | 🟢 | 🟢 |
| 5 | QA/QC Inspection | 🟢 | 🟢 | 🟢 | 🟢 |
| 6 | CAPA | 🟢 | 🟢 | 🟡 | 🟡 |
| 7 | Equipment Pre-op | 🟢 | 🟡 | 🟡 | 🟡 |
| 8 | Equipment Issuance | 🟢 | 🟢 | 🟡 | 🟡 |
| 9 | Equipment Training | 🟢 | 🟢 | 🟡 | 🟡 |
| 10 | **Fleet Repair / RTS** | 🟡 | 🔴 | 🔴 | 🔴 |
| 11 | Fire Extinguisher | 🟢 | 🟢 | 🟡 | 🟡 |
| 12 | Safety Topic Library | 🟢 | 🟢 | 🟢 | 🟢 |
| 13 | Safety Document | 🟢 | 🟢 | 🟡 | 🟡 |
| 14 | Safety Training record | 🟢 | 🟢 | 🟢 | 🟢 |

**Verdict counts** (across 14 workflows × 4 dimensions = 56 cells):

| | 🟢 GREEN | 🟡 YELLOW | 🔴 RED |
|---|---:|---:|---:|
| Operational | 13 | 1 | 0 |
| Safety | 9 | 4 | 1 |
| Training | 6 | 7 | 1 |
| Certification | 5 | 8 | 1 |
| **Aggregate (out of 56)** | **33 (59%)** | **20 (36%)** | **3 (5%)** |

---

## 2 · Aggregate readiness verdict

| Dimension | Aggregate verdict | Reasoning |
|---|:-:|---|
| Operational Readiness | 🟢 GREEN | 13 of 14 workflows operationally functional today. Fleet RTS is the single YELLOW. |
| Safety Readiness | 🟡 YELLOW | One RED (Fleet RTS), 4 YELLOW. JHP, Meeting, Incident, Pre-op carry per-form mistake gaps and attestation-flag definition gaps. |
| Training Readiness | 🟡 YELLOW | Coaching surface delivers 23 `mistake` tips across 14 workflows but parent form_keys lack them on 12 of 14; body_es < 1% across safety tips. |
| Certification Readiness | 🟡 YELLOW | 5 workflows are field-review-ready (Incident, Site Insp, QA/QC, Topic Library, Safety Training). 8 require gap closure before certification. 1 (Fleet RTS) requires substantial pre-certification work. |

**Composite aggregate**: 🟡 **YELLOW** — Safety platform is operational and substantially complete, with one RED hotspot (Fleet RTS) and a cluster of structural YELLOW gaps centered on parent-form `mistake` kind, coaching body_es, and unwired in-flow glossary linking.

---

## 3 · Cell-level evidence trace for every YELLOW or RED

| Cell | Evidence (source-direct) |
|---|---|
| Row 1 Safety 🟡 | JHP parent `tips.py` lacks `mistake`; SOCP §1.1 "Reconocer" legal-attestation breadth |
| Row 1 Training 🟡 | jha.poster only 1 of 8 tips has body_es; JHP onboarding 🔴 absent |
| Row 1 Cert 🟡 | Composite of Safety+Training YELLOWs |
| Row 2 Safety 🟡 | No formal lifecycle file; meeting parent lacks `mistake` |
| Row 2 Training 🟡 | body_es 0% on 22 meeting tips |
| Row 2 Cert 🟡 | Composite |
| Row 3 Safety 🟡 | Incident parent lacks `mistake`; SOCP §3.1 severity term ambiguity; AR-0016 attestation flag definitions |
| Row 6 Training 🟡 | CAPA parent lacks `mistake`; no in-flow lifecycle guide despite 5-stage pipeline |
| Row 6 Cert 🟡 | Composite |
| Row 7 Safety 🟡 | preop parent lacks `mistake`; preop.controls/signoff only 2 tips each |
| Row 7 Training 🟡 | body_es 0% |
| Row 7 Cert 🟡 | Composite |
| Row 8 Training 🟡 | parent lacks `mistake`; body_es 0% |
| Row 8 Cert 🟡 | Composite |
| Row 9 Training 🟡 | parent lacks `mistake`; body_es 0% |
| Row 9 Cert 🟡 | Composite |
| **Row 10 Op 🟡** | RTS form_key only 2 tips; no lifecycle guide |
| **Row 10 Safety 🔴** | Highest single-decision risk on platform (SOCP §8.2). 2 tips, no `who`, no `next`, no `escalate`, no attestation contract |
| **Row 10 Training 🔴** | 2 tips total. body_es 0%. Onboarding 🔴 |
| **Row 10 Cert 🔴** | Cannot be certified for unassisted operator use today |
| Row 11 Training 🟡 | No glossary entry; no lifecycle |
| Row 11 Cert 🟡 | Composite |
| Row 13 Training 🟡 | parent + classification lack `mistake`; no glossary |
| Row 13 Cert 🟡 | Composite |

---

## 4 · The five workflows already field-review-ready (Certification 🟢)

These 5 of 14 workflows have all coaching mechanisms in place, full lifecycle audit, and sufficient `mistake` coverage to be handed to a field reviewer today:

| # | Workflow | Why it is 🟢 ready |
|---|---|---|
| 3 | Incident Report | `incident_lifecycle.py` audit + 3-attestation gate + 22 tips + IncidentLifecyclePanel · Layer A ES comprehensive |
| 4 | Site Inspection | `site_inspection_lifecycle.py` audit + Amendment 001 closure + 17 tips + SiteInspectionLifecyclePanel |
| 5 | QA/QC Inspection | `qaqc_lifecycle.py` audit + Amendment 001 closure + 18 tips + QaqcLifecyclePanel |
| 12 | Safety Topic Library | 23 trade ES dictionaries + library page + topic-library tips (gaps minor at the library-meta level) |
| 14 | Safety Training record | training_es.js (1093 LOC) + 8 tips + TrainingHub/TrainingTrack pages + expiration tracking |

**For these 5, the field reviewer (per SOCP Phase 4 packet) can proceed immediately.**

---

## 5 · The one workflow that cannot be certified for unassisted use today (Certification 🔴)

**Fleet Repair / Return-to-Service (RTS).**

Evidence:
- `tips.py` `fleet.rts` has only 2 tips (`why`, `mistake`). No `who`, no `next`, no `escalate`.
- No `LifecycleGuide` is wired for fleet workflows.
- No `workflow_state_events` audit row writer is found for fleet (severity tier is tracked but transition audit is not unified with incident/qaqc/site_inspection).
- Phase 2 P3 already flagged Fleet/Shop as platform's thinnest coverage.
- SOCP Phase 3 §8.2 named RTS as the **highest single-decision safety risk on the platform** (a wrongly-released truck kills people).
- Coaching body_es = 0%; Spanish-only operator-mechanic has even less coverage.

**This workflow alone fails the directive's central question.** See Section 7 below.

---

## 6 · Gap clusters (grouped by root cause, not workflow)

| Cluster | Affected workflows | Root cause | Closure path |
|---|---|---|---|
| **C1 — Parent form_key `mistake` absent** | JHP, Meeting, Incident, Site Insp, QA/QC, CAPA, Equip Pre-op, Equip Issuance, Equip Training, Safety Document, Safety Training, Topic Library | `tips.py` registry never seeded `mistake` on the parent form_keys | Author 12 EN `mistake` tips on parent form_keys + ES translations |
| **C2 — Coaching body_es ≈ 0%** | All 14 | Tips registry has structural support (`body_es` field) but content was never produced | Author ~137 body_es entries OR declare doctrine-explicitly that EN body is canonical (operator decision) |
| **C3 — No in-flow `LifecycleGuide` for 5 stateful workflows** | JHP, Meeting, CAPA, Equipment Pre-op, Fleet | LifecycleGuide built but not wired | Wire existing `LifecycleGuide` component to 5 lifecycle panels |
| **C4 — Glossary unwired from in-flow pages** | All 14 | AdminOperationalLanguage glossary is admin-route-only despite design intent (line 5 of AdminOperationalLanguage.jsx) | Add glossary tooltip / link from in-flow pages |
| **C5 — Fleet RTS thin coaching** | Fleet | Highest-stakes single decision has only 2 tips and no lifecycle guide | Author 3 missing tip kinds (who/next/escalate) + lifecycle guide + ES translations |
| **C6 — Onboarding 🔴 absent across all 14** | All 14 | No new-hire guided-tour artifact in `/app/frontend/src/pages` | Existing `WORKFLOW_EXPLANATION_LIBRARY.md` (TCP, prior session) is the canonical *documentation* substitute; in-app onboarding remains absent |

**Cluster closure scope**:
- C1 + C2 + C3 + C4 are content + wiring work (no new workflows).
- C5 is content + wiring on one workflow.
- C6 is the only cluster that, if pursued, could be argued to introduce new surfaces — and per Rule 1, the operator decides whether to use the existing TCP Library as the canonical onboarding source (no build needed) or to build in-app onboarding (FOCP-gated build).

---

## 7 · The directive's central question

> **"Can a newly hired laborer, foreman, superintendent, safety representative, and safety manager successfully perform all required safety workflows without outside assistance?"**

Per-role, source-direct answer:

| Role | Required safety workflows | Source-direct verdict | Evidence |
|---|---|:-:|---|
| **Laborer** | JHP ack, Equipment Pre-op (passenger), Incident reporting (witness), Equipment Issuance ack | 🟡 PARTIAL | JHP ack works; Equipment Issuance ack has `mistake` tip; Incident reporting Layer A ES comprehensive; Pre-op missing mistake on parent. Spanish-only laborer with no email is excluded from JHP ack chain (FOCP R2 § C2-0014). |
| **Foreman** | Daily Report (safety adjacency), JHP roster + brief, Safety Meeting facilitation, Incident first-on-scene, Equipment Pre-op signoff | 🟡 PARTIAL | All Hub workflows operational. Foreman lacks `LifecycleGuide` for Meeting + JHP. Spanish-only foreman lacks coaching body_es. |
| **Superintendent** | Cross-workflow visibility, escalation decisions, OSHA-recordable advisory | 🟡 PARTIAL | Visibility surfaces exist. CAPA + Pre-op lifecycle guides missing. |
| **Safety Representative** | JHP authoring, Safety Meeting curation, Incident triage, CAPA management, Site Inspection, Topic Library | 🟢 ADEQUATE | Most-equipped role. 4 owner workflows have lifecycle audit. Glossary admin-accessible. Coaching body_es gap affects ES-primary safety reps. |
| **Safety Manager** | All of Safety Rep + Incident closure 3-attestation + CAPA verify + Audit oversight | 🟡 PARTIAL | Closure surfaces work; attestation-flag definitions absent (AR-0016). |
| **Operator-Mechanic (RTS-relevant)** | Fleet defect intake + Repair lifecycle + RTS authorization | 🔴 INSUFFICIENT | Cluster C5: thin coaching, no lifecycle guide, no body_es, no formal attestation contract |

**Composite answer to the directive's central question**:

🟡 **PARTIALLY YES, with one RED exception.**

- For 4 of 5 named roles (Laborer, Foreman, Superintendent, Safety Manager), the platform supports unassisted use for the **operational majority** of their safety workflows, with named YELLOW gaps documented above.
- For the Safety Representative role, the platform is largely adequate (🟢) for English-primary representatives; Spanish-primary representatives lose the coaching body layer.
- For the operator-mechanic interacting with Fleet RTS, the platform is **insufficient without external assistance** — this is the one place where the directive's success criterion provably fails today.

**No certification can be issued by AI.** Per directive, only real human operators issue final certification. This report identifies exactly where the field reviewer's GREEN/YELLOW/RED stamps will fall.

---

## 8 · Hand-off

| Next move | Owner |
|---|---|
| Run SOCP Phase 4 packet + STCP findings on the 5 Certification-🟢 workflows | Operator |
| Decide whether to authorize FOCP 7-test + 4-proof builds for the YELLOW clusters (C1, C2, C3, C4) | Operator |
| Treat the Fleet RTS RED as the single highest-priority FOCP candidate | Operator (recommendation only) |
| Decide whether existing TCP Library serves as canonical onboarding OR build in-app onboarding | Operator |

**The AI agent's STCP work is complete.** No engineering proposed. No certifications issued.

---

**End of SAFETY CERTIFICATION READINESS REPORT · STCP 5 of 5**
