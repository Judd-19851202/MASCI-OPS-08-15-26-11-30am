# SPANISH FIELD REVIEW PACKET
## OCEP · Spanish Operational Certification Program (SOCP) · Phase 4

**Date**: 2026-06-03
**Authority**: OMEGA · SOCP Phase 4
**Mode**: READ-ONLY packet preparation · no certification by AI
**Audience**: This packet is intended for **real Spanish-speaking field personnel**:
- **Spanish Superintendent** (regional / cross-trade depth)
- **Spanish Foreman** (daily-driver of the platform on-site)
- **Spanish Safety Representative** (hazard / OSHA / liability lens)

**Purpose**: Provide structured per-workflow review prompts and a scoring template the operator can hand to live reviewers. The AI agent produces only the **packet**, not the **certification**.

**Use instructions for the operator**:
1. Print this packet (or share the markdown to a tablet/laptop).
2. Open the platform in **ES mode** (LangToggle → ES).
3. Have each reviewer walk one workflow at a time. Each reviewer fills the 5-question card for every workflow assigned to them.
4. Collect completed packets. Operator (not AI) aggregates verdicts in the Certification Readiness Report.

**Reviewer instructions (Spanish)** *(included for direct reviewer hand-off)*:
> Por favor revise cada flujo de trabajo en el español que aparece en el sistema. Use su experiencia de campo para responder las 5 preguntas. Si algo no se siente natural o podría confundir a su cuadrilla, dígalo. Su voz es la última palabra — no la herramienta, no la traducción, no la IA. Gracias.

---

## 1 · Reviewer assignment matrix (suggested)

| Workflow | Spanish Superintendent | Spanish Foreman | Spanish Safety Rep |
|---|:-:|:-:|:-:|
| Daily Report | ✓ | **PRIMARY** | ✓ |
| Job Hazard Plan (JHP) | ✓ | ✓ | **PRIMARY** |
| Safety Meeting | ✓ | ✓ | **PRIMARY** |
| Incident Report | ✓ | ✓ | **PRIMARY** |
| QA/QC Inspection | **PRIMARY** | ✓ | — |
| Site Inspection | **PRIMARY** | ✓ | ✓ |
| Dispatch (Driver shift-start) | **PRIMARY** | ✓ | — |
| Fleet (Repair / RTS) | **PRIMARY** | — | ✓ |
| Equipment (Inspection / Issuance) | ✓ | **PRIMARY** | ✓ |
| HR Hub / Time-Off (public) | ✓ | ✓ | — |
| Employee Lifecycle (Reactivate vs Rehire — read-side) | **PRIMARY** | ✓ | — |
| Asset Transfer | — | **PRIMARY** | — |
| Payroll Variance (attestation labels) | **PRIMARY** | — | — |
| Constraints | **PRIMARY** | ✓ | — |
| Help Tips · Tooltips · Validation messages | ✓ | **PRIMARY** | ✓ |
| 23 Safety Topic dictionaries (`topics/*.es.js`) | ✓ | ✓ | **PRIMARY** |

---

## 2 · The 5-question card (use one per workflow)

For each workflow listed in Section 3:

```
WORKFLOW: ________________________________
REVIEWER NAME: ____________________________
REVIEWER ROLE: ____________________________
REGION OF EXPERIENCE (Mexico / CA / Caribbean / SA / Other): _______________
DATE: __________

1. Does this sound natural?
   ⬜ Yes, perfectly natural    ⬜ Mostly yes    ⬜ Awkward    ⬜ Not natural
   Comment: ___________________________________________________________

2. Would you use different wording?
   ⬜ No                          ⬜ Minor change   ⬜ Major change
   Specific wording I would change:
   FROM: _______________________________________________________________
   TO:   _______________________________________________________________

3. Is anything confusing?
   ⬜ Nothing confusing           ⬜ Minor confusion   ⬜ Significant confusion
   Specific phrase / page / button that confused me:
   _____________________________________________________________________

4. Could this create a safety misunderstanding?
   ⬜ No risk                     ⬜ Low risk           ⬜ MODERATE risk          ⬜ HIGH risk
   If MODERATE or HIGH, describe what could go wrong:
   _____________________________________________________________________

5. Would your crew understand this?
   ⬜ Yes, everyone               ⬜ Most            ⬜ Some would struggle      ⬜ Most would struggle
   Specific crew profile that would struggle (e.g., new hires, Caribbean Spanish speakers, illiterate readers):
   _____________________________________________________________________

OVERALL SCORE FOR THIS WORKFLOW:
   ⬜ 🟢 GREEN — Ready as-is
   ⬜ 🟡 YELLOW — Acceptable with minor wording polish (operator-led, no engineering)
   ⬜ 🟠 ORANGE — Requires engineering revision before certification
   ⬜ 🔴 RED — Unsafe / unusable as-is, urgent revision needed
```

---

## 3 · Per-workflow review prompts

Each block below tells the reviewer **where to look**, **what to specifically check**, and **which safety-critical concerns to weigh** (drawn from `SPANISH_SAFETY_CRITICAL_REGISTER.md`).

### 3.1 · Daily Report
- **Route**: `/daily-reports/new` and `/daily-reports`
- **In ES mode, check**:
  - Page title, all field labels, the photo-gate validation hint ("NEED N MORE PHOTO(S)")
  - The `HelpTipBlock` "why" / "when" / "next" tips
  - The post-submit success state and sticky-footer copy
  - The kickback-reason language on a returned report
- **Specific Spanish concern (from SOCP Phase 3)**: Does the kickback reason on the list-view tile read naturally? Does the operator know what `Pending Office Review` means without coaching? (AR-0003)

### 3.2 · Job Hazard Plan (JHP)
- **Routes**: `/jha` (public) · `/admin/jha-acknowledgements` (admin)
- **Specific Spanish concern (HIGH RISK per Phase 3)**:
  - Acknowledge button copy: does "Reconocer" feel like a legal attestation or merely "I read it"?
  - Spanish-only crew with no work-email: can they acknowledge at all?
  - Re-acknowledgement on a new version: is it clear both signatures are preserved and which one binds?

### 3.3 · Safety Meeting
- **Route**: `/meetings/new`, `/meetings`
- **In ES mode, check**:
  - Walk all 23 trade topic dictionaries via `/safety-topic-library` and flip through topics by trade.
  - Specifically verify the excavation topic (`trenching_shoring`, `soil_classification`, `excavation_potholing_daylight`, `excavation_spoil_placement`) — these are the most safety-critical.
- **Specific concern**: Does "engullimiento" land for your crew or do they say "sepultamiento"? Is "nomás un minuto" (Mexican Spanish) natural for all your crews?

### 3.4 · Incident Report
- **Routes**: `/incidents/new` (public), incident detail
- **Specific concerns (HIGH RISK per Phase 3)**:
  - Severity classification labels — does the Spanish "Reportable" risk being read as "must report" (which all incidents are) rather than "OSHA-recordable"?
  - The 3-attestation closure flags — is each flag's purpose unambiguous in Spanish?
  - Narrative prompt — does it pull a SPECIFIC narrative ("laceración al dedo índice derecho") or a vague one ("se lastimó el dedo")?

### 3.5 · QA/QC Inspection
- **Route**: `/qaqc-inspections/new`, detail
- **Specific concerns**: 3-path closure (A / B / C) — Spanish copy must clearly distinguish (A) re-inspection passed · (B) corrective action ≥ 20 chars · (C) exception with PM + Safety dual sign-off ≥ 10 chars.

### 3.6 · Site Inspection
- **Route**: `/inspections/new`
- **Specific concerns**: `FINDINGS_RAISED` (Site) vs `DEFICIENCY_RAISED` (QA/QC) — are both Spanish terms clearly distinct? (AR-0007 risk)

### 3.7 · Dispatch / Driver shift-start
- **Routes**: `/admin/dispatch` (admin board) · driver-side QR / shift-start pages
- **Specific concerns**: Driver shift-start instructions must be unambiguous for Spanish-only drivers. Day-1 / Week-1 debrief language.

### 3.8 · Fleet / RTS (Return-to-Service)
- **Routes**: `/admin/fleet`
- **Specific concerns (HIGHEST RISK on the platform per Phase 3 §8.2)**: RTS attestation Spanish — who is authorizing, on what basis, does Spanish copy match the doctrine?
- Severity tier color names (Rojo / Amarillo / Verde) — and the **action** for each tier.

### 3.9 · Equipment (Inspection / Issuance / Training)
- **Routes**: `/admin/equipment` · equipment-issuance acknowledgement
- **Specific concerns**: Pre-shift inspection prompts. Issuance signature line. Training expiration warnings.

### 3.10 · HR Hub / Time-Off (public) / Employee Lifecycle
- **Routes**: `/admin/hr`, `/admin/hr/time-off`, `/time-off` (public), `/admin/hr/employees`
- **Specific concerns**:
  - Time-Off public form — does an employee with limited English understand the request mechanism?
  - Employee Lifecycle **Reactivate vs Rehire** — the Spanish must communicate that **Reactivar** preserves `original_hire_date` and **Re-contratar** loses it. This is the single Phase-2 PASS workflow; reviewer should confirm it stays a PASS in Spanish.

### 3.11 · Asset Transfer
- **Route**: `/asset-transfers`
- **Specific concerns**: Sender / Receiver attestation Spanish. Acceptance / rejection reason field.

### 3.12 · Payroll Variance (attestation labels — read-side for Spanish reviewer)
- **Route**: `/admin/hr/payroll-variance`
- **Specific concerns**: 3-attestation flag labels (`review_complete`, `approval_complete`, `variance_decisions_complete`) — per AR-0004 they have no per-flag definition even in English. Spanish gap is at least as wide. Highest-stakes ticks on the platform after RTS.

### 3.13 · Constraints
- **Route**: `/constraints/new`, detail
- **Specific concerns**: Chronology field — does Spanish prompt elicit specific, dated entries or vague summaries? Resolution root-cause field — does Spanish prompt produce decision-grade text?

### 3.14 · Help Tips / Tooltips / Validation messages (cross-cutting)
- **Locations**: Every form's `<HelpTip>` block + `toast.error` strings
- **Specific concerns**: `mistake` kind absent on 14 form_keys (Phase 2 P1) — this gap exists in BOTH languages. Spanish reviewer should still flag any tip that DOES exist and reads poorly.

### 3.15 · 23 Safety Topic dictionaries (`frontend/src/lib/topics/*.es.js`)
- **Location**: `/safety-topic-library` page
- **The 23 files**:
  1. airport · 2. concrete · 3. dewatering · 4. electrical · 5. environmental · 6. excavation · 7. fall_protection · 8. general · 9. grading · 10. lab · 11. milling · 12. mot · 13. office · 14. paving · 15. pipe · 16. plant · 17. rigging · 18. shop · 19. trucking · 20. utilities · 21. wellness · (22+23) any overflow domains
- **Method**: Walk file-by-file. Use the 5-question card per file. Focus on the four mandatory fields per topic: `incident_pattern`, `hazards_reviewed`, `discussion_notes`, `action_items`, `references_cited`.
- **Specific concerns**: Loanword usage ("spoil", "daylight", "potholing", "TMA", "wellpoint", "comm"), regional verb choices, OSHA citation accuracy.

---

## 4 · Aggregate scoring template

After all per-workflow cards are completed, the operator (NOT the AI) summarizes:

```
SPANISH OPERATIONAL CERTIFICATION — AGGREGATE SCORECARD
Date completed: ___________
Lead reviewer: ___________

WORKFLOW                              GREEN  YELLOW  ORANGE  RED  VERDICT
Daily Report                          [  ]   [  ]    [  ]    [  ] _______
JHP                                   [  ]   [  ]    [  ]    [  ] _______
Safety Meeting                        [  ]   [  ]    [  ]    [  ] _______
Incident Report                       [  ]   [  ]    [  ]    [  ] _______
QA/QC Inspection                      [  ]   [  ]    [  ]    [  ] _______
Site Inspection                       [  ]   [  ]    [  ]    [  ] _______
Dispatch / Driver shift-start         [  ]   [  ]    [  ]    [  ] _______
Fleet (RTS)                           [  ]   [  ]    [  ]    [  ] _______
Equipment                             [  ]   [  ]    [  ]    [  ] _______
HR Hub / Time-Off                     [  ]   [  ]    [  ]    [  ] _______
Employee Lifecycle                    [  ]   [  ]    [  ]    [  ] _______
Asset Transfer                        [  ]   [  ]    [  ]    [  ] _______
Payroll Variance (labels)             [  ]   [  ]    [  ]    [  ] _______
Constraints                           [  ]   [  ]    [  ]    [  ] _______
Help tips / Tooltips / Validation     [  ]   [  ]    [  ]    [  ] _______
23 Safety Topic dictionaries          [  ]   [  ]    [  ]    [  ] _______

OVERALL OPERATIONAL READINESS:     ⬜ GREEN  ⬜ YELLOW  ⬜ ORANGE  ⬜ RED
OVERALL SAFETY READINESS:          ⬜ GREEN  ⬜ YELLOW  ⬜ ORANGE  ⬜ RED
OVERALL TRAINING READINESS:        ⬜ GREEN  ⬜ YELLOW  ⬜ ORANGE  ⬜ RED
OVERALL CERTIFICATION READINESS:   ⬜ GREEN  ⬜ YELLOW  ⬜ ORANGE  ⬜ RED

REVIEWER SIGNATURE: ___________________________________________
```

---

## 5 · What this packet does NOT include

- Does **not** include AI-generated certification.
- Does **not** include AI-generated reviewer quotes or fake field findings.
- Does **not** include AI-generated regional preferences (the field reviewer supplies these).
- Does **not** propose translation changes (per directive STOP).
- The certification can only be issued by the human field reviewers.

---

**End of SPANISH FIELD REVIEW PACKET · SOCP Phase 4**
