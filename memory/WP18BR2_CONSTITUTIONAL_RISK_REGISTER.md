# WP18BR2 Constitutional Risk Register

Date: 2026-08-03

## Purpose

Record the evidence-backed constitutional risks that still prevent automatic authorization of WP-18C.

## Risk register

| Risk ID | Risk | Evidence | Current impact | Enterprise-scale consequence | Severity | Required amendment |
|---|---|---|---|---|---|---|
| CR-01 | Enterprise hierarchy is not constitutionally explicit across domains. | `backend/routes/ods_intelligence.py:29,75-83,367-371`; `backend/routes/operational_kpis.py:173-187`; `backend/routes/ai_admin_config.py:47-52` | Key readers still assume `masci` as the default tenant/company scope. | Multi-company/division growth will create brittle exceptions and reconciliation. | Critical | Create one authoritative enterprise operating hierarchy before scale claims or WP-18C scope expansion. |
| CR-02 | Budget authority is absent. | `backend/routes/po_requests.py:580-711`; `backend/routes/project_health.py:97-206`; `backend/routes/operational_kpis.py:16-18` | Finance-facing project controls remain adjacency-only. | Future controller/CFO views risk a second truth stack or manual reconciliation. | Critical | Authorize a real Budget Hierarchy owner only after upstream truths are locked. |
| CR-03 | Earned Value authority is absent. | `WP18BR_EXECUTIVE_RATIFICATION_REPORT.md:132-149`; `WP18B_PROJECT_CONTROLS_READINESS_AUDIT.md:196-200` | No truthful CPI/SPI/EV reporting path exists. | Executive reporting will drift into synthetic or misleading measures. | Critical | Build EV only as a derived layer after budget authority exists. |
| CR-04 | Executive rollups are latency-bounded and partly sampled. | `OPPC_PERFORMANCE_SCALABILITY_VALIDATION.md:16-27,37-45`; `backend/routes/ods_intelligence.py:408-425` | Current enterprise read paths already run in multi-second bands. | 5x–10x growth will degrade executive trust and system responsiveness. | High | Introduce background materialization/caching before promising enterprise scale. |
| CR-05 | Resource, crew, and equipment planning are federated but not yet constitutionally unified. | `backend/services/cost_codes/foundation.py:173-191`; `backend/routes/project_team_assignments.py:878-1160`; `backend/routes/asset_spine.py:37-82`; `WP18BR_PROJECT_CONTROLS_CONSTITUTIONAL_RATIFICATION.md:16-19` | Cross-domain planning remains understandable to specialists, not yet singular to the enterprise. | Acquisitions and new service lines could create parallel planning lanes. | High | Freeze the federation contract and explicit role of each owner before expansion. |
| CR-06 | Constraints are split between daily field facts and standing blocker workflow. | `backend/routes/daily_reports.py:7-8`; `backend/routes/operational_constraints.py:7-19`; `WP18BR_EXECUTIVE_RATIFICATION_REPORT.md:60-66` | Constraint truth is real but constitutionally dual-lane. | Downstream schedule/KPI consumers may misread one lane as the whole truth. | High | Formalize the dual-lane constraint model and downstream consumption rules. |
| CR-07 | Production truth is broader than a single Daily Report owner. | `backend/routes/daily_reports.py:1-11`; `backend/routes/payroll_variance.py:1-22`; `WP18BR_EXECUTIVE_RATIFICATION_REPORT.md:51-58` | Production lineage is strong but segmented by fact family. | Enterprise reporting may flatten unlike facts into one deceptive “production” number. | High | Ratify explicit production fact families and reporting boundaries. |
| CR-08 | Executive intelligence remains semantically overlapping. | `backend/routes/ods_intelligence.py:1-6,312-494`; `backend/routes/project_health.py:4-7`; `backend/operational_intelligence/routes.py:16-76` | Multiple derived readers coexist. | Over time executives may get different meanings from adjacent dashboards. | High | Consolidate the executive intelligence hierarchy and retire redundant legacy lanes. |
| CR-09 | Operator discoverability is broad but not proven at enterprise scale. | `frontend/src/app/routing/AppRoutes.jsx:1-320`; `WP18BR_PROJECT_CONTROLS_CONSTITUTIONAL_RATIFICATION.md:84-102` | Many routes/workspaces exist. | More divisions and service lines could overwhelm navigation and role clarity. | Medium-high | Keep a strict role-and-workflow hierarchy before expanding surface area. |
| CR-10 | Asset identity still carries split-edge risk across registry and provider mappings. | `backend/routes/asset_spine.py:37-82,223-259`; `WP18BR_EXECUTIVE_RATIFICATION_REPORT.md:68-70,145` | Asset Spine is strong but not yet the only enterprise identity seam that matters. | Each added provider/acquisition raises identity-drift cost. | High | Keep Asset Spine as the permanent registry and subordinate provider mappings explicitly. |
| CR-11 | Embedded project-controls history on `jobs_master` may become long-horizon governance debt if left unbounded. | `backend/services/cost_codes/foundation.py:678-709,764-909,1018-1046` | Today this is efficient and coherent. | At enterprise scale, retention/versioning/restore semantics may become harder to reason about. | Medium-high | Add explicit long-horizon retention/version governance before major expansion. |
| CR-12 | AI assistance may be expanded before upstream truth conflicts are solved. | `backend/routes/ai_admin_config.py:1-15`; `backend/routes/translation.py:97-130`; `backend/routes/ods_intelligence.py:172-219,421-425` | AI is already useful as an assistive consumer. | If upstream truth remains ambiguous, AI can scale ambiguity faster. | High | Keep AI bounded to summarization/translation until constitutional owner gaps are closed. |

## Executive reading

The risk pattern is consistent:

- **The platform is not weak because nothing exists.**
- **It is risky because several important enterprise contracts are still implicit, overlapping, or absent.**

That is why the correct response is not broad rebuilding. It is constitutional tightening before implementation.