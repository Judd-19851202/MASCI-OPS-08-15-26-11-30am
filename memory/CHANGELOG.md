# Change Log

## 2026-07-28 — MASCI OPS OPPC WP-OPPC-11 through WP-OPPC-13 closeout

- Completed `WP-OPPC-11` by extending the canonical schedule engine with deterministic forecasting, scenario comparison, critical-path hardening, forecast snapshots, and audited override governance.
- Completed `WP-OPPC-12` by adding a shared production confidence engine, project-health exposure, ODS rollups, confidence history persistence, and Trust Spine-backed snapshot evidence.
- Completed `WP-OPPC-13` by adding project + enterprise Monday Morning Briefings with approval/freeze lifecycle, PDF export, and canonical evidence composition.
- Added closeout evidence artifacts:
  - `/app/memory/OPPC_FORECASTING_CRITICAL_PATH_CERTIFICATION.md`
  - `/app/memory/OPPC_PRODUCTION_CONFIDENCE_SCORE_CERTIFICATION.md`
  - `/app/memory/OPPC_MONDAY_MORNING_BRIEFING_CERTIFICATION.md`
  - `/app/memory/OPPC_WP11_REGRESSION_GATE.md`
  - `/app/memory/OPPC_WP12_REGRESSION_GATE.md`
  - `/app/memory/OPPC_WP13_REGRESSION_GATE.md`
  - `/app/memory/OPPC_PERFORMANCE_SCALABILITY_VALIDATION.md`
  - `/app/memory/OPPC_SURVIVABILITY_VALIDATION.md`
  - `/app/memory/OPPC_EXECUTIVE_ARCHITECTURE_CLOSEOUT.md`
  - `/app/memory/OPPC_END_TO_END_PREVIEW_CERTIFICATION.md`
- Final verification evidence:
  - `/app/test_reports/iteration_66.json`
  - `/app/test_reports/iteration_67.json`
  - `/app/test_reports/iteration_68.json`
  - final frontend certification rerun: all required OPPC preview panels verified

## 2026-07-28 — OPPC Operational Go-Live Release Gate (24-06)

- Fixed live shared-route auth scoping in `/app/frontend/src/lib/portalAuthScope.js`, restoring registry persistence and PM/shared operational UI flows for `/cost-codes/*`, `/oppc/*`, and `/ods/*`.
- Fixed frozen-briefing admin regeneration in `/app/backend/routes/oppc_execution.py`, allowing project + enterprise Monday briefings to refresh after new operational data while preserving approval/freeze audit history.
- Executed the user-mandated operational gate on project `24-06` with live UI + backend evidence: registry create/persist, assignment save, schedule save, weekly rollover, forecast governance, live daily report `DR-2026-03558`, project health confidence refresh, Trust Spine validation, and project + enterprise Monday briefing refresh.
- Added release-gate evidence file: `/app/memory/OPPC_OPERATIONAL_READINESS_GATE_24-06.md`

## 2026-07-28 — MASCI OPS OPPC WP-OPPC-08 through WP-OPPC-10

- Added one canonical enterprise operational intelligence service at `/app/backend/services/cost_codes/oppc_intelligence.py` for variance intelligence, recovery intelligence, and enterprise resource coordination.
- Extended `/api/oppc/*` with stable canonical APIs for project variance intelligence, variance review updates, enterprise resource coordination, and executive operations center.
- Embedded `variance_intelligence` into the existing OPPC execution workspace and extended PM + Executive UIs to consume canonical APIs.
- Added certification reports:
  - `/app/memory/OPPC_VARIANCE_INTELLIGENCE_CERTIFICATION.md`
  - `/app/memory/OPPC_RECOVERY_INTELLIGENCE_CERTIFICATION.md`
  - `/app/memory/OPPC_ENTERPRISE_RESOURCE_COORDINATION.md`
  - `/app/memory/OPPC_OPERATIONAL_TIMELINE.md`
  - `/app/memory/OPPC_EXECUTIVE_OPERATIONS_CENTER.md`
- Fixed testing-agent finding by routing `ExecutiveOperationalIntelligence` in `AppRoutes.jsx`.

## 2026-07-28 — MASCI OPS OPPC WP-OPPC-05 through WP-OPPC-07 certification closeout

- Added the five required repository-backed evidence artifacts:
  - `/app/memory/OPPC_DAILY_PRODUCTION_CERTIFICATION.md`
  - `/app/memory/OPPC_PAYROLL_RECONCILIATION_CERTIFICATION.md`
  - `/app/memory/OPPC_MONDAY_LOOK_BEHIND_CERTIFICATION.md`
  - `/app/memory/OPPC_OPERATIONAL_EXECUTION_REPORT.md`
  - `/app/memory/OPPC_WEEKLY_REVIEW_WORKFLOW.md`
- Verified the evidence against existing canonical owners: Daily Reports, Payroll Variance, OPPC execution workspace, Tasks, and Trust Spine.
- Recorded readiness declaration for continuation into `WP-OPPC-08` without introducing any parallel schedule, variance, review, or recovery engines.

## 2026-07-28 — MASCI OPS OPPC WP-OPPC-01 through WP-OPPC-04 foundation

- Completed `WP-OPPC-01` canonical architecture inventory with four repository-backed memory artifacts covering architecture inventory, gap register, canonical data ownership, and Trust Spine event mapping.
- Completed `WP-OPPC-02` bounded cost-code foundation hardening inside the existing owner path (`jobs_master.assigned_cost_codes`) with aggregated `planning_readiness`, assignment-level readiness, and Trust Spine workflow `oppc-cost-code-plan`.
- Completed `WP-OPPC-03` rolling two-week planning lifecycle extension with publish-state tracking (`unconfigured`, `needs_attention`, `ready_to_publish`, `published`) and PM schedule UI lifecycle cards/actions.
- Started `WP-OPPC-04` with bounded weekly rollover preview/apply flows on the canonical cost-code route family and Trust Spine workflow `oppc-weekly-rollover`.
- Verification evidence:
  - local focused regression: `11 passed`
  - independent verification report: `/app/test_reports/iteration_63.json`

## 2026-07-27 — BCSS Release 2 S1-4 Notification Delivery Certification (implementation + blocker verification)

- Implemented a bounded Preview-only notification certification lane in `/app/backend/lib/preview_notification_certification.py`, preserving `SAFE_CAPTURE` globally while allowing only one scoped certification send path for `jaymn.judd@mascigc.com`.
- Wired the scoped override through `/app/backend/server.py`, `/app/backend/lib/notification_delivery.py`, `/app/backend/routes/resend_webhook.py`, and `/app/backend/routes/daily_reports.py`, including preserved original-intended recipients, workflow dispatch events, trust-spine continuity, routing audit truth, and operator-status notifications.
- Executed the authoritative Preview certification run `s1-4-cert-e217a5ffd8` / `DR-2026-03557`; the system correctly activated `PROVIDER_LIVE`, attempted provider submission, and failed truthfully with `API key is invalid`.
- Independent verification passed in `/app/test_reports/iteration_50.json`; S1-4 remains blocked only by the invalid external `RESEND_API_KEY`, not by the scoped override implementation.

## 2026-07-27 — BCSS Release 2 S1-2 + S1-3 Preview Certification

- Completed **S1-2 Secrets & Configuration Recovery Certification** with a canonical recovery package in `/app/backend/lib/config_recovery.py`, a new admin endpoint at `/api/admin/recovery/configuration-recovery`, fail-closed Preview/Production separation checks, and the operator runbook at `/app/memory/S1_2_CONFIGURATION_RECOVERY_RUNBOOK.md`.
- Completed **S1-3 Backup Verification Hardening** in `/app/backend/lib/archive_lineage.py`, requiring direct manifest sidecar + checksum sidecar + persisted lineage reconciliation before granting `lineage_confidence=HIGH`.
- Triggered and verified a fresh Preview backup: `MASCI_complete_backup_2026-07-27_111254Z.zip` under `backups/preview/auto-90d/`, with `direct_evidence_status=VERIFIED`, `direct_evidence_read_mode=SIDECAR`, and `valid_recoverable=true`.
- Restored `/api/health/full` compatibility while keeping the richer lineage-backed diagnostics path intact.
- Verification evidence: local regression suite passed `49/49` relevant tests (`5 skipped`), and independent verification passed in `/app/test_reports/iteration_49.json`.

## 2026-07-27 — BCSS Release 2 TRACK D-02 Preview Certification

- Repaired Preview complete-R2 archive construction in `/app/backend/server.py` by binding the archive key into the manifest build path and preserving `backup_run_id` on the live job lookup.
- Hardened preview archive-lineage truth selection in `/app/backend/lib/archive_lineage.py` so runtime identity uses the actual Mongo runtime host/user and no longer falsely quarantines valid Preview archives.
- Increased large-archive manifest probe budget in `/app/backend/backup_verification.py` and verified the latest Preview R2 archive manifest can be read end-to-end with `integrity_result=PASS` and `coverage_complete=true`.
- Executed a fresh Preview-only complete-R2 archive run: `MASCI_complete_backup_2026-07-27_021533Z.zip` uploaded successfully to `backups/auto-90d/`, surfaced as the authoritative recoverable artifact, and moved Preview RPO to `GREEN`.
- Verification evidence: targeted backend suite passed `12/12`, direct admin/API smoke verification passed, and independent backend verification passed `5/5` with consistent archive evidence across backup state, verification, and recovery snapshot endpoints.

## 2026-07-26 — Wave 3 Family 3C Operational Events Phase B

- Preserved bounded Family 3C ownership in `/app/backend/routes/operational_events.py` with `operational_events` as the canonical normalized store and no adjacent-family writes.
- Repaired the direct Family 3C admin auth contract to the current repository reality in tests and verification: admin routes require both `X-Admin-Token` and the bound `X-Directory-Token`.
- Added bounded Family 3C lifecycle evidence: materialization now writes append-only `audit_events` evidence with `kind=operational_events.materialize` and emits Trust Spine workflow `operational-events-materialization`.
- Hardened Family 3C query surfaces with explicit Mongo projections and a date-pushed dashboard aggregation while preserving public endpoint contracts.
- Verification evidence: local Family 3C suite passed `18/18`, independent verification passed in `/app/test_reports/iteration_43.json`, and direct PM Family 3C consumer smoke verification passed.

## 2026-07-25 — Wave 3 Family 3A Core Admin Operations Phase B

- Recorded the repository-backed Family 3 split: `3A Core Admin Operations`, `3B Operations Actions`, `3C Operational Events`, `3D Asset Mapping & Reconciliation`.
- Limited active implementation authority to Family 3A only.
- Applied bounded Family 3A contract fixes in the core admin operations route and direct consumers/tests only.

## 2026-07-25 — Wave 3 Family 3B Operations Actions Phase B

- Unified the Family 3B authentication contract to the secure runtime model: one acting portal token plus the bound `X-Directory-Token`.
- Repaired Family 3B consumers to use a dedicated OA client with explicit portal scoping and directory-session forwarding.
- Added bounded Trust Spine emission, richer history context, duplicate-assignment suppression, query reductions, owner-search parallelization, and photo-path rollback cleanup inside Family 3B only.
- Closed Phase B with bounded verification evidence: `42/42` Family 3B tests passed locally, independent verification passed in `/app/test_reports/iteration_42.json`, and final backend regression sweep passed `19/19`.
- Hardened the Family 3B auth gate further to reject multiple portal headers while preserving the required valid directory session pairing.
- Recorded Phase B latency evidence: list and owner-search improved in preview; summary remained shared-infrastructure dominated.