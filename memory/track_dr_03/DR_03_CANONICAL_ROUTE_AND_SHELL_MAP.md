# DR-03 Canonical Route and Shell Map

## Current implemented state
- `/daily/new` -> `DailyReportRouter` -> `NewDailyReportV3`
- `/daily/submit` -> `DailyReportRouter` -> `NewDailyReportV3`
- `/daily-report/v2` -> redirect away from numbered authoring flow

## Canonical authoring component
- `frontend/src/pages/NewDailyReportV3.jsx`

## Route drift removed
- Hidden feature flag shell switching removed from `DailyReportRouter`

## Remaining open item
- DR-03 final criterion requires one canonical route with redirects from competing authoring routes.
- Current checkpoint has **one canonical shell** but still **two live creation routes**.
