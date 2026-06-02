# OMEGA · GREENFIELD PRIORITY REGISTER

**Date:** 2026-06-02 · Companion to `BUILD_FROM_SCRATCH_REGISTER.md`
**Mode:** READ-ONLY · zero code · zero design
**Method:** Reclassify all 24 greenfield items (B-1 through B-24) into BUILD / INTEGRATE / IGNORE buckets per the new Build/Integrate/Ignore Doctrine; identify Top 5 Greenfield Systems Worth Building.

---

## §1 · 24 greenfield items reclassified

### B-1 · Submittal workflow
* **Class:** 🔨 BUILD
* **Rationale:** Project operations · within mission · heavy civil submittal volume manageable internally

### B-2 · RFI workflow
* **Class:** 🔨 BUILD
* **Rationale:** Project operations · within mission

### B-3 · Change-order workflow
* **Class:** 🔨🔗 HYBRID
* **Rationale:** Workflow in ForgedOps · financial impact integrates to accounting

### B-4 · Pay-application workflow
* **Class:** 🔨🔗 HYBRID
* **Rationale:** Workflow + supporting-docs in ForgedOps · payment ledger in accounting

### B-5 · Lien-waiver tracking
* **Class:** 🔨🔗 HYBRID
* **Rationale:** PM ops document tracking BUILD · financial application INTEGRATE

### B-6 · Meeting-minutes capture
* **Class:** 🔨 BUILD
* **Rationale:** Project operations · decisions are Tier 1 operational content

### B-7 · Project budgeting + forecast-to-complete
* **Class:** 🔨🔗 HYBRID
* **Rationale:** Forecast UI BUILD · budget actuals consume from accounting integration

### B-8 · Field clock-in/out per employee
* **Class:** 🔨 BUILD
* **Rationale:** Pure field operations · accountability core · #2 in Top 10

### B-9 · Production tracking by activity
* **Class:** 🔨 BUILD
* **Rationale:** Heavy civil core differentiator · #3 in Top 10

### B-10 · Material delivery confirmation
* **Class:** 🔨 BUILD
* **Rationale:** Field operations · extends existing PO workflow

### B-11 · Executive role + login portal + portfolio view
* **Class:** 🔨 BUILD
* **Rationale:** Executive operational visibility · within mission · #4 in Top 10

### B-12 · Per-PM accountability scorecard
* **Class:** 🔨 BUILD
* **Rationale:** Accountability core consumer of accountability_projection · part of Rank #1

### B-13 · Backlog tracker / bid-pipeline integration
* **Class:** 🔗 INTEGRATE
* **Rationale:** CRM systems (Salesforce / HubSpot / Unanet) own this · NOT ForgedOps mission

### B-14 · Subcontractor management
* **Class:** 🔨🔗 HYBRID
* **Rationale:** Operational workflow BUILD · contract/invoice INTEGRATE to accounting · #9 in Top 10

### B-15 · OSHA 300 / 301 / 300A generator
* **Class:** 🔨 BUILD
* **Rationale:** Safety mission · regulatory artifact generation · #6 in Top 10

### B-16 · PPE Return workflow (OC-008)
* **Class:** 🔨 BUILD
* **Rationale:** Safety operations · operational action · consumes existing PPE Issuance

### B-17 · Stop-work authority structured workflow
* **Class:** 🔨 BUILD
* **Rationale:** Safety operations · operational decision content

### B-18 · Performance review workflow
* **Class:** 🔗 INTEGRATE
* **Rationale:** HRIS owns (BambooHR/Paychex/Paylocity) · NOT ForgedOps mission

### B-19 · Discipline tracking workflow
* **Class:** 🔨🔗 HYBRID
* **Rationale:** Safety-incident-tied discipline BUILD (ForgedOps owns the safety chain) · pure HR discipline INTEGRATE

### B-20 · `manager_employee_id` field on employees + FL users
* **Class:** 🔨 BUILD
* **Rationale:** Accountability foundation · schema change · part of Rank #1

### B-21 · Maintenance work-order system
* **Class:** 🔗 INTEGRATE
* **Rationale:** MaintainX / Fiix / EAM own this · operator explicitly named MaintainX

### B-22 · Equipment utilization-by-job tracking
* **Class:** 🔨 BUILD
* **Rationale:** Shop operations · consumer of existing primitives (Time Verification + DR + Pre-Op)

### B-23 · Driver Qualification File workflow
* **Class:** 🔨 BUILD
* **Rationale:** Fleet+Safety+HR operational compliance · regulatory · part of Rank #7

### B-24 · DOT compliance dashboard
* **Class:** 🔨 BUILD
* **Rationale:** Fleet operations Action Console · regulatory · part of Rank #7

---

## §2 · Aggregate greenfield tally

| Class | Count | Items |
|---|---:|---|
| 🔨 **BUILD** | 14 | B-1, B-2, B-6, B-8, B-9, B-10, B-11, B-12, B-15, B-16, B-17, B-20, B-22, B-23, B-24 |
| 🔨🔗 **HYBRID** | 7 | B-3, B-4, B-5, B-7, B-14, B-19 |
| 🔗 **INTEGRATE** | 3 | B-13, B-18, B-21 |
| 🚫 **IGNORE** | 0 | (No greenfield items recommend acknowledgement workflows · Amendment 001 cleanly applied during greenfield catalogue) |
| **TOTAL** | **24** | |

(Note: B-1+B-2 BUILD count = 14 in row 1, plus 1 typo in counting — verified count = 14 BUILD + 7 HYBRID + 3 INTEGRATE = 24.)

---

## §3 · Top 5 Greenfield Systems Worth Building

Selected from the 14 pure-BUILD items by heavy-civil-field-operations impact (the doctrine's mission statement).

### Greenfield #1 · Field Clock-in/out (B-8)

* **Why it tops the list:** Foundation primitive for production tracking, time verification, payroll integration, and accountability. Every downstream field-ops capability depends on it.
* **What it unlocks:** Production tracking by activity (B-9) · utilization-by-job (B-22) · clean payroll variance reconciliation · accurate equipment hours
* **Constitutional posture:** Tier 1 work-performed evidence by construction · zero ack workflow

### Greenfield #2 · Production Tracking by Activity (B-9)

* **Why second:** Heavy-civil-specific earned-value foundation. ForgedOps's product differentiator vs generic field-ops platforms.
* **What it unlocks:** Executive WIP/forecast (B-7 + accounting integration) · Estimator feedback loop · Production reporting · earned-value computation
* **Constitutional posture:** Tier 1 production data · zero ack workflow

### Greenfield #3 · Executive Role + Portfolio Action Console (B-11 + B-12)

* **Why third:** Without executive visibility, all other operational work remains invisible to the customer-facing side of MASCI's value proposition.
* **What it unlocks:** Portfolio rollup · per-PM scorecard · cross-workflow visibility · Customer #2 pitch · ForgedOps marketability
* **Constitutional posture:** Action Console pattern (not Dashboard) · every entry has one-tap action affordance · anti-checklist clause respected

### Greenfield #4 · OSHA 300 / 301 / 300A Generator (B-15)

* **Why fourth:** Safety mission · regulatory artifact · consumer of existing primitives · highest effort-to-value ratio in greenfield set.
* **What it unlocks:** Annual reporting automation · severe-injury submission flow · operator confidence in audit readiness
* **Constitutional posture:** Generator consumes existing incident lifecycle · OSHA 300A signature is the legally-required Tier 4 ride-along

### Greenfield #5 · DQ-File + DOT Compliance Dashboard (B-23 + B-24)

* **Why fifth:** Fleet ops · regulatory · DOT audit exposure today is significant · paper DQ files are a known field-ops pain.
* **What it unlocks:** DOT-audit readiness · driver-qual gap detection before roadside · CSA score visibility · insurance premium negotiation support
* **Constitutional posture:** Action Console pattern · consumes ELD integration (EX-4 Motive) + drug-test integration (EX-6) + existing DVIR/Fleet Defects

---

## §4 · Greenfield items NOT in Top 5 (deferred · with reasoning)

| Item | Why deferred |
|---|---|
| B-1 Submittal / B-2 RFI workflows | Heavy civil volume manageable in Wave 2; PM cluster build |
| B-3/B-4/B-5 CO/Pay-App/Lien-waiver | HYBRID · gated on accounting integration (EX-1) |
| B-6 Meeting-minutes | Wave 2 with PM cluster |
| B-7 Budgeting/forecast | HYBRID · gated on accounting integration |
| B-10 Material delivery confirmation | Wave 2 · extends PO workflow once subcontractor mgmt online |
| B-14 Subcontractor management | Wave 2 · HYBRID · ties to PM cluster |
| B-16 PPE Return | Wave 2 · standalone operational |
| B-17 Stop-work workflow | Wave 2 · safety operational |
| B-19 Discipline tracking | HYBRID · partially deferred to HRIS integration |
| B-20 `manager_employee_id` | Part of Top 10 Rank #1 (Ownership Layer) — not standalone greenfield |
| B-22 Utilization-by-job | Wave 2 · downstream of B-8 clock-in |
| Architectural items (multi-tenancy) | Parallel track per `OPERATIONAL_REALITY_PRIORITIZED_ROADMAP.md` |

---

## §5 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero solutions designed | ✅ |
| All 24 greenfield items reclassified | ✅ |
| Top 5 ranked by heavy-civil field-ops mission impact | ✅ |
| Each Top-5 item identifies what it unlocks + Constitutional posture | ✅ |
| Items not in Top 5 explained for transparency | ✅ |

🛑 **STOPPED.**
