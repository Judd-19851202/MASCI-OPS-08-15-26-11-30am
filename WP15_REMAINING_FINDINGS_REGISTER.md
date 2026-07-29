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
| RG-008 | Backend governance migration | `field_memory.py` now routes read/write/resolve authority through Enterprise Governance permissions | Verified Fixed |
| RG-009 | Backend governance migration | `photo_governance.py` now routes read/manage authority through Enterprise Governance permissions | Verified Fixed |
| RG-010 | Backend governance migration | `operational_constraints.py` now routes read/manage authority through Enterprise Governance permissions | Verified Fixed |
| RG-011 | Backend governance migration | `document_expirations.py` now routes read/manage authority through Enterprise Governance permissions and permission-derived category scope | Verified Fixed |
| RG-012 | Backend governance migration | `employee_records.py` now derives lane access from Enterprise Governance permissions instead of route-local role checks | Verified Fixed |
| RG-013 | Backend governance migration | `employee_lifecycle.py` now resolves its HR/Admin write gate through Enterprise Governance permissions | Verified Fixed |
| RG-014 | Backend governance migration | `transportation_dispatch_gate.py` now derives preview/override authority from Enterprise Governance permissions | Verified Fixed |
| RG-015 | Backend governance migration | `operations_center.py` now derives PM project scope from governance context rather than inline role branching | Verified Fixed |

## Residual Legacy Findings (Authoritative Scanner Output = 1)
| Finding ID | File | Scanner symbol | Classification | Rationale |
|---|---|---|---|---|
| RL-001 | `backend/routes/asset_documents.py` | `_require_asset_admin` | Blocked | Mutation routes still rely on route-local asset-admin authorization instead of Enterprise Governance policy evaluation. |

## Special-Case Infrastructure
- Scanner currently records **52** special-case infrastructure items.
- These are documented manual-review surfaces, not hidden debt.
- Examples include projection metadata, visibility projectors, upload partitions, and other non-canonical-but-non-blocking infrastructure seams.

## Current Determination
- Manual builder backlog: **closed**
- Category F uncertainty: **0**
- Residual constitutional blocker: **1 legacy-migratable backend finding remains**