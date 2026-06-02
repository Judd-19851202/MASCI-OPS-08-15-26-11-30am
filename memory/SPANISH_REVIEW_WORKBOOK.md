# SPANISH REVIEW WORKBOOK
## OCEP Operational Completion Sprint · Phase 3

**Date**: 2026-06-02
**Authority**: OMEGA · OPERATIONAL COMPLETION SPRINT
**Mode**: READ-ONLY · audit package (no translation rewrites performed)
**Scope**: Field-facing Spanish surfaces · operational correctness verification
**Audience**: Florida-construction-fluent native Spanish-speaker reviewer

---

## 0 · Review Protocol

This workbook is the **only authorized vehicle** for Spanish operational parity verification under the OMEGA Operational Completion Sprint. It is filled by the reviewer; the AI agent stops at the framework and does not propose translation corrections.

### 0.1 · Reviewer prerequisites
- Native or near-native Spanish speaker
- ≥ 2 years on heavy-civil / underground utility / paving job sites
- Familiar with Florida-construction Spanish (predominantly Mexican / Central-American operational terminology)
- Willing to mark surfaces "operationally wrong" without softening

### 0.2 · Session setup
- Device: phone (field reality) for Laborer / Foreman surfaces; desktop for HR / Dispatch
- Language: app set to Spanish (`lang=es` or LangToggle)
- Two monitors / windows: app + this workbook
- Note pad: optional · audio recording: optional

### 0.3 · Session duration
- 90 minutes per domain (capped) · 8 domains = 12 hours total review time
- Domain order = severity tier descending (start with JHP)

---

## 1 · Reviewer Instructions

For each visible Spanish string on each in-scope surface:

1. Read the Spanish version aloud, as the field crew would
2. Determine whether the operational meaning matches the English canonical
3. Assign a **verdict** (see §2)
4. Assign a **severity** (see §2.2)
5. Record in the §5 findings register

Special rules:
- **Mixed-language surfaces** (English label + Spanish body, or vice versa) are flagged automatically as MIXED_LANGUAGE
- **Missing translations** (English shown when `lang=es`) are flagged automatically as MISSING
- **Construction terminology** drift gets WRONG_TERM (severity HIGH minimum)
- **Safety terminology** drift gets DANGEROUS (severity CRITICAL minimum)

Reviewer does NOT propose rewrites in this workbook. Rewrites are a build action gated by the FOCP 7-test + 4-proof.

---

## 2 · Severity Matrix

### 2.1 · Verdict scale (per-string)
| Verdict | Definition |
|---|---|
| `CORRECT` | Operational meaning preserved · native-speaker readable |
| `LITERAL_BUT_AWKWARD` | Conveys idea; native phrasing would differ. Acceptable; flagged. |
| `WRONG_TERM` | Spanish word does not map to the construction concept |
| `DANGEROUS` | Phrasing alters meaning in a way that risks unsafe action |
| `MISSING` | Surface is English-only when bilingual required |
| `MIXED_LANGUAGE` | Same surface mixes EN + ES confusingly |

### 2.2 · Severity scale (per-finding)
| Severity | Trigger | Action timeline (if remediation later authorized) |
|---|---|---|
| **CRITICAL** | DANGEROUS verdict on a safety surface (JHP · Incident · Safety · QA/QC · Site Inspection) | Halt Final Certification · remediate before Phase 6 sign-off |
| **HIGH** | WRONG_TERM on a safety surface OR MISSING on JHP | Remediate within 7 days of operator authorization |
| **MEDIUM** | WRONG_TERM on a non-safety surface (Daily Reports · Dispatch · HR · Equipment) | Remediate within 30 days of operator authorization |
| **LOW** | LITERAL_BUT_AWKWARD anywhere | Backlog · no certification block |

### 2.3 · Per-domain severity floors (auto-elevation)
- Domain = JHP → any verdict ≥ WRONG_TERM auto-promotes to CRITICAL
- Domain = Incident → any WRONG_TERM auto-promotes to HIGH
- Domain = Safety Meetings → any DANGEROUS auto-promotes to CRITICAL
- All other domains follow the §2.2 default mapping

---

## 3 · In-scope domains (8 · severity-priority order)

| Order | Domain | Primary route(s) | Severity tier | Why |
|---|---|---|---|---|
| 1 | **JHP (Job Hazard Plan)** | `/jha` + Acknowledge modal (post-FOCP R2) | SAFETY | A misunderstood attestation = legal exposure |
| 2 | **Incident Reports** | `/incidents/new` | SAFETY | Misclassification = OSHA exposure |
| 3 | **Safety Meetings / coaching** | `/safety` + `HelpTip` Spanish | SAFETY | Daily briefings; phrasing carries operational meaning |
| 4 | **QA/QC Inspections** | `/qaqc-inspections/new` | SAFETY | Wrong defect terminology = wrong remediation |
| 5 | **Site Inspections** | `/inspections/new` | SAFETY | Same as QA/QC |
| 6 | **Daily Reports** | `/daily-reports/new` (field fill) | OPERATIONAL | Wrong hours / materials = payroll variance |
| 7 | **Dispatch driver-facing** | Driver shift-start, dispatch handoff | OPERATIONAL | Wrong assignment = wrong job |
| 8 | **HR self-service** | Time-off, employee requests | OPERATIONAL | Approval delays from misunderstood request types |

Out of scope (English-canonical admin chrome): AdminHub, AdminCommandCenter, AdminRecoveryStream, AdminJhaAcknowledgements, all PM admin chrome.

---

## 4 · Per-domain worksheet (8 copies · reviewer fills each)

### Domain template (replicate per domain)

```
========================================================
Domain        : ___________________________________
Reviewer      : ___________ (initials)
Date          : ___________
Device        : ☐ phone   ☐ desktop
Lang setting  : ☐ es
Start time    : ___________   End time: ___________
========================================================
```

| # | Surface (page / component) | English string | Current Spanish | Verdict | Severity | Construction-term concern? | Safety-term concern? | Notes |
|---|---|---|---|---|---|:-:|:-:|---|
| 1 |  |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |  |
| 4 |  |  |  |  |  |  |  |  |
| 5 |  |  |  |  |  |  |  |  |
| (add rows as needed) |  |  |  |  |  |  |  |  |

**Domain summary**:
- Total strings audited: ___
- CORRECT: ___ · LITERAL: ___ · WRONG: ___ · DANGEROUS: ___ · MISSING: ___ · MIXED: ___
- Domain Score = (CORRECT + 0.5 × LITERAL) / total × 100 = ___
- CRITICAL findings: ___
- HIGH findings: ___
- Reviewer's open question (if any): ___

---

## 5 · Findings Register (consolidated)

The reviewer copies every finding (any verdict other than CORRECT) from the 8 worksheets into the single register below. This becomes the master remediation list (NOT a build authorization).

| # | Domain | Surface | English string | Current Spanish | Verdict | Severity | Construction risk? | Safety risk? | Status |
|---|---|---|---|---|---|---|:-:|:-:|---|
|  |  |  |  |  |  |  |  |  |  |

Status values: OPEN · ACKNOWLEDGED · REMEDIATION-AUTHORIZED · CORRECTED · WONT-FIX-WITH-REASON.

---

## 6 · Aggregate scoring

After all 8 domains complete:

| Domain | Weight | Score | Weighted contribution |
|---|---:|---:|---:|
| 1 JHP | 3.0 (safety-tier) |  |  |
| 2 Incident | 3.0 |  |  |
| 3 Safety Meetings | 3.0 |  |  |
| 4 QA/QC | 2.0 |  |  |
| 5 Site Inspection | 2.0 |  |  |
| 6 Daily Reports | 1.0 |  |  |
| 7 Dispatch | 1.0 |  |  |
| 8 HR | 1.0 |  |  |
| **Weighted Mean (Overall Spanish Parity Score)** | / 16.0 |  |  |

### Thresholds
- ≥ 85 AND zero CRITICAL = **PASS** for Phase 6 / Final Certification gate
- 70–84 OR any CRITICAL open = **CONDITIONAL** · remediation cycle required
- < 70 = **FAIL** · platform Spanish surface unfit for Spanish-only crew adoption

---

## 7 · Construction-term & Safety-term reference (reviewer guidance)

For the reviewer's convenience while auditing — this is NOT a rewrite specification, only a reference for spotting drift.

### 7.1 · Construction terms
| English | Acceptable Spanish | Reject |
|---|---|---|
| Crew | Cuadrilla | Equipo (generic) |
| Job site | Obra · Sitio de trabajo | Trabajo (ambiguous) |
| Foreman | Capataz · Mayordomo | Líder (vague) |
| Pour / Concrete pour | Vaciado · Colado de concreto | Vertido (Spain-Spanish) |
| Lift / pick | Maniobra de izaje | Subida (ambiguous) |
| Backfill | Relleno | Material (vague) |
| Trench | Zanja · Excavación | — |
| Shoring | Apuntalamiento | — |
| Trench shield | Escudo de zanja · Caja de zanja | — |
| Manhole | Pozo de inspección · Registro | Boca de visita (region) |
| Lift station | Estación de bombeo | Bomba (incomplete) |
| Mobilization | Movilización | Inicio (vague) |
| Tie-in | Empalme · Conexión | — |
| Stormwater | Aguas pluviales | Drenaje (incomplete) |

### 7.2 · Safety terms (CRITICAL surface)
| English | Required Spanish | Why |
|---|---|---|
| Stop Work Authority | Autoridad para Suspender el Trabajo | Legal phrase · must be exact |
| OSHA recordable | Registrable por OSHA | Regulatory |
| Near-miss | Casi accidente · Cuasi accidente | Reporting category |
| LOTO (Lockout / Tagout) | Bloqueo y Etiquetado | Industry standard |
| Confined space | Espacio confinado | Industry standard |
| Hot work | Trabajo en caliente | Industry standard |
| Trench safety | Seguridad en zanjas | OSHA 1926 Subpart P |
| Job Hazard Plan / JHP | Plan de Peligros del Trabajo | Platform convention |
| Acknowledge | Confirmar Recibido | Post-FOCP R2 platform convention |

### 7.3 · Workflow verbs
| English | Required Spanish |
|---|---|
| Submit | Enviar |
| Save | Guardar |
| Sign | Firmar |
| Acknowledge | Confirmar Recibido |
| Approve | Aprobar |
| Reject | Rechazar |
| Reopen | Reabrir |
| Close | Cerrar |
| Finalize | Finalizar |

---

## 8 · Reviewer sign-off

```
This Spanish Review Workbook is the verification record for the
field-facing Spanish surfaces of the MASCI Safety Hub platform.

Reviewer name : _______________________________________________
Credentials   : ______________________________________________
Date opened   : _______________________________________________
Date closed   : _______________________________________________

Total strings audited     : _____
CORRECT verdicts          : _____
LITERAL_BUT_AWKWARD       : _____
WRONG_TERM                : _____
DANGEROUS                 : _____
MISSING                   : _____
MIXED_LANGUAGE            : _____

Overall Spanish Parity Score (weighted): _____ / 100
CRITICAL findings open    : _____   (must be 0 for certification)
HIGH findings open        : _____

Final reviewer verdict:
  ☐ PASS         (≥ 85 AND zero CRITICAL)
  ☐ CONDITIONAL  (70-84 OR any CRITICAL open)
  ☐ FAIL         (< 70)

Reviewer signature : ___________________________
Operator signature : ___________________________ (Jaymn or designee)
Date verified      : ___________________________
```

---

## 9 · Refusal conditions

The AI agent MUST refuse to:
- Auto-translate strings (auto-translation is exactly how dangerous mistranslations enter the platform)
- Pre-fill the findings register based on inference
- Mark this workbook PASS / CONDITIONAL / FAIL without the reviewer's signature in §8
- Treat this workbook as a build authorization (it is an audit · the audit reveals findings; remediation requires separate FOCP-gated authorization)

---

**End of SPANISH REVIEW WORKBOOK · OCEP Phase 3 audit package**
