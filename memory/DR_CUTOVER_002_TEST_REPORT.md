# DR-CUTOVER-002 · Test Report

**Result:** ✅ **68/68 pytest tests passing** (22 new + 17 AI-ADMIN-001 + 17 AI-CONFIG-001 + 12 already-existing DR-CUTOVER regression). Testing agent v3 fork end-to-end: **100% backend / 100% frontend**, `retest_needed=false`, zero critical or minor issues.

Run command:

```
cd /app/backend && python -m pytest \
  tests/test_dr_cutover_002_daily_summary.py \
  tests/test_ai_admin_001_config.py \
  tests/test_ai_config_001_capabilities.py --tb=short
```

## 1. Lock envelope — DR-CUTOVER-002 (22 tests)

Every test proves one invariant. All tests use an in-memory fake
Mongo + a FastAPI TestClient — no live provider call, no real DB
required.

| #  | Invariant                                                                                          | Test                                                                       |
| -- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 1  | AI disabled → draft returns `enabled=false`, never 5xx.                                            | `test_ai_disabled_draft_returns_enabled_false_never_500`                   |
| 2  | Tenant AI off → summary blocked with reason `tenant_ai_disabled`.                                  | `test_tenant_ai_off_blocks_summary_generation`                             |
| 3  | Module off → summary blocked with reason `module_disabled_global:…`.                               | `test_module_off_blocks_summary_generation`                                |
| 4  | Provider flag on but key blank → `no_provider_available`, not 500.                                 | `test_missing_provider_key_reports_no_provider_not_500`                    |
| 5  | Enabled path composes a deterministic, evidence-only summary.                                      | `test_enabled_path_returns_deterministic_composed_summary`                 |
| 6  | Composer never invents safety incidents.                                                           | `test_composer_never_invents_a_safety_incident`                            |
| 7  | Composer never mentions photos when none are attached.                                             | `test_composer_never_mentions_photos_when_none_attached`                   |
| 8  | Composer ignores unrecognised keys (never leaks arbitrary strings).                                | `test_composer_uses_only_allowed_fields`                                   |
| 9  | Response body contains no AI/model/provider vocabulary.                                            | `test_composer_output_contains_no_ai_language`                             |
| 10 | Accept persists `daily_operational_summary_*` onto the doc — nothing else changes.                 | `test_accept_persists_summary_onto_daily_report_doc`                       |
| 11 | Accept 404s for unknown report_id.                                                                 | `test_accept_returns_404_when_report_missing`                              |
| 12 | Accept rejects empty summary_text (422).                                                           | `test_accept_rejects_empty_summary_text`                                   |
| 13 | Accept rejects oversize summary_text (422).                                                        | `test_accept_truncates_ludicrously_long_input`                             |
| 14 | Adversarial fields (`ANTHROPIC_API_KEY`, `id`, `masci_crews`) are silently dropped.                | `test_accept_never_writes_a_provider_key_or_token_field`                   |
| 15 | Accept emits exactly one `intelligence_fact` when ODS enabled.                                     | `test_accept_emits_intelligence_fact_when_ods_enabled`                     |
| 16 | Repeated accepts idempotently supersede prior `is_current` fact.                                   | `test_accept_supersedes_prior_intelligence_fact_idempotency`               |
| 17 | Language "es" persists; unknown language falls back to "en".                                       | `test_language_flag_accepts_es_and_falls_back_to_en`                       |
| 18 | Provider key value never leaks into response body.                                                 | `test_response_never_leaks_provider_key`                                   |
| 19 | Router source never references dr-v2 aliases.                                                      | `test_dr_v2_shell_not_exposed_from_daily_summary_route`                    |
| 20 | Both endpoints' responses avoid AI-agent JSON keys.                                                | `test_field_ui_wire_response_contains_no_ai_agent_language`                |
| 21 | V1 daily_reports route file has zero import of the new module (loose coupling).                    | `test_daily_reports_route_still_ignorant_of_ai_summary`                    |
| 22 | Composer degrades gracefully on an empty payload.                                                  | `test_composer_handles_completely_empty_payload_gracefully`                |

## 2. Regression envelopes

- `test_ai_admin_001_config.py` — **17/17 pass** (AI-ADMIN-001 track).
- `test_ai_config_001_capabilities.py` — **17/17 pass** (AI-CONFIG-001 track).

## 3. Live preview verification (testing agent v3)

Backend HTTP checks against the live preview URL:

- `POST /api/daily-reports/summary/draft` — `enabled=false, reason=tenant_ai_disabled`, HTTP 200 (not 5xx).
- `POST /api/daily-reports/summary/draft` with empty payload — HTTP 200, disabled path.
- `POST /api/daily-reports/nonexistent/summary/accept` — HTTP 404.
- `POST /api/daily-reports/<real-id>/summary/accept` with empty text — HTTP 422.
- `POST /api/daily-reports` — full public submit succeeds (V1 unchanged).
- `GET /api/daily-reports/<id>` (super-admin) — returns the created report with `masci_crews` byte-identical.

Frontend HTTP + DOM checks:

- `/daily/submit` renders `NewDailyReport`.
- `data-testid="daily-operational-summary-section"` renders BEFORE
  `data-testid="band-sign-off"` in the DOM order.
- All button testids present: `daily-summary-draft-btn`,
  `daily-summary-accept-btn`, `daily-summary-clear-btn`.
- Textarea `daily-summary-textarea` renders.
- **Zero banned AI terms** on page: "AI generated", "anthropic", "openai",
  "gemini", "GPT ", "AI agent", "model:", "provider:", "token cost" —
  none appear in HTML.
- Disabled-path toast shows a non-alarming message when Draft Summary
  is clicked (tenant AI is off in preview by design).
- Manual-typing + Accept flow produces the accepted badge and toast.
- `/daily-report/v2` is not present anywhere in the /daily/submit page HTML.
- EN/ES toggle buttons still present.
- `/admin/ai-configuration` (AI-ADMIN-001 page) still renders when
  authed as super-admin.

**Success rate:** backend 100% · frontend 100%.
**Retest needed:** No.
**Critical / minor issues found:** None.

## 4. Live preview screenshot

Captured by the main agent before the testing agent run:
`/daily/submit` shows the Daily Operational Summary section rendered
immediately before the Sign-Off band, matching the design spec.

## 5. Non-goals

- No live LLM API call in tests (composer is deterministic).
- No live email delivery in tests (`EMAIL_SAFETY_MODE=strict`
  is respected — new code does not emit any email).
- No PDF golden-file test yet — see follow-up P2 in
  `DR_CUTOVER_002_HR_EMAIL_PDF_PROTECTION.md`.

## 6. Acceptance criteria

- ✅ 22 new backend lock tests green.
- ✅ 34 regression tests (AI-CONFIG-001 + AI-ADMIN-001) green.
- ✅ Full frontend + backend testing agent run — 100% / 100%.
- ✅ Live preview smoke — section renders, no AI vocabulary, disabled
  path is graceful, submit path untouched.
- ✅ HR crew data preserved, ODS facts still emit, PM/Admin dashboards
  still render deterministic data.
- ✅ Docs, PRD, changelog, tech-debt, manifest all updated.
