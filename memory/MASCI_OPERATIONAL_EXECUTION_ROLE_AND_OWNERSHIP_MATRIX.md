# MASCI Operational Execution Role and Ownership Matrix

## Authority Rule

This matrix defines what each role may read, create, modify, approve, publish, commit, reconcile, override, escalate, audit, certify, transfer, and delegate within the operational execution chain.

No implementation may widen a role’s authority without updating this matrix.

Legend:
- **R** = read
- **C** = create
- **M** = modify
- **A** = approve
- **P** = publish
- **K** = commit/finalize
- **Q** = reconcile
- **O** = override
- **E** = escalate
- **U** = audit review
- **T** = certification authority

## Role Matrix

| Role | Operational Work | Schedule | Daily Report | Reconciliation | Brief | Override | Audit | Certification | Ownership Transfer | Delegation | Conflict Resolution |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Executive | R | R | R | R/A | R/A/P | O (governed, exceptional) | U | T (executive acceptance only) | may approve ownership changes, not perform source edits directly | may delegate review authority | final business conflict escalator |
| Operations | R/C/M | R/C/M/A/P/K | R | R/C/M/A/P/K | R/C/M/A/P | O within operations governance | U | T for operations release acceptance | may transfer operational ownership where policy allows | yes | resolves cross-project execution conflicts |
| Project Manager (PM) | R/C/M on scoped work | R/C/M/A within project scope | R | R/C/M within project scope | R | limited O within project scope, no constitutional override | U within scope | participates in certification evidence, not final platform certification | may request/approve scoped owner changes | may delegate within staffing model | resolves project planning conflicts |
| Superintendent | R/C/M on field execution scope | R/C/M on field commitment layer | R/C/M/K on Daily Report facts they own | R/C/M contribution | R contribution | no platform override; may override field sequencing within scope | U on own scope | contributes to field acceptance | may request field ownership transfer | may delegate to foreman where policy allows | resolves field execution conflicts |
| Foreman | R/C/M on assigned work scope | R contribution | R/C/M/K for owned Daily Reports | R contribution | R | no override beyond own entries | U on own records | participates in field acceptance only | no transfer authority | none except crew assignments in workflow scope | escalate to superintendent |
| Dispatcher | R on work affecting dispatch | R/C/M on dispatch projection only | R | R contribution | R contribution | no override of source work | U on dispatch actions | contributes to dispatch-related certification | no source ownership transfer | may delegate operational dispatch tasks per dispatch workflow | resolves dispatch resource conflicts |
| Shop | R on work affecting shop/equipment | R on schedule constraints | R | R contribution | R contribution | no override of work source | U | contributes to equipment/shop certification | no source ownership transfer | internal shop delegation only | escalate equipment readiness conflicts |
| Fleet | R on fleet/equipment impacts | R on fleet constraints | R | R contribution | R contribution | no override | U | contributes to fleet evidence | no | internal delegation only | escalate availability/safety conflicts |
| Equipment | R/C/M on equipment state only | R on resource readiness | R | R contribution | R contribution | no override of operational work | U | contributes to resource certification | no | internal delegation only | escalate equipment assignment conflicts |
| Safety | R/C/M on safety source records | R on blocked-work/safety constraints | R/C/M on safety-related report facts in own workflows | R/C/M on safety variance/root cause sections | R/C/M safety brief contributions | O only on governed stop-work/safety constraints | U | T for safety acceptance within release gate | no source work ownership transfer | may delegate safety review tasks | resolves safety policy conflicts |
| QA/QC | R/C/M on quality source records | R on quality blockers | R on Daily Report references | R/C/M on quality variance | R/C/M quality brief contributions | no broad override; may block acceptance within QA/QC domain | U | T for QA/QC acceptance within release gate | no | internal delegation only | resolves quality evidence conflicts |
| Accounting | R on cost-code outputs and reports | R | R | R on reconciliation outputs | R | no override | U | no platform certification authority | no | no | escalate to operations/executive |
| HR | R on staffing/person qualification context | R on qualification constraints | R | R contribution | R contribution | no override of source work | U | T only for HR qualification acceptance where required | may manage people-role eligibility, not work ownership | yes within HR workflows | resolves qualification/eligibility conflicts |
| Survey | R/C/M on survey source evidence | R on survey blockers/area definitions | R contribution | R contribution | R contribution | no source work override | U | contributes to work-area certification | no | internal delegation only | resolves survey-control conflicts |
| Training | R on qualification/training records | R on training-related constraints | R | R contribution | R contribution | no override | U | contributes to readiness certification | no | internal delegation only | escalate compliance/training conflicts |
| Field Leadership | R/C/M on assigned operational scope | R/C/M contribution within scope | R/C/M/K on scoped field records where authorized | R contribution | R contribution | no constitutional override | U on own scope | required participant in field acceptance | no broad ownership transfer | limited within field workflows | escalate to superintendent/PM |
| Corporate Admin | R | R | R | R | R | no direct operational override unless also acting in another role under policy | U | no automatic certification authority | may administer user/role system, not source operations | yes for admin operations only | escalate to executive/system |
| System | append, compute, project, index | project and publish by rule | store/route by rule | compute by rule | publish by rule | no discretionary override | full audit logging | no business certification; only mechanical gate execution | no business ownership transfer | none | none |
| AI | suggest, summarize, classify | suggest attention, never own | summarize, never source | summarize patterns, never decide | draft narrative, never verify | no override | no audit authority, only attributed output | no certification authority | none | none | none |

## Detailed Responsibility Rules

### Executive
- may read every operational projection
- may approve or reject published briefs and reconciliations
- may not directly mutate Daily Report source facts as an executive convenience action

### Operations
- operational system owner for cross-project execution behavior
- may approve schedule publication and reconciliation publication
- may escalate and coordinate cross-domain conflicts

### PM
- owns project-level planning and commitment within authorized project scope
- may not create alternate staffing truth outside canonical project-team assignment rules

### Superintendent / Foreman / Field Leadership
- own field execution truth within assigned scope
- may commit Daily Report source facts they directly own
- may not silently publish executive narratives or final reconciliations

### Dispatch / Shop / Fleet / Equipment
- own their operational source domains only
- consume Operational Work and Schedule as projections, not replacement truth

### Safety / QA/QC / HR / Survey / Training
- own their own evidence domains
- may impose governed constraints or acceptance conditions where authorized
- may not duplicate schedule or Daily Report ownership

### System and AI
- System may automate transitions, projections, and validations only under explicit rules
- AI may never become a canonical owner

## Ownership Transfer Rules

- ownership transfer must be explicit
- ownership transfer must be auditable
- ownership transfer must preserve prior owner history
- transfer must not mutate historical published evidence retroactively
- no cross-role ownership transfer may bypass authorization and audit

## Delegation Rules

- delegation is role-bounded
- delegated authority must not exceed delegator authority
- delegated approvals must remain attributable to the acting role/person

## Conflict Resolution Rules

1. Source-record owner decides source truth within authorized domain
2. Cross-domain operational conflict escalates to Operations
3. Safety stop-work conflict escalates to Safety + Operations immediately
4. Executive resolves business-priority deadlock when operational governance cannot
5. Constitutional conflict escalates to architecture governance; code may not proceed until resolved
