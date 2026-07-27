# CANONICAL SURVIVABILITY CAPABILITY INVENTORY

Date: 2026-07-27  
Program: MASCI OPS — Platform Survivability Program  
Scope: Preview-only constitutional survivability validation  
Status: Complete and adopted for execution

---

## 1. Constitutional framing

This inventory records what already exists before declaring any survivability gap.

The repository already had a 10-domain survivability discovery baseline in:

- `/app/memory/BCSS_RELEASE2_PLATFORM_SURVIVABILITY_BASELINE_AND_DISCOVERY.md`

For execution, the Platform Survivability Program is normalized into **Domains A-L** so every failure injection, recovery observation, and governance decision can be recorded against one stable operational frame.

This inventory does **not** reopen Wave 3, does **not** begin PRR, and does **not** authorize new feature work.

---

## 2. Evidence sources used

### Repository evidence

- `backend/server.py:651-662` — directory-admin token validator
- `backend/server.py:928-983` — `require_admin_strict()` fail-closed admin gate
- `backend/session_timeout.py:352-384` — active session + directory-binding enforcement
- `backend/user_directory.py:478-523` — per-user admin token mint/validation
- `backend/lib/backup_runtime.py:109-279` — backup/restore job claiming, heartbeat, stale reclamation, overlap classification
- `backend/lib/scheduler_runs.py:97-240` — deterministic scheduler slot claim, duplicate prevention, completion/failure ledger
- `backend/lib/archive_lineage.py:714-873` — canonical archive-lineage resolution
- `backend/lib/config_recovery.py:638-689` — configuration recovery package + summary
- `backend/lib/trust_spine.py:192-281` — trust-stage emission and index management
- `backend/routes/recovery_dashboard.py:310-321, 340-347, 458-540` — configuration recovery + recovery snapshot + drill/scheduler aggregation
- `backend/routes/scheduler_runs_admin.py:24-97` — admin scheduler-run evidence surface
- `backend/routes/integration_truth.py` — external dependency continuity truth surface
- `backend/backup_verification.py:376-964` — verification report builder, scheduler, and email/report evidence
- `backend/tools/restore_drill.py` and `scripts/ops8_namespace_restore_drill.py` — bounded restore tooling

### Runtime evidence

- `/api/health` → 200
- `/api/healthz` → 200
- `/api/ready` → 200 with `mongo_ok=true`
- `/api/health/full` → 200 with `mongo=true`, `scheduler=true`, `backup_recent=true`
- `/api/admin/recovery/configuration-recovery` → 200
- `/api/admin/recovery/snapshot` → 200
- `/api/admin/backup-verification/preview` → 200
- `/api/admin/backup-verification/state` → 200
- `/api/admin/integrations/truth-status` → 200
- `/api/admin/trust-spine` → 200
- `/api/admin/scheduler-runs?limit=5` → 200

### Execution evidence created in this track

- `/app/memory/PLATFORM_SURVIVABILITY_EXECUTION_RAW.json`

---

## 3. Domain A-L inventory

| Domain | Survivability scope | Canonical subsystem(s) already present | Current state | Gap category | Canonical evidence |
|---|---|---|---|---|---|
| **A** | Runtime legitimacy and environment isolation | Runtime identity, DB authority, fail-closed preview/prod separation | **IMPLEMENTED** | None | `config_recovery.py`, `archive_lineage.py`, `/api/health`, `/api/ready` |
| **B** | Database durability and live continuity | Mongo Atlas connectivity, durable operational collections, readiness gates | **IMPLEMENTED** | None | `/api/health/full`, `/api/admin/integrations/truth-status`, `backup_health`, `scheduler_runs`, `trust_spine_events` |
| **C** | Backup/restore job leasing and overlap protection | Durable `backup_jobs`, lease ownership, heartbeat, stale reclamation | **IMPLEMENTED** | None | `backup_runtime.py:109-279`, `/api/admin/backups-complete-r2-state` |
| **D** | Archive lineage, integrity, and verification | Canonical archive-lineage resolver, verification state/preview routes | **IMPLEMENTED** | None | `archive_lineage.py:714-873`, `backup_verification.py`, `/api/admin/backup-verification/state` |
| **E** | Restore execution and drill evidence | Namespace restore drill, drill evidence ledger, recovery snapshot drill projection | **PARTIALLY IMPLEMENTED** | **EXTERNAL DEPENDENCY** | `test_restore_certification_s1_1.py`, `restore_drill.py`, `ops8_namespace_restore_drill.py`, `drill_runs`, `/api/admin/recovery/snapshot` |
| **F** | Configuration and secret recovery | Config recovery package, redaction, fail-closed blend detection, runbook projection | **IMPLEMENTED** | None | `config_recovery.py:638-689`, `/api/admin/recovery/configuration-recovery` |
| **G** | Scheduler/worker continuity | `scheduler_runs`, `scheduler_locks`, dedup, completion ledger, scheduler health aggregation | **IMPLEMENTED** | None | `scheduler_runs.py:97-240`, `/api/admin/scheduler-runs`, `/api/admin/recovery/snapshot` |
| **H** | Trust integrity and audit integrity | `trust_spine_events`, trust dashboard, audit collections, failed-stage visibility | **IMPLEMENTED** | None | `trust_spine.py:192-281`, `admin_trust_spine.py`, `/api/admin/trust-spine` |
| **I** | Authentication continuity and emergency admin access | Multi-login, directory session binding, per-user admin HMAC, active session enforcement | **IMPLEMENTED** | None | `user_directory.py:478-523`, `server.py:651-662, 928-983`, `session_timeout.py:352-384` |
| **J** | External dependency continuity awareness | Canonical integration truth, mocked/disabled/live distinction, provider continuity honesty | **IMPLEMENTED** | None | `/api/admin/integrations/truth-status`, `routes/integration_truth.py` |
| **K** | Monitoring, health, and detection | Health/readiness/full health, recovery posture, platform status, verification state | **IMPLEMENTED** | None | `/api/health*`, `/api/admin/platform/status`, `/api/admin/recovery/snapshot` |
| **L** | Governance, frozen evidence integrity, and regression protection | Wave 3 freeze artifacts, hash-based regression proof, single decision register | **IMPLEMENTED** | None | Wave 3 hashes in `/app/memory/PLATFORM_SURVIVABILITY_EXECUTION_RAW.json` |

---

## 4. Domain-by-domain findings

### Domain A — Runtime legitimacy and environment isolation

- Preview runtime remains pointed at `masci_safety_preview` and reports valid runtime identity.
- Configuration recovery logic fails closed on preview/production blend.
- No survivability defect was found in the environment authority path.

### Domain B — Database durability and live continuity

- Mongo continuity is live and reachable.
- Durable survivability collections are populated and queryable.
- The platform can still surface truthful posture while the database is healthy.

### Domain C — Backup/restore job leasing and overlap protection

- Backup jobs are durable, leased, heartbeat-aware, and stale-recoverable.
- Overlap classification already exists and blocks simultaneous backup/restore overlap from being misreported.

### Domain D — Archive lineage, integrity, and verification

- Canonical lineage selects only constitutionally acceptable artifacts.
- Checksum mismatch causes quarantine, not optimistic selection.
- Verification state truth remains intentionally limited to scheduler/config projection and honestly reports `UNVERIFIABLE` when appropriate.

### Domain E — Restore execution and drill evidence

- Restore tooling exists and namespace restore evidence exists.
- Latest live recovery snapshot reports a successful bounded drill with `duration_min=41.035`, `records=1902489`, `photos=3206`.
- Full automated side-database drill remains blocked by Atlas authorization outside restore-owned code. This is not a repository-critical survivability defect.

### Domain F — Configuration and secret recovery

- Configuration recovery package is live, redacted, and produces fail-closed validation.
- This domain moved from historical uncertainty to exercised evidence during this track.

### Domain G — Scheduler/worker continuity

- Scheduler slot claiming and duplicate suppression are implemented and evidenced.
- Admin scheduler-run route exposes operator-visible continuity evidence without direct DB access.

### Domain H — Trust integrity and audit integrity

- Trust Spine is capable of surfacing degraded and failed workflows honestly.
- Current live platform band is degraded/red because the endpoint is reporting actual workflow conditions, not because the subsystem is absent.

### Domain I — Authentication continuity and emergency admin access

- Admin continuity exists but requires the constitutional dual-token path when directory session binding is present.
- A single admin token without the matching directory session fails closed as designed.

### Domain J — External dependency continuity awareness

- Integration truth already distinguishes live, mocked, configured, disabled, and idle dependency states.
- Survivability capability exists even where provider-level success is environment-bounded.

### Domain K — Monitoring, health, and detection

- Health and readiness surfaces remained green before and after every preview-only failure injection.
- Recovery posture and integration truth remain queryable through the entire sequence.

### Domain L — Governance, frozen evidence integrity, and regression protection

- Wave 3 frozen artifacts remained byte-for-byte unchanged across all failure injections.
- No historical evidence rewrite occurred during this track.

---

## 5. Canonical gaps after proof-first review

Only one survivability area remains below full implementation closure:

| Domain | Area | Constitutional conclusion |
|---|---|---|
| **E** | Fully automated side-database restore certification | **PARTIALLY IMPLEMENTED / EXTERNAL DEPENDENCY** — the side-DB path is blocked by Atlas authorization outside restore-owned repository logic. Namespace-scoped restore evidence exists and remains valid. |

No **TRUE IMPLEMENTATION GAP** and no unresolved **repository-critical survivability defect** were identified in this execution pass.

---

## 6. Inventory adoption decision

This inventory is the canonical survivability capability baseline for the remainder of the Platform Survivability Program execution in Preview.
