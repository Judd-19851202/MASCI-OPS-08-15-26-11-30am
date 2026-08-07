# WP-18C8 Security and Data Protection

Date: 2026-08-07
Result: PASS

## Access control

- PM earned-value routes require PM portal auth and project scope.
- Executive/Admin earned-value routes require admin + directory auth.
- Unauthenticated PM earned-value access returned `401` with `portal authentication required` during closeout proof.
- Edit authority for budget trust-line linkage stayed on the PM/project-controls lane only.

## Data protection

- No new secrets, URLs, or credentials were hardcoded.
- Backend continues reading environment values from the protected `.env` contract.
- Mongo responses are sanitized and do not expose raw `_id` values in the new C8 payloads.
- C8 exports are route-authenticated and scoped to a single project.

## Truth safety

- Receipt-based actual costs are explicitly labeled as governed linkage, not silent ERP truth.
- No AI-generated value becomes truth inside C8.
- No executive-only hidden formula branch exists.

## Deployment security result

`deployment_agent` reported PASS with no deployment blocker, no hardcoded secret, and environment-variable usage preserved.