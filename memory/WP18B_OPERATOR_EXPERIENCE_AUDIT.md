# WP18B Operator Experience Audit

Date: 2026-08-03  
Perspective: Real Project Manager wayfinding and operational discoverability  
Evidence basis: existing PM navigation audit, current PM sidebar domain map, routed PM entry paths, and already-audited route families only.

## Executive finding

From an operator perspective, the platform already exposes most of the required Project Controls surfaces, but not with uniform discoverability. The PM experience is strongest where the system uses explicit route names (`Schedule`, `Daily Reports`, `Monday Review`, `Photos`, `Meetings`, `QA/QC`, `Equipment`). It is weaker where capabilities are embedded, federated, or described indirectly (`Cost Codes`, `Forecast`, `Lookahead`, `Resources`, `Safety`, `Documents`, `Budget`).

### Discoverability denominator: 14 required operator control areas

- **Natural locate/use:** 7/14
- **Partial locate/use:** 5/14
- **Weak locate/use:** 2/14
- **Missing:** 0/14

## PM wayfinding findings

| Capability | PM route / entry evidence | Natural locate/use | Architectural finding | Evidence source | Confidence | Recommended disposition |
|---|---|---:|---|---|---|---|
| Cost Codes | Embedded in PM schedule path rather than a route explicitly named `Cost Codes` | Partial | Cost-code execution truth is present but operator naming is indirect | `WP18A_PM_NAVIGATION_AND_ENTRY_PATH_AUDIT.md`; `domainMap.js:27-39` | High | EXTEND |
| Schedule | `/pm/project-schedule` | Natural | The schedule surface is explicit and matches operator expectation | `WP18A_PM_NAVIGATION_AND_ENTRY_PATH_AUDIT.md`; AppRoutes evidence cited there | High | REUSE |
| Budget | Financials & Cost domain only; no explicit PM budget route evidenced | Weak | Adjacent financial signals exist, but no direct budget control surface or budget owner was evidenced | `domainMap.js:42-51`; `WP17A_KPI_SOURCE_MAP.md:24` | High | BUILD_NEW |
| Forecast | Primarily embedded inside the schedule workspace and OPPC schedule flow | Partial | Forecast capability exists, but operator discoverability depends on knowing to enter the schedule workspace | `WP18A_SCHEDULE_FORENSIC_AUDIT.md`; `OPPC_FORECASTING_CRITICAL_PATH_CERTIFICATION.md` | High | EXTEND |
| Production | `/pm/daily`, PM command center, OPPC execution consumers | Natural | Daily production and actuals are easy to find and well backed by canonical truth | `domainMap.js:27-39`; `WP18A_DAILY_REPORT_PROJECT_CONTROLS_BINDING_AUDIT.md` | High | REUSE |
| Lookahead | Embedded inside schedule/lifecycle semantics; no first-class PM route named `Lookahead` | Weak | The capability exists, but discoverability depends on hidden schedule lifecycle knowledge | `WP18A_LOOKAHEAD_AND_WEEKLY_RECONCILIATION_AUDIT.md`; `WP18A_PM_NAVIGATION_AND_ENTRY_PATH_AUDIT.md` | High | EXTEND |
| Monday Review | `/pm/monday-review` | Natural | The weekly control ritual is directly discoverable | `WP18A_PM_NAVIGATION_AND_ENTRY_PATH_AUDIT.md`; `WP18A_MONDAY_RECAP_AND_INTELLIGENCE_AUDIT.md` | High | REUSE |
| Resources | Split across command center resources, project staffing, people, fleet, and dispatch-backed consumers | Partial | Operators can reach resource information, but it is federated across several views | `domainMap.js:54-65`; `pm_command_center.py:508-560`; `OPPC_ENTERPRISE_RESOURCE_COORDINATION.md` | Medium-high | EXTEND |
| Photos | `/pm/photos` | Natural | Photo discoverability is explicit and direct | `domainMap.js:37-39`; `WP18A_PM_NAVIGATION_AND_ENTRY_PATH_AUDIT.md` | High | REUSE |
| Documents | Split across JHA plans, trench boxes, trench safety, posters; no single PM documents hub evidenced | Partial | The document-control family exists, but it is segmented by document type rather than one operator-facing control center | `domainMap.js:68-79` | High | EXTEND |
| Meetings | `/pm/meetings` | Natural | Meeting workflows are directly discoverable | `domainMap.js:33-36`; `WP18A_PM_NAVIGATION_AND_ENTRY_PATH_AUDIT.md` | High | REUSE |
| QA/QC | `/pm/qaqc` | Natural | Quality records are directly findable from the PM shell | `domainMap.js:81-90`; `WP18A_PM_NAVIGATION_AND_ENTRY_PATH_AUDIT.md` | High | REUSE |
| Safety | Spread across inspections, incidents, crew compliance, trench safety | Partial | Safety information is reachable, but it is distributed across several route families rather than one PM safety spine | `domainMap.js:31-35,73-90` | High | EXTEND |
| Equipment | `/pm/fleet` and `/pm/equipment` | Natural | Equipment and pre-op discoverability is explicit | `domainMap.js:59-65`; `pm_command_center.py:396-420` | High | REUSE |

## Architectural findings

### 1) PM operators can already find most real control surfaces
- **Evidence source:** `WP18A_PM_NAVIGATION_AND_ENTRY_PATH_AUDIT.md`, `frontend/src/components/pm/sidebar/domainMap.js`
- **Confidence level:** High
- **Architectural impact:** Existing operator entry paths should be preserved as constitutional discoverability anchors
- **Recommended disposition:** **REUSE**

### 2) The weakest PM discoverability zones are the controls that are embedded rather than named
- Embedded or indirect areas: Cost Codes, Forecast, Lookahead, Resources, Documents, Safety
- **Evidence source:** same as above plus `WP18A_LOOKAHEAD_AND_WEEKLY_RECONCILIATION_AUDIT.md`
- **Confidence level:** High
- **Architectural impact:** Future work should extend naming and constitutional information architecture before considering new engines
- **Recommended disposition:** **EXTEND**

### 3) Budget is both a navigation weakness and an architecture weakness
- The PM shell advertises “budget signals,” but no direct PM budget route or constitutional budget owner was evidenced
- **Evidence source:** `domainMap.js:42-51`, `backend/routes/operational_kpis.py:16-17`
- **Confidence level:** High
- **Architectural impact:** Budget cannot be solved by navigation alone because the owner itself is absent
- **Recommended disposition:** **BUILD_NEW**

### 4) The platform does not need a new PM controls shell
- Existing PM navigation already exposes the necessary route family structure
- **Evidence source:** `WP18A_PM_NAVIGATION_AND_ENTRY_PATH_AUDIT.md`
- **Confidence level:** High
- **Architectural impact:** Future UI or IA work should preserve the current PM shell and clarify routing semantics rather than introducing a second PM command architecture
- **Recommended disposition:** **REUSE / EXTEND**

## Constitutional answer

From the operator perspective, the platform already has a valid PM control shell. The architectural problem is **not absence of navigation**; it is **uneven discoverability of already-existing control domains** and the absence of constitutional ownership for **Budget**. WP-18C should therefore begin by reusing the existing PM shell and documented entry paths, then extend naming and hierarchy on top of them rather than redesigning PM operations from scratch.