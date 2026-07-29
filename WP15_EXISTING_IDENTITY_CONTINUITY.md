# WP15 Existing Identity Continuity

Date opened: 2026-07-29
Status: In progress

## Purpose
WP-15C modernization must preserve all legitimate existing MASCI OPS identities while governance and request-lifecycle convergence continue. This document records the authoritative identity sources, continuity rules, production-shaped inventory, and regression expectations.

## Constitutional Principle
### Existing Identity Continuity Principle
Governance and request-lifecycle modernization must preserve the continuity of all legitimate existing identities.

No WP-15C migration may unintentionally:
- change a username or login identifier
- change a password or password-hash algorithm semantics
- force a password reset
- split or merge legitimate identities
- remove legitimate portal membership, tenant membership, roles, or project assignments
- break directory-session binding for otherwise valid sessions
- invalidate valid accounts or legitimate access without explicit policy intent

## Authoritative Identity Sources
| Identity family | Authoritative store | Login key | Password owner | Notes |
|---|---|---|---|---|
| Directory multi-portal users | `user_directory` | `email` | `user_directory.password_hash` | Master identity + directory session authority |
| PM users | `project_managers` | `email` | `project_managers.password_hash` | Per-PM tokens remain bcrypt-bound |
| HR users | `hr_users` | `email` | `hr_users.password_hash` | Per-user portal auth |
| Shop users | `shop_users` | `email` | `shop_users.password_hash` | Per-user portal auth |
| Safety users | `safety_users` | `email` | `safety_users.password_hash` | Per-user portal auth |
| Dispatch users | `dispatch_users` | `email` | `dispatch_users.password_hash` | Per-user portal auth |
| Field Leadership users | `field_leadership_users` | `email` | `field_leadership_users.password_hash` | Per-user portal auth |

## Directory and Portal Identity Relationships
- Directory session authority is established in `directory_sessions`.
- Portal-session activity authority is established in `session_activity`.
- Directory-bound governed requests rely on `session_activity.directory_session_token_hash` linking a portal token to the active directory session.
- Current continuity model is **identity projection, not identity replacement**.
- Governance may normalize identity context for policy evaluation, but password validation remains in the authentication systems above.

## Password and Credential Compatibility
- Current password verification remains bcrypt-based across directory and portal-specific stores.
- No credential migration, password-hash rewrite, or identifier rename has been approved in WP-15C.
- Existing login identifiers remain email-based for all currently verified portal stores.
- No plaintext passwords, raw password hashes, or raw tokens are recorded in this artifact.

## Production-Shaped Identity Inventory Snapshot
Snapshot source: preview database inventory on 2026-07-29.

### Directory inventory
- `user_directory.total`: **191**
- `user_directory.disabled`: **1**
- `user_directory.super_admin`: **1**
- `user_directory.must_change_password`: **2**
- `user_directory.multi_portal`: **5**
- `user_directory.single_portal`: **156**
- `user_directory.duplicate_emails`: **0**

### Portal collection inventory
- `project_managers.total`: **23**
- `hr_users.total`: **70** (`disabled=10`)
- `shop_users.total`: **14** (`disabled=0`)
- `safety_users.total`: **11** (`disabled=7`)
- `dispatch_users.total`: **12** (`disabled=9`)
- `field_leadership_users.total`: **31** (`disabled=7`)

### Cross-identity linkage
- Portal records with email: **161**
- Portal records linked to `user_directory` by email: **161**
- Portal records unlinked to `user_directory` by email: **0**
- Directory users with any linked portal record: **155**
- Directory users without linked portal record: **36**
- Emails with multiple portal collections attached: **3**

### Session continuity snapshot
- `directory_sessions.total`: **10717**
- `session_activity.total`: **676**
- `session_activity` rows with directory binding: **20**
- `session_activity` rows without directory binding: **656**

## Existing-User Migration Rules
1. Discover current identity state before changing any authentication-sensitive path.
2. Preserve existing identifiers, password hashes, and role/project references.
3. Use governance identity projection as a read-oriented layer only.
4. Validate existing login flows after each identity-sensitive batch.
5. Remove legacy authorization only after parity is proven.

## Existing-User Regression Matrix
| User pattern | Login | Existing password | Portal access | Governance access | Directory binding |
|---|---|---|---|---|---|
| Existing Admin | Required pass | Preserved | Must pass | Correct | Verified |
| Existing PM | Required pass | Preserved | Must pass | Project-scoped | Verified |
| Existing Safety user | Required pass | Preserved | Must pass | Policy-scoped | Verified |
| Existing HR user | Required pass | Preserved | Must pass | Policy-scoped | Verified |
| Existing Dispatch user | Required pass | Preserved | Must pass | Policy-scoped | Verified |
| Existing Shop user | Required pass | Preserved | Must pass | Policy-scoped | Verified |
| Existing Field Leadership user | Required pass | Preserved | Must pass | Policy-scoped | Verified |
| Multi-portal user | Required pass | Preserved | All granted portals valid | Context-correct | Verified |
| Disabled user | Must remain denied | Unchanged | Denied | Denied | Verified |
| Delegated user | Pending | Preserved | Pending | Time-bounded | Pending |

### Additional verified continuity checks
- Incorrect PM password returns `401` and does not mutate credentials.
- Disabled directory fixture login remains denied (`401`) through multi-login and HR portal paths.
- PM portal token combined with an HR directory session returns `401`.
- PM portal token without directory context returns `401`.
- PM portal token combined with the matching PM directory session returns `200` on governed reads.
- Repeated multi-login for verified fixture identities remains idempotent.

## Known Anomalies (Recorded, not auto-fixed)
- 36 directory users currently have no linked portal collection by email.
- Only 20 active portal session rows currently carry directory binding metadata; many legacy or standalone portal sessions remain non-directory-bound.
- Distinct legacy role labels remain in shop and field leadership collections and must be preserved during convergence.

## Backup and Rollback Requirements
- Any identity-sensitive batch must be reversible and idempotent.
- Rollback must restore prior code, prior session-handling behavior, and prior projection behavior without forcing password resets.
- No irreversible credential migration is approved for WP-15C.

## Deployment Evidence
- 2026-07-29: Multi-portal governed client header path corrected to preserve directory-session context on shared governed reads.
- 2026-07-29: Existing identity inventory generated without exposing secrets.
- 2026-07-29: Shared dispatch, safety-only, FL-only, and cross-portal governed clients converged onto the canonical scoped auth-header builder without changing credentials, identifiers, or portal mappings.
- 2026-07-29: Existing PM, HR, Dispatch, Shop, Field Leadership, and multi-portal login continuity re-verified after builder and governance-scope migrations.

## Final Identity-Continuity Certification
Not yet certified. Additional portal login continuity checks and disabled-user regression checks remain required.