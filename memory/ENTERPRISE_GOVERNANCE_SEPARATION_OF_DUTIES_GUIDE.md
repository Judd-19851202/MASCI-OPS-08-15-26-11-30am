# Enterprise Governance Separation of Duties Guide

Separation rules are registry-controlled in `/app/backend/services/enterprise_governance.py`.

## Initial verified rules

- `creator_cannot_close_without_override_review`
- `audit_closer_separation`
- `submitter_cannot_self_approve`
- `baseline_approver_cannot_be_requestor`
- `override_requestor_cannot_self_approve`
