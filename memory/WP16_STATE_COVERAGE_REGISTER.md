# WP16 State Coverage Register

Date: 2026-07-29

## Phase 1 status
- No dedicated state-triggering pass has been executed yet.
- Current evidence only confirms route-default shell/state on 16 screenshot-backed routes plus defect-limited partial-data states on 3 routes.

## Current exact totals
| State category | Exact total exercised | Note |
| --- | ---: | --- |
| Default route / shell state | 16 | Screenshot-backed route openings. |
| Partial-data state | 3 | `/hr`, `/hr/employees`, `/dispatch-portal`. |
| Empty state | 0 | Not yet exercised directly. |
| Loading state | 0 | Not yet exercised directly. |
| Skeleton state | 0 | Not yet exercised directly. |
| Success state | 0 | Not yet exercised directly. |
| Warning state | 0 | Not yet exercised directly. |
| Validation-failure state | 0 | Not yet exercised directly. |
| Permission-denied state | 0 | Not normalized as a route-level screen state in current evidence. |
| Authentication-expired state | 0 | Not yet exercised directly. |
| API-error state | 2 blocked + 1 partial | HR blocked routes + Dispatch partial route. |
| General runtime-error state | 0 | Not yet exercised directly. |
| No-results / filtered-empty / offline / reconnection / mobile-overflow states | 0 each | Deferred to later evidence-expansion phases. |

## Seed evidence rows
| State evidence ID | Screen / route | State type | Exercised? | Screenshot | Notes |
| --- | --- | --- | --- | --- | --- |
| STATE-SEED-admin | `/admin` | Default route / shell state | Yes | `WP16-EVID-ADMIN-HOME.jpeg` | Baseline admin shell visible. |
| STATE-SEED-pm | `/pm` | Default route / shell state | Yes | `WP16-EVID-PM-HOME.jpeg` | Baseline PM shell visible. |
| STATE-SEED-hr | `/hr` | Partial-data / blocked API state | Yes | `WP16-EVID-HR-HOME.jpeg` | 403 on employee-completeness prevented full inspection. |
| STATE-SEED-hr-employees | `/hr/employees` | Partial-data / blocked API state | Yes | `WP16-EVID-HR-EMPLOYEES.jpeg` | 403 on employee facets/active bucket prevented full inspection. |
| STATE-SEED-dispatch-portal | `/dispatch-portal` | Partial-data state | Yes | `WP16-EVID-DISPATCH-HOME.jpeg` | MaintainX-backed panel limited by 401. |
| STATE-SEED-daily-submit | `/daily/submit` | Default route / form state | Yes | `WP16-EVID-PUBLIC-DAILY-FORM.jpeg` | Public daily report authoring shell visible. |
