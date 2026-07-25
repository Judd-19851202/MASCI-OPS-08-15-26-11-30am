# BCSS Release 1 · Program 1 · Checkpoint 3
## Master Foundation — Canonical Evidence Taxonomy and Operator Claim Binding

Date: 2026-07-25  
Checkpoint scope: Release 1 → Program 2 → Foundation → Checkpoint 3 only  
Primary remediation items:
- `BCSS-R08` — Recovery evidence classes are not standardized as a governance standard
- `BCSS-R12` — Evidence-class labels and bounded claim bases are not yet bound to operator and certification surfaces

Governing artifacts:
- `/app/memory/BCSS_CONSTITUTION_v1.0.md`
- `/app/memory/BCSS_MASTER_IMPLEMENTATION_PROGRAM_v1.0.md`
- `/app/memory/BCSS_RELEASE1_PROGRAM1_CHECKPOINT1_CANONICAL_OWNERSHIP_AND_REGISTRATION.md`
- `/app/memory/BCSS_RELEASE1_PROGRAM1_CHECKPOINT2_ARCHIVE_LINEAGE_AND_FRESHNESS_PRECEDENCE_CONVERGENCE.md`

---

## 1. Constitutional Authority

### [Constitutional (normative)] Authority rule
This document is the **only constitutional authority** produced for Checkpoint 3.

All supporting Checkpoint 3 artifacts are subordinate reference materials. They may clarify, inventory, map, or sequence adoption work, but they may not create independent constitutional authority.

### [Constitutional (normative)] Scope boundary
Checkpoint 3 is **design and documentation only** unless repository evidence proves a minimal canonical schema or registry is strictly required to state the architecture truthfully.

### [Repository-backed current state (descriptive)] Scope outcome executed in this checkpoint
No runtime behavior, migration, API behavior, UI behavior, collection shape, or consumer contract was changed as part of this checkpoint artifact set.

### [Constitutional (normative)] Non-duplication rule
Checkpoint 3 shall not create:
- a second BCSS truth registry
- a second evidence engine
- a second certification engine
- a second operator truth model
- a parallel archive-lineage architecture
- a parallel dependency-continuity architecture

The constitutional direction must extend or bind to the already adopted BCSS and MASCI OPS canonical architecture.

---

## 2. Executive Conclusion

### [Repository-backed current state (descriptive)] Verified starting condition
The repository already contains:
- formal BCSS truth-subject registration in `backend/lib/canonical_truth.py`
- one canonical BCSS archive-lineage resolver in `backend/lib/archive_lineage.py`
- multiple operator-facing and administrative surfaces that already expose evidence-bearing statements
- multiple domain-local evidence, trust, health, and status vocabularies that remain useful but fragmented

Exact repository evidence includes:
- `backend/lib/canonical_truth.py:307-612`
- `backend/lib/archive_lineage.py:1-637`
- `backend/routes/recovery_dashboard.py:328-625`
- `backend/backup_verification.py:593-729`
- `backend/server.py:11952-12021`
- `backend/routes/admin_deployment_readiness.py:1-403`
- `backend/routes/integration_truth.py:1-811`
- `backend/lib/canonical_status.py:1-225`
- `backend/lib/trust_spine.py:1-285`

### [Repository-backed current state (descriptive)] Core architectural finding
MASCI OPS does **not** lack evidence. It lacks one platform-wide constitutional language that consistently answers, for any BCSS-facing claim:
1. what evidence exists
2. which BCSS truth subject owns the truth boundary
3. what evidence quality the evidence has
4. what confidence the evidence has
5. what truth the evidence can establish
6. what operator claim is permitted
7. what operator claim is prohibited

### [Constitutional (normative)] Checkpoint 3 result
Checkpoint 3 establishes that constitutional language as one four-layer Evidence Taxonomy plus one Operator Claim Binding standard, without introducing runtime drift.

---

## 3. Repository Discovery Summary

### [Repository-backed current state (descriptive)] Canonical BCSS-adjacent sources reviewed

| Repository area | Current role in repository | Current classification | Checkpoint 3 constitutional reading |
|---|---|---|---|
| `backend/lib/canonical_truth.py` | registered truth surfaces including the 10 BCSS truth subjects | canonical | authoritative source for BCSS truth-subject ownership |
| `backend/lib/archive_lineage.py` | canonical archive-lineage and freshness resolver | canonical | strongest current BCSS evidence-language implementation |
| `backend/routes/recovery_dashboard.py` | recovery posture fan-in snapshot | canonical aggregator | BCSS-facing operator surface requiring claim binding |
| `backend/server.py` backup trust endpoint | derived confidence scoring | canonical derived consumer | trust/confidence surface, not certification authority |
| `backend/backup_verification.py` | archive verification report and operator claim-boundary text | canonical BCSS-adjacent | strong current descriptive proof boundary |
| `backend/routes/admin_deployment_readiness.py` | bounded deployment certification decision | canonical but non-BCSS-specific | decision evidence useful to BCSS, but not recovery certification |
| `backend/routes/integration_truth.py` | dependency config/connectivity/activity truth | canonical adjacent | usable as dependency continuity input |
| `backend/lib/canonical_status.py` | shared runtime truth status vocabulary | canonical adjacent | status vocabulary only, not a BCSS evidence taxonomy |
| `backend/lib/trust_spine.py` | lifecycle event evidence spine | canonical adjacent | event evidence pattern, not complete BCSS claim model |
| `backend/services/dr_evidence/manifest.py` | domain-local evidence manifest packaging | canonical within Daily Report domain | repository proof that disciplined evidence packaging already exists |
| `backend/incident_engine/evidence.py` | typed evidence with custody chain | canonical within incident domain | repository proof that durable typed evidence and withdrawal semantics already exist |

### [Repository-backed current state (descriptive)] Fragmentation sources reviewed

| Repository area | Current role | Current classification | Drift risk |
|---|---|---|---|
| `backend/lib/canonical_status.py` | runtime truth statuses (`VERIFIED`, `DEGRADED`, etc.) | canonical for status only | can be mistaken for evidence class vocabulary |
| `backend/lib/trust_spine.py` | workflow bands (`green`, `amber`, `red`) | canonical for trust-spine lifecycle only | can be mistaken for truth/certification semantics |
| `backend/routes/integration_truth.py` | config/connectivity/operational states (`LIVE_VERIFIED`, `CONFIGURED`, etc.) | canonical for integration truth only | can be mistaken for claim class semantics |
| `backend/routes/equipment_detection.py` | confidence bands (`HIGH`, `MEDIUM`, `LOW`) | domain-local | confidence semantics not yet platform-wide |
| `backend/legacy_imports.py` | numeric OCR and field confidence | domain-local | incompatible with operator-facing categorical BCSS language |
| `backend/routes/operational_locations.py` and related flows | domain-local `Verified` workflow statuses | domain-local | word collision with BCSS Verified claims |

### [Constitutional (normative)] Repository-first rule
For Checkpoint 3 and all future BCSS adoption work:
- an existing repository concept shall be reused where equivalent
- a repository concept shall be classified explicitly as `canonical`, `legacy`, `duplicate`, or `missing`
- constitutional language shall clarify and bind existing concepts before any new concept is introduced

---

## 4. Constitutional Evidence Architecture

### [Constitutional (normative)] One evidence architecture rule
BCSS evidence language shall be expressed through **four layers only**:
1. Layer 1 — Raw Evidence
2. Layer 2 — Evidence Quality
3. Layer 3 — Confidence
4. Layer 4 — Truth Subject

No BCSS-facing claim shall skip a layer when the layer is applicable.

### [Constitutional (normative)] Separation rule
The following are constitutionally distinct and shall not be collapsed into each other:
- evidence class
- evidence quality
- confidence
- truth subject
- status
- trust score
- verification verdict
- certification decision
- deployment decision

### [Repository-backed current state (descriptive)] Why this separation is required
The repository already uses overlapping but non-identical languages for:
- status (`backend/lib/canonical_status.py`)
- trust bands (`backend/lib/trust_spine.py`, `backend/lib/trust_score.py`)
- archive-lineage quality and confidence (`backend/lib/archive_lineage.py`)
- operator-verification claim boundaries (`backend/backup_verification.py`)
- deployment decisions (`backend/routes/admin_deployment_readiness.py`)

Without a constitutional layering model, these existing languages can be over-read as stronger or broader claims than the evidence supports.

### [Constitutional (normative)] Canonical four-layer model

| Layer | Constitutional purpose | Required answer | Status type |
|---|---|---|---|
| Layer 1 — Raw Evidence | classify what kind of evidence is present | “What evidence exists?” | Constitutional (normative) |
| Layer 2 — Evidence Quality | classify how that evidence was obtained or strengthened | “What quality does this evidence have?” | Constitutional (normative) |
| Layer 3 — Confidence | classify the confidence in the evidence package or evidence interpretation | “How confident are we?” | Constitutional (normative) |
| Layer 4 — Truth Subject | bind the evidence to the exact BCSS truth boundary and owner | “What truth subject does this evidence establish or constrain?” | Constitutional (normative) |

### [Constitutional (normative)] Claim-binding consequence rule
An operator claim may be made only after the applicable evidence has been bound through all relevant layers and then compared against the claim-class ceiling rules in Section 6 of this document.

---

## 5. Constitutional Evidence Taxonomy Summary

### [Constitutional (normative)] Layer 1 summary
BCSS Raw Evidence classes are constitutionally defined in the supporting taxonomy artifact and derive from Constitution Section 19. They include, at minimum:
- Execution evidence
- Scheduler evidence
- Archive evidence
- Integrity evidence
- Lineage evidence
- Restore evidence
- Drill evidence
- Representative drill evidence
- Full-platform recovery evidence
- Notification evidence
- Provider-acceptance evidence
- Safe-capture evidence
- Trust evidence
- Audit evidence
- Certification evidence
- Deployment decision evidence
- External dependency evidence
- Capacity evidence
- Failure evidence
- Operator acknowledgement evidence
- Exception evidence
- Preview evidence
- Production evidence

### [Constitutional (normative)] Layer 2 summary
BCSS Evidence Quality shall use one constitutional vocabulary for BCSS claim binding:
- `DIRECT_OBSERVED`
- `DURABLE_OBSERVED`
- `DERIVED`
- `ESTIMATED`
- `VALIDATED`
- `EXERCISED`
- `DECISION_RECORDED`

### [Constitutional (normative)] Layer 2 interpretation rule
Evidence Quality describes **how evidence stands**, not **what claim class the operator may state**.

`Verified` and `Certified` are claim-class words, not evidence-quality words.

### [Repository-backed current state (descriptive)] Repository evidence informing Layer 2
The repository already contains examples of these quality shapes:
- observed object presence and secondary diagnostics in `backup_verification.py:619-629, 698-729`
- durable ledgers in `scheduler_runs.py`, `backup_runtime.py`, and `backup_health`
- derived scoring and aggregations in `trust_score.py`, `recovery_dashboard.py`, and `integration_truth.py`
- estimated/fallback timestamp handling in `archive_lineage.py:179-203, 439-440`
- validated archive integrity/origin checks in `archive_lineage.py:119-135` and `server.py` restore origin validation
- exercised drill and restore evidence in `recovery_dashboard.py:446-464`
- recorded decisions in `admin_deployment_readiness.py` and `deployment_decisions`

### [Constitutional (normative)] Layer 3 summary
BCSS Confidence shall use one constitutional operator vocabulary:
- `HIGH`
- `MEDIUM`
- `LOW`
- `UNKNOWN`

### [Repository-backed current state (descriptive)] Repository evidence informing Layer 3
The repository already uses:
- `HIGH` / `MEDIUM` / `LOW` in `archive_lineage.py:206-216` and `equipment_detection.py:13-18, 98-104`
- numeric confidence values in `legacy_imports.py:100-114, 218-225` and `services/dr_evidence/manifest.py:62, 78`

### [Constitutional (normative)] Layer 3 compatibility rule
Subsystem-local numeric confidence may continue to exist internally, but any BCSS-facing operator claim or BCSS-facing evidence display shall normalize to `HIGH`, `MEDIUM`, `LOW`, or `UNKNOWN` once migration waves adopt this foundation.

### [Constitutional (normative)] Layer 4 summary
Layer 4 truth binding shall use the already adopted 10 BCSS truth subjects from Checkpoint 1. Checkpoint 3 introduces no new BCSS truth subjects.

---

## 6. Constitutional Claim Classes and Binding Rules

### [Constitutional (normative)] Constitutional claim classes

| Claim class | Constitutional meaning | Minimum constitutional basis | Prohibited overclaim | Status type |
|---|---|---|---|---|
| `Observed` | a bounded statement that evidence was observed or recorded in the stated scope | applicable Raw Evidence class + applicable Truth Subject + scope/environment disclosure | shall not be stated as verified, exercised, or certified | Constitutional (normative) |
| `Verified` | a bounded statement that evidence was validated or exercised sufficiently to support the stated truth in the stated scope | applicable Raw Evidence class + `VALIDATED` or `EXERCISED` quality + applicable Truth Subject + freshness/scope/environment fit | shall not be stated as certified outside an approved certification owner decision | Constitutional (normative) |
| `Certified` | a bounded decision that a canonical certification owner has approved the claim in the stated scope | Certification evidence or decision-recorded evidence under the applicable certification owner and rules | shall not be expanded beyond the exact certified scope, freshness window, environment, or class | Constitutional (normative) |

### [Constitutional (normative)] Claim ceiling rule
Every BCSS-facing surface has a **claim ceiling**: the strongest claim class that surface may express from its current canonical evidence basis.

### [Constitutional (normative)] Claim basis rule
Every BCSS-facing surface shall eventually disclose, directly or by drill-through:
- truth subject
- raw evidence class or classes
- evidence quality
- confidence
- freshness and scope
- permitted claim class
- prohibited stronger claim class

### [Constitutional (normative)] Claim prohibition rules
1. A trust score is not certification evidence.
2. A deployment decision is not recovery certification.
3. Preview evidence is not production evidence.
4. A newest observed artifact is not automatically a verified recoverable point.
5. A queued or safe-captured notification is not provider-acceptance evidence.
6. A representative namespace restore is not a full-platform restore.
7. A verified archive or integrity result is not by itself a certified recovery claim.

### [Repository-backed current state (descriptive)] Existing repository proof of claim-boundary discipline
The repository already contains explicit examples of bounded claims:
- `backup_verification.py:698-729` states that the newest observed archive object is “Secondary Diagnostic Evidence Only”
- `backup_verification.py:727-729` states that archive verification does not prove restore certification or BCSS recovery-class certification
- `recovery_dashboard.py:605-615` distinguishes “NOT YET EXERCISED” full restore from preview-only evidence
- `canonical_truth.py:515-516, 546-547, 577-580` already distinguishes posture, trust, and registration-only certification ownership

---

## 7. BCSS Truth-Subject Binding Model

### [Constitutional (normative)] Truth-subject binding rule
No BCSS claim shall be made without first binding the claim to exactly one BCSS truth subject owner boundary, even if multiple upstream evidence inputs contribute to the result.

### [Repository-backed current state (descriptive)] Current BCSS truth-subject registry state
Checkpoint 1 already registered the following 10 truth subjects:
- `bcss_runtime_state_authority`
- `bcss_backup_slot_execution`
- `bcss_backup_job_execution`
- `bcss_backup_archive_lineage`
- `bcss_restore_execution`
- `bcss_restore_drill_evidence`
- `bcss_recovery_posture`
- `bcss_recovery_trust`
- `bcss_recovery_certification`
- `bcss_external_dependency_continuity`

Repository evidence:
- `backend/lib/canonical_truth.py:307-612`

### [Constitutional (normative)] Operator binding implication by truth-subject role

| Truth-subject role | What the surface may do | What the surface may not do | Status type |
|---|---|---|---|
| Canonical owner | state source truth within its registered scope | inherit certification authority it does not own | Constitutional (normative) |
| Aggregator | summarize upstream truths and warnings | replace or override upstream canonical ownership | Constitutional (normative) |
| Derived consumer | express confidence, score, or derived posture | become certification or ownership authority | Constitutional (normative) |
| Validator | test or grade evidence against rules | become source truth | Constitutional (normative) |

---

## 8. Current BCSS-Facing Surface Claim Ceilings

### [Repository-backed current state (descriptive)] Current surface inventory and constitutional direction

| Surface | Current repository-backed basis | Current classification | Current strongest defensible claim | Prohibited stronger claim | Constitutional direction |
|---|---|---|---|---|---|
| `archive_lineage` payload | archive, lineage, integrity, completeness, confidence in `backend/lib/archive_lineage.py` | canonical | `Observed` or `Verified`, depending candidate quality and validity | `Certified` | bind explicit claim class to archive-lineage outputs in future wave |
| backup verification report | archive-lineage + verification report text in `backend/backup_verification.py` | canonical BCSS-adjacent | `Observed` and bounded `Verified` archive/integrity claims | recovery certification | preserve existing claim-boundary language and formalize taxonomy labels later |
| recovery snapshot | posture fan-in in `backend/routes/recovery_dashboard.py` | canonical aggregator | `Observed` posture plus bounded `Verified` subclaims where evidence already supports them | full-platform or certified recovery if not proven | bind each displayed claim to taxonomy and claim class later |
| backup trust score | `compute_backup_trust_score()` | canonical derived consumer | derived confidence statement only | `Verified` archive truth or `Certified` recovery | label as confidence-only surface |
| deployment readiness | bounded deploy-decision evidence | canonical adjacent certification surface | bounded deployment `Certified` claim only | BCSS recovery certification | preserve distinction; map as decision evidence only |
| integration truth / dependency continuity | config/connectivity/activity model | canonical adjacent | `Observed` or bounded `Verified` dependency posture | continuity certification | future binding through BCSS external dependency continuity truth |

### [Constitutional (normative)] Required future surface rule
Future BCSS-facing operator surfaces shall not introduce a fourth claim class such as “live verified,” “green means certified,” or “ready means proven” unless that wording maps exactly to the constitutional claim-class model and owning truth subject.

---

## 9. Constitutional Schema for Future BCSS Claim Disclosure

### [Constitutional (normative)] Conceptual disclosure schema

| Field | Meaning | Status type |
|---|---|---|
| `truth_subject` | exact BCSS truth subject being claimed | Constitutional (normative) |
| `owner_surface` | canonical owner or derived/aggregator surface producing the statement | Constitutional (normative) |
| `raw_evidence_classes` | applicable Layer 1 evidence classes | Constitutional (normative) |
| `evidence_quality` | applicable Layer 2 quality value | Constitutional (normative) |
| `confidence` | applicable Layer 3 confidence value | Constitutional (normative) |
| `environment_scope` | preview or production scope | Constitutional (normative) |
| `operational_scope` | archive / representative namespace / subsystem / full platform / dependency subset / etc. | Constitutional (normative) |
| `freshness_basis` | how freshness was judged, if applicable | Constitutional (normative) |
| `claim_class` | Observed / Verified / Certified | Constitutional (normative) |
| `claim_text` | exact bounded operator statement | Constitutional (normative) |
| `prohibited_claims` | stronger claims disallowed from this evidence basis | Constitutional (normative) |

### [Deferred implementation] Adoption note
This schema is architectural guidance only in Checkpoint 3. No route, response model, or UI component is changed in this checkpoint.

---

## 10. Repository-First Convergence Decisions

### [Repository-backed current state (descriptive)] Current constitutional reuse decisions

| Topic | Current repository-backed equivalent | Classification | Constitutional direction | Status type |
|---|---|---|---|---|
| BCSS truth-subject ownership | `backend/lib/canonical_truth.py` | canonical | reuse exactly | Repository-backed current state (descriptive) |
| BCSS archive lineage and freshness | `backend/lib/archive_lineage.py` | canonical | reuse exactly | Repository-backed current state (descriptive) |
| runtime status vocabulary | `backend/lib/canonical_status.py` | canonical but adjacent | do not replace; map status separately from evidence language | Constitutional (normative) |
| workflow lifecycle evidence | `backend/lib/trust_spine.py` | canonical but adjacent | reuse as evidence source pattern, not as BCSS claim taxonomy | Constitutional (normative) |
| Daily Report evidence manifest | `backend/services/dr_evidence/manifest.py` | canonical domain-local | treat as packaging precedent for future BCSS-R10 work | Constitutional (normative) |
| Incident typed evidence and custody chain | `backend/incident_engine/evidence.py` | canonical domain-local | treat as provenance precedent, not as BCSS replacement | Constitutional (normative) |
| deployment certification | `backend/routes/admin_deployment_readiness.py` | canonical adjacent | retain as decision evidence distinct from BCSS recovery certification | Constitutional (normative) |

---

## 11. Checkpoint 3 Deliverables

### [Repository-backed current state (descriptive)] Artifacts produced in this checkpoint
- `/app/memory/BCSS_RELEASE1_PROGRAM1_CHECKPOINT3_MASTER_FOUNDATION.md`
- `/app/memory/BCSS_RELEASE1_PROGRAM1_CHECKPOINT3_EVIDENCE_TAXONOMY.md`
- `/app/memory/BCSS_RELEASE1_PROGRAM1_CHECKPOINT3_CLAIM_BINDING_STANDARD.md`
- `/app/memory/BCSS_RELEASE1_PROGRAM1_CHECKPOINT3_TRUTH_SUBJECT_REGISTRY.md`
- `/app/memory/BCSS_RELEASE1_PROGRAM1_CHECKPOINT3_PLATFORM_MIGRATION_PLAN.md`

### [Constitutional (normative)] Companion-document authority rule
Each supporting artifact shall explicitly state:

> “This document derives its authority from BCSS_RELEASE1_PROGRAM1_CHECKPOINT3_MASTER_FOUNDATION.md and does not establish independent constitutional requirements.”

---

## 12. Explicit Out-of-Scope Boundaries

### [Constitutional (normative)] Out-of-scope actions for Checkpoint 3
The following were and remain out of scope for this checkpoint:
- migrations
- collection rewrites
- consumer rewrites
- UI copy rewrites
- API response changes
- new runtime registries
- new evidence engines
- new certification classes at runtime
- subsystem-by-subsystem modernization

### [Deferred implementation] Future adoption work intentionally deferred
- wave-based evidence vocabulary convergence
- wave-based truth-subject registration adoption outside existing BCSS registrations where justified
- surface-level claim binding implementation
- AI-consumption normalization
- recovery certification convergence under `BCSS-R13`

---

## 13. Checkpoint Verdict

### [Repository-backed current state (descriptive)] Checkpoint 3 completion reading
Checkpoint 3 is successful when a future engineer can answer, for a BCSS-facing feature, without creating a second evidence or truth architecture:
- what evidence exists
- who canonically owns it
- what quality it has
- what confidence it has
- what truth it establishes
- what operator claims are permitted
- what operator claims are prohibited

### [Constitutional (normative)] Verdict statement
`GO — BCSS CHECKPOINT 3 MASTER FOUNDATION ADOPTED AS THE SOLE CONSTITUTIONAL ENTRY POINT FOR EVIDENCE TAXONOMY AND OPERATOR CLAIM BINDING DESIGN.`
