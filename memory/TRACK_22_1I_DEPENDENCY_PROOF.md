# TRACK 22.1I · Dependency Proof

**Question:** Can each of the 20 misc-bootstrap handlers safely execute BEFORE the remaining 3 legacy `on_startup` handlers?

**Answer:** **Yes.** Every migrated handler is idempotent, has no dependency on `_startup` (routes.command_center) or `_start_backup_scheduler`, and executes BEFORE the readiness flip which is now the effective on_startup entrypoint.

## Class-by-class dependency table

| Handler class | Depends on `_startup` (command_center)? | Depends on `_start_backup_scheduler`? | Depends on readiness flag? | Depends on any lifecycle group already migrated (index/seed/scheduler-nonemail/email)? | Verdict |
|---|---|---|---|---|---|
| Failsafes (`_db_isolation_failsafe`) | No | No | No | No | ✅ safe (module-import DB guard already fired) |
| Env tuning (`_tune_asyncio_thread_pool`) | No | No | No | No | ✅ safe |
| Deploy sweeps (`_deploy_fix_001_backup_orphan_sweep`) | No | No | No | No | ✅ safe (idempotent orphan scan) |
| Index-ensure (`_ensure_v_prelude_wave1_indexes`, `_startup_deployment_ledger_indexes`, `_arm_audit_ttl_indexes`, `_ensure_stability_ttls`, `_ensure_field_memory_indexes_startup`) | No | No | No | No | ✅ safe (idempotent `create_index`) |
| Logging (`_log_operational_hygiene_at_startup`) | No | No | No | No | ✅ safe |
| One-shot migrations (`_clear_super_admin_force_pw_change`, `_backfill_doc_ids`) | No | No | No | No | ✅ safe (idempotent — silent if already applied) |
| Ops anchor init (`_oa_startup`) | No | No | No | No | ✅ safe |
| Subsystem bootstraps (`_bootstrap_operations`, `_bootstrap_integrations`) | No | No | No | No | ✅ safe (subsystems bind their own module-level state) |
| Worker starter (`_li_start_worker`) | No | No | No | No | ✅ safe (`asyncio.create_task`) |
| Track-N bootstraps (`_track_16_05/08/09/10_bootstrap_on_startup`, `_track_15_93_run_system_bootstrap`) | No | No | No | No | ✅ safe (idempotent Track-N migration hooks) |

## Ordering guarantee post-22.1I

```
Module import:  DB guard → Mongo client → FastAPI(lifespan=...) → Resend SDK patch → decorator registration
Lifespan run:   LIFECYCLE_STEPS (47 handlers, in source order) → on_startup (3 handlers: _startup → _start_backup_scheduler → _iter453_6_flip_ready_flag) → readiness flip
```

Every misc-bootstrap handler completes BEFORE `_startup` (command_center), which in turn completes BEFORE `_start_backup_scheduler`, which completes BEFORE `_iter453_6_flip_ready_flag`.

## Verdict

🟢 **DEPENDENCY PROOF CERTIFIED.** All 20 misc-bootstrap handlers safe to migrate.
