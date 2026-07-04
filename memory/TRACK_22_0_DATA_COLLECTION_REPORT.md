# TRACK 22.0 · Data & Collection Value Report

## Method
Static reference-count scan across `backend/**/*.py` for `db[<name>]` / `db.<name>` patterns, method-noise filtered.

## Findings

- **328 distinct collection references** across the backend.
- **170 canonical collection names** (matches PLATFORM_MANIFEST.json baseline).
- **68 candidates referenced exactly once** — reviewed per Track 21.3 Phase D:
  - ~5 legitimate audit-only collections (single-writer) → **KEEP**
  - ~3 potentially-dormant candidates → **RETIRE_LATER** (Ops sign-off · Track 21.2z)
  - ~60 scanner false positives (Python attribute names, template placeholders) → **CLASS D**

## Core operational collections (KEEP)

Every domain has a canonical single source of truth:

| Domain | Primary collection(s) |
|---|---|
| Daily Reports | `daily_reports` |
| Incidents | `incidents` |
| Job Hazard Analysis | `jha_plans`, `jha_records` |
| Meetings | `safety_meetings` |
| QA/QC | `qaqc_reports` |
| Fleet | `equipment_master`, `vehicles`, `dvir_reports` |
| Employees | `employees`, `employee_records` |
| Projects | `projects`, `project_assignments` |
| Vendors | `vendors` |
| Historical Records | `records` |
| Job Photos | `job_photos` |
| Universal Threads | `records`, `equipment_master`, `daily_reports`, `job_photos` |
| Audit | `trust_spine_events`, `audit_events`, `admin_audit_events` |

## Data integrity

- Every write to an operational collection emits a `trust_spine_events` entry (workflow-stage emitter).
- No orphan writes detected in Phase 2A scan.
- Retention: `AUDIT_RETENTION_DAYS` env var controls cleanup (default 365).

## Six Pillars

- Trusted: **9.85** — Trust Spine covers every workflow write.
- Durable: **9.80** — retention policy documented; backups run every 12h (`BACKUP_HOURS_UTC=2,18`).
