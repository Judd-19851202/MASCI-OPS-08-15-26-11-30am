# TRACK 22.1E · Index Handler Inventory

Machine-readable source: `memory/track_22_1e/INDEX_HANDLER_INVENTORY_before.json`.

## 11 handlers migrated

| # | Handler | Line | Collections / Purpose | Idempotent |
|---|---|---|---|---|
| 1 | `_ensure_scheduler_lock_indexes_at_startup` | 10563 | `scheduler_locks` — cluster-wide singleton lock keys | ✅ |
| 2 | `_ensure_project_team_assignments_indexes` | 10645 | `project_team_assignments` — project × team lookups | ✅ |
| 3 | `_startup_trust_spine_indexes` | 11339 | `trust_spine_events` — correlation_id + stage + timestamp | ✅ |
| 4 | `_arm_hot_id_indexes` | 11865 | Hot-key ID lookups across daily reports / incidents | ✅ |
| 5 | `_arm_workflow_state_events_indexes` | 11880 | `workflow_state_events` — workflow-record + stage | ✅ |
| 6 | `_arm_iter142_perf_indexes` | 11906 | Iter-142 perf-audit index set (see QA_PERF_AUDIT.md) | ✅ |
| 7 | `_li_ensure_indexes` | 12157 | Lookups-index cluster (label, tenant_key, active flag) | ✅ |
| 8 | `_fleet_ensure_indexes` | 12332 | Fleet inspection collection indexes | ✅ |
| 9 | `_ensure_dls_indexes` | 12688 | Delta-log / DLS collection indexes | ✅ |
| 10 | `_ensure_driver_session_indexes` | 12717 | Driver-session tracking indexes | ✅ |
| 11 | `_ensure_passkey_indexes` | 13026 | WebAuthn passkey credential indexes | ✅ |

Every handler:
- Uses `create_index(...)` semantics that no-op if the target index already exists.
- Swallows internal errors (per source comments) — indexes are best-effort; boot never blocked.
- Has no email side effect.
- Has no scheduler side effect.
- Has no external API call.
