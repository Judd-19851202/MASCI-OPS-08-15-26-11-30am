# DR-03 Canonical Route and Shell Map

## Current implemented state
- `/daily/submit` -> `DailyReportRouter` -> `NewDailyReportV3`
- `/daily/new` -> redirect to `/daily/submit`
- `/reports/daily/new` -> redirect to `/daily/submit`
- `/daily-reports` -> redirect to `/daily/submit`
- `/daily-report/v2` -> redirect to `/daily/submit`
- `/daily/v1`, `/daily/v2`, `/daily/v3`, `/daily-report/v1`, `/daily-report/v3` -> redirect to `/daily/submit`

## Canonical authoring component
- `frontend/src/pages/NewDailyReportV3.jsx`

## Route drift removed
- Hidden feature flag shell switching removed from `DailyReportRouter`

## Route inventory

### Canonical creation route
- `/daily/submit`

### Retired creation routes
- `/daily/new`
- `/reports/daily/new`
- `/daily-reports`
- `/daily-report/v2`
- `/daily/v1`
- `/daily/v2`
- `/daily/v3`
- `/daily-report/v1`
- `/daily-report/v3`

### Historical read routes retained
- `/daily/:id`
- approved-report list + PDF routes remain intact via backend read paths

### Certification-only routes retained
- none changed by this continuation checkpoint

### Unreachable/dead shells
- direct routed V1/V2 numbered authoring shells: unreachable from active runtime
