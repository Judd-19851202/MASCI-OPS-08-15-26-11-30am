# FORGEDOPS · ATLAS PERMISSION ANALYSIS

**Status:** 🟡 **PRE-EXECUTION** · evidence-based.

## Current grants (inferred from runtime probes)
`admin_db_user` has (at minimum) `readWriteAnyDatabase` because:
- `client["masci_safety_preview"].equipment_master.count_documents({})` → 693 ✅
- `client["masci_safety"].equipment_master.count_documents({})` → 596 ✅
- `client["masci_safety"].list_collection_names()` → 159 cols ✅
- `client["admin"].command("usersInfo")` → ❌ Denied (so does NOT have `userAdmin*`).

## Risk classification
| Risk | Level | Mitigation today |
|---|---|---|
| Preview agent reads/writes prod | 🔴 CRITICAL | App code uses `client[DB_NAME]` — env-pinned. **Credential not scoped.** |
| Preview agent escalates to user admin | 🟢 NONE | `userAdmin*` not granted. |
| Production credential reads/writes preview | 🔴 UNKNOWN | Assumes same `admin_db_user`; operator must confirm. |
| Schema-level mutations | 🟡 CAPABLE (`dbAdminAnyDatabase` likely) | Not exercised by app code. |

## Target grants
| User | role array |
|---|---|
| `masci_preview_user` | `[{ role: "readWrite", db: "masci_safety_preview" }]` |
| `masci_prod_user` | `[{ role: "readWrite", db: "masci_safety" }]` |

NO `readWriteAnyDatabase`. NO `atlasAdmin`. NO `dbAdminAnyDatabase`. NO `userAdmin*`. NO cluster-wide privileges of any kind.

## Verification command (operator runs from Atlas Admin UI or `mongosh` post-creation)
```
use admin
db.getUser("masci_preview_user")     // expect roles: [{role:"readWrite", db:"masci_safety_preview"}]
db.getUser("masci_prod_user")        // expect roles: [{role:"readWrite", db:"masci_safety"}]
```
