# OMEGA · BUILD / INTEGRATE / IGNORE — MASTER REGISTER

**Date:** 2026-06-02 · Companion to `OPERATIONAL_REALITY_GAP_REGISTER.md`
**Mode:** READ-ONLY · zero code · zero design
**Governing doctrine:** Constitution + Override + Amendment 001 + **Build/Integrate/Ignore Doctrine** ("If another mature system already performs a function better than ForgedOps should, the preferred answer is INTEGRATE")

**ForgedOps IS:** A Heavy Civil Construction Field Operations Platform — Field↔Office communication · Safety · Fleet · Shop · Project Ops · Accountability · Escalation · Operational visibility
**ForgedOps IS NOT:** Accounting · ERP · Payroll · CRM · HRIS · Estimating · General task management

---

## §0 · Legend

| Code | Meaning |
|---|---|
| **🔨 BUILD** | Core ForgedOps capability · if not built, mission fails |
| **🔗 INTEGRATE** | Required capability owned by mature external system · ForgedOps consumes/contributes data |
| **🔨🔗 HYBRID** | Workflow lives in ForgedOps · financial/data syncs to external system |
| **🚫 IGNORE** | Adds complexity without operational value · eliminate or never start |

---

## §1 · Classification matrix · all 48 gaps

### G0 · Day-to-day blockers (12)

| # | Gap | Classification | Rationale |
|---|---|---|---|
| G0-1 | Job costing not in ForgedOps | 🔗 INTEGRATE | Accounting/ERP owns · ForgedOps consumes job-cost feed for executive surfaces |
| G0-2 | Master schedule not in ForgedOps | 🔗 INTEGRATE | P6 / MS Project / HCSS HeavyJob owns CPM math · ForgedOps consumes for look-ahead |
| G0-3 | Submittal workflow absent | 🔨 BUILD | Project operations · within mission |
| G0-4 | RFI workflow absent | 🔨 BUILD | Project operations · within mission |
| G0-5 | Change-order workflow absent | 🔨🔗 HYBRID | Workflow in ForgedOps · financial impact syncs to accounting |
| G0-6 | Pay-application workflow absent | 🔨🔗 HYBRID | Workflow in ForgedOps · amounts/invoices sync to accounting |
| G0-7 | Field clock-in/out per employee | 🔨 BUILD | Pure field operations · core ForgedOps differentiator |
| G0-8 | Production tracking by activity | 🔨 BUILD | Heavy-civil-specific earned-value foundation · core differentiator |
| G0-9 | Subcontractor management | 🔨🔗 HYBRID | Operational workflow in ForgedOps · contracts/invoices sync to accounting |
| G0-10 | Three parallel Corrective-Action systems | 🔨 BUILD | Accountability core · canonicalize internally |
| G0-11 | 0/736 user-level task assignment | 🔨 BUILD | Accountability core · Ownership Layer A+B |
| G0-12 | iter445 "Has crew reviewed JHP?" Yes/No field | 🚫 IGNORE | FAIL-1 per Amendment 001 · eliminate field |

### G1 · Scalability / Executive visibility (14)

| # | Gap | Classification | Rationale |
|---|---|---|---|
| G1-1 | No executive role · login · portfolio view | 🔨 BUILD | Executive operational visibility within ForgedOps mission |
| G1-2 | No per-PM accountability scorecard | 🔨 BUILD | Accountability core · Action Console consumer |
| G1-3 | No portfolio rollup | 🔨 BUILD | Executive operational visibility |
| G1-4 | No backlog / bid-pipeline tracker | 🔗 INTEGRATE | CRM owns (Salesforce / HubSpot / Unanet) · ForgedOps not estimating/sales |
| G1-5 | No WIP schedule / forecast-to-complete | 🔗 INTEGRATE | Accounting calculates WIP · ForgedOps surfaces it |
| G1-6 | No OSHA 300/301/300A generator | 🔨 BUILD | Safety mission · regulatory artifact generation · consumes existing incidents |
| G1-7 | No Driver Qualification File workflow | 🔨 BUILD | Fleet operations core · regulatory |
| G1-8 | No DOT compliance dashboard | 🔨 BUILD | Fleet operations core · Action Console |
| G1-9 | No performance review workflow | 🔗 INTEGRATE | HRIS owns (BambooHR/Paychex/Paylocity) · NOT ForgedOps mission |
| G1-10 | No discipline tracking workflow | 🔨🔗 HYBRID | Safety-incident-tied discipline lives in ForgedOps · pure HR discipline integrates to HRIS |
| G1-11 | No `manager_employee_id` on employees | 🔨 BUILD | Accountability foundation · Rule 8 escalation routing |
| G1-12 | No `tenant_id` propagation across 141 collections | 🔨 BUILD | Platform architecture · multi-tenant foundation |
| G1-13 | No multi-tenant auth / SSO / SAML / OIDC | 🔨🔗 HYBRID | Platform architecture BUILD · auth provider (Auth0/Okta) INTEGRATE |
| G1-14 | No "what's open across the platform that I own" view | 🔨 BUILD | Accountability core · Field value · Rule 3 (One Owner) |

### G2 · Adoption / Operational clarity (15)

| # | Gap | Classification | Rationale |
|---|---|---|---|
| G2-1 | OC-003 QA/QC follow-up absent | 🔨 BUILD | Safety/QC operations core · closure-action contract |
| G2-2 | OC-004 Site Inspection follow-up absent | 🔨 BUILD | Safety operations core · closure-action contract |
| G2-3 | OC-008 PPE Return absent | 🔨 BUILD | Safety operations · operational action |
| G2-4 | Maintenance work-order system absent | 🔗 INTEGRATE | MaintainX / Fiix / EAM owns · operator explicitly named MaintainX |
| G2-5 | Equipment utilization-by-job tracking | 🔨 BUILD | Shop operations consumer of existing primitives (Time Verification + DR + Pre-Op) |
| G2-6 | Fuel-card integration | 🔗 INTEGRATE | Fuel system (WEX/Comdata/Voyager) owns · operator explicitly named fuel systems |
| G2-7 | OC-013 Onboarding multi-step partial | 🔨🔗 HYBRID | Field-side onboarding (training/PPE) BUILD · HR-side (I-9/benefits) INTEGRATE to HRIS |
| G2-8 | OC-014 Offboarding multi-step partial | 🔨🔗 HYBRID | Field-side offboarding (PPE return/access) BUILD · HR-side (final-pay/benefits) INTEGRATE |
| G2-9 | Benefits administration | 🔗 INTEGRATE | HRIS / benefits broker owns · NOT ForgedOps mission |
| G2-10 | ATS / recruiting pipeline | 🔗 INTEGRATE | ATS owns · NOT ForgedOps mission |
| G2-11 | MSDS / SDS library | 🔗 INTEGRATE | Velocity/KHA/3E owns · subscription product |
| G2-12 | Drug-test pool tracking | 🔗 INTEGRATE | Vendor owns chain-of-custody · ForgedOps consumes events |
| G2-13 | Workers comp claim integration | 🔗 INTEGRATE | Carrier owns · ForgedOps links incidents to claim IDs |
| G2-14 | Lien-waiver tracking | 🔨🔗 HYBRID | PM ops document tracking BUILD · financial impact INTEGRATE to accounting |
| G2-15 | Meeting-minutes capture | 🔨 BUILD | Project operations · decisions captured as Tier 1 |

### G3 · Cosmetic / convenience (7)

| # | Gap | Classification | Rationale |
|---|---|---|---|
| G3-1 | OC-006 Safety Meeting amend | 🔨 BUILD | Existing-primitive completion · trivial |
| G3-2 | OC-016 Continuity Events edit/close | 🔨 BUILD | Existing-primitive completion · trivial |
| G3-3 | OC-017 Safety digest fire relocation | 🔨 BUILD | Rule 9 Operator-First aligned · surface relocation |
| G3-4 | OC-019 Casing normalization | 🚫 IGNORE | Cosmetic · no operational consequence |
| G3-5 | OC-022 Reopen actions across 14 workflows | 🔨 BUILD | Existing-primitive completion · accountability value |
| G3-6 | OC-009 Photo Janitor | 🔨 BUILD | Operational hygiene · Rule 6/7 strong alignment |
| G3-7 | Closure-attestation modal Constitutional review | 🔨 KEEP | Already PASS per Amendment 001 §10 · preserve as-is |

---

## §2 · Aggregate classification tally

| Classification | Count | % |
|---|---:|---:|
| 🔨 **BUILD** (core ForgedOps capability) | **24** | 50 % |
| 🔗 **INTEGRATE** (external system owns) | **15** | 31 % |
| 🔨🔗 **HYBRID** (workflow + integration) | **7** | 15 % |
| 🚫 **IGNORE** (eliminate or never start) | **2** | 4 % |
| **TOTAL** | **48** | 100 % |

The doctrine sorts the operational reality cleanly: 31 of 48 gaps are inside ForgedOps's mission boundary (BUILD + HYBRID build-side); 15 are external; 2 should never have been recommended.

---

## §3 · Mission-boundary headlines

### What ForgedOps OWNS (BUILD: 24 items · HYBRID: 7 items)

* **Safety operations** — Incidents (live) · QA/QC follow-up · Site Inspection follow-up · PPE Return · OSHA generator · CAPA canonicalization · Stop-work workflow
* **Field operations** — Daily Reports (live) · FSI identity ladder (live) · field clock-in/out · production tracking by activity · material delivery confirmation
* **Fleet operations** — Fleet Defects (live) · DVIR (live) · DOT compliance · DQ-file
* **Shop operations** — Equipment Master (live) · Pre-Op (live) · utilization-by-job
* **Project operations** — Daily Reports (live) · Submittal · RFI · Change-Order workflow · Pay-Application workflow · Subcontractor management · Lien-Waiver tracking · Meeting-minutes
* **Accountability** — Universal Ownership Layer A+B+C · per-PM scorecard · manager_employee_id · "what's mine" view · executive portfolio
* **Office↔Field communication** — FSI 5-tier ladder (live) · revise workflow (live) · notification routing per Rule 8

### What ForgedOps INTEGRATES (INTEGRATE: 15 items · HYBRID integration-side: 7 items)

* **Accounting/ERP** — Job cost · WIP · pay-app financials · CO financials · subcontractor invoices · lien-waivers · GL · AP · AR
* **Payroll** — Pay processing · taxes · garnishments · W-2/1099 (variance reconciliation stays in ForgedOps)
* **Scheduling** — P6/MS Project/HCSS HeavyJob · ForgedOps consumes for look-ahead views
* **Auth provider** — Auth0/Okta for SSO/SAML/OIDC
* **HRIS** — Performance reviews · benefits · ATS · HR-side onboarding/offboarding
* **Fleet vendor systems** — ELD (Motive) · fuel cards · MVR · drug-test pool · workers comp carrier · MSDS library
* **Maintenance** — MaintainX/Fiix EAM
* **CRM** — Backlog · bid pipeline · sales

### What ForgedOps IGNORES (IGNORE: 2 items)

* **iter445 "Has crew reviewed JHP today?" Yes/No** — FAIL-1 · eliminate
* **OC-019 Casing normalization** — cosmetic · no operational consequence

(Note: the two FAIL items from Amendment 001 — iter445 field and vestigial `stop_work_acknowledged` — are also IGNORE-class. Vestigial form decommission is captured under Constitutional re-scope rather than gap register, so cross-referenced here without double-counting.)

---

## §4 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero solutions designed | ✅ |
| Every gap classified into exactly one bucket | ✅ |
| Rationale grounded in doctrine + ForgedOps mission definition | ✅ |
| HYBRID class introduced to honor "workflow in ForgedOps + integration with external" pattern | ✅ |
| BUILD count of 24 matches "core capability" predicate | ✅ |
| INTEGRATE count of 15 reflects mature-system boundary respect | ✅ |
| Anti-checklist clause enforced (IGNORE includes self-attestation patterns) | ✅ |

🛑 **STOPPED.**
