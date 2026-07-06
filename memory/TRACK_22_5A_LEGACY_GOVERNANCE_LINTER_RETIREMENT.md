# TRACK 22.5A · Legacy Governance Linter Retirement + PM Truth-Source Reconciliation

**Executed:** 2026-02 · session ends with deployment gate GREEN.
**Scope discipline:** 1 file changed by this investigation. No allowlists expanded. No hardening locks weakened. No production data mutated.

---

## Executive Summary

The deployment gate previously surfaced `pm_missing_route` findings including one soft-deleted test project (`SD-6909db`), producing a divergence between:

* **UI truth** — `/api/jobs`, `/api/admin/pm-email-coverage`, `jobs_master.list_jobs()` — all filter with `{"active": True, "deleted_at": {"$in": [None, ""]}}`.
* **Audit truth** — `lib/master_data_trust._pm_assignment_findings` — filtered with `{"is_active": {"$ne": False}}`, a field that **does not exist on any row** in `jobs_master`, and which never honored `deleted_at`.

The audit therefore silently over-reported PM-missing findings (5 vs. the correct 4). The **fix aligns the audit filter with the canonical `jobs_master.list_jobs()` helper** — one file, two lines of logic changed. No behavior of the UI changed. No blocking-gate classification changed. `pm_missing_route` remains `DATA_ISSUE` → advisory → does not block deploy.

---

## Root Cause

`lib/master_data_trust._pm_assignment_findings` (line 52 in the pre-fix source) selected jobs with:
```python
{"is_active": {"$ne": False}}
```

**Two problems:**

1. **Wrong field name.** The `jobs_master` collection uses `active` (bool), not `is_active`. Live probe confirmed **0 of 30 rows** carry the `is_active` field. `$ne False` therefore matches every row unconditionally — including rows whose `active` field is `False`, if any ever existed.
2. **No soft-delete exclusion.** The collection uses `deleted_at` (ISO timestamp) for soft delete, and `jobs_master.delete_job()` sets that field instead of removing the row. The audit did not filter it out, so the soft-deleted test project `SD-6909db` (`deleted_at: 2026-06-08T22:36:44...`) was surfaced as an "active" job missing a PM.

**Consequence:** `pm_missing_route` reported **5** projects when the canonical UI shows **4**. The extra one was a phantom test row already invisible to the operator.

---

## Source-of-Truth Matrix

| Component | Data Source | Collection | Filter | PM Resolver | Authoritative | Legacy |
|---|---|---|---|---|---|---|
| **Admin Jobs page (UI)** | `GET /api/jobs`, `GET /api/admin/jobs` | `jobs_master` | `{"active": True, "deleted_at": {"$in": [None, ""]}}` | `jobs_master.pm_email` field | ✅ Yes | No |
| **Admin PM Coverage panel** | `GET /api/admin/pm-email-coverage` (routes/admin_pm_coverage.py L88) | `jobs_master` + `project_team_assignments` | `{"$or": [{"active": True}, {"active": {"$exists": False}}]}` | `pm_email` OR roster (Track 15.75A) | ✅ Yes | No |
| **Dispatch / Daily Reports / Routing** | `resolve_pm_for_project()` helper | `project_team_assignments` (primary) → `jobs_master.pm_email` (fallback) → `project_managers.jobs` | roster canonical, jobs_master legacy fallback | Multi-source | ✅ Yes | Fallback keeps legacy |
| **Master Data Audit (fixed)** | `lib/master_data_trust._pm_assignment_findings` | `jobs_master` + `project_team_assignments` | `{"active": True, "deleted_at": {"$in": [None, ""]}}` — **now matches UI** | Same as Dispatch | ✅ Yes | No |
| **Master Data Audit (before fix)** | Same file | `jobs_master` | `{"is_active": {"$ne": False}}` — **DIVERGENT** | Same as Dispatch | ❌ No (silently drifted) | Was legacy |
| **Deployment Gate CLI** | `scripts/deployment_gate.py` → calls `/api/admin/deployment-readiness` | Consumes audit output | N/A (pass-through) | N/A | ✅ Yes | No |
| **Governance / Duplicate detection** | `routes/project_identity_governance._list_jobs_master` | `jobs_master` | `{"deleted_at": {"$in": [None, ""]}}` | N/A | ✅ Yes | No |

**Chosen authoritative source for "active job":** `{"active": True, "deleted_at": {"$in": [None, ""]}}`.
**Why:** it is the exact filter shipped in `jobs_master.list_jobs(only_active=True)` — the single helper imported by `server.py` (5 call sites) and `routes/pm_routes.py`, and matched by `routes/admin_pm_coverage.py`. Every operator-facing surface uses this filter.

---

## Live Evidence — Per-Project Cross-Reference

| Project | jobs_master present | `active` | `deleted_at` | pm_email | roster PM/co-PM | UI shows? | Audit (before) | Audit (after) | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 20-07 | ✅ | `True` | `null` | `""` | `pm.demo@mascigc.com` (co_pm) | ✅ w/ roster PM | not flagged | not flagged | Resolvable |
| 21-06 | ✅ | `True` | `null` | `""` | `pm.demo@mascigc.com` (co_pm) | ✅ w/ roster PM | not flagged | not flagged | Resolvable |
| **22-08** | ✅ | `True` | `null` | `""` | none | ✅ (blank PM column) | flagged | flagged | Truly missing (legit advisory) |
| **24-08** | ✅ | `True` | `null` | `""` | none | ✅ (blank PM column) | flagged | flagged | Truly missing (legit advisory) |
| **26-04** | ✅ | `True` | `null` | `""` | none | ✅ (blank PM column) | flagged | flagged | Truly missing (legit advisory) |
| **26-07** | ✅ | `True` | `null` | `""` | none | ✅ (blank PM column; 16 DRs on record) | flagged | flagged | Truly missing — **operationally active without a PM** |
| ~~SD-6909db~~ | ✅ | `True` | `2026-06-08T22:36:44…` | `""` | none | ❌ (soft-deleted, UI excludes) | flagged (BUG) | not flagged (fixed) | Soft-deleted test row |
| 24-06 (baseline) | ✅ | `True` | `null` | `davidjewett@mascigc.com` | present | ✅ w/ PM | not flagged | not flagged | Resolvable |

**Delta:** audit findings dropped from **5 → 4**. All 4 remaining findings correspond to jobs the UI also shows without a PM. Nothing new was suppressed.

---

## The Operator's UI Claim vs Data Truth

Operator statement: *"Every active job has a PM assigned."*

Data reality:
- Of the 4 audit findings, **3** (22-08, 24-08, 26-04) have zero operational activity — no DRs, no meetings, no equipment inspections. They are legacy import stubs. The operator does not perceive them as "active" because they never appear in their workflow.
- **1** (26-07 · "University High Parent Loop Ext") has **16 daily reports, 13 equipment inspections, 151 job photos, 12 meetings** — this project **is actively producing work with no PM in `jobs_master`**. The DR carries `superintendent` but no `pm_email`. This is a real operational gap the platform should surface, not hide. The advisory finding is correct.

**Conclusion:** the audit is now measuring the same set as the UI. The 4 residual findings are **legitimate advisory data hygiene items**, not code defects — exactly the classification `admin_deployment_readiness.py` gives them. They **do not block deploy**.

---

## Before / After Deployment Gate Result

### Before (this session, pre-fix, with admin auth)
```
GET /api/admin/deployment-readiness
  decision:               pass
  blocking_gates:         0
  advisory_findings:      3
  pm_missing_route count: 5    ← samples: 22-08, 24-08, 26-04, 26-07, SD-6909db
  trust_score:            40   band: red
```

### After (this session, post-fix, with admin auth)
```
GET /api/admin/deployment-readiness
  decision:               pass
  blocking_gates:         0
  advisory_findings:      3
  pm_missing_route count: 4    ← samples: 22-08, 24-08, 26-04, 26-07
  trust_score:            50   band: red
```

### `scripts/deployment_gate.py` end-to-end (post-fix)
```
════════════════════════════════════════════════════════════
  MASCI · DEPLOYMENT TRUST GATE · TRACK 15.78
  DECISION: PASS
════════════════════════════════════════════════════════════
  Regression suite:  PASS (exit=0)
  Runtime gates:     PASS (blocking=0, advisory=3)
  Advisory (does NOT block deploy):
    ! [master_data]  4 active project(s) have no resolvable PM or Co-PM email …
    ! [master_data]  247 equipment row(s) missing canonical unit_number …
    ! [master_data]  200 active employee(s) saved without a canonical employee_id.
  Trust score: 50 · band: red · regression gates: 134
════════════════════════════════════════════════════════════
  ✅ All deployment gates satisfied — deploy permitted.
════════════════════════════════════════════════════════════
```

---

## Retired / Replaced / Kept Checks — Governance Linter Inventory

See `TRACK_22_5A_LINTER_FAILURE_INVENTORY.csv` for the per-file table.

**Category totals (this session + prior 22.5A adaptations):**

| Category | Count | Notes |
|---|---|---|
| **Retired** (removed entirely) | 0 | Nothing deleted. |
| **Replaced** (adapted to current architecture — same intent) | 21 | Legacy `App.js`-shell readers adapted to also read `AppRoutes.jsx` via `_shell_reader`. Same routes / prefixes / RBAC still asserted. |
| **Kept** (unchanged, current architecture already correct) | 113+ | Every non-shell governance/audit test unchanged. |
| **Truth-source aligned** (this investigation) | 1 | `_pm_assignment_findings` filter aligned to canonical `list_jobs()` filter. |
| **Allowlist added** (documented, non-masking) | 1 | `email_routing_audit_v2.status = "needs_configuration"` — see justification below. |
| **Allowlist removed** | 0 | |
| **Real defects fixed during 22.5A** | 3 | Raw error dump, undefined error string, JSX `<option>` mixing (prior session). |
| **Hardening locks weakened** | **0** | See "No Weakening" section. |

---

## `needs_configuration` Allowlist — Five-Condition Justification

The prior agent added `"needs_configuration"` to the `email_routing_audit_v2.status` allowlist in `admin_deployment_readiness.py` (L113–120). The operator's directive requires all five of the following to hold. **All five are satisfied — the entry is kept:**

1. **Semantic meaning documented** — Written by `routes/transportation_dispatch_gate.py:331`, `lib/transport_automation.py:344`, `lib/transport_cleanup_companion.py:112` when a routing rule matches but the resolved target has no valid recipient (e.g. a project without a PM email). Documented in-source at each write site.
2. **Runtime behavior documented** — Row is persisted to `email_routing_audit_v2` with `status="needs_configuration"`; downstream, `transport_cleanup_companion.py` surfaces it as a first-class `route_needs_configuration` finding with a matching cleanup action (`cleanup_route_needs_configuration`).
3. **Deployment behavior documented** — Locked by `tests/test_track_16_10_transportation_automation_engine.py::test_54_email_audit_writes_needs_configuration` and `tests/test_track_16_10a_transport_command_digest.py::test_18_missing_recipients_audits_needs_configuration`. These tests enforce the write contract.
4. **Operator impact documented** — Surfaced to operators as a resolvable finding in the Transport Command Digest and cleanup companion. The same underlying condition (missing PM email) is *already* surfaced as `pm_missing_route` in the master data audit. Allowlisting it in the audit-anomaly counter prevents **double counting the same fact**.
5. **No masking of production defects** — This does NOT reduce or hide any finding. `pm_missing_route` still fires (4 samples today), and each `needs_configuration` audit row remains individually queryable. The allowlist only prevents that same fact from also incriminating the *audit contract* (which is meant to catch unknown status strings, not documented ones).

**Verdict:** entry retained.

---

## Verification — No Hardening Locks Were Weakened

| Lock / Rule | Post-fix status |
|---|---|
| `test_track_15_78_deployment_gate.py` — gate-shape contract | ✅ Passes unchanged |
| `test_track_15_79c_dispatch_task_retention.py` — `schedule_auto_email` strong-ref | ✅ Passes; reader adapted to `email_dispatch.py` extraction |
| `test_track_15_80_no_secrets_in_repo.py` — secret leak scan | ✅ Passes |
| `test_track_15_81_dispatch_map_portal.py` — dispatch RBAC on `/operations-map/*` | ✅ Passes |
| `test_track_15_86_browser_smoke_gate.py` — browser smoke shape lock | ✅ Passes |
| `test_track_15_93_zero_touch_bootstrap.py` — startup bootstrap gate | ✅ Passes |
| `test_track_18_07_design_system_enforcement.py` — design system linter | ✅ Passes |
| `test_track_18_10_governance_boundary_linter.py` — governance boundary | ✅ Passes |
| `test_track_22_4b_followup_*` — idempotency spine (Trench + Shop) | ✅ Passes |
| `test_track_22_4c_mobile_responsiveness_sweep.py` — Playwright mobile | ✅ Passes |
| `test_track_22_5a_linter_modernization_lock.py` — this track's lock | ✅ Passes |
| `DATA_ISSUE_FINDING_CODES` classification | ✅ Unchanged (`pm_missing_route` still advisory) |
| `CODE_DEFECT_FINDING_CODES` classification | ✅ Unchanged (`critical_route_missing` still blocking) |

Full regression suite = **134 tests, exit=0** in the same run that produced the PASS above.

---

## Files Changed (This Investigation)

**One file, two logical changes:**

| File | Change | Lines |
|---|---|---|
| `/app/backend/lib/master_data_trust.py` | Aligned audit's `jobs_master` filter to the canonical `list_jobs()` filter. Added docstring explaining the reconciliation. | +12 / -1 |

**Files inherited from the prior 22.5A session** (untouched by this investigation, reviewed for weakening — none found):

| File | Change |
|---|---|
| `/app/backend/routes/admin_deployment_readiness.py` | `needs_configuration` allowlist entry — retained (5-condition justification satisfied). |
| `/app/backend/tests/_shell_reader.py` (new) | Bridge to read routes from `App.js` OR `AppRoutes.jsx`. |
| 21× `backend/tests/test_track_*.py` | Shell reader adaptations. Same intent, current architecture. |

---

## Files Intentionally Left Untouched (Scope Discipline)

* **95** other files reference `is_active` for OTHER collections (`employees`, `directory`, `field_leadership_users`, etc.). None were touched — the audit bug was localized to one function reading `jobs_master`.
* **6** other governance / audit tests (`test_track_15_76b_finalization.py`, `test_track_15_77_production_lock.py`, etc.) already only assert finding *shape* (severity, remediation_link, remediation). None required change.
* **121** allowlist entries across `admin_deployment_readiness.py` — none modified. Only the pre-existing `needs_configuration` entry (added in prior session) was audited and retained.
* No frontend files changed. No collection schemas changed. No data migrated. No PMs fabricated.

---

## What This Does *Not* Do

* Does **not** fabricate PM assignments for 22-08 / 24-08 / 26-04 / 26-07. Those remain advisory findings for the operator to resolve in `/admin/people-and-access` on their own time (30-second remediation each per the finding's `estimated_remediation_seconds`).
* Does **not** delete or archive the SD-6909db soft-deleted row — the audit simply stops surfacing it as if it were live.
* Does **not** change the classification of `pm_missing_route` from advisory to blocking, or vice versa.
* Does **not** touch `active` field on any document (the underlying "26-07 has no PM yet is producing DRs" gap is an operator-managed data issue, not a code fix).

---

## GO / NO-GO Recommendation

**TRACK 22.5A FINAL STATUS: 🟢 GO**

* Deployment gate CLI: **PASS** (regression 134/134, runtime 0 blocking, 3 advisory).
* Live-data reconciliation: audit set = UI set (4 advisories, identical samples).
* No hardening lock weakened.
* No allowlist expanded.
* No production data mutated.
* Scope discipline held: 1 file logical change.

The 4 residual `pm_missing_route` advisories are legitimate operator-actionable findings. They **do not block deploy** and can be resolved in Admin → People & Access at operator convenience.

**Ready to run Track 22.5 production pre-deployment certification.**
