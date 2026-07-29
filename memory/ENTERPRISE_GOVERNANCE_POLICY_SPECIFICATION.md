# Enterprise Governance Policy Specification

Initial versioned policies are defined in `/app/backend/services/enterprise_governance.py`.

## Initial verified policies

- `operational_case_close_policy`
- `evidence_export_policy`
- `schedule_change_policy`
- `forecast_approval_policy`
- `baseline_protection_policy`

## Policy rules

Policies currently evaluate combinations of:

- required permissions
- project access boundary
- approval flow requirement
- separation-of-duties rule set
