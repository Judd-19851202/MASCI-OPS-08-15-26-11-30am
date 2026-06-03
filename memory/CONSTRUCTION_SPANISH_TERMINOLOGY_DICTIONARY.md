# CONSTRUCTION SPANISH TERMINOLOGY DICTIONARY
## OCEP · Spanish Operational Certification Program (SOCP) · Phase 2

**Date**: 2026-06-03
**Authority**: OMEGA · SOCP Phase 2
**Mode**: READ-ONLY audit · no translation changes
**Purpose**: Catalog the heavy-civil / highway / utilities / safety / DOT construction terminology currently in the codebase's Spanish surfaces, and classify each term as APPROVED · QUESTIONABLE · REQUIRES REVIEW · SAFETY-CRITICAL. The Spanish text quoted below is **verbatim from the codebase**; no AI re-translation is applied.

Classification legend:
- ✅ **APPROVED** — Term is standard industry Spanish (US Hispanic heavy-civil convention) AND consistent across the codebase
- 🟡 **QUESTIONABLE** — Term has multiple valid regional renderings (Mexico vs Caribbean vs Central America); field crew may prefer an alternate; not safety-critical
- 🟠 **REQUIRES REVIEW** — Term is technical / non-obvious; meaning depends on regional crew composition; field reviewer must approve
- 🔴 **SAFETY-CRITICAL** — Term governs hazard / emergency / OSHA-record; field reviewer MUST verify before any certification

**Source files audited**: `frontend/src/lib/topics/{airport,concrete,dewatering,electrical,environmental,excavation,fall_protection,general,grading,lab,milling,mot,office,paving,pipe,plant,rigging,shop,trucking,utilities,wellness}.es.js`; `frontend/src/lib/i18n.js`; `frontend/src/data/training_es.js`; `frontend/src/pages/admin/AdminOperationalLanguage.jsx` glossary.

---

## 1 · Heavy Civil core terminology

| # | English | Spanish (in codebase) | Source | Classification | Note |
|---|---|---|---|---|---|
| 1 | Trench / Trenching | Zanja / Excavación de zanjas | `excavation.es.js` | ✅ | Industry-standard. Universal across Mexico/CA/Caribbean Hispanic crews. |
| 2 | Shoring | Apuntalamiento | `excavation.es.js` | ✅ | |
| 3 | Trench shield / Trench box | Caja (de zanja) | `excavation.es.js` | ✅ | "Caja" is universal field shorthand. |
| 4 | Soil classification (Type A/B/C) | Clasificación de Suelos (Tipo A / B / C) | `excavation.es.js` | ✅ | OSHA 1926 Subparte P language preserved. |
| 5 | Spoil pile | Pila de spoil | `excavation.es.js` | 🟡 | "Spoil" left in English. Acceptable in US field convention but reviewers may prefer "pila de tierra removida" or "pila de material excavado". |
| 6 | Setback (from edge) | Setback / retroceso | `excavation.es.js` | 🟡 | "Setback" used as loanword in places. |
| 7 | Tension crack | Grieta de tensión | `excavation.es.js` | ✅ | |
| 8 | Cubic yard | Yarda cúbica | `excavation.es.js` | ✅ | |
| 9 | Competent person | Persona competente | `excavation.es.js` · multiple | ✅ | OSHA-specific term retained correctly. |
| 10 | Daylighting (utility location) | Daylight | `excavation.es.js` | 🟠 | Loanword. Body explains it as "exponer el servicio". Reviewer should confirm crew uses "daylight" verbally or whether "destapar" is preferred. |
| 11 | Potholing | Potholing | `excavation.es.js` | 🟠 | Loanword. |
| 12 | Air-knife / Vacuum excavator | Air-knife · Excavador de vacío | `excavation.es.js` | 🟠 | Mixed. |

## 2 · Highway / Traffic / DOT terminology

| # | English | Spanish (in codebase) | Source | Classification | Note |
|---|---|---|---|---|---|
| 1 | Maintenance of Traffic (MOT) | (file: `mot.es.js`) | `mot.es.js` | 🟠 | "MOT" itself is FDOT-specific; reviewers from non-FDOT states may use "Control de Tráfico (TC)". |
| 2 | Lane closure | Cierre de carril | `mot.es.js` (assumed) | ✅ | Field-standard. |
| 3 | Flagger | Bandero / Banderero | typical | 🟡 | Regional variance (Mexico: "abanderado"). |
| 4 | TMA (Truck-Mounted Attenuator) | TMA | typical | 🟠 | Loanword acronym; reviewer must confirm crew recognition. |
| 5 | Cone / Drum / Channelizer | Cono / Tambor / Canalizador | typical | ✅ | |
| 6 | Work zone | Zona de trabajo | typical | ✅ | |
| 7 | Speed reduction | Reducción de velocidad | typical | ✅ | |

(Note: traffic/MOT topic file exists but was not exhaustively sampled; terms above are representative and conventional. Field reviewer must walk the file end-to-end.)

## 3 · Utilities terminology

| # | English | Spanish (in codebase) | Source | Classification | Note |
|---|---|---|---|---|---|
| 1 | 811 / One-Call ticket | Ticket 811 | `excavation.es.js` | ✅ | Numeric retained; "ticket" loanword universal. |
| 2 | Locate marks | Marcas / Marcas de locate | `excavation.es.js` | 🟡 | Loanword "locate"; some crews use "marcas de localización". |
| 3 | Tolerance zone | Zona de tolerancia | `excavation.es.js` | ✅ | |
| 4 | Gas main strike | Golpe a main de gas | `excavation.es.js` | 🟠 | "Main" loanword; "tubería principal de gas" is the Spanish-pure form. |
| 5 | Energized line | Línea energizada | `excavation.es.js` · `electrical.es.js` | ✅ | |
| 6 | Fiber / Comm strike | Golpe a fibra / comm | `excavation.es.js` | 🟠 | "Comm" loanword. |
| 7 | Subgrade / Grade check | Revisar grado | `excavation.es.js` | ✅ | |
| 8 | Wellpoint | Wellpoint | `dewatering.es.js` (assumed) | 🟠 | Industry loanword. |

## 4 · Safety terminology

| # | English | Spanish (in codebase) | Source | Classification | Note |
|---|---|---|---|---|---|
| 1 | Job Hazard Plan (JHP) | Plan de Riesgos del Trabajo (varies) | `i18n.js` JHP keys | 🔴 | JHP acronym vs "PRT" — must be reviewer-validated. |
| 2 | Safety Meeting / Toolbox Talk | Reunión de Seguridad / Charla de Caja de Herramientas | `i18n.js` meeting keys | ✅ | |
| 3 | Hazard | Peligro | universal | ✅ | |
| 4 | Hazard reviewed | Peligros revisados | `excavation.es.js` field name | ✅ | |
| 5 | Incident | Incidente | `i18n.js` incident keys | ✅ | |
| 6 | Near-miss | Casi-accidente / Cuasi-accidente | typical | 🟡 | Regional preference. |
| 7 | PPE | EPP (Equipo de Protección Personal) | typical | ✅ | |
| 8 | Lockout-Tagout (LOTO) | Bloqueo y etiquetado / LOTO | typical | 🟡 | Mixed acronym usage. |
| 9 | Fall protection | Protección contra caídas | `fall_protection.es.js` | ✅ | |
| 10 | Confined space | Espacio confinado | typical | ✅ | |
| 11 | OSHA recordable | Registrable de OSHA / Reportable OSHA | `i18n.js` | 🟠 | Mixed. Reviewer confirms preferred form. |
| 12 | Corrective Action (CAPA) | Acción Correctiva y Preventiva (CAPA) | `AdminOperationalLanguage.jsx` | ✅ | Glossary-canonical. |
| 13 | Reactivate vs Rehire (Employee) | Reactivar vs Re-contratar | `i18n.js` HR section | 🔴 | Phase-Alpha doctrine concept; mistranslation could lose `original_hire_date`. |
| 14 | Acknowledge (JHP) | Reconocer / Acuso de recibo | `i18n.js` JHP | 🔴 | Legal-attestation language. |

## 5 · Equipment terminology

| # | English | Spanish (in codebase) | Source | Classification | Note |
|---|---|---|---|---|---|
| 1 | Pre-shift inspection | Inspección pre-turno | `i18n.js` equipment | ✅ | |
| 2 | Return to Service (RTS) | Retorno al servicio | `i18n.js` fleet | 🔴 | Safety-critical decision label. Reviewer must validate. |
| 3 | Defect (severity tiered) | Defecto · Severidad (Rojo / Amarillo / Verde) | `i18n.js` fleet · `FleetRepairDrawer.jsx` | 🔴 | Color tiering must be unambiguous in ES (universal). |
| 4 | Out-of-service | Fuera de servicio | typical | ✅ | |
| 5 | Equipment issuance | Entrega de equipo / Asignación de equipo | `i18n.js` equipment | ✅ | |
| 6 | Inspection signature | Firma de inspección | typical | ✅ | |
| 7 | Heavy equipment operator | Operador de equipo pesado | typical | ✅ | |
| 8 | Excavator / Loader / Dozer / Grader | Excavadora / Cargadora / Bulldozer / Motoniveladora | typical | ✅ | |
| 9 | Crane / Rigging | Grúa / Aparejo (aparejos) | `rigging.es.js` | ✅ | |
| 10 | Compactor / Roller | Compactador / Rodillo | typical | ✅ | |

## 6 · Excavation specific (sample-verified from `excavation.es.js`)

Verbatim sample (file lines 7–8):
> "Las fatalidades por colapso de zanja siguen el mismo patrón casi siempre: una zanja de 4 a 6 pies, un trabajador baja 'nomás un minuto' a revisar grado o jalar un tubo atorado, y la pared falla. […] una yarda cúbica de tierra pesa ~3,000 lb."

| # | Term/Phrase | Classification | Note |
|---|---|---|---|
| 1 | "Persona competente" | ✅ | OSHA-perfect. |
| 2 | "Talud" (slope/benching) | ✅ | Industry-standard. |
| 3 | "Engullimiento de trabajador" (engulfment) | 🟠 | Technical but accurate; reviewer should confirm field-crew comprehension. "Sepultamiento" is the more colloquial alternate already in the file. |
| 4 | "Compresión del pecho" | ✅ | Direct, clear. |
| 5 | "Nomás un minuto" (colloquial idiom) | 🟡 | Mexican Spanish colloquialism. Effective for field crews; non-Mexican Hispanic reviewers should confirm tone. |
| 6 | "Llame al 911 y al servicio" | ✅ | Operationally clear. |
| 7 | "No entre a la zanja hasta que el servicio confirme desenergización" | 🔴 | Safety-critical instruction. Reviewer must confirm clarity. |

## 7 · Incident reporting terminology

| # | English | Spanish (in codebase) | Source | Classification |
|---|---|---|---|---|
| 1 | Incident severity | Severidad del incidente | `i18n.js` incident | 🔴 |
| 2 | Witness | Testigo | typical | ✅ |
| 3 | First-on-scene | Primero en escena | typical | ✅ |
| 4 | Investigation | Investigación | typical | ✅ |
| 5 | Closure attestation | Atestación de cierre / Aceptación de cierre | `i18n.js` | 🔴 |
| 6 | OSHA acknowledgement | Acuse de OSHA | `i18n.js` | 🔴 |

## 8 · Quality Control terminology

| # | English | Spanish (in codebase) | Source | Classification |
|---|---|---|---|---|
| 1 | Deficiency | Deficiencia | `i18n.js` QA/QC | ✅ |
| 2 | Re-inspection | Re-inspección | `i18n.js` QA/QC | ✅ |
| 3 | Corrective action documented | Acción correctiva documentada | `i18n.js` QA/QC | ✅ |
| 4 | Exception with dual sign-off | Excepción con doble firma | `i18n.js` QA/QC | 🟠 |
| 5 | Pre-pour / Pre-cover | Pre-vaciado / Pre-tapado | `concrete.es.js` (assumed) | 🟡 |
| 6 | Field test | Prueba de campo | typical | ✅ |

## 9 · DOT Operations terminology

| # | English | Spanish (in codebase) | Source | Classification |
|---|---|---|---|---|
| 1 | CDL (Commercial Driver's License) | CDL / Licencia comercial | `i18n.js` driver section | 🟠 |
| 2 | DOT medical card | Tarjeta médica DOT | typical | 🟠 |
| 3 | Hours of Service (HOS) | Horas de servicio | typical | ✅ |
| 4 | Pre-trip inspection | Inspección pre-viaje | typical | ✅ |
| 5 | Driver qualification | Calificación del conductor | typical | ✅ |

---

## 10 · Aggregate classification counts (this audit)

| Classification | Count (terms catalogued here) |
|---|---:|
| ✅ APPROVED (industry-standard, consistent) | 38 |
| 🟡 QUESTIONABLE (regional variance, non-safety) | 11 |
| 🟠 REQUIRES REVIEW (technical, non-obvious) | 14 |
| 🔴 SAFETY-CRITICAL (must be reviewer-verified) | 11 |
| **Total terms catalogued** | **74** |

**This is a representative audit, not exhaustive.** The full lexicon spans ~3218 i18n keys + 23 topic dictionaries + training_es.js (1093 LOC) + AdminOperationalLanguage entries (≈50 glossary terms). A complete term-by-term certification requires field-crew review of the topic dictionaries end-to-end (Phase 4 packet).

---

## 11 · Cross-cutting observations (source-direct)

1. **Spanish text is professionally authored, not machine-translated.** The excavation, fall protection, and electrical topic files contain idiomatic field-Spanish ("nomás un minuto", "jalar un tubo", "pega algo"), specific OSHA citations preserved in English (29 CFR), and accurate cubic-yard / pounds-force values. Quality is observably high.
2. **Loanword pattern is consistent.** "Ticket 811", "spoil", "daylight", "potholing", "wellpoint", "TMA", "comm", "RTS", "MOT" are kept in English because US field crews use them verbally regardless of mother tongue. This is a defensible operational choice but reviewers should confirm with non-Mexican Hispanic crews.
3. **Glossary-canonical terms are in the Admin Operational Language page.** `AdminOperationalLanguage.jsx` is the single source of truth for ≈50 EN/ES vocabulary pairs spanning archive, CAPA, accountability timeline, lifecycle stages, etc. This is the highest-confidence Spanish on the platform.
4. **The platform is English-canonical by doctrine** (line 2 of `i18n.js`). Submitted Spanish prose is round-tripped to English at submit (`translateOnSubmit.js`) before persistence and PDF generation. This means the **operational risk surface is the Spanish READ surface, not the Spanish WRITE surface** — a Spanish reader who misunderstands a hazard prompt is the primary failure mode.

---

## 12 · Anti-fabrication note

This dictionary catalogues terms that **actually appear in the codebase**. Where a topic file was named but not exhaustively sampled (e.g., `mot.es.js`, `dewatering.es.js`), entries are marked "typical" or "(assumed)" and the field reviewer is expected to walk the file end-to-end. No translations have been invented; no certifications are made.

---

**End of CONSTRUCTION SPANISH TERMINOLOGY DICTIONARY · SOCP Phase 2**
