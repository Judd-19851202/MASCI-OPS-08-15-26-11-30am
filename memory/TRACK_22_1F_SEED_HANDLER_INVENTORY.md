# TRACK 22.1F · Seed Handler Inventory

Machine-readable source: `memory/track_22_1f/SEED_HANDLER_INVENTORY_before.json`.

## 7 seed handlers migrated

| # | Handler | Original line | Bytecode SHA-256 (first 16) | Idempotent | Env gate | External calls |
|---|---|---|---|---|---|---|
| 1 | `_seed_field_leadership_equipment_catalog` | 10639 | `6aef109dac0bb8d9` | ✅ (delegates to `_seed_field_leadership_equipment(db)`) | none | none |
| 2 | `_seed_shop_users` | 10644 | `f4a0ac30a7792fff` | ✅ (delegates to `shop_users.seed_shop_users(db)`) | none | none |
| 3 | `_seed_hr_users` | 10722 | `f4a0ac30a7792fff` | ✅ (delegates to `hr_users.seed_hr_users(db)`) | none | none |
| 4 | `_seed_field_leadership_users` | 10863 | `f4a0ac30a7792fff` | ✅ (delegates to `field_leadership_users.seed_field_leadership_users(db)`) | none | none |
| 5 | `_seed_safety_users` | 11849 | `b553dcd21dc0282d` | ✅ (delegates to `seed_safety_users(db)`; +8 idempotent `create_index` calls) | none | none |
| 6 | `_bootstrap_user_directory` | 13094 | `c8f5a766faaf7879` | ✅ (`_ud.bootstrap_super_admin` + `identity_mirror.run_startup_mirror` + `role_templates.run_startup_seed` — all idempotent) | reads `SUPER_ADMIN_EMAIL`, `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | none |
| 7 | `_seed_phase1` | 15516 | `513aa17c06f09f54` | ✅ (aggregator: `seed_initial_users`, `seed_initial_projects`, `create_tools_indexes`, `create_phase4_indexes`, `_seed_equipment_master`, `_seed_employees_from_json`, `_seed_suppliers_from_json`, `_create_safety_indexes`, `seed_project_managers`, `seed_jobs_master`, `_jha_files_indexes`, `boot_self_heal` — every sub-seed is idempotent) | none | none |

## Per-handler certification

Every migrated seed:
- Delegates to an existing module-level function, or is an idempotent aggregator of them.
- Uses `insert_one(...) if not exists` / `update_one(..., upsert=True)` semantics inside each sub-seed (verified in each source module).
- Swallows internal errors per source pattern — seeds are best-effort; boot never blocked.
- Has zero email side effect.
- Has zero scheduler side effect.
- Has zero external API call.

## What did NOT get migrated in this track

`_deploy_fix_001_backup_orphan_sweep` (backup side-effect, not seed) · `_seed_employees_from_json` (module-level helper, not startup handler) · `_seed_suppliers_from_json` (module-level helper) · `_seed_equipment_master` (module-level helper). These are either non-seed handlers or non-decorated helpers called by `_seed_phase1`; migrating them here would exceed the track charter. Left owned in the debt register for future consolidation.
