# OPERATOR INDEPENDENCE REPORT
## OCEP · Operational Coaching & Spanish Parity Completion Program (OCSPCP) · 6 of 7

**Date**: 2026-06-03
**Authority**: OMEGA / FOCP DIRECTIVE — OCSPCP Phase 5
**Mode**: READ-ONLY · source-direct · NO engineering
**Purpose**: Evaluate every workflow against — "Can a brand-new employee complete this without calling Jaymn?" Verdict: YES · PARTIAL · NO. For every PARTIAL or NO, identify exactly what information is missing.

**Evidence basis**: Composite of OCSPCP 1–5 + STCP + SOCP + TCP findings. Every PARTIAL/NO ties to a specific source-direct gap already documented above.

---

## 1 · Operator-independence verdict matrix (35 active workflows × 2 languages)

| # | Workflow | EN operator-independent? | ES operator-independent? | Specific missing info (EN) | Specific missing info (ES) |
|---|---|:-:|:-:|---|---|
| 1 | Daily Report | 🟡 PARTIAL | 🟡 PARTIAL | Kickback-reason language on list-view (AR-0003); parent `mistake` absent | Layer B body_es absent |
| 2 | JHP + Ack | 🟡 PARTIAL | 🟡 PARTIAL | Parent `jha` lacks `mistake`; no LifecycleGuide | "Reconocer" semantic breadth + Layer B; ES-only-no-email crew excluded (FOCP R2 § C2-0014) |
| 3 | Safety Meeting | 🟡 PARTIAL | 🟡 PARTIAL | No lifecycle guide; parent missing `mistake` | Layer B absent; 23 topic ES files mitigate (operator can self-serve from topic library) |
| 4 | Incident Report | 🟡 PARTIAL | 🟡 PARTIAL | Severity criteria; 3-attestation flag definitions (AR-0016) | Severity ambiguity (SOCP §3.1) + Layer B |
| 5 | Site Inspection | 🟢 YES | 🟡 PARTIAL | — (full lifecycle, full tips, full audit) | Layer B + `FINDINGS_RAISED` vocab risk (AR-0007) |
| 6 | QA/QC Inspection | 🟡 PARTIAL | 🟡 PARTIAL | A/B/C closure path coaching (Phase 2 P4) | Same + Layer B |
| 7 | CAPA / Corrective | 🟡 PARTIAL | 🟡 PARTIAL | No in-flow lifecycle guide despite 5-stage pipeline | Layer B |
| 8 | Equipment Pre-op | 🟡 PARTIAL | 🟡 PARTIAL | Threshold for "ready" vs "shop visit" | Same + Layer B |
| 9 | Equipment Issuance | 🟢 YES | 🟡 PARTIAL | — | Layer B |
| 10 | Equipment Training | 🟢 YES | 🟡 PARTIAL | — | Layer B |
| 11 | **Fleet Repair / RTS** | 🔴 NO | 🔴 NO | RTS `who` (authority), `next` (downstream), `escalate` (when to refuse); LifecycleGuide; severity tier action criteria | All of EN + Layer B |
| 12 | Fire Extinguisher | 🟢 YES | 🟡 PARTIAL | — | Layer B |
| 13 | Safety Topic Library | 🟢 YES | 🟢 YES | — | 23 ES topic files cover the operational layer; tip-meta Layer B gap is library-meta only |
| 14 | Safety Document | 🟡 PARTIAL | 🟡 PARTIAL | Classification decision criteria | Same + Layer B |
| 15 | Safety Training record | 🟢 YES | 🟡 PARTIAL | — | Expiration-warning copy ES; training_es.js covers majority |
| 16 | Dispatch | 🟢 YES | 🟡 PARTIAL | — | Layer B; dispatch parent-tip gap (Phase 2 P5) — affects both languages |
| 17 | Document Expirations | 🟢 YES | 🟡 PARTIAL | — | Layer B |
| 18 | Driver Qualification | 🟢 YES | 🟡 PARTIAL | — | Layer B |
| 19 | Employee Accountability | 🟡 PARTIAL | 🟡 PARTIAL | Tone examples (acceptable vs not) | Same + Layer B |
| 20 | Employee Lifecycle | 🟢 YES | 🟢 YES | — (Phase 2 §1.7 PASS reference workflow) | Glossary "Archive" entry + Reactivate-vs-Rehire ES tip with full kinds — already complete |
| 21 | Payroll Variance | 🟡 PARTIAL | 🟡 PARTIAL | Attestation-flag definitions (AR-0004) | Same + Layer B |
| 22 | Field Leadership Portal | 🟢 YES | 🟡 PARTIAL | — | Layer B |
| 23 | Time-Off Review | 🟡 PARTIAL | 🟡 PARTIAL | Reopen rule (DOCTRINE-SILENT) | Same + Layer B |
| 24 | Time Verification | 🟢 YES | 🟡 PARTIAL | — | Layer B |
| 25 | Discipline cluster | 🟡 PARTIAL | 🟡 PARTIAL | Tone examples; recognition tax treatment | Same + Layer B |
| 26 | Equipment Checkout/Return | 🟢 YES | 🟡 PARTIAL | — | Layer B |
| 27 | Material Calculator | 🟢 YES | 🟡 PARTIAL | — | Layer B |
| 28 | Attendance | 🟡 PARTIAL | 🟡 PARTIAL | Only 2 tips; mistake absent | Same + Layer B |
| 29 | Asset Transfer | 🟡 PARTIAL | 🟡 PARTIAL | Reopen DOCTRINE-SILENT | Same |
| 30 | Operational Constraints | 🟢 YES | 🟢 YES | (reopen intentionally absent per TR-0007 DOCTRINE-EXEMPT — documented intent) | — |
| 31 | Vendor Management | 🟡 PARTIAL | 🟡 PARTIAL | Archive workflow missing (TR-0003) | Same |
| 32 | PM Hub | 🟢 YES | 🟢 YES | — | — |
| 33 | HR Hub | 🟢 YES | 🟢 YES | — | — |
| 34 | Public Time-Off (employee request) | 🟢 YES | 🟢 YES | — | — |
| 35 | Universal Undo / Recovery Stream | 🟢 YES | 🟢 YES (DOCTRINE-EXEMPT EN-canonical) | — | — |

---

## 2 · Aggregate verdict counts

| Dimension | 🟢 YES | 🟡 PARTIAL | 🔴 NO |
|---|---:|---:|---:|
| EN operator-independence | **20 (57%)** | 14 (40%) | **1 (3%)** |
| ES operator-independence | **8 (23%)** | 26 (74%) | **1 (3%)** |

**Headline**: 
- **EN**: 57% YES · 40% PARTIAL · 3% NO. The platform is **operationally independent in English for the majority of workflows**, with one provable NO (Fleet RTS) and a cluster of YELLOW gaps centered on parent-form `mistake` and attestation-flag definitions.
- **ES**: 23% YES · 74% PARTIAL · 3% NO. The platform is **operationally independent in Spanish only for the read-side/glossary-heavy workflows** (HR Hub, PM Hub, Public Time-Off, Constraints, Recovery Stream, Topic Library, Universal Undo, Employee Lifecycle). All workflow surfaces with substantive coaching content are PARTIAL in Spanish because Layer B (`body_es`) is essentially empty.

---

## 3 · The one provable NO (across both languages)

**Fleet Repair / Return-to-Service (RTS).**

Per OCSPCP 1, 3, and 4 + STCP §5 + SOCP §8.2:

| Why this is the only NO | Evidence |
|---|---|
| Only 2 tips on the highest-stakes decision form | `tips.py` `fleet.rts` |
| No `who` (authority), no `next` (downstream), no `escalate` (refusal trigger) | Same |
| No LifecycleGuide despite multi-stage repair pipeline | No fleet lifecycle file with WORKFLOW="fleet" |
| No unified workflow_state_events audit | Same |
| No body_es | 0 / 2 |
| Phase 2 P3 + SOCP §8.2 + STCP §5 corroborate | Multi-program convergent evidence |

A brand-new operator-mechanic — English-primary or Spanish-primary — **cannot today perform RTS without external assistance.** This is the single most actionable closure target on the platform.

---

## 4 · Per-role operator independence verdict

The directive names roles whose operator independence must be evaluated.

| Role | EN | ES | Source-direct evidence |
|---|:-:|:-:|---|
| Brand-new Laborer | 🟡 PARTIAL | 🟡 PARTIAL | JHP ack + Equipment Issuance ack work; Daily Report + Incident reporting (witness) operable. ES-only laborer faces Layer B gap on coaching + FOCP R2 § C2-0014 email-identity-key |
| Brand-new Foreman | 🟡 PARTIAL | 🟡 PARTIAL | Daily Report + JHP roster + Safety Meeting facilitation operable; Meeting has no LifecycleGuide |
| Brand-new Superintendent | 🟡 PARTIAL | 🟡 PARTIAL | Cross-workflow visibility OK; CAPA + Pre-op LifecycleGuides missing |
| Brand-new Safety Rep | 🟢 YES (4 owner workflows have lifecycle audit) | 🟡 PARTIAL (Layer B body absent) | Most-equipped role |
| Brand-new Safety Manager | 🟡 PARTIAL | 🟡 PARTIAL | 3-attestation closure works; attestation-flag definitions absent (AR-0016) |
| Brand-new Equipment Manager (RTS-relevant) | 🔴 NO | 🔴 NO | RTS cluster (Section 3) |
| Brand-new Dispatcher | 🟢 YES (25 tips · `dispatch_lifecycle.py` exists) | 🟡 PARTIAL | Layer B + Phase 2 P5 parent-tip gap |
| Brand-new PM | 🟢 YES | 🟡 PARTIAL | Constraints + QA/QC + PM Hub operable; Vendor archive missing (TR-0003) |

**Aggregate role verdict**: 🟢 3 · 🟡 4 · 🔴 1 (Equipment Manager via RTS) — for EN. 🟡 7 · 🔴 1 — for ES.

---

## 5 · Remediation register (per directive Phase 5)

For every PARTIAL / NO, the EXACT missing information has been identified above and is consolidated here as a single closure list. Per directive, this register identifies the missing information; it does NOT authorize engineering.

| # | Form_key / surface | Missing info | Closure type | Already-existing infrastructure used |
|---|---|---|---|---|
| 1 | `fleet.rts` | `who` + `next` + `escalate` + LifecycleGuide | EN content + UI wire | tips registry + LifecycleGuide |
| 2 | `fleet.rts` body_es | All ES tip bodies | ES content | body_es field already exists |
| 3 | `qaqc.signoff` | A/B/C decision criteria as `mistake` tip | EN content | tips registry |
| 4 | `incident.severity` | Recordable/First-Aid/Near-Miss criteria deepening | EN content | tips registry |
| 5 | `incident` parent | Attestation-flag definitions inline | UI tooltip | LifecycleGuide pattern |
| 6 | `payroll-variance` | Attestation-flag definitions inline | UI tooltip | Same |
| 7 | `jha` parent | `mistake` kind tip | EN content + ES | tips registry |
| 8 | `meeting` parent | `mistake` + LifecycleGuide (or doctrine declare no lifecycle) | EN content | Existing components |
| 9 | All non-glossary-wired pages | Glossary in-flow tooltip / link | UI wiring | AdminOperationalLanguage entries already exist |
| 10 | All workflows with EN tips but no body_es | Layer B body_es content | ES content authoring | body_es field |
| 11 | Vendor archive (TR-0003) | Archive workflow OR explicit doctrine | Operator decision | TR-0003 already exists |
| 12 | Asset Transfer reopen | Reopen rule OR doctrine | Operator decision | DOCTRINE-SILENT |
| 13 | Time-Off Review reopen | Reopen rule OR doctrine | Operator decision | DOCTRINE-SILENT |
| 14 | Daily Report kickback reason on tile (AR-0003) | Tile-level visibility | UI wire | Existing surfaces |
| 15 | Site Inspection vocab risk (AR-0007) | Per-state name clarification | UI copy | Existing surfaces |
| 16 | `preop.signoff` threshold | "Ready" vs "needs shop" criteria | EN content | tips registry |
| 17 | `attendance` | `mistake` tip + glossary entry | EN content | tips registry |
| 18 | `field-leadership.records.review-tone` | Acceptable-tone examples | EN content + ES | tips registry |
| 19 | `time-off-review.bereavement` | Policy summary inline | EN content + ES | tips registry |
| 20 | `recognition` | Tax-treatment guidance | EN content + ES | tips registry |
| 21 | `safety-training.expiration` | Outreach cadence + script | EN content + ES | tips registry |
| 22 | `dispatch.transfers.lead-time` | Threshold table | EN content | tips registry |

**22 discrete remediations identified. Zero new workflows. Zero new modules. Every item reuses an existing form_key, page, component, or registry slot.** Per Rule 6, every recommendation traces to existing infrastructure.

---

## 6 · Retired false findings

| Inherited claim | Verdict | Disposition |
|---|---|---|
| "Operator independence is 100%" | 57% EN YES · 23% ES YES verifiable today. | **REFINED to evidence-backed figure.** |
| "Operator independence is impossible without onboarding" | 20 of 35 EN workflows already YES; 8 ES YES — onboarding 🔴 is a Phase-6 OCSPCP issue, not the only path to independence. | **REFINED.** |
| "Spanish independence requires full translation" | The directive itself disclaims literal translation; what is needed is operational-intent ES authoring (Layer B content). | **CLARIFIED.** |

---

**End of OPERATOR INDEPENDENCE REPORT · OCSPCP 6 of 7**
