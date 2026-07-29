# Canonical Request Lifecycle

Date opened: 2026-07-29
Status: Draft in active verification

## 1. Purpose
MASCI OPS requires one constitutional request lifecycle so that business authorization is owned only by Enterprise Governance, while authentication and session validation remain infrastructure concerns. This prevents alternate portal-specific authorization paths, hidden client downgrades, and inconsistent governed behavior.

## 2. Scope
### Governed requests
- Shared governed reads and writes across Admin, PM, HR, Safety, Shop, Dispatch, and Field Leadership portals
- Cross-portal dashboard, search, export, PO, task, notification, cost-code, safety, operations, and project-health surfaces

### Infrastructure-only or public requests
- Health/version endpoints
- Login/bootstrap endpoints before a directory session exists
- Token minting and logout endpoints
- Transport and request-integrity checks

## 3. Responsibility boundaries
- **Authentication**: validates credentials against the authoritative identity store.
- **Directory Session Context**: proves the request belongs to a valid directory-bound logical session where applicable.
- **Identity resolution**: resolves the authenticated actor into a canonical governance input shape.
- **Tenant resolution**: determines tenant context without making business-authorization decisions.
- **Portal context**: determines which portal token and portal identity are acting.
- **Enterprise Governance**: determines what the authenticated identity may do.
- **Business logic**: performs the actual read or mutation after governance approval.
- **Trust Spine**: persists required governed operational evidence where applicable.
- **Audit**: records privileged actions and verification trails.
- **Observability**: records privacy-safe operational telemetry.

## 4. Canonical lifecycle diagram
### Success flow
Client request construction
→ required portal token + directory session context (when applicable)
→ request-integrity / transport controls
→ authentication
→ directory session validation
→ canonical identity resolution
→ tenant resolution
→ portal context resolution
→ Enterprise Governance evaluation
→ business logic
→ Trust Spine evidence (if required)
→ audit / response

### Denial flow
Client request construction
→ authentication or directory-session failure → 401
or
→ authenticated + resolved identity
→ Enterprise Governance denial → 403

## 5. Client request contract
For governed first-party API requests, the canonical client path must consistently determine and provide:
- applicable portal token
- `X-Directory-Token` when the portal session is directory-bound
- content type and correlation/request identifiers when required
- idempotency data for governed mutations when applicable

The client builder must not guess business permissions.

## 6. Directory Session Context
### Definition
Directory Session Context is the verified link between a portal token and the authenticated directory session for the same logical user session.

### Current transport
- `X-Directory-Token` is the current transport mechanism.

### Current binding model
- Directory sessions are created in `directory_sessions`.
- Portal session rows are stored in `session_activity`.
- When a portal token is minted through the multi-portal or directory-grant path, `session_activity.directory_session_token_hash` binds that portal token to the active directory session.

### Failure behavior
- Missing required directory context: request fails with 401.
- Mismatched directory context: request fails with 401.
- Expired or revoked directory context: request fails with 401.

## 7. Governance decision contract
Governance input must include:
- canonical actor identity
- resolved portal/role context
- action key
- resource metadata
- request context

Governance output must include:
- allow/deny decision
- policy identifier and version
- explanation
- identity snapshot
- decision metadata suitable for audit/evidence persistence

## 8. Evidence contract
Governed decisions should preserve, where applicable:
- `decision_id`
- `correlation_id`
- `causation_id`
- `policy_version`
- `identity_snapshot`
- explanation / reason
- Trust Spine reference(s)

## 9. Failure semantics
- `400`: malformed request
- `401`: authentication or directory-session-context failure
- `403`: authenticated but denied by Governance
- `404`: inaccessible or nonexistent resource according to documented concealment policy
- `409`: governed conflict
- `422`: validation failure
- `429`: rate limit
- `5xx`: unexpected service failure

## 10. Token and session lifecycle
- Credentials are verified by the authoritative authentication system.
- Portal tokens are minted per portal store or via directory-grant paths.
- Directory sessions are minted separately and may bind multiple portal tokens.
- Revocation/logout clears session state; password change invalidates bcrypt-bound portal tokens.

## 11. Cross-portal requests
One authenticated identity may legitimately access shared endpoints through multiple granted portal contexts, but all governed access must still pass through the same authentication → directory context → identity resolution → governance chain.

## 12. Service identities
Service and background identities remain out of scope for this batch and must be documented before any exception is approved.

## 13. Offline and synchronization behavior
Any queued governed action must preserve identity, timestamp, and reevaluation requirements before mutation. No alternate offline authorization path is permitted.

## 14. Security requirements
- no bypasses
- no weaker fallback authorization path
- no default identities
- no cross-tenant context reuse
- no token forwarding to untrusted origins

## 15. Testing requirements
- unit tests for session validation and governance evaluation
- integration tests for cross-portal lifecycle
- browser verification for governed flows
- security / chaos / regression testing before certification

## 16. Migration rules
- converge clients onto canonical scoped-auth-header builders
- converge backend authorization onto Enterprise Governance
- preserve existing identities and credentials while migrating

## 17. Future extension rules
Any new feature package must integrate through the same canonical authentication-to-governance lifecycle and may not introduce alternate governed request paths.

## Constitutional Principles Preserved
- Single Governance Authority Principle
- Policy Before Permission Principle
- Explainable Authorization Principle
- Governance Determinism Principle
- Immutable Governance History Principle
- Identity Snapshot Principle
- Trust Spine Evidence Principle
- Canonical Request Lifecycle Principle
- Directory Session Context Principle
- Infrastructure Separation Principle
- No Authorization Downgrade Principle
- No Dark Authorization Principle
- Governance Regression Prevention Principle
- Fail-Closed Certification Principle
- Existing Identity Continuity Principle