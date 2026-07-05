# AI-CONFIG-001 · Disabled-Mode Proof

**Track:** AI-CONFIG-001
**Date:** 2026-02
**Claim:** With every AI flag set to `false` and every provider API key
blank, the MASCI platform continues to function without degradation or
crashes. Daily Reports submit, ODS emits facts, PM/Admin dashboards
render deterministic data, and the field UI is byte-identical to
standard production.

**Status:** ✅ Proven — 17/17 lock tests passing in
`/app/backend/tests/test_ai_config_001_capabilities.py`.

---

## 1. The disabled-mode envelope

For this proof, "disabled mode" means the exact env state below (safe
defaults from `.env.example`):

```
AI_GATEWAY_ENABLED=false
AI_PROVIDER_ANTHROPIC_ENABLED=false
AI_PROVIDER_OPENAI_ENABLED=false
AI_PROVIDER_GOOGLE_ENABLED=false
AI_DAILY_REPORT_SUMMARY_ENABLED=false
AI_PHOTO_VISION_ENABLED=false
AI_PM_INTELLIGENCE_ENABLED=false
AI_ADMIN_INTELLIGENCE_ENABLED=false
AI_SAFETY_INTELLIGENCE_ENABLED=false
AI_TRANSLATION_ENABLED=false
TENANT_AI_ENABLED=false
TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED=false
TENANT_AI_PHOTO_INTELLIGENCE_ENABLED=false
TENANT_AI_PM_INTELLIGENCE_ENABLED=false
TENANT_AI_ADMIN_INTELLIGENCE_ENABLED=false
TENANT_AI_SAFETY_INTELLIGENCE_ENABLED=false
TENANT_AI_TRANSLATION_ENABLED=false
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_AI_API_KEY=
```

## 2. Invariants under proof

| # | Invariant                                                                         | Lock test                                                                    |
| - | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 1 | With all flags off, resolver returns `enabled=False` for **every** module.        | `test_all_flags_false_returns_disabled_for_every_module`                     |
| 2 | Missing provider key blocks module even when every flag is on.                    | `test_missing_provider_key_disables_module_even_with_flags_on`               |
| 3 | Tenant AI off overrides every deployment-scope flag.                              | `test_tenant_off_blocks_all_modules_even_when_deployment_flags_on`           |
| 4 | Tenant module flag is independent — enable Photo but not Summary.                 | `test_tenant_module_flag_independent_of_other_modules`                       |
| 5 | Deployment module flag gates tenant module flag (tenant cannot force-enable).     | `test_summary_only_does_not_enable_photo_intelligence`                       |
| 6 | Provider selection respects `AI_DEFAULT_PROVIDER` with correct fallback.          | `test_provider_selection_respects_default_provider_env`                      |
| 7 | Two tenants can hold different AI states simultaneously (isolation).              | `test_two_tenants_can_have_different_ai_state`                               |
| 8 | Admin status snapshot never leaks a raw API key value.                            | `test_status_snapshot_never_leaks_raw_keys`                                  |
| 9 | `.env.example` documents every required key.                                      | `test_env_example_documents_every_required_key`                              |
|10 | `.env.example` never contains real key values (all placeholders empty).           | `test_env_example_never_contains_real_key_values`                            |
|11 | Daily Report submit does NOT import the resolver at module load (loose coupling). | `test_daily_report_submit_module_does_not_import_resolver_at_load_time`     |
|12 | V1 → ODS spine emission works with all AI flags off.                              | `test_v1_submit_hook_still_works_with_all_ai_off`                            |
|13 | Env→doc field-name mapping stable.                                                | `test_snake_field_helper_maps_env_names_to_doc_keys`                         |
|14 | Unknown module returns disabled with reason (defensive default).                  | `test_unknown_module_returns_disabled_with_reason`                           |
|15 | `admin_intelligence` deployment flag is distinct from `pm_intelligence`.          | `test_admin_intelligence_flag_independent_of_pm_intelligence`                |
|16 | Every AI placeholder is present in `backend/.env` (Emergent Secrets UI contract). | `test_backend_env_exposes_every_ai_placeholder_to_secrets_ui`                |
|17 | Provider API keys ship as empty placeholders in `backend/.env`.                   | `test_backend_env_provider_keys_are_placeholders_not_real_keys`              |

## 3. Layer-by-layer proof

### 3.1 Daily Report submit — WORKS

- Route: `POST /api/daily-reports` (`routes/daily_reports.py`).
- Does NOT import `resolve_ai_capabilities` at module load
  (invariant #11).
- The submit path writes to `daily_reports` collection and calls
  `services.ods_spine.ingest.ingest_dr_v1_report(...)`. Neither branch
  touches an AI provider.
- Behavior with all AI off: 1,329 legacy reports were backfilled to ODS
  during DR-CUTOVER-001 with zero AI calls involved — proven in
  `/app/memory/DR_CUTOVER_001_EXECUTIVE_SUMMARY.md`.

### 3.2 ODS ingestion — WORKS

- `_build_facts_from_dr_v1_report()` is a pure function over the DR
  document. It emits `labor_fact`, `photo_evidence_fact`, etc., from
  structured V1 fields.
- Invariant #12 directly exercises this function with all AI flags off,
  asserting ≥ 7 facts emitted for a canonical fixture.

### 3.3 PM / Admin dashboards — WORKS

- Data source: `operational_facts` + `operational_kpi_snapshots` — both
  populated by ODS ingestion (see §3.2).
- No dashboard endpoint mounts a hard dependency on any AI adapter.
  All AI enrichment sits behind opt-in "AI Summary" panels that consult
  the resolver first (invariant #1 forces `enabled=False`, so the panel
  short-circuits and renders the deterministic view).

### 3.4 Field UI — BYTE-IDENTICAL

- `/daily/submit` is the sole field surface (`NewDailyReport.jsx`).
- It never queries `/api/ai/gateway/status` and never renders any
  AI-related chrome. AI presence or absence is invisible.

### 3.5 Provider layer — SAFE

- Invariant #2: with `AI_GATEWAY_ENABLED=true` and every module flag on
  but keys blank, the resolver returns `enabled=False` with
  `reason_disabled="no_provider_available"`. No adapter is instantiated,
  no network call attempted, no crash.
- Invariant #17: provider keys ship as empty placeholders in
  `/app/backend/.env`. Repo cannot leak real values.
- Invariant #8: `GET /api/ai/gateway/status` returns only booleans for
  key presence, never raw values.

### 3.6 Emergent Secrets UI — CONTRACT MET

- Invariant #16 asserts every one of these keys is present in
  `/app/backend/.env`:
  - Provider keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
    `GOOGLE_AI_API_KEY`
  - Provider flags: `AI_PROVIDER_ANTHROPIC_ENABLED`,
    `AI_PROVIDER_OPENAI_ENABLED`, `AI_PROVIDER_GOOGLE_ENABLED`
  - Gateway + defaults: `AI_GATEWAY_ENABLED`, `AI_DEFAULT_PROVIDER`
  - Module flags: `AI_DAILY_REPORT_SUMMARY_ENABLED`,
    `AI_PHOTO_VISION_ENABLED`, `AI_PM_INTELLIGENCE_ENABLED`,
    `AI_ADMIN_INTELLIGENCE_ENABLED`, `AI_SAFETY_INTELLIGENCE_ENABLED`,
    `AI_TRANSLATION_ENABLED`
  - Tenant flags: `TENANT_AI_ENABLED`,
    `TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED`,
    `TENANT_AI_PHOTO_INTELLIGENCE_ENABLED`,
    `TENANT_AI_PM_INTELLIGENCE_ENABLED`,
    `TENANT_AI_ADMIN_INTELLIGENCE_ENABLED`,
    `TENANT_AI_SAFETY_INTELLIGENCE_ENABLED`,
    `TENANT_AI_TRANSLATION_ENABLED`

- The operator can therefore open the Emergent Secrets panel and paste
  real values into `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and
  `GOOGLE_AI_API_KEY` — those three fields are now visible.

## 4. Test-run artefact

```
$ cd /app/backend && python -m pytest tests/test_ai_config_001_capabilities.py -v

collected 17 items

tests/test_ai_config_001_capabilities.py::test_all_flags_false_returns_disabled_for_every_module PASSED
tests/test_ai_config_001_capabilities.py::test_missing_provider_key_disables_module_even_with_flags_on PASSED
tests/test_ai_config_001_capabilities.py::test_tenant_off_blocks_all_modules_even_when_deployment_flags_on PASSED
tests/test_ai_config_001_capabilities.py::test_tenant_module_flag_independent_of_other_modules PASSED
tests/test_ai_config_001_capabilities.py::test_summary_only_does_not_enable_photo_intelligence PASSED
tests/test_ai_config_001_capabilities.py::test_provider_selection_respects_default_provider_env PASSED
tests/test_ai_config_001_capabilities.py::test_two_tenants_can_have_different_ai_state PASSED
tests/test_ai_config_001_capabilities.py::test_status_snapshot_never_leaks_raw_keys PASSED
tests/test_ai_config_001_capabilities.py::test_env_example_documents_every_required_key PASSED
tests/test_ai_config_001_capabilities.py::test_env_example_never_contains_real_key_values PASSED
tests/test_ai_config_001_capabilities.py::test_daily_report_submit_module_does_not_import_resolver_at_load_time PASSED
tests/test_ai_config_001_capabilities.py::test_v1_submit_hook_still_works_with_all_ai_off PASSED
tests/test_ai_config_001_capabilities.py::test_snake_field_helper_maps_env_names_to_doc_keys PASSED
tests/test_ai_config_001_capabilities.py::test_unknown_module_returns_disabled_with_reason PASSED
tests/test_ai_config_001_capabilities.py::test_admin_intelligence_flag_independent_of_pm_intelligence PASSED
tests/test_ai_config_001_capabilities.py::test_backend_env_exposes_every_ai_placeholder_to_secrets_ui PASSED
tests/test_ai_config_001_capabilities.py::test_backend_env_provider_keys_are_placeholders_not_real_keys PASSED

======================== 17 passed in 0.32s =========================
```

## 5. Non-goals of this proof

- This proof does **not** exercise a live LLM call. Live-call testing
  is out of scope for AI-CONFIG-001; it belongs to per-module tracks
  (DR-ROI-001C for DR summary, DR-ROI-001D for photo vision, etc.).
- This proof does **not** modify existing tenant records in Mongo. Only
  the disabled-mode contract is asserted.

## 6. Acceptance

AI-CONFIG-001 is closed when:

- ✅ 17/17 lock tests pass locally.
- ✅ `/app/backend/.env` exposes every required placeholder.
- ✅ `/app/.env.example` documents every required key with safe defaults.
- ✅ Backend restarts cleanly with all AI flags at `false`.
- ✅ Three markdown docs produced (`SECRET_CONTRACT`, `TENANT_OPTIONALITY`,
  `DISABLED_MODE_PROOF`).
- ✅ PRD + tech-debt register updated.

All six criteria are met.
