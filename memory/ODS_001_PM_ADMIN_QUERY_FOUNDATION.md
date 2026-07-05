# ODS-001 · PM / Admin Query Foundation

Additive `/api/ods/*` read surface. Auth gate is inherited from the platform's shared FastAPI middleware; DR-V2 remains feature-flag gated.

## Read endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /api/ods/meta` | provider + gateway + feature-flag state (safe for admin telemetry) |
| `GET /api/ods/facts?project_id=&fact_type=&date_from=&date_to=&limit=` | list current facts, filtered |
| `GET /api/ods/projects/{project_id}/summary?date_from=&date_to=` | cross-fact-type project rollup |
| `GET /api/ods/snapshots?project_id=&date=&window=day` | precomputed snapshot |
| `GET /api/ods/projects/{project_id}/config` | operational blueprint |

## Write / admin endpoints

- `POST /api/ods/snapshots/recompute` — regen a snapshot.
- `PUT  /api/ods/projects/{project_id}/config` — update cost-code blueprint.
- `POST /api/ods/ingest/dr-v2/{report_id}` — regen spine from a DR-V2 draft.

## Boundaries

- All endpoints degrade gracefully when `ODS_ENABLED=false` (return `enabled: false`) — never crash.
- Every read scoped by `tenant_id="masci"` (single tenant today; multi-tenant enforcement point reserved).
- No cross-project reads without an explicit project_id — prevents accidental cross-project leakage.
- Heavy aggregations never run on the hot read path; consumers must read snapshots.

## Future

- Add `admin_summary` endpoint aggregating across snapshots (P1).
- Add `pm_brief` endpoint that dispatches a `pm_brief` task through the AI Gateway (P1).
- Add `executive_brief` endpoint (P2).
