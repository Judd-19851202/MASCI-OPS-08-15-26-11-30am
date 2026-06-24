# TRACK 15.75A · Phase 3 — Source-Chain Mismatch Determination

## Question

Why did Job Master UI show a PM / Co-PM while routing dead-lettered?

## Answer (proven, not "likely")

**Root cause #5 from the operator's enumerated list:** _"PM directory has the email but resolver does not join against it."_ More precisely: the resolver did not consult **the source the UI was actually reading from**.

## Evidence

| Step | What the UI does | What the resolver did | What the resolver does now |
|---|---|---|---|
| User opens Active Jobs Master | `GET /api/admin/jobs/{project_number}/team` → reads `project_team_assignments` rows (active=true) | _did not consult this collection at all_ | _consulted as authoritative fallback when `jobs_master.pm_email` blank_ |
| User clicks "Add PM" → picks "David Jewett" | `POST /api/admin/jobs/{pn}/team` body `{user_id, assignment_role='pm', is_primary=true}` → inserts into `project_team_assignments` | _no signal received in `jobs_master.pm_email`_ | _new helper `_resolve_roster_pm` reads the inserted roster row_ |
| Daily Report submitted for that project | `schedule_auto_email("daily-report", doc)` → `recipients_for_record_async` → `resolve_pm_for_record_async` | _read `jobs_master.pm_email`, found blank → dead-letter_ | _falls through legacy path, then reads roster row → DIRECT_PM_ |

## What it is NOT

| Hypothesis the operator listed | Evaluation |
|---|---|
| 1. Job Master UI writes PM to one field, resolver reads another | ✅ **YES — this is the root cause.** UI writes to `project_team_assignments`; resolver only read `jobs_master`. |
| 2. Job Master stores name, resolver expects email | partial — yes, the resolver does support name→email lookup via `project_managers`, but the UI doesn't even write to `jobs_master.project_manager` |
| 3. PM ID vs email | no — resolver and roster both use email as the human-resolvable key |
| 4. Co-PM chips store names but resolver expects emails | no — roster stores emails inline; if missing, resolved via `user_id` → `user_directory` |
| 5. PM directory has email but resolver doesn't join against it | yes — this is hypothesis #1 phrased differently |
| 6. Resolver using deprecated fields | partial — `jobs_master.pm_email` is not deprecated, just incomplete |
| 7. Tenant-filter wrong | no — single-tenant in preview, dead-letter route configured |
| 8. Project name vs project number | no — both surfaces key by `project_number` |
| 9. Project number normalization | no — `_normalize_job_number` consistent with the regex match |
| 10. V2 vs legacy divergence | no — Track 15.74 + 15.75 already proved V2 audit truthful |

## Affected workflows (all share the same resolver)

| Workflow | Calls `recipients_for_record_async`? | Affected by source-chain mismatch? | Fixed by 15.75A? |
|---|---|---|---|
| Daily Report | yes (`kind='daily-report'`) | ✅ | ✅ |
| Safety Meeting | yes (`kind='meeting'`) | ✅ | ✅ |
| Equipment Pre-Op | yes (`kind='equipment-inspection'`) | ✅ | ✅ |
| Incident | yes (`kind='incident'`) | ✅ | ✅ |
| QA/QC | yes (`kind='qaqc'`) | ✅ | ✅ |
| Inspection | yes (`kind='inspection'`) | ✅ | ✅ |
| JHA | yes (`kind='jha'`) | ✅ | ✅ |

One resolver → one fix → all workflows restored.

## Fix scope

A single read-expansion in `pm_routing.py` was enough. No write-path
changes. No field migrations. No data mutation. No new collection.
No new env var. Backward-compatible by construction (legacy
`jobs_master.pm_email` ALWAYS wins when present — proven by
`test_legacy_pm_email_still_wins_when_present`).
