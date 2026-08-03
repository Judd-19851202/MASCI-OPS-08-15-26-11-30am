# WP-18A Project Controls Existing State

Date: 2026-08-03  
Method: evidence-only source audit. No code execution, no behavior changes, no WP-18B build.

## Executive Readout
The existing project-controls estate is **not greenfield**. The source base already contains substantial capability in five layers:

1. **Canonical operational records**
   - `jobs_master`
   - `daily_reports`
   - `project_team_assignments`
   - `cost_code_registry`
   - `operational_constraints`
2. **Derived operational data / analytics**
   - `project_operational_config`
   - `operational_facts`
   - `operational_kpi_snapshots`
   - embedded OPPC fields on `jobs_master`
   - `oppc_monday_briefings`
3. **Project-control workflow services**
   - cost-code normalization and assignment helpers
   - deterministic schedule engine
   - planning lifecycle / weekly rollover support
   - Monday review workspace builder
   - Monday briefing builder / PDF renderer
4. **Operator-facing delivery surfaces**
   - PM schedule workspace
   - PM staffing and team views
   - PM Monday review workspace
   - PM command center
   - PM/Admin/Executive intelligence surfaces
5. **Governance and fallback layers**
   - project identity drift queue
   - operational constraints registry
   - manual CSV import/export mapping fallback

## Current State by Domain

### 1) Project identity
- Evidence supports `jobs_master` as the main project identity authority used by PM jobs, staffing, schedule, identity governance, and confidence rollups.
- `project_identity_governance.py` is explicitly a **detector / queue** and states it should **never mutate** source records.
- Conclusion: identity governance already exists and should be treated as a **governance overlay**, not as a replacement identity owner.

### 2) Staffing and team ownership
- `project_team_assignments.py` provides explicit roster persistence, scoped read APIs, and summary endpoints.
- `PmProjectStaffing.jsx` and `AdminProjectStaffing.jsx` are thin shells over one shared `ProjectStaffingHub` consumer.
- Conclusion: staffing is **existing and reusable**, not a greenfield requirement.

### 3) Cost-code and schedule spine
- `cost_codes.py` plus `services/cost_codes/foundation.py` and `schedule_engine.py` form an existing schedule-and-cost-code backbone.
- Project assignments are persisted to `jobs_master.assigned_cost_codes` and projected into `project_operational_config` for ODS use.
- The schedule is deterministic and derived from assignment fields, predecessors, durations, and actual production evidence.
- Conclusion: WP-18B should **extend and harden** this spine rather than replace it.

### 4) Daily Reports as actual-production truth
- `daily_reports.py` remains the clearest canonical operational record for field actuals.
- Downstream consumers already exist in Safety, ODS, cost-code progress, OPPC, and health/intelligence layers.
- Conclusion: Daily Reports are a primary truth source and should remain so.

### 5) Lookahead / weekly reconciliation
- No separate standalone “lookahead application” was found.
- Instead, lookahead and weekly rollover logic already live inside the cost-code / planning lifecycle track.
- Conclusion: this is an **embedded existing capability** and should be extended, not rebuilt from zero.

### 6) Monday recap / Monday review / briefings
- `oppc_execution.py` and related cost-code services provide a real Monday review workspace.
- `oppc_briefings.py` persists project and enterprise Monday briefings to `oppc_monday_briefings` and can render PDF output.
- Conclusion: Monday recap/briefing is already present in source and materially connected.

### 7) PM command and intelligence
- `pm_command_center.py` aggregates multiple canonical sources for the PM command center.
- ODS PM/Admin/Executive intelligence routes consume `operational_facts`, `operational_kpi_snapshots`, and confidence rollups.
- A separate legacy `operational_intelligence` package also exists with summary/preview/dispatch/history/audit APIs.
- Conclusion: there are **multiple intelligence lanes**. WP-18B should rationalize their responsibilities rather than create another parallel engine.

### 8) Constraints and manual integration fallback
- `operational_constraints.py` is a real constraint substrate with persistence and governance.
- `imports_exports.py` explicitly documents a manual CSV fallback before Motive/MaintainX credentials are available.
- Conclusion: both capabilities exist, but both require deliberate connection policy in WP-18B.

## Existing-State Classification

### Existing and materially connected
- PM scoped jobs / project selector
- Project team roster and staffing summary
- Cost-code registry and assignment spine
- Schedule / forecast / planning-lifecycle stack
- Daily Report canonical record
- PM Monday review workspace
- Monday briefing persistence / PDF
- PM command center
- ODS PM/Admin/Executive dashboards

### Existing but partial / embedded / not fully connected
- Operational constraints to schedule/intelligence binding
- Planning lifecycle as an embedded sub-capability rather than a dedicated control domain
- Manual import/export fallback versus credentialed provider integration
- Enterprise intelligence overlap between OPPC rollups and legacy operational-intelligence products

### Existing but consumer-only
- Project identity governance queue
- Safety Daily Report projection
- ODS and project-health dashboards

## Source-of-Truth Posture

### Strongest authority evidence
- `jobs_master` for project identity and project-assigned cost-code configuration
- `project_team_assignments` for explicit project roster rows
- `daily_reports` for field actuals and production evidence
- `cost_code_registry` for reusable cost-code definitions

### Derived / downstream stores
- `project_operational_config`
- `operational_facts`
- `operational_kpi_snapshots`
- `jobs_master.oppc_*` embedded history/override/briefing-adjacent fields
- `oppc_monday_briefings`
- `operational_intelligence_history`
- `operational_intelligence_audit`

## WP-18A Conclusion
The project-controls platform already contains the majority of the architectural building blocks requested for WP-18. The main WP-18B opportunity is **reuse, consolidation, and explicit trust-line connection**, not wholesale replacement.

No evidence in this audit justifies assigning `BUILD_NEW` to the core schedule, staffing, Daily Report, Monday review, or intelligence foundations.