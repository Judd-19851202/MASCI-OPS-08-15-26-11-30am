# DR-UNIFY-003 · Test Report

**Result:** ✅ **75/75 pytest tests passing** (19 new + 56 regression from prior tracks).

Command:

```
cd /app/backend && python -m pytest \
  tests/test_dr_unify_003_consolidation.py \
  tests/test_dr_cutover_002_daily_summary.py \
  tests/test_ai_admin_001_config.py \
  tests/test_ai_config_001_capabilities.py
```

Result:

```
75 passed in ~1s
```

## 1. Lock envelope — DR-UNIFY-003 (19 tests)

| #  | Invariant                                                                                          | Test                                                                       |
| -- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 1  | Frontend router redirects `/daily-report/v2` → `/daily/submit`.                                    | `test_frontend_router_redirects_daily_report_v2_to_daily_submit`           |
| 2  | Router no longer imports the `DailyReportV2` component.                                            | `test_frontend_router_no_longer_imports_daily_report_v2_shell`             |
| 3  | Summary endpoints live only under canonical `/api/daily-reports/*`.                                | `test_daily_summary_endpoints_are_under_canonical_prefix`                  |
| 4  | Both canonical and deprecated alias PDF routes are declared.                                       | `test_dr_v2_pdf_router_serves_both_canonical_and_alias`                    |
| 5  | Field form contains no V1/V2/AI-agent vocabulary.                                                  | `test_new_daily_report_form_has_no_v1_or_v2_user_facing_language`          |
| 6  | Compat helper exposes exactly the six canonical/legacy pairs.                                      | `test_compat_helper_exposes_expected_aliases`                              |
| 7  | Resolver returns canonical when populated, legacy when only legacy has data, canonical by default. | `test_resolve_read_prefers_canonical_when_populated`                       |
| 8  | Resolver never merges — always returns a single collection name.                                   | `test_compat_helper_never_returns_a_merge`                                 |
| 9  | Migration script file exists and is readable.                                                      | `test_migration_script_exists_and_is_executable`                           |
| 10 | Migration script implements the four required modes.                                               | `test_migration_script_has_four_required_modes`                            |
| 11 | Migration script `--help` succeeds and lists every flag.                                           | `test_migration_script_help_prints`                                        |
| 12 | Migration script refuses `APP_ENV=production` without `--allow-prod`.                              | `test_migration_script_refuses_production_by_default`                      |
| 13 | Rollback mode prints the plan and touches no DB.                                                   | `test_migration_script_rollback_plan_prints_without_touching_db`           |
| 14 | Neither canonical nor deprecated alias route is silently removed.                                  | `test_no_new_route_deletes_a_legacy_alias`                                 |
| 15 | DR-CUTOVER-002 summary section stays mounted inside NewDailyReport.jsx.                            | `test_daily_submit_form_still_mounts_the_summary_section`                  |
| 16 | Summary route source contains no marketing/AI wording.                                             | `test_no_user_facing_ai_language_in_daily_summary_backend_route`           |
| 17 | V1 submit route stays loose-coupled to the summary module (DR-CUTOVER-002).                        | `test_daily_reports_route_still_ignorant_of_ai_summary_module`             |
| 18 | AI-CONFIG-001 env placeholders remain in `backend/.env`.                                           | `test_ai_config_env_placeholders_still_present`                            |
| 19 | ODS spine module still reads legacy or via compat helper (no silent deletion).                     | `test_ods_module_still_reads_dr_v2_drafts_via_compat_or_legacy_path`       |

## 2. Regression envelopes (all green)

- `test_dr_cutover_002_daily_summary.py` — **22/22**.
- `test_ai_admin_001_config.py` — **17/17**.
- `test_ai_config_001_capabilities.py` — **17/17**.

## 3. Live preview verification

- `GET /api/health` → 200.
- `GET /api/daily-reports/approved` (canonical, public) → 200.
- `GET /api/dr-v2/reports/approved` (deprecated alias, admin-gated) → 401 without token (same auth behaviour as canonical would return with mismatched auth requirements — this is expected because the alias is behind admin auth in the current router).
- `POST /api/daily-reports/summary/draft` (no auth, tenant AI off) →
  200 with `enabled=false, reason=tenant_ai_disabled`.
- Migration `--dry-run` against preview DB → 56 source docs across 6
  legacy collections, 0 collisions, 56 would-copy.
- Playwright: navigating to `/daily-report/v2` lands on
  `/daily/submit` with the canonical form rendering, including the
  DR-CUTOVER-002 summary section. Zero banned strings in HTML.

## 4. Not tested here (deferred)

- Live migration execution against preview (`--live`) — DR-UNIFY-004.
- Byte-comparison test between canonical and deprecated PDF variants
  — deferred until DR-UNIFY-004 with a golden-file baseline.
- Legacy collection drop — DR-UNIFY-005.

## 5. Acceptance criteria

- ✅ 19 new lock tests green.
- ✅ 56 regression lock tests green.
- ✅ Live preview redirect verified.
- ✅ Migration dry-run runs cleanly against a real DB.
- ✅ Zero user-facing V1/V2 or AI vocabulary.
- ✅ 10 markdown docs + PRD/CHANGELOG/tech-debt/manifest updates delivered.
