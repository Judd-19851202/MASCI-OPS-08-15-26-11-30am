# WP-17A Security Configuration Certification

Date opened: 2026-07-31
Status: ACTIVE

## Preview repairs implemented
- effective runtime CORS policy is now the authoritative truth source for the security posture KPI
- blank `CORS_ORIGINS` no longer creates a false missing-required-env / unpinned-CORS warning when regex fallback is active and credential-safe

## Remaining
- add origin allow/deny tests at the API layer
- document exact production-approved origin set / regex policy for deployment review
