# WP18CY.3 Change Without Deployment Root Cause

## Exact conclusion
No direct evidence of a new undeclared application deployment was found that introduced the Daily Report workflow defect.

## Proven mechanism
The observed production behavior was a combination of:
1. **latent live implementation drift already present in the deployed release** — production Daily Reports were already routing through the OPPC communication path instead of the legacy `auto_email_dispatch:daily-report` proof path;
2. **observability/parity drift** — `/api/admin/daily-report-delivery/forensics` only trusted the legacy Daily Report dispatch stages and therefore misclassified OPPC-controlled Daily Reports as `trust_spine_missing_notification_stage` even when production OPPC communications showed provider acceptance;
3. **attestation drift** — production deployment history repeatedly recorded `runtime_commit_does_not_match_intended_release` and `frontend_artifact_identity_unavailable`, proving release identity evidence was degraded even while runtime health stayed green.

## Evidence
- Production revision remained stable during this run: backend commit `bd9bdd2012c4f2e31b57d7390218b20c361c6dcc`, source hash `665ea6071d75dd046905a35dfe8dcea4`.
- Controlled production Daily Report `DR-2026-00449` saved successfully.
- Production `/api/admin/daily-report-delivery/forensics` claimed no email attempt.
- Production `/api/admin/operations-control/communications` for the same OPPC workflow showed a real email transport with provider acceptance.

## Classification
- **data-triggered latent defect**
- **observability drift**
- **release-attestation drift**
