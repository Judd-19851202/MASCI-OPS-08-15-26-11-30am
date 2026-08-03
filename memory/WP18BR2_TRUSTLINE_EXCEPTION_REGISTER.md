# WP18BR2 Trust-Line Exception Register

Date: 2026-08-03

## Purpose

Record the trust lines that are incomplete, bounded, or still too ambiguous to support immediate WP-18C authorization.

## Trust-line exceptions

| Exception ID | Trust line | Current status | Primary evidence | Why it is not yet constitutionally complete | Enterprise-scale effect | Required amendment |
|---|---|---|---|---|---|---|
| TLX-01 | Assigned cost codes → enterprise master schedule | Partial | `backend/routes/cost_codes.py:486-520`; `backend/services/cost_codes/schedule_engine.py:211-540` | Project schedule authority is strong; a separate enterprise master-schedule hierarchy was not proven. | Portfolio planning could over-claim what is still project-scoped truth. | Keep schedule project-scoped until enterprise layer is explicitly ratified. |
| TLX-02 | Daily Report actuals → schedule progress | Strong but bounded | `backend/services/cost_codes/foundation.py:658-675`; `backend/services/cost_codes/schedule_engine.py:110-161,231-267` | Actuals flow is real, but depends on field-entry quality and does not by itself solve production fact-family decomposition. | Executive progress narratives may become too coarse at scale. | Formalize production fact families before broader rollups. |
| TLX-03 | Daily field constraints → standing blocker memory → schedule/KPI consumers | Weak | `backend/routes/daily_reports.py:7-8`; `backend/routes/operational_constraints.py:7-19`; `WP18BR_PROJECT_CONTROLS_CONSTITUTIONAL_RATIFICATION.md:76` | Daily and standing constraint lanes are not yet governed as one explicit downstream contract. | Constraint impact can be underreported or double-counted. | Ratify the dual-lane constraint model and consumer rules. |
| TLX-04 | Demand planning → staffing roster → dispatch deployment | Weak | `backend/services/cost_codes/foundation.py:173-191`; `backend/routes/project_team_assignments.py:878-1160`; `WP18BR_PROJECT_CONTROLS_CONSTITUTIONAL_RATIFICATION.md:16` | The federation exists but is not yet one enterprise-semantic planning contract. | Cross-division staffing may drift into informal workarounds. | Consolidate the federation semantics before scale expansion. |
| TLX-05 | Asset identity → deployment/use → executive resource reporting | Weak | `backend/routes/asset_spine.py:223-259`; `WP18BR_EXECUTIVE_RATIFICATION_REPORT.md:68-70,145` | Asset identity is stronger than before, but provider-local mapping seams remain. | Acquisition and provider expansion increase identity drift risk. | Keep Asset Spine permanent and subordinate all local mappings explicitly. |
| TLX-06 | Operational facts/snapshots → executive ODS rollups | Partial | `backend/routes/ods_intelligence.py:71-123,312-494`; `OPPC_PERFORMANCE_SCALABILITY_VALIDATION.md:24-27` | Read-side lineage is clear, but fixed-tenant assumptions, sampling, and latency bounds limit enterprise claims. | Enterprise dashboards may require selective caching/materialization rather than direct synchronous reads. | Ratify scale posture before broader executive promises. |
| TLX-07 | PO approvals / project-health signals → budget authority | Missing | `backend/routes/po_requests.py:580-711`; `backend/routes/project_health.py:167-186`; `backend/routes/operational_kpis.py:16-18` | Adjacency exists, but no budget owner/store/hierarchy exists. | Finance consumers risk being misled by partial proxies. | Create Budget Hierarchy before any finance-control implementation. |
| TLX-08 | Budget authority → earned value authority | Missing | `WP18BR_EXECUTIVE_RATIFICATION_REPORT.md:132-149` | EV cannot exist constitutionally before budget exists. | Any EV surface would be unstable from day one. | Sequence EV strictly after budget. |
| TLX-09 | Enterprise scope hierarchy → cross-company reporting | Missing | `backend/routes/ods_intelligence.py:29`; `backend/routes/operational_kpis.py:173-187`; `backend/routes/ai_admin_config.py:47-52` | No cross-domain enterprise hierarchy is evidenced strongly enough to govern multi-company reporting. | Acquisitions and new divisions would be absorbed inconsistently. | Establish one enterprise operating hierarchy. |
| TLX-10 | Route breadth → trusted enterprise operator workflow | Bounded | `frontend/src/app/routing/AppRoutes.jsx:1-320`; `WP18BR_PROJECT_CONTROLS_CONSTITUTIONAL_RATIFICATION.md:84-102` | Many routes exist, but no primary evidence proves intuitive enterprise-scale workflow comprehension. | Navigation complexity can outgrow user trust. | Keep IA/workflow hierarchy explicit before adding major new surface area. |

## Executive reading

The strongest trust lines already support reuse. The blocked trust lines are mostly **enterprise-scope and finance-scope seams**, not proof that the whole platform should be rebuilt.