# OMEGA · EXTERNAL DEPENDENCY STRATEGY

**Date:** 2026-06-02 · Companion to `EXTERNAL_DEPENDENCY_REGISTER.md`
**Mode:** READ-ONLY · zero code · zero design · zero vendor selection
**Method:** Apply Build/Integrate/Ignore doctrine to all 11 external dependencies; classify each as Must Remain External · Should Be Integrated · Unnecessary · Blocking Operational Maturity.

---

## §1 · Strategy classification matrix

| # | Dependency | Strategy | Why |
|---:|---|---|---|
| EX-1 | **Accounting / ERP** (QuickBooks/Sage/Foundation/Vista/Viewpoint) | 🔗 **INTEGRATE — BLOCKING** | Single largest unblock for Executive WIP/forecast · pay-app · CO · lien-waiver financials. Without accounting integration, 5 HYBRID greenfield items cannot complete. |
| EX-2 | **Payroll processor** (ADP/Paychex/Foundation) | 🔗 **INTEGRATE — REQUIRED** | Variance reconciliation already partially live · push-to-payroll closes the loop. Constitutionally clean (push events are Tier 1 data movement). |
| EX-3 | **Project scheduling** (P6/MS Project/HCSS HeavyJob) | 🔗 **INTEGRATE — RECOMMENDED** | ForgedOps consumes schedule for look-ahead views and Daily Report context. Heavy civil GCs use HCSS HeavyJob commonly — single integration target available. |
| EX-4 | **ELD / Telematics** (Motive/Samsara/Geotab) | 🔗 **INTEGRATE — REQUIRED** | Operator explicitly named Motive. Feeds DQ-file (B-23) · DOT Compliance Dashboard (B-24) · supplements Fleet Defects. Regulatory non-negotiable. |
| EX-5 | **IFTA reporting** | 🔗 **INTEGRATE — OPTIONAL** | Most ELDs bundle IFTA. If EX-4 selected ELD includes IFTA, no separate integration needed. |
| EX-6 | **Drug-test pool management** (DISA / US HealthWorks / Concentra) | 🔗 **INTEGRATE — RECOMMENDED** | Feeds DQ-file (B-23). Light-touch event consumption · HIPAA-bounded data stays at vendor. |
| EX-7 | **Workers comp carrier** (Travelers/Liberty/Zurich/Hartford) | 🔗 **INTEGRATE — RECOMMENDED** | Link incident records to claim IDs. Carrier-specific; integration depth varies. Often manual claim filing with structured tracking on ForgedOps side. |
| EX-8 | **OSHA reporting portal** (OSHA ITA) | 🔗 **INTEGRATE — REGULATORY** | Government system. ForgedOps generates artifact (B-15); portal receives submission. Direct API submission optional; export-and-upload acceptable. |
| EX-9 | **Benefits administration** (ADP TotalSource/Paychex Flex/Zenefits) | 🔗 **INTEGRATE — OPTIONAL** | Employee-status events flow from ForgedOps to benefits admin. Light integration · NOT replace benefits enrollment. |
| EX-10 | **ATS / recruiting** (Greenhouse/Lever/iCIMS/BambooHR) | 🔗 **INTEGRATE — OPTIONAL** | Consume hire events → seed employee record. Light integration · NOT replace recruiting pipeline. |
| EX-11 | **MSDS / SDS library** (Velocity EHS / KHA / 3E) | 🔗 **INTEGRATE — RECOMMENDED** | Link contextually from JHP / Daily Report. Subscription product · ForgedOps does not host SDS data. |

---

## §2 · Strategy tally

| Strategy | Count | Items |
|---|---:|---|
| 🔗 INTEGRATE — BLOCKING | 1 | EX-1 (accounting) |
| 🔗 INTEGRATE — REQUIRED | 2 | EX-2 (payroll) · EX-4 (ELD/Motive) |
| 🔗 INTEGRATE — REGULATORY | 1 | EX-8 (OSHA portal) |
| 🔗 INTEGRATE — RECOMMENDED | 4 | EX-3 (scheduling) · EX-6 (drug-test) · EX-7 (workers comp) · EX-11 (MSDS) |
| 🔗 INTEGRATE — OPTIONAL | 3 | EX-5 (IFTA · ELD-bundled) · EX-9 (benefits) · EX-10 (ATS) |
| 🚫 UNNECESSARY | 0 | (Every external dependency has operational rationale) |
| **TOTAL** | **11** | |

---

## §3 · Integration priority sequencing

### Wave 1 · Unblock Executive + PM (REQUIRED)
* **EX-1 Accounting / ERP** — without this, B-3 (CO) · B-4 (Pay-App) · B-5 (Lien-Waiver) · B-7 (Budgeting/Forecast) · G1-5 (WIP) cannot complete. Single most-consequential integration.

### Wave 2 · Unblock Fleet compliance + Field accountability (REQUIRED)
* **EX-4 ELD/Motive** — feeds B-23 (DQ-file) + B-24 (DOT Compliance Dashboard).
* **EX-2 Payroll processor** — completes the variance reconciliation loop already live in iter452.

### Wave 3 · Round out compliance + safety surfaces (RECOMMENDED)
* **EX-6 Drug-test** — feeds DQ-file
* **EX-8 OSHA portal** — pairs with B-15 generator
* **EX-11 MSDS** — JHP context linkage
* **EX-7 Workers comp carrier** — incident-to-claim linkage

### Wave 4 · Round out HR (OPTIONAL)
* **EX-3 Scheduling** — look-ahead view (could come earlier with HCSS HeavyJob if MASCI uses it)
* **EX-9 Benefits** — employee-status push
* **EX-10 ATS** — hire-event consumption

### Wave 5 · Bundled (OPTIONAL)
* **EX-5 IFTA** — bundled with EX-4 ELD selection

---

## §4 · Constitutional posture on integrations

Every integration must satisfy:
1. **Rule 7 (Accountability Must Be Automatic):** Data flows automatically · no manual re-entry where possible
2. **Rule 8 (Reduce Operational Noise):** Failures route to one designated operator, never department broadcast
3. **Amendment 001 Rule 11:** Integration events ("PO sent · invoice received · pay-app approved") are Tier 1 work-performed evidence, NOT ack workflows
4. **Anti-checklist clause:** Integration health surfaces are Action Consoles (resolve · retry · reassign), never read-only health dashboards
5. **Build/Integrate/Ignore Doctrine:** Never rebuild what the external vendor does better

---

## §5 · Items that must remain external (no integration)

None. Every external dependency has at least an "OPTIONAL" integration value. The Constitution does not require integrating everything; the operator may explicitly defer EX-5, EX-9, EX-10, EX-11 indefinitely without Constitutional cost.

---

## §6 · Items blocking operational maturity

* **EX-1 Accounting** is the single dependency blocking operational maturity (Executive · PM HYBRID workflows · Financial visibility). Other dependencies improve specific surfaces but do not block platform maturity.

---

## §7 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero vendor recommendations made (per OMEGA scope) | ✅ |
| 11 dependencies strategy-classified | ✅ |
| Wave sequencing rendered (informational only) | ✅ |
| Constitutional posture stated per integration | ✅ |
| Blocking item (EX-1) explicitly identified | ✅ |

🛑 **STOPPED.**
