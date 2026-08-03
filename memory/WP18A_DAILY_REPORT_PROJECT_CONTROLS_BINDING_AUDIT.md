# WP-18A Daily Report Project Controls Binding Audit

Date: 2026-08-03

## Why this audit matters
Daily Reports are the strongest candidate for field-level operational truth in the existing platform. This audit checks whether project controls actually bind to them or merely sit beside them.

## Main conclusion
Project controls already bind to Daily Reports in multiple evidence-backed ways. Daily Reports should remain a canonical truth source in WP-18B.

## Confirmed bindings

### 1) Cost-code actual production
- Daily Report records carry `cost_code_quantities`.
- Cost-code services load these actuals to compute progress snapshots.
- Schedule and Monday review reuse that derived progress.

Trace:  
field submitter  
→ `daily_reports.cost_code_quantities`  
→ cost-code progress/schedule services  
→ PM schedule + Monday review + briefing consumers

### 2) Safety read-only projection
- `backend/routes/safety_portal/daily_reports.py` explicitly states it is a **read-only Safety surface into the Daily Report stream**.
- This confirms Daily Reports already serve multiple domains without duplicating the underlying truth store.

Trace:  
Daily Report canonical record  
→ `GET /api/safety/daily-reports` projection  
→ Safety Portal list/detail consumers

### 3) ODS ingestion and KPI projection
- `daily_reports.py` contains ODS ingest hooks.
- `ods.py` and `ods_intelligence.py` read `operational_facts` and `operational_kpi_snapshots` derived from operational events including Daily Reports.
- PM operational-intelligence surfaces explicitly read accepted summaries and fact rows rather than scraping raw reports in the frontend.

Trace:  
Daily Report canonical record  
→ ODS ingest / derived facts + snapshots  
→ PM/Admin/Executive ODS dashboards

### 4) Monday review / weekly review evidence
- `oppc_execution.py` loads weekly project reports, weather, crews, subcontractors, haul cycles, and related evidence from Daily Reports for Monday review workspaces.
- This is source-level proof that Daily Reports already feed the weekly recap path.

Trace:  
Daily Report canonical record  
→ OPPC workspace builder  
→ Monday review and Monday briefings

## What Daily Reports appear to own
- day-by-day field activity evidence
- production quantities
- weather/narrative context
- certain crew and subcontractor context
- one of the key evidence lines for project intelligence and schedule actuals

## What Daily Reports do not own
- project identity authority
- project roster authority
- cost-code registry authority
- committed schedule policy
- executive dispatch history

## Risks if WP-18B ignores this
1. Duplicate “actuals” stores would create reconciliation drift.
2. Executive KPI layers could diverge from field evidence.
3. Schedule confidence could become detached from submitted production records.

## Evidence limits
- This audit did not prove that every Daily Report field is normalized equally across legacy and modern submission paths.
- This audit did not prove all ODS facts are sourced only from Daily Reports; ODS clearly aggregates more than one source.
- This audit did not prove an immutable approval-state policy for every downstream consumer.

## WP-18 disposition
- Daily Report canonical record: `REUSE_AS_IS`
- Cost-code actuals binding: `REUSE_AS_IS`
- ODS projection from Daily Reports: `EXTEND`
- Monday recap binding: `REUSE_AS_IS`

## Executive conclusion
Daily Reports are already part of the project-controls spine. They are not an adjacent logbook to be mirrored elsewhere; they are one of the major truth feeds that WP-18B should preserve.