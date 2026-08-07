# WP18C7 Commitment Model Contract

## Storage
- Collection: `project_forecast_commitments`
- Source-preserved PO commitments are read-only derived rows and are not written back into the manual collection.

## Lifecycle states
- `proposed`
- `committed`
- `at_risk`
- `missed`
- `met`
- `revised`
- `cancelled`

## Families
- `labor_crew`
- `equipment`
- `materials`
- `vendor_subcontractor`
- `milestone_quantity`

## Required behavior
- PM can create/update scoped manual commitments.
- Derived PO commitments remain read-only.
- History entries append on lifecycle change and note update.
- Commitments compare against governed production/resource/receipt evidence.

## APIs
- `POST /api/pm/project-controls/projects/{project_number}/forecasting/commitments`
- `PATCH /api/pm/project-controls/projects/{project_number}/forecasting/commitments/{commitment_id}`
