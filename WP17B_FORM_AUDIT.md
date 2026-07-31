# WP-17B Form Audit

## Counts
- Frontend form instances: `66`
- Files containing forms: `60`
- Table instances affecting form-heavy workflows: `196`

## Form families identified
| Family | Examples | Main issue | Disposition |
|---|---|---|---|
| Auth forms | `/sign-in`, portal logins, reset/change-password | Too many parallel entry patterns and message styles | `STANDARDIZE` |
| Operational capture forms | daily reports, incidents, inspections, JHA, ODR, field records | Create/submit/revise flows are functionally rich but visually inconsistent | `REFINE` |
| Admin configuration forms | governance, integrations, recovery, communications | Dense and often mixed with report tables on same surface | `MODERNIZE` |
| Historical intake / upload forms | HR/Safety/Asset historical lanes | Reachable but not clearly separated from day-to-day work | `UNHIDE` |
| Search / filter forms | hub search, queue filters, Transportation search rail | Inconsistent placement and reset behavior | `STANDARDIZE` |

## Form standard lock
- One validation voice
- One success/error pattern
- One required-field treatment
- One destructive-confirm pattern
- One upload-state pattern
- One search/filter affordance language set

## Highest-risk form debt
1. Entry-point auth forms
2. Admin config/change forms buried in report-heavy screens
3. Create/submit aliases in public/shared operational flows