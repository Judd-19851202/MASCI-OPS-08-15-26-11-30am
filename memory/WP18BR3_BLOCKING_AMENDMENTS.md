# WP18BR3 Blocking Amendments

Date: 2026-08-03

## Purpose

Because the final BR3 gate is not `GO`, this document prioritizes the amendments that must be accepted before WP-18C.

## P0 blocking amendments

### BA-01 — Propagate existing enterprise hierarchy through downstream readers

**Why this survived challenge:** BR3 found that enterprise hierarchy already exists in governance, but not all read-side systems consume it consistently.

**Evidence:**
- governance hierarchy and identity snapshots: `backend/services/enterprise_governance.py:202-233,858-905,1536-1551`
- fixed MASCI defaults in readers: `backend/routes/ods_intelligence.py:29,75-83`; `backend/routes/operational_kpis.py:173-187`; `backend/routes/ai_admin_config.py:47-52`

**Impact if unresolved:** multi-company, multi-division, and acquisition growth will continue through exceptions instead of one enterprise contract.

### BA-02 — Declare one executive reporting hierarchy

**Why this survived challenge:** BR3 agreed with BR2 that overlap is real, but concluded that simplification is a redesign problem, not a platform-wide NO-GO.

**Evidence:**
- ODS additive reader: `backend/routes/ods_intelligence.py:71-123`
- Project Health derived reader: `backend/routes/project_health.py:4-7`
- KPI no-money reader: `backend/routes/operational_kpis.py:138-152`
- legacy operational intelligence: `backend/operational_intelligence/routes.py:16-76`

**Impact if unresolved:** executives will keep seeing adjacent but not identical answers from multiple visibility lanes.

### BA-03 — Establish canonical Budget Hierarchy

**Why this survived challenge:** BR3 found stronger upstream finance-adjacent architecture than BR2 highlighted, but still no budget owner.

**Evidence:**
- P&L snapshot: `backend/server.py:6619-6754`
- PO workflow: `backend/routes/po_requests.py:586-772`
- cost-code financial fields: `backend/services/cost_codes/foundation.py:15`

**Impact if unresolved:** finance operations will depend on proxies instead of one authoritative project-controls financial model.

### BA-04 — Add Earned Value only after budget exists

**Why this survived challenge:** upstream planning/schedule/progress math is reusable, but EV itself is still missing.

**Evidence:**
- schedule and progress inputs exist: `backend/services/cost_codes/schedule_engine.py:211-540`; `backend/services/cost_codes/foundation.py:658-675`
- no EV owner evidenced: `WP18BR3_FINANCIAL_CONSTITUTIONAL_REVIEW.md`

**Impact if unresolved:** executive performance reporting will remain incomplete or drift into misleading substitutes.

### BA-05 — Lock the federation contract for resources and constraints

**Why this survived challenge:** BR3 found that the systems already connect, but semantics remain implicit across planning, roster, dispatch, and dual-lane constraints.

**Evidence:**
- resource federation: `backend/services/cost_codes/foundation.py:173-191`; `backend/routes/project_team_assignments.py:878-1160`; `frontend/src/app/routing/AppRoutes.jsx:1153-1192`
- constraints: `backend/routes/daily_reports.py:7-8`; `backend/routes/operational_constraints.py:7-19,67-121`

**Impact if unresolved:** operational complexity will rise faster than portfolio scale.

### BA-06 — Enforce operational intelligence as the standing package-completion standard

**Why this now matters:** after C5, future work must not drift into data collection without downstream intelligence, automation, or executive value.

**Evidence:**
- `WP18_OPERATIONAL_INTELLIGENCE_CONSTITUTION.md`
- `WP18_OPERATIONAL_INTELLIGENCE_INHERITANCE_STANDARD.md`

This is the standing **WP-18 Operational Intelligence Constitution** amendment.

**Impact if unresolved:** later packages could remain technically additive while still failing the real business purpose of the platform.

### BA-07 — Enforce the platform as a governed decision engine

**Why this now matters:** later packages could still add data, screens, and KPIs without moving facts through a full governed decision lifecycle or establishing singular metric truth.

**Evidence:**
- `WP18_OPERATIONAL_DECISION_ENGINE_CONSTITUTION.md`
- `WP18_OPERATIONAL_DECISION_ENGINE_BACKWARD_COMPATIBILITY_AND_GAP_REPORT.md`

This is the standing **WP-18 Operational Decision Engine Constitution** amendment.

**Impact if unresolved:** the platform could appear richer while still failing to improve measurable decisions, future recommendations, or governed metric trust.

## BR3 sequencing principle

The amendments above should be read as **bounded architectural decisions that preserve existing validated work**.

They are **not** a license to redesign the platform broadly.