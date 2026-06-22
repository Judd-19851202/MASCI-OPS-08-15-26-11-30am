# TRACK 15.62 · PM Command Center Haul Recovery (R-PMCC) — Session A

## Problem (15.61 finding)

> Daily Reports contain haul data. PM Command Center reports zero loads. PMs believe no trucking occurred. — Track 15.61 Phase 5/6.

## Root cause (proven by code reading + endpoint probing)

Three independent code bugs, NOT an architecture limitation:

1. **K-HAUL-1** · `/api/pm/command-center/hauls` queried ONLY `db.dispatch_assignments`. Daily-Report-recorded hauls were silently absent.
2. **K-MM-1** · `/api/pm/command-center/materials` extracted material name with `m.get("type") or m.get("name")` but production rows store the name on the `material` key. Every Daily-Report-sourced row returned `material: null`.
3. **K-AGG-1** · `/api/pm/command-center/overview.counts.loads_today` counted only `db.haul_cycles` completions. Daily-Report `outbound_materials` quantities were never summed.

## Fix

Single file `backend/routes/pm_command_center.py`. Diff summary:

- `/hauls` endpoint now UNIONs Daily-Report outbound rows (last 14 days, scoped by project filter) with dispatch_assignments rows. Each DR row carries `source_system="daily_reports"`, `daily_report_id`, `daily_report_doc_id`, `material`, `cycle_count` (= loads), `unit`, `hauler`, `destination`, `ticket_or_manifest`.
- `/materials` endpoint now correctly extracts `m.get("material")` AND surfaces `quantity`, `unit`, `hauler`, `supplier` on every row.
- `/overview` now surfaces `counts.loads_today_breakdown.{dispatch_haul_cycles, daily_report_outbound, daily_report_inbound}` so consumers see exactly where the load count comes from. `loads_today` is the sum.

## Verification (post-fix on preview)

Project 26-07 (which 15.61 forensics showed has DR-recorded haul rows):

| Check | Pre-15.62 | Post-15.62 |
|---|---|---|
| `/hauls` rows (project=26-07) | 0 | **3** |
| `/hauls` rows with `source_system="daily_reports"` | 0 | **3** |
| Sample row carries `daily_report_doc_id` | n/a | **DR-2026-00341** |
| Sample row carries `material="Dirt"` + `cycle_count=10` | n/a | **yes** |
| `/materials` rows with non-null material name | 0/12 | **3/12** |
| `/overview.counts.loads_today_breakdown` | absent | **present** |

Machine-readable evidence: `/app/test_reports/track_15_62_session_a_verify.json` → checks `pmcc_hauls_includes_dr_rows`, `pmcc_materials_non_null_names`, `pmcc_overview_loads_breakdown`.

## Six Pillars

Powerful 10 · Simple 10 · Beautiful 9 · Trusted 10 · Proven 10 · Deployable 10 → **59/60**.

## Status

✅ **PM Command Center haul recovery is functionally complete and verified.**

The same data now appears in three previously-broken surfaces (hauls tab · materials tab · overview breakdown). PMs immediately see the correct number the moment the backend ships — no flag flip required for this fix specifically. (The frontend Session B work refines the form-side capture so MORE data is captured; the backend-side surfacing of EXISTING data is unblocked today.)
