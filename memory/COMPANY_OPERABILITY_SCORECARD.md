# OMEGA · COMPANY OPERABILITY SCORECARD

**Date:** 2026-06-02 · Companion to `OPERATIONAL_REALITY_AUDIT.md`
**Mode:** READ-ONLY · scoring against `FORGEDOPS_OPERATIONAL_DESIGN_CONSTITUTION.md`
**Question:** What fraction of MASCI's company operations can run inside ForgedOps today?

---

## §0 · Scoring methodology

Each operational area scored on:
* **Coverage %** — fraction of the area's operational surface that can be performed end-to-end inside ForgedOps today, without external systems, spreadsheets, phone, or tribal knowledge
* **Lifecycle completeness** — workflows have Open → Active → Resolution → Closure (Rule 4)
* **Accountability completeness** — owned by a specific person (Rule 3 + Ownership Audit baseline 0/736 user-level assignment)
* **Field adoption probability** — Amendment 001 axis · "would a foreman/super/PM actually use this without a workaround?"

Score components weighted equally (25 % each). Aggregate is the weighted average per area.

---

## §1 · Per-area scorecard

| # | Operational Area | Coverage % | Lifecycle % | Accountability % | Adoption % | **AGGREGATE** |
|---:|---|---:|---:|---:|---:|---:|
| 1 | **Executive** | 15 | 10 | 0 | 25 | **🔴 12 / 100** |
| 2 | **Operations** | 40 | 50 | 10 | 60 | **🟠 40 / 100** |
| 3 | **Project Management** | 30 | 40 | 15 | 50 | **🟠 34 / 100** |
| 4 | **Field Operations** | 70 | 60 | 15 | 80 | **🟡 56 / 100** |
| 5 | **Safety** | 60 | 55 | 15 | 75 | **🟡 51 / 100** |
| 6 | **HR** | 35 | 35 | 20 | 55 | **🟠 36 / 100** |
| 7 | **Equipment** | 45 | 35 | 10 | 70 | **🟠 40 / 100** |
| 8 | **Fleet** | 35 | 35 | 15 | 60 | **🟠 36 / 100** |
| 9 | **Financial Operations** | 15 | 25 | 10 | 30 | **🔴 20 / 100** |
| 10 | **Customer #2 Readiness** | 25 | 30 | 30 | 30 | **🔴 29 / 100** |
| | **PLATFORM-WIDE AGGREGATE** | **37** | **38** | **14** | **53** | **🔴 35 / 100** |

---

## §2 · Component analysis

### Coverage (37 %)
Approximately one-third of the operational surface area is inside the platform today. The platform handles Field Operations (Daily Reports, Toolbox Talks, Equipment Pre-Op, DVIR) and Safety (Incidents, Inspections, JHP library) substantially well. It handles Project Management, Financial Operations, and Executive surfaces poorly — because the Phase 1A scope deliberately did not include them.

### Lifecycle Completeness (38 %)
A workflow with no closure path violates Rule 4. The platform currently has 24 of 41 workflows with terminal closure paths (per `OPERATIONAL_COMPLETENESS_REGISTER.md`), but lifecycle workflows like Time Off · Payroll Variance · Incident · DR all advance through state machines without closing user-level assignments (0/736 task closures per Ownership Audit). This is the second-largest Constitutional liability after acknowledgement-as-work.

### Accountability (14 %) 🔴
The single weakest dimension. 0/736 tasks have user-level assignment. No workflow names a specific accountable owner. Three parallel Corrective-Action systems disagree on ownership. No executive view exists. This score reflects the Ownership Audit verdict (18/100 maturity) viewed through the operability lens.

### Field Adoption Probability (53 %)
The strongest dimension because Phase 1A investment targets field-side surfaces (FSI 5-tier identity ladder · bilingual public-gate forms · revise workflow). Field adoption would be higher if iter445's "Has crew reviewed JHP?" Yes/No field were eliminated (FAIL-1) and OC-005 ack pattern were not built (P0 violation).

---

## §3 · Per-area headline assessment

### 🔴 12 / 100 — Executive
No executive role exists. No portfolio rollup. The Command Center is operationally IT/ops oriented, not executive-decision oriented. **An executive cannot run the company from inside ForgedOps today.**

### 🟠 40 / 100 — Operations
PO Requests + Asset Transfers + Dispatch + CAPA are strong individual workflows. The cross-project resource allocation layer (subcontractor management · master schedule · weekly look-ahead) is absent. **Operations runs ForgedOps for transactional workflows; relies on spreadsheets + phone for coordination.**

### 🟠 34 / 100 — Project Management
PM uses ForgedOps for Daily Reports · QA/QC + Site Inspection submissions · PO Requests · photos. PM uses spreadsheets/Bluebeam for: Submittals · RFIs · Change Orders · Pay Applications · Lien Waivers · Closeout Package. **PM cannot run the project lifecycle entirely inside ForgedOps.**

### 🟡 56 / 100 — Field Operations
Strongest area. Daily Reports lifecycle live · FSI identity ladder live · Equipment Pre-Op · DVIR · Toolbox Talks. Gaps: field clock-in/out per employee · production-by-activity tracking · material delivery confirmation. **Field Ops is the closest to running entirely inside ForgedOps today — and would clear 75 / 100 if the gaps were closed Constitutionally.**

### 🟡 51 / 100 — Safety
Incident lifecycle live (iter451) · OSHA recordable ack live · JHP library live · CAPA exists. Gaps: OSHA 300/301 generator · workers comp claim integration · drug-test tracking · stop-work workflow · QA/QC + Site Inspection follow-up. **Safety can record events but cannot run the full compliance cycle.**

### 🟠 36 / 100 — HR
Employee directory + Time Off Request + Payroll Variance (lifecycle) + safety_training_records. Gaps: full payroll · performance reviews · discipline · benefits · ATS · I-9/E-Verify · onboarding+offboarding multi-step · `manager_employee_id`. **HR runs payroll outside the platform and most lifecycle workflows in spreadsheets.**

### 🟠 40 / 100 — Equipment
Equipment master · Pre-Op · DVIR · Asset Transfers · Fire Extinguishers · Document Expirations. Gaps: maintenance work-order system · utilization-by-job · repair tracking · fuel · depreciation · capital plan. **Equipment use is recorded; equipment maintenance lifecycle is not.**

### 🟠 36 / 100 — Fleet
Fleet Defects · DVIR · Document Expirations · Asset Transfers. Gaps: Driver Qualification File · DOT compliance · IFTA · ELD integration · MVR · drug-test pool · CSA score. **Fleet compliance runs on spreadsheets and the ELD vendor portal.**

### 🔴 20 / 100 — Financial Operations
PO Requests (request-only) · Suppliers · Payroll Variance. Gaps: GL · AP · AR · job cost · WIP · pay applications · invoicing · bank reconciliation · bonding · sales tax. **The accounting system IS the financial operations system; ForgedOps is structurally NOT the financial system and intentionally so.**

### 🔴 29 / 100 — Customer #2 Readiness
Architecture single-tenant. No `tenant_id` propagation. No SSO. No tenant onboarding wizard. Brand strings hard-coded. **Customer #2 cannot be onboarded today without ~15 weeks of platform work (tenant + brand).**

---

## §4 · Aggregate platform verdict

# 🔴 35 / 100 — MASCI CANNOT RUN THE COMPANY ENTIRELY INSIDE FORGEDOPS

**Plain-English headline:** The platform handles roughly one-third of operational surface area with reasonable maturity. The other two-thirds is either intentionally external (accounting/ERP), deferred to future phases (PM workflows, executive surfaces, full HR lifecycle, fleet compliance), or runs on tribal/spreadsheet/phone substitutes today.

### The 4 paths forward (informational · operator-decision)

| Path | What it accomplishes | Trade-off |
|---|---|---|
| (A) **Close Phase 1A friction first** (Constitution-compliant re-scopes of OC-003/004/005/013/014 + Ownership v1) | Brings Safety + Field Ops + PM partial up to ~70/100 each | Does not change Executive · Financial · Fleet scores |
| (B) **Build PM workflows + Executive surfaces** (Submittal · RFI · CO · Pay-App · Executive role · portfolio rollup) | Brings PM + Executive + Operations up to ~60/100 each | Substantial new build · ~20+ weeks |
| (C) **Integrate accounting/ERP deeply** (instead of building it) | Unblocks Financial + Executive WIP/forecasting | Requires partner system + integration layer · 8-12 weeks |
| (D) **Defer multi-tenancy + brand-config** (focus on single-tenant operability first) | Keeps platform investment on MASCI's operational reality | Customer #2 onboarding remains blocked |

🛑 **None of these is authorized.** Operator selection required.

---

## §5 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero solutions designed | ✅ |
| 4 weighted components per area | ✅ |
| Platform aggregate 35/100 computed from per-area scores | ✅ |
| 4 informational paths-forward rendered (no recommendation) | ✅ |

🛑 **STOPPED.** Scorecard delivered.
