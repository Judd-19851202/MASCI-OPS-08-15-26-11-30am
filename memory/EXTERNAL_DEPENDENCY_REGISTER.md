# OMEGA · EXTERNAL DEPENDENCY REGISTER

**Date:** 2026-06-02 · Companion to `OPERATIONAL_REALITY_AUDIT.md`
**Mode:** READ-ONLY · zero code · zero design · zero estimates
**Definition:** Capabilities that ForgedOps does not provide today and would be unwise to provide (because the function is fulfilled by mature, regulated, or domain-specific third-party systems). The operator-decision is integration scope, not whether to build internally.

---

## §0 · Why "external" is the correct classification for these items

The Constitution favors **operational practicality** (Rule 9) over feature breadth. A construction-operations platform that attempts to be its own accounting system, ELD vendor, and benefits administrator competes with mature systems that customers already license. The Constitutionally correct posture for these items is:

* Do **not** build internally
* Do **integrate** to the extent operationally necessary
* Do **consume** their evidence streams (as Tier 1 work-performed data feeding executive surfaces)

---

## §1 · External dependency register · 11 items

### EX-1 · Accounting / ERP

* **Function:** GL · AP · AR · job cost · WIP · invoicing · bank rec · 1099 · sales tax · bonding posture
* **Common vendors:** QuickBooks Online · Sage 300 Construction · Foundation · Vista by Viewpoint · Spectrum
* **Why external:** Regulated financial system · auditor's primary trust source · construction-specific (job cost) variants are domain-mature
* **Operator decision:** Which platform; integration depth (read-only consumption · two-way sync · full-write)
* **ForgedOps responsibility:** Consume job-cost data for executive WIP / forecast-to-complete · push PO commits + receipts + change orders + pay-app data INTO accounting
* **Areas affected:** Executive · PM · Operations · HR (payroll) · Financial

### EX-2 · Payroll processing

* **Function:** Pay-run · taxes · garnishments · direct deposit · W-2 / 1099 generation · benefits deduction
* **Common vendors:** ADP · Paychex · Foundation Payroll · Sage HRMS · Paycom
* **Why external:** Heavily regulated · tax-compliance burden enormous · domain-mature
* **Operator decision:** Which processor; integration with Time Verification + Payroll Variance
* **ForgedOps responsibility:** Push variance-adjusted hours TO payroll · consume payroll-processed records FOR variance reconciliation
* **Areas affected:** HR · Financial

### EX-3 · Project scheduling

* **Function:** CPM scheduling · resource leveling · what-if analysis · S-curve · pull-planning
* **Common vendors:** Primavera P6 · MS Project · Smartsheet · Touchplan (Lean) · Procore Schedule
* **Why external:** Scheduling is a deeply specialized discipline · planners are domain experts · CPM math is mature
* **Operator decision:** Integration depth (read schedule INTO ForgedOps for Daily Report context · or build look-ahead view as a consumer)
* **ForgedOps responsibility:** Consume current schedule per project for DR / look-ahead views · push field production data BACK to scheduler for actuals
* **Areas affected:** Operations · PM · Field · Executive

### EX-4 · ELD / Telematics

* **Function:** Driver hours-of-service · vehicle GPS · idle time · fuel use · DVIR (some)
* **Common vendors:** Samsara · Geotab · KeepTruckin (Motive) · Verizon Connect
* **Why external:** DOT-regulated · device hardware required · domain-mature
* **Operator decision:** Which ELD; what data ingest INTO ForgedOps (hours, location, defects)
* **ForgedOps responsibility:** Consume ELD events for Driver Qualification File + DOT Compliance Dashboard (B-23 / B-24) · cross-reference with field DVIR · supplement Fleet Defects
* **Areas affected:** Fleet · Safety · HR

### EX-5 · IFTA reporting

* **Function:** Quarterly fuel tax reconciliation across jurisdictions
* **Common vendors:** ELD-bundled (Samsara · Geotab) · standalone (IFTA Plus · KeepTruckin)
* **Why external:** Quarterly tax filing · regulated · low recurrence
* **Operator decision:** Most ELDs include · ForgedOps does not need its own IFTA module
* **ForgedOps responsibility:** None beyond ensuring vehicle/driver assignment data is available
* **Areas affected:** Fleet · Financial

### EX-6 · Drug-test pool management

* **Function:** Random-pool selection · vendor scheduling · result tracking · DOT-compliant chain-of-custody
* **Common vendors:** US HealthWorks · Concentra · DISA Global · CCS
* **Why external:** HIPAA + DOT regulated · chain-of-custody legal posture
* **Operator decision:** Vendor + integration to track results
* **ForgedOps responsibility:** Consume result events to drop into Driver Qualification File (B-23) and HR compliance · never store raw test artifacts
* **Areas affected:** Safety · Fleet · HR

### EX-7 · Workers comp / general liability carrier

* **Function:** Claim filing · adjuster coordination · settlement · medical-only vs lost-time tracking · NCCI claim feed
* **Common vendors:** Travelers · Liberty Mutual · Zurich · The Hartford · CNA · Old Republic
* **Why external:** Carrier-specific · regulated · litigation-sensitive
* **Operator decision:** Integration depth (often manual claim filing; structured claim-tracking on ForgedOps side OK)
* **ForgedOps responsibility:** Link incidents to claims · track claim status as Tier 1 evidence · NOT replace the carrier's claim system
* **Areas affected:** Safety · HR · Financial

### EX-8 · OSHA reporting portal

* **Function:** Annual 300A submission · severe-injury reporting · ITA (Injury Tracking Application)
* **Common vendors:** OSHA government portal (no commercial alternative)
* **Why external:** Government system; mandatory submission
* **Operator decision:** ForgedOps generates the artifact (B-15) · OSHA portal receives submission
* **ForgedOps responsibility:** OSHA 300 / 301 / 300A artifact generator (B-15 is greenfield; portal is external)
* **Areas affected:** Safety · Executive

### EX-9 · Benefits administration

* **Function:** Enrollment · life event · ACA reporting · COBRA · 401(k) · HSA · FSA
* **Common vendors:** ADP Total Source · Paychex Flex · Gusto · Zenefits · BenefitMall
* **Why external:** Regulated · ACA-burden · benefits-broker mediated
* **Operator decision:** Which benefits admin; what employee-status data ForgedOps exposes
* **ForgedOps responsibility:** Maintain employee directory as source of truth for status changes (active/terminated) feeding benefits admin · NOT replace enrollment
* **Areas affected:** HR

### EX-10 · ATS / recruiting

* **Function:** Posting · candidate pipeline · interview scheduling · offer letters · background check coordination
* **Common vendors:** Greenhouse · Lever · iCIMS · ApplicantPro · BambooHR (lite)
* **Why external:** Discipline-mature · candidate-experience considerations
* **Operator decision:** ATS choice; trigger Onboarding (B-? · OC-013) on hire event
* **ForgedOps responsibility:** Consume hire events → seed employee record + trigger onboarding workflow
* **Areas affected:** HR

### EX-11 · MSDS / SDS library

* **Function:** Safety Data Sheets per chemical · OSHA HazCom 2012 compliance
* **Common vendors:** Velocity EHS (formerly MSDS Online) · KHA · 3E (Verisk)
* **Why external:** Library size + supplier-specific updates make in-house maintenance impractical
* **Operator decision:** Subscription + integration depth (link library access from JHP / Daily Report contexts)
* **ForgedOps responsibility:** Link contextually · do not host SDS data internally
* **Areas affected:** Safety

---

## §2 · Cross-cutting integration observations

### 2.1 · One external dependency dominates: accounting

EX-1 (accounting) accounts for 6 of 9 EXTERNAL gaps in the Gap Register and is the single most consequential integration decision MASCI faces. Without it, executive WIP / forecast-to-complete / PM job-cost projections / pay-app workflow / lien-waiver financial coupling are all blocked. **Operator should rank accounting integration ahead of any new ForgedOps internal workflow build.**

### 2.2 · Three regulatory dependencies are non-negotiable

EX-4 (ELD), EX-6 (drug-test), and EX-8 (OSHA portal) are regulatory and cannot be replaced. ForgedOps's posture is "consume and produce regulatory artifacts," never replace the regulatory system.

### 2.3 · Three HR dependencies are domain-specific

EX-2 (payroll), EX-9 (benefits), EX-10 (ATS) are HR-discipline-mature systems. Building any of them inside ForgedOps would be Constitutional Rule 9 violation (Operator First) — operations would lose to feature-breadth.

### 2.4 · Two safety-domain dependencies are subscription products

EX-7 (workers comp carrier) and EX-11 (SDS library) are subscription products that customers already license. ForgedOps consumes their data streams.

---

## §3 · Constitutional posture on integrations

Every integration must satisfy:

1. **Rule 7 (Accountability Must Be Automatic):** Data flows from external → ForgedOps without manual re-entry where possible.
2. **Rule 8 (Reduce Operational Noise):** Failures route to one designated operator, not a department broadcast.
3. **Amendment 001 Rule 11:** Integration events (e.g., "PO sent to accounting · invoice received · pay-app approved") are Tier 1 work-performed evidence, NOT ack workflows.
4. **Anti-checklist clause:** Integration status pages must be Action Consoles (resolve · retry · reassign), not read-only health dashboards.

---

## §4 · What this register does NOT do

| Constraint | Status |
|---|---|
| Does not recommend a specific vendor | ✅ |
| Does not estimate integration effort | ✅ |
| Does not design integration architecture | ✅ |
| Does not authorize any integration build | ✅ |
| Does not modify existing audit findings | ✅ |

Vendor selection and integration scoping are operator-decision territory. This register identifies the external boundary; operator selects vendors and integration depth.

---

## §5 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero solutions designed | ✅ |
| 11 external dependencies catalogued with vendors + rationale | ✅ |
| Accounting identified as the single dominant integration | ✅ |
| Constitutional posture stated per integration class | ✅ |

🛑 **STOPPED.**
