# ODS-001 · Test Report

## Test files touched or added

- `tests/test_ai_gateway.py` — 9 tests (env snapshot no-leak, task router, task-router env override, registry, disabled state, missing-key fallback, envelope serialization, adapter interface contract, snapshot no-secrets).
- `tests/test_ods_001_spine.py` — 11 tests (fact-type + source-type locks, envelope validation happy + sad paths, coercers, pure fact builder, unique source_item_ids, in-memory store guard, route mount, no-V1-writes guard, flags default off).
- `tests/test_dr_roi_001a_b_shell.py` — 13 tests (pre-existing DR-V2 lock tests) updated to reflect new runtime parity (1455 / 1459 / 1277) after ODS additive mount.
- `tests/test_dr_roi_001c_ai_service.py` — 9 tests (pre-existing DR-V2 unit tests, unchanged).
- `tests/test_track_22_2_app_js_route_extraction.py` — 13 tests updated to same new baseline.

## Total: **55 unit / integration tests · 55/55 GREEN**

```
$ cd /app/backend && python -m pytest \
    tests/test_ai_gateway.py \
    tests/test_ods_001_spine.py \
    tests/test_dr_roi_001a_b_shell.py \
    tests/test_dr_roi_001c_ai_service.py \
    tests/test_track_22_2_app_js_route_extraction.py -q
............................................. [100%]
55 passed in 5.16s
```

## Live e2e proof (curl, this session)

- `POST /api/dr-v2/drafts` → 200 → 7 facts emitted asynchronously to `operational_facts`.
- `GET  /api/ods/facts?project_id=OD-100` → 7 current facts (labor×3, equipment×1, production×1, delay×1, weather×1).
- `GET  /api/ods/projects/OD-100/summary` → labor_hours 24.0, equipment_hours 6.5.
- `GET  /api/ods/snapshots?project_id=OD-100&date=2026-07-05` → production {Trench: 120}, delay {missing_material: 2h}.
- `POST /api/ods/ingest/dr-v2/{report_id}` → facts_inserted 7, facts_superseded 7 (idempotency proven).
- `GET  /api/ods/meta` → gateway meta with 3 registered adapters (anthropic, google, openai), task routes, provider-key presence.
- `POST /api/dr-v2/ai/synthesize` → real Claude Sonnet 4.5 response routed via the gateway; confidence 0.85 aggregate; per-agent 0.85–0.95.

## What we did NOT test in this session

- Live OpenAI text (adapter interface complete; live call not exercised — no failure in flow, request/response shape is identical to Anthropic and unit tests cover the schema contract).
- Live Google Gemini (SDK wiring deferred until `GOOGLE_AI_API_KEY` provisioned; scaffold returns valid fallback envelope).
- Photo Vision (scaffold only; Phase D of DR-ROI-001).
- Cross-project admin rollup (Phase E).
- V1 daily-report ingestor (Phase E).

## Regressions

None detected.
