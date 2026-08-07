# WP18C7 Forecasting Model Contract

## Service contract
- Service: `backend/services/project_forecasting_commitments.py`
- Primary method: `get_project_forecasting_workspace(db, project_number, actor, audience, note)`

## Forecast families
1. **Schedule**
   - likely finish date
   - committed finish date
   - slipped activity register
   - scenario comparison
2. **Production**
   - remaining quantity by unit
   - next-day / next-7-day quantity outlook
   - required and recovery pace
3. **Resources**
   - crews
   - equipment
   - materials
   - vendors / subcontractors
4. **Authorized cost scope**
   - projected remaining cost
   - commitment exposure
   - projected final cost floor

## Output invariants
- `authority_boundaries` always present.
- `versioning` always present.
- Forecast family status must be `ready`, `complete`, or `insufficient_evidence`.
- Confidence bands must be ranges, not single-point fake precision.

## Failure behavior
- Missing governed upstream inputs produce `insufficient_evidence`.
- Open constraints lower confidence but do not silently mutate operator commitments.
