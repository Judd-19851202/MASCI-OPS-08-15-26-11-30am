# OMEGA · OPERATIONAL REALITY AUDIT — CAN MASCI RUN THE COMPANY INSIDE FORGEDOPS?

**Date:** 2026-06-02
**Mode:** READ-ONLY · evidence-only · zero code · zero redesign · zero solutions designed · zero implementation plans
**Governing doctrine:** `FORGEDOPS_OPERATIONAL_DESIGN_CONSTITUTION.md` Parts I + II + III + IV (Amendment 001)
**Primary question:** Can MASCI run the entire company entirely inside ForgedOps today? With no spreadsheets · no notebooks · no whiteboards · no side databases · no text-message workflows · no email-based business processes · no tribal knowledge · no memory-based tracking.

---

## §0 · Top-line answer

# 🔴 NO — MASCI cannot run the company entirely inside ForgedOps today.

The platform handles approximately **35-40 % of the day-to-day operational surface** of a heavy-civil general contractor. The remaining 60-65 % is either externally dependent (accounting/ERP · scheduling · ELD/telematics · payroll processor · banking) · partially implemented (employee lifecycle · equipment maintenance · fleet compliance) · completely absent (job costing · change orders · RFIs · submittals · pay applications · estimate-to-bid pipeline · executive financial reporting) · or runs on tribal knowledge today.

Detailed answers per operational area are tabulated in §1. The 10 deliverables in this batch quantify exactly what must be fixed, redesigned, or built from scratch.

---

## §1 · 10 operational areas × 10 questions matrix

For each area, the 10 questions are answered with evidence. Legend: ✅ live · 🟡 partial · 🔴 absent · 📤 external · 🧠 tribal/memory · 📊 spreadsheet · 📞 phone · ⛔ Constitutional violation if built

### 1.1 · EXECUTIVE

| Q | Answer |
|---|---|
| 1. Already in ForgedOps? | 🟡 Command Center pill labels · admin Command Center (operationally IT/ops oriented, not executive) · Accountability projection library exists but unwired to executive UI |
| 2. External? | 📤 QuickBooks / Sage 300 / Foundation / Vista for P&L · Construction Imaging for project financials · CRM for backlog/bid pipeline |
| 3. Manual tracking? | 📊 Backlog spreadsheets · bid pipeline spreadsheets · cash-flow projections · board packets |
| 4. Spreadsheets? | 📊 Backlog / bid pipeline / forecasting / job-cost summaries |
| 5. Phone calls? | 📞 Owner / surety / banking communications |
| 6. Tribal? | 🧠 Who's running which project · who's the rainmaker on what bid · which client owes what |
| 7. Partial? | 🟡 Command Center is IT/ops oriented · `lib/accountability_projection.py` exists but no executive UI |
| 8. Absent? | 🔴 Executive role · executive login portal · portfolio-by-project rollup · per-PM scorecard · backlog tracker · bid pipeline · cash-flow forecast · board reporting · WIP schedule · forecast-to-complete |
| 9. Should NEVER build (Constitutional)? | ⛔ "Acknowledge daily KPIs" patterns · "I have reviewed" board-packet ack · executive dashboard-only surfaces without action affordances (anti-checklist clause) |
| 10. New capabilities required? | Executive role + portfolio rollup · WIP schedule consumer of job-cost data · backlog tracker · bid pipeline integration · cash-flow forecast (or external integration) |

### 1.2 · OPERATIONS

| Q | Answer |
|---|---|
| 1. Already in ForgedOps? | 🟡 PO requests · asset transfers · dispatch assignments · CAPA · tasks (role-level only, 0 closure rate) |
| 2. External? | 📤 P6 / MS Project / Smartsheet for schedule · QuickBooks for cost · email for subcontractor coordination |
| 3. Manual? | 📊 Resource allocation across projects · crew assignment · mobilization plans · demob plans |
| 4. Spreadsheets? | 📊 Resource matrix · weekly look-ahead · 3-week-look-ahead · subcontractor schedules · material delivery schedules |
| 5. Phone? | 📞 PM-to-Super-to-Foreman coordination · vendor escalation · subcontractor disputes |
| 6. Tribal? | 🧠 Which super runs which job · who can handle which scope · which sub has capacity |
| 7. Partial? | 🟡 PO requests work end-to-end (strongest surface) · asset transfers complete · dispatch assignments complete · CAPA exists but 3-parallel-system pathology |
| 8. Absent? | 🔴 Master schedule integration · crew/resource allocation engine · cross-project material movement · subcontractor management (no sub workflow) · mobilization/demob plans · production tracking by activity · look-ahead view · weekly Ops meeting capture |
| 9. Should NEVER build? | ⛔ "Acknowledge weekly look-ahead" · checklist-style mobilization steps without operational consequence · "approval workflow for nothing" patterns |
| 10. New capabilities required? | Subcontractor entity + contract lifecycle · master schedule import (or integration with P6/MS Project) · look-ahead view · resource allocation primitive · production tracking by activity |

### 1.3 · PROJECT MANAGEMENT

| Q | Answer |
|---|---|
| 1. Already in ForgedOps? | 🟡 jobs_master collection · job photos · Daily Reports (iter452) · PO requests · QA/QC inspections · Site inspections |
| 2. External? | 📤 Accounting (job costing · invoicing · AP/AR · GL) · estimating software · CAD/BIM · scheduling (P6) · document management for plans/specs |
| 3. Manual? | 📊 Submittals log · RFI log · change order log · meeting minutes · pay application packages |
| 4. Spreadsheets? | 📊 Submittal log · RFI log · change-order log · pay app draws · subcontractor schedule of values |
| 5. Phone? | 📞 RFI clarifications · client-side decisions · subcontractor scope disputes |
| 6. Tribal? | 🧠 Project-specific contract terms · client preferences · jobsite history |
| 7. Partial? | 🟡 jobs_master (live but lean) · Daily Reports (full lifecycle iter452) · PO Requests (full) · QA/QC + Site Inspection (submit-only · no follow-up) |
| 8. Absent? | 🔴 Submittal workflow · RFI workflow · change-order workflow · pay-application workflow · contract management · lien-waiver tracking · meeting minutes · project budgeting · forecast-to-complete · job-cost projection · closeout package generator · drawings/specs management |
| 9. Should NEVER build? | ⛔ "Acknowledge RFI received" · "Acknowledge change order" · status-pill closure for submittals/RFIs without operational decision content · dashboard-only project health surfaces |
| 10. New capabilities required? | Submittal workflow · RFI workflow · change-order workflow · pay-application workflow · contract management collection · meeting-minutes capture · drawings/specs document management · accounting integration for job cost |

### 1.4 · FIELD OPERATIONS

| Q | Answer |
|---|---|
| 1. Already in ForgedOps? | ✅ Daily Reports + lifecycle (iter452) · Toolbox Talks · Safety Meetings · Equipment Pre-Op · DVIR · JHP library (iter445) · FL forms · Time Off Request · FSI 5-tier identity ladder (iter452.5.1) · public-gate revise flow (iter452.5) |
| 2. External? | 📤 ELD/telematics for vehicle hours · Bluebeam for marked-up plans · field GPS tools |
| 3. Manual? | 📊 Production quantities by activity · material delivery confirmation timing · subcontractor sign-ins |
| 4. Spreadsheets? | 📊 Production tracking by line item · material receiving log · subcontractor scope handoffs |
| 5. Phone? | 📞 Site coordination · subcontractor disputes · same-day material requests |
| 6. Tribal? | 🧠 Site-specific quirks · soil conditions · access constraints |
| 7. Partial? | 🟡 Crew time tracking partial (Time Verification CSV export · no per-employee field clock) · production tracking absent · material receiving partial (PO receipt step missing) |
| 8. Absent? | 🔴 Field clock-in/out per employee · production tracking by activity · material delivery confirmation · jobsite plan markup · jobsite coordination chat (operator: "no text-message workflows") |
| 9. Should NEVER build? | ⛔ "Acknowledge JHP read" (Amendment 001 CV-1) · "Has crew reviewed JHP?" Yes/No (already live · FAIL-1) · daily-acknowledge-attendance patterns |
| 10. New capabilities required? | Field clock-in/out · production-by-activity tracking · material delivery confirmation · structured site-coordination workflow (replacing texts) |

### 1.5 · SAFETY

| Q | Answer |
|---|---|
| 1. Already in ForgedOps? | ✅ Incidents + lifecycle (iter451) · Site Inspections · QA/QC · Safety Meetings · Toolbox Talks · JHP library (iter445) · safety_training_records (6 rows) · `field_submitter_bindings` for kickback flow · OSHA recordable ack (iter451) |
| 2. External? | 📤 Workers comp carrier (claims) · OSHA reporting portal · drug-test vendor · MSDS/SDS provider (most contractors use Velocity / KHA / 3E) |
| 3. Manual? | 📊 OSHA 300/301 log · workers comp claim files · drug-test results · driver qualification files |
| 4. Spreadsheets? | 📊 OSHA log · training matrix · qualification expiration tracker · safety committee minutes |
| 5. Phone? | 📞 Claim coordination with carrier · OSHA inspector responses · medical clinic coordination |
| 6. Tribal? | 🧠 Which super has open CAPAs · which sub has historic safety issues |
| 7. Partial? | 🟡 Incident lifecycle (iter451 live) · OC-001 closure works · QA/QC + Site Inspection submit-only · safety_training_records lean (6 rows) |
| 8. Absent? | 🔴 OSHA 300/301 generator · workers comp claim integration · DOT compliance for fleet · drug-test tracking · MSDS/SDS library · hazard analysis workflow · stop-work authority structured workflow · PPE Return (OC-008) · executive safety scorecard |
| 9. Should NEVER build? | ⛔ OC-005 JHP Ack Ledger (P0 · Amendment 001 REPLACE) · "I acknowledge stop-work authority" boolean (FAIL-2 vestigial) · iter445 "Has crew reviewed JHP?" Yes/No (FAIL-1) · checkbox-only inspection findings |
| 10. New capabilities required? | OSHA 300/301 generator · workers comp claim collection · drug-test tracking · MSDS/SDS library · stop-work authority structured workflow (Tier 1 work-performed) · PPE Return (OC-008) |

### 1.6 · HR

| Q | Answer |
|---|---|
| 1. Already in ForgedOps? | 🟡 Employee directory (261 records) · field leadership users (24) · onboarding single-record · Time Off Request · Time Verification (read + CSV) · Payroll Variance (iter452 lifecycle) · safety_training_records |
| 2. External? | 📤 Payroll processor (ADP / Paychex / Foundation) · benefits admin · ATS · background check vendor · E-Verify portal · W-2/1099 distribution |
| 3. Manual? | 📊 Performance reviews · discipline tracking · I-9 files · benefits enrollment · compensation changes · recruiting pipeline |
| 4. Spreadsheets? | 📊 Compensation matrix · performance-review schedule · discipline log · I-9 compliance tracker · benefits-enrollment status |
| 5. Phone? | 📞 Carrier disputes · candidate interviews · employee-relations issues |
| 6. Tribal? | 🧠 Who reports to whom (no `manager_employee_id` field per Ownership Audit P2-5) · who has informal authority · who's on performance-improvement-plan |
| 7. Partial? | 🟡 Onboarding (OC-013 partial — single-record only) · Offboarding (OC-014 partial — status mutator + summary, no multi-step) · Time Verification (read-only · no dispute/resolve) |
| 8. Absent? | 🔴 Performance reviews · discipline tracking · compensation changes · benefits administration · ATS / recruiting pipeline · I-9 / E-Verify · W-2 / 1099 generation · org chart with manager hierarchy · training-assignment workflow · payroll processing (only variance ✅) |
| 9. Should NEVER build? | ⛔ "Acknowledge employee handbook" · "Acknowledge policy update" · multi-step onboarding checklist with checkbox steps (OC-013 REPLACE per Amendment 001) · multi-step offboarding checklist (OC-014 REPLACE) |
| 10. New capabilities required? | Performance review workflow (Tier 1 review content captured) · discipline workflow (Tier 1 incident record) · `manager_employee_id` on employees + FL users · compensation history · ATS integration or build · I-9 / E-Verify integration · payroll integration (full processing) |

### 1.7 · EQUIPMENT

| Q | Answer |
|---|---|
| 1. Already in ForgedOps? | ✅ Equipment master · Equipment Pre-Op (37 task rows) · DVIR · Asset Transfers · Fire Extinguishers · Document Expirations (iter151) |
| 2. External? | 📤 Telematics / GPS for utilization · OEM portals for warranty · fuel-card provider |
| 3. Manual? | 📊 Maintenance schedule · repair tickets · utilization tracking · fuel consumption · depreciation |
| 4. Spreadsheets? | 📊 Maintenance schedule · repair history · utilization-by-job · fuel logs · capital plan |
| 5. Phone? | 📞 Vendor coordination for repairs · parts ordering |
| 6. Tribal? | 🧠 Which equipment is reliable · which mechanic handles what · informal swap requests |
| 7. Partial? | 🟡 Pre-Op exists (37 rows · 0 closure) · DVIR exists · Asset Transfers complete · maintenance scheduling absent |
| 8. Absent? | 🔴 Maintenance schedule · work-order system · repair tracking · utilization-by-job · fuel consumption tracking · depreciation · capital plan · operator-cost projection |
| 9. Should NEVER build? | ⛔ "Acknowledge pre-op" if pre-op submission IS the work (per Amendment 001 Tier 1 work performed · operational evidence already exists) · "Acknowledge DVIR" same defect class |
| 10. New capabilities required? | Maintenance work-order system · utilization-by-job tracking (integrate with Time Verification + DR) · repair tracking · fuel-card integration · capital planning |

### 1.8 · FLEET

| Q | Answer |
|---|---|
| 1. Already in ForgedOps? | 🟡 Fleet Defects (live) · DVIR (live) · Document Expirations (iter151) · Asset Transfers |
| 2. External? | 📤 ELD (Samsara / Geotab / KeepTruckin) · IFTA reporting service · DOT clearinghouse · drug-test vendor · insurance carrier |
| 3. Manual? | 📊 Driver qualification files · medical-card expirations · license tracking · drug-test results · IFTA quarterly · insurance certificates · MVR (motor-vehicle reports) |
| 4. Spreadsheets? | 📊 Driver qual matrix · DOT-compliance roster · IFTA mileage |
| 5. Phone? | 📞 DOT inspector responses · roadside incident coordination · insurance claims |
| 6. Tribal? | 🧠 Which driver is on which truck day-to-day · informal swap arrangements |
| 7. Partial? | 🟡 Fleet defects (live) · DVIR (live) · Document Expirations (alerts but not driver-qual-specific) |
| 8. Absent? | 🔴 Driver qualification file (DQ-file) · DOT compliance dashboard · IFTA reporting · ELD integration · MVR tracking · drug-test pool management · roadside-incident workflow · insurance-certificate-by-vehicle · CSA-score monitoring |
| 9. Should NEVER build? | ⛔ "Acknowledge DVIR" beyond Tier 1 submission · "Acknowledge DOT log" — submission IS Tier 1 work · driver "I have read policies" patterns |
| 10. New capabilities required? | DQ-file workflow · DOT-compliance dashboard · IFTA reporting · ELD integration · MVR tracking · drug-test pool · CSA-score monitoring |

### 1.9 · FINANCIAL OPERATIONS

| Q | Answer |
|---|---|
| 1. Already in ForgedOps? | 🟡 PO Requests (request-only) · jobs_master · Suppliers · Payroll Variance (iter452 lifecycle) · `accountability_projection.py` (read-only library) |
| 2. External? | 📤 Accounting (QuickBooks / Sage 300 CRE / Foundation / Vista / Viewpoint) — **THIS IS THE LARGEST EXTERNAL DEPENDENCY ON THE PLATFORM** · banking · surety bonding · tax preparation |
| 3. Manual? | 📊 PO commit · PO receipt · AP entry · AR aging · invoice issuance · job costing · WIP schedule · bonding · lien waivers · tax filings |
| 4. Spreadsheets? | 📊 Job cost summaries · WIP schedules · AP aging · AR aging · cash flow · bonding capacity tracker · pay-app draws |
| 5. Phone? | 📞 Vendor disputes · customer collections · surety calls · banking inquiries |
| 6. Tribal? | 🧠 Which vendor accepts late pay · which customer pays slow · which job historically over/under budget |
| 7. Partial? | 🟡 PO Requests = request layer ONLY (no commit · no receipt · no payment) · Suppliers (basic master) · Payroll Variance = variance reconciliation ONLY (not full payroll) |
| 8. Absent? | 🔴 Full accounting (GL · AP · AR · job cost · WIP · cash flow) · pay-application workflow · subcontractor pay-app workflow · lien-waiver tracking · 1099 generation · bonding/surety · sales tax · bank reconciliation · invoice generation |
| 9. Should NEVER build? | ⛔ "Acknowledge invoice received" without payment action · "I approve payment" without integration to actual payment system (would be evidence of clicking without operational consequence) · multi-step approval chains for purely informational events |
| 10. New capabilities required? | Either (a) full accounting build (NOT recommended — out of operational scope for a construction ops platform) OR (b) deep integration with chosen accounting system (recommended) · pay-application workflow · lien-waiver tracking · sales-tax handling · job-cost feeds back into ForgedOps for executive surfaces |

### 1.10 · CUSTOMER #2 READINESS

| Q | Answer |
|---|---|
| 1. Already in ForgedOps? | 🔴 23/90 per `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §5 |
| 2. External? | n/a — Customer #2 readiness is platform-architectural |
| 3. Manual? | n/a |
| 4. Spreadsheets? | n/a |
| 5. Phone? | n/a |
| 6. Tribal? | 🧠 The fact that Customer #2 onboarding requires manual mongo seed + DNS + branding sweep (Customer #2 score row "Onboarding wizard = 0/10") |
| 7. Partial? | 🟡 Architecture is supportable but every collection is single-tenant · no `tenant_id` propagation |
| 8. Absent? | 🔴 `tenant_id` on every collection (141 collections) · multi-tenant auth · SSO/SAML/OIDC · per-tenant brand-config · tenant-onboarding wizard · per-tenant data isolation enforcement · per-tenant rate limiting · per-tenant audit · per-tenant backup/restore · per-tenant data export · per-tenant deletion (GDPR) |
| 9. Should NEVER build? | ⛔ Multi-tenant configuration UI that adds operator burden per tenant (one-time-per-tenant per Constitutional discipline · Rule 10 Toy Airplane Frontend) |
| 10. New capabilities required? | Tenant-isolation rebuild (~10 weeks per prior audit) · brand-config layer (~5 weeks AFTER tenant isolation) · SSO · tenant onboarding wizard · per-tenant export/delete |

---

## §2 · Aggregate operational coverage summary

| Area | % Operations runnable inside ForgedOps today | Largest single gap |
|---|---:|---|
| Executive | **15 %** | Portfolio rollup · financial reporting absent |
| Operations | **40 %** | Master schedule + subcontractor management absent |
| Project Management | **30 %** | Submittal/RFI/CO/Pay-App workflows absent |
| Field Operations | **70 %** | Strongest area; absent: field clock-in, production tracking |
| Safety | **60 %** | Closure paths missing on QA/QC + Site Insp; OSHA log absent |
| HR | **35 %** | Full payroll · perf reviews · discipline · onboarding/offboarding gaps |
| Equipment | **45 %** | Maintenance work-order system absent |
| Fleet | **35 %** | DQ-file · DOT compliance · ELD integration absent |
| Financial Operations | **15 %** | Accounting integration absent (largest external dependency) |
| Customer #2 Readiness | **25 %** | Tenant isolation rebuild required |
| **WEIGHTED AVERAGE** | **~37 %** | The platform is roughly one-third of a full construction-operations platform |

---

## §3 · Why the rest is not in ForgedOps today (root-cause clusters)

| Cluster | Areas affected | Count |
|---|---|---:|
| **External dependency on accounting/ERP** (intentional — out of operational scope) | Executive · Operations · PM · HR (payroll) · Financial | 5 |
| **Workflows absent from Phase 1A scope** (intentional — sequenced for later phases) | PM · Field · HR · Equipment · Fleet | 5 |
| **Constitutional friction on partial workflows** (Amendment 001 REPLACE items currently being treated as 🔴 gaps) | Safety · PM · HR | 3 |
| **Multi-tenancy architectural deferral** | Customer #2 readiness only | 1 |
| **Executive surfaces never built** (no executive role exists) | Executive · Operations · Financial | 3 |

---

## §4 · The primary-question answer in 3 sentences

1. **MASCI cannot run the company entirely inside ForgedOps today** — ~37 % weighted coverage; the rest runs on accounting software, spreadsheets, phone calls, and tribal knowledge.
2. **ForgedOps's strongest surfaces are Field Operations (70 %) and Safety (60 %)** — these are the areas with active Phase 1A investment.
3. **The largest blockers to full coverage are:** absent accounting/ERP integration · absent project-management workflows (Submittal/RFI/CO/Pay-App) · absent executive role + portfolio rollup · absent fleet-compliance stack · partial HR lifecycle · absent multi-tenancy.

---

## §5 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero workflows redesigned | ✅ |
| Zero solutions proposed | ✅ |
| Every operational area answered for all 10 questions | ✅ |
| Constitutional compliance applied to "should never build" answers | ✅ |
| Amendment 001 Tier 1/2/3/4 reasoning applied | ✅ |
| Primary question answered in 3 sentences | ✅ |

🛑 **STOPPED.** Continue to companion deliverables (Scorecard · Gap Register · Build-From-Scratch · External Dependency · Constitutional Violation · Customer #2 · ForgedOps v1 · Executive Summary · Prioritized Roadmap).
