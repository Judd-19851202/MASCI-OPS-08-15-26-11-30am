# WP-18A Schedule Forensic Audit

Date: 2026-08-03  
Focus: existing schedule capability, trust lines, and reuse suitability.

## Key finding
The platform already contains a real schedule system. It is not just a placeholder page.

## Evidence chain

### 1) Real schedule engine exists
- `backend/services/cost_codes/schedule_engine.py` is a deterministic service module.
- Source comments and downstream callers show it computes forecast dates, critical path, hardening summaries, and Monday-look-behind readiness support.

### 2) Route layer already exposes schedule payloads
- `backend/routes/cost_codes.py` returns schedule payloads for project-specific consumers.
- The same route family also exposes progress, forecast history, overrides, planning lifecycle, rollover preview/apply, and DOT report generation.

### 3) Frontend schedule workspace is a genuine consumer
- `frontend/src/pages/PmProjectSchedule.jsx` consumes API payloads for:
  - assignments
  - progress
  - schedule
  - forecast
  - planning lifecycle
  - weekly rollover preview/apply
  - DOT schedule report export
- This is evidence of an actual user-facing project-control workspace, not an empty shell.

## Current schedule trust model

### Inputs
- `jobs_master.assigned_cost_codes`
- assignment metadata such as quantity, duration, predecessors, performer, and CPM identifiers
- `daily_reports.cost_code_quantities`
- forecast overrides and embedded history on `jobs_master`

### Transformation
- `load_project_assignments()`
- `load_project_cost_code_actuals()`
- `build_progress_snapshot()`
- `build_schedule_snapshot()`
- planning-lifecycle snapshot builders

### Consumers
- PM schedule workspace
- Monday review workspace
- Monday briefings
- executive OPPC surfaces

## What is already mature
- Deterministic schedule math exists.
- Schedule is connected to actual production evidence.
- Schedule supports forecast history and override governance.
- Schedule drives downstream Monday-review readiness.

## What is partial or embedded
- There is no separately evidenced standalone “master schedule service boundary”; schedule remains embedded inside the cost-code module family.
- Planning-lifecycle / weekly-reconciliation behavior is tightly coupled to the same module family rather than isolated as a dedicated bounded context.
- The audit did not prove external Primavera/MSP import parity or bidirectional sync.

## Reuse assessment

### Reuse-as-is candidates
- deterministic schedule engine
- PM schedule page as the operator-facing base workspace
- forecast history model

### Extend candidates
- explicit lifecycle statusing for weekly reconciliation
- executive-facing traceability from schedule deltas to project-health and constraint consumers
- stronger authority documentation for committed finish vs projected finish ownership

### Avoid
- Do not introduce a second parallel schedule store.
- Do not move schedule authority into ODS snapshots.
- Do not infer schedule truth from dashboard views when the source path already exists.

## WP-18 disposition
- Core schedule engine: `REUSE_AS_IS`
- PM schedule workspace: `EXTEND`
- lifecycle/rollover controls: `EXTEND`
- executive traceability around schedule: `CONNECT`

## Executive conclusion
The schedule capability already exists, is materially connected, and should become the formal WP-18B schedule backbone. The work ahead is architecture clarification and tighter trust-line connection, not replacement.