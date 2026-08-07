# WP18C7 Resource Forecast Evidence

## Authority
- `services.project_operational_intelligence`

## Families carried into C7
- crews
- equipment
- materials
- vendors
- subcontractors

## Model behavior
- Reuses governed resource productivity already tied to work-block evidence.
- Returns `insufficient_evidence` when productivity is not present.
- FL view exposes only constrained crew/material emphasis.

## Runtime proof
- Response keys confirmed in PM/Admin workspace payloads.
- FL endpoint returns `field_summary`, `production`, `commitments`, `schedule`, `drivers`, `constraints`, and `confidence` slices.
