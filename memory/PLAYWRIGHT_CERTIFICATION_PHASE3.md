# PLAYWRIGHT_CERTIFICATION_PHASE3

Status: governance artefact restored for Sigma-III deployment gate.

## Purpose
- Declares that browser-level certification remains a required operator stage outside static GitHub checks.
- Points operators to the live preview validation flow enforced by `scripts/pre_deploy_check.sh`.

## Operator acknowledgement
- Static CI alone is insufficient for production approval.
- Playwright/browser coverage must be executed against preview before deploy.
- Any browser failure is a hard deployment stop until resolved.
