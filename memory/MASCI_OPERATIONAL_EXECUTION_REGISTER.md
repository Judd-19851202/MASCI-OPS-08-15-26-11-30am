# MASCI Operational Execution Register

## 1. Register Authority

This register is the canonical implementation sequencing, dependency, and release-blocking authority for the MASCI Operational Execution build.

No downstream implementation may begin if its upstream constitutional, ownership, schema, API, lifecycle, certification, performance, security, concurrency, caching, offline, synchronization, or release prerequisites are unresolved.

This register must be read together with:
- `MASCI_OPERATIONAL_EXECUTION_CONSTITUTION.md`
- `MASCI_OPERATIONAL_EXECUTION_ZERO_DRIFT_MATRIX.md`
- `MASCI_OPERATIONAL_EXECUTION_ROLE_AND_OWNERSHIP_MATRIX.md`
- `MASCI_OPERATIONAL_EXECUTION_CERTIFICATION_PLAN.md`
- `MASCI_OPERATIONAL_EXECUTION_CONSTITUTIONAL_APPENDIX.md`

## 2. Register Integrity Rules

### REG-001 · One Track, One Authority Rule
Every track must contain one and only one authoritative value for each required field.

Repeated authoritative fields inside one track are prohibited.

### REG-002 · Required Track Fields
Every track must define exactly one authoritative value for:
- track_id
- purpose
- dependencies
- prerequisites
- constitutional_sections
- stable_requirement_ids
- in_scope
- out_of_scope
- existing_architecture_to_preserve
- deliverables
- prohibited_architecture
- entry_criteria
- exit_criteria
- release_blocking_conditions
- required_evidence
- owner_decisions
- completion_state

### REG-003 · No Implied Governance Rule
No track may rely on implied upstream behavior.
No track may defer constitutional questions to later coding.

### REG-004 · Register Integrity Certification Rule
Every track must be certifiable for:
- single authoritative field presence
- no duplicated field headings
- no conflicting track-level truth
- complete dependency expression
- complete constitutional traceability

## 3. Constitutional Sequence

Track order is binding.
No implementation may skip dependency validation.
Before each track begins, all upstream assumptions must be revalidated under the release sequencing rule in the Constitution and the Certification Plan.

## 4. Track 1 · Constitutional Lock and Governance Completion

- **track_id:** T1
- **purpose:** establish the complete constitutional foundation for the Operational Execution build
- **dependencies:** none
- **prerequisites:** repository-grounded understanding of MASCI’s current canonical systems, legacy boundaries, projection layers, role gates, and existing shared shell patterns
- **constitutional_sections:** Constitution §§1–27, Appendix §§1–11, Role Matrix, Zero-Drift Matrix, Certification Plan, manual GitHub/deployment boundary
- **stable_requirement_ids:** REG-001 through REG-007, FG-001 through FG-010, ID-001 through ID-046, EVT-001 through EVT-026, LIF-001 through LIF-094, KPI-001 through KPI-029, DASH-001 through DASH-022, NOTIF-001 through NOTIF-028, BRIEF-001 through BRIEF-017, SEC-001 through SEC-026, UX-001 through UX-030, DEPLOY-001 through DEPLOY-004
- **in_scope:** doctrine, ownership, identifiers, schema governance, API governance, performance governance, security governance, workflow dependency governance, state-machine governance, event governance, data-lineage governance, KPI governance, dashboard governance, notification governance, Daily Brief governance, AI governance, offline governance, synchronization governance, concurrency governance, caching governance, product identity governance, bilingual governance, accessibility governance, release governance, Five-Gate Release Governance, certification governance, manual GitHub/deployment boundary governance, appendix authority required to eliminate ambiguity
- **out_of_scope:** implementation code, runtime schema changes, endpoint implementation, UI implementation, background job implementation, deployment execution
- **existing_architecture_to_preserve:** current canonical project identity in `jobs_master`, staffing authority in `project_team_assignments`, Daily Report actual authority in `daily_reports`, existing notification ecosystem, existing shared portal shell/navigation, existing ODS read patterns, existing Trust/audit append-only patterns, existing domain authorities in Dispatch, Transportation, Shop, Equipment/Fleet, Safety, QA/QC, HR, Training, Search, Backup/Recovery
- **deliverables:** six normative constitutional artifacts plus `MASCI_OPERATIONAL_EXECUTION_ARTIFACT_VERIFICATION.md`
- **prohibited_architecture:** duplicate work engine, duplicate schedule engine, duplicate brief engine, duplicate notification engine, duplicate KPI formulas by portal, duplicate Trust proof chain, duplicate ODS write authority, duplicate search authority, alternate deployment authority, prompt-driven GitHub/deployment claims
- **entry_criteria:** governance remediation track approved; constitutional defects CAG-001 through CAG-012 confirmed
- **exit_criteria:** no unresolved constitutional gap remains across the seven governing documents; no orphan requirement remains; no cross-document contradiction remains; owner acceptance pending
- **release_blocking_conditions:** any unresolved owner, lifecycle, identifier, publication rule, dashboard authority, executive reporting authority, notification authority, briefing authority, scheduling authority, reconciliation authority, Trust Spine rule, ODS rule, AI rule, search rule, audit rule, security rule, API rule, schema rule, migration rule, release rule, performance rule, scalability rule, concurrency rule, caching rule, offline rule, synchronization rule, manual GitHub/deployment boundary rule, failure-mode rule, or constitutional conflict
- **required_evidence:** cross-document traceability map, stable identifier catalog, lifecycle catalog, event envelope, KPI/dashboard contracts, notification contract, Daily Brief contract, security contract, product identity contract, manual deployment boundary contract, Five-Gate governance traceability report, skipped-test classification contract, verification document
- **owner_decisions:** none required for constitutional completeness if all defects are repaired; only post-amendment owner acceptance is required
- **completion_state:** AMENDED — OWNER ACCEPTANCE REQUIRED BEFORE FINAL CONSTITUTIONAL VERIFICATION

## 5. Track 2 · Canonical Company Cost Code Catalog Foundation

- **track_id:** T2
- **purpose:** define the canonical enterprise cost-code catalog and remove all future ambiguity about cost-code authority
- **dependencies:** T1
- **prerequisites:** accepted constitutional package; stable identifier catalog; security boundary contract; product identity contract
- **constitutional_sections:** Constitution §§7, 9, 10, 11, 13, 14, 18, 22, 23, 24, 25; Appendix §§4, 5, 6, 8
- **stable_requirement_ids:** CC-001 through CC-030, ID-007, ID-008, ID-009, SEC-006, EVT-001, KPI-001
- **in_scope:** company cost-code source identity, schema contract, API contract, lifecycle, alias contract, migration, search, ODS, KPI linkage, notification suppression, export safety
- **out_of_scope:** accounting ledger postings, ERP redesign, invoice logic
- **existing_architecture_to_preserve:** existing read-only cost-code provider and routes, existing project-facing cost-code reads, existing project identity contract
- **deliverables:** canonical company cost-code authority with identifier, lifecycle, security, API, and certification contracts
- **prohibited_architecture:** project-local master catalogs, free-text code truth, frontend-owned code formulas, duplicate code alias systems
- **entry_criteria:** T1 accepted
- **exit_criteria:** one company cost-code truth source with governed alias and migration behavior
- **release_blocking_conditions:** duplicate catalog authority, missing migration rules, undefined alias handling, unresolved lifecycle, unresolved security/search/ODS behavior
- **required_evidence:** schema/API/security/performance certification, identifier proof, search parity, historical compatibility proof
- **owner_decisions:** none unless company policy changes cost-code publication rights
- **completion_state:** blocked until T1 owner acceptance

## 6. Track 3 · Project Cost Codes

- **track_id:** T3
- **purpose:** define project-scoped cost-code assignment without duplicating the company catalog
- **dependencies:** T1, T2
- **prerequisites:** accepted cost-code foundation, accepted project identity and staffing authority
- **constitutional_sections:** Constitution §§7, 9, 10, 11, 13, 14, 18, 22, 24, 25; Appendix §§5, 8
- **stable_requirement_ids:** PCC-001 through PCC-025, ID-010, SEC-007, EVT-002
- **in_scope:** project cost-code identity, alias handling, assignment rules, API contract, lifecycle, search/ODS mapping, permissions, history, migration
- **out_of_scope:** financial posting, billing logic, accounting journal logic
- **existing_architecture_to_preserve:** existing project number identity, cost-code provider read surface, project scoping rules
- **deliverables:** one project cost-code assignment authority with stable IDs and alias lineage
- **prohibited_architecture:** project-specific duplicate master code systems, fuzzy text-based cross-domain code matching
- **entry_criteria:** T2 accepted
- **exit_criteria:** project code usage is traceable to company catalog and project assignment identity
- **release_blocking_conditions:** alternate project catalog, unresolved lifecycle, unresolved alias rules, unresolved migration/security behavior
- **required_evidence:** assignment integrity proof, API contract proof, role-bound mutation proof, search/export parity
- **owner_decisions:** none unless business requires project-only alias policy beyond governed default
- **completion_state:** blocked until upstream acceptance

## 7. Track 4 · Project Work Areas

- **track_id:** T4
- **purpose:** define the canonical spatial execution context for planning and execution
- **dependencies:** T1
- **prerequisites:** accepted constitutional identity rules and project identity authority
- **constitutional_sections:** Constitution §§7, 9, 10, 11, 13, 14, 15, 21, 22, 24, 25; Appendix §§2, 4, 8
- **stable_requirement_ids:** WA-001 through WA-025, ID-012, EVT-003, LIF-020, SEC-008
- **in_scope:** work-area identity, hierarchy, lifecycle, merge/split lineage, search behavior, ODS behavior, permissions, mobile selector rules
- **out_of_scope:** GIS replacement, survey platform replacement
- **existing_architecture_to_preserve:** existing project linkage, existing survey and project intelligence boundaries, existing shared selector patterns
- **deliverables:** one work-area authority with stable lineage and field-safe UX governance
- **prohibited_architecture:** free-text location truth replacing canonical work-area identity
- **entry_criteria:** T1 accepted
- **exit_criteria:** one spatial execution context authority exists for planning and execution
- **release_blocking_conditions:** duplicate area authority, unresolved hierarchy lineage, unresolved merge/archive rules, unresolved mobile accessibility behavior
- **required_evidence:** field selector proof, hierarchy integrity proof, migration compatibility proof, accessibility/mobile proof
- **owner_decisions:** none unless business requires special survey-only states beyond constitutional default
- **completion_state:** blocked until upstream acceptance

## 8. Track 5 · Operational Work Foundation

- **track_id:** T5
- **purpose:** create the canonical planned work object for MASCI OPS
- **dependencies:** T1, T2, T3, T4
- **prerequisites:** accepted identifiers, role authority, security boundaries, lifecycle catalog, event envelope
- **constitutional_sections:** Constitution §§6–25; Appendix §§2, 3, 4, 5, 7, 8
- **stable_requirement_ids:** OW-001 through OW-050, ID-014, EVT-004, LIF-001, SEC-010, KPI-002, DASH-003
- **in_scope:** work identity, schema, API, state machine, split/merge/defer/cancel/close/reopen rules, dependency model, audit, Trust, search, ODS, readiness links, notification eligibility
- **out_of_scope:** CPM solver replacement, speculative AI planning engine, finance posting
- **existing_architecture_to_preserve:** project identity, staffing, cost-code and area boundaries, shared RBAC model, shared shell and selectors
- **deliverables:** one canonical Operational Work truth object with full lineage, lifecycle, and event contract
- **prohibited_architecture:** task-title-based identity, duplicate work collections, dashboard-owned work truth
- **entry_criteria:** T2–T4 accepted
- **exit_criteria:** one work authority exists for schedule, actual linkage, reconciliation, and briefing
- **release_blocking_conditions:** duplicate work identity, undefined split/merge rules, undefined event propagation, undefined mutation rights, undefined migration path
- **required_evidence:** lifecycle certification, event certification, security certification, mobile selector proof, lineage proof
- **owner_decisions:** none unless business later changes work split/merge policy defaults
- **completion_state:** blocked until upstream acceptance

## 9. Track 6 · Daily Report Work Integration

- **track_id:** T6
- **purpose:** connect Daily Report actuals to canonical Operational Work without weakening Daily Report authority
- **dependencies:** T1, T4, T5
- **prerequisites:** accepted Daily Report actual authority, Operational Work authority, identifier catalog, offline/sync governance
- **constitutional_sections:** Constitution §§7, 9, 11, 14, 15, 16, 17, 22, 24, 25; Appendix §§2, 3, 7, 8
- **stable_requirement_ids:** DRI-001 through DRI-040, ID-019, ID-020, EVT-005, LIF-003, SEC-012
- **in_scope:** work references on reports, actual linkage, idempotent updates, offline/reconnect rules, duplicate-submit handling, source lineage, stale linkage behavior
- **out_of_scope:** Daily Report workflow replacement, historical report redesign
- **existing_architecture_to_preserve:** `daily_reports` actual authority, existing Daily Report resilience and continuity patterns, existing PDF/export truth rules
- **deliverables:** governed link between report actuals and planned work with preserved field truth
- **prohibited_architecture:** Daily Report mutation through schedule/work projections, future-plan rewrite from actuals
- **entry_criteria:** T5 accepted
- **exit_criteria:** Daily Reports contribute actuals to work truth without losing source integrity
- **release_blocking_conditions:** report fact drift, duplicate source authority, unresolved continuity behavior, undefined stale-link rules
- **required_evidence:** continuity certification, duplicate-submit/idempotency proof, lineage proof, role-bound edit proof
- **owner_decisions:** none
- **completion_state:** blocked until upstream acceptance

## 10. Track 7 · Canonical Actual Production Projection

- **track_id:** T7
- **purpose:** derive operational production projections from verified Daily Report evidence and linked work context
- **dependencies:** T1, T5, T6
- **prerequisites:** accepted actuals linkage, KPI constitution, projection security and stale-state rules
- **constitutional_sections:** Constitution §§12, 16, 18, 19, 20, 22, 24, 25; Appendix §§3, 4, 5, 8
- **stable_requirement_ids:** AP-001 through AP-035, ID-021, EVT-006, KPI-003, DASH-004, SEC-013
- **in_scope:** derived actual projection rules, freshness, confidence, stale handling, KPI linkage, dashboard semantics, queue/recompute behavior
- **out_of_scope:** forecast optimization, AI-owned production truth
- **existing_architecture_to_preserve:** ODS read patterns, Daily Report source facts, existing projection/read-only doctrine
- **deliverables:** one governed actual production projection authority with lineage and KPI contracts
- **prohibited_architecture:** dashboard-specific production formulas, AI-invented production values
- **entry_criteria:** T6 accepted
- **exit_criteria:** actual production is consumable across reconciliation and briefing with source traceability
- **release_blocking_conditions:** hidden calculations, KPI drift, unresolved stale-state handling, unresolved projection lineage
- **required_evidence:** KPI certification, lineage proof, stale cache proof, role-safe visibility proof
- **owner_decisions:** none
- **completion_state:** blocked until upstream acceptance

## 11. Track 8 · Rolling Two-Week Schedule

- **track_id:** T8
- **purpose:** establish the canonical near-term commitment engine over Operational Work
- **dependencies:** T1, T5, T6, T7
- **prerequisites:** accepted work, actual, KPI, event, role, and lifecycle contracts
- **constitutional_sections:** Constitution §§6, 7, 9, 11, 14, 15, 16, 17, 19, 22, 24, 25; Appendix §§2, 3, 4, 8
- **stable_requirement_ids:** SCH-001 through SCH-050, ID-015, ID-016, ID-017, EVT-007, LIF-010, SEC-014, DASH-005
- **in_scope:** schedule activity, schedule window, publication/version, revision, carry-forward, blocked status, commit/publish lifecycle, role-bounded editing, history preservation
- **out_of_scope:** long-range CPM replacement, uncontrolled AI auto-scheduling
- **existing_architecture_to_preserve:** existing dispatch/shop/readiness domain boundaries, existing shared shell and board patterns, existing project scope rules
- **deliverables:** one near-term schedule authority for commitment and publication with versioned history
- **prohibited_architecture:** duplicate local schedule systems, silent schedule rewrite from downstream actuals, frontend-owned scheduling truth
- **entry_criteria:** T7 accepted
- **exit_criteria:** schedule commitment and publication are canonical, versioned, and reconcilable
- **release_blocking_conditions:** competing schedule authority, ambiguous publication semantics, unresolved schedule window lifecycle, unresolved event propagation
- **required_evidence:** lifecycle certification, publication/version proof, concurrency proof, mobile board proof, history retention proof
- **owner_decisions:** none unless business later changes delegation policy for field commit proposals
- **completion_state:** blocked until upstream acceptance

## 12. Track 9 · Weekly Reconciliation

- **track_id:** T9
- **purpose:** compare planned, committed, and actual work for truth, learning, and recovery
- **dependencies:** T1, T5, T6, T7, T8
- **prerequisites:** accepted plan/actual boundary, KPI contract, event envelope, lifecycle rules
- **constitutional_sections:** Constitution §§7, 14, 15, 16, 17, 18, 19, 22, 24, 25; Appendix §§2, 3, 4, 5, 8
- **stable_requirement_ids:** REC-001 through REC-045, ID-022, ID-023, EVT-008, LIF-004, SEC-015, KPI-004, DASH-006
- **in_scope:** reconciliation identity, variance, root cause, responsibility distinction, recovery action, carry-forward, unplanned work, publication, history, role-bounded review
- **out_of_scope:** finance-grade cost variance engine, punitive ranking systems
- **existing_architecture_to_preserve:** Daily Report actual truth, schedule publication history, root-cause non-blame doctrine
- **deliverables:** one reconciliation authority for plan-vs-actual classification and recovery insight
- **prohibited_architecture:** retroactive plan fabrication, silent erasure of prior published plan, root cause as automatic personal blame
- **entry_criteria:** T8 accepted
- **exit_criteria:** reconciliation becomes canonical close-the-loop authority
- **release_blocking_conditions:** hidden calculations, missing evidence lineage, unresolved root-cause ownership, unresolved publication lifecycle
- **required_evidence:** source-lineage proof, publication history proof, KPI parity, role-bound approval proof
- **owner_decisions:** none
- **completion_state:** blocked until upstream acceptance

## 13. Track 10 · Domain Projections

- **track_id:** T10
- **purpose:** project canonical execution truth into Dispatch, Transportation, Shop, Equipment/Fleet, Safety, HR, QA/QC, PM, and Executive surfaces without duplicating ownership
- **dependencies:** T1 through T9
- **prerequisites:** accepted source authorities, Zero-Drift rows, role matrix, notification contract, security contract
- **constitutional_sections:** Constitution §§7, 13, 14, 16, 19, 21, 22, 24, 25; Appendix §§3, 4, 6, 8
- **stable_requirement_ids:** DOM-001 through DOM-050, EVT-009 through EVT-014, SEC-016 through SEC-024, DASH-007 through DASH-015, NOTIF-001 through NOTIF-012
- **in_scope:** cross-domain event consumption, projections, read surfaces, dashboards, notifications, search and ODS propagation, domain-specific action queues
- **out_of_scope:** duplicate per-domain planning engines, source-ownership takeover by projections
- **existing_architecture_to_preserve:** existing dispatch lifecycle, transportation foundations, PM command center, shop/equipment/fleet/safety/QA/QC/HR authorities, executive intelligence read-only doctrine, existing notification rails, global search, existing portal shell and navigation
- **deliverables:** cross-domain consumption without duplicate truth or orphan features
- **prohibited_architecture:** separate brief engine, separate notification engine, separate search truth, separate ODS truth, portal-specific KPI formulas
- **entry_criteria:** T9 accepted
- **exit_criteria:** all declared consumers use canonical upstream truth through governed projection contracts
- **release_blocking_conditions:** hidden consumers, undocumented event propagation, duplicate domain authority, unresolved notification/search/ODS rules
- **required_evidence:** read-scope proof, event-map proof, search parity, notification dedupe proof, dashboard mission proof
- **owner_decisions:** none unless specific business escalation audiences require policy confirmation
- **completion_state:** blocked until upstream acceptance

## 14. Track 11 · Daily Company Operations Brief

- **track_id:** T11
- **purpose:** create the canonical daily executive operational publication from verified and derived operational truth
- **dependencies:** T1 through T10
- **prerequisites:** accepted brief contract, KPI contract, event envelope, domain projection coverage, product identity contract, bilingual/accessibility contract
- **constitutional_sections:** Constitution §§7, 16, 18, 19, 20, 21, 22, 24, 25; Appendix §§2, 3, 4, 5, 6, 8
- **stable_requirement_ids:** BRIEF-001 through BRIEF-017, ID-025, ID-026, EVT-015, LIF-061 through LIF-068, KPI-010, DASH-016, NOTIF-013, SEC-025
- **in_scope:** brief identity, reporting window, source coverage, lifecycle, versioning, revisioning, late-data behavior, distribution, evidence drill-down, fact/derived/AI separation
- **out_of_scope:** duplicate intelligence engine, marketing communications, unsupported storytelling systems
- **existing_architecture_to_preserve:** executive intelligence read-only principles, existing PDF/export/email boundaries, existing MASCI shell and bilingual patterns, existing notification rails
- **deliverables:** one canonical brief contract and publication authority with versioned history and source coverage truth
- **prohibited_architecture:** polished certainty over incomplete data, duplicate executive publication engines, AI-owned brief truth
- **entry_criteria:** T10 accepted
- **exit_criteria:** one governed executive brief engine exists with complete lifecycle and coverage truth
- **release_blocking_conditions:** AI fact drift, hidden calculations, unresolved publication authority, incomplete coverage handling, duplicate briefing authority
- **required_evidence:** source coverage proof, revision history proof, late-data handling proof, bilingual labeling proof, PDF/email parity proof
- **owner_decisions:** none unless business later changes recipient groups or material-change threshold policy
- **completion_state:** blocked until upstream acceptance

## 15. Track 12 · Cross-Cutting Hardening

- **track_id:** T12
- **purpose:** harden the full operational execution foundation across search, ODS, Trust, notifications, security, performance, backup/recovery, accessibility, and translation
- **dependencies:** T1 through T11
- **prerequisites:** accepted domain and brief authorities, accepted product identity and deployment boundary contracts
- **constitutional_sections:** Constitution §§12, 13, 17, 19, 21, 22, 23, 24, 25; Appendix §§3, 6, 7, 8
- **stable_requirement_ids:** HARD-001 through HARD-040, SEC-026 through SEC-040, KPI-020, DASH-020, NOTIF-020, DEPLOY-001 through DEPLOY-010
- **in_scope:** hardening of role gates, search scope, notification suppression, backup/recovery coverage, performance protections, mobile/accessibility parity, translation parity, no-noise rules
- **out_of_scope:** unrelated feature expansion, duplicate infrastructure programs
- **existing_architecture_to_preserve:** existing backup and recovery patterns, existing notification ecosystem, existing search architecture, existing portal shell and i18n infrastructure
- **deliverables:** cross-cutting hardening proof without duplicate engines
- **prohibited_architecture:** feature creep disguised as hardening, new notification/search/backup engines without constitutional amendment
- **entry_criteria:** T11 accepted
- **exit_criteria:** cross-cutting protections are fully governed and certifiable
- **release_blocking_conditions:** unresolved search scope, unresolved backup/recovery coverage, unresolved accessibility parity, unresolved translation gaps, unresolved performance guards
- **required_evidence:** negative authorization tests, backup/recovery readiness proof, mobile/iPad/desktop accessibility proof, translation coverage proof
- **owner_decisions:** none
- **completion_state:** blocked until upstream acceptance

## 16. Track 13 · Production Certification and Field Acceptance

- **track_id:** T13
- **purpose:** establish the mandatory Five-Gate release-governance path through immutable candidate, deployed verification, operational acceptance, and truthful closeout
- **dependencies:** T1 through T12
- **prerequisites:** accepted constitutional package; all prior implementation tracks completed locally and certified for their scope
- **constitutional_sections:** Constitution §§5, 21, 22, 23, 24, 25, 27; Certification Plan entire; manual GitHub/deployment boundary contract
- **stable_requirement_ids:** FG-001 through FG-010, DEPLOY-011 through DEPLOY-020, CERT-001 through CERT-040
- **in_scope:** contract lock evidence, local engineering verification, independent adversarial certification, immutable release candidate verification, deployed operational acceptance, GitHub handoff status separation, preview verification, production verification, field acceptance, executive acceptance, final operational closeout, rollback triggers, source/build/environment verification
- **out_of_scope:** automated GitHub publish by Emergent, automated deployment by Emergent
- **existing_architecture_to_preserve:** existing deployment health checks, existing backup/recovery readiness patterns, existing preview/production distinction
- **deliverables:** complete manual handoff and certification governance for Jaymn-controlled save and deployment actions
- **prohibited_architecture:** prompts instructing Emergent to push/deploy, local work misrepresented as GitHub or deployment work, preview misrepresented as production, production misrepresented as field acceptance
- **entry_criteria:** T12 accepted; `CONTRACT_LOCKED` achieved; implementation complete for governed scope
- **exit_criteria:** all five release-governance gates are unambiguous, separately evidenced, correctly ordered, and non-overlapping
- **release_blocking_conditions:** any missing Five-Gate milestone, missing GitHub/deployment boundary, missing status separation, unresolved rollback ownership, unresolved independent adversarial lane, unresolved immutable candidate identity, unresolved deployed operational acceptance lane, or unresolved field/executive acceptance lane when in scope
- **required_evidence:** milestone evidence chain, contract-lock evidence, local verification evidence, independent adversarial evidence, immutable release-candidate evidence, GitHub confirmation evidence when applicable, preview evidence, production evidence, field acceptance evidence, executive acceptance evidence
- **owner_decisions:** Jaymn alone performs physical GitHub save/publish and physical preview/production deployment
- **completion_state:** blocked until Jaymn executes manual actions and applicable acceptance lanes are VERIFIED

## 17. Dependency Enforcement Rules

### REG-005 · Hard Dependency Rule
No track may begin if its dependencies are incomplete, uncertified, or constitutionally contradictory.

### REG-006 · Revalidation Rule
Before any track starts, dependencies must be rechecked for:
- schema assumptions
- API assumptions
- lifecycle assumptions
- KPI assumptions
- event assumptions
- search assumptions
- ODS assumptions
- security assumptions
- performance assumptions
- concurrency assumptions
- caching assumptions
- offline assumptions
- synchronization assumptions
- product identity assumptions
- manual GitHub/deployment boundary assumptions
- release assumptions

### REG-007 · No Rework-by-Neglect Rule
If a track would force redesign of an already accepted upstream track due to missing governance, that downstream track is blocked until constitutional correction occurs.

## 18. Register-Level No-Orphan Rule

No track deliverable may be approved unless it answers, for every major feature within that track:
- Who creates it?
- Who owns it?
- Who consumes it?
- What updates because of it?
- What reports on it?
- What dashboard displays it?
- What audit trail records it?
- What Trust Spine events are emitted?
- What search indexes it?
- What certification validates it?

If any answer is unresolved, the track remains blocked.

## 19. Manual GitHub and Deployment Boundary

### DEPLOY-001 · Manual Save Authority Rule
ONLY JAYMN MAY PHYSICALLY SAVE OR PUBLISH CHANGES TO GITHUB.

### DEPLOY-002 · Manual Deployment Authority Rule
ONLY JAYMN MAY PHYSICALLY DEPLOY PREVIEW OR PRODUCTION.

### DEPLOY-003 · Emergent Prohibited Action Rule
Emergent may not push, publish, save to GitHub, deploy preview, deploy production, or claim those manual actions occurred.

### DEPLOY-004 · Allowed Emergent Action Rule
Emergent may inspect, implement locally, run tests, create evidence, prepare a clean handoff, verify GitHub only after Jaymn confirms he saved, verify preview only after Jaymn confirms he deployed preview, and verify production only after Jaymn confirms he deployed production.

## 20. Workflow Milestone Set

The following Five-Gate milestones are mandatory workflow markers and do
not replace certification statuses:
- CONTRACT_LOCKED
- LOCAL_ENGINEERING_VERIFIED
- INDEPENDENT_ADVERSARIAL_CERTIFIED
- IMMUTABLE_RELEASE_CANDIDATE_VERIFIED
- DEPLOYED_OPERATIONAL_ACCEPTANCE_VERIFIED
- DONE

Supporting workflow markers may coexist, but they do not overrule the
Five-Gate sequence:
- GOVERNANCE_DOCUMENTED
- LOCAL_IMPLEMENTATION_COMPLETE
- LOCAL_TESTS_VERIFIED
- READY_FOR_JAYMN_GITHUB_SAVE
- JAYMN_GITHUB_SAVE_CONFIRMED
- GITHUB_SOURCE_VERIFIED
- READY_FOR_JAYMN_PREVIEW_DEPLOYMENT
- JAYMN_PREVIEW_DEPLOYMENT_CONFIRMED
- PREVIEW_VERIFIED
- READY_FOR_JAYMN_PRODUCTION_DEPLOYMENT
- JAYMN_PRODUCTION_DEPLOYMENT_CONFIRMED
- PRODUCTION_VERIFIED
- FIELD_ACCEPTANCE_VERIFIED
- EXECUTIVE_ACCEPTANCE_VERIFIED
- FINAL_OPERATIONAL_CLOSEOUT

Each milestone must also carry one permitted certification status from
the Certification Plan. `DONE` may appear only when the five
release-governance milestones above are all VERIFIED in order.