# WP15 Request Lifecycle Convergence Report

Last updated: 2026-07-29
Status: Verified for current governed surfaces

## Current Metrics
- Manual governed header builders: **0**
- Canonical request-builder sites: **23 / 50 = 46.0%**
- Category F lifecycle uncertainty: **0**

## Verified Convergence Achieved
- The final 20 manual governed frontend builders were converged onto `buildScopedPortalAuthHeaders(...)` or a canonical equivalent.
- Shared infrastructure and mixed-portal components were prioritized first during the closeout wave.
- Cross-portal governed requests now preserve `X-Directory-Token` correctly.
- Missing directory-session context denial verified (`401`).
- Mismatched directory-session context denial verified (`401`).
- Explicit expired directory-session fixture verified (`200` before expiry → `401` after expiry mutation).
- Frontend targeted regression passed via QA run `iteration_71.json`.
- Independent backend verification confirmed no 401 storm or sign-in loop regression across sequential governed API checks.

## Interpretation of 46.0% Adoption
- This metric is **not** a manual-builder backlog count.
- The scanner counts explicit scoped-builder callsites, while some first-party requests now rely on canonical axios/fetch/xhr interceptor plumbing rather than per-call inline builders.
- The constitutional requirement for this phase was to eliminate **manual governed header construction**. That requirement is satisfied.

## Constitutional Position
- No alternate first-party manual governed request-construction path remains in the current scan.
- The canonical request lifecycle (`portal token + bound directory token`) is enforced on governed admin and PM surfaces.
- Public/bootstrap endpoints remain outside governed-builder requirements where architecturally appropriate.

## Residual Notes
- Future lifecycle hardening can increase explicit builder adoption further, but this is no longer a manual-construction defect class.