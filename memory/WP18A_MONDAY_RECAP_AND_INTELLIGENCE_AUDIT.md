# WP-18A Monday Recap and Intelligence Audit

Date: 2026-08-03

## Question answered
Does the platform already contain Monday recap/review and executive intelligence capability, or would WP-18 need to build it from zero?

## Short answer
It already exists in multiple connected layers.

## Evidence-backed capability stack

### 1) Project Monday review workspace
- `backend/routes/oppc_execution.py` exposes project Monday review routes.
- `backend/services/cost_codes/oppc_execution.py` builds the workspace from:
  - schedule snapshots
  - progress actuals
  - planning lifecycle
  - weekly Daily Report evidence
  - task status
  - trust-spine events
- `frontend/src/pages/PmMondayReviewWorkspace.jsx` is a live consumer with save/freeze/briefing actions.

Conclusion: Monday review is a real project-control workspace, not an aspirational placeholder.

### 2) Monday briefing persistence
- `oppc_briefings.py` persists project and enterprise briefing docs to `oppc_monday_briefings`.
- It supports draft/freeze/approve and PDF rendering.
- Project briefing content explicitly cites shared truth sources such as:
  - `jobs_master.assigned_cost_codes`
  - `daily_reports.cost_code_quantities`
  - `payroll_variance_batches`
  - `operational_variance_reviews`
  - `trust_spine_events`

Conclusion: Monday briefing is already a structured persisted artifact, not just computed screen text.

### 3) Enterprise operations center
- `oppc_execution.py` exposes `/api/oppc/enterprise/executive-operations-center`.
- `ExecutiveOperationalIntelligence.jsx` consumes this route.
- `oppc_briefings.py` also uses the same executive operations center when building enterprise Monday briefings.

Conclusion: executive Monday recap is already connected to project-level workspaces.

### 4) ODS intelligence lane
- `ods_intelligence.py` exposes PM/Admin/Executive intelligence summaries and attention feeds.
- These read from `operational_facts`, `operational_kpi_snapshots`, and confidence rollups.
- PM project cards specifically use accepted summary facts and photo-evidence facts.

Conclusion: there is an existing operational-intelligence lane separate from, but adjacent to, OPPC recap/briefing.

### 5) Legacy operational-intelligence lane
- `backend/operational_intelligence/routes.py` exposes summary, preview, dispatch, history, audit, recipients, and groups.
- `AdminOperationalIntelligence.jsx` consumes these APIs.
- The engine persists `operational_intelligence_history` and `operational_intelligence_audit`.

Conclusion: a second intelligence framework also exists and must be reconciled rather than ignored.

## Trust and ownership assessment

### Project-control recap owner
- Closest existing owner: OPPC execution + briefing services.

### Derived intelligence owner
- ODS dashboards and legacy operational-intelligence products are both downstream consumers and presentation/briefing layers.

### Strongest Monday source bundle
- schedule snapshot
- daily-report actuals
- planning lifecycle
- task / variance / trust-spine evidence

## Core overlap discovered
There are **three related but distinct intelligence/review families**:

1. **OPPC Monday review / recap / briefings** — closest to project controls.
2. **ODS intelligence dashboards** — derived KPI/fact dashboards.
3. **Legacy operational-intelligence digest engine** — productized briefing/dispatch framework.

These should not be treated as one thing, but they also should not spawn a fourth parallel system.

## WP-18 disposition
- OPPC Monday review workspace: `EXTEND`
- Monday briefings: `REUSE_AS_IS`
- ODS dashboards: `CONNECT`
- Legacy operational-intelligence engine: `CONSOLIDATE`

## Executive conclusion
Monday recap and executive intelligence are already present. WP-18B should establish hierarchy and responsibility across the existing lanes instead of building a new recap platform.