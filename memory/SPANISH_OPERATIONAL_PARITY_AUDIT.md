# SPANISH OPERATIONAL PARITY AUDIT
## OCEP Phase 3 · Operational Completion Evidence Program

**Date opened**: 2026-06-02
**Authority**: OMEGA · OCEP
**Mode**: READ-ONLY · evidence checklist
**Status**: Awaits native Spanish speaker reviewer
**Scope**: Field-facing bilingual surfaces · operational correctness, not literal translation

---

## 0 · Doctrine

The platform's i18n file (`/app/frontend/src/lib/i18n.js`) states verbatim:

> "English is the canonical language — all submitted data is stored in English. Spanish is a read/fill aid for Spanish-speaking crew members on forms."

Spanish is therefore an **operational safety surface**, not a marketing surface. A bad Spanish translation can:
- Mis-route an incident
- Mis-state a hazard
- Mis-classify equipment
- Cause a Spanish-only crew member to misunderstand attestation language and ack a JHP they didn't actually understand

This audit is therefore **operationally critical**, not nice-to-have.

The AI agent **cannot** complete this audit. A native Spanish speaker fluent in **heavy-civil construction terminology** must conduct it. The AI agent provides the worksheet, scoring, and remediation register.

---

## 1 · Reviewer prerequisites

The reviewer must:
- Be a native or near-native Spanish speaker
- Have ≥ 2 years experience on a heavy-civil / underground utility / paving job site
- Recognize the difference between Spain-Spanish, Mexico-Spanish, Central-America-Spanish, and South-America-Spanish operational terminology (Florida crews use predominantly Mexican / Central American Spanish)
- Be willing to mark surfaces as "operationally wrong" without softening the finding

If the reviewer is not Florida-construction-fluent the audit is INADMISSIBLE.

---

## 2 · In-scope domains (9 · operational priority order)

| # | Domain | Primary route(s) | Why this matters |
|---|---|---|---|
| 1 | JHP acknowledgement (Job Hazard Plan) | `/jha` + JhaAcknowledgeButton modal | A misunderstood attestation = legal exposure |
| 2 | Incident reporting | `/incidents/new` | A misclassified incident = OSHA exposure |
| 3 | Safety topic library / coaching | `/safety` + `HelpTip` Spanish | Daily safety briefings |
| 4 | Daily Reports | `/daily-reports/new` (field-fill surfaces) | Wrong hours / materials = payroll variance |
| 5 | QA/QC deficiency reporting | `/qaqc-inspections/new` | Wrong defect terminology = wrong remediation |
| 6 | Site Inspection findings | `/inspections/new` | Same as QA/QC |
| 7 | Equipment / Fleet | Equipment pages + driver shift-start | Wrong terminology = wrong unit reported |
| 8 | HR self-service (time-off, requests) | HR public-facing pages | Approval delays if request type misunderstood |
| 9 | Dispatch driver-facing | Driver pages | Wrong assignment = wrong job |

Out of scope (English-canonical admin chrome): AdminHub, AdminCommandCenter, AdminRecoveryStream, AdminJhaAcknowledgements, HR admin queues, Safety admin chrome, PM admin chrome.

---

## 3 · Terminology master list (required parity)

For each domain, the reviewer verifies these construction-Spanish terms map to the right operational concept. Wrong choices kill confidence and risk safety.

### 3.1 · Construction terminology
| English | Required Spanish | NEVER use |
|---|---|---|
| Crew | Cuadrilla | Equipo (generic) |
| Job site | Obra · Sitio de trabajo | Trabajo (ambiguous) |
| Foreman | Capataz · Mayordomo | Líder (vague) |
| Superintendent | Superintendente | Supervisor (overloaded) |
| Pour | Vaciado · Colado | Vertido (Spain-Spanish) |
| Lift / pick | Levantamiento · Maniobra | Subida (ambiguous) |
| Tagline | Cabo guía · Soga guía | Línea (generic) |
| Backfill | Relleno | Material (vague) |
| Trench | Zanja · Excavación | — |
| Shoring / shielding | Apuntalamiento · Escudo de zanja | — |

### 3.2 · Heavy-civil terminology
| English | Required Spanish | NEVER use |
|---|---|---|
| Stormwater | Aguas pluviales | Drenaje (incomplete) |
| Sanitary | Sanitario · Aguas servidas | — |
| Force main | Tubería de impulsión | — |
| Manhole | Pozo de inspección · Registro | Boca de visita (region-specific) |
| Lift station | Estación de bombeo | Bomba (incomplete) |
| Right-of-way | Servidumbre · Derecho de vía | — |
| Mobilization | Movilización | Inicio (vague) |
| Tie-in | Empalme · Conexión | — |

### 3.3 · Safety terminology
| English | Required Spanish | Reason |
|---|---|---|
| Stop Work Authority | Autoridad para Suspender el Trabajo | Legal phrase; must be exact |
| OSHA recordable | Registrable por OSHA | Regulatory; literal acceptable |
| Near-miss | Casi accidente · Cuasi accidente | Reporting category |
| LOTO (Lockout/Tagout) | Bloqueo y Etiquetado | Industry standard |
| Confined space | Espacio confinado | Industry standard |
| Hot work | Trabajo en caliente | Industry standard |
| Trench safety | Seguridad en zanjas | OSHA 1926 Subpart P |
| Job Hazard Plan / JHP | Plan de Peligros del Trabajo | Per platform convention |
| Acknowledgement (of a plan) | Confirmación · Reconocimiento | Per platform convention (FOCP R2) |

### 3.4 · Equipment terminology
| English | Required Spanish | NEVER use |
|---|---|---|
| Excavator | Excavadora | Pala (informal) |
| Backhoe | Retroexcavadora | — |
| Skid steer | Minicargador | Bobcat (brand) |
| Dump truck | Volqueta · Camión de volteo | Volquete (region-specific) |
| Roller / compactor | Rodillo compactador | — |
| Forklift | Montacargas | — |
| Pre-shift inspection | Inspección pre-turno · Inspección antes del turno | — |

### 3.5 · Workflow terminology (platform-specific verbs)
| English | Required Spanish | Source |
|---|---|---|
| Submit | Enviar | i18n.js |
| Save | Guardar | i18n.js |
| Sign | Firmar | FOCP R2 |
| Acknowledge | Confirmar Recibido | FOCP R2 |
| Approve | Aprobar | iter71 |
| Reject | Rechazar | iter71 |
| Reopen | Reabrir | iter453 |
| Close | Cerrar | iter451 |
| Finalize | Finalizar | iter452 |
| Undo last status change | (admin-only · stays English) | FOCP R2 doctrine |

---

## 4 · Per-domain audit worksheet

For each of the 9 domains in §2, the reviewer fills:

```
Domain: ___________
Reviewer: ___________ (initials)
Date: ___________
Device: ☐ phone (field reality) · ☐ desktop
Lang setting: ☐ es

For each visible string on the surface:
  English  : <copy verbatim>
  Spanish  : <copy verbatim>
  Verdict  : ☐ CORRECT  ☐ LITERAL_BUT_AWKWARD  ☐ WRONG_TERM  ☐ DANGEROUS  ☐ MISSING  ☐ MIXED_LANGUAGE
  Severity : ☐ CRITICAL  ☐ HIGH  ☐ MEDIUM  ☐ LOW
  Suggested correction (operational-Spanish): ___________
  Notes    : ___________
```

### 4.1 · Verdict definitions

| Verdict | Definition |
|---|---|
| `CORRECT` | Operational reality preserved; native-speaker readable |
| `LITERAL_BUT_AWKWARD` | Conveys the right idea but a native speaker would phrase it differently. Acceptable but flagged. |
| `WRONG_TERM` | The Spanish word doesn't map to the construction concept (e.g., "Equipo" for Crew when Cuadrilla is required) |
| `DANGEROUS` | The Spanish phrasing changes the meaning in a way that could cause unsafe action (e.g., "Detener Trabajo" reads as a casual "pause" instead of "Stop Work Authority") |
| `MISSING` | Surface is English-only when it must be bilingual |
| `MIXED_LANGUAGE` | Same surface uses both English and Spanish in confusing ways (e.g., "Acknowledge el Plan") |

### 4.2 · Severity scale

| Severity | Trigger | Action timeline |
|---|---|---|
| CRITICAL | DANGEROUS verdict on any safety-tier surface (Domains 1, 2, 3, 5, 6) | Halt Phase 7 certification; remediate before re-test |
| HIGH | WRONG_TERM on any safety-tier surface, OR MISSING on Domain 1 (JHP) | Remediate within 7 days |
| MEDIUM | WRONG_TERM on non-safety-tier surfaces (Domains 4, 7, 8, 9) | Remediate within 30 days |
| LOW | LITERAL_BUT_AWKWARD anywhere | Backlog; no certification block |

---

## 5 · Domain-by-domain scoring template

For each of the 9 domains, after completing 4.x worksheets:

| Domain | Strings audited | CORRECT | LITERAL | WRONG | DANGEROUS | MISSING | MIXED | Score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 JHP acknowledgement |  |  |  |  |  |  |  |  |
| 2 Incident reporting |  |  |  |  |  |  |  |  |
| 3 Safety topic library / coaching |  |  |  |  |  |  |  |  |
| 4 Daily Reports |  |  |  |  |  |  |  |  |
| 5 QA/QC deficiency reporting |  |  |  |  |  |  |  |  |
| 6 Site Inspection findings |  |  |  |  |  |  |  |  |
| 7 Equipment / Fleet |  |  |  |  |  |  |  |  |
| 8 HR self-service |  |  |  |  |  |  |  |  |
| 9 Dispatch driver-facing |  |  |  |  |  |  |  |  |

**Score** = (CORRECT + 0.5 × LITERAL) / (total strings audited) × 100.

**Overall Spanish Parity Score** = weighted mean over domains, weights:
- Domains 1, 2, 3: weight 3 (safety-tier)
- Domains 5, 6: weight 2
- Domains 4, 7, 8, 9: weight 1

Threshold for Phase 7 certification: **≥ 85** AND **zero CRITICAL findings**.

---

## 6 · Remediation register (reviewer fills as findings emerge)

| # | Domain | Surface (page / component) | English string | Current Spanish | Verdict | Severity | Suggested operational-Spanish | Status |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

Status values: OPEN · ACKNOWLEDGED · CORRECTED-IN-PREVIEW · CORRECTED-IN-PROD · WONT-FIX-WITH-REASON.

---

## 7 · Where corrections live (single source of truth)

If a correction is authorized (separate directive · FOCP doctrine still applies), the only edit site is:
- `/app/frontend/src/lib/i18n.js` — primary dictionary
- `/app/backend/guidance/translations_es.py` — HelpTip Spanish content
- `/app/backend/guidance/translations_es_iter279.py` / `_iter280.py` — iteration-specific overlays

The AI agent **must not** invent new keys; it can only correct existing key→value pairs. Adding new bilingual surfaces is a build action and is currently OUT OF SCOPE under the FOCP Final Directive.

---

## 8 · Refusal conditions

The AI agent MUST refuse to:
- Auto-translate strings (this is exactly how dangerous mistranslations arrive)
- Score a domain without a reviewer's worksheet on file
- Mark a finding `CORRECTED-IN-PREVIEW` without operator authorization and a corresponding edit to the source files

---

**End of SPANISH OPERATIONAL PARITY AUDIT · OCEP Phase 3**
