# AI-CONFIG-001 · Secret + Feature-Flag Contract

**Track:** AI-CONFIG-001 (TENANT_AI_ENABLED amendment)
**Date closed:** 2026-02
**Owner:** Platform / AI Gateway
**Status:** ✅ Delivered — 17/17 lock tests passing.

---

## 1. Doctrine

AI is a **premium, optional, per-tenant enhancement layer**.
The platform is 100% usable with:

- every AI flag set to `false`,
- every provider API key blank,
- the `AI_GATEWAY_ENABLED` flag flipped off entirely.

Daily Reports still submit. ODS still emits facts. PM/Admin dashboards still
render deterministic data from `operational_facts` + `operational_kpi_snapshots`.
The field UI is byte-identical to standard production when AI is off (per
Invisible Intelligence: no "AI is off" chrome ever surfaces to a field user).

## 2. Where secrets live

| Location                | Purpose                                                                                                    | Committed to git?               |
| ----------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------- |
| `/app/backend/.env`     | **Runtime.** Emergent Secrets UI reads this file. Operator pastes real key values here via the Secrets UI. | Values NEVER committed (see §5). |
| `/app/.env.example`     | **Documentation.** Enumerates every AI key with safe defaults. Never contains real values.                 | Yes (structure only).           |
| Mongo `tenant_ai_capabilities` | **Per-tenant overrides.** One doc per tenant with per-module booleans.                              | N/A (database).                 |

## 3. The switchboard — full key inventory

Every one of these keys is present in `/app/backend/.env` as of AI-CONFIG-001.
Test `test_backend_env_exposes_every_ai_placeholder_to_secrets_ui` asserts
this contract holds. If the Emergent Secrets UI ever fails to render one
of these fields, that test will fail.

### 3.1 Provider API keys (pasted via Secrets UI, never git)

| Key                  | Type          | Default | Notes                                                    |
| -------------------- | ------------- | ------- | -------------------------------------------------------- |
| `ANTHROPIC_API_KEY`  | secret string | *empty* | Required for Anthropic provider. Empty = provider off.   |
| `OPENAI_API_KEY`     | secret string | *empty* | Required for OpenAI provider (text + vision).            |
| `GOOGLE_AI_API_KEY`  | secret string | *empty* | Required for Google/Gemini provider.                     |

Lock test `test_backend_env_provider_keys_are_placeholders_not_real_keys`
asserts these ship empty in the repo — real values only ever come from
the operator via the Secrets UI at deploy time.

### 3.2 Global gateway + provider flags

| Key                              | Default    | Purpose                                                            |
| -------------------------------- | ---------- | ------------------------------------------------------------------ |
| `AI_GATEWAY_ENABLED`             | `true`*    | Master kill switch. `false` → resolver returns disabled for all.   |
| `AI_PROVIDER_ANTHROPIC_ENABLED`  | `false`    | Enable Anthropic provider. Also needs `ANTHROPIC_API_KEY` set.     |
| `AI_PROVIDER_OPENAI_ENABLED`     | `false`    | Enable OpenAI provider. Also needs `OPENAI_API_KEY` set.           |
| `AI_PROVIDER_GOOGLE_ENABLED`     | `false`    | Enable Google/Gemini provider. Also needs `GOOGLE_AI_API_KEY` set. |
| `AI_DEFAULT_PROVIDER`            | `anthropic`| First-choice provider. Others become fallbacks.                    |
| `AI_DEFAULT_TEXT_MODEL`          | operator   | e.g. `claude-sonnet-4-5-20250929`. No default required.            |
| `AI_DEFAULT_VISION_PROVIDER`     | `openai`   | Vision-specific override.                                          |
| `AI_DEFAULT_VISION_MODEL`        | operator   | e.g. `gpt-5.2-vision`.                                             |
| `AI_PROVIDER_TIMEOUT_MS`         | `30000`    | Per-call timeout.                                                  |
| `AI_PROVIDER_MAX_RETRIES`        | `2`        | Retry budget.                                                      |
| `AI_PROVIDER_FAILOVER_ENABLED`   | `true`     | If selected provider fails, try fallback.                          |

\* Current preview deployment already has `AI_GATEWAY_ENABLED=true`. On a
brand-new deployment, this ships `false` per `.env.example`.

### 3.3 Module deployment flags (deployment-scope)

Each AI capability must be independently enabled at the deployment level
before any tenant can enable it. Turning one off at deployment blocks it
for every tenant.

| Key                                  | Module                     |
| ------------------------------------ | -------------------------- |
| `AI_DAILY_REPORT_SUMMARY_ENABLED`    | Daily Report summarisation |
| `AI_PHOTO_VISION_ENABLED`            | Photo Intelligence         |
| `AI_PM_INTELLIGENCE_ENABLED`         | PM dashboards / briefs     |
| `AI_ADMIN_INTELLIGENCE_ENABLED`      | Admin/executive briefs     |
| `AI_SAFETY_INTELLIGENCE_ENABLED`     | Safety intelligence        |
| `AI_TRANSLATION_ENABLED`             | EN↔ES translation          |

`AI_ADMIN_INTELLIGENCE_ENABLED` is a **distinct** flag from
`AI_PM_INTELLIGENCE_ENABLED` (lock test
`test_admin_intelligence_flag_independent_of_pm_intelligence`).

### 3.4 Tenant-scope default flags

If a given tenant has no override doc in `tenant_ai_capabilities`, these
env-level defaults apply. See `AI_CONFIG_001_TENANT_OPTIONALITY.md` for
the Mongo override schema.

| Key                                        | Controls the tenant default for… |
| ------------------------------------------ | -------------------------------- |
| `TENANT_AI_ENABLED`                        | Whole tenant AI envelope         |
| `TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED`   | DR summary module                |
| `TENANT_AI_PHOTO_INTELLIGENCE_ENABLED`     | Photo intelligence module        |
| `TENANT_AI_PM_INTELLIGENCE_ENABLED`        | PM intelligence module           |
| `TENANT_AI_ADMIN_INTELLIGENCE_ENABLED`     | Admin intelligence module        |
| `TENANT_AI_SAFETY_INTELLIGENCE_ENABLED`    | Safety intelligence module       |
| `TENANT_AI_TRANSLATION_ENABLED`            | Translation module               |

All ship `false` by default. AI is opt-in per tenant.

### 3.5 Daily Report UX capability flags (not AI-gated)

These are independent of the AI layer — they govern V1 form workflow.
Kept in the same block for operator convenience.

| Key                                        | Default |
| ------------------------------------------ | ------- |
| `DR_DAILY_OPERATIONAL_SUMMARY_ENABLED`     | `false` |
| `DR_PHOTO_INTELLIGENCE_ENABLED`            | `false` |
| `DR_EN_ES_MODE_ENABLED`                    | `true`  |
| `DR_CANONICAL_ENGLISH_SUBMIT_ENABLED`      | `true`  |

## 4. Precedence chain (evaluated top-to-bottom)

The resolver returns `enabled=True` **only** when every link passes:

1. `AI_GATEWAY_ENABLED == true` (global)
2. Tenant AI enabled — either
   - Mongo `tenant_ai_capabilities[{tenant_id}].tenant_ai_enabled == true`, or
   - `TENANT_AI_ENABLED == true` (env default) if no Mongo doc exists
3. `AI_<MODULE>_ENABLED == true` (deployment module flag)
4. Tenant module flag `true` — Mongo per-tenant override or its env default
5. Selected provider passes: `AI_PROVIDER_<X>_ENABLED == true` AND
   `<X>_API_KEY` is non-empty

Any failure short-circuits with a machine-readable `reason_disabled`:

- `ai_gateway_disabled_global`
- `tenant_ai_disabled`
- `module_disabled_global:<module>`
- `module_disabled_tenant:<module>`
- `no_provider_available`
- `unknown_module`

`reason_disabled` is for logs only. The field UI never surfaces "AI is off".

## 5. Never-commit contract

Provider API key values must **never** be committed to any file in git,
including `backend/.env`. The values live only in the running container's
env, populated by the Emergent Secrets UI.

Lock tests enforce this:

- `test_env_example_never_contains_real_key_values`
- `test_backend_env_provider_keys_are_placeholders_not_real_keys`

If either regresses, CI fails.

## 6. Admin visibility

`GET /api/ai/gateway/status` (admin-gated) returns a sanitised snapshot
of the switchboard: booleans for every flag and `key_present` booleans
for the three provider keys — never raw key values.

Lock test `test_status_snapshot_never_leaks_raw_keys` asserts this.

## 7. Change control

Adding a new AI module requires **all** of:

1. New entry in `MODULE_ENV_MAP` in `services/ai_gateway/capabilities.py`
   with a distinct deployment env flag and a distinct tenant env flag.
2. Add both flags to `/app/backend/.env` and `/app/.env.example`
   (default `false`).
3. Extend `test_backend_env_exposes_every_ai_placeholder_to_secrets_ui`
   with the new keys.
4. Route every callsite through `resolve_ai_capabilities()` before any
   provider call. Never import the resolver at module load in a non-AI
   route (lock test
   `test_daily_report_submit_module_does_not_import_resolver_at_load_time`).

## 8. References

- Resolver: `/app/backend/services/ai_gateway/capabilities.py`
- Admin route: `/app/backend/routes/ai_gateway_status.py`
- Env template: `/app/.env.example`
- Live env: `/app/backend/.env`
- Lock envelope: `/app/backend/tests/test_ai_config_001_capabilities.py`
- Companion docs:
  - `AI_CONFIG_001_TENANT_OPTIONALITY.md`
  - `AI_CONFIG_001_DISABLED_MODE_PROOF.md`
