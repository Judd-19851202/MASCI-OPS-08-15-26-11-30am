# Remediation Candidate List · Critical Fix Sprint 1A

**Batch:** OMEGA Critical Fix Sprint 1A · Phase 1
**Date:** 2026-05-31
**Scope:** Every record flagged for potential cleanup with collection · ID · why-flagged · recommendation. **NO MODIFICATIONS EXECUTED.**

---

## 1 · 🔴 CRITICAL · Delete-or-deactivate (15 records)

| # | Collection | Record ID(s) | Why flagged | Recommendation |
|---|---|---|---|---|
| C-1 | `field_leadership_users` | `d805f3d4-76c8-480e-a268-b64b274e059c` (`fieldleader@mascigc.com`) | Test FL user with documented password | **Deactivate** (`is_active=False`) — preserves audit trail · easy to reactivate |
| C-2 | `incidents` | `d9626eeb-37a8-4e55-a5bb-3ea74f46ccd3` | "John Smith" test marker + duplicate `doc_id='INC-2026-00001'` + holds legacy `incident_number='INC-2026-0517-002'` | **Delete** (or move to `archived_incidents` collection · operator choice). Resolves contamination AND deduplicates doc_id in one step. |
| C-3..C-12 | `payroll_variance_batches` | 10 IDs created by `hrmanager@mascigc.com` 2026-05-12/13: `674300c9` · `48cbc60e` · `6590febb` · `f1371d01` · `76d952ce` · `f28d4b44` · `ed8ec430` · `8b649f92` · `2eb4c2d2` · `d3150925` | All contain "John Smith"/"Smith" canary; 0 matched_rows; iter238/iter282 test artifacts | **Delete** all 10 |
| C-13..C-14 | `payroll_variance_decisions` | (7 docs · IDs not enumerated · cross-link via `batch_id` filter) | Linked to deleted batches (presumed) | **Delete** if `batch_id` matches any of the 10 deleted batches |
| C-15 | `daily_reports` | 1 of `4cab04c6` or `ac306ad5` (duplicate `doc_id='DR-2026-00007'`) | Counter race | **Rename one** — the older record keeps `DR-2026-00007`; the newer gets next available number |

---

## 2 · 🟡 IMPORTANT · Cleanup/Backfill (90 records)

| # | Collection | Record(s) | Why flagged | Recommendation |
|---|---|---|---|---|
| I-1 | `notifications` | `64f443d6` + `9ac645f3` (PREVIEW_POSTENV) | Pre-2026-05-26 preview/prod crossover artifacts | **Delete** (no operational consequence; no user has read them) |
| I-2 | `session_activity` | 68 rows (`email=fieldleader@mascigc.com`) | Test FL user telemetry | **Optional delete** when C-1 ships; OR keep as audit trail |
| I-3 | `incidents` | All 7 records | `status=null` and `resolution_status=null` | **Backfill** with `status="open"` and `resolution_status="open"` |
| I-4 | `user_directory` | 7 rows (all) | `is_active=null` (schema drift) | **Backfill** with `is_active=True` |
| I-5 | `users` (legacy owner accounts) | `david.jewett` · `chris.wright` · `ramon.rodriguez` (3 idle 33+ days) | Stale; never used since platform stood up | **Operator consult** then either rotate password or deactivate |

---

## 3 · 🟢 COSMETIC · Optional retention sweep (~83 records)

| # | Collection | Records | Recommendation |
|---|---|---|---|
| Co-1 | `transfer_requests` | 29 Cancelled | **Optional** — leave as historical audit OR archive |
| Co-2 | `hub_banners` | 1 expired (Memorial Day) | **Optional** — relies on `expires_at` display filter |
| Co-3 | `idempotency_keys` | 24 (no codified retention) | **Optional** — purge keys older than 24 hr |
| Co-4 | `usage_events` | 255,921 (no codified retention) | **Operator decision** — define retention policy (90 d? 180 d?) |
| Co-5 | `audit_events` | 10,155 (no codified retention) | **Operator decision** — define retention policy (1 y? 7 y for compliance?) |

---

## 4 · Per-collection touch list (collections that will be written to during cleanup)

| Collection | Records changed | Operation |
|---|---|---|
| `field_leadership_users` | 1 | UPDATE (`is_active=False`) |
| `incidents` | 1 | DELETE (or move to archive) |
| `incidents` | 7 | UPDATE (status backfill) |
| `payroll_variance_batches` | 10 | DELETE |
| `payroll_variance_decisions` | up to 7 | DELETE (conditional) |
| `daily_reports` | 1 | UPDATE (rename `doc_id`) |
| `notifications` | 2 | DELETE |
| `user_directory` | 7 | UPDATE (`is_active=True`) |
| `users` (legacy owners) | 0..3 | UPDATE (deactivate / rotate · operator-driven) |
| `session_activity` | 68 | OPTIONAL DELETE |
| **TOTAL records touched** | **~104** (~36 hard-delete · ~28 update · ~40 optional) |

---

## 5 · No collections touched

These collections remain untouched in this remediation:

`audit_events` · `admin_audit` · `admin_audit_log` · `usage_events` · `events` · `operations_events` · `system_health_events` · `mfa_audit_events` · `login_attempts` · `command_center_thresholds` · `command_center_calendar` · `digest_settings` · `email_routing_config` · `integration_settings` · `role_templates` · `hub_banners` (cosmetic) · `backup_health` · `scheduler_locks` · `health_monitor_runs` · `tasks` · `corrective_actions` (no items) · `po_requests` · `fleet_defects` · `equipment_units` · `equipment_master` · `equipment_inspections` · `jobs_master` · `projects` · `project_managers` · `dispatch_assignments` · `qaqc_inspections` · `safety_documents` · `safety_equipment_*` · `safety_training_records` · `meetings` · `jhas` · `messages` · `notifications` (non-PREVIEW) · all ODR collections · all operational substrate collections.

---

## 6 · Closeout

🟡 **~104 records flagged across 10 collections** for the full remediation. Bulk of records (68) are test-user session telemetry; if the test FL user is deactivated, the telemetry can be left as audit OR purged at operator discretion. **NO MODIFICATIONS EXECUTED.**

🛑 STOP. See `PRODUCTION_CLEANUP_EXECUTION_PLAN.md` for the categorized execution plan.
