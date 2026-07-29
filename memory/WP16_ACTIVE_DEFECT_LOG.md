# WP16 Active Defect Log

Date: 2026-07-29

## Phase 1 checkpoint note
- No runtime fixes were attempted.
- No new route-level defects were discovered during registry/route reconciliation.
- Existing accepted defects are retained and restructured below for the evidence-expansion campaign.

| Defect ID | Affected portal | Affected routes | Affected roles | Affected components / surfaces | Evidence impact | Screen rendered? | Partially or fully blocked? | Visual review possible? | Prevents constitutional comparison? | Screenshot refs | Current status | Proposed repair phase | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WP16-DEF-001 | HR | Exact route set unresolved; observed on some HR pages | HR authenticated | Notification surfaces / notification fetch path | Limits completeness of HR notification evidence because exact route scope remains unresolved | Partially known | Partially blocked | Partially | Potentially, if notification pattern comparison becomes material | No dedicated screenshot | Open / documented only | Post-audit defect remediation | Derived from accepted handoff and prior QA evidence. |
| WP16-DEF-002 | HR | /hr | HR authenticated | HR overview dashboard / employee completeness-fed regions | Prevents full data-backed inspection of the HR overview route | Yes | Partially blocked by API failure | Yes — partial | Yes, for HR dashboard comparison breadth | WP16-EVID-HR-HOME.jpeg | Open / documented only | Post-audit defect remediation | 403 responses from `/api/hr/employee-completeness`. |
| WP16-DEF-003 | HR | /hr/employees | HR authenticated | Employee list, facets, active bucket regions | Prevents full data-backed inspection of HR employee-list behavior | Yes | Partially blocked by API failure | Yes — partial | Yes, for HR table/list comparison breadth | WP16-EVID-HR-EMPLOYEES.jpeg | Open / documented only | Post-audit defect remediation | 403 responses from `/api/hr/employees/facets` and `/api/hr/employees?bucket=active`. |
| WP16-DEF-004 | Dispatch | /dispatch-portal | Dispatch authenticated | MaintainX defect-coverage-backed panel on Dispatch home | Leaves a meaningful home-screen sub-surface partially hidden during inspection | Yes | Partially blocked by API failure | Yes — partial | Partially, for Dispatch integrations comparison | WP16-EVID-DISPATCH-HOME.jpeg | Open / documented only | Post-audit defect remediation | 401 response from `/api/integrations/maintainx/defect-coverage?sample_limit=1&since_days=60`. |
