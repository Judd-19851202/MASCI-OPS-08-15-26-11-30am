# OMEGA · PHASE 4 — COMPANY OPERATING SYSTEM AUDIT

**Date:** 2026-06-02 · Comprehensive function-by-function classification
**Mode:** READ-ONLY · zero code · zero design · zero estimates · zero authorization
**Operator authorization:** "Can MASCI run the entire company from ForgedOps today? Classify every operational function BUILD / INTEGRATE / EXISTS / IGNORE. The goal is operational completeness."
**Governing doctrine:** Constitution + Override + Amendment 001 + Build/Integrate/Ignore Doctrine + Ownership Doctrine O-1 through O-15

---

## §0 · Classification system (4-bucket · adds EXISTS to prior 3-bucket)

| Code | Meaning |
|---|---|
| ✅ **EXISTS** | Operationally live on platform today · serves the function · no build required (may have polish backlog) |
| 🔨 **BUILD** | Mission-core capability · platform must build · within ForgedOps mission boundary |
| 🔗 **INTEGRATE** | Mature external system owns this · ForgedOps consumes/contributes data |
| 🔨🔗 **HYBRID** | Workflow lives in ForgedOps · financial/data syncs to external system |
| 🚫 **IGNORE** | Adds complexity without operational value · eliminate or never start |

---

## §1 · Operations function

| Operational capability | Class | Evidence / Reasoning |
|---|---|---|
| Universal state machine across workflows | ✅ EXISTS | iter451 + iter452 + 5-state vocab live |
| Daily Reports workflow end-to-end | ✅ EXISTS | OC-002 live · PENDING_REVIEW + kickback + closure |
| Incidents workflow end-to-end | ✅ EXISTS | OC-001 live · 5-state lifecycle · OSHA + CAPA + reopen |
| Field Submitter Identity (5-tier) | ✅ EXISTS | iter452.5.1 live · orphan corner closed |
| Operational ownership graph (per record · per state) | 🔨 BUILD | Ownership Layer A+B+C (Top 10 #1) · gated by Phase 1/2 doctrine |
| "What's open across the platform that I own" | 🔨 BUILD | G1-14 · part of Ownership Layer B |
| Notification routing per Rule 8 | 🔨 BUILD | Notification Routing + iter452.5.2 P1 webhook (pre-authorized) |
| Cross-workflow corrective_actions canonicalization | 🔨 BUILD | G0-10 · single CA system across QA/QC + Incidents + Inspections |
| Operations Manager Action Console | 🔨 BUILD | Mandatory Exec Surface #3 |
| Workflow exception capture (dual-signoff documented exception) | 🔨 BUILD | NEW · single `workflow_exceptions` collection for all closure-action workflows |
| Stop-work authority structured workflow | 🔨 BUILD | B-17 · Constrained Co-Authority via O-11 |
| Master schedule (CPM math) | 🔗 INTEGRATE | EX-3 P6 / MS Project / HCSS HeavyJob owns |
| ELD / Hours-of-service compliance | 🔗 INTEGRATE | EX-4 Motive owns |

### Operations verdict
**Foundation EXISTS · accountability glue must BUILD · scheduling INTEGRATES.** Operations is roughly 50 % capable today; remaining 50 % is the Ownership Layer (BUILD) + scheduling INTEGRATE.

---

## §2 · Project Management function

| Capability | Class | Reasoning |
|---|---|---|
| Project master data + PM assignment | ✅ EXISTS | `jobs_master` collection · primary_pm field live |
| Daily Reports per project | ✅ EXISTS | OC-002 |
| Project-level CAPA visibility | ✅ EXISTS | corrective_actions tied to project via record_id linkage |
| Submittal workflow | 🔨 BUILD | G0-3 / B-1 · Constitutional re-scope required (no ack ride-along V-1) |
| RFI workflow | 🔨 BUILD | G0-4 / B-2 · no ack ride-along V-2 |
| Change-Order workflow | 🔨🔗 HYBRID | G0-5 / B-3 · workflow ForgedOps + financial EX-1 accounting |
| Pay-Application workflow | 🔨🔗 HYBRID | G0-6 / B-4 |
| Lien-Waiver tracking | 🔨🔗 HYBRID | G2-14 / B-5 |
| Project Budgeting / Forecast-to-Complete UI | 🔨🔗 HYBRID | B-7 (UI in ForgedOps · actuals from EX-1) |
| Meeting-minutes capture | 🔨 BUILD | G2-15 / B-6 · no "Read and Acknowledged" V-5 |
| Subcontractor management | 🔨🔗 HYBRID | G0-9 / B-14 · contracts + insurance + scope · financial INTEGRATE |
| Material delivery confirmation | 🔨 BUILD | B-10 · extends PO workflow |
| Project Risk Lens Action Console | 🔨 BUILD | Mandatory Exec Surface #2 |
| Per-PM Action Console | 🔨 BUILD | Mandatory Exec Surface #1 (G1-2) |
| Job costing | 🔗 INTEGRATE | EX-1 accounting owns · ForgedOps consumes |
| WIP / forecast-to-complete actuals | 🔗 INTEGRATE | EX-1 owns the math |
| CRM / bid pipeline / backlog | 🔗 INTEGRATE | EX-13 CRM owns · out of mission |

### Project Management verdict
**Foundations EXIST · cluster of 7 PM workflows must BUILD or HYBRID · CRM + Accounting INTEGRATE.** PM function is roughly 25 % capable today.

---

## §3 · Safety function

| Capability | Class | Reasoning |
|---|---|---|
| Incidents lifecycle | ✅ EXISTS | OC-001 |
| OSHA recordable classification on closure | ✅ EXISTS | iter451 attestation modal |
| Safety Training records | ✅ EXISTS | `safety_training_records` collection |
| Toolbox Talks | ✅ EXISTS | Live workflow |
| JHP library | ✅ EXISTS | `JhaPlansHub` + `JhaPlansAdmin` live |
| Safety Manager Action Console | 🔨 BUILD | Mandatory Exec Surface #4 |
| Site Inspection follow-up | 🔨 BUILD | OC-004 · iter453 (closure-action contract per Phase 3) |
| QA/QC follow-up | 🔨 BUILD | OC-003 · iter453 |
| OSHA 300 / 301 / 300A generator | 🔨 BUILD | G1-6 / B-15 · OSHA portal EX-8 INTEGRATE consumer |
| OC-005 JHP Evidence (re-scoped) | 🔨 BUILD | per Amendment 001 REPLACE-1 (Toolbox Talk + attendance + JHP download identity) |
| OC-008 PPE Return | 🔨 BUILD | G2-3 / B-16 |
| Stop-work authority | 🔨 BUILD | B-17 · O-11 Constrained Co-Authority pattern |
| OSHA portal submission | 🔗 INTEGRATE | EX-8 government system |
| Workers comp claim linkage | 🔗 INTEGRATE | EX-7 carrier owns |
| Drug-test pool tracking | 🔗 INTEGRATE | EX-6 vendor owns |
| MSDS / SDS library | 🔗 INTEGRATE | EX-11 Velocity/KHA/3E owns |
| iter445 "Has crew reviewed JHP?" Yes/No field | 🚫 IGNORE | FAIL-1 · eliminate |
| Vestigial `db.jhas` form | 🚫 IGNORE | FAIL-2 · decommission |
| Pattern D BilingualConsent on JHP | 🚫 IGNORE | Constitutional violation per Compliance Sweep |

### Safety verdict
**Strongest functional area today · ~55 % capable.** Remaining work: closure-action contracts (iter453 BUILD) + OC-005 re-scope + OC-008 + Stop-work workflow + OSHA generator + 4 INTEGRATE items.

---

## §4 · QA/QC function

| Capability | Class | Reasoning |
|---|---|---|
| QA/QC inspection submission | ✅ EXISTS | Live workflow |
| Deficiency capture as data | ✅ EXISTS | Inspection records |
| Re-inspection record linkage | 🔨 BUILD | NEW · `original_deficiency_id` linkage primitive |
| OC-003 closure-action contract | 🔨 BUILD | iter453 per Phase 3 package |
| Sub-coordination event capture | 🔨 BUILD | `sub_coordination_event` schema |
| "Mark Resolved" ack-click | 🚫 IGNORE | Amendment 001 REPLACE-5 · eliminate |
| Quality Manager Action Console | 🔨 BUILD | (subset of Operations Manager Console initially · separable later) |
| Per-PM quality scorecard | 🔨 BUILD | Part of Per-PM Action Console |
| Third-party quality consultant integration | 🔗 INTEGRATE | If MASCI uses one · operator-dependent · light-touch consumer |

### QA/QC verdict
**Inspections EXIST · follow-up loop BUILDs.** ~35 % capable today; iter453 closes the gap.

---

## §5 · Fleet function

| Capability | Class | Reasoning |
|---|---|---|
| Vehicle master / Fleet inventory | ✅ EXISTS | Live |
| DVIR submission | ✅ EXISTS | Live |
| Fleet Defects lifecycle | ✅ EXISTS | Live · state machine in place |
| Fleet Manager Action Console | 🔨 BUILD | Mandatory Exec Surface #5 |
| Driver Qualification File workflow | 🔨 BUILD | G1-7 / B-23 · Constitutional re-scope (no V-10 annual DOT-policy ack) |
| DOT Compliance Dashboard (Action Console) | 🔨 BUILD | G1-8 / B-24 · Mandatory Exec Surface #5 |
| ELD / Telematics integration | 🔗 INTEGRATE | EX-4 Motive (operator-named) |
| IFTA reporting | 🔗 INTEGRATE | EX-5 ELD-bundled |
| Fuel-card integration | 🔗 INTEGRATE | EX (fuel vendor owns) |
| MVR / Drug-test (DQ-file feeds) | 🔗 INTEGRATE | EX-6 |
| "Driver acknowledges DOT policy" annual click | 🚫 IGNORE | V-10 · eliminate from any DQ-file build scope |

### Fleet verdict
**~40 % capable** today. Remaining work: DQ-file BUILD + DOT Action Console BUILD + ELD/fuel/drug-test INTEGRATEs.

---

## §6 · Equipment function

| Capability | Class | Reasoning |
|---|---|---|
| Asset Master | ✅ EXISTS | Live |
| Pre-Op submission | ✅ EXISTS | Live |
| Asset Transfers | ✅ EXISTS | Live · state machine in place |
| Maintenance work-order system | 🔗 INTEGRATE | EX MaintainX (operator-named) |
| Equipment utilization-by-job | 🔨 BUILD | G2-5 / B-22 · consumer of existing primitives |
| Shop Foreman Action Console | 🔨 BUILD | (subset of Operations Manager Console initially) |
| Equipment Manager Action Console | 🔨 BUILD | (subset / sibling of Shop Foreman) |
| Preventive maintenance cycle tracking | 🔗 INTEGRATE | MaintainX owns · ForgedOps consumes events |
| Photo Janitor (OC-009) | 🔨 BUILD | G3-6 · Rule 6/7 strong alignment |

### Equipment verdict
**~45 % capable** today · strong foundation. Remaining: MaintainX INTEGRATE + utilization BUILD + Action Consoles.

---

## §7 · Shop function

(Note: Shop function overlaps Equipment. Shop = the operational unit; Equipment = the asset class. Distinct accountability surfaces.)

| Capability | Class | Reasoning |
|---|---|---|
| Pre-Op flow into Shop work queue | ✅ EXISTS | DVIR + Equipment Defect lifecycle |
| Asset return → Shop intake | ✅ EXISTS | Asset Transfer state machine |
| Shop labor hours | 🔗 INTEGRATE | Payroll EX-2 |
| Shop work-order tracking | 🔗 INTEGRATE | MaintainX/Fiix |
| Parts inventory | 🔗 INTEGRATE | MaintainX / vendor inventory |
| Shop Foreman per-asset PM cycle tracking | 🔗 INTEGRATE | MaintainX |
| Shop Foreman Action Console (operational triage) | 🔨 BUILD | Consumer of MaintainX events + existing primitives |

### Shop verdict
**~30 % capable** today (operational data flows EXIST · work-order system INTEGRATEs · Action Console BUILDs).

---

## §8 · HR function

| Capability | Class | Reasoning |
|---|---|---|
| Employee master | ✅ EXISTS | Live |
| Time verification | ✅ EXISTS | Live |
| Payroll Variance lifecycle | ✅ EXISTS | OC-007 live |
| Time Off requests | ✅ EXISTS | Live with manager approval (manager_employee_id pending for full automation) |
| `manager_employee_id` field | 🔨 BUILD | G1-11 · foundation for HR accountability |
| Onboarding · field-side (training · PPE · access) | 🔨 BUILD | OC-013 re-scoped (REPLACE-7) |
| Offboarding · field-side (PPE return · access revoke) | 🔨 BUILD | OC-014 re-scoped (REPLACE-6) |
| Discipline tracking (safety-incident-tied) | 🔨🔗 HYBRID | G1-10 / B-19 |
| HR Operational Action Console (field-side only) | 🔨 BUILD | Mandatory Exec Surface #7 |
| Performance review | 🔗 INTEGRATE | EX-9 / HRIS owns · NOT ForgedOps mission |
| Benefits administration | 🔗 INTEGRATE | EX-9 |
| ATS / recruiting | 🔗 INTEGRATE | EX-10 |
| Compensation history | 🔗 INTEGRATE | HRIS |
| I-9 / E-Verify | 🔗 INTEGRATE | E-Verify portal + HRIS |
| Payroll processing | 🔗 INTEGRATE | EX-2 payroll processor |
| OC-013 orientation checkbox | 🚫 IGNORE | REPLACE-7 · use safety_training_records (Tier 1) |
| OC-014 exit-interview checkbox | 🚫 IGNORE | REPLACE-6 · capture as Tier 1 data |
| "Employee acknowledges handbook" | 🚫 IGNORE | V-14 · eliminate |
| "Employee acknowledges performance review" | 🚫 IGNORE | V-8 · eliminate |

### HR verdict
**~30 % capable** for field-ops-tied HR (operational onboarding/offboarding/variance). **Pure HR (benefits, payroll processing, performance reviews) explicitly INTEGRATE · out of mission.** HR field-side is roughly 35 %.

---

## §9 · Accounting function

| Capability | Class | Reasoning |
|---|---|---|
| Accounting / ERP (GL · AP · AR · bank rec) | 🔗 INTEGRATE | **EX-1 BLOCKING** · single largest unblock · operator's named systems: QuickBooks · Sage · Foundation · Vista · Viewpoint |
| Job cost computation engine | 🔗 INTEGRATE | EX-1 · ForgedOps consumes job-cost feed |
| WIP / forecast-to-complete | 🔗 INTEGRATE | EX-1 |
| AP processing | 🔗 INTEGRATE | EX-1 |
| AR / invoicing | 🔗 INTEGRATE | EX-1 |
| Sales tax | 🔗 INTEGRATE | EX-1 (tax-regulated) |
| Bonding / surety capacity | 🔗 INTEGRATE | EX-1 + surety broker |
| Pay-Application financial side | 🔗 INTEGRATE | EX-1 (workflow side is HYBRID · captured in PM function) |
| CO financial side | 🔗 INTEGRATE | EX-1 |
| Lien-waiver financial impact | 🔗 INTEGRATE | EX-1 |
| Accounting/EX-1 Integration Surface (ForgedOps side) | 🔨 BUILD | Mandatory Exec Surface #6 · ForgedOps reads accounting events + surfaces them in Action Consoles |
| Payroll processing | 🔗 INTEGRATE | EX-2 payroll processor |
| Estimating / bid software | 🔗 INTEGRATE | HCSS Estimator / B2W / Heavy-Bid |

### Accounting verdict
**~5 % capable** today (only the data structures exist · zero accounting integration). **EX-1 is the single largest unblock for the entire platform.** Without EX-1, Executive financial visibility, HYBRID PM workflows, and pay-application closure are all impossible.

---

## §10 · Executive Leadership function

| Capability | Class | Reasoning |
|---|---|---|
| Executive role / login / portal | 🔨 BUILD | G1-1 / B-11 · Mandatory Exec Surface #1 anchor |
| PM Portfolio Action Console | 🔨 BUILD | Mandatory Exec Surface #1 |
| Project Risk Lens | 🔨 BUILD | Mandatory Exec Surface #2 |
| Operations Manager Action Console | 🔨 BUILD | Mandatory Exec Surface #3 |
| Safety Manager Action Console | 🔨 BUILD | Mandatory Exec Surface #4 |
| Fleet + DOT Action Console | 🔨 BUILD | Mandatory Exec Surface #5 |
| Accounting/EX-1 Integration Surface | 🔨 BUILD | Mandatory Exec Surface #6 |
| HR Operational Surface (field-side) | 🔨 BUILD | Mandatory Exec Surface #7 |
| "What's open across the platform that I own" | 🔨 BUILD | Mandatory Exec Surface #8 (G1-14) |
| Backlog / bid pipeline | 🔗 INTEGRATE | EX-13 CRM |
| External BI tools (Tableau · Power BI · Looker) | 🔗 INTEGRATE | Data export · NOT internal rebuild · Rule 9 |
| Executive blast emails | 🚫 IGNORE | Rule 8 violation |
| "Print Board Packet" with ack ride-along | 🚫 IGNORE | V-13 |
| Read-only KPI dashboards | 🚫 IGNORE | Anti-checklist clause |
| "Executive acknowledges weekly KPIs" boolean | 🚫 IGNORE | V-13 |
| Standalone chart tiles | 🚫 IGNORE | O-15 No-Standalone-Chart Rule |

### Executive Leadership verdict
**~5 % capable** today (no executive role exists). **8 mandatory Action Consoles must BUILD.** BI tools INTEGRATE via data export · zero internal dashboard rebuild.

---

## §11 · Aggregate classification tally (operational-capability count)

Counted across all 10 functions:

| Class | Count |
|---|---:|
| ✅ EXISTS | ~22 |
| 🔨 BUILD | ~38 |
| 🔗 INTEGRATE | ~21 (including HYBRID integration-side) |
| 🔨🔗 HYBRID | ~9 |
| 🚫 IGNORE | ~14 |
| **Approximate total** | **~104** |

Counts overlap (some capabilities span multiple functions; e.g., Per-PM Action Console serves Operations · PM · Executive).

---

## §12 · The 5 mandatory answers

### Answer 1 · What MASCI can run today
| Function | Capability |
|---|---|
| Operations | Universal state machine · Daily Reports · Incidents · FSI 5-tier identity · Asset Transfers · Fleet Defects · Equipment Pre-Op · DVIR · Time Verification · Payroll Variance · Safety Training · Toolbox Talks · JHP library · CAPA collection · Document expirations · MFA · Backups · Recovery · 9 admin/reporting surfaces — **~22 capabilities EXISTS** |
| Foundations strong | State machine, 5-tier identity ladder, audit trail (workflow_state_events), tasks schema, employees, jobs_master |

### Answer 2 · What MASCI cannot run today
| Function | Gap |
|---|---|
| Executive | No role · no login · 0/8 mandatory Action Consoles |
| Accounting | 0 integration · all financial in external accounting · invisible to ForgedOps |
| PM workflows | Submittal · RFI · CO · Pay-App · Sub-Mgmt · Lien-Waiver · Meeting-Minutes — all absent |
| Field clock-in/out | Paper · spreadsheet |
| Production tracking | Spreadsheets · tribal knowledge |
| Closure-action loops | QA/QC + Site Inspection submit-only · closure absent (pending iter453) |
| Ownership glue | 0/736 user-level task assignment · 0/12 escalation coverage |
| Notification routing per Rule 8 | Multi-recipient fan-out is current pattern |
| Field-side onboarding/offboarding multi-step | Partial · checklist-shaped |
| DQ-file + DOT compliance | Paper · spreadsheets |
| OSHA reporting | Spreadsheet annual |
| Maintenance work-order | External (operator-named MaintainX) |
| ELD / Telematics | External (operator-named Motive) |
| CRM / backlog / bid pipeline | External |
| HRIS-side (benefits · ATS · performance) | External |

**Roughly 63 % of operational surface runs OUTSIDE ForgedOps today.**

### Answer 3 · What must be built
**~38 BUILD capabilities · 7 HYBRID build-side.**

Top 10 build priorities per Build/Integrate/Ignore audit Top 10:
1. Universal Ownership Layer A+B
2. Field Clock-in/out
3. Production Tracking by Activity
4. Executive Role + Portfolio Action Console
5. iter453 OC-003 + OC-004 Closure-Action Contract (Constitutional package complete · Phase 3)
6. OSHA 300/301/300A Generator
7. DOT Compliance + Driver Qualification File
8. OC-005 JHP Evidence (re-scoped)
9. Subcontractor Management (HYBRID)
10. Notification Routing per Rule 8 + iter452.5.2 P1

### Answer 4 · What should be integrated
**~21 INTEGRATE capabilities.** EX-1 Accounting is BLOCKING (single largest unblock). Wave sequence per `EXTERNAL_DEPENDENCY_STRATEGY.md`:
* Wave 1: EX-1 Accounting/ERP
* Wave 2: EX-2 Payroll · EX-4 ELD/Motive
* Wave 3: EX-3 Scheduling · EX-6 Drug-test · EX-7 Workers Comp · EX-8 OSHA portal · EX-11 MSDS
* Wave 4: EX-5 IFTA · EX-9 Benefits · EX-10 ATS
* Plus: MaintainX (maintenance) · Fuel card · CRM · HRIS · auth provider (Auth0/Okta for multi-tenancy)

### Answer 5 · What should never be built
**~14 IGNORE items** in this audit + 48 prior IGNORE items in `FORGEDOPS_IGNORE_LIST.md` = ~62 distinct items the platform must never build, including:
* Every acknowledgement-as-work pattern (V-1 through V-14)
* Every mature-system replacement (accounting · payroll · CRM · estimating · ATS · benefits · ELD · maintenance · MSDS · workers comp · fuel · IFTA)
* Every architectural anti-pattern (read-only dashboards · multi-recipient broadcasts · manual-assign UI · standalone charts · checklist-shaped workflows)

---

## §13 · Operational completeness ceiling projection

| State | Operational completeness (informational projection) |
|---|---:|
| **Today** (this audit · 22 EXISTS / 104 total) | **~22 % core EXISTS + ~15 % adjacent partial = ~37 %** (matches `OPERATIONAL_REALITY_AUDIT.md` 35/100 score) |
| + Ownership Layer A+B (BUILD Wave 1) | ~50 % |
| + Field Clock-in/out + Production Tracking (BUILD Wave 2) | ~58 % |
| + iter453 + OC-005 + Stop-work + PPE Return (BUILD Wave 3) | ~63 % |
| + EX-1 Accounting integration (INTEGRATE Wave 1) | ~70 % |
| + Executive Role + 8 Action Consoles (BUILD Wave 4) | ~78 % |
| + PM workflow cluster (Submittal · RFI · CO · Pay-App · Sub-Mgmt · MoM) | ~85 % |
| + INTEGRATE Waves 2-3 (Payroll · ELD · OSHA portal · Drug-test · MSDS · Workers Comp) | ~90 % |
| + DQ-file + DOT Dashboard (BUILD Wave 3 cont.) | ~93 % |
| + Architectural multi-tenancy parallel track | (architectural · doesn't move operability score) |
| + Remaining INTEGRATE optional + polish | ~95+ % |

This projection mirrors `RECOMMENDED_ROADMAP_RESET.md §5`.

---

## §14 · The "reduce work / create work" test

Every future recommendation must answer: **Does this reduce work or does it create work?**

| Recommendation pattern | Reduces or creates work? | Constitutional standing |
|---|---|---|
| Ownership inference engine | Reduces · removes manual assignment | ✅ Required |
| Action Console executive surfaces | Reduces · executives see + act in one place | ✅ Required |
| iter452.5.2 Resend bounce webhook | Reduces · prevents silent delivery failures from creating manual chase work | ✅ Required |
| Field Clock-in/out (B-8) | Reduces · eliminates paper time tickets + reconciliation friction | ✅ Required |
| Production Tracking by Activity | Reduces · replaces spreadsheet + tribal knowledge | ✅ Required |
| EX-1 Accounting integration | Reduces · eliminates manual data entry between systems | ✅ Required |
| OSHA Generator | Reduces · automates annual reporting | ✅ Required |
| **Read-only KPI dashboard** | **Creates** · forces "I have to check this" recurring action | 🚫 Forbidden |
| **"Mark Resolved" ack button** | **Creates** · invents a click that no operational reality requires | 🚫 Forbidden |
| **"Assignee" dropdown** | **Creates** · invents an upstream decision (who owns?) before downstream work begins | 🚫 Forbidden |
| **Multi-step onboarding checklist** | **Creates** · invents N clicks where Tier 1 evidence already exists | 🚫 Forbidden |
| **Executive weekly KPI ack boolean** | **Creates** · invents a click without operational consequence | 🚫 Forbidden |
| **Standalone chart tile** | **Creates** · invents a "look at me" surface without action | 🚫 Forbidden |
| **"Acknowledge findings" button** | **Creates** · replaces operational action (re-inspection) with a click | 🚫 Forbidden |

The test is **forward-binding on every future scoping conversation**. If it creates work, it is presumed unconstitutional until proven otherwise.

---

## §15 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code | ✅ |
| Zero design | ✅ |
| Zero estimates | ✅ |
| Zero authorization | ✅ |
| All 10 functions classified | ✅ |
| BUILD / INTEGRATE / EXISTS / HYBRID / IGNORE per capability | ✅ |
| 5 mandatory answers delivered | ✅ |
| Operational completeness ceiling projection rendered | ✅ |
| Reduce-work-vs-create-work test rendered | ✅ |

🛑 **STOPPED.**
