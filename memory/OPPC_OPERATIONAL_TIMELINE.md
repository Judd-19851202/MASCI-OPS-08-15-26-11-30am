# OPPC Operational Timeline

## Canonical rule

The operational timeline is a visualization of Trust Spine history. It is **not** a new database.

## Repository ownership

- Existing timeline route: `/app/backend/routes/operational_timeline.py`
- Trust Spine event owner: `/app/backend/lib/trust_spine.py`
- OPPC route emitters: `/app/backend/routes/oppc_execution.py`

## Timeline coverage now supported for OPPC

- Created
- Modified
- Submitted
- Approved
- Executed
- Daily production
- Quantity updates
- Payroll updates
- Variance review started
- Variance cause recorded
- Variance review completed
- Recovery required
- Variance closed
- Executive review visibility

## Architectural proof

- No new timeline table was introduced.
- OPPC extends the Trust Spine event vocabulary and reuses existing timeline visualization architecture.
