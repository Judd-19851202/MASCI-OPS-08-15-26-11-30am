# WP-17A KPI Truth Master Register

Date opened: 2026-07-31
Status: ACTIVE
Authority: WP-17A Executive Authorization

This is the authoritative remediation register for WP-17A. No KPI or truth surface may be removed once inventoried.

## Verification evidence rubric for active repairs
- `code_present_locally`: source patched in preview workspace
- `tests_passed`: targeted automated tests passed
- `runtime_restarted`: supervisor restart completed after repair batch when needed
- `post_restart_endpoint_verified`: repaired response observed from running preview runtime or equivalent authenticated runtime path
- `ui_verified`: preview UI rendered the repaired truth surface

Current batch-1 verification state:
- code_present_locally: YES
- tests_passed: YES
- runtime_restarted: YES
- post_restart_endpoint_verified: PARTIAL (local/authenticated preview runtime checks continue alongside broader WP-17A sweep)
- ui_verified: PARTIAL (governance / storage / diagnostics preview smoke passed; full platform reconciliation still in progress)

## Status legend
- OPEN
- IN PROGRESS
- VERIFIED FIXED
- VERIFIED TRUTHFUL
- OPERATIONAL REMEDIATION REQUIRED
- ACCEPTED RISK
- BLOCKED

## Initial inventoried KPI / truth surfaces

### WP17A-KPI-001
- Portal: Admin OS / Operations Control Center
- Page: `/admin/operations-control`
- KPI or status name: Daily Report Draft Health
- User-facing label: `Daily Report · Draft Health`
- Current displayed value: production showed high abandoned/stale counts (`11750 abandoned`, `534 stale`, `0 failed` during live sweep)
- Current displayed status/color: `MISMATCH`
- Backend endpoint: `/api/admin/draft-health`
- Source collection/table/service: `draft_telemetry`
- Formula: raw event counts by event + time bucket; no canonical draft entity reduction yet
- Filters: event names (`draft.write.ok`, `draft.write.fail`, `quota.warning`, `draft.restore.offered`, `draft.restore.action`)
- Denominator: none
- Date range: `<1h`, `1h–24h`, `>24h`, last `24h`
- Tenant scope: global / platform-wide admin view
- Role scope: Super Admin / admin-only
- Refresh frequency: on request
- Cache behavior: none known
- Last refresh: live production sweep 2026-07-31
- Data age: near real-time event ingestion, but semantic drift suspected
- Confidence level: LOW
- Drill-down destination: telemetry / event drill-down only; no canonical draft entity drill-down
- Current defect classification: telemetry events appear to be presented as draft entities
- Severity: P0
- Repair status: VERIFIED FIXED
- Verification evidence: live production sweep; preview repair verified by `test_daily_report_draft_health_contract.py`
- Final disposition: preview-fixed; deployment pending

### WP17A-KPI-002
- Portal: Operations Control Center
- Page: `/admin/operations-control`
- KPI or status name: Backup Health Check
- User-facing label: `Backup Health Check`
- Current displayed value: `no local backups` on production OCC
- Current displayed status/color: `WARNING`
- Backend endpoint: OCC operation `backups.health`
- Source collection/table/service: `services/operations_control/backups.py` reading local `BACKUP_DIR`
- Formula: local directory existence + file count + latest modified time
- Filters: local filesystem only
- Denominator: none
- Date range: current snapshot
- Tenant scope: platform-wide
- Role scope: admin-only
- Refresh frequency: on request
- Cache behavior: none
- Last refresh: live production sweep 2026-07-31
- Data age: current filesystem snapshot
- Confidence level: MEDIUM
- Drill-down destination: none
- Current defect classification: secondary local signal presented adjacent to canonical backup truth
- Severity: P0
- Repair status: VERIFIED FIXED
- Verification evidence: live production sweep; preview repair verified by `test_wp17a_kpi_truth_p0.py`
- Final disposition: preview-fixed; deployment pending

### WP17A-KPI-003
- Portal: Operations Control Center
- Page: `/admin/operations-control`
- KPI or status name: Deploy Recovery Playbook
- User-facing label: `Deploy Recovery Playbook`
- Current displayed value: `NO local backups found`
- Current displayed status/color: `WARNING`
- Backend endpoint: OCC operation `deploy.recovery_playbook`
- Source collection/table/service: `services/operations_control/deploy.py` + local `BACKUP_DIR`
- Formula: static playbook + local backup folder presence
- Filters: local filesystem only
- Denominator: none
- Date range: current snapshot
- Tenant scope: platform-wide
- Role scope: admin-only
- Refresh frequency: on request
- Cache behavior: none
- Last refresh: live production sweep 2026-07-31
- Data age: current filesystem snapshot
- Confidence level: MEDIUM
- Drill-down destination: legacy `/admin/deploy-recovery`
- Current defect classification: local backup cache posture is not canonical production recovery truth
- Severity: P0
- Repair status: VERIFIED FIXED
- Verification evidence: live production sweep; preview repair verified by `test_wp17a_kpi_truth_p0.py`
- Final disposition: preview-fixed; deployment pending

### WP17A-KPI-004
- Portal: Admin Recovery / Recovery Dashboard
- Page: `/admin/recovery`
- KPI or status name: Recovery Snapshot / Backup Truth
- User-facing label: recovery snapshot backup posture
- Current displayed value: production latest backup healthy, hourly cadence active, RPO green, overall recovery AMBER
- Current displayed status/color: `AMBER`
- Backend endpoint: `/api/admin/recovery/snapshot`
- Source collection/table/service: canonical archive lineage + backup jobs + recovery truth services
- Formula: canonical backup freshness / failure history / drill evidence / scheduler state
- Filters: production authoritative archive lineage
- Denominator: none
- Date range: current authoritative recovery window
- Tenant scope: platform-wide
- Role scope: admin-only
- Refresh frequency: route read
- Cache behavior: service-level truth aggregation
- Last refresh: live production sweep 2026-07-31
- Data age: current
- Confidence level: HIGH
- Drill-down destination: recovery portal detail
- Current defect classification: mostly truthful, but must reconcile against non-canonical OCC backup cards
- Severity: P0
- Repair status: VERIFIED TRUTHFUL
- Verification evidence: live production sweep and WP-16A certification evidence
- Final disposition: canonical truth surface retained as authoritative

### WP17A-KPI-005
- Portal: Operations Control / Security
- Page: `/admin/operations-control`
- KPI or status name: Security & Deployment Posture — CORS pinned
- User-facing label: `CORS pinned=no`
- Current displayed value: `no`
- Current displayed status/color: `WARNING`
- Backend endpoint: OCC operation `security.posture`
- Source collection/table/service: env-var presence probe only
- Formula: checks `CORS_ORIGINS` env string rather than effective middleware configuration
- Filters: current runtime env
- Denominator: none
- Date range: current runtime snapshot
- Tenant scope: platform-wide
- Role scope: admin-only
- Refresh frequency: on request
- Cache behavior: none
- Last refresh: live production sweep 2026-07-31
- Data age: current
- Confidence level: LOW
- Drill-down destination: none
- Current defect classification: likely false warning because effective CORS middleware uses pinned regex fallback even when env string is blank / `*`
- Severity: P0
- Repair status: VERIFIED FIXED
- Verification evidence: live production sweep + preview repair verified by `test_wp17a_kpi_truth_p0.py`
- Final disposition: preview-fixed; deployment pending

### WP17A-KPI-006
- Portal: Governance / Trust
- Page: `/admin/governance`, `/admin/governance/trust`
- KPI or status name: Governance Summary / Findings Convergence
- User-facing label: governance summary / convergence score
- Current displayed value: production showed open PPE / employee-link findings with stale last scan
- Current displayed status/color: `MISMATCH`
- Backend endpoint: `/api/admin/governance/summary`
- Source collection/table/service: `compliance_findings`, `compliance_scans`
- Formula: weighted score from persisted open findings; `last_scan` shown but no freshness state model yet
- Filters: open + acknowledged findings
- Denominator: none
- Date range: persisted current store; scan freshness varies
- Tenant scope: platform-wide
- Role scope: admin-only
- Refresh frequency: on request
- Cache behavior: none known
- Last refresh: live production sweep 2026-07-31
- Data age: stale scan evidence observed
- Confidence level: MEDIUM
- Drill-down destination: findings lists / rule counts
- Current defect classification: stale findings may appear current without explicit freshness confidence model
- Severity: P1
- Repair status: OPEN
- Verification evidence: live production sweep + code trace in `backend/routes/governance.py`
- Final disposition: pending

### WP17A-KPI-007
- Portal: Storage & Recovery
- Page: `/admin/storage-recovery`
- KPI or status name: R2 Lifecycle Health
- User-facing label: storage lifecycle health score
- Current displayed value: production degraded by low ownership score and stale inventory freshness
- Current displayed status/color: `AMBER`
- Backend endpoint: `/api/admin/r2/lifecycle/health`
- Source collection/table/service: `r2_inventory`, `r2_classifications`, `r2_lifecycle_runs`, `backup_health`
- Formula: weighted composite score blending capacity, ownership, orphan, retention, backup, lifecycle, freshness
- Filters: latest classification + latest inventory run
- Denominator: total classified objects / total objects in latest inventory
- Date range: latest lifecycle runs
- Tenant scope: platform-wide
- Role scope: admin-only
- Refresh frequency: on request
- Cache behavior: none known
- Last refresh: live production sweep 2026-07-31
- Data age: stale inventory age observed
- Confidence level: MEDIUM
- Drill-down destination: storage/recovery page
- Current defect classification: stale inventory and ownership risk are conflated in one ambiguous score
- Severity: P1
- Repair status: OPEN
- Verification evidence: live production sweep + code trace in `backend/services/r2_lifecycle/health.py`
- Final disposition: pending

### WP17A-KPI-008
- Portal: Deploy Readiness
- Page: `/admin/deploy-readiness`
- KPI or status name: Cross-portal master binding coverage
- User-facing label: master-binding coverage percentages
- Current displayed value: production examples included very low employee/equipment coverage in some modules
- Current displayed status/color: `ATTENTION`
- Backend endpoint: `/api/admin/deploy-readiness`, `/api/admin/deployment-readiness`
- Source collection/table/service: master data trust / asset binding / route readiness helpers
- Formula: percentage of rows with canonical bindings per surface
- Filters: per module / record family
- Denominator: eligible records for each binding type
- Date range: current database state
- Tenant scope: platform-wide
- Role scope: admin-only
- Refresh frequency: on request
- Cache behavior: none known
- Last refresh: live production sweep 2026-07-31
- Data age: current
- Confidence level: MEDIUM
- Drill-down destination: deploy readiness / trust details
- Current defect classification: requires formula verification plus historical backfill + future ingestion prevention
- Severity: P1
- Repair status: OPEN
- Verification evidence: live production sweep; source tracing in readiness and mapping code
- Final disposition: pending

### WP17A-KPI-009
- Portal: Production Certification
- Page: `/admin/trust-spine` and certification surfaces
- KPI or status name: Workflow certification freshness
- User-facing label: production certification
- Current displayed value: stale / not-yet-exercised workflows under fixed 2-day freshness window
- Current displayed status/color: `DEGRADED`
- Backend endpoint: `/api/admin/production-certification`
- Source collection/table/service: `trust_spine_events`
- Formula: workflow state machine + universal `FRESHNESS_WINDOW = 2 days`
- Filters: per workflow terminal evidence
- Denominator: workflow catalog
- Date range: latest qualifying evidence
- Tenant scope: platform-wide
- Role scope: admin-only
- Refresh frequency: on request
- Cache behavior: none known
- Last refresh: live production sweep 2026-07-31
- Data age: mixed
- Confidence level: HIGH
- Drill-down destination: trust spine / workflow details
- Current defect classification: freshness policy may be overly universal; needs workflow-specific SLA audit
- Severity: P1
- Repair status: OPEN
- Verification evidence: live production sweep + code trace in `backend/lib/production_certification.py`
- Final disposition: pending

### WP17A-KPI-010
- Portal: Platform / Storage / System Health
- Page: multiple admin health surfaces
- KPI or status name: `/app` disk pressure
- User-facing label: storage / system usage
- Current displayed value: production observed around `76–81%` used
- Current displayed status/color: `WARNING`
- Backend endpoint: multiple health surfaces
- Source collection/table/service: local filesystem probes
- Formula: local disk usage percentage / file counts / artifact audits
- Filters: app container filesystem
- Denominator: total available disk
- Date range: current snapshot / trend varies
- Tenant scope: platform-wide
- Role scope: admin-only
- Refresh frequency: on request
- Cache behavior: none known
- Last refresh: live production sweep 2026-07-31
- Data age: current
- Confidence level: HIGH
- Drill-down destination: system/storage pages
- Current defect classification: operational capacity pressure; needs inventory, retention, cleanup policy, and trend model
- Severity: P1
- Repair status: OPEN
- Verification evidence: live production sweep
- Final disposition: pending

### WP17A-KPI-011
- Portal: Admin OS
- Page: `/admin`
- KPI or status name: Governance convergence display scaling
- User-facing label: governance convergence metric
- Current displayed value: preview code previously multiplied `convergence_score` by 100 and could overstate the score
- Current displayed status/color: metric display defect
- Backend endpoint: governance probe within Admin OS
- Source collection/table/service: `/api/admin/governance/summary`
- Formula: direct reuse of `convergence_score`
- Filters: none
- Denominator: score is already 0–100
- Date range: current summary snapshot
- Tenant scope: platform-wide
- Role scope: admin-only
- Refresh frequency: on request
- Cache behavior: none
- Last refresh: preview source tracing 2026-07-31
- Data age: current
- Confidence level: HIGH
- Drill-down destination: admin governance / governance trust
- Current defect classification: UI multiplied an already normalized 0–100 score by 100 again and also looked for a missing `rule_counts.total`
- Severity: P1
- Repair status: VERIFIED FIXED
- Verification evidence: source tracing + preview frontend patch + lint/smoke
- Final disposition: preview-fixed; deployment pending

### WP17A-KPI-012
- Portal: Deploy Readiness / Master Lookup
- Page: `/admin/deploy-readiness`, `/api/master-lookup/audit`
- KPI or status name: Cross-portal master-binding coverage formula
- User-facing label: master-binding coverage percentages
- Current displayed value: now computed from eligible denominator rather than all rows
- Current displayed status/color: remediation in progress
- Backend endpoint: `/api/master-lookup/audit`, `/api/admin/deploy-readiness`
- Source collection/table/service: `master_lookup` audit helpers + collection-level binding stats
- Formula: eligible records = canonical binding present OR at least one source field populated
- Filters: per collection / per binding type
- Denominator: eligible records only
- Date range: current database state
- Tenant scope: platform-wide
- Role scope: admin-only
- Refresh frequency: on request
- Cache behavior: none
- Last refresh: preview repair batch 2026-07-31
- Data age: current snapshot
- Confidence level: HIGH
- Drill-down destination: `/api/master-lookup/audit`
- Current defect classification: prior denominator overstated gaps and lacked source/backfill/review-queue metadata
- Severity: P1
- Repair status: VERIFIED FIXED
- Verification evidence: `test_wp17a_binding_storage_truth.py`
- Final disposition: preview-fixed; deployment pending

### WP17A-KPI-013
- Portal: Governance / Data Integrity
- Page: employee-link governance remediation surfaces
- KPI or status name: Ambiguous employee-link review queue
- User-facing label: review queue for ambiguous employee bindings
- Current displayed value: new auditable queue endpoint prepared in preview
- Current displayed status/color: remediation in progress
- Backend endpoint: `/api/admin/compliance/employee-link-review-queue`
- Source collection/table/service: governance linkage detector + `employee_link_review_queue`
- Formula: one queue item per ambiguous normalized employee-name finding
- Filters: active ambiguous linkage findings only
- Denominator: ambiguous linkage findings
- Date range: current detector snapshot
- Tenant scope: platform-wide
- Role scope: admin-only
- Refresh frequency: on demand
- Cache behavior: none
- Last refresh: preview repair batch 2026-07-31
- Data age: current snapshot
- Confidence level: HIGH
- Drill-down destination: review queue collection / API response
- Current defect classification: ambiguous matches previously skipped but not materialized into an auditable review queue
- Severity: P1
- Repair status: VERIFIED FIXED
- Verification evidence: `test_wp17a_binding_storage_truth.py`
- Final disposition: preview-fixed; deployment pending

### WP17A-KPI-014
- Portal: Storage & Recovery / OCC Maintenance
- Page: storage audit / safe cleanup surfaces
- KPI or status name: Local disk pressure observability
- User-facing label: storage audit / safe cleanup projection
- Current displayed value: threshold + retention + projected post-cleanup state + protected paths + last cleanup evidence
- Current displayed status/color: remediation in progress
- Backend endpoint: OCC `storage.audit`, `storage.safe_cleanup`
- Source collection/table/service: local filesystem audit + `storage_cleanup_history`
- Formula: point-in-time `/app` disk usage plus safe-cleanup reclaim preview
- Filters: audit paths + supervisor logs + python cache locations
- Denominator: total `/app` disk capacity
- Date range: current snapshot; cleanup history if available
- Tenant scope: platform-wide
- Role scope: admin-only
- Refresh frequency: on request
- Cache behavior: none
- Last refresh: preview repair batch 2026-07-31
- Data age: current snapshot
- Confidence level: HIGH
- Drill-down destination: OCC storage operations
- Current defect classification: previous surface lacked thresholds, retention classes, cleanup history context, and protected-evidence disclosure
- Severity: P1
- Repair status: VERIFIED FIXED
- Verification evidence: `test_wp17a_binding_storage_truth.py`
- Final disposition: preview-fixed; deployment pending
