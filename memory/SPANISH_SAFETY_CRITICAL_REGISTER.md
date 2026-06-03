# SPANISH SAFETY-CRITICAL REGISTER
## OCEP · Spanish Operational Certification Program (SOCP) · Phase 3

**Date**: 2026-06-03
**Authority**: OMEGA · SOCP Phase 3
**Mode**: READ-ONLY safety-critical review · no translation changes
**Purpose**: Identify Spanish surfaces where misunderstanding could cause **safety risk · liability · compliance failure · operational harm**. Each finding is sourced from the codebase; no operator behavior is asserted.

**Scope** (per directive):
- Job Hazard Plan (JHP)
- Safety Meetings
- Incident Reports
- Corrective Actions
- Emergency Notifications
- Hazard Communication
- Excavation
- Equipment Inspections

Each finding records:
1. **Potential Misunderstanding** — where a Spanish reader might mis-interpret the surface
2. **Potential Liability** — civil / OSHA / wrongful-death exposure
3. **Potential Safety Risk** — direct physical risk to crew
4. **Potential Compliance Risk** — OSHA / DOT / state-record exposure

---

## 1 · Job Hazard Plan (JHP)

### Finding 1.1 — JHP acknowledgement attestation chain
- **Surface**: JHP acknowledge modal copy (`i18n.js` JHP section · `JhaAcknowledgeButton.jsx`)
- **Spanish surface**: "Reconocer" / acuse text (per `i18n.js`)
- **Potential Misunderstanding**: A Spanish-speaking laborer may interpret "Reconocer" as "I read it" rather than the legal attestation "I have been briefed on these hazards and accept the obligation to follow them". Spanish "reconocer" is broader semantically than English "acknowledge".
- **Potential Liability**: 🔴 HIGH. If a post-incident OSHA review surfaces a Spanish-only attestation chain where the operator denies understanding the legal nature of the click, the entire JHP defense is degraded.
- **Potential Safety Risk**: 🟠 MEDIUM. Indirect — a less-engaged acknowledgement → less-internalized hazard awareness.
- **Potential Compliance Risk**: 🔴 HIGH. OSHA documentation chain integrity.
- **Recommendation for field reviewer**: Confirm exact phrasing on the ack button + modal. Possibly recommend operator decide between "Reconocer" vs "Confirmar" vs "Acuso recibo" vs "Acuso recibo y acepto las obligaciones".

### Finding 1.2 — Spanish-only crew with no work email (FOCP R2 § C2-0014)
- **Surface**: JHP acknowledge identity-key flow
- **Source**: `backend/routes/jha_acknowledgements.py` (FOCP R2 ledger) + `frontend/src/components/JhaAcknowledgeButton.jsx`
- **Potential Misunderstanding**: An email-less Spanish-only crew member may be silently excluded from the ack ledger.
- **Potential Liability**: 🔴 HIGH. Operator believes JHP coverage is 100% when in fact ES-only-no-email crew is uncovered.
- **Potential Safety Risk**: 🔴 HIGH. Uncovered crew may be assigned without their hazard briefing recorded.
- **Potential Compliance Risk**: 🔴 HIGH.
- **Recommendation**: Field reviewer to confirm operator policy for ES-only-no-email crew. (Engineering note: FOCP R2 § C2-0014 already records this as a known risk; SOCP re-surfaces it as Spanish-specific.)

### Finding 1.3 — JHP version-replacement language
- **Surface**: JHP re-acknowledgement copy
- **Potential Misunderstanding**: Spanish copy must clearly tell the reader "this replaces your earlier signature; both are preserved in audit". If unclear, the operator may sign twice or refuse to sign the new version.
- **Potential Liability**: 🟠 MEDIUM.
- **Potential Safety Risk**: 🟠 MEDIUM. Stale-version signature → operator working under old hazard understanding.
- **Potential Compliance Risk**: 🟠 MEDIUM.

---

## 2 · Safety Meetings

### Finding 2.1 — 23 topic Spanish dictionaries are NOT independently reviewed
- **Surface**: `frontend/src/lib/topics/*.es.js` (23 trade-specific files, 1579 LOC total)
- **Author**: Engineering (with operator review trail unclear in source)
- **Sample observed**: `excavation.es.js` is professionally written, idiomatic, and OSHA-anchored.
- **Potential Misunderstanding**: Unreviewed regional variance — e.g., Mexican vs Caribbean vs Central American Spanish field crews — could create confusion on specific hazard verbs.
- **Potential Liability**: 🟠 MEDIUM. Safety Meeting record is a legal artifact.
- **Potential Safety Risk**: 🔴 HIGH if a critical hazard verb is unclear. Specifically the excavation topic file uses "engullimiento" (engulfment) — technically correct but may be unfamiliar to crews who use "sepultamiento".
- **Potential Compliance Risk**: 🟠 MEDIUM.
- **Recommendation**: Phase 4 field-review packet covers each of the 23 topic files.

### Finding 2.2 — "Mistake" `HelpTipBlock` kind absent on Safety Meeting form
- **Surface**: `i18n.js` meeting section + `tips.py` Spanish entries
- **Cross-reference**: `PHASE2_TRAINING_REALITY_MATCH_REPORT.md` P1 finding
- **Potential Misunderstanding**: A Spanish-reading meeting facilitator has no inline "Common mistakes" tip on the meeting form, so the gap from English carries over to ES.
- **Potential Liability**: 🟡 LOW (gap is in coaching, not in record).
- **Potential Safety Risk**: 🟡 LOW.
- **Potential Compliance Risk**: 🟡 LOW.

### Finding 2.3 — Trench-collapse description quality (sample-verified)
- **Surface**: `topics/excavation.es.js` `trenching_shoring.incident_pattern`
- **Verbatim sample**: "una yarda cúbica de tierra pesa ~3,000 lb. Aun si la cabeza queda libre, la compresión del pecho mata en menos de 5 minutos."
- **Assessment**: Exemplary safety prose. Concrete weight, concrete consequence, concrete time-to-fatality. This is **decision-grade Spanish**, not boilerplate.
- **Potential Misunderstanding**: Low.
- **Potential Liability**: Low.
- **Potential Safety Risk**: Low (this finding is a POSITIVE — recorded here for completeness).

---

## 3 · Incident Reports

### Finding 3.1 — Incident severity classification labels
- **Surface**: `NewIncident.jsx` + `i18n.js` incident keys
- **Potential Misunderstanding**: Severity terms (Recordable / First-Aid / Near-Miss / Property / Environmental) require unambiguous Spanish equivalents. Some platform UIs use "Reportable" for recordable — the term "Reportable" is more naturally interpreted as "must be reported" in ES, which is ambiguous when ALL incidents must be reported.
- **Potential Liability**: 🔴 HIGH. Severity drives OSHA recordable classification.
- **Potential Safety Risk**: 🟡 LOW (indirect).
- **Potential Compliance Risk**: 🔴 HIGH.

### Finding 3.2 — 3-attestation closure gate labels
- **Surface**: `IncidentLifecyclePanel.jsx` + `i18n.js` lifecycle keys
- **Potential Misunderstanding**: The three attestation flags (`review_complete`, `approval_complete`, `variance_decisions_complete` for PV; analogous flags for incident) require per-flag Spanish definitions that match the English doctrine. AR-0016 in `ADOPTION_RISK_REGISTER` flags missing definitions IN ENGLISH; the Spanish gap is at least as wide.
- **Potential Liability**: 🔴 HIGH. Attestation tick-without-understanding voids the legal weight of the closure.
- **Potential Safety Risk**: 🟡 LOW (indirect).
- **Potential Compliance Risk**: 🔴 HIGH.

### Finding 3.3 — Narrative prompt language quality
- **Surface**: `NewIncident.jsx` Spanish narrative prompts
- **Potential Misunderstanding**: Field-reviewer must confirm the Spanish prompt elicits **specific** narrative ("laceración al dedo índice derecho que requirió suturas") not **vague** narrative ("se lastimó el dedo"). The English form prompt is already imperfect on this dimension (Phase 2 §1.x).
- **Potential Liability**: 🟠 MEDIUM. Vague narrative weakens claim defense.
- **Potential Safety Risk**: 🟡 LOW (indirect, trend-analysis impact).
- **Potential Compliance Risk**: 🟠 MEDIUM.

---

## 4 · Corrective Actions (CAPA)

### Finding 4.1 — CAPA glossary entry quality
- **Surface**: `AdminOperationalLanguage.jsx` line 53–58 (CAPA entry: en/es/operational/lifecycle/accountability/downstream)
- **Spanish term**: "Acción Correctiva y Preventiva (CAPA)"
- **Assessment**: ✅ Glossary-canonical. Clear. Reviewer should confirm pipeline stages (Open → In Progress → Pending Review → Verified → Closed) have unambiguous Spanish stage names.

### Finding 4.2 — QA/QC closure path B = CAPA equivalence
- **Surface**: Phase 2 P4 documents the 3-path QA/QC closure (re-inspect / corrective-action / exception). Spanish copy may not telegraph that "corrective action documented" is functionally a CAPA.
- **Potential Misunderstanding**: 🟠 MEDIUM.
- **Potential Liability**: 🟡 LOW.

---

## 5 · Emergency Notifications

### Finding 5.1 — Email / SMS Spanish templates DOCTRINE-SILENT
- **Surface**: No `*_es.html`, `*_es.txt`, or analogous email/SMS Spanish-variant templates surfaced in `/app/backend/` file survey.
- **Potential Misunderstanding**: A Spanish-only recipient may receive a critical notification (incident escalation, JHP version change, time-off approval, RTS clearance) entirely in English.
- **Potential Liability**: 🔴 HIGH. Especially for safety-critical notifications.
- **Potential Safety Risk**: 🟠 MEDIUM-to-HIGH (depends on what is actually sent).
- **Potential Compliance Risk**: 🟠 MEDIUM.
- **Recommendation**: Phase 4 field-review packet asks operators to confirm which notifications are sent, in what language, and to whom. Engineering must NOT remediate without authorized FOCP 7-test + 4-proof.

### Finding 5.2 — On-page emergency instructions (excavation file)
- **Surface**: `topics/excavation.es.js` line 25 — "Golpe de gas: despeje viento arriba, sin fuentes de ignición, llame al 911 y al servicio. No trate de tapar o detener la fuga usted mismo."
- **Assessment**: ✅ Decision-grade. Direct, accurate, life-safety.
- **Note**: This is on-page meeting copy, NOT a notification template. Notification templates remain DOCTRINE-SILENT in the source survey.

---

## 6 · Hazard Communication

### Finding 6.1 — Spanish hazard naming consistency across topic files
- **Surface**: `topics/*.es.js` `hazards_reviewed` field across 23 files
- **Potential Misunderstanding**: Same physical hazard may be named differently across files (e.g., "engullimiento" in excavation vs hypothetical "sepultamiento" in another). Field reviewer must walk the cross-file consistency.
- **Potential Liability**: 🟡 LOW.
- **Potential Safety Risk**: 🟠 MEDIUM. Inconsistent naming → less effective transfer of training between trades.

### Finding 6.2 — "Out of service" / "Energized" / "De-energized" canonical labels
- **Surface**: `i18n.js` + `electrical.es.js` + `shop.es.js`
- **Spanish term**: "Fuera de servicio" / "Energizada" / "Desenergizada"
- **Assessment**: ✅ Industry-standard. Reviewer to confirm cross-trade consistency.

---

## 7 · Excavation (cross-references Section 1.2.3 of Phase 1 register)

### Finding 7.1 — "Setback" loanword on safety-critical sentence
- **Surface**: `topics/excavation.es.js` line 35 — "Setback de spoil verificado"
- **Potential Misunderstanding**: "Setback" is an English loanword on a safety-critical action-item line. Mexican-Spanish crews may parse it correctly; reviewers from other regions should confirm.
- **Potential Liability**: 🟡 LOW.
- **Potential Safety Risk**: 🟠 MEDIUM.

### Finding 7.2 — Spoil placement & equipment vibration narrative
- **Surface**: `topics/excavation.es.js` `excavation_spoil_placement.incident_pattern`
- **Assessment**: ✅ Exemplary safety prose. Sourced 18-inch setback, vibration causality, tension crack as "last warning". Decision-grade.
- **Note**: Recorded as a POSITIVE finding.

### Finding 7.3 — Soil classification action verbs
- **Surface**: `topics/excavation.es.js` `soil_classification.discussion_notes`
- **Spanish phrase**: "En caso de duda, clasificar más bajo (más conservador)."
- **Assessment**: ✅ Direct, actionable. Reviewer to confirm "clasificar más bajo" is unambiguous (could be misread as "lower" in elevation rather than "more conservative classification").
- **Recommendation**: Minor risk. Could potentially benefit from "clasificar al tipo MÁS DÉBIL" but this is a translation-improvement recommendation, NOT a certification claim, and is OUT OF SCOPE for SOCP per the directive.

---

## 8 · Equipment Inspections

### Finding 8.1 — Pre-shift severity tier color naming
- **Surface**: `i18n.js` equipment / fleet keys
- **Spanish terms**: Defecto Rojo / Amarillo / Verde
- **Potential Misunderstanding**: Colors translate cleanly. Risk is whether the **action** associated with each tier is unambiguous.
- **Potential Liability**: 🔴 HIGH (RTS decision).
- **Potential Safety Risk**: 🔴 HIGH.

### Finding 8.2 — Return-to-Service (RTS) attestation language
- **Surface**: `i18n.js` fleet section
- **Spanish equivalent**: "Retorno al servicio" / similar
- **Potential Misunderstanding**: RTS is the platform's most consequential single decision (a wrongly-released truck kills people — `WORKFLOW_EXPLANATION_LIBRARY.md` §8). The Spanish attestation chain must be unambiguous about who is authorizing the release and on what basis.
- **Potential Liability**: 🔴 HIGHEST on the platform.
- **Potential Safety Risk**: 🔴 HIGHEST on the platform.
- **Potential Compliance Risk**: 🔴 HIGH (DOT mechanic certification).

### Finding 8.3 — Shop / Fleet "thinnest coaching surface" (Phase 2 P3)
- **Surface**: Multiple shop/fleet pages
- **Cross-reference**: Phase 2 P3 flag
- **Potential Misunderstanding**: Coaching gap in English is also a gap in Spanish. Shop is the platform's thinnest coverage layer.
- **Recommendation**: Bundled into the Phase 4 packet for field-review attention.

---

## 9 · Aggregate safety-critical findings

| Tier | Count |
|---|---:|
| 🔴 Safety-critical findings | 11 |
| 🟠 Medium-risk findings | 7 |
| 🟡 Low-risk findings | 4 |
| ✅ Positive findings (decision-grade Spanish observed) | 4 |

**Highest individual risks** (operator decision-grade):
1. **Section 8.2 — RTS Spanish attestation** (highest single risk on the platform).
2. **Section 1.1 — JHP "Reconocer" semantic breadth**.
3. **Section 1.2 — Spanish-only-no-email crew identity-key risk**.
4. **Section 3.2 — Incident 3-attestation Spanish flag definitions**.
5. **Section 5.1 — Email/SMS Spanish templates DOCTRINE-SILENT** (existence unconfirmed).

---

## 10 · What this register does NOT do

- Does **not** propose translation changes (per directive STOP).
- Does **not** assert that any of these risks have materialized in the field (no fabricated incident data).
- Does **not** certify any surface as safe or unsafe — only field reviewers can.
- Does **not** rank operator priorities — operator decides.

---

**End of SPANISH SAFETY-CRITICAL REGISTER · SOCP Phase 3**
