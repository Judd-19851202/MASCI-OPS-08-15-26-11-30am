# WP18CX5 Production Scope — Release 1.0

## Executive scope rule
Release 1.0 includes only functionality that:
1. is intended for the initial production deployment, and
2. has evidence-backed runtime certification.

Anything lacking runtime scope, runtime proof, or production-readiness evidence is classified as a **Deferred Release Module** and does **not** block Release 1.0 GO.

## Runtime evidence basis
- `/app/test_reports/iteration_117.json`
- `/app/test_reports/iteration_118.json`
- `/app/test_reports/iteration_119.json`
- `/app/test_reports/iteration_120.json`
- `/app/test_reports/iteration_121.json`

## Included in Release 1.0

### Portals and dashboards
- Executive Leadership shared portal
  - Executive Overview
  - Executive Operations Dashboard
- Admin governance portal
  - Project Controls Standards
  - Project Budget Review
  - Project Schedule Review
  - Operations Dashboard Review
  - Notifications Digest
- PM portal
  - Project Controls
  - Project Budget
  - Project Schedule
  - Project Performance
  - Daily Job Report review/detail
- Safety portal
  - Safety Hub V2
- Dispatch portal
  - Dispatch Hub V2
- Shop portal
  - Shop Hub V2
- Equipment operations
  - Equipment Dashboard
- HR / Payroll portal
  - HR Hub V2
  - Payroll Variance
- Field Leadership portal
  - Field Leadership Portal Dashboard

### Included operator roles
- Executive Leadership shared role family
  - President
  - COO
  - VP Operations
  - Area Manager
  - Project Executive
- Project Manager
- Field Leadership role family
  - Superintendent
  - Foreman
- Safety
- Dispatch
- Shop
- Equipment
- HR
- Payroll

### Included runtime communications and outputs
- Daily Job Report Print / PDF flow
- Daily Job Report email flow
- PM Project Budget export
- PM Project Schedule download export
- HR Payroll Variance CSV export
- Notifications Digest

### Included runtime decision support / AI-like operator outputs
- PM Project Performance recommendations and explainability blocks
- Executive Overview attention verdict / threshold-driven decision support

### Included supported production device classes
- iPhone-class smartphone width (`390px` runtime proof)
- Android-class smartphone width (`412px` runtime proof)
- iPad-class tablet width (`768px` runtime proof)
- Windows-class laptop / desktop web experience (`1920px` runtime proof)

## Deferred Release Modules

### 1. Survey Portal / Survey Workflow Family
- Status: **Deferred Release Module**
- Why deferred: no dedicated Survey route, login, workflow, or operator surface exists in the current preview runtime.
- Evidence: `iteration_119`, `iteration_121`
- Future certification path: standalone Survey module certification before any Survey activation in a later release.

### 2. Executive Monday Briefing PDF generation
- Status: **Deferred Release Module**
- Why deferred: briefing surface exists, but runtime data was not generated; PDF button could not be fully certified with generated content.
- Evidence: `iteration_121`
- Future certification path: executive briefing PDF runtime certification when generated briefing data is available.

### 3. PM Project Performance CSV export
- Status: **Deferred Release Module**
- Why deferred: export button exists but runtime proof was not completed because project selection precondition was not satisfied during final scope testing.
- Evidence: `iteration_121`
- Future certification path: project-selected PM Project Performance export runtime certification before activation in a later release.

### 4. PM Schedule email-review queue action
- Status: **Deferred Release Module**
- Why deferred: no direct runtime route / proof was captured in final scope testing.
- Evidence: `iteration_121`
- Future certification path: PM schedule email-review runtime certification before later activation.

### 5. Daily Report dedicated AI summary family
- Status: **Deferred Release Module**
- Why deferred: no visible seeded AI summary content was available in final runtime testing.
- Evidence: `iteration_119`, `iteration_121`
- Future certification path: seeded runtime AI-summary certification before later activation.

## Explicitly outside Release 1.0
- Survey runtime workflows
- future forecasting
- future earned value
- future portfolio expansion beyond the certified executive surfaces
- future analytics not already runtime-proven in Release 1.0
- any PDF / export / email family not listed as included above

## Final Release 1.0 scope decision
Release 1.0 is **eligible for GO WITH DEFERRED MODULES** based on runtime evidence for the included scope above.