# BCSS Release 1 · Program 1 · Checkpoint 3
## Claim Binding Standard

This document derives its authority from BCSS_RELEASE1_PROGRAM1_CHECKPOINT3_MASTER_FOUNDATION.md and does not establish independent constitutional requirements.

Date: 2026-07-25

---

## 1. Purpose

### [Repository-backed current state (descriptive)] Purpose
This artifact converts the constitutional claim-class model into a repository-first standard for how BCSS-facing operator and certification surfaces shall bind claims to evidence.

---

## 2. Constitutional Claim Model

### [Constitutional (normative)] Claim model

| Component | Meaning | Status type |
|---|---|---|
| Claim basis | the exact evidence package currently supporting the surfaced statement | Constitutional (normative) |
| Claim class | the allowed operator word for the statement: `Observed`, `Verified`, or `Certified` | Constitutional (normative) |
| Claim ceiling | the strongest claim class the current basis can support | Constitutional (normative) |
| Prohibited claim | a stronger statement not allowed from the same basis | Constitutional (normative) |

### [Constitutional (normative)] Mandatory determination order
When a BCSS-facing claim is rendered, future adoption shall determine in this order:
1. truth subject
2. raw evidence classes
3. evidence quality
4. confidence
5. freshness and scope
6. claim ceiling
7. prohibited stronger claims

---

## 3. Claim Classes

### [Constitutional (normative)] Claim-class table

| Claim class | Allowed statement shape | Minimum basis | Typical BCSS examples | Prohibited overclaim |
|---|---|---|---|---|
| `Observed` | “Evidence was observed / recorded in this stated scope.” | applicable raw evidence + truth subject + scope/environment disclosure | newest observed archive object, dependency unreachable now, warning currently active | may not be stated as verified, exercised, or certified |
| `Verified` | “Evidence was validated or exercised sufficiently for this bounded truth.” | applicable raw evidence + `VALIDATED` or `EXERCISED` quality + truth subject + freshness fit | archive integrity verified, representative drill exercised, origin validation passed | may not be stated as certified outside a certification owner decision |
| `Certified` | “A canonical certification owner approved this bounded decision.” | certification/decision evidence + certification owner + explicit scope/class/environment | deployment readiness decision, future BCSS recovery certification class | may not be expanded beyond certified scope |

### [Repository-backed current state (descriptive)] Current repository examples

| Repository evidence | Current strongest defensible claim class | Why |
|---|---|---|
| `backup_verification.py` newest observed archive object section | `Observed` | secondary diagnostic evidence only |
| `archive_lineage.py` authoritative recoverable point with valid lineage/integrity/completeness | `Verified` | validated archive/lineage truth in bounded scope |
| `recovery_dashboard.py` representative namespace drill summary | `Verified` | exercised representative scope only |
| `admin_deployment_readiness.py` decision output | `Certified` for deployment readiness only | decision evidence exists, but only for deploy-readiness scope |
| `trust_score.py` backup trust score | no claim class beyond derived confidence statement | trust score is not certification evidence |

---

## 4. Surface Binding Matrix

### [Repository-backed current state (descriptive)] Current surface matrix

| Surface / route | Current basis | Current classification | Permitted claim class | Prohibited claim class | Constitutional direction |
|---|---|---|---|---|---|
| `backend/lib/archive_lineage.py` public payload | archive, integrity, completeness, confidence, environment match | canonical | `Observed` or `Verified` depending selected candidate | `Certified` | future payloads should expose claim basis explicitly |
| `GET /api/admin/recovery/snapshot` | posture fan-in over archive, drill, runtime, scheduler, capacity | canonical aggregator | mixed: posture as `Observed`; specific validated/exercised subclaims may be `Verified` | `Certified` unless a certification owner surface says so | future UI/API binding should label each displayed claim |
| backup verification email/report | archive verification and claim-boundary text | canonical BCSS-adjacent | `Observed` and bounded `Verified` archive claims | recovery certification | preserve and formalize existing honesty |
| `GET /api/admin/backup-trust-score` | derived trust score inputs | canonical derived consumer | no stronger than derived confidence statement | `Verified`, `Certified` | future label should state confidence-only |
| `GET /api/admin/deployment-readiness` | deploy gate decision evidence | canonical adjacent | `Certified` for deployment readiness scope only | BCSS recovery certification | future BCSS mapping must preserve this distinction |
| `GET /api/admin/integrations/truth-status` | dependency config/connectivity/activity evidence | canonical adjacent | `Observed` or bounded `Verified` dependency posture | continuity certification | future BCSS dependency continuity binding |

### [Constitutional (normative)] Surface honesty rule
If one surface contains multiple subclaims with different ceilings, the surface shall not flatten them into one stronger umbrella claim.

Example:
- recovery posture may contain an observed warning, a verified archive-integrity fact, and a representative exercised drill fact at the same time
- therefore the whole surface shall not be presented as “Certified recovery”

---

## 5. Operator Claim Grammar

### [Constitutional (normative)] Required grammar direction
Future BCSS-facing operator copy should be structurally expressible in the following form:

`<Claim Class>: <bounded statement> · basis=<raw evidence classes> · quality=<evidence quality> · confidence=<confidence> · scope=<scope> · environment=<environment>`

### [Deferred implementation] Example future renderings
- `Observed: Newest archive object seen in R2 · basis=Archive evidence · quality=DIRECT_OBSERVED · confidence=LOW · scope=archive presence only · environment=preview`
- `Verified: Archive integrity passed for the current authoritative recoverable point · basis=Archive evidence, Integrity evidence, Lineage evidence · quality=VALIDATED · confidence=HIGH · scope=archive integrity only · environment=preview`
- `Certified: Deployment readiness pass recorded for this release candidate · basis=Deployment decision evidence · quality=DECISION_RECORDED · confidence=HIGH · scope=deployment readiness only · environment=preview`

---

## 6. Prohibited Claim Matrix

### [Constitutional (normative)] Claim-prohibition matrix

| If the current basis is only... | Permitted claim | Prohibited stronger claim | Repository-backed reason |
|---|---|---|---|
| newest observed archive object | `Observed` archive presence statement | verified recoverable point or certified recovery | `backup_verification.py:698-729` |
| trust score penalties and scores | derived confidence statement | verified archive truth or certified recovery | `trust_score.py:202-268`; `canonical_truth.py:546-547` |
| deployment readiness decision | certified deployment readiness | recovery certification | `admin_deployment_readiness.py:1-31`; Constitution Sections 19 and 29 |
| preview safe-capture | preview capture occurred | provider acceptance or production delivery | `integration_truth.py`, delivery doctrine |
| representative drill evidence | representative restore exercised | subsystem/full-platform/DR/BC certification | Constitution Section 20; `recovery_dashboard.py:605-615` |
| domain-local workflow `Verified` status | domain-local workflow progression | BCSS verified claim without BCSS truth-subject binding | repository-wide status collision risk |

---

## 7. Claim Registry and Truth-Subject Binding Matrix

### [Repository-backed current state (descriptive)] BCSS truth-subject claim ceilings

| Truth subject | Current owner role | Typical current evidence basis | Current practical claim ceiling | Future note |
|---|---|---|---|---|
| `bcss_runtime_state_authority` | canonical owner | runtime identity + database authority | `Verified` | may block stronger downstream claims |
| `bcss_backup_slot_execution` | canonical owner | scheduler evidence | `Verified` | not certification by itself |
| `bcss_backup_job_execution` | canonical owner | execution evidence | `Verified` | not archive proof by itself |
| `bcss_backup_archive_lineage` | canonical owner | archive + integrity + lineage evidence | `Verified` | certification still separate |
| `bcss_restore_execution` | canonical owner | restore execution evidence | `Verified` in bounded scope | not full-platform proof by itself |
| `bcss_restore_drill_evidence` | canonical owner | drill/representative drill evidence | `Verified` in exercise scope | not certified recovery by itself |
| `bcss_recovery_posture` | aggregator | posture fan-in | `Observed` plus bounded embedded `Verified` subclaims | not a certification owner |
| `bcss_recovery_trust` | derived consumer | trust evidence | derived confidence only | not a verified/certified owner |
| `bcss_recovery_certification` | canonical owner | decision/certification evidence | `Certified` once class model exists | current runtime still registration-only for BCSS classes |
| `bcss_external_dependency_continuity` | aggregator | dependency evidence | `Observed` or bounded `Verified` dependency posture | not certification authority |

---

## 8. Deferred Adoption Guidance

### [Deferred implementation] Future implementation sequence
- bind archive-lineage payloads first because they already expose quality/confidence primitives
- bind recovery snapshot and backup verification surfaces next because they are the main BCSS operator surfaces
- bind trust score explicitly as confidence-only
- bind dependency continuity through the existing integration truth surface
- bind certification surfaces only after `BCSS-R13` class adoption

### [Deferred implementation] Explicitly not done here
- no route contract updates
- no UI labels added
- no claim fields added to payloads
