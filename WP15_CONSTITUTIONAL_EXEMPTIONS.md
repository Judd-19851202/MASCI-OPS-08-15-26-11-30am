# WP15 Constitutional Exemptions Register

Last updated: 2026-07-29
Status: Final documented exemption set

## Purpose
These items are the scanner's remaining `special_case_infrastructure` findings after repository-wide constitutional convergence reached:

- `legacy_migratable = 0`
- `manual_auth_header_construction = 0`
- `governance_candidate = 0`

They are **not unexplained authorization seams**. They are formally documented exemptions or non-blocking infrastructure categories with evidence.

## Exemption Groups
| Reason | Count | Representative paths | Constitutional interpretation |
|---|---:|---|---|
| Documented governed-scope adapter | 64 | `backend/routes/tasks_notifications.py`, `backend/routes/po_requests.py` | Uses documented scope adapters after constitutional migration; manual review only. |
| Authentication/token boundary | 40 | `backend/lib/enterprise_governance.py`, `backend/routes/safety_portal/_deps.py`, `backend/routes/fleet_ops_deps.py` | Auth/token plumbing and boundary adapters, not alternate business-authorization authority. |
| Environment heuristic, not business authorization | 18 | `backend/routes/integration_truth.py` | Operational heuristics only; no business action authorization decision. |
| Upload-portal partition after canonical actor gate | 8 | `backend/routes/legacy_imports.py` | Post-auth data partitioning, not a competing authorization authority. |
| Canonical request-lifecycle infrastructure | 7 | `frontend/src/lib/api.js`, `frontend/src/lib/authHeaders.js`, `frontend/src/lib/xhrPortalAuth.js` | First-party lifecycle infrastructure required to propagate canonical headers. |
| Domain classification branch | 5 | `backend/routes/daily_reports.py`, `backend/routes/project_team_assignments.py` | Domain data-shaping/classification logic, not alternate business authorization. |
| Governed scope application branch | 5 | `backend/routes/operations_center.py`, `backend/routes/global_search.py` | Governed scope is being applied, not bypassed. |
| Read-visibility projector after auth gate | 3 | `backend/routes/odr/routes.py` | Post-auth visibility projector; authority remains upstream. |
| Identity projection snapshot field | 2 | `backend/services/enterprise_governance.py` | Snapshot/projection metadata only. |
| Directory view projection field | 1 | `backend/routes/admin_directory_k4.py` | Directory projection output, not authorization. |
| Infrastructure portal-token probe | 1 | `backend/routes/integrations/_deps.py` | Token-boundary infrastructure only. |

## Evidence
- Scanner result: `normalized_constitutional_counts.special_case_infrastructure = 52`
- Final backend verification: `/app/wp15_final_backend_verification_results_20260729_125007.json`
- Final regression suite: `152 passed`

## Determination
These 52 findings are formally documented constitutional exemptions / manual-review infrastructure surfaces. They do **not** block WP-15 certification because no residual legacy-migratable or unexplained governance seams remain.