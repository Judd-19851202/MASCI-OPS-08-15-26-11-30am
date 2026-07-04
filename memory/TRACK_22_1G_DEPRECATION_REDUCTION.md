# TRACK 22.1G · Deprecation Reduction Report

## Warning count

| State | `@app.on_event("startup")` count | Est. FastAPI DeprecationWarnings per pytest run |
|---|---|---|
| Track 22.1D close | 51 | ~117 |
| Track 22.1E close | 40 | ~95 |
| Track 22.1F close | 33 | ~81 |
| Track 22.1G close | **29** | **~73** (81 − ~8 for the 4 handlers × 2 warnings each) |
| Target (all migrated) | 0 | 0 |

**Reduction this track: −4 decorators, −~8 warnings.**

## Cumulative reduction

| Track | Cumulative `on_startup` count | Cumulative `LIFECYCLE_STEPS` count | Cumulative migrated_pct |
|---|---|---|---|
| Pre-22.1E | 51 | 0 | 0.00% |
| 22.1E close | 40 | 11 | 21.57% |
| 22.1F close | 33 | 18 | 35.29% |
| **22.1G close** | **29** | **22** | **43.14%** |
| 22.1H target | 24 (roughly) | 27 | ~52.94% |
| Full retirement | 0 | 51 | 100.00% |

## Follow-up tracks (queued)

| Track | Target group | Approx handlers |
|---|---|---|
| 22.1H | Email-capable scheduler handlers | 4–5 (fingerprint-locked) |
| 22.1I | Miscellaneous bootstrap handlers | ~10 (e.g., `_bootstrap_operations`, `_bootstrap_integrations`, `_ensure_stability_ttls`, `_clear_super_admin_force_pw_change`, `_ensure_field_memory_indexes_startup`, `_backfill_doc_ids`, `_track_16_05/08/09/10_bootstrap_on_startup`, `_arm_audit_ttl_indexes`, `_deploy_fix_001_backup_orphan_sweep`, etc.) |
| 22.1J | Readiness-flip + reminder-scheduler handlers | 2 (must remain last · `_iter453_6_flip_ready_flag` + `_dispatch_reminder_scheduler_start`) |
| 22.1K | Backup scheduler + shutdown handler | 2+ |

## No pytest.ini `filterwarnings` band-aid

Per constitutional mandate: FastAPI `on_event` deprecation warnings remain visible. Silencing is not a substitute for migration.

## Verdict

🟢 **REDUCTION CERTIFIED.** 4 more decorators retired. 29 remain, each with an owner, target track, and defined migration pattern. Cumulative progress trackable at `/api/admin/platform/status.lifecycle.migration_progress.migrated_pct` = **43.14%**.
