# WP16 Active Defect Log

Date: 2026-07-29

## Directive note
These defects are documented only in this phase. No runtime fixes are authorized under the current read-only audit directive.

| ID | Surface / route | Current behavior | Evidence | Audit status | Notes |
| --- | --- | --- | --- | --- | --- |
| WP16-DEF-001 | HR notifications scope (known from handoff) | `/api/notifications` returns 403 on some HR pages. Exact route set remains unresolved in this phase. | Handoff summary + prior QA note | OPEN / DOCUMENTED ONLY | User explicitly instructed to document, not fix. |
| WP16-DEF-002 | `/hr` | HR overview rendered, but capture log recorded repeated `403` responses from `/api/hr/employee-completeness`. | `/root/.emergent/automation_output/20260729_193849/console_20260729_193849.log` + `WP16-EVID-HR-HOME.jpeg` | OPEN / DOCUMENTED ONLY | Route counted as `BLOCKED` in coverage because live data calls failed during audit. |
| WP16-DEF-003 | `/hr/employees` | Employee list rendered shell/chrome, but capture log recorded `403` from `/api/hr/employees/facets` and `/api/hr/employees?bucket=active`. | `/root/.emergent/automation_output/20260729_193849/console_20260729_193849.log` + `WP16-EVID-HR-EMPLOYEES.jpeg` | OPEN / DOCUMENTED ONLY | Route counted as `BLOCKED` in coverage because live data calls failed during audit. |
| WP16-DEF-004 | `/dispatch-portal` | Dispatch home rendered, but capture log recorded `401` responses from `/api/integrations/maintainx/defect-coverage?sample_limit=1&since_days=60`. | `/root/.emergent/automation_output/20260729_194003/console_20260729_194003.log` + `WP16-EVID-DISPATCH-HOME.jpeg` | OPEN / DOCUMENTED ONLY | Screen remained visible during capture; recorded here as an active backend-dependent defect. |