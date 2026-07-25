# BCSS Release 1 · Program 1 · Checkpoint 3
## Evidence Taxonomy

This document derives its authority from BCSS_RELEASE1_PROGRAM1_CHECKPOINT3_MASTER_FOUNDATION.md and does not establish independent constitutional requirements.

Date: 2026-07-25

---

## 1. Purpose

### [Repository-backed current state (descriptive)] Purpose
This artifact inventories the repository-backed evidence language relevant to BCSS and maps it into the constitutional four-layer taxonomy defined by the Master Foundation.

---

## 2. Layer 1 — Raw Evidence Inventory

### [Repository-backed current state (descriptive)] Inventory table

| Raw Evidence class | Current repository-backed implementation | Current classification | Constitutional direction | Status type |
|---|---|---|---|---|
| Execution evidence | `backup_runtime.py`, restore execution in `server.py`, job ledgers | canonical | retain as BCSS raw evidence class | Repository-backed current state (descriptive) |
| Scheduler evidence | `scheduler_runs.py`, scheduler snapshot logic | canonical | retain as BCSS raw evidence class | Repository-backed current state (descriptive) |
| Archive evidence | `backup_health`, R2 object listings, `archive_lineage.py` | canonical | retain as BCSS raw evidence class | Repository-backed current state (descriptive) |
| Integrity evidence | manifest reads and integrity workflows in `archive_lineage.py`, `backup_verification.py` | canonical but bounded | retain as BCSS raw evidence class | Repository-backed current state (descriptive) |
| Lineage evidence | `archive_lineage.py`, restore origin validation | canonical but partially bounded | retain as BCSS raw evidence class | Repository-backed current state (descriptive) |
| Restore evidence | restore endpoint audit and replay summaries | canonical | retain as BCSS raw evidence class | Repository-backed current state (descriptive) |
| Drill evidence | `drill_runs`, recovery snapshot drill summary | canonical but partial | retain as BCSS raw evidence class | Repository-backed current state (descriptive) |
| Representative drill evidence | namespace-scoped drill reporting in recovery snapshot | canonical but partial | retain as distinct BCSS raw evidence class | Repository-backed current state (descriptive) |
| Full-platform recovery evidence | no repository-backed full-platform exercise package found | missing | keep class defined; mark unimplemented | Repository-backed current state (descriptive) |
| Notification evidence | `email_routing_audit_v2`, delivery state, capture rows | canonical adjacent | retain as BCSS-adjacent raw evidence class | Repository-backed current state (descriptive) |
| Provider-acceptance evidence | provider-live acceptance rows and integration truth inputs | canonical adjacent | retain as distinct BCSS-adjacent raw evidence class | Repository-backed current state (descriptive) |
| Safe-capture evidence | preview capture state and audit rows | canonical adjacent | retain as preview-only evidence class | Repository-backed current state (descriptive) |
| Trust evidence | `trust_spine_events`, trust score penalty inputs | canonical adjacent | retain as trust evidence, not certification evidence | Repository-backed current state (descriptive) |
| Audit evidence | `admin_audit`, `audit_events`, legacy import audit, restore audit | canonical | retain as BCSS raw evidence class | Repository-backed current state (descriptive) |
| Certification evidence | deploy-readiness outcomes and review artifacts | canonical adjacent | retain as bounded certification evidence | Repository-backed current state (descriptive) |
| Deployment decision evidence | `deployment_decisions`, deployment-readiness route | canonical adjacent | retain as distinct decision evidence class | Repository-backed current state (descriptive) |
| External dependency evidence | integration truth, notification delivery contracts | canonical adjacent | retain as dependency evidence class | Repository-backed current state (descriptive) |
| Capacity evidence | bucket usage, disk preflight, retention checks | canonical adjacent | retain as capacity evidence class | Repository-backed current state (descriptive) |
| Failure evidence | failed jobs, failed trust-spine events, denial rows, red findings | canonical | retain as BCSS raw evidence class | Repository-backed current state (descriptive) |
| Operator acknowledgement evidence | no repository-backed BCSS acknowledgement model found | missing | keep class defined; do not invent runtime now | Repository-backed current state (descriptive) |
| Exception evidence | no repository-backed BCSS constitutional exception record found in this scope | missing | keep class defined; do not invent runtime now | Repository-backed current state (descriptive) |
| Preview evidence | multiple preview-only proof paths already exist | canonical | retain as explicit environment-scoped evidence class | Repository-backed current state (descriptive) |
| Production evidence | production-scoped evidence exists unevenly and is not uniformly current | canonical but partial | retain as explicit environment-scoped evidence class | Repository-backed current state (descriptive) |

### [Constitutional (normative)] Raw Evidence rule
The Layer 1 class answers only **what kind of evidence exists**. It does not answer whether the claim is observed, verified, or certified.

---

## 3. Layer 2 — Evidence Quality Vocabulary

### [Constitutional (normative)] Constitutional quality vocabulary

| Evidence Quality value | Constitutional meaning | Repository-backed example | Status type |
|---|---|---|---|
| `DIRECT_OBSERVED` | directly observed fact not yet strengthened by durability or validation | freshest object or row observation, human/operator observation text | Constitutional (normative) |
| `DURABLE_OBSERVED` | evidence durably stored in a ledger, object store, audit trail, or collection | `backup_health`, `scheduler_runs`, `deployment_decisions`, `admin_audit` | Constitutional (normative) |
| `DERIVED` | evidence produced by a deterministic aggregation or scoring process over upstream evidence | `recovery_dashboard.py`, `trust_score.py`, `integration_truth.py` | Constitutional (normative) |
| `ESTIMATED` | fallback or inferred evidence used because stronger evidence is absent | `archive_lineage.py` estimated/fallback timestamp paths | Constitutional (normative) |
| `VALIDATED` | evidence passed a structural, identity, contract, or integrity validation step | archive integrity checks, restore origin validation | Constitutional (normative) |
| `EXERCISED` | evidence comes from an action or drill that was actually executed in the stated scope | restore execution, representative drill evidence | Constitutional (normative) |
| `DECISION_RECORDED` | evidence is a bounded approval or certification decision recorded against explicit scope | deployment readiness decision, future BCSS recovery certification decision | Constitutional (normative) |

### [Repository-backed current state (descriptive)] Why this vocabulary is repository-first
This vocabulary was chosen because the repository already contains:
- observed diagnostics (`backup_verification.py`)
- durable ledgers and collections (`scheduler_runs.py`, `backup_runtime.py`, `backup_health`)
- derived surfaces (`recovery_dashboard.py`, `trust_score.py`, `integration_truth.py`)
- estimated fallback logic (`archive_lineage.py:197-203, 439-440`)
- validated checks (`archive_lineage.py:119-135`; restore origin validation)
- exercised outcomes (`recovery_dashboard.py:446-464`)
- recorded decisions (`admin_deployment_readiness.py`)

### [Constitutional (normative)] Quality separation rule
Evidence Quality shall not be represented to operators as a claim class.

Examples:
- `VALIDATED` evidence may support a `Verified` claim, but it is not the same thing as a `Verified` claim.
- `DECISION_RECORDED` evidence may support a `Certified` claim, but it is not the same thing as a `Certified` claim.

---

## 4. Layer 3 — Confidence Vocabulary

### [Constitutional (normative)] Constitutional confidence vocabulary

| Confidence value | Constitutional meaning | Repository-backed notes | Status type |
|---|---|---|---|
| `HIGH` | evidence package is strongly bound and low ambiguity remains for the stated scope | already used in archive lineage and equipment detection | Constitutional (normative) |
| `MEDIUM` | evidence package is materially useful but ambiguity or fallback remains | already used in archive lineage and equipment detection | Constitutional (normative) |
| `LOW` | evidence package is weak, partial, or diagnostic-only | already used in archive lineage and equipment detection | Constitutional (normative) |
| `UNKNOWN` | confidence cannot yet be honestly classified | needed because some current surfaces use status without confidence | Constitutional (normative) |

### [Repository-backed current state (descriptive)] Current confidence fragmentation

| Repository area | Current confidence expression | Current classification | Constitutional direction |
|---|---|---|---|
| `archive_lineage.py` | `HIGH` / `MEDIUM` / `LOW` lineage confidence | canonical BCSS-aligned | preserve and map directly |
| `equipment_detection.py` | `HIGH` / `MEDIUM` / `LOW` confidence bands | domain-local | reuse vocabulary shape, not domain semantics |
| `legacy_imports.py` | numeric `confidence` and `field_confidences` | domain-local | allow internal numeric values; normalize later at BCSS surfaces |
| `dr_evidence/manifest.py` | numeric photo and attachment confidence | domain-local | allow internal numeric values; normalize later at BCSS surfaces |

### [Constitutional (normative)] Confidence compatibility rule
Until migration waves converge subsystem-local confidence models, the BCSS-facing operator layer shall normalize confidence to the four-value constitutional vocabulary without forcing immediate runtime rewrites in domain-local internals.

---

## 5. Layer 4 — Truth Subject Binding Reference

### [Repository-backed current state (descriptive)] Current BCSS truth-subject basis
Layer 4 binds evidence to the 10 truth subjects registered in Checkpoint 1 and preserved through Checkpoint 2:
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

### [Constitutional (normative)] Layer 4 rule
Truth Subject binding answers **what truth boundary the evidence establishes or constrains**. It is the bridge between evidence language and operator claim language.

---

## 6. Vocabulary Convergence Inventory

### [Repository-backed current state (descriptive)] Existing vocabulary inventory

| Vocabulary family | Current repo-backed values | Current classification | Constitutional treatment | Status type |
|---|---|---|---|---|
| runtime status vocabulary | `VERIFIED`, `DEGRADED`, `MISMATCH`, `UNVERIFIABLE`, `NOT_APPLICABLE` | canonical adjacent | preserve for status only | Repository-backed current state (descriptive) |
| trust bands | `green`, `amber`, `red`, `amber-no-activity` | canonical adjacent | preserve for trust/KPI only | Repository-backed current state (descriptive) |
| integration posture vocabulary | `LIVE_VERIFIED`, `CONFIGURED`, `PARTIAL`, `UNREACHABLE`, etc. | canonical adjacent | preserve for dependency posture only | Repository-backed current state (descriptive) |
| archive-lineage time-source vocabulary | `VERIFIED_LOGICAL_RECOVERY_POINT`, `COMPLETED_ARCHIVE_TIME`, `PROVIDER_DURABLE_COMPLETION_TIME`, `ESTIMATED_RECOVERY_POINT` | canonical | map into Layer 2 quality semantics | Repository-backed current state (descriptive) |
| domain-local verified workflows | `Verified`, `Closed - Verified`, etc. in non-BCSS modules | domain-local | do not auto-treat as BCSS Verified claims | Repository-backed current state (descriptive) |

### [Constitutional (normative)] Vocabulary collision rule
Word reuse alone does not create constitutional equivalence. A domain-local `Verified` workflow status is not automatically a BCSS `Verified` claim.

---

## 7. Deferred Implementation Notes

### [Deferred implementation] Future runtime adoption areas
- add explicit evidence-quality labels to BCSS-facing route payloads where justified
- add confidence normalization on operator surfaces
- add BCSS-facing evidence manifests where constitutionally justified
- add BCSS claim-basis disclosure to AI- and operator-facing surfaces

### [Deferred implementation] Explicitly not done in this checkpoint
- no API response changes
- no new collections
- no migrations
- no UI rewrites
