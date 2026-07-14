# MASCI Operational Execution Role and Ownership Matrix

## 1. Role Authority

This matrix defines what each role may read, create, modify, approve, publish, commit, reconcile, override, certify, delegate, transfer, and audit within the MASCI Operational Execution system.

No role may exceed the authority defined here.
No implementation may widen role authority without updating this matrix and the related constitutional references.

## 2. Legend

- **R** = read
- **C** = create
- **M** = modify
- **A** = approve
- **P** = publish
- **K** = commit / finalize
- **Q** = reconcile / run governed reconciliation action
- **O** = override within explicitly governed boundaries only
- **E** = escalate
- **U** = audit review / evidence review
- **T** = certification authority for the role’s governed acceptance lane
- **D** = delegate within bounded role authority only

## 3. Role Matrix

| Role | Operational Work | Schedule | Daily Report | Reconciliation | Brief | Schema / API Governance Input | Security Governance Input | KPI Governance Input | Trust Spine / Audit Review | Override Authority | Certification Authority | Ownership Transfer | Delegation | Conflict Resolution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Executive | R | R | R | R/A | R/A/P | review only, no direct engineering authority | review only, no direct implementation bypass | approves business KPI acceptance, not formulas by convenience | U | O only as governed business exception; cannot rewrite source facts | T for executive acceptance only | may approve ownership changes at business level, not perform source edits | D review authority only | final business deadlock escalator |
| Operations | R/C/M | R/C/M/A/P/K | R | R/C/M/A/P/Q | R/C/M/A/P | required reviewer for operational dependency/governance impacts | required reviewer for operational boundary impacts | required reviewer for operational KPI semantics | U | O within governed operations rules only; no constitutional override | T for operations release acceptance | may transfer operational ownership where policy allows | D within operations chain | resolves cross-project and cross-domain execution conflicts |
| Project Manager (PM) | R/C/M within project scope | R/C/M/A within project scope | R | R/C/M within project scope | R | input to project-scoped schema/API needs only | input to project-scope access and workflow boundaries | input to project KPI interpretation, not competing formula creation | U within scope | limited O within project scope; no override of constitutional or source-owner rules | contributes to certification evidence; not final platform authority | may request or approve scoped owner changes where policy allows | D within project staffing model | resolves project planning conflicts |
| Superintendent | R/C/M on field execution scope | R/C/M on field commitment contribution | R/C/M/K on Daily Reports they own | R/C/M contribution | R contribution | no direct schema/API authority; operational input only | input on field authorization and continuity risk | input on field KPI usability | U on scoped records | may override field sequencing inside governed scope only | contributes to field acceptance | may request field ownership transfer | D to foreman within policy | resolves field execution conflicts |
| Foreman | R/C/M on assigned work | R contribution | R/C/M/K on owned Daily Reports | R contribution | R | no | no direct authority; may report workflow risk | input on field KPI readability only | U on own records | no override beyond own entries and explicit field scope | field acceptance participant only | none | no general delegation authority | escalate to superintendent |
| Field Leadership | R/C/M on scoped work and field records where authorized | R/C/M contribution within scope | R/C/M/K on scoped field records where authorized | R contribution | R contribution | no direct schema/API authority; field-operability input only | input on mobile-first, continuity, and role boundary impacts | input on field KPI consumption only | U on own scope | no constitutional override | required participant in field acceptance where affected | may request scoped ownership changes only | D within bounded field workflows | escalate to superintendent / PM |
| Dispatcher | R on work affecting dispatch | R/C/M on dispatch projections only | R | R contribution | R contribution | input to dispatch API and event-contract impacts only | input to dispatch boundary and abuse-risk controls | input to dispatch KPI semantics only | U on dispatch actions | no override of source work or schedule authority | contributes to dispatch-related certification | none on source ownership | D dispatch tasks within dispatch workflow only | resolves dispatch resource conflicts |
| Shop | R on work affecting shop and PM readiness | R on schedule constraints | R | R contribution | R contribution | input only for shop/PM integration points | input on readiness boundaries and attachment visibility where relevant | input to maintenance KPI consumption only | U | no override of source work | contributes to shop/equipment certification evidence | none | D internal only | escalate readiness conflicts |
| Fleet | R on fleet/equipment impacts | R on fleet constraints | R | R contribution | R contribution | input only for fleet integration impacts | input on fleet visibility and authorization boundaries | input to fleet KPI semantics only | U | no override | contributes to fleet evidence | none | D internal only | escalate availability/safety conflicts |
| Equipment | R/C/M on equipment state only | R on schedule readiness | R | R contribution | R contribution | input only for asset integration impacts | input on asset authorization and attachment safety | input to utilization and uptime KPIs only | U | no override of Operational Work or schedule authority | contributes to resource certification | none | D internal only | resolve/escalate equipment assignment conflicts |
| Safety | R/C/M on safety source records | R on schedule blockers and stop-work constraints | R/C/M in safety workflows and safety-linked report facts where authorized | R/C/M on safety variance / root-cause sections | R/C/M safety brief contributions | required reviewer for safety schema/API implications where safety domain changes | required reviewer for safety access and stop-work boundaries | input to incident and safety KPI formulas | U | O only for governed safety stop-work and safety constraint authority | T for safety acceptance inside release gate | no source work ownership transfer | D safety review tasks within policy | resolves safety policy conflicts |
| QA/QC | R/C/M on QA/QC source records | R on quality blockers | R on report references | R/C/M on quality variance sections | R/C/M quality brief contributions | required reviewer for QA/QC domain impacts | input on quality evidence visibility and permissions | input to QA/QC KPI formulas | U | may block acceptance within QA/QC domain only; no broad override | T for QA/QC acceptance in release gate | none | D internal only | resolves quality evidence conflicts |
| HR | R on staffing and qualification context | R on qualification constraints | R | R contribution | R contribution | input only where people/qualification data is part of governed workflows | required reviewer for qualification visibility and eligibility boundaries | input to labor and qualification KPI definitions where HR-owned | U | no override of source work or schedule | T only for qualification/eligibility acceptance where required | may manage people-role eligibility, not work ownership | D within HR workflows | resolves qualification/eligibility conflicts |
| Survey | R/C/M on survey source evidence | R on survey blockers / area definitions | R contribution | R contribution | R contribution | input to work-area schema/API impacts only | input on survey evidence boundaries | no KPI formula authority unless explicitly survey-owned | U | no source override | contributes to work-area certification | none | D internal only | resolves survey-control conflicts |
| Training | R on qualification/training records | R on training constraints | R | R contribution | R contribution | no direct schema/API authority beyond training domain input | input on training visibility and compliance boundaries | input to training-readiness KPI semantics only | U | no override | contributes to readiness certification evidence | none | D internal only | escalate compliance/training conflicts |
| Accounting | R on cost-code outputs and operational reports | R | R | R on reconciliation outputs | R | review only where accounting-facing data contracts are impacted | review only for financial visibility boundaries | review only for accounting-consumed KPI parity | U | no override | no platform certification authority | none | none | escalate to operations / executive |
| Corporate Admin | R | R | R | R | R | no direct business-governance authority; administrative only | administers user/role system, not operational truth | no direct KPI authority | U | no direct operational override unless also acting in another governed role | no automatic certification authority | may manage administrative role assignments only | D for admin operations only | escalate to executive / system governance |
| System | append, validate, compute, project by rule | project, publish, and validate by rule | store/route by rule | compute/run by explicit rule | publish by explicit rule | enforces approved schema/API contracts only | enforces approved security boundaries only | computes KPI formulas exactly as approved | writes audit/trust evidence mechanically | no discretionary override | executes mechanical gates only, never business acceptance | no business ownership transfer | none | none |
| AI | suggest, summarize, classify only | suggest attention only | summarize, never source | summarize patterns, never decide | draft narrative, never verify | no schema/API authority | no security authority; must obey input/output boundaries | may assist explanation only, never redefine KPI formulas | attributed output only; no audit authority | no override | no certification authority | none | none | none |

## 4. Ownership Rules

### 4.1 Source Ownership Rule
The source-record owner decides source truth within the authorized domain.
No consumer role may silently overwrite source truth outside that authority.

### 4.2 Publication Rule
Reading a source record does not authorize publishing a derived operational artifact.
Approval and publication rights must be explicit and role-bounded.

### 4.3 Dashboard Rule
Seeing a dashboard does not authorize mutating the source records that feed it.

### 4.4 Briefing Rule
Contributing evidence to a brief does not grant authority to alter the source evidence or publish the executive brief.

## 5. Override Rules

### 5.1 Exceptional and Governed Only
Override authority is exceptional, bounded, auditable, and role-specific.

### 5.2 Override Never Means Source Erasure
No override may erase historical truth, remove audit lineage, or hide prior state.

### 5.3 Constitutional Override Prohibition
No business or operational role may override the Constitution itself through implementation convenience.

## 6. Ownership Transfer Rules

Ownership transfer must be:
- explicit
- authorized
- auditable
- historically preserved
- non-retroactive for already published evidence unless governed correction rules explicitly permit it

No cross-role ownership transfer may bypass authorization, audit, or project/company boundaries.

## 7. Delegation Rules

Delegation is role-bounded.
Delegated authority may never exceed delegator authority.
Delegated approvals and actions must remain attributable to the acting person and role.

Delegation may not create shadow authority.

## 8. Security and Authorization Rules by Role

### 8.1 Least Authority
Every role receives only the minimum read/write/approve/publish authority necessary for its governed duties.

### 8.2 Cross-Company / Cross-Project Isolation
No role may gain unauthorized access across company, project, or domain boundaries through dashboards, search, ODS, exports, attachments, AI, or debug endpoints.

### 8.3 Attachment Access
Roles may access attachments only through the governed visibility of the source record or publication that owns them.

## 9. Certification and Acceptance Rules

### 9.1 Certification Is Lane-Specific
Certification authority is lane-specific:
- executive acceptance is not engineering certification
- field acceptance is not release authorization
- domain acceptance is not constitutional authority
- system automation is not business certification

### 9.2 Required Participation
Where workflows impact field trust, Field Leadership / Superintendent / Foreman lanes must participate in acceptance.
Where workflows impact executive brief truth, Executive and Operations lanes must participate.
Where workflows impact safety or QA/QC authority, those roles must participate in acceptance.

## 10. Conflict Resolution Rules

1. Source-record owner decides source truth within authorized domain.
2. Cross-domain execution conflict escalates to Operations.
3. Safety stop-work conflict escalates immediately to Safety + Operations.
4. Executive resolves business-priority deadlock when operational governance cannot.
5. Constitutional conflict escalates to constitutional amendment; implementation may not proceed until resolved.

## 11. No Orphan Role Rule

For every governed feature, this matrix must be able to answer:
- which role creates it?
- which role owns it?
- which role approves it?
- which role publishes it?
- which role audits it?
- which role certifies it?
- which role resolves conflicts about it?

If any answer is missing, role governance is incomplete and implementation is blocked.