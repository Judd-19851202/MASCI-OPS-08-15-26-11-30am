# Enterprise Governance Approval Framework Specification

Approval flows are centrally defined in the governance registry.

## Initial verified approval flows

- `critical_case_close`
- `sensitive_export_review`
- `schedule_change_review`
- `forecast_approval`
- `baseline_control_review`
- `emergency_override_review`

Approval requests are persisted in `enterprise_governance_approval_requests` and surfaced through `/api/admin/governance/approval-flows`.
