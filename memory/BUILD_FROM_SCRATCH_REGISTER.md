# OMEGA · BUILD-FROM-SCRATCH REGISTER

**Date:** 2026-06-02 · Companion to `OPERATIONAL_REALITY_AUDIT.md`
**Mode:** READ-ONLY · zero code · zero design · zero estimates
**Definition:** Capabilities that are completely absent from ForgedOps today and would require greenfield construction (i.e., no existing primitive can be extended). External-dependency items are NOT included here (see `EXTERNAL_DEPENDENCY_REGISTER.md`).

---

## §0 · Greenfield-build items only

The Gap Register catalogues 48 gaps. Of those:
* **22 ABSENT items** are greenfield-build candidates → listed in §1
* **9 EXTERNAL items** are integration candidates → see `EXTERNAL_DEPENDENCY_REGISTER.md`
* **11 PARTIAL items** are completion candidates → not greenfield
* **4 CONSTITUTIONAL items** are re-scope candidates → not greenfield
* **2 TRIBAL items** are capture-as-data candidates → not greenfield

This document focuses on the 22 greenfield candidates plus a small number of items that emerge during the Reality Audit but are not yet in the Gap Register.

---

## §1 · Greenfield-build register · 24 items

For each item: target operational area · Constitutional posture · evidence-tier framing (per Amendment 001) · whether new collection required.

### Project Management greenfield (7 items)

| # | Capability | Area | Evidence-tier framing | New collection? |
|---:|---|---|---|---|
| B-1 | **Submittal workflow** | PM | Tier 1 — submission record · transmittal record · response · approval (all Tier 1 work content) | YES |
| B-2 | **RFI workflow** | PM | Tier 1 — question · response · resolution (all Tier 1 work content; never "I acknowledge RFI") | YES |
| B-3 | **Change-order workflow** | PM · Financial | Tier 1 — change request · pricing · approval · execution (all Tier 1 work · feeds GL) | YES |
| B-4 | **Pay-application workflow** | PM · Financial | Tier 1 — application · supporting docs · approval chain · payment (Tier 1 + GL integration) | YES |
| B-5 | **Lien-waiver tracking** | PM · Financial | Tier 1 — waiver received · type (partial/final · conditional/unconditional) · date · vendor (Tier 1 document with metadata) | YES |
| B-6 | **Meeting-minutes capture** | PM · Operations · Executive | Tier 1 — agenda · attendees (Tier 2) · decisions (Tier 1) · action items (Tier 1) | YES |
| B-7 | **Project budgeting + forecast-to-complete** | PM · Executive · Financial | Tier 1 — budget data · actuals from accounting integration · ETC (Tier 1 PM judgment) | YES |

### Field Operations greenfield (3 items)

| # | Capability | Area | Evidence-tier framing | New collection? |
|---:|---|---|---|---|
| B-8 | **Field clock-in/out per employee** | Field · HR | Tier 1 — clock-in IS work performed · device + GPS + time + project = Tier 1 evidence (never "I acknowledge I'm starting work") | YES |
| B-9 | **Production tracking by activity** | Field · PM · Executive | Tier 1 — quantity installed · activity code · date · crew · location (Tier 1 production data) | YES |
| B-10 | **Material delivery confirmation** | Field · PM · Operations | Tier 1 — receiving record · PO link · quantity · condition · receiver identity (Tier 1 receipt) | YES (extends PO Request workflow) |

### Executive / Operations greenfield (4 items)

| # | Capability | Area | Evidence-tier framing | New collection? |
|---:|---|---|---|---|
| B-11 | **Executive role + login portal + portfolio view** | Executive | Tier 1 — every executive surface must have an action affordance (Action Console pattern), not a read-only dashboard | NO (role + view layer) |
| B-12 | **Per-PM accountability scorecard** | Executive · Operations | Tier 1 — operational metrics derived from existing workflows (no new ack workflows) | NO (consumer of accountability_projection) |
| B-13 | **Backlog tracker / bid-pipeline integration** | Executive | Tier 1 — bid awarded · contract executed · backlog projection (Tier 1 events with operational consequence) | YES |
| B-14 | **Subcontractor management** | Operations · PM | Tier 1 — subcontractor entity · contract · scope of work · insurance · pay-app · close-out (Tier 1 lifecycle) | YES |

### Safety greenfield (3 items)

| # | Capability | Area | Evidence-tier framing | New collection? |
|---:|---|---|---|---|
| B-15 | **OSHA 300 / 301 / 300A generator** | Safety · Executive | Tier 1 — generator consumes incident lifecycle data; not a new ack workflow; produces the legally required artifact | NO (consumer of incidents + safety_training_records) |
| B-16 | **PPE Return workflow (OC-008)** | Safety · HR | Tier 1 — return IS the action · per item · per employee · reconciled against issuance | YES |
| B-17 | **Stop-work authority structured workflow** | Safety | Tier 1 — invocation record (who, when, what, why) + resolution record (Tier 1 decision content) · NOT a "I acknowledge stop-work authority" ack | YES |

### HR greenfield (3 items)

| # | Capability | Area | Evidence-tier framing | New collection? |
|---:|---|---|---|---|
| B-18 | **Performance review workflow** | HR | Tier 1 — review content captured as data (NOT a "I conducted review" checkbox) · cycle scheduled · trend tracked | YES |
| B-19 | **Discipline tracking workflow** | HR · Safety | Tier 1 — incident record per discipline event · type · response · resolution (Tier 1 operational content) | YES |
| B-20 | **`manager_employee_id` field on employees + FL users** | HR · Ownership | Tier 1 — not a workflow · a schema addition enabling Rule 8 escalation routing | NO (schema change · existing collections) |

### Equipment / Fleet greenfield (4 items)

| # | Capability | Area | Evidence-tier framing | New collection? |
|---:|---|---|---|---|
| B-21 | **Maintenance work-order system** | Equipment | Tier 1 — work-order opened · work performed · completion record (Tier 1 work · not an ack) | YES |
| B-22 | **Utilization-by-job tracking** | Equipment · PM · Financial | Tier 1 — equipment hours pinned to job · derived from Time Verification + DR + Pre-Op | NO (consumer of existing collections) |
| B-23 | **Driver Qualification File workflow** | Fleet · HR · Safety | Tier 1 — DQ file is a structured collection of required documents (CDL · medical · drug-test · MVR) · each item Tier 1 evidence | YES |
| B-24 | **DOT compliance dashboard** | Fleet · Executive | Tier 1 — Action Console consuming DQ files · DVIR · Fleet Defects · ELD integration data; every entry has an action affordance | NO (consumer view) |

---

## §2 · Cross-cutting greenfield observations

### 2.1 · 14 of 24 items require new collections; 10 are consumers of existing primitives

The platform's existing primitive set (state machine · audit trail · identity ladder · tasks · workflow_state_events · accountability_projection) can support 10 of 24 greenfield items as new views/routes/consumers rather than new collections. The 14 new collections are predominantly in PM and HR — areas Phase 1A deliberately did not touch.

### 2.2 · All 24 items can be designed Constitution-compliant

Per Amendment 001 framing applied above, every item can be scoped as Tier 1 work-performed evidence. None requires an acknowledgement workflow. The Constitutional Test ("What operational problem is solved by requiring this acknowledgement?") would return **NONE** for any ack-flavored version of these items.

### 2.3 · 4 items are foundation for ForgedOps v1 ownership model

* **B-11 Executive role + portfolio view** — supports Rule 3 (One Owner) at executive layer
* **B-12 Per-PM accountability scorecard** — consumer of Ownership Audit Layer C
* **B-20 `manager_employee_id`** — foundation for Rule 8 escalation routing
* **B-24 DOT compliance dashboard** — pattern for Action Console (anti-Dashboard)

These four interlock with the Ownership Audit §7 ForgedOps Ownership v1 recommendation.

### 2.4 · 3 items unblock Customer #2 readiness independently of tenant rebuild

* **B-11 Executive role** — applies cross-tenant
* **B-12 PM scorecard** — applies cross-tenant
* **B-15 OSHA log generator** — applies cross-tenant

Customer #2 architectural work (multi-tenancy + brand-config) is in a separate path; these items improve operability for any tenant.

---

## §3 · Items NOT classified as greenfield-build (for clarity)

These appeared in the Reality Audit but belong elsewhere:

| Item | Why not greenfield |
|---|---|
| **OC-005 JHP Ack Ledger** | Constitutional REPLACE per Amendment 001 — addressable via existing Toolbox Talk + JHP download identity capture |
| **OC-003 QA/QC follow-up** | PARTIAL — existing `qaqc_inspections` collection · needs completion · not greenfield |
| **OC-004 Site Inspection follow-up** | PARTIAL — same pattern |
| **OC-013/014 onboarding/offboarding** | PARTIAL · CONSTITUTIONAL re-scope per Amendment 001 (existing collections; need data-capture per step) |
| **Job costing / GL / AP / AR / pay processing** | EXTERNAL — accounting/ERP boundary · ForgedOps integrates, does not rebuild |
| **ELD / telematics / IFTA / drug-test vendor / MSDS** | EXTERNAL — domain-specific vendor systems |

---

## §4 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero solutions designed | ✅ |
| Zero estimates produced (per OMEGA scope) | ✅ |
| 24 greenfield items catalogued | ✅ |
| Every item framed by Amendment 001 Tier hierarchy | ✅ |
| Constitution-compliant framing demonstrated per item | ✅ |
| 4 ownership-v1 interlock items called out | ✅ |
| 3 Customer #2 cross-tenant items called out | ✅ |

🛑 **STOPPED.**
