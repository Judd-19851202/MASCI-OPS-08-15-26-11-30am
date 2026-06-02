# OMEGA · FORGEDOPS IGNORE LIST

**Date:** 2026-06-02 · Companion to `BUILD_INTEGRATE_IGNORE_MASTER_REGISTER.md`
**Mode:** READ-ONLY · zero code · zero design
**Purpose:** Enumerate every capability, feature, or recommendation that ForgedOps should NOT build, integrate, or maintain — because doing so would violate the Constitution, duplicate mature systems, or add complexity without operational value.

---

## §1 · Hard IGNORE list (eliminate or never start)

### From Operational Reality Gap Register

| # | Item | Why IGNORE |
|---|---|---|
| 1 | **iter445 `NewDailyReport.jsx` "Has crew reviewed JHP today?" Yes/No field** (G0-12 / FAIL-1) | Self-attestation · no operational consumer · Rule 1 + Rule 11 violation. Eliminate via separate code change. |
| 2 | **Vestigial `db.jhas` form system** including `stop_work_acknowledged` boolean (FAIL-2) | Operator confirmed unused · 1 row likely test data · Rule 1 + Rule 9 violation. Decommission via separate code change. |
| 3 | **OC-005 JHP Acknowledgement Ledger as currently scoped** (P0 CV-1) | Rule 11 textbook violation per Amendment 001 worked example. Re-scope per REPLACE-1 (Toolbox Talk + Tier 3 download identity) OR eliminate. |
| 4 | **OC-019 status casing normalization** (G3-4) | Pure cosmetic · no operational consequence · low-value · do not invest. |

### From Constitutional Conflict Register

| # | Item | Why IGNORE |
|---|---|---|
| 5 | **F-18 row 18 "Acknowledge that I read the JHP"** as gap-closure goal | Closing this 🔴 with an ack click violates Rule 1 + Rule 11. Mark row 18 as Constitutionally exempt. |
| 6 | **Top-10 Improvement #3 "OC-005 JHP Ack Ledger build authorization"** | Inherits CV-1 defect. Remove from Top-10 list. |
| 7 | **Pattern D BilingualConsent + SignaturePad reuse on JHP** | Pattern reuse does not justify Constitutional violation. |

### From Operational Reality Constitutional Violation Register (forward-looking)

| # | Pattern | Why IGNORE |
|---|---|---|
| 8 | "Acknowledge Receipt" steps in Submittal / RFI / Pay-App workflows | V-1, V-2, V-4 — Rule 11 violations |
| 9 | "Acknowledged" intermediate status in RFI lifecycle | V-2 — Rule 1 + Rule 11 |
| 10 | Multi-step approval ack chains in CO workflow | V-3 — Rule 1 + Rule 8 |
| 11 | "Read and Acknowledged" on meeting minutes | V-5 — Rule 11 |
| 12 | "I am at the correct jobsite" clock-in attestation | V-6 — Rule 11 (GPS already provides Tier 1) |
| 13 | "I acknowledge this performance review" employee click | V-8 — Rule 11 |
| 14 | "Driver acknowledges DOT policy" annual click | V-10 — Rule 11 |
| 15 | "Mechanic acknowledges assignment" before work order | V-11 — Rule 7 violation (assignment is auto) |
| 16 | "Subcontractor acknowledges scope of work" | V-12 — Rule 11 (contract execution is sufficient) |
| 17 | "Executive acknowledges weekly KPIs" | V-13 — Rule 1 + Rule 2 + anti-checklist |
| 18 | "Employee acknowledges handbook update" | V-14 — Rule 11 + Amendment 001 worked example |

---

## §2 · Mature-system replacement IGNORE list (do not build internally)

### HRIS-side functions (HRIS owns)

| # | Function | Why ForgedOps must not build |
|---|---|---|
| 19 | Performance review software | HRIS owns (BambooHR/Paychex) · ForgedOps is not HRIS |
| 20 | Benefits administration | HRIS / benefits broker owns · ACA-regulated |
| 21 | ATS / recruiting pipeline | ATS owns · candidate-experience considerations |
| 22 | Compensation history management | HRIS owns |
| 23 | I-9 / E-Verify processing | E-Verify portal + HRIS |

### Accounting-side functions (Accounting/ERP owns)

| # | Function | Why ForgedOps must not build |
|---|---|---|
| 24 | General ledger | Accounting · regulated · audit-source-of-truth |
| 25 | AP processing | Accounting |
| 26 | AR / invoicing | Accounting |
| 27 | Bank reconciliation | Accounting |
| 28 | Sales tax handling | Accounting · tax-regulated |
| 29 | Bonding / surety capacity tracking | Accounting + surety broker |
| 30 | Job cost computation engine | Accounting (ForgedOps consumes) |

### Fleet/Safety vendor-owned functions

| # | Function | Why ForgedOps must not build |
|---|---|---|
| 31 | ELD / hours-of-service compliance | Motive/Samsara/Geotab — hardware required · DOT-regulated |
| 32 | IFTA quarterly tax computation | ELD-bundled |
| 33 | Drug-test chain-of-custody | DISA/Concentra — HIPAA-bounded |
| 34 | Workers comp claim portal | Carrier-specific · litigation-sensitive |
| 35 | MSDS / SDS library | Velocity/KHA/3E subscription |

### Sales/Marketing functions

| # | Function | Why ForgedOps must not build |
|---|---|---|
| 36 | CRM / customer pipeline | Salesforce/HubSpot owns |
| 37 | Estimating / bid software | HCSS Estimator/B2W Estimate/Heavy-Bid |
| 38 | Marketing automation | Out of mission |

### Maintenance/Equipment vendor-owned

| # | Function | Why ForgedOps must not build |
|---|---|---|
| 39 | Maintenance work-order system | MaintainX/Fiix · operator explicitly named MaintainX |
| 40 | Fuel-card transactions | WEX/Comdata/Voyager fuel providers |

---

## §3 · Anti-pattern IGNORE list (architectural / UX)

| # | Anti-pattern | Why IGNORE |
|---|---|---|
| 41 | Read-only "Ownership Dashboard" | Anti-checklist clause violation · use Action Console instead |
| 42 | Read-only Operations Center surfaces | Same |
| 43 | "I have reviewed" board-packet acknowledgement | Rule 11 |
| 44 | Multi-recipient PENDING_REVIEW fan-out (current iter452 behavior) | Rule 8 violation — refactor, do not extend |
| 45 | Manual-assign dropdown UI on lifecycle records (Layer A risk) | Rule 6 + Rule 7 violation — assignment must derive |
| 46 | Status-pill-only closure for any workflow | Rule 1 + Rule 4 — closure requires operational action |
| 47 | "Acknowledge Tier 1 work" patterns | Amendment 001 — work IS the evidence |
| 48 | Department-wide notification broadcasts | Rule 8 — single-recipient discipline |

---

## §4 · Aggregate IGNORE tally

| Category | Count |
|---|---:|
| Acknowledgement-as-work patterns (Amendment 001 violations) | 18 |
| Mature-system replacements (Build/Integrate/Ignore Doctrine violations) | 22 |
| Anti-pattern architectural/UX | 8 |
| **TOTAL** | **48** |

---

## §5 · Constitutional posture on the IGNORE list

The IGNORE list is the operational fence around ForgedOps's mission. Items on this list are not "low priority" — they are **out-of-mission**. Treating them as backlog items risks scope drift over time as customers/competitors/employees demand "could we add X." The Constitution + Build/Integrate/Ignore Doctrine + Amendment 001 together provide the operator with explicit authority to decline these items without justification beyond doctrine reference.

> **The platform's strength is what it does NOT do.**

---

## §6 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero solutions designed | ✅ |
| 48 IGNORE items catalogued across 3 categories | ✅ |
| Every item has explicit doctrine citation | ✅ |
| Mission-fence posture stated clearly | ✅ |

🛑 **STOPPED.**
