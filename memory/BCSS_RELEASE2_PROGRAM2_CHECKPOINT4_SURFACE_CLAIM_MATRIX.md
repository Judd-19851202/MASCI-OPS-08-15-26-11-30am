# BCSS Release 2 · Program 2 · Foundation · Checkpoint 4
## Surface Claim Matrix

This document derives constitutional authority from BCSS_RELEASE2_PROGRAM2_CHECKPOINT4_OPERATIONAL_TRUTH_SPINE.md and establishes no independent governance.

Date: 2026-07-25

---

## Entry 01
### Surface Name
`GET /api/health`

### Repository Location
`backend/routes/health_routes.py`

### Purpose
Repository classification: **canonical active surface**. Public liveness surface for current runtime reachability.

### Truth Subject(s)
`bcss_runtime_state_authority` + adjacent `platform_availability`

### Canonical Owner
`bcss_runtime_state_authority`

### Reality Sources
running FastAPI process, runtime identity bundle

### Observation Sources
HTTP 200/503 outcome, runtime identity snippet

### Evidence Types
runtime liveness evidence, runtime identity evidence

### Required Evidence
successful route execution, `ok=true|false`, runtime identity validity fields

### Optional Evidence
liveness headers

### Forbidden Evidence
trust scores, backup trust, deployment decisions

### Evidence Quality Rules
`DIRECT_OBSERVED` for liveness; `DERIVED` for embedded runtime-identity status

### Confidence Rules
`MEDIUM` when 200 + identity valid; `LOW` when identity invalid or partial

### Truth Evaluation Rules
May establish only that the service responded and what runtime identity snippet it exposed at request time.

### Current Repository Claim
Service is alive and returns runtime identity status.

### Maximum Constitutional Claim
`OBSERVED`

### Claim Ceiling Justification
Single-route liveness does not prove deeper operational health or BCSS readiness.

### Evidence Required To Raise Claim Ceiling
deep health, authoritative runtime attestation, and cross-surface consistency evidence

### Forbidden Wording
“recovery verified”, “platform certified”, “BCSS healthy”

### Permitted Wording
“API responded”, “runtime identity status observed”

### Automation Consumers
k8s/ops liveness checks, smoke scripts

### AI Consumers
future summaries may quote only as liveness evidence

### Audit Consumer
support logs and smoke reports

### Repository Evidence
`backend/routes/health_routes.py:24-43`

### Implementation Gap
No explicit OTS evidence-quality / confidence labeling

### Migration Wave
Wave 2

### Future Owner
platform runtime / BCSS runtime authority maintainers

### Truth Trace
Reality → live app process → HTTP response + runtime identity snippet → runtime liveness evidence → `DIRECT_OBSERVED` / `DERIVED` → `MEDIUM|LOW` → `bcss_runtime_state_authority` → liveness observed → `OBSERVED` → `/api/health` → smoke automation → future AI summary → support/audit record

---

## Entry 02
### Surface Name
`GET /api/version`

### Repository Location
`backend/server.py`

### Purpose
Repository classification: **canonical active surface**. Build fingerprint, release identity, uptime, and frontend/backend release-match surface.

### Truth Subject(s)
`bcss_runtime_state_authority` + adjacent `platform_availability`

### Canonical Owner
`bcss_runtime_state_authority`

### Reality Sources
backend startup state, source hash, runtime commit, served frontend identity

### Observation Sources
route payload, release-identity file reads, served frontend identity fetch

### Evidence Types
runtime identity evidence, release fingerprint evidence, uptime evidence

### Required Evidence
runtime commit, source hash, startup time

### Optional Evidence
frontend served identity, release parity reason

### Forbidden Evidence
trust scores, backup freshness, certification decisions

### Evidence Quality Rules
`DURABLE_OBSERVED` for build metadata; `DERIVED` for release-match evaluation

### Confidence Rules
`HIGH` when backend and served frontend identities align; `MEDIUM` when partial identity exists

### Truth Evaluation Rules
May establish bounded release identity and uptime truth only.

### Current Repository Claim
Backend version/release identity and uptime are exposed; frontend/backend match is evaluated.

### Maximum Constitutional Claim
`VERIFIED`

### Claim Ceiling Justification
The surface validates release identity but does not establish BCSS recovery truth.

### Evidence Required To Raise Claim Ceiling
independent validation record or deployment decision evidence

### Forbidden Wording
“deployment certified”, “platform healthy”, “recovery verified”

### Permitted Wording
“release identity verified”, “uptime observed”, “frontend/backend release match evaluated”

### Automation Consumers
deploy probes, smoke scripts, support diagnostics

### AI Consumers
future explainers may reference build identity only

### Audit Consumer
deploy and support verification logs

### Repository Evidence
`backend/server.py:1891-1925`

### Implementation Gap
No explicit separation between release-identity verification and broader operational claim language

### Migration Wave
Wave 2

### Future Owner
platform runtime / release-identity maintainers

### Truth Trace
Reality → deployed backend/frontend artifacts → startup/source identity reads → fingerprint evidence → `DURABLE_OBSERVED` + `DERIVED` → `HIGH|MEDIUM` → `bcss_runtime_state_authority` → release identity verified in scope → `VERIFIED` → `/api/version` → deploy automation → future AI explanation → deploy/support audit

---

## Entry 03
### Surface Name
`GET /api/health/full`

### Repository Location
`backend/server.py`

### Purpose
Repository classification: **canonical active surface**. Public deep-health surface for mongo/scheduler/backup/runtime checks.

### Truth Subject(s)
adjacent `platform_availability`, `bcss_runtime_state_authority`, `bcss_backup_archive_lineage`

### Canonical Owner
Composite mapped to `bcss_runtime_state_authority` for runtime truth; not an independent BCSS owner

### Reality Sources
runtime identity, mongo ping, scheduler state, backup recency state

### Observation Sources
deep health snapshot computation

### Evidence Types
runtime health evidence, scheduler evidence, backup recency evidence

### Required Evidence
public full health snapshot, runtime identity, scheduler status, backup recent truth

### Optional Evidence
diagnostics block

### Forbidden Evidence
trust score, certification decisions

### Evidence Quality Rules
`DERIVED` over direct runtime and scheduler observations

### Confidence Rules
`MEDIUM` when all inputs align; `LOW` when any child signal unavailable

### Truth Evaluation Rules
May express composite operational health posture only.

### Current Repository Claim
Current runtime/deep health is okay or degraded.

### Maximum Constitutional Claim
`CORRELATED`

### Claim Ceiling Justification
Aggregator over multiple signals; not a source-truth or certification owner.

### Evidence Required To Raise Claim Ceiling
surface-by-surface source-owner confirmations and explicit claim binding

### Forbidden Wording
“BCSS verified”, “certified healthy”

### Permitted Wording
“deep health correlated”, “current health checks align / conflict”

### Automation Consumers
ops health probes, deployment smoke

### AI Consumers
future summaries of platform health

### Audit Consumer
support/ops verification records

### Repository Evidence
`backend/server.py:1623-1629`

### Implementation Gap
Composite health not yet normalized into explicit OTS truth trace labels

### Migration Wave
Wave 1

### Future Owner
runtime and recovery platform maintainers

### Truth Trace
Reality → runtime/mongo/scheduler/backup state → full-health snapshot → mixed operational evidence → `DERIVED` → `MEDIUM|LOW` → mapped runtime/dependency/recovery subjects → composite health correlation → `CORRELATED` → `/api/health/full` → smoke automation → future AI summary → ops audit

---

## Entry 04
### Surface Name
`GET /api/admin/platform/status`

### Repository Location
`backend/server.py`, `backend/lib/platform_status.py`

### Purpose
Repository classification: **canonical active surface**. Runtime attestation and administrative platform status surface.

### Truth Subject(s)
`bcss_runtime_state_authority`

### Canonical Owner
`bcss_runtime_state_authority`

### Reality Sources
runtime identity bundle, database authority, lifecycle registry, route inventory, bytecode fingerprints

### Observation Sources
platform status builder output

### Evidence Types
runtime identity evidence, database authority evidence, lifecycle evidence, release integrity evidence

### Required Evidence
runtime identity + DB authority

### Optional Evidence
CORS summary, lifecycle migration progress, bytecode fingerprint summary

### Forbidden Evidence
trust scores, recovery posture pills, operator anecdotes

### Evidence Quality Rules
`DIRECT_OBSERVED` + `VALIDATED` for runtime/DB authority; `DERIVED` for summaries

### Confidence Rules
`HIGH` when identity valid and DB authority clean; `MEDIUM` when summary-only evidence remains

### Truth Evaluation Rules
May establish administrative runtime legitimacy and database authority only.

### Current Repository Claim
Platform runtime and authority state are attested admin-side.

### Maximum Constitutional Claim
`VERIFIED`

### Claim Ceiling Justification
Canonical owner for runtime state, but not a certification owner.

### Evidence Required To Raise Claim Ceiling
decision-recorded approval over deployment/certification scope

### Forbidden Wording
“certified deploy-ready”, “certified recovery-ready”

### Permitted Wording
“runtime authority verified”, “database authority verified”, “platform status validated in scope”

### Automation Consumers
diagnostics, governance, deploy scripts

### AI Consumers
future explainers of runtime legitimacy

### Audit Consumer
admin diagnostics and support reviews

### Repository Evidence
`backend/server.py:1345-1349`, `backend/lib/platform_status.py:1-301`

### Implementation Gap
Needs explicit OTS claim labels on the route contract

### Migration Wave
Wave 3

### Future Owner
platform runtime authority maintainers

### Truth Trace
Reality → runtime + DB authority → attestation observations → runtime/database evidence → `DIRECT_OBSERVED` + `VALIDATED` → `HIGH|MEDIUM` → `bcss_runtime_state_authority` → runtime legitimacy verified in scope → `VERIFIED` → `/api/admin/platform/status` → diagnostics automation → future AI explanation → admin audit/support review

---

## Entry 05
### Surface Name
`GET /api/platform/data-truth`

### Repository Location
`backend/routes/platform_data_truth.py`

### Purpose
Repository classification: **canonical active surface**. Public environment/data-source/banner truth for operator UI surfaces.

### Truth Subject(s)
`bcss_runtime_state_authority` + adjacent `platform_availability`

### Canonical Owner
Mapped to `bcss_runtime_state_authority`

### Reality Sources
runtime identity bundle, environment, database identity

### Observation Sources
public data-truth route payload

### Evidence Types
environment identity evidence, database identity evidence, UI banner evidence

### Required Evidence
runtime identity payload

### Optional Evidence
certification stamp, integration status flags

### Forbidden Evidence
trust scores, recovery posture, BCSS certification

### Evidence Quality Rules
`DIRECT_OBSERVED` for environment/database fields; `DERIVED` for banner payload

### Confidence Rules
`MEDIUM` when runtime identity valid; `LOW` when payload is partial

### Truth Evaluation Rules
May establish which environment/database the UI is reading, not broader health.

### Current Repository Claim
Environment and data-source truth for UI banners.

### Maximum Constitutional Claim
`CORRELATED`

### Claim Ceiling Justification
Derived public convenience surface over runtime identity.

### Evidence Required To Raise Claim Ceiling
explicit source-owner contract plus validation of all consuming surfaces

### Forbidden Wording
“production certified”, “recovery verified”

### Permitted Wording
“preview/test data”, “live production data”, “environment truth observed”

### Automation Consumers
frontend banner initialization

### AI Consumers
future UI explainers only

### Audit Consumer
support diagnostics for preview/production drift

### Repository Evidence
`backend/routes/platform_data_truth.py:1-106`

### Implementation Gap
Surface is not explicitly mapped as adjacent/composite in active claim language

### Migration Wave
Wave 2

### Future Owner
runtime identity / platform shell maintainers

### Truth Trace
Reality → runtime environment + DB identity → public data-truth observation → identity/banner evidence → `DIRECT_OBSERVED` + `DERIVED` → `MEDIUM|LOW` → `bcss_runtime_state_authority` → environment/data-source correlation → `CORRELATED` → `/api/platform/data-truth` → UI shell automation → future AI explanation → support/audit trail

---

## Entry 06
### Surface Name
`GET /api/admin/recovery/snapshot`

### Repository Location
`backend/routes/recovery_dashboard.py`

### Purpose
Repository classification: **canonical active surface**. Recovery posture aggregator for storage, archive lineage, drill, scheduler, capacity, and warnings.

### Truth Subject(s)
`bcss_recovery_posture`, `bcss_backup_archive_lineage`, `bcss_restore_drill_evidence`, `bcss_backup_slot_execution`, `bcss_backup_job_execution`

### Canonical Owner
`bcss_recovery_posture` (aggregator over upstream owners)

### Reality Sources
backup_health, drill_runs, scheduler state, bucket usage, runtime state, archive lineage

### Observation Sources
recovery snapshot builder and canonical archive-lineage resolver

### Evidence Types
archive evidence, lineage evidence, integrity evidence, scheduler evidence, drill evidence, capacity evidence, warning evidence

### Required Evidence
archive lineage + backup age + scheduler state + drill summary

### Optional Evidence
capacity warnings, activation state, RPO/RTO summaries

### Forbidden Evidence
trust score as source truth, deployment decisions as posture truth

### Evidence Quality Rules
mixed upstream `VALIDATED` / `EXERCISED` evidence summarized through `DERIVED` posture logic

### Confidence Rules
`HIGH` only for bounded subclaims backed by upstream owner evidence; surface-level posture remains `MEDIUM`

### Truth Evaluation Rules
Must separate posture summary from archive-lineage truth and drill-exercise truth.

### Current Repository Claim
Recovery posture pill and subordinate recovery indicators.

### Maximum Constitutional Claim
`CORRELATED`

### Claim Ceiling Justification
Surface is an aggregator only and current repository contract explicitly says it does not certify recovery.

### Evidence Required To Raise Claim Ceiling
explicit class-bound certification evidence under `bcss_recovery_certification`

### Forbidden Wording
“certified recovery”, “full-platform recovery verified”

### Permitted Wording
“recovery posture correlated”, “archive lineage verified in scope”, “representative drill verified in scope”

### Automation Consumers
Storage & Recovery, Recovery page, OCC recovery card

### AI Consumers
future recovery summaries only

### Audit Consumer
recovery snapshot evidence in reports and diagnostics

### Repository Evidence
`backend/routes/recovery_dashboard.py:1-625`, `backend/lib/canonical_truth.py:489-519`

### Implementation Gap
Surface needs explicit per-subclaim claim ceilings and prohibited wording

### Migration Wave
Wave 3

### Future Owner
BCSS recovery posture maintainers

### Truth Trace
Reality → backup/drill/scheduler/capacity state → recovery snapshot observation → mixed BCSS evidence → upstream `VALIDATED`/`EXERCISED` + surface `DERIVED` → `MEDIUM` posture with higher-confidence subclaims → `bcss_recovery_posture` → recovery posture correlation → `CORRELATED` → `/api/admin/recovery/snapshot` → operator and OCC consumption → future AI summary → recovery/audit record

---

## Entry 07
### Surface Name
`/admin/recovery`

### Repository Location
`frontend/src/pages/admin/AdminRecovery.jsx`

### Purpose
Repository classification: **canonical active surface**. Main admin recovery posture page consuming snapshot and backup trust.

### Truth Subject(s)
`bcss_recovery_posture`, `bcss_backup_archive_lineage`, `bcss_restore_drill_evidence`, `bcss_recovery_trust`

### Canonical Owner
Primary owner: `bcss_recovery_posture`

### Reality Sources
same upstream reality as `recovery/snapshot` plus backup trust score

### Observation Sources
`GET /api/admin/recovery/snapshot`, `GET /api/admin/backup-trust-score`

### Evidence Types
posture evidence, archive-lineage evidence, drill evidence, trust evidence

### Required Evidence
recovery snapshot payload

### Optional Evidence
backup trust score payload

### Forbidden Evidence
deployment readiness as recovery certification, trust score as source truth

### Evidence Quality Rules
UI must preserve the underlying route separation between `DERIVED` posture and `DERIVED` trust confidence.

### Confidence Rules
Page inherits confidence from child surfaces and may not upgrade it.

### Truth Evaluation Rules
The page may aggregate display but may not flatten trust, posture, and lineage into one stronger recovery claim.

### Current Repository Claim
Read-only recovery posture dashboard.

### Maximum Constitutional Claim
`CORRELATED`

### Claim Ceiling Justification
UI page combines mixed subclaims and derived trust values.

### Evidence Required To Raise Claim Ceiling
explicit claim labeling per card plus recovery certification evidence

### Forbidden Wording
“recovery certified”, “platform proven recoverable”

### Permitted Wording
“recovery posture”, “archive lineage details”, “trust confidence”, “representative drill evidence”

### Automation Consumers
none directly; human operator page

### AI Consumers
future UI explainers only

### Audit Consumer
operator screenshots, runbooks, review artifacts

### Repository Evidence
`frontend/src/pages/admin/AdminRecovery.jsx:1-419`

### Implementation Gap
No explicit in-UI OTS claim boundary disclosure per card

### Migration Wave
Wave 4

### Future Owner
Admin Recovery UI + BCSS recovery posture maintainers

### Truth Trace
Reality → BCSS recovery inputs → API observations → posture/trust evidence → `DERIVED` child payloads → inherited confidence only → recovery posture / trust subjects → bounded page rendering → `CORRELATED` → `/admin/recovery` → human operator → future AI explanation → audit screenshot/review

---

## Entry 08
### Surface Name
`/admin/storage-recovery`

### Repository Location
`frontend/src/pages/admin/AdminStorageRecovery.jsx`

### Purpose
Repository classification: **canonical active surface**. Storage & Recovery domain landing aggregating recovery snapshot, scheduler, integrations health, and lifecycle evidence.

### Truth Subject(s)
`bcss_recovery_posture`, `bcss_backup_slot_execution`, `bcss_backup_job_execution`, `bcss_backup_archive_lineage`, `bcss_external_dependency_continuity`

### Canonical Owner
Composite consumer; primary BCSS owner is `bcss_recovery_posture`

### Reality Sources
recovery snapshot, scheduler state, integrations health, bucket lifecycle signals

### Observation Sources
multiple probe calls from the page builders

### Evidence Types
recovery evidence, scheduler evidence, dependency evidence, capacity evidence

### Required Evidence
recovery snapshot

### Optional Evidence
integrations health, scheduler state, R2 lifecycle health

### Forbidden Evidence
claim inflation from page-level color chips alone

### Evidence Quality Rules
Surface is primarily `DERIVED` from child surfaces and must preserve child-surface honesty.

### Confidence Rules
Confidence is inherited from child evidence; unknown child evidence must remain unknown.

### Truth Evaluation Rules
The page may compare child truths but may not override them.

### Current Repository Claim
Storage & Recovery health and action-planning surface.

### Maximum Constitutional Claim
`CORRELATED`

### Claim Ceiling Justification
Domain landing fan-in over multiple surfaces; no certification owner role.

### Evidence Required To Raise Claim Ceiling
explicit claim binding per card and verified dependency-to-recovery mapping

### Forbidden Wording
“system recoverable”, “recovery verified end-to-end”, “certified storage state”

### Permitted Wording
“storage and recovery signals correlate”, “specific child signal degraded/unknown”

### Automation Consumers
none directly; human operator domain page

### AI Consumers
future UI explainers only

### Audit Consumer
operator review artifacts

### Repository Evidence
`frontend/src/pages/admin/AdminStorageRecovery.jsx:1-903`

### Implementation Gap
Needs standardized claim-bound language across domain cards

### Migration Wave
Wave 4

### Future Owner
Storage & Recovery UI maintainers

### Truth Trace
Reality → recovery/storage/dependency signals → page probes → child evidence bundle → child `DERIVED` and owner evidence → inherited confidence → multiple BCSS truth subjects → domain-level correlation → `CORRELATED` → `/admin/storage-recovery` → human operator → future AI explanation → review/audit artifact

---

## Entry 09
### Surface Name
`GET /api/admin/backups-scheduler-state`

### Repository Location
`backend/server.py`, `backend/routes/recovery_dashboard.py`

### Purpose
Repository classification: **canonical active surface**. Scheduler heartbeat/liveness and recent backup runtime evidence surface.

### Truth Subject(s)
`bcss_backup_slot_execution`

### Canonical Owner
`bcss_backup_slot_execution`

### Reality Sources
in-process scheduler state, scheduler locks, recent successful backup fallback, backup runtime state

### Observation Sources
canonical scheduler snapshot logic

### Evidence Types
scheduler evidence, execution evidence

### Required Evidence
last tick or backup fallback or lock evidence

### Optional Evidence
recent health rows, hourly activation state

### Forbidden Evidence
archive trust, deployment decisions

### Evidence Quality Rules
`DIRECT_OBSERVED` + `DURABLE_OBSERVED`; `VALIDATED` through canonical scheduler snapshot rules

### Confidence Rules
`HIGH` with current heartbeat; `MEDIUM` with fallback; `LOW` when stale-only

### Truth Evaluation Rules
May establish scheduler liveness and slot-bounded execution truth only.

### Current Repository Claim
Scheduler alive/healthy and recent execution posture.

### Maximum Constitutional Claim
`VERIFIED`

### Claim Ceiling Justification
Canonical owner for scheduler slot execution; not archive lineage or recovery certification.

### Evidence Required To Raise Claim Ceiling
archive lineage + restore exercise evidence for downstream recovery claims

### Forbidden Wording
“recovery verified”, “backup archive verified”, “certified ready”

### Permitted Wording
“scheduler execution verified”, “heartbeat current”, “fallback signal in use”

### Automation Consumers
Storage & Recovery page, ops scripts, OCC health

### AI Consumers
future scheduler explainers only

### Audit Consumer
backup operations review

### Repository Evidence
`backend/server.py:11890-11955`, `backend/lib/canonical_truth.py:338-367`

### Implementation Gap
Needs explicit OTS vocabulary on the route contract

### Migration Wave
Wave 1

### Future Owner
backup scheduler / BCSS slot execution maintainers

### Truth Trace
Reality → scheduler ticks/locks/recent backup → canonical snapshot observation → scheduler/slot evidence → `DIRECT_OBSERVED`/`DURABLE_OBSERVED`/`VALIDATED` → `HIGH|MEDIUM|LOW` → `bcss_backup_slot_execution` → scheduler execution verified in scope → `VERIFIED` → `/api/admin/backups-scheduler-state` → ops automation → future AI explanation → backup audit

---

## Entry 10
### Surface Name
`GET /api/admin/backups-complete-r2-state`

### Repository Location
`backend/server.py`, `backend/lib/backup_runtime.py`

### Purpose
Repository classification: **canonical active surface**. Durable backup job runtime state and overlap/heartbeat surface.

### Truth Subject(s)
`bcss_backup_job_execution`

### Canonical Owner
`bcss_backup_job_execution`

### Reality Sources
backup_jobs, backup runtime state collectors, overlap state, heartbeat state

### Observation Sources
runtime collection and route serialization

### Evidence Types
execution evidence, audit/runtime evidence

### Required Evidence
job state rows and runtime collector outputs

### Optional Evidence
hourly activation state

### Forbidden Evidence
archive lineage claims, certification decisions

### Evidence Quality Rules
`DURABLE_OBSERVED` + `VALIDATED`

### Confidence Rules
`HIGH` when durable runtime and heartbeat align; `MEDIUM` when partial runtime evidence remains

### Truth Evaluation Rules
May establish backup job execution state only.

### Current Repository Claim
Backup jobs completed / active / overlapped state is exposed.

### Maximum Constitutional Claim
`VERIFIED`

### Claim Ceiling Justification
Canonical owner for job execution, but not for archive recoverability.

### Evidence Required To Raise Claim Ceiling
archive lineage evidence and drill evidence

### Forbidden Wording
“archive verified”, “recovery verified”, “certified backup”

### Permitted Wording
“backup job execution verified”, “runtime overlap observed”

### Automation Consumers
recovery snapshot, system pages

### AI Consumers
future job execution explainers only

### Audit Consumer
backup operations review

### Repository Evidence
`backend/lib/canonical_truth.py:368-397`, `backend/server.py` route registration references

### Implementation Gap
Route not yet explicitly surfaced in OTS claim matrix language at runtime

### Migration Wave
Wave 1

### Future Owner
backup runtime / BCSS job execution maintainers

### Truth Trace
Reality → backup job runtime and ledgers → route observation → execution evidence → `DURABLE_OBSERVED` + `VALIDATED` → `HIGH|MEDIUM` → `bcss_backup_job_execution` → backup job execution verified in scope → `VERIFIED` → `/api/admin/backups-complete-r2-state` → recovery automation → future AI explanation → backup audit

---

## Entry 11
### Surface Name
`GET /api/admin/backup-trust-score`

### Repository Location
`backend/server.py`, `backend/lib/trust_score.py`

### Purpose
Repository classification: **canonical active surface**. Deterministic backup/recovery trust-confidence surface.

### Truth Subject(s)
`bcss_recovery_trust`

### Canonical Owner
`bcss_recovery_trust`

### Reality Sources
archive lineage, drill freshness, backup runtime overlap, failures_7d, bucket usage

### Observation Sources
trust score computation route

### Evidence Types
trust evidence, archive evidence, drill evidence, capacity evidence

### Required Evidence
archive lineage payload and trust score inputs

### Optional Evidence
hourly activation, runtime overlap details

### Forbidden Evidence
decision-recorded certification evidence, operator assertions

### Evidence Quality Rules
Primary surface quality is `DERIVED` over upstream evidence.

### Confidence Rules
Surface expresses confidence only; it does not independently upgrade confidence of upstream truths.

### Truth Evaluation Rules
Trust score may summarize confidence and penalties only.

### Current Repository Claim
Backup/recovery trust score and score inputs.

### Maximum Constitutional Claim
`CORRELATED`

### Claim Ceiling Justification
Canonical truth registry explicitly limits it to derived confidence, not certification authority.

### Evidence Required To Raise Claim Ceiling
upstream owner verification + explicit certification decision evidence

### Forbidden Wording
“recovery verified”, “certified recoverable”, “proof of restore”

### Permitted Wording
“confidence score”, “derived trust posture”, “penalty-based trust model”

### Automation Consumers
Admin Recovery page

### AI Consumers
future risk summaries only

### Audit Consumer
review of trust trends and score inputs

### Repository Evidence
`backend/server.py:11958-12026`, `backend/lib/canonical_truth.py:520-550`

### Implementation Gap
Needs explicit route-level warning that trust is not verification or certification

### Migration Wave
Wave 3

### Future Owner
BCSS recovery trust maintainers

### Truth Trace
Reality → archive/drill/runtime/capacity conditions → trust-score observation → trust evidence → `DERIVED` → inherited confidence only → `bcss_recovery_trust` → confidence correlation → `CORRELATED` → `/api/admin/backup-trust-score` → operator UI → future AI risk summary → trust review/audit

---

## Entry 12
### Surface Name
`GET /api/admin/backup-verification/state`

### Repository Location
`backend/routes/backup_verification_routes.py`

### Purpose
Repository classification: **canonical active surface**. Read-only cron configuration and last/next verification state surface.

### Truth Subject(s)
`bcss_backup_archive_lineage` (supporting state), `bcss_backup_slot_execution`

### Canonical Owner
Primary BCSS owner: `bcss_backup_archive_lineage`; route is a support-state surface, not the validation report itself

### Reality Sources
backup_health marker row, schedule configuration, recipients config

### Observation Sources
state route payload

### Evidence Types
scheduler evidence, notification configuration evidence, verification schedule evidence

### Required Evidence
enabled flag, last run marker, next fire calculation

### Optional Evidence
recipient list, threshold hours

### Forbidden Evidence
treating config state as archive validation proof

### Evidence Quality Rules
`DURABLE_OBSERVED` for last-run marker; `DIRECT_OBSERVED` for current config

### Confidence Rules
`MEDIUM` for scheduler/config state; not a truth surface for archive quality

### Truth Evaluation Rules
May establish only that the verification mechanism is configured/scheduled and when it last ran.

### Current Repository Claim
Verification cron enabled/disabled, recipients, and last/next fire metadata.

### Maximum Constitutional Claim
`OBSERVED`

### Claim Ceiling Justification
Configuration/schedule state is not archive verification evidence.

### Evidence Required To Raise Claim Ceiling
preview/report output from actual verification run

### Forbidden Wording
“backup verified”, “archives validated”, “recoverable point proven”

### Permitted Wording
“verification cron configured”, “last run observed”, “next run scheduled”

### Automation Consumers
AdminBackupVerificationPanel

### AI Consumers
future administrative explainers only

### Audit Consumer
cron/run-history review

### Repository Evidence
`backend/routes/backup_verification_routes.py:67-94`

### Implementation Gap
Needs explicit separation from actual validation/report claims

### Migration Wave
Wave 3

### Future Owner
backup verification maintainers

### Truth Trace
Reality → cron config + marker rows → state observation → schedule/config evidence → `DIRECT_OBSERVED` + `DURABLE_OBSERVED` → `MEDIUM` → mapped archive-lineage support state → schedule observed → `OBSERVED` → `/api/admin/backup-verification/state` → admin UI → future AI explainer → operations audit

---

## Entry 13
### Surface Name
`GET /api/admin/backup-verification/preview`

### Repository Location
`backend/routes/backup_verification_routes.py`, `backend/backup_verification.py`

### Purpose
Repository classification: **canonical active surface**. On-demand validation preview that builds the backup verification report without emailing it.

### Truth Subject(s)
`bcss_backup_archive_lineage`, `bcss_restore_execution` (bounded only where report discusses claim boundaries)

### Canonical Owner
`bcss_backup_archive_lineage`

### Reality Sources
backup_health, R2 metadata, archive lineage, manifest reads, ledger rows

### Observation Sources
verification report builder

### Evidence Types
archive evidence, integrity evidence, lineage evidence, ledger evidence

### Required Evidence
archive lineage payload, R2 archive facts, backup ledger context

### Optional Evidence
collection counts, secondary diagnostic object observation

### Forbidden Evidence
restore certification claims, deploy-readiness claims

### Evidence Quality Rules
`VALIDATED` over archive/integrity/lineage evidence with explicit degradation reasons

### Confidence Rules
`HIGH` when authoritative recoverable point is proven; `LOW|MEDIUM` when only secondary observation remains

### Truth Evaluation Rules
Must preserve the report’s explicit claim-boundary language.

### Current Repository Claim
Latest archive verification preview with verdict and issues.

### Maximum Constitutional Claim
`VALIDATED`

### Claim Ceiling Justification
Surface performs explicit validation but still states it does not prove restore certification or BCSS recovery-class certification.

### Evidence Required To Raise Claim Ceiling
restore exercise proof and class-bound certification evidence

### Forbidden Wording
“certified recovery”, “production restore proven”

### Permitted Wording
“archive lineage validated”, “authoritative recoverable point validated in scope”, “secondary diagnostic evidence only”

### Automation Consumers
AdminBackupVerificationPanel preview action

### AI Consumers
future summary/explanation of report only

### Audit Consumer
verification artifacts and operator review

### Repository Evidence
`backend/routes/backup_verification_routes.py:31-36`, `backend/backup_verification.py:593-729`

### Implementation Gap
Needs explicit route-level OTS claim ladder disclosure separate from HTML report wording

### Migration Wave
Wave 3

### Future Owner
backup verification and archive lineage maintainers

### Truth Trace
Reality → archive/ledger facts → verification preview generation → archive/integrity/lineage evidence → `VALIDATED` (+ `DIRECT_OBSERVED` secondary diagnostics where applicable) → `HIGH|MEDIUM|LOW` → `bcss_backup_archive_lineage` → bounded validation truth → `VALIDATED` → preview route → admin operator → future AI summary → verification artifact/audit

---

## Entry 14
### Surface Name
Backup Verification report / email

### Repository Location
`backend/backup_verification.py`, `frontend/src/components/AdminBackupVerificationPanel.jsx`

### Purpose
Repository classification: **canonical active surface**. Operator-visible report/email artifact for bounded archive verification.

### Truth Subject(s)
`bcss_backup_archive_lineage`

### Canonical Owner
`bcss_backup_archive_lineage`

### Reality Sources
same sources as preview report

### Observation Sources
HTML report rendering and delivered email/report content

### Evidence Types
archive evidence, integrity evidence, lineage evidence, report decision text

### Required Evidence
generated verification report

### Optional Evidence
delivery evidence, recipient evidence

### Forbidden Evidence
certification claims, full restore claims, production recovery claims

### Evidence Quality Rules
`VALIDATED` for primary claim; `DIRECT_OBSERVED` for newest-object diagnostic section

### Confidence Rules
Report must expose lineage confidence and degradation reasons directly.

### Truth Evaluation Rules
The report must preserve “secondary diagnostic evidence only” and “claim boundary” language.

### Current Repository Claim
Weekly backup verification report describing archive lineage, integrity, completeness, and freshness.

### Maximum Constitutional Claim
`VALIDATED`

### Claim Ceiling Justification
Report explicitly validates archive-lineage truth but also explicitly denies stronger certification claims.

### Evidence Required To Raise Claim Ceiling
restore-exercise evidence plus BCSS recovery certification class evidence

### Forbidden Wording
“restore certified”, “BCSS certified”, “production continuity proven”

### Permitted Wording
“authoritative recoverable point”, “secondary diagnostic evidence only”, “claim boundary”

### Automation Consumers
weekly cron, manual run-now pipeline

### AI Consumers
future explanatory summaries of the report

### Audit Consumer
email artifact, backup health marker, operator review trail

### Repository Evidence
`backend/backup_verification.py:666-741`, `frontend/src/components/AdminBackupVerificationPanel.jsx:119-293`

### Implementation Gap
Need uniform claim-ladder disclosure if surfaced outside the report/email body

### Migration Wave
Wave 4

### Future Owner
backup verification/reporting maintainers

### Truth Trace
Reality → archive/ledger facts → report generation → validation evidence + diagnostic observation → `VALIDATED` + explicit diagnostic `OBSERVED` note → explicit confidence text → `bcss_backup_archive_lineage` → bounded validated claim → report/email surface → operators / notification channel → future AI explanation → archived verification artifact

---

## Entry 15
### Surface Name
`GET /api/admin/deployment-readiness`

### Repository Location
`backend/routes/admin_deployment_readiness.py`

### Purpose
Repository classification: **canonical active surface**. Read-only deployment gate that separates code defects from operator-data issues.

### Truth Subject(s)
`bcss_recovery_certification` (bounded), adjacent platform deploy readiness truth

### Canonical Owner
`bcss_recovery_certification`

### Reality Sources
trust spine payload, master-data findings, audit integrity, silent failures, delivery contract

### Observation Sources
deployment-readiness decision builder

### Evidence Types
validation evidence, decision evidence, workflow evidence, governance evidence

### Required Evidence
blocking gates and advisory findings

### Optional Evidence
trust score reference, summary counters

### Forbidden Evidence
archive age alone, trust score alone, unbounded recovery posture

### Evidence Quality Rules
`VALIDATED` for gate evaluation; `DECISION_RECORDED` only when paired with ledger/history persistence elsewhere

### Confidence Rules
`HIGH` when blocking/advisory logic completes; `MEDIUM` when some child evidence unavailable

### Truth Evaluation Rules
Surface may certify deploy-readiness scope only.

### Current Repository Claim
Platform code is safe or unsafe to deploy right now, with blockers/advisories.

### Maximum Constitutional Claim
`CERTIFIED`

### Claim Ceiling Justification
Explicit decision gate with bounded scope, but current canonical truth notes this is not equivalent to BCSS recovery-class certification.

### Evidence Required To Raise Claim Ceiling
recovery-class evidence model under `BCSS-R13`

### Forbidden Wording
“BCSS recovery certified”, “production survival certified”, “full-platform recovery certified”

### Permitted Wording
“deployment readiness certified in scope”, “deploy blocked”, “deploy advisory”

### Automation Consumers
deploy gate scripts, OCC trust events

### AI Consumers
future release summaries only

### Audit Consumer
deployment decision records and closeout reviews

### Repository Evidence
`backend/routes/admin_deployment_readiness.py:1-403`, `backend/lib/canonical_truth.py:551-580`

### Implementation Gap
Needs explicit certification-scope language in every downstream consumer

### Migration Wave
Wave 7

### Future Owner
deployment governance + future BCSS certification maintainers

### Truth Trace
Reality → workflow/audit/governance state → readiness evaluation → validation/decision evidence → `VALIDATED` / `DECISION_RECORDED` → `HIGH|MEDIUM` → `bcss_recovery_certification` (bounded scope) → deploy-readiness decision → `CERTIFIED` (deployment scope only) → `/api/admin/deployment-readiness` → deploy automation → future AI release summary → deployment ledger/audit

---

## Entry 16
### Surface Name
`GET /api/admin/deployment-readiness/history`

### Repository Location
`backend/routes/admin_deployment_ledger.py`

### Purpose
Repository classification: **canonical active surface**. Immutable historical ledger of deploy-readiness decisions.

### Truth Subject(s)
`bcss_recovery_certification` (historical bounded decision evidence)

### Canonical Owner
`bcss_recovery_certification`

### Reality Sources
deployment_decisions immutable collection

### Observation Sources
history route over ledger rows

### Evidence Types
decision-recorded evidence, audit evidence

### Required Evidence
immutable decision rows

### Optional Evidence
verification_id, release/build metadata

### Forbidden Evidence
retrofitting history into present-tense certification without current decision context

### Evidence Quality Rules
`DECISION_RECORDED`

### Confidence Rules
`HIGH` for what decision was recorded; not for current deploy state unless paired with freshness evaluation

### Truth Evaluation Rules
May establish historical deployment decisions only.

### Current Repository Claim
History of pass/fail deployment decisions.

### Maximum Constitutional Claim
`CERTIFIED`

### Claim Ceiling Justification
Immutable decision ledger preserves certified historical decision records in bounded scope.

### Evidence Required To Raise Claim Ceiling
current decision context if used as present-tense claim

### Forbidden Wording
“currently certified” from stale history alone

### Permitted Wording
“historical deployment decision recorded”, “pass/fail decision on date X”

### Automation Consumers
release reporting, audit review

### AI Consumers
future historical release summaries only

### Audit Consumer
deployment forensics

### Repository Evidence
`backend/routes/admin_deployment_ledger.py:1-159`

### Implementation Gap
Needs explicit freshness-bound wording if reused outside the ledger view

### Migration Wave
Wave 7

### Future Owner
deployment governance maintainers

### Truth Trace
Reality → deploy decision event → immutable ledger write → decision-recorded evidence → `DECISION_RECORDED` → `HIGH` for historical fact → `bcss_recovery_certification` (bounded historical scope) → historical certified decision → `CERTIFIED` (historical deployment scope) → history route → reporting automation → future AI history summary → forensic audit

---

## Entry 17
### Surface Name
`GET /api/admin/production-certification`

### Repository Location
`backend/routes/admin_production_certification.py`, `backend/lib/production_certification.py`

### Purpose
Repository classification: **canonical active adjacent surface**. Continuous per-workflow operational certification built from trust spine evidence.

### Truth Subject(s)
adjacent operational certification concept; BCSS mapping touches `bcss_recovery_certification` only where scopes overlap

### Canonical Owner
No distinct BCSS owner; adjacent certification surface

### Reality Sources
trust_spine_events terminal success/failure evidence

### Observation Sources
production certification builder

### Evidence Types
workflow lifecycle evidence, freshness evidence

### Required Evidence
completed/completed_for_environment trust spine events

### Optional Evidence
failure remediation, audit correlation hints

### Forbidden Evidence
relabeling operational workflow certification as BCSS recovery certification

### Evidence Quality Rules
`EXERCISED` + `VALIDATED` over trust-spine terminal evidence

### Confidence Rules
`HIGH` within workflow scope when terminal evidence is current; `LOW` when stale or not-yet-exercised

### Truth Evaluation Rules
May certify workflow execution readiness/health within its own operational scope only.

### Current Repository Claim
Per-workflow statuses such as VERIFIED / FAILED / STALE / NOT_YET_EXERCISED.

### Maximum Constitutional Claim
`VALIDATED`

### Claim Ceiling Justification
Surface uses the word certification, but repository evidence shows operational workflow validation/certification, not BCSS recovery-class certification.

### Evidence Required To Raise Claim Ceiling
explicit BCSS recovery class model and certification owner decision evidence

### Forbidden Wording
“BCSS certified”, “recovery certified”, “platform survivability certified”

### Permitted Wording
“workflow validated/certified within operational scope”, “not yet exercised”, “stale evidence”

### Automation Consumers
Governance & Trust domain landing

### AI Consumers
future operational summaries only

### Audit Consumer
trust-spine evidence review

### Repository Evidence
`backend/routes/admin_production_certification.py:1-28`, `backend/lib/production_certification.py:1-427`

### Implementation Gap
Needs explicit constitutional distinction from BCSS recovery certification

### Migration Wave
Wave 7

### Future Owner
production/operations certification maintainers

### Truth Trace
Reality → workflow execution events → trust-spine terminal observations → lifecycle evidence → `EXERCISED` + `VALIDATED` → `HIGH|LOW` by freshness/scope → adjacent operational certification concept → workflow truth evaluation → `VALIDATED` → production certification route → reporting automation → future AI summary → ops audit

---

## Entry 18
### Surface Name
`/admin/deploy-recovery`

### Repository Location
`frontend/src/pages/admin/DeployRecovery.jsx`, `backend/routes/admin_ops.py`

### Purpose
Repository classification: **canonical active surface**. Read-only deploy recovery playbook plus current build/R2/recent backup evidence.

### Truth Subject(s)
`bcss_runtime_state_authority`, `bcss_backup_archive_lineage`, adjacent deploy readiness truth

### Canonical Owner
Composite consumer; no new BCSS owner

### Reality Sources
current build env vars, recent backups, R2 configuration state, known-good history

### Observation Sources
`GET /api/admin/deploy-recovery` consumed by page

### Evidence Types
release evidence, backup evidence, R2 configuration evidence, historical deploy evidence

### Required Evidence
current version + recent backups

### Optional Evidence
R2 detail, known-good build history

### Forbidden Evidence
claiming deploy or recovery certification from static playbook text alone

### Evidence Quality Rules
mixed `DIRECT_OBSERVED`, `DURABLE_OBSERVED`, and page-level static guidance

### Confidence Rules
`MEDIUM`; playbook guidance must not be read as present-tense validated truth without current route data

### Truth Evaluation Rules
Page may support operator action planning only.

### Current Repository Claim
Rollback playbook with current build / backup chain context.

### Maximum Constitutional Claim
`OBSERVED`

### Claim Ceiling Justification
UI combines static guidance and current context; it is not the certification or verification owner.

### Evidence Required To Raise Claim Ceiling
explicit linkage to current deployment-readiness certification decision

### Forbidden Wording
“deploy certified”, “recovery certified”, “safe to deploy” from the page alone

### Permitted Wording
“playbook available”, “current backup chain observed”, “rollback guidance provided”

### Automation Consumers
none directly

### AI Consumers
future operator guidance explainers only

### Audit Consumer
operator review of rollback readiness

### Repository Evidence
`frontend/src/pages/admin/DeployRecovery.jsx:1-197`, `backend/routes/admin_ops.py:588-649`

### Implementation Gap
Needs clean separation between static guidance and live bounded claims

### Migration Wave
Wave 4

### Future Owner
deploy operations UI maintainers

### Truth Trace
Reality → build/backup/R2/history state → deploy-recovery route observation + static playbook text → mixed evidence + guidance → `DIRECT_OBSERVED`/`DURABLE_OBSERVED` → `MEDIUM` → mapped runtime/archive subjects → bounded operator guidance truth → `OBSERVED` → `/admin/deploy-recovery` → human operator → future AI guide → review/audit artifact

---

## Entry 19
### Surface Name
`GET /api/admin/integrations/truth-status`

### Repository Location
`backend/routes/integration_truth.py`

### Purpose
Repository classification: **canonical active surface**. Integration configuration, connectivity, and operational continuity truth surface.

### Truth Subject(s)
`bcss_external_dependency_continuity`

### Canonical Owner
`bcss_external_dependency_continuity`

### Reality Sources
runtime env vars, integration_settings, provider probes, recent sync activity, delivery contract

### Observation Sources
integration truth payload builder

### Evidence Types
external dependency evidence, provider-acceptance evidence, safe-capture evidence

### Required Evidence
config state, connectivity state, operational state

### Optional Evidence
AI key status, alias telemetry

### Forbidden Evidence
configuration alone interpreted as live continuity proof

### Evidence Quality Rules
`DIRECT_OBSERVED` for config/connectivity; `DURABLE_OBSERVED` for recent sync activity; `DERIVED` for overall posture

### Confidence Rules
`HIGH` when live activity + reachability align; `MEDIUM` when config only; `LOW` when unreachable or stale

### Truth Evaluation Rules
Must preserve three-state doctrine and never collapse config into live proof.

### Current Repository Claim
Integration overall/status truth with separated config/connectivity/operational posture.

### Maximum Constitutional Claim
`VERIFIED` for bounded dependency subclaims; surface-level aggregate `CORRELATED`

### Claim Ceiling Justification
Canonical dependency continuity owner, but aggregate overall state remains derived over multiple sub-signals.

### Evidence Required To Raise Claim Ceiling
explicit claim binding per provider row and continuity certification class if ever introduced

### Forbidden Wording
“all dependencies certified”, “live verified from config alone”

### Permitted Wording
“dependency continuity posture”, “configured”, “reachable”, “live verified in bounded provider scope”

### Automation Consumers
Integration Truth page, recovery dependency reads

### AI Consumers
future dependency summaries only

### Audit Consumer
integration posture reviews

### Repository Evidence
`backend/routes/integration_truth.py:1-811`, `backend/lib/canonical_truth.py:582-611`

### Implementation Gap
Needs explicit OTS mapping of notification delivery and AI key surfaces to dependency continuity language

### Migration Wave
Wave 3

### Future Owner
integration truth / dependency continuity maintainers

### Truth Trace
Reality → provider config/connectivity/activity → integration truth observations → dependency evidence → `DIRECT_OBSERVED`/`DURABLE_OBSERVED`/`DERIVED` → `HIGH|MEDIUM|LOW` → `bcss_external_dependency_continuity` → bounded provider verification + overall correlation → `CORRELATED` / bounded `VERIFIED` → truth-status route → UI/automation → future AI summary → integration audit

---

## Entry 20
### Surface Name
`/admin/integration-truth`

### Repository Location
`frontend/src/pages/admin/IntegrationTruth.jsx`

### Purpose
Repository classification: **canonical active surface**. Operator page for AI key status, integration truth, and legacy alias telemetry.

### Truth Subject(s)
`bcss_external_dependency_continuity`

### Canonical Owner
Primary owner: `bcss_external_dependency_continuity`

### Reality Sources
integration truth route, AI key status route, alias telemetry route

### Observation Sources
frontend page fetches and panel renders

### Evidence Types
dependency evidence, key-status evidence, telemetry evidence

### Required Evidence
integration truth payload

### Optional Evidence
AI key rows, alias telemetry retirement posture

### Forbidden Evidence
upgrading configuration posture into continuity certification

### Evidence Quality Rules
Page inherits child route evidence and must not rewrite their claim ceilings.

### Confidence Rules
Inherited only; page-level badges may not strengthen child route confidence.

### Truth Evaluation Rules
The page may present child truths side-by-side only.

### Current Repository Claim
Integration and AI key runtime truth panel.

### Maximum Constitutional Claim
`CORRELATED`

### Claim Ceiling Justification
UI page aggregates multiple child panels and derived badges.

### Evidence Required To Raise Claim Ceiling
per-panel claim binding and explicit notification-delivery mapping

### Forbidden Wording
“all integrations certified”, “AI fully operational”, “dependency continuity proven”

### Permitted Wording
“integration truth”, “AI key status”, “runtime dependency posture”

### Automation Consumers
none directly; human operator page

### AI Consumers
future UI explainers only

### Audit Consumer
operator investigation artifacts

### Repository Evidence
`frontend/src/pages/admin/IntegrationTruth.jsx:1-556`

### Implementation Gap
Needs visible OTS wording for bounded provider-level vs aggregate claims

### Migration Wave
Wave 4

### Future Owner
Integration Truth UI maintainers

### Truth Trace
Reality → dependency/provider state → route observations → dependency/key/telemetry evidence → child route qualities only → inherited confidence → `bcss_external_dependency_continuity` + adjacent AI-key posture → page-level correlation → `CORRELATED` → `/admin/integration-truth` → human operator → future AI explanation → review/audit artifact

---

## Entry 21
### Surface Name
`GET /api/admin/occ/health`

### Repository Location
`backend/routes/occ_health_aggregator.py`

### Purpose
Repository classification: **canonical active adjacent surface**. Operations Control Center health aggregator over multiple upstream probes.

### Truth Subject(s)
adjacent `operational_health`, plus imported runtime/recovery/dependency truths

### Canonical Owner
No BCSS owner of its own; mapped composite consumer

### Reality Sources
child endpoint fanout, runtime identity bundle, per-card evaluator evidence

### Observation Sources
fresh probe fanout per request

### Evidence Types
health evidence, recovery evidence, dependency evidence, AI gateway evidence, governance evidence

### Required Evidence
successful probe results or explicit probe failures

### Optional Evidence
runtime identity card, root-cause grouping

### Forbidden Evidence
treating aggregate worst-status as authoritative source truth for child surfaces

### Evidence Quality Rules
`DERIVED` only

### Confidence Rules
`MEDIUM` when probes are current; `LOW` when many children are unreachable

### Truth Evaluation Rules
Must preserve child-source truth and disclose probe failures separately.

### Current Repository Claim
One canonical OCC trust snapshot with card-by-card status.

### Maximum Constitutional Claim
`CORRELATED`

### Claim Ceiling Justification
Aggregator only; explicit repository contract says upstream canonical owners remain authoritative.

### Evidence Required To Raise Claim Ceiling
none; surface should remain aggregator-only

### Forbidden Wording
“certified healthy”, “source truth”, “BCSS verified”

### Permitted Wording
“aggregated operational health”, “probe-derived posture”, “child source truth remains authoritative”

### Automation Consumers
OCC frontend

### AI Consumers
future operational prioritization only

### Audit Consumer
root-cause grouping and operator review

### Repository Evidence
`backend/routes/occ_health_aggregator.py:1-794`, especially `CARDS` at `560-628`

### Implementation Gap
Needs explicit OTS claim boundaries per card and per aggregate posture

### Migration Wave
Wave 5

### Future Owner
OCC / operations-control maintainers

### Truth Trace
Reality → child source states → probe fanout observations → mixed child evidence → `DERIVED` aggregate only → `MEDIUM|LOW` → mapped composite operational health concept → posture correlation → `CORRELATED` → `/api/admin/occ/health` → OCC automation/UI → future AI prioritization → OCC audit/review

---

## Entry 22
### Surface Name
`GET /api/admin/trust-spine`

### Repository Location
`backend/routes/admin_trust_spine.py`

### Purpose
Repository classification: **canonical active adjacent surface**. Workflow lifecycle truth rollup over trust-spine events.

### Truth Subject(s)
adjacent workflow lifecycle truth; BCSS-adjacent support for certification and operational trust

### Canonical Owner
`trust_spine` (adjacent canonical owner outside the BCSS-specific 10-subject set)

### Reality Sources
`trust_spine_events`, expected stage contract

### Observation Sources
per-workflow aggregation, last failure/success lookups

### Evidence Types
workflow lifecycle evidence, audit-stage evidence

### Required Evidence
trust_spine_events over last 24h

### Optional Evidence
workflow drilldown events

### Forbidden Evidence
archive/recovery certification claims without BCSS owner binding

### Evidence Quality Rules
`DURABLE_OBSERVED` + `VALIDATED` by expected-stage contract

### Confidence Rules
`HIGH` where full expected stages are satisfied; `LOW` when no activity or failures exist

### Truth Evaluation Rules
May establish workflow lifecycle truth only.

### Current Repository Claim
Per-workflow lifecycle band, reason, and remediation.

### Maximum Constitutional Claim
`VALIDATED`

### Claim Ceiling Justification
Contract validator over trust-spine evidence, but not BCSS recovery certification.

### Evidence Required To Raise Claim Ceiling
scope-specific certification decision evidence

### Forbidden Wording
“BCSS certified”, “recovery certified”, “platform source truth”

### Permitted Wording
“workflow lifecycle validated”, “missing evidence”, “no activity”, “failing”

### Automation Consumers
Operations Trust Center, Platform Trust Dashboard/Validator inputs

### AI Consumers
future operational summaries only

### Audit Consumer
workflow evidence and drilldown review

### Repository Evidence
`backend/routes/admin_trust_spine.py:1-259`, `backend/lib/canonical_truth.py:98-126`

### Implementation Gap
Needs formal BCSS-adjacent mapping where consumed by BCSS surfaces

### Migration Wave
Wave 2

### Future Owner
platform trust spine maintainers

### Truth Trace
Reality → workflow lifecycle events → rollup observations → lifecycle evidence → `DURABLE_OBSERVED` + `VALIDATED` → `HIGH|LOW` by stage completion → adjacent workflow lifecycle truth → validation result → `VALIDATED` → `/api/admin/trust-spine` → trust surfaces/automation → future AI summary → lifecycle audit

---

## Entry 23
### Surface Name
`GET /api/admin/operations-trust-center`

### Repository Location
`backend/routes/admin_operations_trust_center.py`

### Purpose
Repository classification: **canonical active adjacent surface**. Derived operational trust score and prioritized action center.

### Truth Subject(s)
adjacent shared operational trust score; BCSS consumption touches recovery trust and lifecycle trust only indirectly

### Canonical Owner
`operations_trust_center` derived consumer

### Reality Sources
trust spine payload, master data trust findings, audit counts, trust history

### Observation Sources
categorized score computation and panel payload

### Evidence Types
trust evidence, workflow evidence, master-data evidence

### Required Evidence
trust spine rows and master data findings

### Optional Evidence
trend history, operator action links

### Forbidden Evidence
using derived score as source truth or certification

### Evidence Quality Rules
`DERIVED`

### Confidence Rules
Expresses confidence/trust posture only; inherited confidence from child evidence

### Truth Evaluation Rules
Must remain a derived consumer and not become canonical truth.

### Current Repository Claim
“Can I trust this platform to run operations today?” with score, band, findings, actions.

### Maximum Constitutional Claim
`CORRELATED`

### Claim Ceiling Justification
Derived consumer only per canonical truth contract.

### Evidence Required To Raise Claim Ceiling
none; should remain derived

### Forbidden Wording
“verified platform”, “certified operations”, “source truth”

### Permitted Wording
“operational trust score”, “derived risk posture”, “prioritized actions”

### Automation Consumers
Admin Email page embedding

### AI Consumers
future prioritization/recommendation only

### Audit Consumer
trust trend/history review

### Repository Evidence
`backend/routes/admin_operations_trust_center.py:1-543`, `backend/lib/canonical_truth.py:246-276`

### Implementation Gap
Needs explicit in-surface claim boundary text wherever rendered with stronger-sounding bands

### Migration Wave
Wave 5

### Future Owner
operations trust maintainers

### Truth Trace
Reality → trust-spine + master-data conditions → score/action observations → trust evidence → `DERIVED` → inherited confidence only → adjacent operational trust concept → risk correlation → `CORRELATED` → operations-trust-center route → operator UI/automation → future AI prioritization → trust review/audit

---

## Entry 24
### Surface Name
`GET /api/admin/platform-trust/validate`

### Repository Location
`backend/routes/admin_platform_trust.py`

### Purpose
Repository classification: **canonical active adjacent surface**. Defensive validator over system heartbeat, email routing, audit integrity, workflow delivery, PM coverage, and dead-letter health.

### Truth Subject(s)
adjacent `platform_validation_truth`; imports runtime and integration truths

### Canonical Owner
`platform_trust_validator` validator surface

### Reality Sources
health/full heartbeat, email routing status, PM coverage, `email_routing_audit_v2`

### Observation Sources
validator route payload

### Evidence Types
validation evidence, audit evidence, workflow delivery evidence

### Required Evidence
system block, email routing block, audit integrity block, workflow health rows

### Optional Evidence
dead-letter and PM coverage summaries

### Forbidden Evidence
representing validator verdict as canonical platform source truth or BCSS certification

### Evidence Quality Rules
`VALIDATED` over admin-safe evidence only

### Confidence Rules
`HIGH` when validator completes with complete evidence; `MEDIUM` with partial data

### Truth Evaluation Rules
Validation verdict is separate from source truth and certification.

### Current Repository Claim
Platform trust validation pass/attention/critical with explicit reasons.

### Maximum Constitutional Claim
`VALIDATED`

### Claim Ceiling Justification
Surface is validator-only by contract.

### Evidence Required To Raise Claim Ceiling
decision-recorded certification evidence under a certification owner

### Forbidden Wording
“canonical truth”, “certified platform”, “BCSS recovery certified”

### Permitted Wording
“validation passed”, “validation failed”, “critical reasons”, “attention reasons”

### Automation Consumers
Admin Email page embedding, governance trust inputs

### AI Consumers
future operational explanation only

### Audit Consumer
validation reviews and deploy support

### Repository Evidence
`backend/routes/admin_platform_trust.py:1-404`, `frontend/src/components/PlatformTrustValidator.jsx:1-368`

### Implementation Gap
Needs explicit OTS mapping when consumed alongside BCSS recovery surfaces

### Migration Wave
Wave 5

### Future Owner
platform trust validation maintainers

### Truth Trace
Reality → system/email/audit/workflow conditions → validation observations → validation evidence → `VALIDATED` → `HIGH|MEDIUM` → adjacent platform validation truth → validation verdict → `VALIDATED` → validator route → UI/automation → future AI explanation → validation audit
