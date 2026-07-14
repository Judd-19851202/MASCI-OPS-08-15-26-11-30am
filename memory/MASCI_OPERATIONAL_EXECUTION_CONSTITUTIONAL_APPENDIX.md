# MASCI Operational Execution Constitutional Appendix

## 1. Appendix Authority

This appendix is a mandatory part of the MASCI Operational Execution constitutional set.

It exists because the core governing artifacts require normative catalogs to eliminate ambiguity around:
- stable identifiers
- lifecycle/state-machine rules
- event envelopes and event vocabulary
- KPI and dashboard contracts
- notification contracts
- Daily Company Operations Brief contract
- offline, synchronization, caching, and concurrency authority
- MASCI product identity and bilingual/accessibility rules
- manual GitHub and deployment boundary milestones

This appendix does not create a parallel constitution.
It supplies the normative detail that the Constitution, Register, Zero-Drift Matrix, Role Matrix, and Certification Plan require.

## 2. Stable Identifier Catalog

### 2.1 Identifier Rules
- **ID-001** Display name is never a stable identifier.
- **ID-002** Email is never the lifetime professional identity.
- **ID-003** Project name is never project identity.
- **ID-004** Cost-code text alone is never project-cost-code identity.
- **ID-005** Activity title is never Operational Work identity.
- **ID-006** Work-area label is never Work Area identity.
- **ID-007** Fuzzy text matching may assist discovery only; it may never replace stable cross-domain linkage.
- **ID-008** Human-readable codes may be retained as labels while immutable identifiers govern relationships.
- **ID-009** Historical records retain snapshots of labels and codes without severing stable IDs.
- **ID-010** Split and merge operations create lineage; they never reuse prior IDs.

### 2.2 Identifier Catalog

| Requirement ID | Concept | Canonical Field Name | Data Type | Issuer / Owner | Uniqueness Scope | Immutable | Human Readable | Externally Exposed | Labels May Change | Tenant Scope | Project Scope | Migration / Legacy Rule |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ID-011 | Organization / Tenant | `tenant_id` | string | platform/company authority | global | yes | yes | yes | name may change, id may not | tenant root | n/a | legacy single-tenant defaults must map explicitly |
| ID-012 | Person / Professional | `person_id` | string | identity authority | tenant | yes | no | controlled | display labels may change | tenant | optional | email/name aliases map to person_id only |
| ID-013 | Employee / Company Membership | `membership_id` | string | HR/company membership authority | tenant | yes | no | controlled | employment labels may change | tenant | optional | historical memberships preserved |
| ID-014 | Project | `project_id` | string | project authority | tenant | yes | no | controlled | project labels may change | tenant | n/a | if absent in legacy, governed mapping required |
| ID-015 | Project Number | `project_number` | string | `jobs_master` | tenant | yes while project exists | yes | yes | human label around it may change | tenant | n/a | remains canonical exposed project reference |
| ID-016 | Project Team Assignment | `assignment_id` | string | `project_team_assignments` | tenant | yes | no | controlled | role labels may change | tenant | project | legacy roster rows must map to assignment_id |
| ID-017 | Company Cost-Code Catalog Item | `company_cost_code_id` | string | company cost-code authority | tenant | yes | yes optional | yes | description may change | tenant | n/a | legacy code text must map explicitly |
| ID-018 | Project Cost Code | `project_cost_code_id` | string | project cost-code authority | tenant+project | yes | yes optional | yes | aliases/description may change | tenant | project | project alias must not replace id |
| ID-019 | Cost-Code Alias | `cost_code_alias_id` | string | cost-code alias authority | tenant+project or tenant | yes | yes | controlled | alias text may change | tenant | optional | alias retains lineage to canonical code ids |
| ID-020 | Unit | `unit_id` | string | unit governance authority | global/tenant as governed | yes | yes | yes | label may change | tenant if extended | optional | canonical unit codes remain stable |
| ID-021 | Work Area | `work_area_id` | string | work-area authority | tenant+project | yes | no | controlled | area labels may change | tenant | project | merge/split lineage preserved |
| ID-022 | Operational Work | `operational_work_id` | string | Operational Work authority | tenant | yes | no | controlled | titles may change | tenant | project | split/merge creates child/replacement lineage |
| ID-023 | Schedule Activity | `schedule_activity_id` | string | schedule authority | tenant | yes | no | controlled | activity title may change | tenant | project | revisions preserve lineage |
| ID-024 | Schedule Window | `schedule_window_id` | string | schedule authority | tenant+project+timebox | yes | no | controlled | labels may change | tenant | project | revised windows retain linkage |
| ID-025 | Schedule Publication / Version | `schedule_publication_id` | string | schedule publication authority | tenant | yes | yes optional | controlled | display version label may change format, id may not | tenant | project | publication lineage preserved |
| ID-026 | Schedule Revision | `schedule_revision_id` | string | schedule authority | tenant | yes | no | controlled | reason label may change | tenant | project | revisions never overwrite prior ids |
| ID-027 | Resource Demand | `resource_demand_id` | string | owning source domain | tenant | yes | no | controlled | labels may change | tenant | project | demand rows retain source lineage |
| ID-028 | Resource Conflict | `resource_conflict_id` | string | conflict evaluation authority | tenant | yes | no | controlled | labels may change | tenant | project | conflict history preserved |
| ID-029 | Constraint | `constraint_id` | string | constraint authority | tenant | yes | no | controlled | title may change | tenant | project | supersession creates linkage, not reuse |
| ID-030 | Readiness Evaluation | `readiness_evaluation_id` | string | readiness authority | tenant | yes | no | controlled | labels may change | tenant | project | evaluations remain attributable by version |
| ID-031 | Daily Report | `daily_report_id` | string | `daily_reports` | tenant | yes | yes optional doc ref | controlled | title/date labels may change | tenant | project | doc_id and source ids preserved together |
| ID-032 | Daily Report Work Item | `daily_report_work_item_id` | string | Daily Report authority | tenant | yes | no | controlled | description may change by amendment/version | tenant | project | report item lineage retained across amendments |
| ID-033 | ODS Fact / Projection | `ods_projection_id` | string | ODS authority | tenant | yes | no | controlled | labels may change | tenant | project optional | projection versions preserve source ids |
| ID-034 | Reconciliation | `reconciliation_id` | string | reconciliation authority | tenant | yes | no | controlled | labels may change | tenant | project | published runs retain ids and successors |
| ID-035 | Carry-Forward Linkage | `carry_forward_id` | string | schedule/reconciliation authority | tenant | yes | no | controlled | n/a | tenant | project | links prior and successor work/activity ids |
| ID-036 | Executive Attention Item | `executive_attention_item_id` | string | executive attention authority | tenant | yes | no | controlled | titles may change | tenant | project optional | dismissed/resolved history preserved |
| ID-037 | Daily Company Operations Brief | `brief_id` | string | brief authority | tenant | yes | no | controlled | section labels may change, id may not | tenant | optional multi-project | brief versions retain parent brief id |
| ID-038 | Brief Version / Revision | `brief_revision_id` | string | brief authority | tenant | yes | no | controlled | version label may change format | tenant | optional | revisions preserve lineage |
| ID-039 | Event | `event_id` | string | event authority | tenant | yes | no | controlled | no | tenant | optional | append-only |
| ID-040 | Correlation | `correlation_id` | string | workflow authority | workflow scope | yes | no | controlled | no | tenant | optional | reused across related events only |
| ID-041 | Causation | `causation_id` | string | workflow authority | event chain scope | yes | no | controlled | no | tenant | optional | points to causal event or trigger |
| ID-042 | Notification | `notification_id` | string | notification authority | tenant | yes | no | controlled | content may change by locale; id may not | tenant | optional | retries preserve same logical notification lineage per policy |
| ID-043 | Evidence / Attachment Reference | `evidence_ref_id` | string | source-record authority | tenant | yes | no | controlled | filename/label may change | tenant | optional | storage key lineage preserved |
| ID-044 | Audit Record | `audit_record_id` | string | audit authority | tenant | yes | no | controlled | no | tenant | optional | append-only |
| ID-045 | Trust Event | `trust_event_id` | string | Trust Spine authority | tenant | yes | no | controlled | no | tenant | optional | append-only |
| ID-046 | Certification Artifact | `certification_artifact_id` | string | certification authority | tenant | yes | no | controlled | labels may change | tenant | optional | historical evidence preserved |

## 3. Canonical Lifecycle Catalog

### 3.1 Lifecycle Rules
- **LIF-001** Every lifecycle is closed-set.
- **LIF-002** Direct state mutation outside permitted transitions is prohibited.
- **LIF-003** Every transition requires actor, timestamp, event emission, audit visibility, and concurrency behavior.
- **LIF-004** Terminal states cannot be exited without explicit reopen or supersession rule.
- **LIF-005** Split/merge/revision/supersession must preserve lineage.

### 3.2 Operational Work Lifecycle
- **Requirement IDs:** LIF-010 through LIF-019
- **States:** DRAFT, READY, COMMITTED, IN_EXECUTION, BLOCKED, DEFERRED, SPLIT, MERGED, COMPLETED, CLOSED, CANCELLED, SUPERSEDED, ARCHIVED
- **Entry criteria:** work identity created; minimum required project/code/area links present for DRAFT
- **Exit criteria:** downstream conditions satisfied for target state
- **Permitted transitions:**
  - DRAFT → READY, CANCELLED
  - READY → COMMITTED, DEFERRED, CANCELLED
  - COMMITTED → IN_EXECUTION, BLOCKED, DEFERRED, CANCELLED, SPLIT, SUPERSEDED
  - IN_EXECUTION → COMPLETED, BLOCKED, SPLIT, MERGED, SUPERSEDED
  - BLOCKED → READY, COMMITTED, CANCELLED
  - DEFERRED → READY, CANCELLED
  - COMPLETED → CLOSED, REOPENED via governed reopen path only
  - CLOSED → REOPENED only by governed role and evidence
  - SPLIT → SUPERSEDED
  - MERGED → SUPERSEDED
  - CANCELLED → ARCHIVED
  - SUPERSEDED → ARCHIVED
  - CLOSED → ARCHIVED
- **Prohibited transitions:** DRAFT → COMPLETED, CANCELLED → COMMITTED, ARCHIVED → active states
- **Transition owner:** Operational Work authority
- **Propose-only roles:** PM, Superintendent, Foreman, Field Leadership where scoped
- **Approval-required roles:** PM or Operations Leadership for COMMITTED/CANCELLED/CLOSED/REOPENED/SUPERSEDED as governed
- **System-derived transitions:** none unless explicitly event-driven and auditable
- **Required reason/evidence:** split, merge, defer, cancel, reopen, supersede require explicit reason; split/merge require quantity and lineage evidence
- **Trust mapping:** CREATED, COMMITTED, STARTED, BLOCKED, UNBLOCKED, PARTIALLY_COMPLETED, COMPLETED, REOPENED, SUPERSEDED, CANCELLED, CLOSED
- **Special lineage rule:** split/merge must preserve original id references, child/replacement ids, quantity conservation, schedule lineage, actual linkage, reconciliation linkage, and no double counting

### 3.3 Schedule Activity Lifecycle
- **Requirement IDs:** LIF-020 through LIF-027
- **States:** OPEN_FOR_PLANNING, DRAFT, UNDER_REVIEW, READY_TO_PUBLISH, PUBLISHED, REVISED, SUPERSEDED, RECONCILING, CLOSED, CANCELLED
- **Permitted transitions:** OPEN_FOR_PLANNING → DRAFT; DRAFT → UNDER_REVIEW/CANCELLED; UNDER_REVIEW → READY_TO_PUBLISH/DRAFT; READY_TO_PUBLISH → PUBLISHED/DRAFT; PUBLISHED → REVISED/RECONCILING/SUPERSEDED; REVISED → READY_TO_PUBLISH/PUBLISHED; RECONCILING → CLOSED/REVISED; CLOSED → REVISED by governed successor only
- **Prohibited transitions:** PUBLISHED → DRAFT directly, SUPERSEDED → active states, CLOSED → PUBLISHED without revision lineage
- **Transition owner:** schedule authority
- **Approval-required roles:** PM/Operations per schedule publication policy
- **Trust mapping:** CREATED, REVIEW_REQUESTED, REVIEWED, COMMITTED, PUBLISHED, REVISED, SUPERSEDED, RECONCILED, CLOSED, CANCELLED

### 3.4 Schedule Window Lifecycle
- **Requirement IDs:** LIF-028 through LIF-035
- **States:** OPEN_FOR_PLANNING, DRAFT, UNDER_REVIEW, READY_TO_PUBLISH, PUBLISHED, REVISED, SUPERSEDED, RECONCILING, CLOSED
- **Permitted transitions:** OPEN_FOR_PLANNING → DRAFT; DRAFT → UNDER_REVIEW; UNDER_REVIEW → READY_TO_PUBLISH/DRAFT; READY_TO_PUBLISH → PUBLISHED; PUBLISHED → REVISED/RECONCILING/SUPERSEDED; REVISED → READY_TO_PUBLISH/PUBLISHED; RECONCILING → CLOSED/REVISED; CLOSED terminal unless successor window created
- **Required reason/evidence:** REVISED, SUPERSEDED, CLOSED require reason; RECONCILING requires linked actual/reconciliation context
- **Notification impact:** publication/revision may generate schedule-change notifications through governed contract only

### 3.5 Daily Report Lifecycle
- **Requirement IDs:** LIF-036 through LIF-042
- **States:** LOCAL_DRAFT, SERVER_DRAFT, SUBMITTED, REVISED, APPROVED, FINALIZED, SUPERSEDED
- **Permitted transitions:** LOCAL_DRAFT → SERVER_DRAFT; SERVER_DRAFT → SUBMITTED; SUBMITTED → REVISED/APPROVED/FINALIZED where approval model exists; REVISED → SUBMITTED; APPROVED → FINALIZED/SUPERSEDED; FINALIZED → SUPERSEDED only by governed correction version
- **Transition owner:** Daily Report authority
- **Approval-required roles:** governed approver role only where approval model exists
- **Special rule:** PMs may not rewrite submitted Daily Report actuals; revisions create version lineage
- **Trust mapping:** CREATED, SUBMITTED, REVIEW_REQUESTED, APPROVED, REVISED, SUPERSEDED

### 3.6 Weekly Reconciliation Lifecycle
- **Requirement IDs:** LIF-043 through LIF-048
- **States:** DRAFT, RUNNING, UNDER_REVIEW, PUBLISHED, REOPENED, SUPERSEDED, CANCELLED
- **Permitted transitions:** DRAFT → RUNNING/CANCELLED; RUNNING → UNDER_REVIEW/CANCELLED; UNDER_REVIEW → PUBLISHED/RUNNING; PUBLISHED → REOPENED/SUPERSEDED; REOPENED → UNDER_REVIEW; SUPERSEDED terminal; CANCELLED terminal
- **Required evidence:** publication/reopen/supersede require rationale and source coverage evidence

### 3.7 Constraint Lifecycle
- **Requirement IDs:** LIF-049 through LIF-055
- **States:** IDENTIFIED, VALIDATING, OPEN, OWNER_ASSIGNED, ACTION_IN_PROGRESS, WAITING_EXTERNAL, AT_RISK, BLOCKING, MITIGATED, RESOLVED, VERIFIED_CLOSED, CANCELLED, SUPERSEDED
- **Permitted transitions:** IDENTIFIED → VALIDATING/OPEN; VALIDATING → OPEN/CANCELLED; OPEN → OWNER_ASSIGNED/BLOCKING/CANCELLED/SUPERSEDED; OWNER_ASSIGNED → ACTION_IN_PROGRESS/WAITING_EXTERNAL/BLOCKING; ACTION_IN_PROGRESS → MITIGATED/AT_RISK/BLOCKING/WAITING_EXTERNAL; WAITING_EXTERNAL → ACTION_IN_PROGRESS/AT_RISK/BLOCKING; BLOCKING → ACTION_IN_PROGRESS/MITIGATED/RESOLVED; MITIGATED → RESOLVED/BLOCKING; RESOLVED → VERIFIED_CLOSED/REOPENED via governed successor; CANCELLED terminal; SUPERSEDED terminal
- **Approval-required roles:** owning domain plus operations/safety when a hold/block exists
- **Notification impact:** only BLOCKING, AT_RISK, VERIFIED_CLOSED transitions may trigger notification evaluation

### 3.8 Executive Attention Item Lifecycle
- **Requirement IDs:** LIF-056 through LIF-060
- **States:** OPEN, ACKNOWLEDGED, OWNER_ASSIGNED, ACTION_IN_PROGRESS, MONITORING, RESOLVED, CLOSED, DISMISSED_WITH_REASON
- **Permitted transitions:** OPEN → ACKNOWLEDGED/OWNER_ASSIGNED/DISMISSED_WITH_REASON; ACKNOWLEDGED → OWNER_ASSIGNED/ACTION_IN_PROGRESS; OWNER_ASSIGNED → ACTION_IN_PROGRESS/MONITORING; ACTION_IN_PROGRESS → MONITORING/RESOLVED; MONITORING → ACTION_IN_PROGRESS/RESOLVED/CLOSED; RESOLVED → CLOSED/REOPENED by governed successor; DISMISSED_WITH_REASON terminal

### 3.9 Daily Company Operations Brief Lifecycle
- **Requirement IDs:** LIF-061 through LIF-068
- **States:** DATA_WINDOW_OPEN, PRELIMINARY, GENERATED, UNDER_REVIEW, PUBLISHED, REVISED, FINAL, SUPERSEDED
- **Permitted transitions:** DATA_WINDOW_OPEN → PRELIMINARY; PRELIMINARY → GENERATED; GENERATED → UNDER_REVIEW/REVISED; UNDER_REVIEW → PUBLISHED/REVISED; PUBLISHED → FINAL/REVISED/SUPERSEDED; REVISED → GENERATED/UNDER_REVIEW/PUBLISHED; FINAL → SUPERSEDED only by governed successor

### 3.10 Dispatch Assignment Lifecycle
- **Requirement IDs:** LIF-069 through LIF-072
- **States:** CREATED, ASSIGNED, EN_ROUTE, ON_SITE, PARTIALLY_COMPLETED, COMPLETED, CANCELLED, REASSIGNED
- **Trust mapping:** CREATED, ASSIGNED, REASSIGNED, STARTED, PARTIALLY_COMPLETED, COMPLETED, CANCELLED

### 3.11 PM Work Order Lifecycle
- **Requirement IDs:** LIF-073 through LIF-076
- **States:** DRAFT, SCHEDULED, ACTIVE, BLOCKED, COMPLETED, CANCELLED, ARCHIVED

### 3.12 Notification Lifecycle
- **Requirement IDs:** LIF-077 through LIF-080
- **States:** ELIGIBLE, QUEUED, SENT, DELIVERED, VIEWED, FAILED, RETRIED, SUPPRESSED, EXPIRED, RESOLVED

### 3.13 ODS Projection / Background Job Lifecycle
- **Requirement IDs:** LIF-081 through LIF-085
- **States:** PENDING, RUNNING, SUCCEEDED, FAILED, RETRIED, STALE, SUPERSEDED, SKIPPED

### 3.14 Readiness Evaluation Lifecycle
- **Requirement IDs:** LIF-086 through LIF-089
- **States:** PENDING, EVALUATED, BLOCKED, VERIFIED, SUPERSEDED

### 3.15 Certification Artifact Lifecycle
- **Requirement IDs:** LIF-090 through LIF-094
- **States:** DRAFT, COLLECTING_EVIDENCE, READY_FOR_REVIEW, VERIFIED, FAILED, STALE, SUPERSEDED, ARCHIVED

## 4. Canonical Event Envelope and Vocabulary

### 4.1 Event Envelope Contract
- **EVT-001** `event_id` required
- **EVT-002** `event_type` required
- **EVT-003** `event_version` required
- **EVT-004** `tenant_id` required
- **EVT-005** `project_id` optional where concept is non-project scoped
- **EVT-006** `entity_type` required
- **EVT-007** `entity_id` required
- **EVT-008** `source_family` required
- **EVT-009** `source_type` required
- **EVT-010** `source_version` required
- **EVT-011** `source_record_id` required
- **EVT-012** `source_revision` optional but required where revisioned source exists
- **EVT-013** `actor_id` required for human/system/AI actor identity
- **EVT-014** `actor_role` required
- **EVT-015** `occurred_at` required
- **EVT-016** `recorded_at` required
- **EVT-017** `correlation_id` required where workflow chain exists
- **EVT-018** `causation_id` optional but required for causal replay chains
- **EVT-019** `before` optional structured prior state snapshot
- **EVT-020** `after` optional structured resulting state snapshot
- **EVT-021** `reason_code` optional but required where transition/publish/cancel/revise requires reason
- **EVT-022** `evidence_refs` optional array, required where evidence-gated transition exists
- **EVT-023** `status` required
- **EVT-024** `metadata` optional governed extension bag
- **EVT-025** `idempotency_key` required where retry/replay is possible
- **EVT-026** `sensitivity_classification` required where redaction/privacy boundary applies

### 4.2 Event Contract Rules
- validation owner: emitting workflow authority plus event contract governance
- event-version compatibility must be additive or explicitly migrated
- retries must be idempotent
- replay must not create duplicate business truth
- event history is append-only where required by audit or Trust
- sensitive narratives may not be copied into broad metadata when redaction rules apply
- events may drive side effects, but no material side effect may be hidden
- events are evidence of change; they are not alternate source-record truth

### 4.3 Canonical Event Vocabulary
CREATED, UPDATED, ASSIGNED, REASSIGNED, SUBMITTED, REVIEW_REQUESTED, REVIEWED, APPROVED, REJECTED, COMMITTED, PUBLISHED, RELEASED, STARTED, PAUSED, BLOCKED, UNBLOCKED, PARTIALLY_COMPLETED, COMPLETED, VERIFIED, RECONCILED, REVISED, SUPERSEDED, CANCELLED, CLOSED, REOPENED, ESCALATED, EXPORTED, DELIVERED, VIEWED, FAILED, RETRIED, SKIPPED

## 5. KPI and Dashboard Contracts

### 5.1 KPI Contract
Every KPI must define:
- **KPI-001** `kpi_id`
- **KPI-002** name
- **KPI-003** plain-English meaning
- **KPI-004** operational question
- **KPI-005** primary role/user
- **KPI-006** decision supported
- **KPI-007** action supported
- **KPI-008** action owner
- **KPI-009** canonical source records
- **KPI-010** formula
- **KPI-011** numerator
- **KPI-012** denominator
- **KPI-013** unit
- **KPI-014** time window
- **KPI-015** inclusion rules
- **KPI-016** exclusion rules
- **KPI-017** synthetic/test/certification exclusion
- **KPI-018** freshness target
- **KPI-019** stale threshold
- **KPI-020** truth classification
- **KPI-021** missing-data behavior
- **KPI-022** partial-period behavior
- **KPI-023** threshold rationale
- **KPI-024** drill-down path
- **KPI-025** history retention
- **KPI-026** audit/version behavior
- **KPI-027** notification relationship
- **KPI-028** owner
- **KPI-029** certification tests

Prohibited:
- unexplained health scores
- percentages without denominators
- different formulas by portal
- estimated values shown as verified
- synthetic/certification records in production KPIs
- arbitrary red/yellow/green without governed rationale
- metrics with no decision or action
- frontend-owned KPI formulas

### 5.2 Dashboard Contract
Every dashboard must define:
- **DASH-001** dashboard_id / surface id
- **DASH-002** role mission
- **DASH-003** data coverage and freshness
- **DASH-004** critical exceptions
- **DASH-005** operational board
- **DASH-006** action queue
- **DASH-007** resource/readiness view
- **DASH-008** recent changes
- **DASH-009** evidence drill-down
- **DASH-010** history/trends
- **DASH-011** search and filters
- **DASH-012** user
- **DASH-013** question
- **DASH-014** decision
- **DASH-015** action
- **DASH-016** owner
- **DASH-017** source
- **DASH-018** truth classification
- **DASH-019** empty-state behavior
- **DASH-020** mobile/iPad behavior
- **DASH-021** permissions
- **DASH-022** certification

### 5.3 Locked Role Missions
- Field Leadership: What is planned, what must be captured, and what is blocking work?
- PM: What requires action across my projects?
- Dispatch: Where are resources, and what must move next?
- Transportation: What hauling or movement work is required, active, delayed, or complete?
- Shop: What equipment requires attention, and what scheduled work is affected?
- Equipment/Fleet: What is available, unavailable, assigned, or at risk?
- Safety: What risk, hold, or compliance issue requires action?
- HR: What workforce or qualification issue requires action?
- QA/QC: What work requires inspection, evidence, hold, approval, or release?
- Executive: What happened, what changed, and what requires intervention?

## 6. Notification Contract

### 6.1 Notification Fields
Every notification type must define:
- **NOTIF-001** `notification_type_id`
- **NOTIF-002** trigger
- **NOTIF-003** source event
- **NOTIF-004** evidence
- **NOTIF-005** tenant/project scope
- **NOTIF-006** audience
- **NOTIF-007** recipient-resolution owner
- **NOTIF-008** priority
- **NOTIF-009** required action
- **NOTIF-010** action owner
- **NOTIF-011** channel
- **NOTIF-012** timing
- **NOTIF-013** expiration
- **NOTIF-014** dedupe key
- **NOTIF-015** suppression rule
- **NOTIF-016** escalation rule
- **NOTIF-017** retry rule
- **NOTIF-018** delivery status
- **NOTIF-019** resolution condition
- **NOTIF-020** lifecycle state
- **NOTIF-021** deep link
- **NOTIF-022** permission behavior
- **NOTIF-023** English text
- **NOTIF-024** Spanish text
- **NOTIF-025** audit event
- **NOTIF-026** Trust Spine relationship
- **NOTIF-027** certification/test suppression
- **NOTIF-028** synthetic-record suppression

### 6.2 Priority Set
INFORMATIONAL, NORMAL, IMPORTANT, URGENT, CRITICAL

### 6.3 Ecosystem Reuse Rule
The existing MASCI notification ecosystem — bell, email, digest, task, and alarm patterns already verified in the repository — must be reused.
No new notification engine may be introduced without constitutional amendment.

## 7. Daily Company Operations Brief Contract

### 7.1 Brief Identity
- **BRIEF-001** `brief_id`
- **BRIEF-002** `tenant_id`
- **BRIEF-003** `reporting_date`
- **BRIEF-004** `reporting_window_start`
- **BRIEF-005** `reporting_window_end`
- **BRIEF-006** `timezone`
- **BRIEF-007** `version_number`
- **BRIEF-008** `revision_reason`
- **BRIEF-009** `lifecycle_state`
- **BRIEF-010** `generated_at`
- **BRIEF-011** `published_at`
- **BRIEF-012** `finalized_at`
- **BRIEF-013** `data_through`
- **BRIEF-014** `source_coverage_snapshot`
- **BRIEF-015** source/version metadata
- **BRIEF-016** `generated_by`
- **BRIEF-017** `approved_by` where required

### 7.2 Fixed Section Order
Brief Identity → Data Coverage → Executive Summary → Company Operations Snapshot → What Went Well → What Did Not Go as Planned → Project Highlights → Schedule and Reconciliation → Safety → Dispatch / Transportation / Trucking → Shop / Fleet / Equipment → Materials → QA/QC → Workforce / Qualifications → Constraints and Blockers → Executive Attention Required → Today’s Risks and Required Decisions → Evidence / Drill-Down Appendix

### 7.3 Reporting Rules
- prior-day reporting window is authoritative unless governed special window exists
- company timezone is authoritative for reporting_date and cutoff
- night-shift crossing midnight must follow one governed attribution rule
- preliminary generation time, review period, publication time, and final-close time must be explicit
- late Daily Reports and late domain data must trigger revision or coverage-warning behavior, not silent certainty
- material-change threshold must govern whether revision is required
- one canonical source snapshot powers all role-specific views for a given brief version
- fact vs derived vs AI labeling is mandatory

## 8. Security / Tenant Contract

### 8.1 Security Fields
- **SEC-001** tenant_id stable identity
- **SEC-002** company membership scope
- **SEC-003** tenant isolation
- **SEC-004** project scope
- **SEC-005** role scope
- **SEC-006** object-level authorization
- **SEC-007** field-level protection where required
- **SEC-008** internal versus public visibility
- **SEC-009** attachment/evidence access
- **SEC-010** search visibility
- **SEC-011** dashboard visibility
- **SEC-012** brief visibility
- **SEC-013** notification recipient scope
- **SEC-014** export permissions
- **SEC-015** PDF permissions
- **SEC-016** AI input/output privacy
- **SEC-017** event redaction
- **SEC-018** Trust/audit access
- **SEC-019** system-automation authority
- **SEC-020** certification/test isolation
- **SEC-021** synthetic-record isolation
- **SEC-022** cross-tenant prohibition
- **SEC-023** support/admin access governance
- **SEC-024** least privilege
- **SEC-025** privilege escalation prevention
- **SEC-026** unauthorized counter/metadata leakage prevention

## 9. MASCI Product Identity and Experience Contract

### 9.1 Product Identity Rules
- **UX-001** reuse shared PortalShell or canonical shared shell
- **UX-002** reuse shared navigation
- **UX-003** reuse shared page-header hierarchy
- **UX-004** reuse shared typography and spacing
- **UX-005** reuse shared cards, panels, badges, selectors, drawers, modals, evidence timeline, drill-down patterns, empty states, coaching language, responsive behavior, permission-aware navigation, translation patterns, Trust/audit language
- **UX-006** every new surface must look like, sound like, and behave like MASCI OPS
- **UX-007** no one-off themes, no spreadsheet-first product drift, no portal identity drift, no duplicated component systems

### 9.2 English / Spanish Rules
- **UX-010** English remains canonical backend language
- **UX-011** all user-facing labels, coaching, validation, notifications, status labels, and brief headings must have English and Spanish where shown to users
- **UX-012** no new English-only workflow
- **UX-013** missing translations block applicable certification

### 9.3 Accessibility Rules
- **UX-020** no color-only state communication
- **UX-021** text/icon/state-label redundancy
- **UX-022** screen-reader labels where applicable
- **UX-023** keyboard navigation where applicable
- **UX-024** visible focus states
- **UX-025** sufficient touch targets
- **UX-026** semantic headings and accessible tables or mobile alternatives
- **UX-027** accessible error summaries and evidence drill-down
- **UX-028** clear required vs optional labels
- **UX-029** no clipped controls or horizontal scrolling on phone/iPad
- **UX-030** progressive disclosure, plain heavy-civil language, helpful recovery instructions, reduced operator typing, search-first selectors

## 10. Manual GitHub / Deployment Boundary Contract

### 10.1 Binding Rules
- **DEPLOY-001** ONLY JAYMN MAY PHYSICALLY SAVE OR PUBLISH CHANGES TO GITHUB.
- **DEPLOY-002** ONLY JAYMN MAY PHYSICALLY DEPLOY PREVIEW OR PRODUCTION.
- **DEPLOY-003** Emergent must never be instructed to push, publish, save to GitHub, deploy preview, deploy production, or claim those manual actions occurred.
- **DEPLOY-004** Emergent may inspect, implement locally, run tests, create evidence, prepare handoff, and verify later stages only after Jaymn confirms the manual action occurred.

### 10.2 Workflow Milestones
GOVERNANCE_DOCUMENTED, LOCAL_IMPLEMENTATION_COMPLETE, LOCAL_TESTS_VERIFIED, READY_FOR_JAYMN_GITHUB_SAVE, JAYMN_GITHUB_SAVE_CONFIRMED, GITHUB_SOURCE_VERIFIED, READY_FOR_JAYMN_PREVIEW_DEPLOYMENT, JAYMN_PREVIEW_DEPLOYMENT_CONFIRMED, PREVIEW_VERIFIED, READY_FOR_JAYMN_PRODUCTION_DEPLOYMENT, JAYMN_PRODUCTION_DEPLOYMENT_CONFIRMED, PRODUCTION_VERIFIED, FIELD_ACCEPTANCE_VERIFIED, EXECUTIVE_ACCEPTANCE_VERIFIED, FINAL_OPERATIONAL_CLOSEOUT

## 11. Appendix Cross-Reference Map

This appendix is normatively referenced by:
- Constitution stable identifier, lifecycle, event, KPI/dashboard, notification, brief, security, product identity, and deployment boundary sections
- Register Track 1 and downstream tracks
- Zero-Drift Matrix foundational rows
- Role Matrix explicit permissions and object authority
- Certification Plan status, lifecycle, event, KPI/dashboard, notification, brief, security, product identity, and deployment boundary certification gates