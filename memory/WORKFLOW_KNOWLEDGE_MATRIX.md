# WORKFLOW KNOWLEDGE MATRIX
## OCEP · Training Completion Program (TCP)

**Date**: 2026-06-03
**Authority**: OMEGA · TCP
**Mode**: READ-ONLY · role × workflow understanding requirements
**Purpose**: For each role, identify which workflows the role MUST understand (Owner), SHOULD understand (Participant), and may IGNORE (Out-of-Scope). This matrix drives role-targeted training prioritization without authorizing any build.

Legend:
- **O** = Owner (must know all 10 fields cold; primary author/decider)
- **P** = Participant (must understand the workflow; not owner; their role intersects)
- **R** = Read-side (visibility only; no decision authority)
- **·** = Out-of-scope for this role

---

## 1 · 19 × 9 master grid

| # | Workflow | Laborer | Foreman | Super | PM | Safety | Dispatch | HR | Shop | Executive |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | Daily Report | P | **O** | P | R | · | P | R | · | R |
| 2 | JHP | **O** (ack) | **O** (roster + brief) | P | P | **O** (author) | · | · | · | R |
| 3 | Safety Meeting | P (attend) | **O** (facilitator) | P | P | **O** (curator) | · | · | · | R |
| 4 | Incident Report | P (report) | P (first-on-scene) | P | P | **O** (triage + close) | P (driver-involved) | P (employee record) | P (equipment-involved) | R |
| 5 | QA/QC Inspection | · | P | P | **O** (closure) | **O** (closure) | · | · | · | · |
| 6 | Site Inspection | · | P | P | P | **O** (author + closure) | · | · | · | · |
| 7 | Dispatch | P (assignment recipient) | P (assignment recipient) | P | P | · | **O** | P (qualifications) | P (equipment) | R |
| 8 | Fleet (Repair/RTS) | P (defect report) | P | · | · | P (incident-involved) | P (offline visibility) | · | **O** | R |
| 9 | Equipment | **O** (pre-shift + ack) | P | · | · | P (issuance auth) | P (operator-binding) | P (training records) | P (readiness) | · |
| 10 | HR Hub | · | · | · | · | · | · | **O** | · | R |
| 11 | Time Off | **O** (requestor) | P (approver of crew) | · | P (approver) | · | · | **O** (queue) | · | R |
| 12 | Employee Lifecycle | · | P (hire recommendation) | P | P | · | · | **O** | · | R |
| 13 | Asset Transfer | P (sender/receiver) | P | P | P | · | P | · | P | · |
| 14 | Payroll Variance | · | · | · | · | · | · | **O** (review/approve) | · | **O** (finalize-authority sits with admin) |
| 15 | Constraints | · | P (impact reporter) | P | **O** (author) | · | · | · | · | R |
| 16 | Submittals | · | · | · | **O** (not built) | · | · | · | · | R |
| 17 | Purchase Orders | · | · | · | **O** (initiator) | · | · | · | · | **O** (approver above threshold) |
| 18 | Vendor Management | · | · | · | **O** | · | · | · | · | R |
| 19 | Project Management | · | P | P | **O** | P | · | P | · | R |

---

## 2 · Per-role mandatory-knowledge load

| Role | Owner count | Participant count | Read count | Out-of-scope | Total touched |
|---|---:|---:|---:|---:|---:|
| Laborer | 2 (JHP ack, Equipment pre-shift, Time-Off requestor) | 6 | 0 | 11 | 8 |
| Foreman | 3 (Daily Report, JHP roster, Safety Meeting) | 11 | 0 | 5 | 14 |
| Superintendent | 0 | 9 | 0 | 10 | 9 |
| PM | 5 (QA/QC, Constraints, Submittals*, POs, Vendor, Project) | 7 | 0 | 7 | 12 |
| Safety | 4 (JHP author, Safety Meeting curator, Incident, QA/QC closure, Site Inspection) | 5 | 0 | 10 | 9 |
| Dispatch | 1 (Dispatch) | 5 | 0 | 13 | 6 |
| HR | 4 (HR Hub, Time-Off queue, Employee Lifecycle, Payroll Variance) | 2 | 0 | 13 | 6 |
| Shop | 1 (Fleet) | 4 | 0 | 14 | 5 |
| Executive | 2 (Payroll Variance finalize, PO above threshold) | 0 | 11 | 6 | 13 |

(*Submittals listed as Owner for PM but workflow is NOT-IMPLEMENTED; resolved by operator decision.)

**Observations** (source-direct only, no inference of operator behavior):
- **Foreman** carries the broadest knowledge load (3 owner workflows + 11 participant workflows = 14 of 19 touched). Highest leverage role for training investment.
- **HR** owns 4 workflows but touches only 6 total; depth-not-breadth training profile.
- **PM** carries the second-broadest profile (5 owner + 7 participant), with the most cross-workflow decision authority.
- **Laborer** has the smallest mandatory knowledge load (8 of 19 touched) — supports the assertion that field-crew training can be focused tightly.
- **Executive** is mostly Read-side; the 2 Owner workflows (PV finalize authority, large-threshold PO) are high-stakes / low-frequency.

---

## 3 · Cross-workflow knowledge dependencies

Workflows where understanding ONE requires fluency in ANOTHER:

| Primary workflow | Dependency workflows | Why |
|---|---|---|
| Daily Report | JHP (must be acknowledged before DR makes sense); Payroll Variance (DR hours flow into) | Sequential |
| JHP | Daily Report; Incident Report; Safety Meeting | Bidirectional |
| Incident Report | JHP review post-incident; Corrective Action; Safety Meeting | Causal |
| QA/QC + Site Inspection | Corrective Action (closure path B IS a CAPA) | Definitional |
| Dispatch | Driver Qualification (HR-side); Fleet (Shop offline status); Time-Off | Cross-domain |
| Payroll Variance | Daily Report (source data); Time-Off (PTO impact) | Reconciliation |
| Employee Lifecycle | Time-Off (separation affects PTO); Payroll Variance | Bidirectional |
| Purchase Orders | Vendor Management (POs go to vendors); Project Management (PO charges project) | Containment |
| Constraints | Project Management (job health); Daily Report (DR notes impact) | Cross-reference |

A role responsible for the Primary workflow should also be conversant with the Dependency workflows even when not Owner.

---

## 4 · Highest-leverage training targets (source-direct prioritization)

Based on Owner-count × cross-role-dependency × Phase-2 verdict:

| Rank | Workflow | Why this is the highest-leverage training surface |
|---|---|---|
| 1 | **Daily Report** | Foreman owner + Super/PM/Dispatch/HR/Exec all touch + Phase 2 PARTIAL with `mistake` gap |
| 2 | **JHP** | 5 roles own/participate + Phase 2 PARTIAL post-FOCP-R2 newness + identity-key risk for Spanish-only crew |
| 3 | **Incident Report** | Every role touches + safety-tier risk + Phase 2 PARTIAL `mistake` gap |
| 4 | **QA/QC closure** | 3-path Amendment 001 contract; highest decision-complexity workflow on the platform |
| 5 | **Payroll Variance** | NO AUTO-FINALIZE doctrine + 3-attestation gate; HR + Exec joint authority; weekly cadence |
| 6 | **Approvals class** (Time-Off, PO, Asset Transfer, Employee Request) | Phase 2 FAIL · PM + HR + Foreman all touch |
| 7 | **Fleet (Repair/RTS)** | Phase 2 FAIL · Shop's mistakes are the platform's most consequential |
| 8 | **Dispatch** | Phase 2 PARTIAL · entry-point coaching absent · daily-run |
| 9 | **Employee Lifecycle Reactivate-vs-Rehire** | Already at PASS (reference) — keep current; do not regress |
| 10 | **Universal Undo + Recovery Stream** | Brand-new (FOCP R2); admin-only; doctrine-exempt from tips but un-validated against operator behavior |

---

**End of WORKFLOW KNOWLEDGE MATRIX · TCP**
