# BCSS Release 2 · Program 2 · Foundation · Checkpoint 4
## Truth Subject Inventory

This document derives constitutional authority from BCSS_RELEASE2_PROGRAM2_CHECKPOINT4_OPERATIONAL_TRUTH_SPINE.md and establishes no independent governance.

Date: 2026-07-25

---

## 1. Canonical BCSS Truth Subjects

| Canonical Name | Owner | Authoritative Evidence | Permitted Evidence | Forbidden Evidence | Evidence Quality Requirements | Confidence Inputs | Truth Evaluation Rules | Maximum Claim | Constitutional Boundaries | Repository Status | Future Migration |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `bcss_runtime_state_authority` | `/api/admin/platform/status` | runtime identity + DB authority payloads | runtime identity, database authority, platform status | trust scores, UI-only banners | `DIRECT_OBSERVED`, `VALIDATED` | runtime identity validity, DB authority state | environment + DB authority must match runtime truth | `VERIFIED` | may not certify recovery | canonical | Wave 2 surface registration convergence |
| `bcss_backup_slot_execution` | `/api/admin/scheduler-runs` | scheduler ledger + lock evidence | scheduler runs, scheduler locks | archive-only observations without scheduler evidence | `DURABLE_OBSERVED`, `VALIDATED` | heartbeat currency, lock currency | unique slot + completion truth only | `VERIFIED` | may not imply archive recoverability | canonical | Wave 1 vocabulary normalization |
| `bcss_backup_job_execution` | `/api/admin/backups-complete-r2-state` | backup_jobs + runtime state | job runtime, heartbeat, overlap evidence | trust score outputs | `DURABLE_OBSERVED`, `VALIDATED` | heartbeat failure, overlap state | job execution truth only | `VERIFIED` | may not imply certified recovery | canonical | Wave 1 vocabulary normalization |
| `bcss_backup_archive_lineage` | `/api/admin/backup-verification/state` + `archive_lineage.py` | backup_health, R2 metadata, manifests | archive, lineage, integrity, completeness, recoverable-point evidence | trust scores, deploy decisions | `DURABLE_OBSERVED`, `VALIDATED`, `ESTIMATED` where fallback is explicit | lineage confidence, integrity/completeness status | authoritative recoverable point must disclose source and degradation | `VERIFIED` | may not imply restore certification | canonical | Wave 3 claim binding |
| `bcss_restore_execution` | `/api/exports/restore` | restore audit + replay evidence | restore execution rows, manifest origin validation | archive presence alone | `EXERCISED`, `VALIDATED` | origin validation, replay results | bounded restore execution only | `VERIFIED` | may not imply full-platform recovery proof | canonical | Wave 3 claim binding |
| `bcss_restore_drill_evidence` | `/api/admin/recovery/snapshot` | drill_runs + restore drill evidence | representative drill evidence, archive linkage | scheduler evidence alone | `EXERCISED`, `DURABLE_OBSERVED` | drill freshness, records restored, outcome | representative scope only unless full-platform evidence exists | `VERIFIED` | may not imply certified recovery | canonical | Wave 3 claim binding |
| `bcss_recovery_posture` | `/api/admin/recovery/snapshot` | posture fan-in over registered BCSS inputs | upstream BCSS truths, capacity signals, warnings | deploy certification decisions as posture proof | `DERIVED` with upstream `VALIDATED` / `EXERCISED` inputs where available | archive confidence, drill freshness, scheduler posture | aggregator only; posture summary may not replace upstream owners | `CORRELATED` | not a certification owner | canonical | Wave 4 operator-surface adoption |
| `bcss_recovery_trust` | `/api/admin/backup-trust-score` | deterministic penalty model | trust score inputs, penalties, archive/drill freshness | direct certification language | `DERIVED` | trust score, score inputs, penalty model | confidence-only meaning | `CORRELATED` | may not verify or certify recovery | canonical | Wave 4 operator-surface adoption |
| `bcss_recovery_certification` | `/api/admin/deployment-readiness` | deployment findings, decisions, independent review artifacts | decision-recorded evidence, bounded certification evidence | trust scores, posture summaries, archive age alone | `DECISION_RECORDED`, `VALIDATED` | verification artifacts, decision record | current owner registration exists; BCSS class model absent | `CERTIFIED` for bounded deployment readiness only | not equivalent to recovery-class certification | canonical | Wave 7 recovery certification |
| `bcss_external_dependency_continuity` | `/api/admin/integrations/truth-status` | integration truth + delivery contract | configuration, connectivity, operational activity, runtime identity | config-only presence claimed as live continuity | `DIRECT_OBSERVED`, `DERIVED`, `VALIDATED` when live probes succeed | connectivity, recent activity, provider validation | dependency posture only | `CORRELATED` at surface level; bounded subclaims may be `VERIFIED` | not a certification owner | canonical | Wave 3 claim binding |

---

## 2. Adjacent Represented Truth Concepts

| Canonical Name | Owner | Authoritative Evidence | Permitted Evidence | Forbidden Evidence | Evidence Quality Requirements | Confidence Inputs | Truth Evaluation Rules | Maximum Claim | Constitutional Boundaries | Repository Status | Future Migration |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `platform_availability` | mapped to `bcss_runtime_state_authority` | `/api/health`, `/api/health/full`, `/api/version` | liveness, readiness, runtime identity, uptime | trust score outputs | `DIRECT_OBSERVED`, `DERIVED` | liveness + deep health consistency | availability is subordinate to runtime authority | `OBSERVED` to `CORRELATED` | do not create separate BCSS subject | adjacent / duplicate if declared separately | Wave 2 mapping only |
| `backup_integrity` | mapped to `bcss_backup_archive_lineage` | lineage + integrity outputs | integrity checks, completeness, archive metadata | trust scores, deploy decisions | `VALIDATED` | lineage confidence | subordinate evidence concept under archive lineage | `VERIFIED` | no standalone BCSS subject needed | adjacent | Wave 1 vocabulary convergence |
| `manifest_integrity` | mapped to `bcss_backup_archive_lineage` and `bcss_restore_execution` | manifests + restore origin validation | manifest reads, origin checks | UI summaries without manifest evidence | `VALIDATED` | manifest validation outcomes | subordinate evidence concept only | `VERIFIED` | no parallel manifest truth engine | adjacent | Wave 1 vocabulary convergence |
| `notification_delivery` | mapped to `bcss_external_dependency_continuity` plus trust-spine evidence | email routing audit, provider acceptance, preview capture | provider acceptance, safe-capture, routing audit | claiming delivery success from config only | `DIRECT_OBSERVED`, `DURABLE_OBSERVED`, `VALIDATED` where provider acceptance exists | provider acceptance vs preview capture path | remains BCSS-adjacent until explicitly bound | `OBSERVED` to `VERIFIED` | no standalone BCSS subject yet | missing as standalone BCSS mapping | Wave 2 mapping |
| `recovery_readiness` | composite over `bcss_recovery_posture` + `bcss_recovery_certification` | recovery snapshot + deployment readiness | posture evidence + bounded decision evidence | trust score alone, archive age alone | `DERIVED`, `VALIDATED`, `DECISION_RECORDED` | posture confidence + decision evidence | composite concept only | `CORRELATED` to bounded `CERTIFIED` | must not bypass posture / certification separation | adjacent composite | Wave 7 certification convergence |
| `operational_health` | composite over runtime, recovery, dependency, and OCC health surfaces | health endpoints + OCC health | liveness, deep health, recovery, dependency posture | single red/green claim without source drilldown | `DERIVED` | worst-status aggregation | composite only | `CORRELATED` | do not declare a new BCSS subject | duplicate if independently registered | Wave 8 platform convergence |

---

## 3. Inventory Rules

### [Constitutional (normative)] Non-duplication rule
Adjacent represented concepts shall be mapped back to existing canonical BCSS owners wherever repository evidence already supports that mapping.

### [Constitutional (normative)] Unknown rule
Where no standalone BCSS truth subject exists in the repository, the inventory shall explicitly state `adjacent`, `missing`, or `duplicate` rather than invent a new subject.
