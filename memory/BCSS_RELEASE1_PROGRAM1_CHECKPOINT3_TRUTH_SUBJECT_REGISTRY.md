# BCSS Release 1 · Program 1 · Checkpoint 3
## Truth Subject Registry Reference

This document derives its authority from BCSS_RELEASE1_PROGRAM1_CHECKPOINT3_MASTER_FOUNDATION.md and does not establish independent constitutional requirements.

Date: 2026-07-25

---

## 1. Purpose

### [Repository-backed current state (descriptive)] Purpose
This artifact restates the already adopted BCSS truth subjects and maps them to their current repository-backed evidence and claim-binding implications for Checkpoint 3.

---

## 2. Registered BCSS Truth Subjects

### [Repository-backed current state (descriptive)] Registry reference table

| Truth subject | Current repository-backed owner surface | Current classification | Primary evidence inputs | Claim-binding implication | Status type |
|---|---|---|---|---|---|
| `bcss_runtime_state_authority` | `/api/admin/platform/status` + `backend/lib/database_authority.py` | canonical | runtime identity, DB authority, environment identity | establishes whether stronger downstream claims may be trusted in the current runtime | Repository-backed current state (descriptive) |
| `bcss_backup_slot_execution` | `/api/admin/scheduler-runs` + `backend/lib/scheduler_runs.py` | canonical | scheduler evidence | proves slot ownership and dedup, not archive integrity | Repository-backed current state (descriptive) |
| `bcss_backup_job_execution` | `/api/admin/backups-complete-r2-state` + `backend/lib/backup_runtime.py` | canonical | execution evidence | proves live job state, not archive recoverability | Repository-backed current state (descriptive) |
| `bcss_backup_archive_lineage` | `/api/admin/backup-verification/state` + `backend/lib/archive_lineage.py` | canonical | archive, lineage, integrity, completeness | strongest current BCSS evidence-language source | Repository-backed current state (descriptive) |
| `bcss_restore_execution` | `/api/exports/restore` + `backend/server.py` | canonical | restore execution evidence | supports bounded verified restore claims | Repository-backed current state (descriptive) |
| `bcss_restore_drill_evidence` | `/api/admin/recovery/snapshot` drill data | canonical | drill and representative drill evidence | supports exercised claims only within actual drill scope | Repository-backed current state (descriptive) |
| `bcss_recovery_posture` | `/api/admin/recovery/snapshot` | canonical aggregator | posture fan-in | summaries and warnings only; not certification authority | Repository-backed current state (descriptive) |
| `bcss_recovery_trust` | `/api/admin/backup-trust-score` + `backend/lib/trust_score.py` | canonical derived consumer | trust evidence | confidence-only meaning; no certification authority | Repository-backed current state (descriptive) |
| `bcss_recovery_certification` | `/api/admin/deployment-readiness` is current bounded adjacent evidence source | canonical owner registration exists; shared BCSS class runtime missing | certification and decision evidence | certification owner boundary exists, but BCSS recovery classes remain deferred | Repository-backed current state (descriptive) |
| `bcss_external_dependency_continuity` | `/api/admin/integrations/truth-status` + `backend/routes/integration_truth.py` | canonical aggregator | external dependency evidence | binds dependency posture into BCSS without a second dependency engine | Repository-backed current state (descriptive) |

### [Constitutional (normative)] Registry rule
Checkpoint 3 introduces **no additional BCSS truth subjects**. The constitutional task is binding evidence and claims to the already adopted truth-subject registry, not expanding the registry.

---

## 3. Truth-Subject Roles and Claim Ceilings

### [Constitutional (normative)] Role-to-claim rule

| Truth-subject role | Maximum direct claim the role may support on its own | Notes | Status type |
|---|---|---|---|
| Canonical owner | `Verified`, and `Certified` only if the truth subject is itself a certification owner with proper decision evidence | ownership alone does not create certification | Constitutional (normative) |
| Aggregator | `Observed` surface-level posture plus bounded embedded upstream verified statements | may not replace upstream owners | Constitutional (normative) |
| Derived consumer | confidence/trust statements only | may not become source truth or certification | Constitutional (normative) |

---

## 4. BCSS-Adjacent Repository Surfaces

### [Repository-backed current state (descriptive)] Adjacent surface inventory

| Surface | Current classification | Why it matters to BCSS | Constitutional direction |
|---|---|---|---|
| `platform_attestation` | canonical adjacent | runtime legitimacy and release identity truth | consume as upstream runtime truth, not new BCSS subject |
| `trust_spine` | canonical adjacent | workflow lifecycle evidence pattern and anti-fake-green behavior | consume as evidence source/pattern, not BCSS evidence taxonomy replacement |
| `integration_truth` | canonical adjacent | dependency continuity input | consume through `bcss_external_dependency_continuity` |
| `occ_health_aggregator` | canonical adjacent aggregator | operator posture summary | not a BCSS owner; may eventually consume BCSS-bound claims |
| `operations_trust_center` | canonical adjacent derived consumer | operations-wide trust narrative | not a BCSS certification surface |
| `admin_platform_trust` | canonical adjacent validator | proof of defensive trust validation patterns | useful precedent for bounded evidence review |
| `dr_evidence/manifest.py` | canonical domain-local | strong evidence packaging precedent | preserve as precedent for future `BCSS-R10` |
| `incident_engine/evidence.py` | canonical domain-local | typed evidence plus custody chain precedent | preserve as provenance precedent |

### [Constitutional (normative)] Adjacent-surface rule
BCSS adoption shall consume and bind adjacent canonical surfaces where appropriate. It shall not re-declare them as independent BCSS truth architectures unless a future constitutional amendment explicitly does so.

---

## 5. Missing or Deferred Areas

### [Repository-backed current state (descriptive)] Missing registry-adjacent capabilities

| Area | Current state | Classification | Constitutional direction | Status type |
|---|---|---|---|---|
| BCSS recovery class runtime model | not yet implemented | missing | future `BCSS-R13` work | Repository-backed current state (descriptive) |
| BCSS operator acknowledgement evidence | not found as BCSS capability | missing | define later only if constitutionally justified | Repository-backed current state (descriptive) |
| BCSS constitutional exception records | not found as BCSS runtime capability in scope | missing | define later only if constitutionally justified | Repository-backed current state (descriptive) |

---

## 6. Deferred Implementation Notes

### [Deferred implementation] Future uses of this registry reference
- surface-by-surface claim binding
- BCSS evidence-manifest standard planning
- recovery certification class adoption
- survivability-registration wave planning
