# DR-UNIFY-004 · Security Certification

## Authentication / Authorization

- Admin config surface (`/api/admin/ai/*`) gated by
  `require_admin_strict`. PM/HR/Safety/Shop/Dispatch/Field tokens
  are rejected with 401. Verified live.
- Field submit (`POST /api/daily-reports`) is public and rate-limited
  via `rate_limit_public_post` (unchanged from prior tracks).
- Summary endpoints (`POST /api/daily-reports/summary/draft`,
  `POST /api/daily-reports/{id}/summary/accept`) reuse the same
  rate-limit gate.

## Secret exposure

- **Zero raw API key values** in any response, any audit blob, any
  rendered HTML, or any log line. Locked by:
  - `test_status_endpoint_returns_no_raw_key_values` (AI-ADMIN-001)
  - `test_provider_test_endpoint_returns_booleans_only`
  - `test_update_writes_audit_entry_with_before_after_and_actor`
  - `test_response_never_leaks_provider_key` (DR-CUTOVER-002)
  - `test_backend_env_provider_keys_are_placeholders_not_real_keys`
    (AI-CONFIG-001)
- **Provider API keys ship as empty placeholders in `backend/.env`.**
  Real values are pasted via the Emergent Secrets UI at deploy time
  and never enter the git tree.
- Playwright HTML scan on `/daily/submit` and `/admin/ai-configuration`
  confirms no `sk-*` string in rendered markup.

## Prompt / provider / model leakage

- Backend responses never expose `"model": …`, `"provider": …`, or
  `"token_cost": …` fields. Enforced by
  `test_field_ui_wire_response_contains_no_ai_agent_language` and
  `test_composer_output_contains_no_ai_language`.
- The composer never issues an LLM call, so there is no prompt to
  leak.

## Audit trail

- Every AI-ADMIN-001 mutation writes to `tenant_ai_capability_audit`
  with actor, before, after, changed fields, note, timestamp, IP,
  user-agent — never a secret.
- Every DR-CUTOVER-002 acceptance emits an `intelligence_fact`
  containing only `audience`, `agent`, `language`, `source`, `chars`.
  No secrets, no PII.

## Denial telemetry

- `require_admin_strict` denial channel unchanged; existing
  `_record_access_denial` continues to log 401 events.

## Environment / repo hygiene

- Deployment audit: no hardcoded secrets, no hardcoded URLs,
  no `load_dotenv(override=True)`.
- CORS configured for production (accepts `*` during preview; hardened
  by Emergent deployment).
- No provider adapter changes; no new dependencies.
- No debug endpoints exposed publicly.

**Verdict:** Security surface preserved. Additive changes strictly
respect the AI-CONFIG-001 "never commit real values" contract.
Certified.
