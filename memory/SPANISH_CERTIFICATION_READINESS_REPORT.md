# SPANISH CERTIFICATION READINESS REPORT
## OCEP · Spanish Operational Certification Program (SOCP) · Phase 5

**Date**: 2026-06-03
**Authority**: OMEGA · SOCP Phase 5
**Mode**: READ-ONLY pre-certification readiness assessment
**Purpose**: For each workflow, classify the **codebase-only** readiness for Spanish operational certification as **GREEN · YELLOW · RED**, broken into four dimensions: **Operational · Safety · Training · Certification**. This is a pre-interview baseline — final certification belongs to real Spanish-speaking field personnel, not this report.

**Reading guide**:
- 🟢 **GREEN** — Spanish content exists, is professionally authored, source-direct verified, and presents no obvious risk on the dimension. Field review is procedural rather than corrective.
- 🟡 **YELLOW** — Spanish content exists but has at least one acceptable-but-non-ideal property (loanword usage, regional variance risk, definition gap that mirrors the English gap). Field review is required before certification but no engineering revision is presumed needed.
- 🔴 **RED** — Spanish content is absent, ambiguous on a safety-critical dimension, or carries a HIGH-risk finding from `SPANISH_SAFETY_CRITICAL_REGISTER.md`. Field review + likely engineering action (FOCP-gated) is required before certification.

The four dimensions:
- **Operational Readiness** — Can a Spanish-speaking operator do the workflow today without confusion?
- **Safety Readiness** — Does the Spanish content prevent unsafe interpretation?
- **Training Readiness** — Can a new Spanish-speaking hire learn the workflow from the surface itself?
- **Certification Readiness** — Is the surface ready to be presented to the field reviewer (Phase 4 packet) and likely to receive a certification verdict?

---

## 1 · Per-workflow readiness matrix

| # | Workflow | Operational | Safety | Training | Certification | Notes |
|---|---|:-:|:-:|:-:|:-:|---|
| 1 | Daily Report | 🟡 | 🟡 | 🟡 | 🟡 | Phase 2 `mistake` gap + kickback-reason language unclear; not a safety risk per se |
| 2 | Job Hazard Plan (JHP) | 🟡 | 🔴 | 🟡 | 🔴 | "Reconocer" semantic breadth (Phase 3 §1.1) + ES-only-no-email crew (§1.2) |
| 3 | Safety Meeting | 🟢 | 🟡 | 🟢 | 🟡 | 23 topic files are professionally written; field reviewer must walk for regional preferences |
| 4 | Incident Report | 🟡 | 🔴 | 🟡 | 🔴 | Severity labels (§3.1) + 3-attestation flag definitions (§3.2) |
| 5 | QA/QC Inspection | 🟡 | 🟡 | 🟡 | 🟡 | 3-path closure (A/B/C) needs Spanish-clarity field check |
| 6 | Site Inspection | 🟡 | 🟡 | 🟡 | 🟡 | `FINDINGS_RAISED` vs `DEFICIENCY_RAISED` Spanish naming risk (AR-0007) |
| 7 | Dispatch (board + driver) | 🟡 | 🟡 | 🟡 | 🟡 | Phase 2 P5 — Dispatch parent tip absent; ES gap mirrors EN |
| 8 | Fleet (Repair / RTS) | 🟡 | 🔴 | 🟡 | 🔴 | **Highest single-decision safety risk on the platform** (Phase 3 §8.2) |
| 9 | Equipment | 🟡 | 🟡 | 🟡 | 🟡 | Pre-shift + Issuance Spanish coverage; severity tier action wording |
| 10 | HR Hub / Time-Off | 🟢 | 🟢 | 🟢 | 🟢 | Public Time-Off is the simplest ES surface; HR Hub coverage strong |
| 11 | Employee Lifecycle (Reactivate vs Rehire) | 🟢 | 🟢 | 🟢 | 🟢 | The Phase-2 PASS reference workflow. Holds in ES per glossary. |
| 12 | Asset Transfer | 🟡 | 🟢 | 🟡 | 🟡 | Approvals-class Spanish coaching absent (Phase 2 P2) |
| 13 | Payroll Variance (attestation labels) | 🟡 | 🟢 | 🟡 | 🟡 | AR-0004 — attestation flag definitions absent in EN; same gap in ES |
| 14 | Constraints | 🟢 | 🟢 | 🟡 | 🟢 | Spanish exists; chronology / root-cause prompt quality is the risk |
| 15 | Purchase Orders | 🟡 | 🟢 | 🟡 | 🟡 | Approvals-class Spanish gap (Phase 2 P2) |
| 16 | Vendor Management | 🟡 | 🟢 | 🟡 | 🟡 | TR-0003 missing archive workflow; gap is structural, not linguistic |
| 17 | Project Management (hub view) | 🟢 | 🟢 | 🟡 | 🟢 | PM hub is read-side surface |
| 18 | Submittals | ⛔ | ⛔ | ⛔ | ⛔ | NOT-IMPLEMENTED; out of scope under FOCP |
| 19 | Universal Undo / Recovery Stream | 🟡 | 🟢 | 🟡 | 🟡 | FOCP R2 § 8 declares English-canonical for Recovery Stream; ES status field-reviewer-decided |

---

## 2 · Cross-cutting dimension readiness

### 2.1 · Operational Readiness (aggregate)

| Tier | Workflows | Count |
|---|---|---:|
| 🟢 GREEN | HR Hub, Employee Lifecycle, Constraints, Project Management | 4 |
| 🟡 YELLOW | Daily Report, JHP, Safety Meeting (op-tier), Incident, QA/QC, Site Insp, Dispatch, Fleet, Equipment, Asset Transfer, Payroll Variance, POs, Vendor, Recovery Stream | 14 |
| 🔴 RED | — | 0 |
| ⛔ NOT-IMPLEMENTED | Submittals | 1 |

**Aggregate operational readiness**: 🟡 **YELLOW** — Most workflows are operable in Spanish today; coaching gaps mirror English and do not block operation.

### 2.2 · Safety Readiness (aggregate)

| Tier | Workflows | Count |
|---|---|---:|
| 🟢 GREEN | HR Hub, Employee Lifecycle, Asset Transfer, Payroll Variance, Constraints, POs, Vendor, Project Management, Recovery Stream | 9 |
| 🟡 YELLOW | Daily Report, Safety Meeting, QA/QC, Site Inspection, Dispatch, Equipment | 6 |
| 🔴 RED | **JHP, Incident Report, Fleet (RTS)** | 3 |
| ⛔ NOT-IMPLEMENTED | Submittals | 1 |

**Aggregate safety readiness**: 🔴 **RED** — Three workflows carry HIGH risk findings (JHP attestation breadth, Incident attestation labels, Fleet RTS). Each requires field-reviewer judgment before any certification.

### 2.3 · Training Readiness (aggregate)

| Tier | Workflows | Count |
|---|---|---:|
| 🟢 GREEN | Safety Meeting, HR Hub, Employee Lifecycle | 3 |
| 🟡 YELLOW | All others except Submittals | 15 |
| 🔴 RED | — | 0 |

**Aggregate training readiness**: 🟡 **YELLOW** — Spanish content is broadly present and high-quality; Library closes the canonical-content gap (`WORKFLOW_EXPLANATION_LIBRARY.md` cited where applicable). Lift into in-app Spanish surfaces is the remaining gap.

### 2.4 · Certification Readiness (aggregate)

| Tier | Workflows | Count |
|---|---|---:|
| 🟢 GREEN — Ready for field review with high pass probability | HR Hub, Employee Lifecycle, Constraints, Project Management | 4 |
| 🟡 YELLOW — Ready for field review; YELLOW verdicts expected | Daily Report, Safety Meeting, QA/QC, Site Insp, Dispatch, Equipment, Asset Transfer, Payroll Variance, POs, Vendor, Recovery Stream | 11 |
| 🔴 RED — Field review likely surfaces engineering action items | JHP, Incident Report, Fleet (RTS) | 3 |
| ⛔ NOT-IMPLEMENTED | Submittals | 1 |

**Aggregate certification readiness**: 🟡 **YELLOW with three RED hotspots**.

---

## 3 · Highest-leverage targets for field-reviewer time

1. **Fleet RTS (Return-to-Service) attestation Spanish** — single highest decision-grade risk on the platform.
2. **JHP "Reconocer" attestation** — legal-attestation-chain risk; affects every Spanish-speaking acknowledger.
3. **Incident severity + 3-attestation flag Spanish definitions** — OSHA-recordable record integrity.
4. **JHP Spanish-only-no-email crew identity-key resolution** — coverage-gap, not language-gap, but surfaces only for ES-only operators.
5. **Email / SMS Spanish template DOCTRINE-SILENT** — existence/coverage of Spanish notification templates is unconfirmed; field reviewer should request operator clarification.

---

## 4 · What the field reviewer CANNOT verify from this package alone

Some Spanish-readiness facts are decidable only at runtime / by users:
- **Real comprehension under field pressure** — paper review cannot replicate a foreman handling a JHP at 5:55 a.m. on a Monday.
- **Regional-Spanish reception** — Spanish reviewers from one region cannot decide whether their wording works for crews from another.
- **Multi-modal operators** — operators who use bilingual code-switching may rate differently from operators who are Spanish-only.
- **PDF print fidelity** — Spanish content that displays cleanly on a tablet may render poorly on a printed Spanish PDF (`backend/pdf_render.py` flow). Reviewer must print and review a sample of each PDF artifact.

These limitations are honest. They do NOT block the field review; they bound its scope.

---

## 5 · What is NOT in this report

- No AI certification. Operator and field reviewers issue the final verdict.
- No fabricated reviewer feedback.
- No translation revisions proposed.
- No promotion of any finding to engineering action (all gaps remain ACTIVE / DEFERRED / DOCTRINE-EXEMPT per existing Truth Register classifications).

---

## 6 · Hand-off

This report is the **operator-facing readiness map**. The companion `SPANISH_FIELD_REVIEW_PACKET.md` is the **reviewer-facing review tool**. Together they form the SOCP Phase-4 + Phase-5 deliverables.

The next move belongs to:
1. The operator (assigns reviewers, sets a review window).
2. The Spanish-speaking field reviewers (walk the packet, fill the 5-question cards).
3. The operator (aggregates the cards, issues GREEN / YELLOW / RED certification).

The AI agent's work on SOCP Phases 1–5 is complete.

---

**End of SPANISH CERTIFICATION READINESS REPORT · SOCP Phase 5**
