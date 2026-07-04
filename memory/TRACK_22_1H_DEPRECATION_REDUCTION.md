# TRACK 22.1H · Deprecation Reduction Report

## Warning count

| State | `@app.on_event("startup")` count (source) | `app.router.on_startup` (runtime; includes any dupes) | Est. FastAPI DeprecationWarnings per pytest run |
|---|---|---|---|
| Track 22.1D close | 51 | 51 | ~117 |
| Track 22.1E close | 40 | 40 | ~95 |
| Track 22.1F close | 33 (source) | 34 (runtime · included `_start_safety_digest_cron` dupe) | ~81 |
| Track 22.1G close | 29 (source) | 29 (runtime · dupe carried through) | ~73 |
| **Track 22.1H close** | **23** (source) | **23** (runtime · dupe **retired**) | **~59** (73 − 14) |
| Target (all migrated) | 0 | 0 | 0 |

**Reduction this track: −6 items from `app.router.on_startup` (5 migrations + 1 defect closure), −~14 warnings.**

## Cumulative reduction

| Track | Cumulative `on_startup` (runtime) | Cumulative `LIFECYCLE_STEPS` | Cumulative migrated_pct | Cumulative unique lifecycle callables per boot |
|---|---|---|---|---|
| Pre-22.1E | 51 | 0 | 0.00% | 51 |
| 22.1E close | 40 | 11 | 21.57% | 51 |
| 22.1F close | 34 (with dupe) | 18 | 34.62% | 51 |
| 22.1G close | 29 (with dupe) | 22 | 43.14% | 51 |
| **22.1H close** | **23** | **27** | **54.00%** | **50** ← dupe retired |
| 22.1I target | ~13 | ~37 | ~74% | 50 |
| 22.1J target | ~11 | ~39 | ~78% | 50 |
| Full retirement | 0 | 50 | 100.00% | 50 |

## Follow-up tracks (queued)

| Track | Target group | Approx handlers |
|---|---|---|
| 22.1I | Miscellaneous bootstrap handlers | ~10 (e.g., `_bootstrap_operations`, `_bootstrap_integrations`, `_ensure_stability_ttls`, `_clear_super_admin_force_pw_change`, `_ensure_field_memory_indexes_startup`, `_backfill_doc_ids`, `_track_16_05/08/09/10_bootstrap_on_startup`, `_arm_audit_ttl_indexes`, `_deploy_fix_001_backup_orphan_sweep`, `_start_backup_scheduler`, etc.) |
| 22.1J | Readiness-flip + reminder-scheduler final ordering | 2 (must remain last · `_iter453_6_flip_ready_flag`) |
| 22.1K | Shutdown handler | 1 |

## No pytest.ini `filterwarnings` band-aid

Per constitutional mandate: FastAPI `on_event` deprecation warnings remain visible. Silencing is not a substitute for migration.

## Verdict

🟢 **REDUCTION CERTIFIED.** 5 more decorators retired plus 1 pre-existing double-registration closed. `/api/admin/platform/status.migrated_pct` = **54.00%**. Cumulative unique lifecycle callables per boot now correctly reads **50**.
