# TRACK 22.1I · Misc Bootstrap Inventory

## 20 migrated handlers (`LIFECYCLE_STEPS` group=`misc-bootstrap`)

| Handler | Line | Purpose | Email risk (grep-verified) | Idempotent | Decision |
|---|---|---|---|---|---|
| `_db_isolation_failsafe` | 10620 | Defense-in-depth DB isolation probe | none | yes | ✅ |
| `_tune_asyncio_thread_pool` | 10633 | asyncio thread-pool tuning | none | yes | ✅ |
| `_deploy_fix_001_backup_orphan_sweep` | 10714 | DEPLOY-FIX-001 startup sweep | none | yes | ✅ |
| `_ensure_v_prelude_wave1_indexes` | 10751 | Wave-1 substrate index-ensure | none | yes | ✅ |
| `_log_operational_hygiene_at_startup` | 10777 | Operational hygiene log line | none | yes | ✅ |
| `_clear_super_admin_force_pw_change` | 10805 | One-shot iter117 migration | none | yes | ✅ |
| `_startup_deployment_ledger_indexes` | 11387 | Deployment ledger indexes | none | yes | ✅ |
| `_oa_startup` | 11662 | Operations Anchor startup init | none | yes | ✅ |
| `_arm_audit_ttl_indexes` | 11776 | Audit TTL indexes | none | yes | ✅ |
| `_bootstrap_operations` | 11816 | Operations subsystem bootstrap | none | yes | ✅ |
| `_bootstrap_integrations` | 11824 | Integrations subsystem bootstrap | none | yes | ✅ |
| `_ensure_stability_ttls` | 12026 | Stability TTL indexes | none | yes | ✅ |
| `_li_start_worker` | 12192 | Long-running LI worker starter | none | yes | ✅ |
| `_ensure_field_memory_indexes_startup` | 12689 | Field memory indexes | none | yes | ✅ |
| `_backfill_doc_ids` | 13215 | One-shot doc_id backfill | none | yes | ✅ |
| `_track_16_05_bootstrap_on_startup` | 13372 | Track 16.05 bootstrap | none | yes | ✅ |
| `_track_16_08_bootstrap_on_startup` | 13401 | Track 16.08 bootstrap | none | yes | ✅ |
| `_track_16_09_bootstrap_on_startup` | 13431 | Track 16.09 bootstrap | none | yes | ✅ |
| `_track_16_10_bootstrap_on_startup` | 13519 | Track 16.10 bootstrap | none | yes | ✅ |
| `_track_15_93_run_system_bootstrap` | 16004 | Track 15.93 system bootstrap | none | yes | ✅ |

All 20 grep-verified for `resend`, `_dispatch_auto_email`, `send(`, `sendemail` — **all clean** at handler-body level.

## Runtime snapshot references

`memory/track_22_1i/RUNTIME_ENUMERATION_before.json` (routes=1441, on_startup=23, lifecycle=27) → `.../RUNTIME_ENUMERATION_after.json` (routes=1441, on_startup=3, lifecycle=47).
