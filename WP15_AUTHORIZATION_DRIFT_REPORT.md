# WP15 Authorization Drift Report

Date: 2026-07-29
Scope: Enterprise Governance managed surfaces + repository-wide drift scan

## Quantitative Convergence Snapshot
- Total authorization decision points discovered: **249**
- Canonical Governance Engine: **37**
- Legacy but migratable: **161**
- Special-case infrastructure: **51**
- Dead code removed: **1** (`_is_admin_actor` OPPC bypass helper)

## Managed-Scope Migration Completed
- Fixed broken governance APIs: delegation, emergency override, approval request approval
- Added immutable governance decision records with `decision_id`, `correlation_id`, `causation_id`, `decision_timestamp`, `policy_version`, `policy_effective_at`, `identity_snapshot`, `policy_snapshot`, and `determinism_fingerprint`
- Added structured authorization explanations to decisions and denial payloads
- Persisted preview-safe communication outcomes on approval requests and emergency overrides
- Removed OPPC frozen-briefing regeneration admin bypass and routed it through canonical governance evaluation

## Managed-Scope Verification Result
Verified governed surfaces:
- `backend/routes/enterprise_governance.py`
- `backend/routes/operations_control.py`
- `backend/routes/daily_report_lifecycle.py`
- `backend/routes/executive_overview.py`
- `backend/routes/ods_intelligence.py`
- `backend/routes/oppc_execution.py`

Convergence notes:
- `oppc_execution.py` legacy scope and frozen-regeneration bypasses were migrated to Governance Engine enforcement
- task and notification entry points now require governed actions for read/write/ack flows

Result: No confirmed alternate write-path authorization bypass remains in the verified WP-15 managed scope after the OPPC fix above.

## Remaining Legacy Checks Found
Repository-wide scan still found legacy authorization patterns outside the fully remediated WP-15 scope.

Examples:
- `backend/routes/tasks_notifications.py`
  - remaining legacy points are concentrated here (`9` scanner hits)
  - the remaining logic is read-side scope shaping for task/notification visibility and is still migratable to the canonical Governance Engine
- `backend/routes/asset_documents.py`
  - inline admin role branching remains
- `backend/routes/project_team_assignments.py`
  - inline PM role branching remains
- `backend/routes/trench_project_intelligence.py`
  - PM role gating remains
- `backend/routes/global_search.py`
  - PM role-specific branching remains
- additional route families still rely on legacy portal-token or role-specific logic patterns discovered by static scan

## Exceptions
- Some findings are authentication boundary modules or portal token plumbing rather than business-action authorization.
- However, several findings are still true authorization or read-scope decisions and therefore block a strict repository-wide zero-drift certification.

## Risk Assessment
- Managed WP-15 governance admin and core governed decision paths: **Low residual risk** after fixes and backend verification
- Repository-wide authorization drift risk: **Medium**
  - reason: legacy role-based read/write scope logic still exists outside the fully migrated governance path

## Final Certification
- Managed WP-15 scope: **PASS**
- Repository-wide zero authorization drift: **NOT YET CERTIFIED**

## Remaining Technical Debt
- **Non-zero** — concentrated in legacy read-side visibility logic and older route families outside the converged core.

Largest remaining legacy clusters from the scan:
- `backend/routes/cost_codes.py` — 35
- `backend/routes/global_search.py` — 18
- `backend/routes/safety.py` — 10
- `backend/routes/tasks_notifications.py` — 9
- `backend/routes/po_requests.py` — 8
- `backend/routes/operations_center.py` — 8

## Required Next Migration Targets
1. Migrate `tasks_notifications.py` read-scope filters to governance-backed identity and permission evaluation
2. Audit remaining route families flagged by repository scan for inline role/admin branching
3. Re-run repository-wide drift verification after each migration batch

---

## 2026-07-29 — WP-15C Baseline Expansion — Frontend Request-Lifecycle Surface Added

This checkpoint expands scanner coverage beyond backend-only authorization drift and now includes frontend governed-request construction patterns. The raw increase after expansion is a **baseline-model change**, not an automatic code regression.

### Identity Continuity Snapshot
- No credential rewrite or account migration was performed in this batch.
- Authoritative password ownership remains in the existing source collections:
  - `user_directory.password_hash`
  - `project_managers.password_hash`
  - `hr_users.password_hash`
  - `shop_users.password_hash`
  - `safety_users.password_hash`
  - `dispatch_users.password_hash`
  - `field_leadership_users.password_hash`
- Cross-identity email linkage inventory shows `161/161` portal records with email currently link to `user_directory` by email.

### Canonical Findings Model (normalized constitutional decision points)
- Scanner schema version: `2.0.0`
- Detection rules version: `2.0.0`
- Metric model version: `2.0.0`
- Comparable to previous scan: **No**
- Non-comparability reason: **WP-15C Baseline Expansion — Frontend Request-Lifecycle Surface Added**

### Migration and Lifecycle Notes
- Shared governance scope helpers were added and used to replace another batch of `compute_pm_scope` consumers.
- Shared governed frontend reads that previously missed `X-Directory-Token` were converged onto the canonical scoped header builder.
- A production-shaped identity continuity inventory was generated without exposing credentials.

### Risks still blocking certification
- Manual governed-request header construction remains present in many frontend surfaces and must be converged.
- Repository-wide governance convergence is still incomplete.
- Existing-user regression verification is still incomplete for several supported portal patterns.
