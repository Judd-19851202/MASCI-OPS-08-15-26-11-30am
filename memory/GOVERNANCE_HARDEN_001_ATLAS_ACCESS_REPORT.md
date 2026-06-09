# GOVERNANCE-HARDEN-001 · Workstream A · Atlas Access Report

```
Environment    : production + preview (same Atlas cluster)
Access Level   : prod-DB-read · preview-DB-read+write · admin.system.users (find only)
Evidence Source: direct mongo `connectionStatus` + `find` on `admin.system.users`
Confidence     : VERIFIED for all sections below
```

---

## §A.1 · Atlas user inventory (live · 2026-06-09)

The Atlas cluster `masci-prod.1nduwmg.mongodb.net` has **7 user accounts**. Five are MongoDB-Cloud (Atlas/MMS) internal automation agents; **two are customer-controlled and both have unrestricted cluster-wide access.**

| # | User | Auth DB | Roles | Class | Notes |
|---|---|---|---|---|---|
| 1 | `admin_db_user` | admin | **`atlasAdmin@admin`** | **Customer** (held by THIS fork) | This is the user in the preview pod's `MONGO_URL`. `atlasAdmin` = `readWriteAnyDatabase` + `dbAdminAnyDatabase` + `userAdminAnyDatabase` + `clusterAdmin` + `backup` + `restore`. Maximum customer-level privilege. |
| 2 | `Password` | admin | **`readWriteAnyDatabase@admin`** | **Customer** (holder unknown) | Suspicious name; unrestricted read+write across every DB. Could be a relic or a second active credential. |
| 3 | `mms-automation` | admin | backup, clusterAdmin, directShardOperations, dbAdminAnyDatabase, MongodbAutomationAgentUserRole, userAdminAnyDatabase, readWriteAnyDatabase, restore | Atlas-internal | MongoDB Cloud Manager automation. Cannot be removed by customer. |
| 4 | `mms-monitoring-agent` | admin | clusterMonitor, directShardOperations | Atlas-internal | Health metrics. |
| 5 | `mms-backup-agent` | admin | clusterAdmin, directShardOperations, readAnyDatabase, readWrite, userAdminAnyDatabase, readWrite@local | Atlas-internal | Cloud backups. |
| 6 | `mms-mongot` | admin | atlasSearchFsyncRole, bypassDefaultMaxTimeMSRole, clusterMonitor, directShardOperations, readWriteAnyDatabase, readWrite@local | Atlas-internal | Atlas Search engine. |
| 7 | `mms-mongotune` | admin | atlasIWMInternalKillOpRole, atlasIWMInternalSetParameterRole, clusterMonitor, setUserWriteBlockMode | Atlas-internal | Index/query tuning. |

## §A.2 · Effective access matrix per user

| User | masci_safety (PROD) | masci_safety_preview (PREVIEW) | Other 28 DBs | Cluster-level commands |
|---|---|---|---|---|
| `admin_db_user` | **READ + WRITE** | **READ + WRITE** | **READ + WRITE** | YES (atlasAdmin) |
| `Password` | **READ + WRITE** | **READ + WRITE** | **READ + WRITE** | NO (only readWriteAnyDatabase) |
| `mms-*` (5 users) | varies — internal Atlas use only | varies | varies | varies |

**There are ZERO per-environment-scoped customer Atlas users.** No preview-only user. No production-only user. No service-account scoping. No agent-account scoping.

## §A.3 · Verifying the fork's role

```
$ mongosh ... --eval 'db.runCommand({connectionStatus: 1, showPrivileges: true})'

authInfo.authenticatedUsers:
  - admin_db_user@admin

authInfo.authenticatedUserRoles:
  - atlasAdmin@admin
  - backup@admin                          (auto-granted by atlasAdmin)
  - clusterMonitor@admin                  (auto-granted)
  - dbAdminAnyDatabase@admin              (auto-granted)
  - enableSharding@admin                  (auto-granted)
  - readWriteAnyDatabase@admin            (auto-granted)

authInfo.authenticatedUserPrivileges (count): 19
  on CLUSTER: 70+ cluster commands
  on .: full DML/DDL across every DB and collection
  on .system.users: find
  on admin.system.roles: find
  on admin.system.version: find
  on local.replset.minvalid: find
  on config.system.sessions: collStats, dbStats, moveChunk, splitChunk, ...
  (and 12 more privilege grants)
```

## §A.4 · DBs visible to the fork (33 total)

```
admin, config, local, sample_mflix                           ← Atlas system
masci_safety                                                 ← PROD
masci_safety_preview                                         ← PREVIEW
masci_restore_drill_2026_05_30                               ← backup restore drill
masci_restore_drill_auto_20260601_015003                     ← backup restore drill
masci_test_autoresolve_*_preview            (5 ephemeral)    ← pytest residue
masci_test_webhook_harden_001_*_preview     (15 ephemeral)   ← pytest residue
masci_test_webhook_harden_*_preview         (3 ephemeral)    ← pytest residue
scheduler_test_iter445                                       ← pytest residue
```

## §A.5 · Principle of Least Privilege — current state

❌ **VIOLATED.**

- `admin_db_user` should hold a single least-privileged role for its intended purpose. Today it holds `atlasAdmin`, the highest customer-level privilege.
- A second customer account (`Password`) also holds `readWriteAnyDatabase` on all DBs.
- Neither account is scoped to an environment or a database list.
- A compromise of *either* customer account = total cluster compromise.

## §A.6 · Deliverable matrix (per directive)

| Requirement | Status |
|---|---|
| Preview User: preview databases only, no production access | ❌ **NOT IN PLACE** (no such user exists) |
| Production User: production databases only, no preview access | ❌ **NOT IN PLACE** (no such user exists) |
| Principle of Least Privilege | ❌ **VIOLATED** |
| Written matrix showing User · Role · DB Access · Write · Read · Environment | ✅ **DELIVERED** (§A.1, §A.2 above) |

## §A.7 · Recommended remediation (operator-only · NO action taken in this audit)

The remediation must happen in the **MongoDB Atlas console** (not via the application) because Atlas user management is administered there. The fork agent has no UI access to Atlas Console.

Phased plan:
1. In Atlas Console → Database Access, create two new users:
   - `masci_preview` with role `readWrite@masci_safety_preview` only.
   - `masci_prod` with role `readWrite@masci_safety` only.
2. Update the **production pod's** `/app/backend/.env` `MONGO_URL` to use `masci_prod`'s credentials.
3. Update the **preview pod's** `/app/backend/.env` `MONGO_URL` to use `masci_preview`'s credentials.
4. Verify both pods boot cleanly and pass their existing test suites.
5. **Disable** the existing `admin_db_user` and `Password` users (or rotate their passwords and restrict them to break-glass-only access by the operator).
6. Document the break-glass rotation cadence (e.g., quarterly).

The above is a **WRITE-AUTHORIZED CHANGE** to live infrastructure — explicitly out-of-scope for GOVERNANCE-HARDEN-001 which is read-only audit.
