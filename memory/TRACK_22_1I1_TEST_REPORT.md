# TRACK 22.1I.1 · Test Report

## Lock test: `backend/tests/test_track_22_1i1_backup_scheduler_migration.py`

Environment:
```
EMAIL_SAFETY_MODE=strict
SCHEDULER_ENABLED=false
AUTO_EMAIL_REPORTS=false
DISABLE_BACKUP_SCHEDULER=true
```

### Assertions (22 total)
1. `test_backup_scheduler_migrated_to_lifecycle_steps` — `_start_backup_scheduler` in `LIFECYCLE_STEPS.backup-scheduler`.
2. `test_backup_scheduler_no_longer_in_on_startup` — legacy decorator retired.
3. `test_lifecycle_steps_total_is_48` — group counts (11/7/4/5/20/1).
4. `test_on_startup_count_dropped_to_2` — legacy count = 2.
5. `test_excluded_handlers_remain_in_on_startup` — `_startup` (router) + `_iter453_6_flip_ready_flag`.
6. `test_readiness_flip_remains_last` — order preserved.
7. `test_command_center_router_startup_still_queued`.
8. `test_shutdown_handler_still_registered`.
9. `test_no_duplicate_registrations` — no cross-registry overlap.
10. `test_backup_scheduler_bytecode_matches_baseline` — SHA-256 identical.
11. `test_bytecode_fingerprint_index_updated`.
12. `test_bytecode_fingerprints_all_clean` — 6/6.
13. `test_route_and_openapi_parity` — 1441/1445/1264.
14. `test_middleware_count_unchanged`.
15. `test_platform_status_reflects_track_22_1i1` — payload + secret-scrub.
16. `test_email_safety_strict_mode_intact` — Resend send stub active.
17. `test_lifespan_bootstrap_still_no_resend_import` — AST-clean.
18. `test_platform_status_lib_still_no_resend_import_at_module_scope`.
19. `test_snapshot_artifacts_committed` — 5 JSONs present.
20. `test_all_deliverables_present` — 13 MDs present.
21. `test_no_live_r2_or_email_paths_touched_by_migration` — handler body clean.
22. `test_prd_and_changelog_updated`.

### Extended regression envelope
Full pre-existing Track 22.1[C-I] lock-test suites re-run under the same env. Baseline integers in `test_track_22_1i_misc_bootstrap_migration.py` loosened from `==` to `<=/>=` to allow subsequent-track progression (documented in `TRACK_22_1I1_ZERO_DRIFT_MATRIX.md`).

### Results
See `test_reports/iteration_track_22_1i1.json` for the machine record.

### Deployment impact
🟢 **NONE.** Zero user-visible change. Zero data change. Zero permission change. Rollback path documented and single-diff.
