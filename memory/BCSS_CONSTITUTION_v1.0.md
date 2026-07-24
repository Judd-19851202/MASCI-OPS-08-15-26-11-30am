# MASCI OPS — Business Continuity & Survivability System Constitution

## 1. Title Page

**Document Name:** MASCI OPS — Business Continuity & Survivability System Constitution  
**Version:** 1.0  
**Status:** Adopted and frozen constitutional standard  
**Scope:** Platform-wide BCSS governing standard  
**Execution posture:** Documentation only. No implementation. No remediation execution. No deployment. No production activation.

## 2. Version and Status

### Document Control

| Field | Value |
|---|---|
| Document name | MASCI OPS — Business Continuity & Survivability System Constitution |
| Version | 1.0 |
| Constitutional status | **ADOPTED AND FROZEN** |
| Status | **CONSTITUTION COMPLETE** · **IMPLEMENTATION CONFORMANCE NOT COMPLETE** · **FINAL INDEPENDENT VERIFICATION PASSED** |
| Constitutional authority | Platform-wide governing authority for Backup, Recovery, Disaster Recovery, Business Continuity, Operational Continuity, Survivability, Recovery Intelligence, Recovery Trust, Recovery KPIs, Recovery Evidence, Recovery Certification, Dependency Continuity, Data Protection, Restore Readiness, and Operational Resilience |
| Repository path | `/app/memory/BCSS_CONSTITUTION_v1.0.md` |
| Repository SHA reviewed during independent review | `fbb7045b083fb509e9d448d6615d248c727c153c` |
| Repository SHA containing this amendment | `d51b486fb428ca4beddd832226061267db0e605a` |
| Final pre-adoption verification HEAD | `01fb629a48587f6c9a5c1dea88e9e9cc719a17d9` |
| Metadata-synchronization SHA | `01fb629a48587f6c9a5c1dea88e9e9cc719a17d9` |
| Effective date | `2026-07-24` |
| Adoption authority | `Jaymn Kurtis Judd — Platform Owner, MASCI OPS / ForgedOps` |
| Adoption date | `2026-07-24` |
| Final independent verification | **PASSED — READY FOR OWNER ADOPTION AND CONSTITUTIONAL FREEZE** |
| Adoption commit | **TO BE RECORDED BY POST-COMMIT ADOPTION VERIFICATION** |
| Supersedes | BCSS Constitution v1.0 Candidate; BCSS Constitutional Phase 0 artifact |
| Amendment history reference | Section 40 and Annex A |
| Platform conformance status | **IMPLEMENTATION CONFORMANCE NOT COMPLETE** |
| Recovery certification status | **NOT YET PROVEN** |
| Independent-review status | Final independent freeze verification passed; owner adoption recorded |
| Amendment rule | Changes require formal constitutional amendment governance |

### Repository Materialization Note

This repository stores architecture, governance, certification, and standards artefacts in `/app/memory/`, including files such as `DEPLOYMENT_GOVERNANCE_MATURITY.md`, `ENGINEERING_STANDARDS.md`, `TRACK_15_78_FINAL_CERTIFICATION.md`, and `TRACK_15_79_FINAL_CERTIFICATION.md`. Consistent with that verified convention, the BCSS constitution is materialized at `/app/memory/BCSS_CONSTITUTION_v1.0.md`. No competing constitutional documentation hierarchy is introduced.

## 3. Constitutional Authority

### Frozen Version Notice

BCSS Constitution v1.0 is adopted and frozen as of `2026-07-24`. Version 1.0 may be changed only through formal constitutional amendment governance. Ordinary implementation work, remediation work, or implementation discoveries shall not silently rewrite this constitution.

This constitution governs MASCI OPS platform-wide wherever backup, recovery, disaster recovery, business continuity, operational continuity, survivability, recovery intelligence, recovery trust, recovery KPIs, recovery evidence, recovery certification, dependency continuity, data protection, restore readiness, or operational resilience are implicated.

MASCI OPS shall be treated as **one integrated operational organism**, not a collection of disconnected applications. BCSS is therefore a platform constitution, not a standalone backup feature or a domain-local survivability overlay.

This constitution governs:
- architecture
- truth ownership
- evidence classes
- trust and KPI interpretation
- operator-facing survivability truth
- certification boundaries
- conformance expectations
- future change obligations

## 4. Purpose

### Constitutional Purpose

BCSS exists to define the permanent governing architecture for:
- Backup
- Recovery
- Disaster Recovery
- Business Continuity
- Operational Continuity
- Platform Survivability
- Recovery Intelligence
- Recovery Trust
- Recovery KPIs
- Recovery Evidence
- Recovery Certification
- Dependency Continuity
- Data Protection
- Restore Readiness
- Operational Resilience

BCSS does **not** exist merely to govern file copying or archive creation. It governs the full chain from **authority** through **execution**, **evidence**, **intelligence**, **trust**, and **certification**.

### Verified Current State

The repository already contains survivability-relevant authority, execution, evidence, intelligence, trust, and certification mechanisms, but they are distributed across multiple canonical platform systems rather than formally registered as one BCSS constitutional layer. Evidence includes:
- runtime DB authority (`backend/lib/database_authority.py:64-101, 166-210`)
- backup/restore runtime state (`backend/lib/backup_runtime.py:56-145, 161-234`)
- scheduler execution audit (`backend/lib/scheduler_runs.py:66-94, 97-246`)
- recovery snapshot (`backend/routes/recovery_dashboard.py:308-314, 328-631`)
- backup trust score (`backend/server.py:11952-12021`; `backend/lib/trust_score.py:202-268`)
- deploy certification (`backend/routes/admin_deployment_readiness.py:72-393`; `backend/routes/admin_deployment_ledger.py:42-97, 103-156`)

## 5. Scope

### Constitutional Scope Rule

Every applicable persistent operational data source shall participate in BCSS unless an approved constitutional exception documents why it does not.

### Constitutional Applicability

BCSS applies to any platform capability that:
- creates persistent operational data
- stores persistent operational data
- changes persistent operational data
- transforms persistent operational data
- transmits persistent operational data
- indexes persistent operational data
- derives decisions from persistent operational data
- depends on persistent operational data
- depends on external services required for continuity
- produces operational evidence
- produces certification or trust claims

### In-Scope Platform Areas

Where applicable, BCSS governs:
- Admin Console
- PM Portal
- Dispatch
- Shop
- HR
- Safety
- Jobs and Field
- Daily Reports
- Equipment
- Suppliers
- Training
- Professional Qualifications
- Forms
- Compliance
- Audits
- Tasks
- Actions
- PO Requests
- Project Health
- Asset Transfers
- Operations Events
- Operational Daily Records
- Plans
- Documents
- Photos
- Attachments
- Videos
- AI-generated or AI-consumed operational artifacts
- Operational Data Store
- Integrations
- Notifications
- Identity
- Authorization
- Scheduling
- Reporting
- Certification
- Future modules

### Verified Current State

Repository evidence confirms survivability-relevant scope already spans identity, workflow trust, integrations, recovery posture, and certification:
- identity/session continuity (`backend/lib/canonical_truth.py:156-185`)
- integration truth (`backend/lib/canonical_truth.py:127-155`; `backend/routes/integrations/config.py:43-52, 174-202`)
- workflow lifecycle truth (`backend/lib/trust_spine.py:1-40, 50-82, 187-284`)
- operational trust (`backend/routes/admin_operations_trust_center.py:1-30, 297-320`)
- recovery posture (`backend/routes/recovery_dashboard.py:328-631`)
- certification (`backend/routes/admin_deployment_readiness.py:72-393`)

## 6. Interpretation Rules

1. **Verified Current State** means a statement supported by repository evidence.
2. **Constitutional Requirement** means a governing rule that is mandatory whether or not full implementation is complete.
3. **Recommended Future Conformance** means required future work not executed in this track.
4. Repository reality overrides unsupported documentation claims.
5. Tests may prove contract behavior in a bounded context; they do not by themselves prove production exercise.
6. Preview evidence shall not be represented as production evidence.
7. Representative restore evidence shall not be represented as full-platform recovery proof.
8. Endpoint existence shall not be treated as proof of sustained operator use.
9. Configuration possibility shall not be treated as proof of activation.
10. When documentation and code conflict, the conflict shall be recorded explicitly.
11. De facto implementation behavior is not the same as formal canonical registration.
12. Behavioral alignment shall not be overstated as full constitutional conformance where registration, ownership binding, evidence integration, or governance remains incomplete.

## 7. Definitions

| Term | Constitutional Definition |
|---|---|
| Backup | A governed act that captures persistent operational data and/or required recovery material for future restoration. |
| Archive | A durable backup package or stored backup object, including its structure, metadata, and lineage context. |
| Backup evidence | Durable proof that a backup action occurred, what it captured, when it occurred, and under what conditions. |
| Backup verification | A governed assessment that backup evidence and archive state support a bounded claim such as presence, freshness, or integrity. |
| Archive integrity | Evidence that an archive is structurally readable and internally valid for its claimed format and manifest contract. |
| Archive lineage | The traceable relationship between archive origin, runtime identity, environment, database target, manifest, and resulting evidence. |
| Recovery | The governed act of restoring service capability, data availability, or operational continuity after degradation or loss. |
| Restore | A concrete recovery operation that replays backup material into a target environment or subsystem. |
| Restore drill | A deliberately executed restore exercise performed to generate recovery evidence. |
| Representative restore drill | A drill that proves a bounded slice or namespace, but not the entire platform. |
| Full-platform restore | A restore exercise intended to prove recovery of the platform as an integrated organism, not just one subset. |
| Disaster Recovery | Recovery of platform operation after major infrastructure, data, provider, environment, or systemic failure. |
| Business Continuity | The ability to continue priority business operations during degradation, disruption, or partial loss. |
| Survivability | The platform’s ability to protect itself, continue operating where possible, recover when disrupted, and prove that recovery truthfully. |
| Continuity dependency | Any internal or external dependency whose loss materially affects continued platform operation. |
| Recovery dependency | Any dependency required to verify, initiate, execute, complete, or certify recovery. |
| Operational data | Data used to run, prove, audit, guide, or improve MASCI OPS operations. |
| Persistent operational data | Operational data intended to survive request boundaries, process restarts, or runtime replacement. |
| Canonical truth | The authoritative platform truth for a defined subject, owned by exactly one canonical owner. |
| Truth subject | A distinct area of platform truth requiring declared ownership, evidence, and interpretation rules. |
| Canonical owner | The single authority permitted to define source truth for a truth subject. |
| Aggregator | A surface that combines upstream truths without replacing them. |
| Derived consumer | A surface that interprets canonical truth into scores, summaries, KPIs, or operator guidance. |
| Validator | A surface that checks or grades truth claims against rules but does not become source truth. |
| Evidence | Durable, attributable information used to support or limit a claim. |
| Certification | A governed decision that a bounded claim is sufficiently supported by evidence. |
| Recovery certification | Certification of recovery readiness or exercised recovery capability. |
| Deployment certification | Certification that current code/system state is safe to deploy under defined gate rules. |
| Trust | Operator confidence derived from transparent evidence, not assumption. |
| Recovery trust | A derived confidence measure about survivability and recoverability. |
| Recovery posture | The current evidence-backed view of recovery readiness, gaps, and risks. |
| KPI | A defined performance or readiness indicator whose inputs and meaning are explicit. |
| RPO | Recovery Point Objective: the maximum tolerable data-loss interval. |
| RTO | Recovery Time Objective: the target time to restore bounded service capability. |
| Freshness | How recent evidence is relative to the policy or claim it supports. |
| Fail closed | Refuse or downgrade the action or claim when safety, truth, or authorization cannot be established. |
| Preview evidence | Evidence produced in a non-production environment. |
| Production evidence | Evidence produced in the production environment. |
| Operator data issue | A problem caused by missing, stale, incomplete, or incorrect operational data rather than platform code/system behavior. |
| Code/system defect | A defect in code, runtime logic, configuration contract, or platform mechanism. |
| Constitutional conformance | Alignment between a subsystem and this constitution’s ownership, evidence, trust, and control rules. |
| Constitutional exception | A documented, approved, version-controlled deviation from a constitutional rule. |
| Material architectural change | A change that affects BCSS truth subjects, persistent data, recovery behavior, dependencies, evidence, certification, or shared governance. |
| Survivability registration | The future mandatory declaration of a module’s BCSS participation and obligations. |
| Recovery dependency graph | The declared upstream/downstream structure required to support recovery truth and execution. |
| Proof of recovery | Evidence sufficient to support a bounded recovery claim at a defined certification class. |
| No Fake PASS | A non-negotiable rule that no success, green state, trust score, or certification may overstate the evidence actually exercised. |

## 8. Governing Principles

The final BCSS constitution shall comply with:
- Powerful
- Simple
- Beautiful
- Trusted
- Proven
- Deployable
- Durable
- Relentless Ownership

And:
- Zero Drift
- One Source of Truth
- One canonical architecture
- Smallest Safe Repair
- No Fake PASS
- Screenshots and observable evidence over unsupported reports
- Repository reality over documentation claims
- Operator experience over builder claims
- Field First
- Operations First
- Mobile First
- Trust First
- Continuity First
- Survivability First

### Constitutional Implication

No duplicate engine, scheduler, dashboard, trust calculation, KPI system, notification system, evidence system, status engine, identity system, access-control system, intelligence system, audit system, certification system, backup system, recovery system, or survivability registry may be introduced without an explicit constitutional exception.

## 9. Constitutional Invariants

The following are non-negotiable governing constraints:

1. One canonical owner per truth subject.
2. Repository reality overrides unsupported documentation claims.
3. Derived views shall not become canonical truth by implication.
4. No recovery claim without durable evidence.
5. No certification claim beyond the evidence actually exercised.
6. Representative restore evidence shall not equal full-platform restore certification.
7. Preview evidence shall not equal production evidence.
8. No silent failure.
9. No duplicate survivability architecture without approved exception.
10. No orphaned persistent operational data without documented exclusion.
11. No survivability-sensitive operation without authorization.
12. No false green, fake PASS, or unsupported trust score.
13. No restoration across invalid environment or data-origin boundaries.
14. No single subsystem may privately redefine shared BCSS truth.
15. Conformance is a release requirement, not deferred cleanup.
16. Future modules shall conform from inception.
17. Existing modules shall be evaluated and updated where appropriate to achieve architectural convergence.
18. Every material architectural change shall complete a Constitutional Impact Analysis.
19. Evidence shall be secret-free where exposed to operator or audit surfaces.
20. Survivability controls shall fail closed where safety or truth cannot be established.
21. **Deployment certification and recovery certification are distinct; neither implies the other.**
22. An approved exception is not proof of conformance.

### Verified Current State

Several invariants are already reflected in implementation patterns:
- origin/environment restore guard (`backend/server.py:12504-12588`)
- anti-fake-green lifecycle bands (`backend/routes/admin_trust_spine.py:121-173, 190-228`)
- preview vs production notification separation (`backend/lib/notification_delivery.py:70-137`)
- representative vs full restore distinction in recovery posture (`backend/routes/recovery_dashboard.py:618-629`)

## 10. Authority and Precedence

1. This BCSS Constitution governs survivability architecture platform-wide.
2. Repository implementation is evidence of current reality; it is not automatic proof of constitutional conformance.
3. A later approved constitutional version supersedes earlier constitutional versions.
4. Domain specifications may impose stricter requirements, but may not weaken BCSS.
5. PRDs, summaries, test narratives, implementation notes, or agent claims may not override this constitution.
6. When documentation conflicts with verified repository behavior, the conflict shall be recorded explicitly.
7. When two implementations claim canonical ownership for the same truth subject, that state shall be treated as a constitutional conflict until resolved.
8. Formal canonical registration is stronger than undocumented de facto behavior, but de facto behavior still governs verified current state.

## 11. Verified Current State

MASCI OPS already contains a substantial survivability foundation:
- validated runtime database authority (`backend/lib/database_authority.py:64-101`)
- durable backup and restore job ownership (`backend/lib/backup_runtime.py:56-145`)
- scheduler slot dedup and audit (`backend/lib/scheduler_runs.py:97-161`)
- weekly backup verification (`backend/backup_verification.py:315-467`)
- recovery snapshot operator surface (`backend/routes/recovery_dashboard.py:571-631`)
- deterministic backup trust scoring (`backend/lib/trust_score.py:202-268`)
- admin-strict restore with archive-origin guards (`backend/server.py:12388-12864`)
- lifecycle trust evidence (`backend/lib/trust_spine.py:187-284`)
- deploy-readiness certification with code-vs-data distinction (`backend/routes/admin_deployment_readiness.py:150-393`)
- immutable deployment decision ledger (`backend/routes/admin_deployment_ledger.py:42-97`)
- notification continuity contract (`backend/lib/notification_delivery.py:70-137`)
- canonical truth role taxonomy (`backend/lib/canonical_truth.py:68-307`)

The verified current state is therefore **not absence of survivability**. It is **partial constitutionalization of survivability**.

## 12. Repository Discovery

### Preserved Deliverable 1 — Complete Repository Discovery

| Capability Area | Verified Current State | Exact Repository Evidence |
|---|---|---|
| Runtime state authority | Runtime DB use requires valid runtime identity, explicit authority plan, and redacted public authority payload. | `backend/lib/database_authority.py:64-101, 166-210, 218-227` |
| Backup/restore job runtime | Backup jobs are durable, leased, heartbeated, and stale-recoverable. | `backend/lib/backup_runtime.py:48-53, 56-145, 161-234` |
| Scheduler execution authority | Scheduled work uses unique slot claims and immutable run history. | `backend/lib/scheduler_runs.py:66-94, 97-161, 164-246` |
| Weekly backup verification | Verification checks both local ledger and R2 state, then produces verdict and dispatch result. | `backend/backup_verification.py:224-309, 315-467, 669-771, 777-877` |
| Verification control surface | Admin preview/run-now/state endpoints exist. | `backend/routes/backup_verification_routes.py:28-96` |
| Recovery posture | Recovery snapshot composes archive, drill, scheduler, bucket, disk, cadence, warning, and production-only evidence status. | `backend/routes/recovery_dashboard.py:328-631` |
| Public backup-recent truth | Public full-health backup recency truth uses scheduler-aware precedence across local and R2 signals. | `backend/server.py:1532-1605` |
| Backup trust score | Backup trust is computed from recency, restore drill, integrity, overlap, failures, and bucket usage. | `backend/server.py:11952-12021`; `backend/lib/trust_score.py:202-268` |
| Restore authority | Restore blocks on active backup jobs, validates manifest, validates environment/database origin, supports dry run, and audits result. | `backend/server.py:12388-12864` |
| Trust Spine | Lifecycle evidence is stored as `trust_spine_events` under a defined contract. | `backend/lib/trust_spine.py:1-40, 50-82, 187-284` |
| Trust dashboard rollup | Workflow trust bands explicitly prevent fake green. | `backend/routes/admin_trust_spine.py:34-228` |
| Operations trust | Derived operational trust center synthesizes categories, actions, trends, and narrative. | `backend/routes/admin_operations_trust_center.py:1-30, 151-291, 297-320` |
| Notification continuity | Preview/test force safe capture; production requires provider-live configuration. | `backend/lib/notification_delivery.py:70-137` |
| Notification contract proof | Dedicated tests verify preview capture and production blocking semantics. | `backend/tests/test_c2_phase2_notification_contract.py:34-155` |
| Canonical truth governance | Shared truth registry already models owner, aggregator, derived consumer, and validator roles. | `backend/lib/canonical_truth.py:68-307, 326-345, 379-526` |
| Deployment certification | Deployment readiness blocks on code/system defects and separates advisory operator data issues. | `backend/routes/admin_deployment_readiness.py:72-393` |
| Decision evidence | Deployment decisions are append-only and TTL-managed. | `backend/routes/admin_deployment_ledger.py:1-12, 24-39, 42-97, 103-156` |
| OCC trust feed | Unified trust events combine audit, scheduler, ops audit, and deploy blockers. | `backend/routes/occ_trust_events.py:152-235` |
| Operations governance | OCC overview, audited dry-run/apply, and audit retrieval exist. | `backend/routes/operations_control.py:62-81, 122-218` |
| Integration continuity | Integration settings and health surfaces already exist. | `backend/routes/integrations/config.py:43-52, 56-113, 174-202` |
| Evidence manifest pattern | Evidence manifests can be typed, hashed, warning-bearing, and AI-consumable. | `backend/services/dr_evidence/manifest.py:268-355, 375-439` |

## 13. Duplicate Architecture Audit

### Preserved Deliverable 2 — Duplicate Architecture Audit

| Area | Verified Overlap | Constitutional Reading | Exact Evidence |
|---|---|---|---|
| Backup freshness truth | Public full-health logic and recovery snapshot both derive recency using overlapping but not identical precedence. | Valid specialization, but canonical precedence is not yet formalized. | `backend/server.py:1561-1605`; `backend/routes/recovery_dashboard.py:328-379` |
| Posture vs trust | Recovery snapshot emits pill/RPO/RTO/warnings; backup trust score emits composite trust/band. | Acceptable only if posture and trust remain explicitly distinct. | `backend/routes/recovery_dashboard.py:571-631`; `backend/server.py:11952-12021` |
| Verification vs certification | Weekly verification, recovery posture, backup trust, deploy readiness, and deployment ledger all evaluate overlapping evidence. | Acceptable only when each claim class is bounded. | `backend/backup_verification.py:315-467`; `backend/routes/admin_deployment_readiness.py:150-393`; `backend/routes/admin_deployment_ledger.py:42-97` |
| Trust summarization surfaces | Trust Spine, Operations Trust Center, OCC Trust Events, and deploy readiness each summarize truth differently. | Healthy only if canonical owner vs derived role is explicit. | `backend/lib/trust_spine.py:1-40`; `backend/routes/admin_trust_spine.py:202-228`; `backend/routes/admin_operations_trust_center.py:297-320`; `backend/routes/occ_trust_events.py:178-235` |
| Access governance | Route-local survivability guards exist while centralized RBAC remains non-enforcing. | Constitutional convergence gap. | `backend/lib/rbac.py:7-10, 323-391`; `backend/server.py:868-923` |
| Evidence manifest patterns | Daily Report evidence manifest is strong but domain-local. | Reusable pattern, not platform BCSS owner. | `backend/services/dr_evidence/manifest.py:268-355, 375-439` |

### Constitutional Rule

Parallel derivation is allowed only when the following are explicit:
- truth subject
- owner role
- upstream inputs
- derived nature
- bounded claim class

## 14. Survivability Coverage Matrix

### Preserved Deliverable 3 — Survivability Coverage Matrix

| BCSS Domain | Current Coverage | Constitutional Conformance Status | Evidence |
|---|---|---|---|
| Runtime authority | Present | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/lib/database_authority.py:64-101` |
| Scheduler survivability | Present | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/lib/scheduler_runs.py:97-161`; `backend/routes/recovery_dashboard.py:488-517` |
| Backup execution | Present | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/lib/backup_runtime.py:56-145`; `backend/server.py:10445-10470` |
| Backup verification | Present | **PARTIALLY CONFORMS** | `backend/backup_verification.py:315-467`; `backend/routes/backup_verification_routes.py:28-96` |
| Backup lineage truth | Partial | **REQUIRES MODIFICATION** | `backend/server.py:11222-11313`; `backend/server.py:12384-12524` |
| Restore execution | Present | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/server.py:12388-12864` |
| Restore drill evidence | Present | **PARTIALLY CONFORMS** | `backend/routes/recovery_dashboard.py:468-486`; `backend/server.py:11976-12020` |
| Recovery posture | Present | **PARTIALLY CONFORMS** | `backend/routes/recovery_dashboard.py:571-631` |
| Recovery trust | Present | **PARTIALLY CONFORMS** | `backend/lib/trust_score.py:202-268`; `backend/server.py:11998-12021` |
| Recovery certification | Present | **PARTIALLY CONFORMS** | `backend/routes/admin_deployment_readiness.py:150-393` |
| Notification continuity | Present | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/lib/notification_delivery.py:70-137` |
| Integration/dependency continuity | Present | **PARTIALLY CONFORMS** | `backend/routes/integrations/config.py:174-202` |
| Capacity intelligence | Present | **PARTIALLY CONFORMS** | `backend/routes/recovery_dashboard.py:442-465`; `backend/lib/trust_score.py:244-249` |
| Canonical truth registration for BCSS | Absent | **REQUIRES MODIFICATION** | `backend/lib/canonical_truth.py:68-307` |
| Centralized survivability policy plane | Partial | **REQUIRES MODIFICATION** | `backend/lib/rbac.py:7-10` |

## 15. Integration Matrix

### Preserved Deliverable 4 — BCSS Integration Matrix

| BCSS Concern | Existing Canonical System | Integration |
|---|---|---|
| Runtime legitimacy | Database Authority | DB identity and authority plans govern runtime state. |
| Scheduled execution discipline | Scheduler Runs | Prevents duplicate slot execution and preserves audit. |
| Long-running backup/restore safety | Backup Runtime | Heartbeats, overlap guard, stale-job handling. |
| Archive verification | Weekly Backup Verification | Cross-checks local ledger and R2. |
| Recovery posture | Recovery Dashboard | Consumes backup, drill, bucket, scheduler, and cadence evidence. |
| Recovery trust | Backup Trust Score | Derived from posture-relevant evidence, not source truth. |
| Lifecycle truth | Trust Spine | Existing evidence model for status/failure stages. |
| Operator trust feed | OCC Trust Events / Operations Trust Center | Aggregates cross-subsystem evidence. |
| Notification continuity | Notification Delivery | Environment-aware provider vs safe-capture behavior. |
| Dependency continuity | Integration Center | Existing provider health/config surfaces. |
| Certification | Deployment Readiness + Deployment Ledger | Distinguishes defects vs operator data and records decisions. |
| Canonical ownership model | Canonical Truth Registry | Existing role taxonomy to extend, not replace. |

## 16. Recovery Dependency Graph

### Preserved Deliverable 5 — Recovery Dependency Graph

```text
Runtime Identity
  -> Database Authority
    -> Mongo runtime access

Scheduler Runs
  -> slot claim / duplicate prevention

Backup Runtime
  -> backup_jobs
  -> overlap classification
  -> stale job recovery

Backup execution
  -> backup_health
  -> Cloudflare R2 archives
  -> archive manifests

Archive / ledger / scheduler evidence
  -> public health backup_recent truth
  -> recovery snapshot
  -> backup trust score
  -> weekly verification report
  -> integrity check workflows

Restore endpoint
  -> backup job lease
  -> manifest validation
  -> environment / db origin validation
  -> audit_events
  -> replay / dry-run results

drill_runs
  -> recovery snapshot
  -> backup trust score

trust_spine_events + admin_audit + scheduler_runs + deployment_readiness + operations_audit
  -> OCC trust events
  -> Operations Trust Center
  -> deployment decisioning context
```

### Constitutional Dependency Order

1. Authority  
2. Execution  
3. Evidence  
4. Intelligence  
5. Trust  
6. Certification

No future survivability feature may bypass this chain.

## 17. Constitutional Architecture

### Preserved Deliverable 6 — Constitutional BCSS Architecture

BCSS uses six layers.

### 17.1 Authority Layer

**Constitutional responsibility:** define whether the platform is authorized to trust the state it is about to use or change.  
**May own:** runtime identity, environment identity, database legitimacy, access policy, origin boundaries.  
**May consume:** runtime config, identity state, session/auth state.  
**May not duplicate:** trust scoring, dashboard posture, certification summaries.  
**Required upstream inputs:** runtime identity, auth identity, environment configuration.  
**Required downstream outputs:** authority decisions, origin validation, allowed/denied state.  
**Durable evidence expectation:** audit-grade proof of authority decision where action is sensitive.  
**Failure behavior:** fail closed.  
**Operator visibility:** redacted authority posture only.  
**Relationship to Trust Spine:** authority failures should emit durable failure evidence where lifecycle-covered.  
**Relationship to canonical truth governance:** authority truth subjects shall be canonical.  
**Relationship to certification:** no certification without authority validity.

**Verified current state:** runtime DB authority and restore origin boundary exist (`backend/lib/database_authority.py:64-101`; `backend/server.py:12504-12588`).

### 17.2 Execution Layer

**Responsibility:** execute backup, verification, restore, and survivability-sensitive workflows.  
**May own:** scheduler slot claims, backup jobs, restore jobs, verification jobs.  
**May consume:** authority decisions and runtime state.  
**May not duplicate:** canonical evidence interpretation or trust scoring.  
**Required outputs:** execution evidence, completion/failure state, operator-safe status.  
**Failure behavior:** durable failure state, no silent drop.  
**Operator visibility:** in-progress, deferred, failed, completed.  
**Relationship to Trust Spine:** execution stages should integrate where practical.  
**Relationship to canonical truth governance:** execution truth subjects require canonical owners.  
**Relationship to certification:** execution without evidence cannot support certification.

**Verified current state:** `backup_runtime`, `scheduler_runs`, restore execution, and backup integrity job patterns already exist (`backend/lib/backup_runtime.py:56-145`; `backend/lib/scheduler_runs.py:97-161`; `backend/server.py:11200-11380`; `backend/server.py:12388-12864`).

### 17.3 Evidence Layer

**Responsibility:** hold durable proof of what happened.  
**May own:** job ledgers, audit rows, manifests, archive metadata, drill evidence, decision records.  
**May consume:** execution outputs.  
**May not duplicate:** truth ownership semantics or scoring logic.  
**Required outputs:** durable, attributable, freshness-aware evidence.  
**Failure behavior:** missing evidence downgrades claims.  
**Operator visibility:** evidence-linked and claim-bounded.  
**Relationship to Trust Spine:** Trust Spine is one evidence source, not the entire evidence layer.  
**Relationship to canonical truth governance:** evidence sources must be mapped to truth subjects.  
**Relationship to certification:** certification class depends on evidence class.

**Verified current state:** `backup_health`, `backup_jobs`, `scheduler_runs`, `trust_spine_events`, `admin_audit`, `audit_events`, `deployment_decisions`, and manifest-based evidence exist (`backend/backup_verification.py:354-467`; `backend/lib/backup_runtime.py:48-53`; `backend/lib/scheduler_runs.py:58-94`; `backend/lib/trust_spine.py:17-40`; `backend/routes/admin_deployment_ledger.py:21-39`; `backend/services/dr_evidence/manifest.py:268-382`).

### 17.4 Intelligence Layer

**Responsibility:** synthesize evidence into readable posture, warnings, and bounded operational meaning.  
**May own:** snapshots, health cards, bounded summaries, dependency posture views.  
**May consume:** canonical evidence only.  
**May not duplicate:** source truth or certification authority.  
**Required outputs:** evidence-linked operator interpretation.  
**Failure behavior:** state uncertainty explicitly.  
**Operator visibility:** actionable, severity-consistent, environment-aware.  
**Relationship to Trust Spine:** may consume Trust Spine evidence.  
**Relationship to canonical truth governance:** usually aggregator or derived consumer, not canonical owner.  
**Relationship to certification:** intelligence may inform certification, not replace it.

**Verified current state:** recovery snapshot, integration health, OCC trust events, and operations trust center are existing intelligence surfaces (`backend/routes/recovery_dashboard.py:571-631`; `backend/routes/integrations/config.py:174-202`; `backend/routes/occ_trust_events.py:178-235`; `backend/routes/admin_operations_trust_center.py:297-320`).

### 17.5 Trust Layer

**Responsibility:** express evidence-backed confidence and penalties transparently.  
**May own:** trust rollups, categorized penalties, trust bands, explanation of degradation.  
**May consume:** canonical evidence directly and intelligence summaries secondarily when they do not weaken stronger direct evidence.  
**May not duplicate:** archive source truth, execution truth, or certification authority.  
**Required outputs:** transparent penalties, no opaque green state.  
**Failure behavior:** degrade visibly.  
**Operator visibility:** score plus reasons.  
**Relationship to Trust Spine:** Trust Spine is a primary input for lifecycle trust.  
**Relationship to canonical truth governance:** trust is typically derived consumer output.  
**Relationship to certification:** trust can inform but cannot substitute for certification class.

**Verified current state:** lifecycle bands and backup trust score already prevent fake-green by design (`backend/routes/admin_trust_spine.py:130-173`; `backend/lib/trust_score.py:202-268`).

### 17.6 Certification Layer

**Responsibility:** make bounded go/no-go or class-based claims.  
**May own:** deployment readiness decisions, recovery class decisions, immutable certification records.  
**May consume:** authority, execution, evidence, intelligence, and trust inputs.  
**May not duplicate:** execution or source-truth systems.  
**Required outputs:** explicit claim class, blockers, advisory findings, and decision evidence.  
**Failure behavior:** fail closed or remain unclassified.  
**Operator visibility:** blockers, class, freshness, and unresolved prerequisites.  
**Relationship to Trust Spine:** may consume trust events; not owned by Trust Spine.  
**Relationship to canonical truth governance:** certification truth subjects require explicit ownership.  
**Relationship to Deployment Gate:** deployment certification is bounded to deployment readiness only.  
**Relationship to recovery certification:** recovery certification is bounded to survivability/recovery proof only.  
**Non-equivalence rule:** deployment certification does not imply recovery certification, and recovery certification does not imply deployment certification.

**Verified current state:** deployment readiness and deployment decisions ledger exist (`backend/routes/admin_deployment_readiness.py:72-393`; `backend/routes/admin_deployment_ledger.py:42-97, 103-156`).

### 17.7 Cross-Cutting Responsibilities

These shall be extended through existing canonical systems, not parallel engines:
- **Identity:** current auth/session truth surfaces (`backend/lib/canonical_truth.py:156-185`)
- **RBAC:** current centralized but non-enforcing policy brain (`backend/lib/rbac.py:1-18`)
- **Notifications:** existing delivery contract (`backend/lib/notification_delivery.py:70-137`)
- **Audit:** existing `admin_audit`, `audit_events`, OCC audit, deployment ledger
- **Evidence:** existing ledgers/manifests/event collections
- **KPIs:** existing snapshot fields and trust scores
- **Dashboards:** existing recovery/admin/trust/OCC surfaces
- **Intelligence:** existing recovery snapshot/OCC/operations trust
- **AI:** existing evidence-manifest pattern and AI-consuming artifacts (`backend/services/dr_evidence/manifest.py:387-439`)
- **Integration health:** existing Integration Center
- **Dependency mapping:** existing trust and readiness surfaces, to be extended constitutionally
- **Capacity intelligence:** existing bucket/capacity signals (`backend/routes/recovery_dashboard.py:442-465`; `backend/lib/trust_score.py:244-249`)

## 18. BCSS Truth Subjects

Each BCSS truth subject has exactly one constitutional owner-role category. The role may be defined even when the current implementation binding is not yet formally registered.

| Truth Subject | Purpose | Constitutional Owner Role | Current Implementation Binding | Formal Registration Status | Expected Upstream Evidence | Permitted Non-Owner Roles | Freshness Rule | Failure State | Operator Representation | Certification Significance |
|---|---|---|---|---|---|---|---|---|---|---|
| Runtime State Authority | Determine runtime legitimacy, environment identity, and state trust boundary | **AUTHORITY-LAYER CANONICAL OWNER** | `database_authority.py` behavior and related runtime identity flows | **CONSTITUTIONAL OWNER ROLE DEFINED — IMPLEMENTATION BINDING NOT YET FORMALLY REGISTERED** | runtime identity, DB plan, environment identity | aggregators, derived consumers, validators | current runtime state | invalid / unverifiable authority | redacted authority posture | blocks higher claims |
| Backup Slot Execution Truth | Prove scheduled slot ownership and duplicate prevention | **EXECUTION-LAYER CANONICAL OWNER** | `scheduler_runs.py` | **CONSTITUTIONAL OWNER ROLE DEFINED — IMPLEMENTATION BINDING NOT YET FORMALLY REGISTERED** | scheduler_runs, scheduler lock state | posture aggregators, validators | slot-bounded | duplicate / stale / missing / failed slot | scheduler state | supports cadence and execution claims |
| Backup Job Execution Truth | Prove long-running backup/restore execution state | **EXECUTION-LAYER CANONICAL OWNER** | `backup_runtime.py` and related server runtime state | **CONSTITUTIONAL OWNER ROLE DEFINED — IMPLEMENTATION BINDING NOT YET FORMALLY REGISTERED** | backup_jobs, heartbeats, overlap state | posture aggregators, derived trust | live/heartbeat bounded | queued / running / stale / failed / overlap-blocked | runtime state | supports posture and trust |
| Backup Archive Lineage Truth | Prove what archive exists, from where, when, and for which environment | **EVIDENCE-LAYER CANONICAL OWNER** | distributed across `backup_health`, R2 object state, manifests, integrity check flows | **CONSTITUTIONAL OWNER ROLE DEFINED — IMPLEMENTATION BINDING NOT YET FORMALLY REGISTERED** | backup_health, manifests, R2 object metadata, integrity checks | posture aggregators, trust consumers, validators | archive freshness policy dependent | stale / missing / conflicting / unverifiable lineage | last archive and lineage posture | supports Classes 1 and 2 |
| Restore Execution Truth | Prove restore request, guardrails, and replay result | **EXECUTION-LAYER CANONICAL OWNER** | `/exports/restore` flow in `server.py` | **CONSTITUTIONAL OWNER ROLE DEFINED — IMPLEMENTATION BINDING NOT YET FORMALLY REGISTERED** | restore job rows, manifest validation, audit, replay result | posture/certification consumers | action-scoped | blocked / rejected / partial_failure / failed | restore result and audit | supports restore exercise claims |
| Restore Drill Evidence Truth | Prove exercised restore drills and their bounded scope | **EVIDENCE-LAYER CANONICAL OWNER** | `drill_runs` consumption in recovery and trust surfaces | **CONSTITUTIONAL OWNER ROLE DEFINED — IMPLEMENTATION BINDING NOT YET FORMALLY REGISTERED** | drill_runs, related audit evidence | posture, trust, certification consumers | recertification-window dependent | missing / stale / failed / ambiguous scope | last drill, scope, age | supports Classes 3, 4, and 5 |
| Recovery Posture Truth | Present current recovery readiness and active BCSS warnings | **INTELLIGENCE-LAYER AGGREGATOR** | `recovery_dashboard.py` | **CONSTITUTIONAL OWNER ROLE DEFINED — IMPLEMENTATION BINDING NOT YET FORMALLY REGISTERED** | archive, drill, scheduler, runtime, capacity, activation evidence | derived trust consumers, validators | snapshot freshness | red / amber / unknown / unavailable | recovery posture | informs but does not certify |
| Recovery Trust Truth | Express transparent confidence in survivability signals | **TRUST-LAYER DERIVED CONSUMER** | backup trust score and related trust surfaces | **CONSTITUTIONAL OWNER ROLE DEFINED — IMPLEMENTATION BINDING NOT YET FORMALLY REGISTERED** | posture and direct evidence inputs | validators and operator dashboards | tied to underlying evidence freshness | degraded / not trusted | trust score plus penalties | informative only; not certification evidence |
| Recovery Certification Truth | Bound what recovery level may be claimed | **CERTIFICATION-LAYER CANONICAL OWNER** | class model not yet implemented as a shared runtime surface | **CONSTITUTIONAL OWNER ROLE DEFINED — IMPLEMENTATION BINDING NOT YET FORMALLY REGISTERED** | posture, evidence, class rules, independent review | dashboards may display, validators may check | class-dependent | not yet exercised / expired / blocked / uncertified | recovery certification class | direct certification meaning |
| External Dependency Continuity Truth | Prove continuity posture of required third-party dependencies | **INTELLIGENCE-LAYER AGGREGATOR** | distributed across Integration Center and notification-delivery contract | **CONSTITUTIONAL OWNER ROLE DEFINED — IMPLEMENTATION BINDING NOT YET FORMALLY REGISTERED** | integration health, provider mode/config, dependency evidence | posture/trust/certification consumers | provider-specific | missing / degraded / blocked / unknown | dependency posture | affects continuity and certification scope |

## 19. Evidence Taxonomy

A weaker evidence class shall never be presented as a stronger evidence class.

### Constitutional Evidence Rules

1. Missing retention policy does not invalidate the existence of evidence, but it prevents claims of retention conformance.
2. Missing lineage downgrades any claim dependent on origin, scope, environment, or actor identity.
3. Operator acknowledgement is not proof that the underlying condition was corrected.
4. An approved exception is not proof of conformance.
5. External dependency configuration is not proof of external dependency availability.
6. A queued notification is not provider-acceptance evidence.
7. A safe-captured notification is not production delivery evidence.
8. A trust score is not certification evidence.
9. A successful execution row is not proof of full outcome integrity unless outcome evidence exists.
10. A deployment decision is not recovery certification.

### Hardened Evidence Taxonomy

| Evidence Class | Purpose | Canonical / Expected Source Category | Required Durability | Required Freshness Treatment | Required Retention Treatment | Redaction Requirement | Lineage Requirement | Permitted Claim | Prohibited Overclaim | Preview Eligibility | Production Eligibility | Certification Significance | Current Implementation Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Execution evidence | Prove action attempt or completion state | job ledgers, execution rows, runtime state | durable | evaluate against task cadence / action window | retain per operational policy | secret-free when surfaced | actor/system/time/scope linkage required | action executed or attempted | does not alone prove outcome integrity | yes | yes | supporting only | implemented across backup/restore/scheduler paths |
| Scheduler evidence | Prove slot claim, dedup, scheduler liveness | `scheduler_runs`, locks, heartbeat state | durable + runtime | slot and heartbeat windows | retain run history per policy | secret-free | slot key and owner linkage required | slot ownership / duplicate prevention | not proof of archive presence by itself | yes | yes | supporting only | implemented |
| Archive evidence | Prove archive presence and basic object facts | `backup_health`, R2 object metadata | durable | compare against archive freshness policy | retain per retention policy | secret-free | archive/object/environment linkage required | archive exists | not proof of integrity or restorability | yes | yes | supports Class 1 | implemented |
| Integrity evidence | Prove archive readability / contract validity | manifest read and integrity workflows | durable | compare against integrity recertification window | retain verifier result per policy | secret-free | verifier/version/archive linkage required | archive integrity verified | not proof of restore exercise | yes | yes | supports Class 2 | implemented in bounded form |
| Lineage evidence | Prove archive origin, environment, database, and source identity | archive manifest, origin validation, environment identity | durable | freshness tied to archive and environment scope | retain with archive evidence | secret-free in operator surfaces | mandatory environment/db/source linkage | archive belongs to stated origin | cannot be omitted for cross-environment claims | yes | yes | required for many recovery claims | partially implemented |
| Restore evidence | Prove restore execution occurred | restore job rows, replay result, audit | durable | tied to restore event date | retain per restore policy | redact secrets and sensitive payloads | scope / actor / target linkage required | restore action succeeded/failed in stated scope | not proof of full-platform recovery unless class-qualified | yes | yes | supports Classes 3–5 depending on scope | implemented |
| Drill evidence | Prove an exercise occurred | `drill_runs`, related audit, operator evidence | durable | recertification-window dependent | retain exercise history | secret-free when surfaced | exercise/scope/archive linkage required | drill occurred in stated scope | not proof of broader scope | yes | yes | supports exercise classes | partially implemented |
| Representative drill evidence | Prove a bounded representative restore exercise | bounded drill artefacts | durable | recertification-window dependent | retain with drill history | secret-free when surfaced | mandatory scope boundary | representative restore succeeded | not full-platform proof | yes | yes | supports Class 3 | partially implemented |
| Full-platform recovery evidence | Prove integrated platform restore exercise | integrated platform exercise package | durable | recertification-window dependent | retain under protected exercise history | redaction required before broad exposure | full platform scope and dependency lineage required | full-platform restore exercised | not DR or BC proof by itself | possibly | yes when actually production-backed | supports Class 5 | not yet implemented/proven |
| Notification evidence | Prove dispatch path behavior | delivery rows, audit, capture rows | durable | evaluate per message/event | retain message evidence per policy | redact recipients/content as required | workflow/message correlation required | notification was queued/captured/accepted/blocked | queued != accepted; capture != production delivery | yes | yes | supporting only | implemented |
| Provider-acceptance evidence | Prove provider accepted delivery | provider-live acceptance result | durable | tied to message event time | retain per policy | redact secrets; limit recipient disclosure | provider/message/workflow linkage required | provider accepted message | not proof of recipient read or BC continuity alone | no | yes | bounded delivery proof only | implemented where provider-live exists |
| Safe-capture evidence | Prove preview/test capture without external send | capture store and preview delivery state | durable | tied to preview/test event time | retain per preview evidence policy | secret-free where practical | workflow/message/environment linkage required | preview capture occurred | not production delivery evidence | yes | no | preview-only proof | implemented |
| Trust evidence | Explain why trust is healthy or degraded | trust spine events, trust inputs, penalty records | durable | tied to underlying evidence freshness | retain trust history per policy | secret-free when surfaced | source-evidence linkage required | trust rationale | not certification evidence | yes | yes | informative only | implemented |
| Audit evidence | Prove actor/system action and trace | `admin_audit`, `audit_events`, operations audit | durable | tied to event time | retain per audit policy | redact secrets and sensitive payloads | actor/time/action linkage required | action occurred | not proof of conformance by itself | yes | yes | supporting only | implemented |
| Certification evidence | Prove a bounded certification decision | class decision records, review outcomes, gate results | durable | certification-window dependent | retain certification history | secret-free for operator surfaces | decision scope and evidence linkage required | bounded certification claim | not proof outside its bounded class | yes if preview-scoped | yes if production-scoped | direct certification evidence | partially implemented |
| Deployment decision evidence | Prove deployment-readiness decision | `deployment_decisions` | durable | tied to release decision window | retained with TTL per ledger policy | secret-free | verification scope and release linkage required | deployment readiness decision | not recovery certification | yes | yes | deployment-only | implemented |
| External dependency evidence | Prove dependency continuity posture | integration health/config surfaces, provider contract, telemetry | durable | provider and polling cadence dependent | retain dependency history per policy | secrets redacted | dependency/source/environment linkage required | dependency configured/degraded/healthy in stated scope | config != availability; one provider != continuity certification | yes | yes | supporting only | partially implemented |
| Capacity evidence | Prove storage/resource risk posture | bucket usage rows, trend data, resource preflight | durable | threshold-window dependent | retain history sufficient for trend | secret-free | storage scope / timestamp linkage required | capacity risk exists or not | not proof that retention policy is sufficient | yes | yes | supporting only | partially implemented |
| Failure evidence | Prove degradation, blocker, or failed path | failed events, failed jobs, blockers, denial rows | durable | immediate and historical | retain failure history per policy | secret-free when surfaced | actor/system/time/path linkage required | failure occurred | acknowledgement != correction | yes | yes | may block claims | implemented |
| Operator acknowledgement evidence | Prove a human acknowledged a condition | future acknowledgement records | durable | tied to acknowledgement time only | retain per governance policy | actor identity required; secret-free | actor/time/condition linkage required | operator acknowledged condition | not proof of remediation or reduced risk | yes | yes | supporting only | not yet implemented |
| Exception evidence | Prove an approved deviation exists | ADR / constitutional exception record | durable | valid only until expiry or withdrawal | retain full historical record | secret-free summary; sensitive detail redacted if needed | rule/owner/risk/expiry linkage required | approved exception exists | not proof of conformance; expired exception is non-conforming | yes | yes | may explain deviation only | not yet implemented |
| Preview evidence | Prove a claim in preview scope | preview-generated evidence of any relevant class | durable | freshness tied to preview claim | retain per evidence policy | environment scope explicit | preview environment linkage mandatory | preview-scoped claim | not production proof | yes | no | preview-only | implemented in multiple bounded areas |
| Production evidence | Prove a claim in production scope | production-generated evidence of any relevant class | durable | freshness tied to production claim | retain per evidence policy | appropriate redaction required | production environment linkage mandatory | production-scoped claim | not broader claim than evidence scope | no | yes | required for production certification | partially implemented / not uniformly current |

## 20. Recovery Certification Classes

### Class Structure

**Foundational Recovery Classes**
- Class 0 — Not Yet Exercised
- Class 1 — Archive Presence Verified
- Class 2 — Archive Integrity Verified
- Class 3 — Representative Restore Exercised
- Class 4 — Subsystem Recovery Exercised
- Class 5 — Full-Platform Restore Exercised

**Advanced Exercise Classes**
- Class 6 — Disaster Recovery Exercised
- Class 7 — Business Continuity Exercised

**Final Production Certification**
- Class 8 — Production Recovery Certified

### Non-Linearity Rule

Classes 6 and 7 represent distinct advanced exercise dimensions and are **not inherently sequential relative to each other**. Neither Class 6 nor Class 7 automatically implies attainment of the other. Class 8 may require one, both, or a formally approved subset of Classes 6 and 7 depending on certification scope and criticality policy. No class automatically inherits unsupported evidence from another class.

| Class | Name | Minimum Evidence | Allowed Claim | Prohibited Claim | Environment Requirements | Scope | Freshness / Expiration | Independent Review | Recertification Expectations |
|---|---|---|---|---|---|---|---|---|---|
| 0 | NOT YET EXERCISED | no exercised recovery proof | no exercised recovery claim | any exercised recovery capability | any | none | immediate | not applicable | not applicable |
| 1 | ARCHIVE PRESENCE VERIFIED | archive evidence | archive exists | archive integrity or restorability | preview or production | archive presence only | archive freshness policy | recommended | **POLICY VALUE REQUIRED — NOT YET CONSTITUTIONALLY APPROVED** |
| 2 | ARCHIVE INTEGRITY VERIFIED | archive evidence + integrity evidence | archive is structurally valid and contract-verified | restore exercised | preview or production | archive integrity only | integrity freshness policy | recommended | **POLICY VALUE REQUIRED — NOT YET CONSTITUTIONALLY APPROVED** |
| 3 | REPRESENTATIVE RESTORE EXERCISED | representative drill evidence | bounded representative restore succeeded | subsystem, full-platform, DR, or BC proof | environment and scope explicit | representative subset only | drill freshness policy | required | **POLICY VALUE REQUIRED — NOT YET CONSTITUTIONALLY APPROVED** |
| 4 | SUBSYSTEM RECOVERY EXERCISED | subsystem restore evidence | named subsystem recovery exercised | full-platform, DR, or BC proof | environment and scope explicit | subsystem only | subsystem recertification window | required | **POLICY VALUE REQUIRED — NOT YET CONSTITUTIONALLY APPROVED** |
| 5 | FULL-PLATFORM RESTORE EXERCISED | integrated full-platform restore evidence | full-platform restore exercised | DR or BC proof unless separately evidenced | environment and dependency scope explicit | integrated platform restore | full-platform recertification window | required | **POLICY VALUE REQUIRED — NOT YET CONSTITUTIONALLY APPROVED** |
| 6 | DISASTER RECOVERY EXERCISED | DR exercise evidence including infrastructure/config/dependency reconstruction as scoped | bounded DR exercise completed | BC proof or production certification unless separately evidenced | environment and disaster scenario explicit | DR exercise scope | DR recertification window | required | **POLICY VALUE REQUIRED — NOT YET CONSTITUTIONALLY APPROVED** |
| 7 | BUSINESS CONTINUITY EXERCISED | BC exercise evidence including degraded-operation continuity as scoped | bounded BC exercise completed | DR proof or production certification unless separately evidenced | environment and continuity scenario explicit | BC exercise scope | BC recertification window | required | **POLICY VALUE REQUIRED — NOT YET CONSTITUTIONALLY APPROVED** |
| 8 | PRODUCTION RECOVERY CERTIFIED | production evidence, approved class prerequisites, current blockers cleared, independent verification complete | production recovery certified for stated scope only | any claim beyond certified scope or stale evidence | production only | approved certified scope | certification expiry policy | mandatory | **POLICY VALUE REQUIRED — NOT YET CONSTITUTIONALLY APPROVED** |

### Current Attainment Boundary

The reviewed repository supports foundational archive, integrity, representative drill, and posture/trust patterns. It does **not** by itself prove current attainment of Class 6, Class 7, or Class 8.

## 21. RPO/RTO and Criticality Governance

### Constitutional Requirement

BCSS shall govern:
- RPO
- RTO
- Maximum Tolerable Downtime
- Minimum Business Continuity Objective
- dependency recovery sequence
- data criticality
- service criticality
- operational tiering

### Criticality Classes

- Constitutional Core
- Critical Operations
- Operationally Important
- Supporting
- Noncritical
- Excluded by approved exception

### Policy Rule

If an RPO, RTO, or criticality value is not formally approved, the constitution shall mark it:

**POLICY VALUE REQUIRED — NOT YET CONSTITUTIONALLY APPROVED**

### Verified Current State

The code contains default posture values for backup-related objectives, but they are implementation defaults, not constitutionally approved policy:
- `BACKUP_RPO_TARGET_MINUTES` default 60
- `BACKUP_RTO_TARGET_MINUTES` default 15
- `BACKUP_AGE_TARGET_HOURS` default 24  
  (`backend/routes/recovery_dashboard.py:322-324`)

Accordingly, those defaults are verified implementation behavior, not final constitutional policy.

## 22. Backup Governance

### Verified Current State

- backup execution can be hourly/nightly depending on activation logic (`backend/server.py:10395-10470`)
- activation state depends on scheduler health, persistence, overlap, stale jobs, retention validity, resource preflight, and environment (`backend/server.py:7871-7905`)
- retention policy is currently encoded as selected surviving hourly archives with 72h/30d/90d/12mo tiers (`backend/server.py:10048-10054`; `backend/server.py:7855-7867`)
- verification cross-checks local ledger and R2 (`backend/backup_verification.py:323-467`)

### Constitutional Requirement

Backup governance shall define:
- what is backed up
- by which mechanism
- under which authority
- at what cadence
- with what retention
- with what verification class
- with what archive lineage requirements
- with what failure evidence
- with what operator truth surface

Backup governance shall not be reduced to archive creation alone.

## 23. Recovery Governance

### Verified Current State

- restore requires admin-strict authorization (`backend/server.py:12395`)
- restore is blocked while backup jobs are active (`backend/server.py:12407-12410`)
- restore validates archive manifest and origin environment/database (`backend/server.py:12484-12588`)
- dry-run is supported (`backend/server.py:12722-12747`)
- replay result is summarized with processed/failed counts (`backend/server.py:12833-12864`)

### Constitutional Requirement

Recovery governance shall define:
- allowed recovery modes
- dry-run vs destructive restore
- merge vs replace semantics
- evidence required before and after recovery
- scope classification
- post-recovery reconciliation expectations
- authorization and separation of duties
- current blockers and warnings
- evidence class used for any claim

## 24. Disaster Recovery Governance

### A. Verified Current State

The reviewed repository supports meaningful application-level recovery patterns including archive creation, archive verification, restore guardrails, restore audit, and operator-facing posture/trust/certification support. Evidence includes backup verification, restore origin validation, and bounded certification surfaces (`backend/backup_verification.py:315-467`; `backend/server.py:12388-12864`; `backend/routes/admin_deployment_readiness.py:72-393`).

### B. Constitutional Requirement

Disaster Recovery shall include governance for:
- infrastructure loss
- runtime environment loss
- database loss
- storage loss
- credential/secret loss
- configuration loss
- provider loss
- code repository loss
- deployment pipeline loss
- regional failure
- corrupted archive
- compromised archive
- compromised administrator account
- destructive operator action
- ransomware or malicious modification
- systemic data corruption

Disaster Recovery is broader than an application-level restore. It requires governance for:
- infrastructure reconstruction
- configuration recovery
- secret recovery
- dependency restoration
- environment identity validation
- code/deployment recovery
- recovery command structure
- recovery evidence package
- independent certification

### C. Current Evidence Limitation

The reviewed repository does **not**, by itself, prove a complete implemented Disaster Recovery program. It does **not** by itself prove infrastructure reconstruction, secret recovery, provider substitution, command-authority exercise, regional failover, or complete disaster-recovery certification. These remain constitutional obligations and future conformance requirements, not verified implemented capabilities. No wording in this constitution shall be interpreted as current attainment of Class 6 or Class 8.

## 25. Business Continuity Governance

### A. Verified Current State

The reviewed repository supports partial continuity-aware behavior, including dependency-aware notification modes, scheduler liveness fallback logic, storage/capacity warnings, and explicit preview-vs-production recovery posture distinctions (`backend/lib/notification_delivery.py:70-137`; `backend/routes/recovery_dashboard.py:488-629`).

### B. Constitutional Requirement

Business continuity shall govern:
- degraded operation
- partial service availability
- loss of external provider
- loss of notification provider
- loss of storage provider
- database interruption
- scheduler interruption
- identity interruption
- authorization interruption
- AI service interruption
- field connectivity interruption
- mobile/offline operation
- operator communications
- manual fallback procedures
- recovery command authority
- operational prioritization
- restoration sequencing
- post-recovery reconciliation
- recovery evidence
- executive decision support

### C. Current Evidence Limitation

The reviewed repository does **not**, by itself, prove a complete implemented Business Continuity program. It does **not** by itself prove provider substitution, manual field fallback, command-authority exercise, regional continuity, or complete business-process continuity. These remain constitutional obligations and future conformance requirements, not verified implemented capabilities. No wording in this constitution shall be interpreted as current attainment of Class 7 or Class 8.

## 26. Capacity and Retention Governance

### Verified Current State

- retention policy is coded centrally in scheduler/backups state (`backend/server.py:10048-10054`)
- retention validity is evaluated (`backend/server.py:7855-7867`)
- bucket usage thresholds are surfaced (`backend/routes/recovery_dashboard.py:325-326, 442-465`)
- capacity penalties affect trust (`backend/lib/trust_score.py:244-249`)

### Constitutional Requirement

Capacity and retention governance shall cover:
- retention classes
- deletion protections
- minimum archive history
- long-term evidence retention
- legal/operational holds
- storage utilization
- projected exhaustion
- alert thresholds
- capacity warnings
- protected recovery points
- immutable recovery points where required

Retention shall not be scattered across modules. One canonical retention policy shall govern, with domain-specific extensions only by approved exception.

## 27. Access Governance

### Survivability-Sensitive Action Classes

- View posture
- View evidence
- Execute verification
- Execute backup
- Execute dry-run restore
- Execute destructive restore
- Approve production recovery
- Certify recovery
- Modify retention policy
- Modify activation state
- Modify dependency configuration
- Acknowledge BCSS warning
- Override constitutional control
- Approve exception

### Constitutional Requirement

BCSS access governance shall enforce:
- least privilege
- separation of duties
- elevated approval for destructive actions
- complete audit evidence
- centralized policy convergence
- no hidden route-local bypass
- emergency access governance
- break-glass evidence
- post-use review

### Approval Authority Pending-State Rule

Where a required approval authority has not yet been formally designated, mark:

**APPROVAL AUTHORITY REQUIRED — NOT YET CONSTITUTIONALLY DESIGNATED**

This pending state does not authorize unrestricted action. It requires the affected action to remain governed by existing stricter controls or fail closed until approved authority is established.

This pending-state rule applies where relevant to:
- destructive restore
- production recovery approval
- constitutional exception approval
- break-glass use
- retention-policy override
- recovery certification
- constitutional adoption/amendment

### Verified Current State

- high-risk restore and backup-sensitive surfaces use admin-strict dependencies (`backend/server.py:868-923, 11683-11729, 12388-12395`)
- centralized RBAC library exists but is explicitly non-enforcing (`backend/lib/rbac.py:7-10`)
- some governance routes still depend on `require_admin` rather than a clearly declared super-admin-only contract (`backend/routes/operations_control.py:1-5, 62-120`)

This is partial conformance, not centralized survivability policy convergence.

## 28. Operator Experience and Truth Surfaces

### Constitutional Requirement

Every BCSS operator surface shall be:
- truthful
- understandable
- action-oriented
- evidence-linked
- severity-consistent
- mobile-capable where operationally required
- explicit about Preview vs Production
- explicit about stale vs fresh evidence
- explicit about representative vs full recovery
- explicit about active blockers
- free of fake green states

### Canonical Operator Concepts

Every canonical BCSS operator surface should eventually express, where applicable:
- Current posture
- Current risk
- Current recovery class
- Last verified archive
- Last successful restore drill
- Last full-platform exercise
- Current backup cadence
- Activation state
- Capacity posture
- Dependency posture
- Current blockers
- Required operator action
- Evidence link
- Certification status

### Verified Current State

Current surfaces already distinguish:
- representative vs full recovery (`backend/routes/recovery_dashboard.py:618-621`)
- preview vs production (`backend/routes/recovery_dashboard.py:622-629`)
- active warnings/blockers (`backend/routes/recovery_dashboard.py:530-569`)
- anti-fake-green lifecycle trust (`backend/routes/admin_trust_spine.py:149-173`)
- explicit penalties in trust score (`backend/lib/trust_score.py:213-267`)

No new duplicate dashboard is authorized by this constitution.

## 29. KPI and Trust Governance

### Constitutional Separation

BCSS shall distinguish:
- factual status
- KPI
- trust score
- verification verdict
- certification decision
- deployment decision
- warning
- blocker
- operator data issue
- system defect

### BCSS KPI Glossary

At minimum:
- Archive freshness
- Backup execution success
- Scheduler reliability
- Restore drill age
- Restore success
- Integrity verification
- Lineage confidence
- Capacity risk
- Dependency continuity
- Certification freshness
- Evidence completeness
- Unresolved BCSS failures
- Overlap/rejection rate
- Stale job rate
- Recovery readiness class
- RPO compliance
- RTO compliance where exercised

### Constitutional Rules

1. A composite trust score shall always expose material penalties and underlying evidence.
2. A trust score is not certification evidence.
3. Deployment certification and recovery certification shall never be conflated in operator surfaces, KPI summaries, audit evidence, or documentation.

### Verified Current State

The platform already exposes transparent trust penalties in backup trust score (`backend/lib/trust_score.py:213-267`) and separates deploy blockers from advisory operator data issues (`backend/routes/admin_deployment_readiness.py:150-393`).

## 30. Automatic Survivability Registration

### Constitutional Requirement

Every future module with persistent operational impact shall eventually register:
- subsystem identity
- business owner
- technical owner
- data stores
- data classifications
- backup method
- restore method
- dependencies
- recovery order
- RPO requirement
- RTO requirement
- retention class
- evidence class
- notification requirements
- Trust Spine participation
- certification requirements
- test requirements
- exclusion rationale if applicable

This registration shall extend the existing canonical truth model or another verified canonical registry. It shall not become an ungoverned parallel system.

### Verified Current State

The current repository includes a canonical truth registry framework but not formal BCSS survivability registration entries (`backend/lib/canonical_truth.py:68-307, 326-345`).

## 31. Constitutional Impact Analysis

Every material change shall answer:

1. Which BCSS truth subjects are affected?  
2. Which canonical owners are affected?  
3. Which persistent operational data is created, changed, moved, or retired?  
4. Which backup behavior changes?  
5. Which restore behavior changes?  
6. Which recovery dependencies change?  
7. Which Trust Spine events change?  
8. Which audit evidence changes?  
9. Which notifications change?  
10. Which KPIs change?  
11. Which dashboards or operator surfaces change?  
12. Which certification rules change?  
13. Which Deployment Gate checks change?  
14. Which access permissions change?  
15. Which retention rules change?  
16. Which evidence classes change?  
17. Which Business Continuity procedures change?  
18. Which Disaster Recovery procedures change?  
19. Does the change introduce duplicate architecture?  
20. Does the change require a constitutional amendment or approved exception?  

Constitutional Impact Analysis shall be a release requirement for material changes.

## 32. Conformance Lifecycle

### Conformance Classification Model

1. **FULLY CONFORMS**  
   Verified behavior, ownership, registration, evidence, and constitutional integration are complete.
2. **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING**  
   Current implementation materially behaves in alignment with BCSS, but formal BCSS ownership or registration is incomplete.
3. **PARTIALLY CONFORMS**  
   Some required behavior or governance exists, but one or more material requirements remain incomplete.
4. **REQUIRES MODIFICATION**  
   A verified conflict, defect, contradiction, or missing required capability exists.
5. **OUT OF SCOPE / INFORMATIVE**  
   The system is not a BCSS owner but may supply a reusable pattern or evidence reference.

### Continuous Conformance Lifecycle

1. Discover  
2. Verify repository reality  
3. Map canonical ownership  
4. Classify conformance  
5. Identify gaps  
6. Prioritize remediation  
7. Implement through bounded tracks  
8. Test  
9. Independently verify  
10. Certify  
11. Deploy through approved gate  
12. Monitor  
13. Exercise recovery  
14. Reassess after material change  
15. Record evidence  
16. Update conformance status

Conformance is not a one-time cleanup project.

## 33. Exceptions and ADRs

Any constitutional deviation requires a version-controlled Architectural Decision Record containing:
- unique ID
- date
- owner
- affected subsystem
- affected BCSS truth subject
- exact constitutional rule affected
- reason existing canonical architecture cannot be extended
- risk
- mitigation
- duration
- whether temporary or permanent
- approval authority
- monitoring requirement
- retirement or reassessment date
- evidence
- independent review where material

No undocumented exception is permitted.

### Temporary Exception Expiry Rule

A temporary constitutional exception automatically becomes:

**EXPIRED — NON-CONFORMING**

at its expiration date unless renewed through the complete evidence-backed approval process before expiry.

Expiration shall:
- restore the original constitutional obligation
- prohibit continued representation as an approved exception
- create an active conformance finding
- require operator visibility where the risk remains material
- prohibit silent extension
- preserve the complete historical exception record

An expired exception may not be treated as grandfathered approval.

## 34. Constitutional Change Control

### Version Model

- **PATCH** — clarification that does not alter obligations
- **MINOR** — new compatible requirements
- **MAJOR** — material change to constitutional ownership, authority, or architecture

### Required Change Inputs

- version history
- change summary
- affected sections
- rationale
- repository evidence
- impact analysis
- backward compatibility assessment
- independent architectural review
- approval
- effective date
- migration implications
- conformance implications

No silent constitutional drift is allowed.

## 35. Platform Conformance Matrix

| Subsystem | Verified Current Behavior | Constitutional Expectation | Final Classification | Exact Evidence | Required Future Conformance |
|---|---|---|---|---|---|
| Database Authority | Validates runtime DB legitimacy and publishes authority payload | One canonical runtime authority | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/lib/database_authority.py:64-101, 166-210` | Register under BCSS truth subjects |
| Backup Runtime | Durable backup/restore job state with overlap guard and stale recovery | Canonical long-running execution owner | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/lib/backup_runtime.py:56-145, 161-234` | Formalize BCSS ownership |
| Scheduler Runs | Atomic slot claim and run history | Canonical scheduled execution evidence | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/lib/scheduler_runs.py:97-161, 164-246` | Map into BCSS registry |
| Weekly Backup Verification | R2 + ledger cross-check and dispatch | Canonical archive verification authority | **PARTIALLY CONFORMS** | `backend/backup_verification.py:315-467, 669-771` | Map to evidence taxonomy and certification classes |
| Recovery Dashboard | Single recovery posture snapshot with warnings and distinctions | Canonical recovery posture aggregator | **PARTIALLY CONFORMS** | `backend/routes/recovery_dashboard.py:571-631` | Declare formal BCSS truth role and evidence-class bindings |
| Backup Trust Score | Deterministic recovery trust score | Derived consumer only | **PARTIALLY CONFORMS** | `backend/server.py:11952-12021`; `backend/lib/trust_score.py:202-268` | Register as derived consumer and bind claim classes |
| Restore Endpoint | Admin-strict, origin-aware, dry-run capable restore | Canonical restore execution owner | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/server.py:12388-12864` | Add formal BCSS truth ownership |
| Trust Spine | Canonical lifecycle evidence model | BCSS lifecycle evidence should extend, not bypass | **PARTIALLY CONFORMS** | `backend/lib/trust_spine.py:1-40, 187-284` | Extend or map BCSS lifecycle evidence |
| Admin Trust Spine Rollup | Anti-fake-green trust rollup | Valid derived lifecycle trust consumer | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/routes/admin_trust_spine.py:34-228` | Map BCSS event categories when extended |
| Operations Trust Center | Derived cross-system trust scoring | Derived consumer only | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/routes/admin_operations_trust_center.py:297-320` | Include BCSS-specific mappings through existing architecture |
| OCC Trust Events | Unified trust event aggregation | Aggregator only | **PARTIALLY CONFORMS** | `backend/routes/occ_trust_events.py:152-235` | Correct endpoint mismatch and preserve bounded role |
| Deployment Readiness | Code-vs-data blocker classification | Certification gate must remain bounded and explicit | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/routes/admin_deployment_readiness.py:72-403` | Add BCSS class references and transparency hardening |
| Deployment Ledger | Append-only decision evidence | Certification evidence should be immutable | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/routes/admin_deployment_ledger.py:42-97, 103-156` | Extend for BCSS recovery certification if needed |
| Notification Delivery Contract | Preview safe-capture vs production live separation | Continuity communication truth must remain environment-aware | **BEHAVIORALLY CONFORMS — CONSTITUTIONAL REGISTRATION PENDING** | `backend/lib/notification_delivery.py:70-137`; `backend/tests/test_c2_phase2_notification_contract.py:34-155` | Ensure all BCSS messaging uses this contract |
| Integration Center | Existing provider health/config | Dependency continuity should extend this system | **PARTIALLY CONFORMS** | `backend/routes/integrations/config.py:174-202` | Add BCSS dependency classification |
| RBAC Library | Centralized but non-enforcing | Central survivability policy convergence required | **REQUIRES MODIFICATION** | `backend/lib/rbac.py:7-10, 323-391` | Converge enforcement later through bounded track |
| Canonical Truth Registry | Shared truth role model exists, BCSS entries absent | BCSS truth subjects must be registered | **REQUIRES MODIFICATION** | `backend/lib/canonical_truth.py:68-307, 326-345` | Register BCSS surfaces |
| Operations Control auth contract | Docstring says super-admin; routes use `require_admin` | High-risk governance auth semantics must be unambiguous | **REQUIRES MODIFICATION** | `backend/routes/operations_control.py:1-5, 62-120` | Align declaration and implementation |
| Daily Report manifest pattern | Strong evidence contract exists in one domain | Reusable evidence pattern, not BCSS owner | **OUT OF SCOPE / INFORMATIVE** | `backend/services/dr_evidence/manifest.py:268-382, 387-439` | Reuse pattern where appropriate |

## 36. Remediation Register

### BCSS-R01 — BCSS truth subjects absent from canonical truth registry
- **Priority:** P0
- **Constitutional sections:** 18, 30, 39
- **Current verified state:** canonical truth registry exists, but reviewed registered surfaces do not include BCSS truth subjects.
- **Gap:** BCSS ownership is not formally registered.
- **Required future state:** all ten BCSS truth subjects registered with owner roles and upstream references.
- **Exact repository evidence:** `backend/lib/canonical_truth.py:68-307, 326-345`
- **Dependencies:** none
- **Upstream dependencies:** none
- **Downstream dependents:** BCSS-R03, BCSS-R08, BCSS-R12, BCSS-R13, BCSS-R15
- **Explicitly In Scope:** formal registration of BCSS truth subjects and canonical ownership
- **Explicitly Out of Scope:** evidence-class binding, recovery certification classes, future-module registration workflow design
- **Completion Boundary:** registration is complete when all ten truth subjects are declared with one owner role each and no owner conflicts
- **Non-Duplication Statement:** this item governs **formal registration only**; it does not govern posture/trust separation, evidence taxonomy, certification classes, or future-module registration
- **Bounded-track recommendation:** truth-subject registration track
- **Measurable completion criteria:** all ten BCSS truth subjects present with one owner each and no owner conflict findings
- **Required tests:** registry validation tests
- **Required independent evidence:** read-only registry review
- **Deployment impact:** low direct runtime impact, high governance value
- **Conformance status:** Open

### BCSS-R02 — Backup recency precedence is distributed
- **Priority:** P0
- **Constitutional sections:** 13, 18, 29
- **Current verified state:** backup recency is derived in multiple places with overlapping precedence logic.
- **Gap:** no single constitutional precedence contract exists.
- **Required future state:** one declared archive-lineage precedence policy used across posture/trust/health surfaces.
- **Exact repository evidence:** `backend/server.py:1561-1605`; `backend/routes/recovery_dashboard.py:328-379`
- **Dependencies:** BCSS-R01
- **Bounded-track recommendation:** archive-lineage convergence track
- **Measurable completion criteria:** one shared precedence rule documented and consumed by all relevant surfaces
- **Required tests:** parity tests across health/snapshot/trust surfaces
- **Required independent evidence:** read-only endpoint comparison
- **Deployment impact:** medium
- **Conformance status:** Open

### BCSS-R03 — Recovery posture and recovery trust roles are not formally separated
- **Priority:** P0
- **Constitutional sections:** 18, 19, 20, 29, 39
- **Current verified state:** recovery snapshot and backup trust score use overlapping evidence but role boundaries are implicit.
- **Gap:** posture owner vs trust derived-consumer roles are not formally declared and registered.
- **Required future state:** explicit role separation with correct truth-subject mapping.
- **Exact repository evidence:** `backend/routes/recovery_dashboard.py:571-631`; `backend/server.py:11952-12021`; `backend/lib/trust_score.py:202-268`
- **Dependencies:** BCSS-R01
- **Upstream dependencies:** BCSS-R01
- **Downstream dependents:** BCSS-R12, BCSS-R13
- **Explicitly In Scope:** formal separation of recovery posture and recovery trust roles
- **Explicitly Out of Scope:** evidence taxonomy adoption, certification class adoption, future-module registration contract
- **Completion Boundary:** complete when posture and trust each have explicit truth roles and no ambiguity remains in operator/certification use
- **Non-Duplication Statement:** this item governs **role separation only**; it does not govern evidence taxonomy or class implementation
- **Bounded-track recommendation:** posture/trust role registration track
- **Measurable completion criteria:** each surface declares canonical/derived role and upstream evidence
- **Required tests:** contract tests for role metadata if exposed
- **Required independent evidence:** architectural review
- **Deployment impact:** low-medium
- **Conformance status:** Open

### BCSS-R04 — BCSS event model is incomplete
- **Priority:** P0
- **Constitutional sections:** 17, 19, 29
- **Current verified state:** Trust Spine is workflow-centered; BCSS-specific lifecycle evidence is not constitutionally mapped.
- **Gap:** backup/restore/verification/certification events are not fully mapped to BCSS truth subjects.
- **Required future state:** BCSS lifecycle evidence model extending existing Trust Spine patterns.
- **Exact repository evidence:** `backend/lib/trust_spine.py:1-40, 50-82`; `backend/server.py:11200-11380`
- **Dependencies:** BCSS-R01
- **Bounded-track recommendation:** BCSS lifecycle evidence extension track
- **Measurable completion criteria:** BCSS event classes and mappings documented and emitted where required
- **Required tests:** event-contract tests
- **Required independent evidence:** drill-through trust review
- **Deployment impact:** medium
- **Conformance status:** Open

### BCSS-R05 — Access governance remains distributed
- **Priority:** P1
- **Constitutional sections:** 27, 39
- **Current verified state:** route-local guards protect survivability-sensitive actions; centralized RBAC is not yet enforcing.
- **Gap:** survivability policy is not centrally enforced.
- **Required future state:** centralized survivability-sensitive policy convergence.
- **Exact repository evidence:** `backend/lib/rbac.py:7-10`; `backend/server.py:868-923`
- **Dependencies:** none
- **Bounded-track recommendation:** survivability access convergence track
- **Measurable completion criteria:** approved central policy path for defined action classes
- **Required tests:** authz regression matrix
- **Required independent evidence:** read-only permission review
- **Deployment impact:** high
- **Conformance status:** Open

### BCSS-R06 — Operations Control auth declaration mismatch
- **Priority:** P1
- **Constitutional sections:** 10, 27, 35
- **Current verified state:** route file header claims super-admin authentication, but endpoints depend on `require_admin`.
- **Gap:** declaration and implementation are not aligned.
- **Required future state:** one explicit access contract reflected in both documentation and code.
- **Exact repository evidence:** `backend/routes/operations_control.py:1-5, 62-120`
- **Dependencies:** BCSS-R05
- **Bounded-track recommendation:** governance auth alignment track
- **Measurable completion criteria:** route contract and implementation match
- **Required tests:** endpoint auth matrix
- **Required independent evidence:** read-only route/audit review
- **Deployment impact:** medium
- **Conformance status:** Open

### BCSS-R07 — External dependency survivability is not centralized
- **Priority:** P1
- **Constitutional sections:** 18, 25, 29
- **Current verified state:** integration health exists, but dependency continuity is not formalized as a BCSS truth subject.
- **Gap:** dependency continuity lacks explicit BCSS ownership and class rules.
- **Required future state:** external dependency continuity truth formally declared.
- **Exact repository evidence:** `backend/routes/integrations/config.py:174-202`; `backend/lib/notification_delivery.py:70-137`
- **Dependencies:** BCSS-R01
- **Bounded-track recommendation:** dependency continuity mapping track
- **Measurable completion criteria:** dependency inventory and truth-role mapping documented
- **Required tests:** dependency health contract tests
- **Required independent evidence:** read-only dependency review
- **Deployment impact:** medium
- **Conformance status:** Open

### BCSS-R08 — Recovery evidence classes are not standardized as a governance standard
- **Priority:** P1
- **Constitutional sections:** 19, 20, 39
- **Current verified state:** multiple evidence forms exist without a shared BCSS taxonomy.
- **Gap:** evidence class inflation risk.
- **Required future state:** shared BCSS evidence taxonomy adopted as a governance standard.
- **Exact repository evidence:** `backend/backup_verification.py:315-467`; `backend/routes/recovery_dashboard.py:571-631`; `backend/server.py:11952-12021`
- **Dependencies:** BCSS-R01
- **Upstream dependencies:** BCSS-R01
- **Downstream dependents:** BCSS-R12, BCSS-R13
- **Explicitly In Scope:** adoption of the shared BCSS evidence taxonomy as a governance standard
- **Explicitly Out of Scope:** surface-level evidence-class labels and certification-class adoption
- **Completion Boundary:** taxonomy approved and referenced as governing standard for BCSS evidence classes
- **Non-Duplication Statement:** this item governs **taxonomy adoption only**; it does not govern UI/API labeling or certification-class adoption
- **Bounded-track recommendation:** evidence taxonomy adoption track
- **Measurable completion criteria:** evidence classes referenced in BCSS governance artefacts and implementation planning
- **Required tests:** evidence classification contract tests
- **Required independent evidence:** read-only claim-vs-evidence review
- **Deployment impact:** medium
- **Conformance status:** Open

### BCSS-R09 — Full-platform restore certification remains unproven
- **Priority:** P1
- **Constitutional sections:** 20, 23, 24, 39
- **Current verified state:** recovery snapshot explicitly states full-platform restore not yet exercised.
- **Gap:** full-platform recovery certification cannot be claimed.
- **Required future state:** full-platform restore classified and eventually exercised against the approved certification-class model.
- **Exact repository evidence:** `backend/routes/recovery_dashboard.py:618-629`
- **Dependencies:** BCSS-R13
- **Bounded-track recommendation:** full-platform recovery certification track
- **Measurable completion criteria:** full-platform restore evidence classified against approved class model; unsupported claims removed
- **Required tests:** recovery class presentation tests
- **Required independent evidence:** independent recovery certification review
- **Deployment impact:** high
- **Conformance status:** Open

### BCSS-R10 — Platform-wide evidence manifest standard is absent
- **Priority:** P2
- **Constitutional sections:** 19, 22, 23
- **Current verified state:** strong evidence manifest discipline exists in a domain-local subsystem only.
- **Gap:** no shared BCSS evidence packaging pattern exists.
- **Required future state:** reusable evidence packaging conventions where justified.
- **Exact repository evidence:** `backend/services/dr_evidence/manifest.py:268-382, 387-439`
- **Dependencies:** BCSS-R08
- **Bounded-track recommendation:** evidence packaging standards track
- **Measurable completion criteria:** shared evidence schema guidance approved
- **Required tests:** schema conformance tests where adopted
- **Required independent evidence:** architecture review
- **Deployment impact:** low-medium
- **Conformance status:** Open

### BCSS-R11 — KPI vocabulary is distributed
- **Priority:** P2
- **Constitutional sections:** 29, 39
- **Current verified state:** pill, trust score, verification verdict, and deploy decision use related but separate semantics.
- **Gap:** shared KPI glossary is not formalized.
- **Required future state:** BCSS KPI glossary adopted across surfaces.
- **Exact repository evidence:** `backend/routes/recovery_dashboard.py:521-631`; `backend/lib/trust_score.py:202-268`; `backend/backup_verification.py:428-467`; `backend/routes/admin_deployment_readiness.py:362-393`
- **Dependencies:** BCSS-R08
- **Bounded-track recommendation:** KPI glossary adoption track
- **Measurable completion criteria:** shared KPI definitions documented and referenced
- **Required tests:** copy/contract tests where exposed
- **Required independent evidence:** operator-surface audit
- **Deployment impact:** low
- **Conformance status:** Open

### BCSS-R12 — Evidence-class labels and bounded claim bases are not yet bound to operator and certification surfaces
- **Priority:** P1
- **Constitutional sections:** 19, 20, 28, 29
- **Current verified state:** evidence-bearing surfaces exist, but they do not yet expose one shared BCSS taxonomy in claim presentation.
- **Gap:** evidence inflation risk remains at the operator/certification presentation layer.
- **Required future state:** each BCSS-facing surface identifies evidence class or bounded claim basis.
- **Exact repository evidence:** `backend/routes/recovery_dashboard.py:571-631`; `backend/server.py:11952-12021`; `backend/backup_verification.py:315-467`
- **Dependencies:** BCSS-R01, BCSS-R03, BCSS-R08
- **Upstream dependencies:** BCSS-R01, BCSS-R03, BCSS-R08
- **Downstream dependents:** none mandatory; may inform BCSS-R09 and BCSS-R13 adoption quality
- **Explicitly In Scope:** binding evidence-class labels and bounded claim bases to operator and certification surfaces
- **Explicitly Out of Scope:** taxonomy creation, posture/trust role separation, certification-class adoption
- **Completion Boundary:** complete when BCSS-facing surfaces map displayed claims to approved evidence classes
- **Non-Duplication Statement:** this item governs **surface-level evidence binding only**; it does not create the taxonomy or certification classes themselves
- **Bounded-track recommendation:** operator evidence classification track
- **Measurable completion criteria:** each BCSS truth surface maps displayed claims to evidence classes
- **Required tests:** surface contract tests
- **Required independent evidence:** read-only UI/API evidence review
- **Deployment impact:** medium
- **Conformance status:** Open

### BCSS-R13 — Recovery certification classes are not yet implemented as a shared constitutional model
- **Priority:** P1
- **Constitutional sections:** 20, 23, 24, 39
- **Current verified state:** the repository distinguishes representative vs full recovery, but no explicit shared class ladder exists at runtime surfaces.
- **Gap:** recovery claims remain harder to compare and govern consistently.
- **Required future state:** explicit class model adopted in BCSS certification surfaces.
- **Exact repository evidence:** `backend/routes/recovery_dashboard.py:618-629`; `backend/server.py:11976-12020`
- **Dependencies:** BCSS-R01, BCSS-R03, BCSS-R08
- **Upstream dependencies:** BCSS-R01, BCSS-R03, BCSS-R08
- **Downstream dependents:** BCSS-R09
- **Explicitly In Scope:** adoption of the shared recovery-certification-class model
- **Explicitly Out of Scope:** full-platform restore exercise execution and future-module registration contract
- **Completion Boundary:** complete when recovery claims are rendered against approved classes 0–8 without unsupported inheritance
- **Non-Duplication Statement:** this item governs **class-model adoption only**; it does not itself prove full-platform restore or create module-registration workflows
- **Bounded-track recommendation:** recovery certification-class track
- **Measurable completion criteria:** recovery claims rendered against approved classes 0–8
- **Required tests:** class-boundary tests
- **Required independent evidence:** certification review
- **Deployment impact:** medium-high
- **Conformance status:** Open

### BCSS-R14 — RPO/RTO policy values are not constitutionally approved
- **Priority:** P1
- **Constitutional sections:** 21, 39
- **Current verified state:** code defaults exist for posture calculations.
- **Gap:** policy authority and approval are not established.
- **Required future state:** approved policy values or explicit pending-state declarations by criticality class.
- **Exact repository evidence:** `backend/routes/recovery_dashboard.py:322-324`
- **Dependencies:** none
- **Bounded-track recommendation:** RPO/RTO policy approval track
- **Measurable completion criteria:** policy values or approved pending states declared for required domains
- **Required tests:** policy rendering tests
- **Required independent evidence:** governance approval record
- **Deployment impact:** medium
- **Conformance status:** Open

### BCSS-R15 — Future-module survivability registration contract is not yet formalized
- **Priority:** P1
- **Constitutional sections:** 18, 30, 37
- **Current verified state:** canonical truth framework exists but no BCSS survivability registration contract is present.
- **Gap:** future modules can drift before registration.
- **Required future state:** survivability registration contract defined and adopted.
- **Exact repository evidence:** `backend/lib/canonical_truth.py:68-307, 326-345`
- **Dependencies:** BCSS-R01
- **Upstream dependencies:** BCSS-R01
- **Downstream dependents:** future module onboarding and conformance review
- **Explicitly In Scope:** creation of the future-module survivability registration contract
- **Explicitly Out of Scope:** current truth-subject registration, evidence taxonomy adoption, or certification-class adoption
- **Completion Boundary:** contract exists with required registration fields and approved governance usage
- **Non-Duplication Statement:** this item governs **future-module registration contract only**; it does not perform current BCSS truth registration
- **Bounded-track recommendation:** survivability registration design track
- **Measurable completion criteria:** registration schema/process approved
- **Required tests:** registry validation tests
- **Required independent evidence:** architecture review
- **Deployment impact:** medium
- **Conformance status:** Open

### BCSS-R16 — Constitutional Impact Analysis is not yet a verified release input
- **Priority:** P1
- **Constitutional sections:** 31, 32, 37
- **Current verified state:** deploy readiness and operations governance exist, but no explicit CIA requirement was verified in reviewed governance surfaces.
- **Gap:** material changes can proceed without a standard BCSS impact checklist.
- **Required future state:** CIA required for material changes.
- **Exact repository evidence:** `backend/routes/admin_deployment_readiness.py:72-393`; `backend/routes/operations_control.py:62-218`
- **Dependencies:** none
- **Bounded-track recommendation:** governance workflow track
- **Measurable completion criteria:** material change process references CIA and stores result
- **Required tests:** governance contract tests
- **Required independent evidence:** release-review audit
- **Deployment impact:** medium
- **Conformance status:** Open

### BCSS-R17 — Constitutional exception/ADR process is not yet verified in BCSS governance
- **Priority:** P2
- **Constitutional sections:** 33, 34, 39
- **Current verified state:** reviewed BCSS governance sources do not verify an explicit exception lifecycle for survivability deviations.
- **Gap:** duplicate architecture or temporary deviations can become undocumented.
- **Required future state:** version-controlled exception/ADR process adopted.
- **Exact repository evidence:** `backend/lib/canonical_truth.py:379-526`; `backend/routes/operations_control.py:62-218`
- **Dependencies:** none
- **Bounded-track recommendation:** BCSS exception governance track
- **Measurable completion criteria:** ADR template and approval path approved
- **Required tests:** process verification only
- **Required independent evidence:** architecture review
- **Deployment impact:** low
- **Conformance status:** Open

### BCSS-R18 — OCC trust-events deployment-readiness probe path is inconsistent with actual endpoint
- **Priority:** P1
- **Constitutional sections:** 10, 17, 28, 29
- **Current verified state:** OCC trust-events probes `/api/admin/deploy-readiness`, while deployment readiness is defined at `/api/admin/deployment-readiness`.
- **Gap:** trust aggregation can misrepresent certification posture.
- **Required future state:** aggregator endpoint target and canonical endpoint match exactly.
- **Exact repository evidence:** `backend/routes/occ_trust_events.py:171-176`; `backend/routes/admin_deployment_readiness.py:72-75`
- **Dependencies:** none
- **Bounded-track recommendation:** trust-feed endpoint alignment track
- **Measurable completion criteria:** OCC trust events successfully consume canonical deployment readiness source
- **Required tests:** trust-feed integration tests
- **Required independent evidence:** read-only endpoint verification
- **Deployment impact:** medium
- **Conformance status:** Open

### BCSS-R19 — Deployment-readiness regression-gate transparency is a stub
- **Priority:** P2
- **Constitutional sections:** 20, 31, 39
- **Current verified state:** response includes `regression_gate_count`, but helper currently returns `0`.
- **Gap:** certification transparency is incomplete.
- **Required future state:** bounded, truthful regression gate accounting or explicit removal if not supported.
- **Exact repository evidence:** `backend/routes/admin_deployment_readiness.py:398-403`
- **Dependencies:** none
- **Bounded-track recommendation:** certification transparency track
- **Measurable completion criteria:** reported regression count reflects approved source of truth
- **Required tests:** endpoint contract tests
- **Required independent evidence:** read-only deploy-gate review
- **Deployment impact:** low-medium
- **Conformance status:** Open

## 37. Future Module Obligations

A future module with persistent operational impact shall not be eligible for deployment until it has:
- declared canonical ownership
- completed survivability registration
- declared persistent data stores
- declared backup coverage
- declared restore procedure
- declared recovery dependencies
- declared RPO/RTO policy or approved pending state
- declared retention class
- declared Trust Spine participation
- declared audit evidence
- declared notification behavior
- declared access policy
- declared certification requirements
- passed Constitutional Impact Analysis
- passed applicable tests
- produced evidence
- passed independent verification
- passed Deployment Gate

Use:
- **NOT YET EXERCISED**
- **AMBER — POLICY VALUE REQUIRED**

where appropriate. Never manufacture a PASS.

## 38. Independent Verification Requirements

Independent review shall verify:
- no required chapter is absent
- no current-state claim lacks evidence
- no constitutional rule conflicts with another
- no duplicate canonical owner is authorized
- no future architecture duplicates verified canonical systems
- Preview and Production remain distinct
- representative and full-platform recovery remain distinct
- implementation status is not overstated
- remediation items remain traceable
- existing IDs are preserved
- Version 1.0 freeze criteria are measurable
- the constitution reflects the entire platform, not only backups

Recommended independent review activities:
1. truth-subject ownership review
2. evidence-class review
3. claim-boundary review
4. preview-vs-production review
5. representative-vs-full recovery review
6. remediation traceability review
7. ambiguity/conflict review
8. freeze-criteria audit

## 39. Success Criteria

### Constitution Complete

The constitution is complete when:
- every required chapter exists
- every current-state claim is repository-backed or explicitly marked insufficient
- BCSS truth subjects are defined
- evidence taxonomy is defined
- recovery certification classes are defined
- conformance and remediation are preserved
- freeze criteria are measurable
- independent review gate is explicit

### Platform Conformance Complete

Platform conformance is complete only when:
- every applicable subsystem is classified under the final five-level model
- every BCSS truth subject has exactly one declared canonical owner and completed formal registration where required
- every persistent operational data source participates or has an approved exception
- no undocumented duplicate survivability architecture remains
- backup, restore, trust, evidence, and certification roles are explicit
- recovery claims are evidence-backed
- Preview and Production claims are separated
- representative and full-platform recovery claims are separated
- every survivability-sensitive action is access-governed
- every BCSS failure produces durable evidence
- external continuity dependencies are inventoried
- recovery dependencies and order are documented
- RPO/RTO policies are approved where required
- recovery exercises are classified and current
- KPIs and trust scores are evidence-transparent
- Constitutional Impact Analysis is part of material change review
- independent certification has been completed where required
- Deployment Gate includes applicable BCSS conformance checks
- No Fake PASS exists
- operator surfaces accurately represent current reality

This document reaches **Constitution Complete**. It does **not** claim **Platform Conformance Complete**.

## 40. Version History

| Version | Status | Summary |
|---|---|---|
| Phase 0 Draft | Complete baseline | Established 11 deliverables, evidence-backed discovery, architecture, conformance matrix, and remediation register. |
| Version 1.0 Candidate | Completed and submitted for independent review | Added platform-wide purpose, scope, definitions, invariants, ownership model, evidence taxonomy, certification classes, BC/DR governance, conformance lifecycle, and freeze annexes. |
| Version 1.0 Freeze Amendment Candidate | Independent-review findings corrected; artifact repository-materialized; formal freeze verification pending | Resolved repository materialization gap, owner-role ambiguity, conformance overstatement, class non-linearity, evidence taxonomy unevenness, BC/DR truth boundaries, exception expiry, approval-authority pending-state, and remediation boundary/dependency issues. |
| Version 1.0 Adopted and Frozen | Owner-adopted constitutional baseline | Final independent verification passed, owner adoption recorded, Version 1.0 frozen as governing BCSS standard, implementation conformance still incomplete, recovery certification not yet proven. |

### Amendment Record

| Field | Value |
|---|---|
| Amendment date | 2026-07-24 |
| Reviewed SHA | `fbb7045b083fb509e9d448d6615d248c727c153c` |
| Amendment SHA / repository state | `d51b486fb428ca4beddd832226061267db0e605a` |
| Findings resolved | F-001 through F-011 resolved; F-012 accepted as observation |
| Sections changed | 2, 18, 19, 20, 24, 25, 27, 29, 32, 33, 35, 36, 39, Annexes |
| Remediation entries changed | BCSS-R01, R03, R08, R09, R12, R13, R15 |
| Architecture changed | NO |
| Implementation changed | NO |
| Deployment changed | NO |

## 41. Constitutional Conclusion

MASCI OPS already contains meaningful survivability capability. The repository proves the existence of authority, execution, evidence, intelligence, trust, and certification mechanisms. What it does not yet prove is fully converged, formally registered, platform-wide BCSS conformance.

This Version 1.0 Freeze Amendment Candidate preserves the established BCSS architecture, resolves the independent-review blockers and major constitutional defects, materially saves the constitution into the repository, and prepares the artifact for one final independent freeze verification.

The platform may now proceed to final read-only independent verification and then, if approved, to bounded remediation tracks that extend existing canonical systems rather than create new survivability architecture.

### Formal Adoption and Freeze Statement

BCSS Constitution v1.0 is hereby adopted as the governing Business Continuity and Survivability constitutional standard for MASCI OPS. Version 1.0 is frozen as of `2026-07-24`. Existing and future platform systems are subject to its requirements. Platform conformance and recovery certification must be established through separately verified implementation and exercise evidence.

---

## Annex A — Amendment Summary (Version 1.0 Candidate → Version 1.0 Freeze Amendment Candidate)

Added or corrected:
- repository materialization and Document Control block
- exact repository path and reviewed SHA recording
- truth-subject owner-role precision with distinct fields for role, current binding, and formal registration status
- five-level conformance classification model
- clarified recovery class structure and explicit 6/7 non-linearity rule
- hardened evidence taxonomy fields and anti-overclaim rules
- explicit deployment-certification vs recovery-certification non-equivalence
- strengthened BC/DR truth-boundary language using Verified Current State / Constitutional Requirement / Current Evidence Limitation structure
- explicit temporary exception expiry to non-conforming state
- approval-authority pending-state rule
- removal of BCSS-R09 / BCSS-R13 dependency cycle
- sharper remediation boundaries for BCSS-R01 / R03 / R08 / R12 / R13 / R15

No application behavior, runtime logic, deployment, or production activation changed.

## Annex B — Coverage Checklist

| Required Area | Present |
|---|---|
| 1. Title Page | Yes |
| 2. Version and Status | Yes |
| 3. Constitutional Authority | Yes |
| 4. Purpose | Yes |
| 5. Scope | Yes |
| 6. Interpretation Rules | Yes |
| 7. Definitions | Yes |
| 8. Governing Principles | Yes |
| 9. Constitutional Invariants | Yes |
| 10. Authority and Precedence | Yes |
| 11. Verified Current State | Yes |
| 12. Repository Discovery | Yes |
| 13. Duplicate Architecture Audit | Yes |
| 14. Survivability Coverage Matrix | Yes |
| 15. Integration Matrix | Yes |
| 16. Recovery Dependency Graph | Yes |
| 17. Constitutional Architecture | Yes |
| 18. BCSS Truth Subjects | Yes |
| 19. Evidence Taxonomy | Yes |
| 20. Recovery Certification Classes | Yes |
| 21. RPO/RTO and Criticality Governance | Yes |
| 22. Backup Governance | Yes |
| 23. Recovery Governance | Yes |
| 24. Disaster Recovery Governance | Yes |
| 25. Business Continuity Governance | Yes |
| 26. Capacity and Retention Governance | Yes |
| 27. Access Governance | Yes |
| 28. Operator Experience and Truth Surfaces | Yes |
| 29. KPI and Trust Governance | Yes |
| 30. Automatic Survivability Registration | Yes |
| 31. Constitutional Impact Analysis | Yes |
| 32. Conformance Lifecycle | Yes |
| 33. Exceptions and ADRs | Yes |
| 34. Constitutional Change Control | Yes |
| 35. Platform Conformance Matrix | Yes |
| 36. Remediation Register | Yes |
| 37. Future Module Obligations | Yes |
| 38. Independent Verification Requirements | Yes |
| 39. Success Criteria | Yes |
| 40. Version History | Yes |
| 41. Constitutional Conclusion | Yes |
| Amendment summary | Yes |
| Coverage checklist | Yes |
| Conflict/ambiguity report | Yes |
| Evidence-sufficiency report | Yes |
| Freeze checklist | Yes |
| Independent-review checklist | Yes |
| First bounded-track recommendation | Yes |

## Annex C — Conflict / Ambiguity Report

### C1 — Operations Control authorization declaration mismatch
- **Verified current state:** file header says endpoints require super-admin authentication; implementation uses `require_admin`.
- **Evidence:** `backend/routes/operations_control.py:1-5, 62-120`
- **Disposition:** preserved as remediation item BCSS-R06.

### C2 — OCC trust-events deployment-readiness path mismatch
- **Verified current state:** OCC trust-events probes `/api/admin/deploy-readiness`; canonical endpoint is `/api/admin/deployment-readiness`.
- **Evidence:** `backend/routes/occ_trust_events.py:171-176`; `backend/routes/admin_deployment_readiness.py:72-75`
- **Disposition:** preserved as remediation item BCSS-R18.

### C3 — Backup freshness precedence split
- **Verified current state:** multiple surfaces derive recency using overlapping but different logic.
- **Evidence:** `backend/server.py:1561-1605`; `backend/routes/recovery_dashboard.py:328-379`
- **Disposition:** preserved as remediation item BCSS-R02.

### C4 — Policy defaults vs approved policy
- **Verified current state:** RPO/RTO defaults exist in code.
- **Evidence:** `backend/routes/recovery_dashboard.py:322-324`
- **Disposition:** preserved as remediation item BCSS-R14.

## Annex D — Repository-Evidence Sufficiency Report

| Area | Sufficiency | Notes |
|---|---|---|
| Runtime authority | Strong | Direct code evidence |
| Backup execution | Strong | Durable job/scheduler evidence present |
| Recovery posture | Strong | Recovery snapshot and trust score clearly implemented |
| Restore safety | Strong | Admin-strict restore and lineage guard clearly implemented |
| Notification continuity | Strong | Explicit environment contract and tests |
| Deployment certification | Strong | Readiness and immutable ledger clearly implemented |
| Canonical truth framework | Strong | Role taxonomy and validation present |
| BCSS formal registration | Limited | Framework exists, BCSS entries absent |
| Business continuity governance | Moderate | Partial continuity-aware behavior present; broad governance still constitutional/future |
| Disaster recovery governance | Limited | Application-level recovery is evidenced; full DR program is not fully evidenced |
| RPO/RTO policy authority | Limited | Defaults exist, approval evidence absent |
| Exception/ADR governance | Limited | No explicit BCSS exception workflow verified in reviewed governance files |
| CIA requirement | Limited | No explicit CIA artifact verified in reviewed governance files |

### Conclusion

Repository evidence is sufficient to support this constitution without overstating implementation, provided that limited-evidence areas remain marked as constitutional requirements rather than claimed implemented capability.

## Annex E — Freeze Checklist (Reset)

| Freeze Item | Result |
|---|---|
| Constitution artifact exists in repository | PASS |
| Exact repository path recorded | PASS |
| Exact reviewed SHA recorded | PASS |
| Exact amended SHA recorded or worktree state declared | PASS |
| Required sections present | PASS |
| All material current-state claims repository-backed or explicitly bounded | PASS |
| Truth-subject owner roles unambiguous | PASS |
| Conformance classifications use final five-level model | PASS |
| Recovery classes clarified | PASS |
| Evidence taxonomy hardened | PASS |
| Deployment vs recovery certification separated | PASS |
| BC/DR limitations explicit | PASS |
| Exception expiry rule explicit | PASS |
| R09/R13 dependency cycle removed | PASS |
| Coupled remediation boundaries explicit | PASS |
| No unresolved BLOCKER findings | PASS |
| No unresolved MAJOR findings | PASS |
| No unsupported Production claim | PASS |
| No duplicate architecture authorized | PASS |
| Independent freeze verification still pending | PASS |
| Owner adoption still pending | PASS |

## Annex F — Independent-Review Checklist

Independent reviewer should verify:
- every required section exists
- every verified current-state claim has exact repository evidence
- no constitutional rule contradicts another
- no duplicate canonical owner is implicitly authorized
- no BCSS-derived surface is mislabeled as canonical truth
- preview and production claims remain distinct
- representative and full-platform recovery remain distinct
- business continuity and disaster recovery sections do not overclaim implementation
- remediation IDs BCSS-R01 through BCSS-R19 are preserved and traceable
- BCSS-R09 and BCSS-R13 no longer form a cycle
- freeze criteria are measurable
- the constitution remains extension-based rather than duplicate-architecture based

## Annex G — First Bounded-Track Recommendation After Final Freeze

**Recommended first bounded remediation track after final constitutional freeze:**  
**BCSS Canonical Ownership and Registration Track**

### Why first

It resolves the highest-leverage governance gap without introducing runtime architecture:
- BCSS-R01
- BCSS-R03
- BCSS-R08 (foundation only)
- BCSS-R12 (enables later binding)
- BCSS-R13 (foundation only)
- BCSS-R15 (future-module preparation)

### Bounded objective

- register the ten BCSS truth subjects
- declare one owner role per subject
- separate posture from trust formally
- adopt shared BCSS evidence taxonomy as governance standard
- define future-module survivability registration contract

### Not included

- no new dashboard
- no new scheduler
- no backup/restore runtime redesign
- no production activation
- no deployment
