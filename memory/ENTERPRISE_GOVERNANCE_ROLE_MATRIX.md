# Enterprise Governance Role Matrix

Initial registry-backed roles are defined in `/app/backend/services/enterprise_governance.py`.

## Verified initial roles

- `system_administrator`
- `executive`
- `project_manager`
- `hr`
- `safety`
- `shop`
- `dispatch`
- `field_leadership`

## Notes

- roles are configurable through the governance registry, not hard-coded across modules
- role semantics are evaluated alongside project scope, policy, approvals, delegation, and separation rules
