# WP15 Remaining Findings Register

Last updated: 2026-07-29
Status: Reconciled for final determination

## Verified Fixed in This Closeout Wave
| Finding ID | Area | Resolution | Status |
|---|---|---|---|
| RG-001 | Frontend request lifecycle | Final 20 manual governed builders converged to canonical scoped headers | Verified Fixed |
| RG-002 | Backend scope drift | `field_leadership.py` unreachable PM scope helper retired | Verified Fixed |
| RG-003 | Backend scope drift | `operations_map_contract.py` migrated from `compute_pm_scope` to enterprise governance scope | Verified Fixed |
| RG-004 | Scanner normalization | Canonical governance scope adapters are now counted as canonical, not legacy | Verified Fixed |
| RG-005 | Scanner normalization | ODR visibility projector and legacy-import upload partition moved to special-case infrastructure classification | Verified Not Applicable |
| RG-006 | Security evidence | Session-expiry, negative lifecycle, and recovery verification expanded | Verified Fixed |
| RG-007 | Override evidence | Emergency override exercised and independently verified | Verified Fixed |

## Residual Legacy Findings (Authoritative Scanner Output = 9)
| Finding ID | File | Scanner symbol | Classification | Rationale |
|---|---|---|---|---|
| RL-001 | `backend/routes/asset_documents.py` | `_require_asset_admin` | Blocked | Mutation routes still rely on route-local asset-admin authorization instead of Enterprise Governance policy evaluation. |
| RL-002 | `backend/routes/operations_center.py` | `operations_center` | Accepted Risk | Residual inline PM narrowing is read-only and already derives from governed context; no privilege expansion observed in testing. |
| RL-003 | `backend/routes/operational_constraints.py` | `_can_write` | Blocked | Write authority remains route-local role matrix. |
| RL-004 | `backend/routes/document_expirations.py` | `_scope` | Accepted Risk | Read-only category partition remains route-local; no write authority, but not yet policyized. |
| RL-005 | `backend/routes/photo_governance.py` | `_can_write` | Blocked | Write authority remains route-local role matrix. |
| RL-006 | `backend/routes/field_memory.py` | `_can_write_subject` | Blocked | Subject-level write permissions remain route-local and materially authoritative. |
| RL-007 | `backend/routes/employee_records.py` | `_actor_can_read_lane` | Blocked | Lane visibility and ownership checks remain route-local authority. |
| RL-008 | `backend/routes/employee_lifecycle.py` | `require_hr_or_admin` | Blocked | HR/Admin mutation gate is still local to the router. |
| RL-009 | `backend/routes/transportation_dispatch_gate.py` | `_is_override_authorized` | Blocked | Dispatch override authorization remains inline and has not yet been moved to governance policy. |

## Special-Case Infrastructure
- Scanner currently records **52** special-case infrastructure items.
- These are documented manual-review surfaces, not hidden debt.
- Examples include projection metadata, visibility projectors, upload partitions, and other non-canonical-but-non-blocking infrastructure seams.

## Current Determination
- Manual builder backlog: **closed**
- Category F uncertainty: **0**
- Residual constitutional blocker: **9 legacy-migratable backend findings remain**