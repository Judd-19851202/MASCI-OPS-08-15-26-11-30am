# Auth / Session Proof Guide

## Scope
- Prove the PRE-C10 auth/session/public-access contract end-to-end in preview.
- Use preview-only fixtures from `/app/memory/test_credentials.md`.
- Treat the shared super-admin account as noisy for deterministic auth proofs; prefer the stable preview-only fixtures below.

## Stable Preview Fixtures
- Unified multi-portal: `ops8-admin-pm-preview@example.com / AdminPmOps8!`
- Admin only: `ops8-admin-only-preview@example.com / AdminOnlyOps8!`
- PM: `cert.pm@example.com / CertProof2026!`
- HR: `cert.hr@example.com / CertProof2026!`
- Safety: `cert.safety@example.com / CertProof2026!`
- Dispatch: `cert.dispatch@example.com / CertProof2026!`
- Shop: `cert.shop@example.com / CertProof2026!`
- Field Leadership: `cert.foreman@example.com / CertProof2026!`

## Core Auth Contract
1. Signed-out `/` loads public home and shows Sign In.
2. Signed-out protected routes redirect to governed auth.
3. Unified sign-in with the multi-portal fixture lands correctly and grants Admin + PM access.
4. `/api/auth/me-directory` is valid before logout and invalid after logout.
5. `/api/auth/multi-logout` revokes directory + portal access server-side.
6. Browser Back after logout does not resurrect protected content.
7. Refresh after logout stays signed out.
8. No stale prior-role context leaks after switching login surfaces.
9. Public field/safety routes stay usable while signed out and must not show `Session Expired`.
10. Public draft/device continuity remains intact for public submission flows.

## Suggested Runtime Checks
- Unified flow: `/sign-in`, `/admin`, `/pm`, `/api/auth/me-directory`, `/api/auth/multi-logout`
- Public field routes: `/field`, `/daily/submit`, `/equipment/submit`, `/fleet/dvir/new`
- Public safety routes: `/safety`, `/meetings/submit`, `/incidents/report`, `/jha`, `/trench-safety/excavation/new`, `/safety/forms/equipment-issuance/new`
- Portal logins: `/pm/login`, `/hr/login`, `/safety-portal/login`, `/dispatch-portal/login`, `/shop/login`, `/leadership/login`, `/admin/login`

## Important Notes
- Do not mutate preview business records to force a green result.
- If a failure occurs, classify it first: real defect, stale oracle, preview data condition, or runtime/environment issue.
- Prefer the stable preview fixtures above for deterministic browser/auth proofs.