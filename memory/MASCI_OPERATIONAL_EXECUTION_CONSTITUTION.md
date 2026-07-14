# MASCI Operational Execution Constitution

## 1. Authority

This document is the permanent constitutional authority governing the MASCI OPS Operational Work Foundation, Rolling Two-Week Scheduling System, Weekly Reconciliation Engine, and Daily Company Operations Brief.

No implementation track may contradict this constitution.
No implementation track may define a competing owner, competing identifier, competing lifecycle, or competing source of truth for an operational concept governed here.
Where the existing platform already has a canonical architecture, implementation must extend it rather than replace it.

This constitution is binding on:
- backend implementation
- frontend implementation
- reporting
- search
- ODS projections
- Trust Spine
- AI summaries
- exports
- PDFs
- notifications
- certification
- production deployment

## 2. Permanent Platform Philosophy

MASCI OPS is permanently governed by the following doctrine:

### 2.1 Field First
The field operator is the primary evidence creator. Architecture must reduce operator burden, preserve entered facts, and minimize workflow ambiguity.

### 2.2 Operations First
The platform exists to run construction operations, not to showcase tools. Every new capability must improve execution, coordination, recovery, reconciliation, or decision quality.

### 2.3 Mobile First
Every execution model must support mobile and tablet-first interaction. Field workflows must not depend on desktop-only complexity.

### 2.4 Trust First
Every fact must be explainable. Every derived projection must identify its source records. AI outputs must never masquerade as verified facts.

### 2.5 Production First
No architecture is considered complete until it is deployable, observable, certifiable, and survivable in production.

### 2.6 Continuity First
Operational truth must survive device changes, session changes, partial workflow failure, and delayed reconciliation.

### 2.7 Survivability First
Failures must degrade safely. No silent loss. No silent drift. No irreversible mutation without evidence and authorization.

### 2.8 One Platform
MASCI OPS is one operating system. Scheduling, Daily Reports, Dispatch, Shop, Equipment, Safety, HR, QA/QC, Executive, Search, Trust, ODS, and Briefing are projections of the same operational reality.

## 3. Eight Permanent Engineering Pillars

Every implementation governed by this constitution must be:

1. **Powerful** — supports real enterprise construction operations
2. **Simple** — usable with minimal training in the field
3. **Beautiful** — consistent with MASCI visual and interaction language
4. **Trusted** — auditable, explainable, verifiable
5. **Proven** — grounded in actual operational evidence
6. **Deployable** — buildable, releasable, supportable
7. **Durable** — no temporary architecture, no hidden drift, no disposable foundations
8. **Relentless Ownership** — every defect is repaired or formally owned

## 4. Done Means Done

No governed concept is complete until all of the following are defined:
- canonical owner
- canonical identifier
- single source of truth
- allowed mutations
- historical behavior
- derived consumers
- ODS behavior
- Trust Spine behavior
- audit behavior
- search behavior
- export/PDF behavior
- scheduling behavior
- reconciliation behavior
- briefing behavior
- certification behavior
- production evidence required

No implementation may hide missing decisions behind TODOs, placeholders, or implied future resolution.

## 5. Non-Negotiable Architectural Prohibitions

The following are permanently prohibited unless this constitution is formally revised:

- no duplicate scheduling engine
- no duplicate project registry
- no duplicate employee identity system
- no duplicate cost-code system
- no duplicate operational intelligence engine
- no duplicate notification engine
- no duplicate reporting engine
- no duplicate briefing engine
- no duplicate trust engine
- no duplicate search authority
- no duplicate audit chain
- no silent mutation of historical operational facts
- no AI-generated fact stored as if operator-verified fact
- no destructive deletion of evidence-bearing operational history without explicit policy and certification

## 6. Constitutional Scope

This constitution governs the lifecycle:

Operational Work Foundation  
→ Rolling Two-Week Schedule  
→ Daily Execution  
→ Daily Reports  
→ Operational Data Spine  
→ Weekly Reconciliation  
→ Daily Company Operations Brief  
→ Executive Decisions  
→ Updated Schedule

This is the canonical execution loop for MASCI OPS.

## 7. Core Domain Definitions

### 7.1 Job / Project
The job/project is the canonical operational container.

- canonical owner: `jobs_master`
- canonical identifier: `project_number`
- primary human label: `project_name`
- role context owner: `project_team_assignments`

Jobs/projects are not redefined inside scheduling, Daily Reports, Dispatch, or briefing.

### 7.2 Operational Work
Operational Work is the canonical planned unit of execution.

It is not a Daily Report.
It is not a Dispatch assignment.
It is not a PM work order.
It is not an HR record.

Operational Work represents the planned, owned, scheduleable, reconcilable unit of field execution tied to a job/project.

### 7.3 Rolling Two-Week Schedule
The Rolling Two-Week Schedule is the canonical near-term operational commitment layer.

It is a projection over Operational Work, not an independent source of truth.
It may sequence, group, commit, block, and carry forward Operational Work, but may not redefine the work object itself.

### 7.4 Daily Execution
Daily Execution is the factual record of what happened on a specific operating day.

Its primary field evidence source is the Daily Report workflow.
Daily Execution may include additional evidence from Dispatch, Shop, Equipment, Safety, QA/QC, and related modules, but no consumer may overwrite the Daily Report’s primary field facts without explicit provenance.

### 7.5 Daily Report
The Daily Report is the canonical operator-entered daily execution record for a job/project/date/report instance.

It is authoritative for:
- crew participation entered on that report
- crew time entered on that report
- equipment usage entered on that report
- production entries entered on that report
- constraints entered on that report
- notes, weather, and field narrative entered on that report

The Daily Report is not the planner of future work, but it is a canonical actuals source for reconciliation.

### 7.6 Weekly Reconciliation
Weekly Reconciliation is the canonical process for comparing planned work vs committed work vs actual work.

It must classify:
- planned
- committed
- actual
- partial
- blocked
- cancelled
- unplanned
- carry forward
- variance
- root cause
- lessons learned
- recovery actions

### 7.7 Daily Company Operations Brief
The Daily Company Operations Brief is the canonical executive operational narrative for the prior operating period.

It is a derived briefing artifact, never a primary source of fact.

It must clearly separate:
- verified facts
- derived metrics
- AI-assisted summaries
- unresolved/low-confidence signals

### 7.8 Cost Code Catalog
The company cost code catalog is the canonical enterprise cost-code reference library.
Project cost codes are scoped projections or assignments from that master catalog.

### 7.9 Work Area
Work Area is the canonical spatial execution context for Operational Work and Daily Execution.
It must support simple field use while remaining extensible for hierarchical, station-based, and future GIS/plan-room alignment.

## 8. Single Source of Truth Rules

### 8.1 Canonical Sources Already Present in MASCI
- jobs/projects: `jobs_master`
- project staffing and role assignment: `project_team_assignments`
- daily execution actuals: `daily_reports`
- PM operational maintenance schedules/work orders: PM engine routes
- dispatch operational movement state: dispatch lifecycle / dispatch command center sources
- trust lifecycle evidence: `trust_spine_events`
- global search visibility rules: `global_search`

### 8.2 Rule of Primacy
When multiple systems reference the same operational concept:
- one system owns the source record
- all others are derived consumers or scoped projections

### 8.3 Prohibited Drift
No module may create an alternate truth for:
- project identity
- person identity
- operational work identity
- report identity
- reconciliation verdict
- briefing fact source

## 9. Canonical Identifier Rules

### 9.1 Job / Project ID
- canonical: `project_number`
- display support: `project_name`

### 9.2 Person ID
- canonical: existing authenticated/profile identity already used by MASCI auth and role systems
- email and display name are secondary labels only

### 9.3 Daily Report ID
- canonical: immutable report `id` / `doc_id` issued at creation
- report instance context must include `project_number` + `report_date` + report-instance discriminator where applicable

### 9.4 Operational Work ID
- canonical: immutable work identifier issued once and reused across schedule, reconciliation, brief, search, trust, and audit

### 9.5 Reconciliation Record ID
- canonical: immutable reconciliation record keyed to the timebox + job scope + work scope being reconciled

### 9.6 Briefing Record ID
- canonical: immutable briefing publication identifier; briefing facts must reference their underlying source record IDs

## 10. Mutability Rules

### 10.1 Primary Source Records
Primary operational source records may be created and corrected under governed workflows, but historical truth must be preserved through audit and version history.

### 10.2 Derived Projections
Derived views must never mutate their primary source indirectly unless explicitly designed as the canonical editor for that source.

### 10.3 Published Artifacts
Published schedule views, reconciliations, and briefs are mutable only through governed lifecycle updates with historical trace.

### 10.4 AI Outputs
AI outputs are always derived. They are never canonical facts. They may suggest, summarize, rank, or draft, but they may not silently mutate verified records.

## 11. Historical Rules

### 11.1 Historical Preservation
All operationally significant state changes must preserve:
- prior state
- change time
- actor
- reason when applicable
- confidence/provenance

### 11.2 No Silent Reinterpretation
A historical Daily Report, reconciliation verdict, or executive brief may not be silently reinterpreted by newer logic without retaining the original version context.

### 11.3 Derived History
When a derived projection changes because upstream truth changed, the new projection must be traceable back to the upstream change.

## 12. Version Rules

Every governed concept must distinguish:
- source record version
- derived projection version
- published artifact version
- certification status version

Version identity must be explicit enough that production support can answer:
- what source facts existed?
- what derived logic ran?
- what publication was shown?
- what commit/build produced it?

## 13. Publication Rules

### 13.1 Schedule Publication
The Rolling Two-Week Schedule may be published only from canonical work + scope + ownership state.

### 13.2 Reconciliation Publication
Weekly Reconciliation may be published only when the evidence set, variance classification, and ownership are complete enough for truthful review.

### 13.3 Brief Publication
The Daily Company Operations Brief may be published only when verified facts and derived narrative are explicitly separated.

## 14. Derived Data Rules

Derived data includes:
- readiness indicators
- attention items
- status rollups
- coverage percentages
- plan-vs-actual summaries
- executive briefing narratives
- AI explanations

Derived data must always declare:
- upstream source owners
- freshness
- confidence level
- whether the value is verified, inferred, estimated, or AI-assisted

## 15. AI Rules

### 15.1 AI May Not Replace Source Truth
AI may summarize, classify, or draft, but AI may not replace operator-entered or system-verified operational facts.

### 15.2 AI Must Be Separated
Every AI contribution to schedule explanation, reconciliation explanation, or executive brief must be clearly marked as AI-derived.

### 15.3 Confidence Discipline
Low-confidence AI outputs must never be surfaced as authoritative operational facts.

## 16. Trust Rules

The Trust Spine is the canonical lifecycle proof layer for cross-workflow operational truthfulness.

Every governed workflow that creates or publishes operational truth must define:
- lifecycle stages
- correlation ID propagation
- status semantics (`ok`, `skipped`, `failed`)
- failure visibility

Missing expected Trust Spine stages must degrade certification truthfully.

## 17. ODS Rules

The Operational Data Spine is the canonical cross-domain read fabric for operational aggregation.

ODS is a consumer/projection layer.
ODS must not become an alternate write authority for source records.

ODS projections must carry:
- source owner
- source record ID
- freshness
- projection timestamp
- confidence/truth status where applicable

## 18. Audit Rules

Every material operational mutation must be auditable.

Audit minimums:
- actor
- timestamp
- source record ID
- workflow/module
- mutation type
- prior/new value or structured change summary
- correlation ID where applicable

## 19. Search Rules

Global Search is permission-safe and projection-based.

Search may index operational concepts only if:
- canonical owner is defined
- read-scope rules are defined
- indexed fields avoid sensitive payload leakage
- result labels truthfully identify the record type

Search does not create authority. Search reflects authority.

## 20. Certification Rules

No implementation track is complete until certification evidence proves:
- engineering behavior
- test behavior
- preview behavior
- production behavior when in scope
- field/device behavior when required
- trust and audit behavior

Permitted statuses are constitutionally closed-set:
- VERIFIED
- FAILED
- BLOCKED
- STALE
- NOT_YET_EXERCISED
- UNKNOWN

Unexecuted work must never be marked FAILED.
Unproven work must never be marked VERIFIED.

## 21. Production Rules

Production is the only environment that proves live operational trust.

Preview may prove implementation quality.
Preview may not overrule production evidence.

Production readiness requires:
- source lineage
- build lineage
- environment correctness
- production-safe observability
- rollback criteria
- operator-safe release communication

## 22. Scheduling Philosophy

Scheduling in MASCI OPS is not an isolated planning toy.
It is an operational commitment layer tied to actual execution and future executive decision-making.

The Rolling Two-Week Schedule must:
- sequence canonical Operational Work
- surface ownership
- surface constraints
- surface equipment/crew/material readiness
- feed Daily Execution expectations
- feed Weekly Reconciliation
- feed the Daily Company Operations Brief

Scheduling must remain operationally explainable, not mathematically opaque.

## 23. Reconciliation Philosophy

Reconciliation exists to close the loop between plan, commitment, execution, and learning.

Reconciliation is not blame accounting.
It is an operational truth engine for recovery, course correction, and briefing.

## 24. Executive Brief Philosophy

The Daily Company Operations Brief exists to tell yesterday’s operational story truthfully.

It must include, where evidence exists:
- crew activity
- projects worked
- production
- materials
- equipment
- dispatch
- transportation
- shop
- fleet
- safety
- QA/QC
- constraints
- weather
- delays
- missing reports
- coverage percentage
- plan vs actual
- leadership attention items
- wins
- failures

The brief must separate:
- verified facts
- calculated summaries
- AI narrative

## 25. Cost Code Philosophy

Cost code architecture must support:
- company master catalog
- project-specific cost-code assignment
- unit semantics
- quantity semantics
- work area linkage
- operational work linkage
- Daily Report linkage
- schedule linkage
- reconciliation linkage
- historical versioning

This constitution authorizes those foundations but does not authorize financial implementation drift or duplicate accounting systems.

## 26. Work Area Philosophy

Work Areas must be simple enough for field operators and rich enough for future hierarchy.

Work Areas must support:
- simple labels
- hierarchical breakdowns
- station ranges
- coordinate association
- future plan-room integration
- future GIS integration

Field burden must remain minimal.

## 27. Non-Goals

This constitution does not authorize:
- full financial ERP redesign
- alternate PM engine replacement
- alternate dispatch engine replacement
- alternate HR system
- alternate GIS platform
- alternate notification platform
- uncontrolled AI planning

## 28. Future Extensibility Philosophy

Future implementation may extend:
- work-type specialization
- resource planning sophistication
- work area richness
- executive briefing intelligence
- AI assistance
- spatial integration

But every extension must preserve:
- single source of truth
- canonical ownership
- historical traceability
- search safety
- trust truthfulness
- mobile-first field operability

## 29. Constitutional Self-Audit

This constitution is complete only if every downstream implementation can answer:
- what is the source record?
- who owns it?
- who may mutate it?
- who consumes it?
- how is history preserved?
- how is trust proven?
- how is it surfaced in search?
- how is it reconciled?
- how is it briefed?
- how is it certified?

If any implementation cannot answer those questions, it is constitutionally incomplete.
