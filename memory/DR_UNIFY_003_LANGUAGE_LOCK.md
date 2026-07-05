# DR-UNIFY-003 · Language Lock

## Doctrine

The field surface (`NewDailyReport.jsx`) and any backend response that
crosses the wire to the field surface must **never** expose:

- V1 / V2 vocabulary ("Try V2", "next generation", `"v1"`, `"v2"`).
- AI implementation vocabulary (AI agent, model, provider, token cost,
  cost meter).

Internal filenames, tests, and comments may still reference `v2`
where a rename would be unsafe — but they must never appear in user
copy or in JSON response payloads.

## Enforcement — locked by pytest

| Test                                                                     | Guards                                             |
| ------------------------------------------------------------------------ | -------------------------------------------------- |
| `test_new_daily_report_form_has_no_v1_or_v2_user_facing_language`        | Field form JSX source                              |
| `test_no_user_facing_ai_language_in_daily_summary_backend_route`         | Summary route Python source                        |
| `test_daily_summary_endpoints_are_under_canonical_prefix`                | Backend route paths                                |
| `test_composer_output_contains_no_ai_language` (DR-CUTOVER-002)          | Composed summary response body                     |
| `test_field_ui_wire_response_contains_no_ai_agent_language` (DR-CUTOVER-002)| Both summary endpoint response bodies           |
| `test_response_never_leaks_provider_key` (DR-CUTOVER-002)                | Provider key value never appears in response text  |
| `test_status_snapshot_never_leaks_raw_keys` (AI-CONFIG-001)              | Admin config-status endpoint                       |
| `test_backend_env_provider_keys_are_placeholders_not_real_keys` (AI-CONFIG-001) | `backend/.env` shipped with empty placeholders |

## Enforcement — locked live

Playwright smoke on `/daily-report/v2` (which now redirects to
`/daily/submit`) verifies the rendered HTML contains none of:

- `try v2`
- `next generation`
- `anthropic`
- `openai`
- `gemini`
- `"model":`
- `"provider":`

The same scan is repeated by the testing agent every time a track
touches the field form.

## Banned string index

```
User-facing (JSX / HTML / user-visible text):
    "V1"  "V2"  "Try V2"  "next generation"  "DR-V2"
    "AI generated"  "AI-generated"  "AI agent"
    "model:"  "provider:"  "token cost"  "cost meter"

Wire (response body scanned as lower-case string):
    "anthropic"  "openai"  "gemini"  "gpt "  "claude"
    "\"model\":"  "\"provider\":"  "\"token_cost\":"
    "sk-" prefix (real API keys)
```

## Internal exceptions

Filenames explicitly whitelisted (renames deferred to DR-UNIFY-004+):

- `backend/routes/dr_v2.py`
- `backend/routes/dr_v2_canonicalize.py`
- `backend/routes/dr_v2_photos.py`
- `backend/routes/dr_v2_pdf.py`
- `frontend/src/pages/daily-report-v2/**`
- `frontend/src/lib/drV2Api.js`
- `frontend/src/lib/dailyReportV2Lang.js`
- `frontend/src/lib/dailyReportV2Flag.js`

None of these files are surfaced in the field UI; each one is either
purely internal or only reachable behind admin-strict auth.
