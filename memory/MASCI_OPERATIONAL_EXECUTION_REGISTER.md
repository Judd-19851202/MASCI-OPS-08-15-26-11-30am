# MASCI Operational Execution Register

## Purpose

This register permanently governs implementation sequencing for the Operational Work Foundation and all dependent execution systems.

Every implementation track is numbered.
Every track defines dependencies, evidence, and completion.
No downstream implementation may begin if its required upstream track is incomplete or uncertified.

---

## Track 1 · Operational Execution Constitution Lock

- **Purpose:** ratify the permanent constitutional governance for operational execution
- **Dependencies:** none
- **Prerequisites:** repository forensic understanding of current MASCI architecture
- **In Scope:** constitutional documents, zero-drift rules, ownership rules, certification rules
- **Out of Scope:** code, schemas, APIs, UI
- **Deliverables:** the five governing artifacts
- **Required testing:** document consistency review, ownership conflict review
- **Certification gate:** architecture governance review
- **Production evidence required:** none
- **Completion definition:** all five artifacts exist, are internally consistent, and define no duplicate systems
- **Future dependency chain:** prerequisite for every track below

## Track 2 · Company Cost Code Catalog Foundation

- **Purpose:** establish canonical enterprise cost-code catalog ownership and lifecycle
- **Dependencies:** Track 1
- **Prerequisites:** constitutional approval of cost-code philosophy
- **In Scope:** master catalog ownership, identifiers, versioning, project assignment model
- **Out of Scope:** financial ERP, accounting journal logic, estimating implementation
- **Deliverables:** canonical model, zero-drift mapping, certification criteria
- **Required testing:** ownership contract tests, search/export parity tests, version-history tests
- **Certification gate:** architecture + source-of-truth proof
- **Production evidence required:** catalog visibility, version lineage, search parity
- **Completion definition:** company catalog exists as the only master source for operational code references
- **Future dependency chain:** prerequisite for Tracks 3, 5, 6, 8, 10

## Track 3 · Project Cost Codes

- **Purpose:** define project-specific cost-code assignment without duplicating the company catalog
- **Dependencies:** Tracks 1, 2
- **Prerequisites:** canonical project spine and master catalog contract
- **In Scope:** project assignment, override restrictions, version traceability, read projections
- **Out of Scope:** financial actual costing engine
- **Deliverables:** project mapping authority, search/export/reporting behavior
- **Required testing:** project assignment integrity, historical reassignment safety, read-scope tests
- **Certification gate:** source-owner proof + no duplicate catalog logic
- **Production evidence required:** project read behavior across Daily Report/schedule/reconciliation surfaces
- **Completion definition:** project-specific cost-code use is traceable to the company catalog
- **Future dependency chain:** prerequisite for Tracks 5, 6, 8, 10

## Track 4 · Project Work Area Foundation

- **Purpose:** define canonical work-area structure for planning and execution
- **Dependencies:** Track 1
- **Prerequisites:** project identity lock
- **In Scope:** work-area identity, hierarchy, stationing, spatial extensions, field UX rules
- **Out of Scope:** GIS implementation, plan-room implementation
- **Deliverables:** work-area ownership rules, mutation rules, derived consumer rules
- **Required testing:** field usability, hierarchy integrity, project association tests
- **Certification gate:** simple-field-UX review + zero-drift review
- **Production evidence required:** use in Daily Report, schedule, reconciliation read surfaces
- **Completion definition:** work areas exist as the single spatial execution context
- **Future dependency chain:** prerequisite for Tracks 5, 6, 8, 10

## Track 5 · Operational Work Foundation

- **Purpose:** create the canonical planned work object for MASCI OPS
- **Dependencies:** Tracks 1, 2, 3, 4
- **Prerequisites:** job/project, cost-code, and work-area authority locked
- **In Scope:** work identity, lifecycle, ownership, constraints, dependency model, evidence rules
- **Out of Scope:** full advanced scheduling UI, AI scheduling, financial posting
- **Deliverables:** canonical operational work authority, mutation contract, history rules
- **Required testing:** ownership tests, lifecycle tests, audit tests, Trust Spine lifecycle tests
- **Certification gate:** zero-drift matrix conformance + search/trust/ODS integration proof
- **Production evidence required:** stable work IDs visible across consumers
- **Completion definition:** a single operational work model governs scheduling, reconciliation, and briefing inputs
- **Future dependency chain:** prerequisite for Tracks 6–11

## Track 6 · Daily Report Work-Item Integration

- **Purpose:** tie Daily Report actuals to canonical Operational Work without replacing Daily Report authority
- **Dependencies:** Tracks 1, 4, 5
- **Prerequisites:** work object + work-area contract
- **In Scope:** source linkage, actuals mapping, evidence classification, carry-forward relevance
- **Out of Scope:** rewriting Daily Report workflow
- **Deliverables:** work-item reference model inside Daily Report domain
- **Required testing:** exact field preservation, actuals linkage, history integrity, failed-submit survivability
- **Certification gate:** Daily Report trust + reconciliation readiness
- **Production evidence required:** linked Daily Reports remain operator-truthful and history-safe
- **Completion definition:** Daily Reports can contribute actuals to work-level reconciliation without losing daily field truth
- **Future dependency chain:** prerequisite for Tracks 7, 8, 9, 10

## Track 7 · Actual Production Projection Layer

- **Purpose:** derive operational production projections from verified Daily Report evidence
- **Dependencies:** Tracks 1, 5, 6
- **Prerequisites:** work linkage and unit/cost-code/work-area truth
- **In Scope:** projection rules, confidence rules, freshness rules, exception handling
- **Out of Scope:** forecast optimization and financial earned value
- **Deliverables:** canonical actual production projection rules
- **Required testing:** unit parity, quantity parity, stale-data handling, confidence classification
- **Certification gate:** verified-fact vs derived-value separation
- **Production evidence required:** projections trace back to source Daily Reports
- **Completion definition:** actual production can be consumed by reconciliation and briefing truthfully
- **Future dependency chain:** prerequisite for Tracks 8, 9, 10

## Track 8 · Rolling Two-Week Scheduling Engine

- **Purpose:** establish the canonical near-term schedule over Operational Work
- **Dependencies:** Tracks 1–7
- **Prerequisites:** work model, work areas, project cost-code linkage, Daily Report actuals integration
- **In Scope:** commitment layer, sequencing, blocked-work status, carry-forward state, ownership visibility
- **Out of Scope:** full CPM/Primavera-class engine, AI auto-scheduling
- **Deliverables:** canonical rolling schedule authority and publication rules
- **Required testing:** scope isolation, coexistence of multiple report instances, project/date isolation, history/publish tests
- **Certification gate:** preview schedule truth + production schedule publication proof
- **Production evidence required:** committed work survives read paths and feeds Daily Execution expectations
- **Completion definition:** the platform has one schedule authority for near-term operational commitments
- **Future dependency chain:** prerequisite for Tracks 9–11

## Track 9 · Weekly Reconciliation Engine

- **Purpose:** compare planned, committed, and actual work for operational recovery and learning
- **Dependencies:** Tracks 1, 5, 6, 7, 8
- **Prerequisites:** work, actuals, schedule, and source linkages complete
- **In Scope:** reconciliation statuses, root cause, variance, carry-forward, recovery actions, lessons learned
- **Out of Scope:** finance-grade cost variance and executive scorecard politics
- **Deliverables:** canonical reconciliation authority and evidence model
- **Required testing:** variance truth, ownership truth, blocked/partial/unplanned cases, audit history
- **Certification gate:** reconciliation evidence completeness + no fact drift
- **Production evidence required:** reconciliations trace to schedule + Daily Report + work source facts
- **Completion definition:** weekly reconciliation becomes the official close-the-loop engine
- **Future dependency chain:** prerequisite for Track 10

## Track 10 · Daily Company Operations Brief

- **Purpose:** create the canonical executive operational brief from verified and derived operational truth
- **Dependencies:** Tracks 1, 5, 6, 7, 8, 9
- **Prerequisites:** work, schedule, actuals, reconciliation, and trust rules complete
- **In Scope:** yesterday’s story, attention items, plan-vs-actual rollups, verified vs AI narrative separation
- **Out of Scope:** marketing communications, external reporting, investor storytelling
- **Deliverables:** briefing publication rules, fact provenance rules, confidence display rules
- **Required testing:** source traceability, AI separation, search/export parity, PDF/brief consistency
- **Certification gate:** executive brief truthfulness + trust/audit parity
- **Production evidence required:** brief references real operational evidence and remains reproducible
- **Completion definition:** one daily company brief becomes the executive operational truth surface
- **Future dependency chain:** prerequisite for Track 11

## Track 11 · Cross-Domain Operational Projections

- **Purpose:** project the Operational Work loop into Dispatch, Shop, Equipment, HR, Safety, QA/QC, Fleet, and Executive surfaces
- **Dependencies:** Tracks 1–10
- **Prerequisites:** canonical work, schedule, reconciliation, and briefing layers operational
- **In Scope:** projections only; no duplicate source systems
- **Out of Scope:** separate per-domain planning engines
- **Deliverables:** projection contracts and read/write authority boundaries per domain
- **Required testing:** read-scope, no duplicate ownership, projection freshness, search/trust parity
- **Certification gate:** zero-drift review across all consuming modules
- **Production evidence required:** consumers reference the same canonical work/schedule/reconciliation facts
- **Completion definition:** all major domains consume one operational execution chain without drift
- **Future dependency chain:** prerequisite for Track 12

## Track 12 · Full Operational Certification and Release Gate

- **Purpose:** establish production-grade certification for the full operational execution loop
- **Dependencies:** Tracks 1–11
- **Prerequisites:** preview-complete operational foundation
- **In Scope:** engineering certification, preview, production sanity, field acceptance, rollback criteria, audit/trust/search/ODS verification
- **Out of Scope:** unrelated feature roadmap items
- **Deliverables:** release gate implementation and evidence standards
- **Required testing:** full regression suite, field acceptance suite, source-lineage proof, deployment proof
- **Certification gate:** all constitutional statuses evidence-backed
- **Production evidence required:** live operator workflows and live executive brief proof
- **Completion definition:** the operational foundation is production-trusted and field-proven
- **Future dependency chain:** prerequisite for future optimization/enhancement waves only
