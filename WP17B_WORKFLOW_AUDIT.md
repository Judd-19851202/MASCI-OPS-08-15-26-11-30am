# WP-17B Workflow Audit

## Workflow classes audited
| Workflow | Primary owner | Current state | Disposition | Dependency |
|---|---|---|---|---|
| Multi-portal sign-in | Shared | Functional, but not role-first | `REBUILD` | `WP-17C`, `WP-17F` |
| Daily report capture/review | Shared + PM/Admin/HR | Mature but route-alias heavy | `STANDARDIZE` | `WP-17E` |
| Incident / CAPA lifecycle | Safety + PM + Admin | Strong business value; naming and path drift remain | `REFINE` | `WP-17E` |
| Shop recovery workflow | Shop + Dispatch | Rich and truthful, but visually dense | `SPLIT` | `WP-17E` |
| Transportation command workflow | Transportation + Dispatch | Useful but spread across dual shells and child tabs | `MERGE` | `WP-17C`, `WP-17D` |
| Historical record intake/review | HR + Safety + Asset admin | Functional, under-discoverable | `UNHIDE` | `WP-17C` |
| Admin governance / recovery operations | Admin | Powerful but hierarchically crowded | `MODERNIZE` | `WP-17C`, `WP-17D` |
| KPI/help explanation flow | Cross-portal | Present but inconsistent | `STANDARDIZE` | `WP-17F` |

## Workflow conclusions
1. The platform mostly has the workflows it needs.
2. The largest risk is not missing steps; it is route duplication, naming drift, and hierarchy inconsistency around those steps.
3. WP-17C should sequence workflow simplification after IA and nav canon are set.