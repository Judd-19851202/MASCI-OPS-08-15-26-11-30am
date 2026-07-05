# AI-ADMIN-001 · Test Report

**Track:** AI-ADMIN-001 · Admin AI Configuration Center
**Date:** 2026-02
**Result:** ✅ **34/34 backend tests passing** (17 new + 17 AI-CONFIG-001 regression).

Run command:

```
cd /app/backend && python -m pytest \
  tests/test_ai_admin_001_config.py \
  tests/test_ai_config_001_capabilities.py -v
```

Result:

```
34 passed, 1 warning in 0.54s
```

---

## 1. Lock envelope — new AI-ADMIN-001 tests

Every test proves one invariant. All tests use an in-memory fake Mongo
+ a FastAPI TestClient — no live provider calls, no real DB required.

| # | Invariant                                                                                          | Test                                                                       |
| - | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 1 | Status endpoint never returns raw API key values.                                                  | `test_status_endpoint_returns_no_raw_key_values`                           |
| 2 | Status endpoint requires an admin token (401 without).                                             | `test_status_endpoint_requires_admin_token`                                |
| 3 | Strict admin gate rejects PM-token-shaped callers.                                                 | `test_pm_token_is_rejected_by_strict_admin_gate`                           |
| 4 | Tenants list always includes the canonical MASCI default even with no override doc.                | `test_tenants_list_always_includes_default_masci`                          |
| 5 | Tenants list reflects saved override docs (name, ai state, has_override_doc).                      | `test_tenants_list_reflects_saved_overrides`                               |
| 6 | GET capabilities returns `overrides` + resolved per-module verdicts.                               | `test_tenant_capabilities_get_returns_modules_and_overrides`               |
| 7 | Update writes only allow-listed fields; secrets and `tenant_id` overrides are stripped.            | `test_update_tenant_capabilities_writes_only_allowlisted_fields`           |
| 8 | Update rejects an empty patch (400) — note alone is not sufficient.                                | `test_update_rejects_empty_patch`                                          |
| 9 | Update to tenant A never touches tenant B; version stamps advance per-tenant.                      | `test_update_is_tenant_isolated`                                           |
|10 | Update writes an audit entry with actor / before / after / changed_fields / note; no secrets.      | `test_update_writes_audit_entry_with_before_after_and_actor`               |
|11 | Update response recomputes module verdicts so UI can reflect new state instantly.                  | `test_update_response_recomputes_modules`                                  |
|12 | Audit endpoint returns entries newest-first.                                                       | `test_audit_endpoint_returns_recent_entries_newest_first`                  |
|13 | Provider probe returns booleans only, never a raw key value.                                       | `test_provider_test_endpoint_returns_booleans_only`                        |
|14 | Provider probe 404s for an unknown provider name.                                                  | `test_provider_test_unknown_provider_returns_404`                          |
|15 | Provider probe reports `missing_key` when flag on but key blank.                                   | `test_provider_test_reports_status_missing_key`                            |
|16 | Daily-report submit module never imports the admin AI config router.                               | `test_daily_report_submit_route_does_not_import_ai_admin_config`           |
|17 | ODS ingestion still emits facts with every AI env var stripped from the process.                   | `test_ai_off_still_lets_ods_ingestion_run`                                 |

## 2. AI-CONFIG-001 regression

All 17 AI-CONFIG-001 lock tests continue to pass:

- `test_all_flags_false_returns_disabled_for_every_module`
- `test_missing_provider_key_disables_module_even_with_flags_on`
- `test_tenant_off_blocks_all_modules_even_when_deployment_flags_on`
- `test_tenant_module_flag_independent_of_other_modules`
- `test_summary_only_does_not_enable_photo_intelligence`
- `test_provider_selection_respects_default_provider_env`
- `test_two_tenants_can_have_different_ai_state`
- `test_status_snapshot_never_leaks_raw_keys`
- `test_env_example_documents_every_required_key`
- `test_env_example_never_contains_real_key_values`
- `test_daily_report_submit_module_does_not_import_resolver_at_load_time`
- `test_v1_submit_hook_still_works_with_all_ai_off`
- `test_snake_field_helper_maps_env_names_to_doc_keys`
- `test_unknown_module_returns_disabled_with_reason`
- `test_admin_intelligence_flag_independent_of_pm_intelligence`
- `test_backend_env_exposes_every_ai_placeholder_to_secrets_ui`
- `test_backend_env_provider_keys_are_placeholders_not_real_keys`

## 3. Live sanity checks

Executed against the running preview backend on 2026-02:

```
GET  /api/health                                → 200 (backend healthy)
GET  /api/admin/ai/config/status                → 401 (no token)
GET  /api/admin/ai/tenants                      → 401 (no token)
GET  /api/admin/ai/tenants/masci/capabilities   → 401 (no token)
POST /api/admin/ai/providers/anthropic/test     → 401 (no token)
```

Frontend smoke: hitting `/admin/ai-configuration` unauthenticated
correctly redirects to Admin Sign In (verified via Playwright screenshot).

## 4. Frontend testing scope (deferred to testing agent v3 fork)

Frontend flow tests (login → open page → verify sections → flip a
toggle → save → confirm audit entry appears) are run via the
project's `testing_agent_v3_fork` immediately after this document
is written. Any regressions surfaced there will be recorded in the
next iteration report at `/app/test_reports/iteration_*.json`.

## 5. Non-goals of this test envelope

- No live LLM API calls. The provider `/test` endpoint returns
  readiness only; a live-probe endpoint is a P2 follow-up.
- No load / soak testing of the audit collection. Audit currently
  writes best-effort; index optimisation is a P2 follow-up when
  audit volume exceeds ~1k entries per tenant.

## 6. Acceptance

- ✅ 17 new lock tests green.
- ✅ 17 AI-CONFIG-001 regression tests green.
- ✅ Backend boots cleanly with the new router mounted.
- ✅ Admin gate returns 401 for unauthed callers on every endpoint.
- ✅ Field UI unchanged (grep + regression lock).
- ✅ Zero raw API key values leave the backend.
- ✅ Docs, PRD, changelog, tech-debt, manifest updated.
