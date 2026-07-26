# BCSS RELEASE 2 · PLATFORM SURVIVABILITY PROGRAM
# PHASE 1 — CANONICAL BASELINE ADOPTION
# BCSS_RELEASE2_PLATFORM_SURVIVABILITY_BASELINE_AND_DISCOVERY

Date: 2026-07-26
Status: Discovery Baseline Adopted
Authority Class: Canonical planning authority for survivability implementation sequencing

---

## 1. Executive Summary

This document is the single authoritative survivability baseline for BCSS Release 2.

It converts repository evidence, runtime evidence, discovery evidence, live health evidence, supervisor-log evidence, and existing recovery/deployment evidence into one canonical planning baseline for all future Platform Survivability work.

This is a discovery baseline.

It is **NOT** a survivability certification.

### Current survivability posture

- Backup capability is present, active, and supported by recent successful runtime evidence.
- Database persistence is present, live, and evidenced by healthy runtime connectivity and durable operational collections.
- Object storage is present and actively used for backup archives and file/photo references.
- Scheduler liveness and lock behavior are evidenced in runtime logs.
- Monitoring and readiness surfaces are present and exercised.
- Restore tooling exists, but current restore capability is **NOT VERIFIED** because the latest recorded restore drill failed.
- Secrets/configuration recovery remains unproven by exercised evidence.
- Notification handling is evidenced in preview safe-capture mode, but live provider delivery remains unverified.

### Strongest verified capabilities

- Recent successful backup execution to R2-backed archive lineage.
- Healthy live backend, readiness, and full-health endpoints.
- Active Atlas-backed database persistence in preview runtime.
- Scheduler lock acquisition and continuous runtime activity.
- Persistent backup evidence collections and drift-watch evidence.
- Preview notification safe-capture evidence.

### Major survivability risks

- Restore certification is not established.
- Secrets/configuration recovery certification is not established.
- Backup verification deep-inspection confidence is reduced by current manifest-read timeouts.
- Notification evidence is partial because provider acceptance and delivery confirmation are not proven in the current environment.

### Implementation philosophy

- Recoverability first.
- Evidence elevation second.
- Hardening and optimization last.
- Repository and runtime evidence override documentation.
- Exercised capability always outranks declared capability.

### Transition recommendation

Discovery is complete.

The platform now has enough evidence to establish a single baseline and authorize bounded survivability implementation slices.

PRR remains blocked pending restore certification and secrets/configuration recovery certification.

---

## 2. Governing Authority

Authority is applied in the following precedence order:

1. Wave 3 Formal Closeout
2. BCSS Release 2 Master Execution Plan
3. Platform Constitutional Standards
4. Repository evidence
5. Runtime evidence
6. Discovery evidence
7. Live health evidence
8. Supervisor logs
9. Existing recovery documentation
10. Existing deployment documentation

### Governing artifacts reviewed

- `/app/memory/BCSS_RELEASE2_PROGRAM2_WAVE3_MASTER_EXECUTION_PLAN.md`
- `/app/memory/PRD.md`
- `/app/docs/recovery/DEPLOYMENT_ROLLBACK_RUNBOOK.md`
- `/app/docs/recovery/LIVE_VS_RECOVERY_RECONCILIATION.md`
- Repository code evidence listed in Section 24
- Runtime endpoint evidence listed in Section 24
- Supervisor backend logs listed in Section 24

Precedence rule:

**Repository and runtime evidence always override documentation. Historical documentation may remain as historical evidence but never overrides current verified findings.**

---

## 3. Scope

### Included

- Backup and restore configuration discovery
- Database persistence and recovery mechanism discovery
- Object/file storage and retention discovery
- Scheduler, worker, and queue inventory
- Monitoring and health endpoint discovery
- Notification routing and retry-behavior discovery
- Authentication continuity and emergency-access discovery
- Secrets/configuration recovery discovery
- Deployment topology discovery
- Recovery scripts and operational tooling discovery

### Excluded

- Backend code implementation
- Frontend code implementation
- Infrastructure change
- Deployment change
- Provider change
- Scheduler or queue modification
- Backup execution
- Restore execution
- Secrets rotation
- Runtime configuration updates
- Cloud resource creation

### Discovery-only boundaries

- Read-only review only
- No implementation performed
- No runtime behavior modified
- No infrastructure modified
- No provider state modified

---

## 4. Repository and Runtime Topology

| Component | Purpose | Provider | Persistence | Failure Impact | Owner |
|---|---|---|---|---|---|
| React Frontend | Operator and admin web surface | React SPA | Stateless app bundle | Users lose interactive access | Frontend platform |
| FastAPI Backend | API, schedulers, auth, recovery tooling | FastAPI / Python | Runtime process + Mongo + R2 integrations | Core platform unavailable | Backend platform |
| MongoDB Database | Canonical durable system of record | MongoDB Atlas | Durable database collections | Data access and recovery coordination fail | Backend/data platform |
| Object/File Storage | Photos, documents, backup archives, signed retrieval | Cloudflare R2 via S3-compatible client | Durable bucket objects | Attachments and archive access degrade/fail | Storage platform |
| Backup Runtime | Creates, tracks, and leases backup/restore jobs | In-process backend runtime | `backup_jobs`, `backup_health`, drift collections | Backup freshness and recoverability evidence degrade | Survivability/ops |
| Backup Verification | Validates archive-lineage health and emits reports | Backend module + notification delivery | `backup_health`, `backup_jobs`, R2 archive scan | Verification confidence degrades | Survivability/ops |
| Restore Tooling | Preview-safe and admin-driven restore paths | Python tooling + backend restore endpoint | Mongo collections + archive ZIP inputs | Recovery cannot be proven | Survivability/ops |
| Scheduler Locks | Singleton execution control for schedulers | Mongo-backed lock rows | `scheduler_locks` | Duplicate or missing scheduled work risk | Backend platform |
| Scheduler Runs | Historical scheduler execution ledger | Mongo-backed scheduler-run history | `scheduler_runs` | Reduced visibility into scheduler health | Backend platform |
| Asset Spine Scheduler | Daily asset-spine maintenance task | In-process scheduler | Scheduler logs / Mongo side-effects | Asset governance lag | Asset/ops |
| Transport Automation Schedulers | Operational automation and digest jobs | In-process schedulers | Scheduler logs / Mongo state | Transport operations lag | Transport platform |
| Authentication | JWT session auth plus legacy admin-token continuity path | Custom backend auth | `users`, `directory_sessions`, `session_activity` | Admin/operator continuity degraded | Identity/auth |
| Notifications | Email/provider delivery abstraction with preview capture | Resend + internal capture contract | `notification_capture_v1`, webhook events | Operators lose alerts/verification messaging | Notifications/ops |
| Monitoring / Health | Liveness, readiness, persistence and recovery posture surfaces | Backend endpoints + internal probes | Health collections / runtime state | Reduced failure detection confidence | Platform/ops |
| Deployment Governance | Readiness and deployment-decision evidence | Backend routes + scripts + docs | `deployment_decisions`, audit collections | Unsafe release / weak rollback posture | Platform/deploy |
| Recovery Documentation | Runbooks and reconciliation evidence | Markdown + JSON docs | Repository docs | Operator guidance drifts from reality | Platform governance |
| External AI Dependency | Non-core AI capability provider keys | Emergent/OpenAI/Anthropic/Google flags | Env/config only | AI features degrade; core survivability should remain separable | AI platform |
| Email Provider | Transactional provider contract | Resend | Provider state + webhook events | Alert/provider delivery evidence incomplete | Notifications |

### Runtime topology summary

- Frontend runtime URL observed via environment: preview external URL.
- Backend runtime served behind `/api` ingress path.
- Backend process managed by supervisor.
- Mongo target observed as Atlas SRV connection with preview database `masci_safety_preview`.
- Storage target observed as S3-compatible R2-backed bucket `masci-hub`.
- Scheduler model observed as in-process singleton-locked runtime tasks.
- No separate queue broker or external worker fleet was evidenced in this sweep.

---

## 5. Discovery Coverage

**10/10 survivability domains assessed.**

1. Backup and restore configuration
2. Database persistence and recovery mechanisms
3. Object/file storage and retention
4. Scheduler, worker, and queue inventory
5. Monitoring and health endpoints
6. Notification routing and retry behavior
7. Authentication continuity and emergency access
8. Secrets/configuration recovery
9. Deployment topology
10. Existing recovery scripts and operational tooling

---

## 6. Capability State Matrix

| Capability | Capability State | Evidence State | Last Exercised | Classification |
|---|---|---|---|---|
| Database Backup | Present | Recent successful `complete-r2` backup recorded in runtime ledgers and health signals | 2026-07-25T23:13:00+00:00 | VERIFIED |
| Backup Freshness Health Signal | Present | `/api/health/full` returned `backup_recent=true` | 2026-07-26 | VERIFIED |
| Database Persistence | Present | `/api/ready` and runtime database authority show live connected Atlas-backed persistence | 2026-07-26 | VERIFIED |
| Object Storage / Archive Persistence | Present | R2-backed archive lineage, inventory, and successful archive upload evidenced | 2026-07-25T23:12:59+00:00 | VERIFIED |
| Scheduler Locking and Runtime Liveness | Present | Supervisor logs show singleton locks acquired and scheduler activity running | 2026-07-26 | VERIFIED |
| Health / Readiness Endpoints | Present | `/api/health`, `/api/healthz`, `/api/ready`, `/api/health/full` all healthy | 2026-07-26 | VERIFIED |
| Backup Verification Route Family | Present | Repository routes exist; state/preview/run-now endpoints identified but not exercised in this sweep | Not exercised in this sweep | CONFIGURED BUT UNVERIFIED |
| Notification Provider Delivery | Partial / environment-specific | Preview capture contract exists; live provider acceptance not proven here | Preview capture observed 2026-07-24 | CONFIGURED BUT UNVERIFIED |
| Authentication Continuity | Present | JWT plus legacy admin continuity path exists in repository; emergency continuity not exercised | No current exercise evidence | CONFIGURED BUT UNVERIFIED |
| Deployment Rollback Continuity | Present | Runbook and readiness/deployment evidence exist; rollback outcome not exercised here | No current exercise evidence | CONFIGURED BUT UNVERIFIED |
| Restore Drill Capability | Present | Latest recorded restore drill ended in failed outcome | 2026-05-31 | EXERCISED BUT FAILED |
| Deep Archive Verification Confidence | Present | Verification logic exists, but current manifest-read timeouts degrade exercised confidence | 2026-07-26 log observation | EXERCISED BUT FAILED |
| Secrets / Configuration Recovery | Unknown / unproven | No exercised proof found | None | NOT YET EXERCISED |
| Current End-to-End Recovery Certification | Present in tooling only | No current successful full recovery proof found | None current | NOT YET EXERCISED |

---

## 7. Discovery Findings

### Finding 1 — Restore classification downgraded

Latest restore drill failed.

Therefore restore is:

**EXERCISED BUT FAILED**

**NOT CURRENTLY VERIFIED**

Why:

- `drill_runs` contains a recorded restore drill with outcome `failed`.
- The drill showed negative proof on photo-reference reconciliation and coverage-gap criteria.
- Repository restore tooling existence is not enough to claim verified recoverability.

### Finding 2 — Notification classification narrowed

Preview SAFE_CAPTURE verified.

Live provider delivery remains unverified.

Why:

- `lib/notification_delivery.py` forces preview/test environments to `SAFE_CAPTURE` mode.
- `notification_capture_v1` contains captured preview notification evidence for backup verification.
- This proves preview capture workflow only; it does not prove live provider acceptance, delivery, retries, or escalations.

### Finding 3 — Backup verification endpoint corrected

Actual endpoints:

- Preview: `/api/admin/backup-verification/preview`
- Run-now: `/api/admin/backup-verification/run-now`
- State: `/api/admin/backup-verification/state`

Base path drift recorded:

- Base path `/api/admin/backup-verification` returned 404 in live read-only checking.
- The route family exists, but the valid paths are the sub-routes above.

---

## 8. Proof Posture

Capability totals preserved exactly:

- **VERIFIED: 6**
- **CONFIGURED BUT UNVERIFIED: 4**
- **EXERCISED BUT FAILED: 2**
- **NOT YET EXERCISED: 2**

These totals are discovery-baseline counts and shall not be silently modified without new evidence.

---

## 9. Survivability Domains

### 9.1 Backup and Restore Configuration

**Current capability**

- Backup runtime is present and active.
- Restore tooling is present.

**Evidence**

- Recent `complete-r2` backup job completed successfully.
- Backup scheduler logs show active runtime.
- Restore tooling exists in repository and restore endpoint logic exists.
- Latest restore drill failed.

**Risk**

- Backups are better evidenced than restores.

**Gaps**

- No current passing restore certification.

**Next implementation objective**

- Restore certification and reproducible exercised recovery proof.

### 9.2 Database Persistence and Recovery Mechanisms

**Current capability**

- Atlas-backed durable Mongo persistence is present.

**Evidence**

- `/api/ready` returned `mongo_ok=true`.
- Runtime environment points to Atlas SRV and preview DB.
- Durable survivability collections are populated.

**Risk**

- Database persistence is live, but end-to-end recovery evidence remains weaker than write/read continuity evidence.

**Gaps**

- No current certified restore-to-service proof.

**Next implementation objective**

- Prove restore-to-service against current data shape.

### 9.3 Object/File Storage and Retention

**Current capability**

- Cloud object storage is present and used for photos/documents/archives.

**Evidence**

- `photo_storage.py` R2/S3 contract.
- Archive upload recorded in backup job lineage.
- `r2_inventory` populated.

**Risk**

- Storage access exists, but restore parity across referenced objects remains part of the broader restore-certification gap.

**Gaps**

- Full object-reference recovery certification remains incomplete.

**Next implementation objective**

- Certify archive-to-object-reference recoverability.

### 9.4 Scheduler, Worker, and Queue Inventory

**Current capability**

- In-process schedulers with singleton locking and scheduler-run evidence are present.

**Evidence**

- Supervisor logs show lock acquisition for backup, automation, digest, and reliability schedulers.
- `scheduler_runs` and `scheduler_locks` collections exist.

**Risk**

- Scheduler resilience appears runtime-coupled to backend pod/process behavior.

**Gaps**

- Separate worker-failover evidence not found.

**Next implementation objective**

- Certify scheduler resilience, restart behavior, and failure visibility.

### 9.5 Monitoring and Health Endpoints

**Current capability**

- Liveness, readiness, and deeper health surfaces exist.

**Evidence**

- `/api/health`, `/api/healthz`, `/api/ready`, `/api/health/full` all healthy.
- Persistence-health and recovery dashboard surfaces exist in repository.

**Risk**

- Monitoring is broad, but alert-certification is weaker than health-surface existence.

**Gaps**

- Monitoring-to-alert proof chain remains incomplete.

**Next implementation objective**

- Monitoring and alert certification.

### 9.6 Notification Routing and Retry Behavior

**Current capability**

- Notification abstraction exists with preview capture and provider-live path.

**Evidence**

- Preview capture rows exist in `notification_capture_v1`.
- Webhook events exist in `resend_webhook_events`.

**Risk**

- Live provider delivery, retries, and escalation are not proven in this environment sweep.

**Gaps**

- Provider acceptance proof is incomplete.
- Delivery confirmation chain is incomplete.

**Next implementation objective**

- Notification delivery certification.

### 9.7 Authentication Continuity and Emergency Access

**Current capability**

- JWT auth exists, plus legacy admin-token continuity path.

**Evidence**

- `auth.py` defines JWT/cookie auth.
- Server comments and auth boundaries preserve legacy admin-token coexistence.
- `users`, `directory_sessions`, `session_activity` collections are populated.

**Risk**

- Emergency or post-restore continuity is not proven.

**Gaps**

- No exercised auth-continuity recovery proof.

**Next implementation objective**

- Certify authentication continuity after restore and incident scenarios.

### 9.8 Secrets / Configuration Recovery

**Current capability**

- Configuration keys exist in environment and code consumes them.

**Evidence**

- `.env` keys are present for DB, storage, auth, email, AI, and scheduler settings.
- No exercised recovery evidence located.

**Risk**

- Major survivability blind spot if config/secret recovery is required after failure.

**Gaps**

- No exercised configuration/secret recovery proof.

**Next implementation objective**

- Secrets and configuration recovery certification.

### 9.9 Deployment Topology

**Current capability**

- Deployment governance, readiness, rollback documentation, and decision ledgers exist.

**Evidence**

- `deployment_decisions` collection populated.
- Deploy-readiness route exists.
- Rollback runbook exists and explicitly constrains rollback semantics.

**Risk**

- Rollback is not a full recovery substitute.

**Gaps**

- Automatic production rollback is not implemented.

**Next implementation objective**

- Keep deployment continuity subordinate to recovery certification.

### 9.10 Recovery Scripts and Operational Tooling

**Current capability**

- Recovery scripts, restore drills, and recovery dashboards exist.

**Evidence**

- `backend/tools/restore_drill.py`
- `scripts/restore_drill.py`
- recovery dashboard route and rollback runbook

**Risk**

- Tooling existence exceeds exercised recovery proof.

**Gaps**

- Tooling must be certified with current archives and current data shapes.

**Next implementation objective**

- Bind tooling to successful exercised recoverability evidence.

---

## 10. Data Protection Register

| Data Class | Examples | Durability Class | Survivability Classification |
|---|---|---|---|
| Mission-Critical Core Records | `daily_reports`, `incidents`, `inspections`, `employees`, `equipment_master`, `jobs_master` | Durable Mongo + archive lineage | Mission Critical |
| Audit and Trust Evidence | `audit_events`, `admin_audit`, `deployment_decisions`, `platform_audit`, `mfa_audit_events` | Durable Mongo + backup archive | Compliance |
| Operational Control State | `scheduler_runs`, `scheduler_locks`, `backup_jobs`, `backup_health`, `backup_drift_history` | Durable Mongo + runtime state | Operational |
| File/Object References | `job_photos`, `operational_attachments`, `safety_documents`, `promo_assets`, R2 references | Mongo refs + R2 objects | Recoverable |
| Auth and Session State | `users`, `directory_sessions`, `session_activity`, login/session metadata | Durable Mongo, time-sensitive continuity class | Operational |
| Notification Evidence | `notification_capture_v1`, `resend_webhook_events`, routing audits | Durable Mongo/provider evidence | Operational |
| Temporary / Runtime Ephemera | temp uploads, caches, local spool files, transient process state | Pod-local / TTL / temporary paths | Temporary |

---

## 11. Backup Register

### Schedules

- Backup scheduler armed in runtime logs.
- Runtime log evidence shows scheduled hours at **02:00** and **18:00 UTC** for the local scheduler loop.
- Backup verification weekly scheduler exists by repository contract.

### Archives

- Latest successful complete archive observed:
  - `backups/auto-90d/MASCI_complete_backup_2026-07-25_230328Z.zip`
- Archive size observed: ~1.91 GB.

### Retention

- Archive pathing indicates `auto-90d` retention family.
- Backup-job TTL set to 120 days for backup runtime metadata.
- Retention behavior exists in code, but full retention certification was not executed here.

### Integrity

- Archive lineage contains checksum and manifest identity fields.
- `backup_integrity_jobs` collection exists with integrity-result fields.

### Verification

- Backup verification report builder exists.
- Admin verification routes exist at `/preview`, `/run-now`, and `/state`.

### Limitations

- Current logs show repeated manifest-read timeouts during verification.
- Backup evidence exceeds restore evidence.

---

## 12. Restore Register

Current restore capability is **NOT VERIFIED**.

Latest drill failed.

Recovery tooling exists.

Operational recovery remains to be proven.

### Evidence

- Preview-safe restore drill script exists with environment guardrails.
- Admin restore endpoint exists with backup-job leasing and overlap protection.
- `drill_runs` contains failed restore-drill evidence.

### Posture

- Tooling: present
- Safety guardrails: present
- Latest exercise outcome: failed
- Current certification state: not established

### Limitations

- Do not inflate restore posture from tooling presence.
- No current successful end-to-end restore proof was found in this sweep.

---

## 13. Notification Register

### Preview capture

- Verified.
- `notification_capture_v1` contains captured backup-verification notification evidence.
- Preview mode is forced to `SAFE_CAPTURE` by contract.

### Provider acceptance

- Not verified in this sweep.
- Repository live-provider path exists.

### Delivery confirmation

- Historical webhook evidence exists in `resend_webhook_events`.
- Current survivability baseline does not treat this as proof of current end-to-end alert certification.

### Retries

- Retryable/permanent states are modeled in notification contract.
- Current exercised retry evidence was not established in this sweep.

### Escalation

- Routing and capture models exist.
- End-to-end escalation certification remains unverified.

### Dead-letter handling

- Dead-letter email configuration surface exists by env contract.
- Exercised dead-letter certification not found.

---

## 14. Monitoring Register

| Monitoring Area | Current Evidence | State | Gaps |
|---|---|---|---|
| Health | `/api/health`, `/api/healthz` healthy | Present and exercised | None material |
| Ready | `/api/ready` healthy | Present and exercised | None material |
| Persistence | Admin persistence-health route exists | Present | Not exercised in this sweep |
| Backup | `/api/health/full` shows backup recent | Present and exercised | Deeper verification confidence gap |
| Scheduler | Logs + scheduler collections | Present and exercised | Formal resilience certification absent |
| Worker | In-process scheduler workers visible in logs | Present | No separate worker-fleet proof |
| Notification | Capture and webhook evidence | Partial | Live provider certification absent |
| Audit | Audit collections populated | Present | Recovery of audit trail not yet certified |
| Deployment | Deploy-readiness route and decision ledger | Present | Rollback != recovery proof |
| Recovery | Recovery dashboard and restore tooling | Present | Restore not verified |
| Alerting | Outage/notification surfaces exist | Partial | Alert chain certification absent |

---

## 15. Scheduler and Worker Register

### Inventory

- Backup scheduler
- Backup verification scheduler
- Asset spine scheduler
- Transport automation scheduler
- Transport command digest scheduler
- Motive reliability events/assets/users/geofences schedulers

### Locks

- Mongo-backed singleton-lock behavior observed in supervisor logs.

### Workers

- No independent worker fleet evidenced.
- Current model appears in-process under backend runtime.

### Restart behavior

- Scheduler state and backup freshness logic explicitly account for restart conditions.
- Log evidence shows boot-time scheduler arming and state seeding.

### Failure visibility

- Scheduler runs and logs provide visibility.
- Health surfaces and backup state surfaces add additional visibility.

### Retry

- Some retry and dedup semantics exist in scheduler/notification/storage contracts.
- Complete resilience certification remains pending.

### Idempotency

- Slot-claiming and singleton-lock design provide idempotency controls.
- Restore/backup overlap controls exist in backup runtime.

---

## 16. Authentication Continuity

### Current mechanisms

- JWT access + refresh token model
- Cookie and Bearer-token support
- Legacy admin-token coexistence path preserved during migration window

### Emergency continuity evidence

- Continuity path exists in repository design.
- No exercised emergency auth continuity evidence found in this sweep.

### Tenant continuity

- Seed-user and environment-aware auth wiring exists.
- No tenant-specific survivability certification performed here.

### Current limitations

- Post-restore auth continuity is not currently certified.
- Secrets/config recovery gap directly affects auth survivability confidence.

---

## 17. Disaster Scenario Register

| Scenario | Detection | Containment | Recovery | Current Evidence | Risk |
|---|---|---|---|---|---|
| Backend process restart | Health/ready/log signals | Supervisor-managed restart | Runtime resumes; scheduler re-arms | Verified runtime/log evidence | S2 |
| Recent backup loss concern | Health/full + backup ledgers | Backup scheduler state and archive lineage | Restore needed to complete proof | Backup evidence strong, restore weak | S1 |
| Archive verification degradation | Verification logs | Warning surfaces and logs | Hardening required | Current manifest-read timeouts observed | S2 |
| Mongo outage / persistence failure | Ready/ping/persistence surfaces | N/A in this sweep | Recovery not exercised here | Persistence healthy, outage recovery unproven | S2 |
| Object-storage access issue | Storage health/probes/logs | Fallback patterns exist in some paths | Full recovery not certified | Partial evidence only | S2 |
| Notification transport failure | Capture/provider/webhook evidence | Contracted statuses exist | End-to-end retry/escalation not certified | Partial | S2 |
| Secrets/config loss | No exercised evidence | N/A | No certified recovery path evidenced | Unproven | S1 |
| Full platform restore after major failure | Restore tooling and archives exist | Overlap protection exists | Current operational recovery unproven | Latest drill failed | S1 |

---

## 18. RTO / RPO Baseline

Never present draft values as commitments.

Current backup evidence exceeds restore evidence.

### RPO

**Target**

- Draft candidate only: conservative baseline target ≤24h until formal adoption.

**Current demonstrated capability**

- Backup freshness evidence materially exceeds the conservative target in the observed runtime.
- Latest successful backup completed on 2026-07-25T23:13:00+00:00.

**Evidence gap**

- Uniform certified recovery-point proof across all durable classes remains incomplete because restore proof is weaker than backup proof.

### RTO

**Target**

- TBD. No formal commitment is established by this discovery baseline.

**Current demonstrated capability**

- Historical restore drill runtime exists, but the latest drill failed and therefore does not qualify as a demonstrated recoverability commitment.

**Evidence gap**

- No current successful end-to-end restore-to-service certification.

---

## 19. Risk Register

### S0

- None evidenced in this sweep.

### S1

- Restore certification not established.
- Secrets/configuration recovery certification not established.

### S2

- Backup verification manifest-read timeouts reduce deep verification confidence.
- Notification provider delivery/retry/escalation evidence is partial.
- Scheduler resilience is not fully certified beyond current runtime behavior.
- Rollback continuity is narrower than full recovery continuity.

### S3

- Documentation/runtime drift risk on some operational paths.
- Proof fragmentation across multiple surfaces.

### S4

- Canonical survivability baseline had not existed before this artifact.

---

## 20. Survivability Gap Register

| Identifier | Description | Severity | Owner | Evidence | Implementation Recommendation | Dependency |
|---|---|---|---|---|---|---|
| SVG-01 | Restore capability not currently verified | S1 | Survivability / backend ops | Latest drill failed in `drill_runs` | Certify restore against current archive/data shape | Existing restore tooling |
| SVG-02 | Secrets/config recovery unproven | S1 | Platform / deploy / security ops | No exercised proof found | Create and certify secrets/config recovery path | Environment/config governance |
| SVG-03 | Backup verification deep-inspection confidence reduced | S2 | Survivability / storage ops | Manifest-read timeouts in logs | Harden verification depth and timeout handling | Backup verification route family |
| SVG-04 | Notification live-delivery certification incomplete | S2 | Notifications / ops | Preview safe-capture only verified | Certify provider acceptance, delivery, retries, escalation | Provider-routing contract |
| SVG-05 | Scheduler resilience not fully certified | S2 | Backend platform | Scheduler evidence exists but resilience exercise absent | Certify restart/failover/lock behavior | Scheduler lock model |
| SVG-06 | Monitoring-to-alert chain not certified | S2 | Platform ops | Monitoring surfaces broader than alert proof | Certify alert path end-to-end | Monitoring + notifications |
| SVG-07 | Disaster-recovery exercise program incomplete | S2 | Survivability program | Partial historical drills only | Run bounded DR exercise set | Restore + notification + auth continuity |

---

## 21. Survivability Implementation Queue

Sequence rule:

- Recoverability first.
- Evidence second.
- Optimization last.

### Slice 1 — Restore Certification

- **Scope:** certify end-to-end restore against current backup format, current durable classes, and current service continuity expectations.
- **Out of scope:** retention redesign, storage-provider replacement, deployment redesign.
- **Owner:** Survivability / backend ops.
- **Acceptance criteria:** successful restore exercise; current archive parsed correctly; critical data classes restored; service continuity validated; evidence captured.
- **Verification:** repository tests, runtime evidence, logged restore proof, artifact evidence.
- **Independent QA:** required.
- **Formal adoption:** required.

### Slice 2 — Secrets and Configuration Recovery

- **Scope:** define, implement, and certify secrets/config restoration posture.
- **Out of scope:** provider migration, credential rotation strategy redesign beyond survivability minimum.
- **Owner:** Platform / deploy / security ops.
- **Acceptance criteria:** controlled recovery procedure exists and is exercised.
- **Verification:** evidence-backed recovery walkthrough and runtime validation.
- **Independent QA:** required.
- **Formal adoption:** required.

### Slice 3 — Backup Verification Hardening

- **Scope:** increase verification depth and reduce archive-manifest uncertainty.
- **Out of scope:** backup architecture replacement.
- **Owner:** Survivability / storage ops.
- **Acceptance criteria:** verification route family yields reliable archive-depth evidence; timeouts controlled; classifications truthful.
- **Verification:** route evidence, log evidence, archive evidence.
- **Independent QA:** required.
- **Formal adoption:** required.

### Slice 4 — Notification Delivery Certification

- **Scope:** certify provider acceptance, delivery confirmation, retries, escalation, and dead-letter posture.
- **Out of scope:** notification feature expansion.
- **Owner:** Notifications / ops.
- **Acceptance criteria:** each evidence class proven separately.
- **Verification:** capture, provider, webhook, and escalation evidence.
- **Independent QA:** required.
- **Formal adoption:** required.

### Slice 5 — Scheduler Resilience

- **Scope:** certify lock behavior, restart behavior, retry/idempotency, and failure visibility.
- **Out of scope:** major scheduler architecture rewrite.
- **Owner:** Backend platform.
- **Acceptance criteria:** bounded resilience scenarios exercised successfully.
- **Verification:** logs, scheduler ledgers, health evidence.
- **Independent QA:** required.
- **Formal adoption:** required.

### Slice 6 — Monitoring and Alert Certification

- **Scope:** connect health/persistence/backup/scheduler/recovery signals to trustworthy alert evidence.
- **Out of scope:** full observability-platform replacement.
- **Owner:** Platform ops.
- **Acceptance criteria:** monitored failure classes raise truthful, auditable alerts.
- **Verification:** end-to-end signal-to-alert proof.
- **Independent QA:** required.
- **Formal adoption:** required.

### Slice 7 — Disaster Recovery Exercises

- **Scope:** bounded scenario exercises for major failure classes.
- **Out of scope:** production deployment authorization itself.
- **Owner:** Survivability program.
- **Acceptance criteria:** scenarios exercised with evidence and residual-risk classification.
- **Verification:** exercise records and outcome evidence.
- **Independent QA:** required.
- **Formal adoption:** required.

### Slice 8 — Survivability Closeout

- **Scope:** reconcile all survivability slices into one closeout decision.
- **Out of scope:** PRR or deployment approval bypass.
- **Owner:** Survivability program governance.
- **Acceptance criteria:** gap register reconciled; PRR blockers formally re-evaluated.
- **Verification:** evidence review and formal closeout artifact.
- **Independent QA:** required.
- **Formal adoption:** required.

---

## 22. PRR Blocking Assessment

Current PRR blockers:

1. Restore certification
2. Secrets/configuration recovery certification

Lower-priority survivability items are not elevated to PRR blockers here without stronger evidence.

---

## 23. Executive Recommendation

- Discovery complete.
- Baseline established.
- Implementation authorized.
- PRR remains blocked.
- Deployment remains blocked.

This baseline now governs all future Platform Survivability implementation work.

---

## 24. Evidence Ledger

### Exact files reviewed

- `/app/memory/PRD.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_WAVE3_MASTER_EXECUTION_PLAN.md`
- `/app/backend/backup_verification.py`
- `/app/backend/lib/backup_runtime.py`
- `/app/backend/lib/scheduler_bootstrap.py`
- `/app/backend/photo_storage.py`
- `/app/backend/auth.py`
- `/app/backend/routes/health_routes.py`
- `/app/backend/routes/backup_verification_routes.py`
- `/app/backend/routes/recovery_dashboard.py`
- `/app/backend/routes/admin_persistence_health.py`
- `/app/backend/routes/deploy_readiness.py`
- `/app/backend/services/operations_control/backups.py`
- `/app/backend/services/operations_control/queues.py`
- `/app/backend/services/operations_control/storage.py`
- `/app/backend/services/operations_control/health.py`
- `/app/backend/lib/database_authority.py`
- `/app/backend/lib/notification_delivery.py`
- `/app/backend/tools/restore_drill.py`
- `/app/backend/server.py`
- `/app/docs/recovery/DEPLOYMENT_ROLLBACK_RUNBOOK.md`
- `/app/docs/recovery/LIVE_VS_RECOVERY_RECONCILIATION.md`

### Runtime evidence reviewed

- `/api/health`
- `/api/healthz`
- `/api/ready`
- `/api/health/full`
- `/api/admin/system-health` (auth boundary observed)
- `/api/admin/backup-verification` (base path drift observed)

### Supervisor logs reviewed

- `/var/log/supervisor/backend.err.log`
- `/var/log/supervisor/backend.out.log`

### Mongo/runtime evidence reviewed

- `backup_jobs`
- `backup_health`
- `backup_integrity_jobs`
- `audit_events`
- `admin_audit`
- `scheduler_runs`
- `scheduler_locks`
- `users`
- `directory_sessions`
- `session_activity`
- `deployment_decisions`
- `drill_runs`
- `notification_capture_v1`
- `resend_webhook_events`
- `r2_inventory`
- `backup_drift_history`

---

## 25. Required Consistency Checks

- Discovery coverage still equals **10/10**: PASS
- Capability totals remain **Verified 6 / Configured but unverified 4 / Exercised but failed 2 / Not yet exercised 2**: PASS
- Three corrected findings remain preserved exactly: PASS
- No runtime files modified: PASS
- No infrastructure modified: PASS
- One canonical artifact created: PASS
- No competing survivability plans exist in `/app/memory`: PASS at time of adoption

---

## 26. Final Baseline Determination

This document is the single source of truth for BCSS Release 2 Platform Survivability planning.

It answers the governing question truthfully as of this baseline date:

**If the platform experiences a major failure today, backup evidence suggests recoverable data exists, but full recovery cannot yet be claimed as proven because restore certification and secrets/configuration recovery certification are still incomplete.**
