# FORGEDOPS · ATLAS NAMESPACE & PERMISSION ANALYSIS

**Date:** 2026-02-10 · **Status:** 🟡 **PRE-EXECUTION · OPERATOR ACTION REQUIRED**

## Namespace targets (after rotation)
- `masci_safety_preview` — preview only · accessed by `masci_preview_user`
- `masci_safety` — production only · accessed by `masci_prod_user`
- All `masci_test_*`, `masci_restore_drill_*` scratch DBs — preview-side only

## Permission matrix (target state · post-execution)
| User | DB scope | Granted role | Forbidden |
|---|---|---|---|
| `masci_preview_user` | `masci_safety_preview` ONLY | `readWrite@masci_safety_preview` | `readWriteAnyDatabase`, `atlasAdmin`, `dbAdminAnyDatabase`, `userAdmin*` |
| `masci_prod_user` | `masci_safety` ONLY | `readWrite@masci_safety` | same forbidden list |
| `admin_db_user` | n/a (deleted in Phase 6) | (none) | n/a |

## Current state (verified violation)
- `admin_db_user`: `readWriteAnyDatabase` (cluster-wide). Direct probe confirmed cross-DB read.

## Test users / scratch DBs
Preview-side scratch DBs (`masci_test_*`, `masci_restore_drill_*`) — `masci_preview_user` will not be able to access them after rotation because they are outside `masci_safety_preview`. If the platform needs them, grant `readWrite` on each individually OR consolidate them into `masci_safety_preview` as namespaced collections. **Operator decision required** — listed in the Operator Runbook as an open item.

See `ATLAS_USER_INVENTORY.md` for full evidence.
