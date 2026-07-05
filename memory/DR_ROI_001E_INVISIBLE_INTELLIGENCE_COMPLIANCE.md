# DR-ROI-001E · Invisible Intelligence Compliance

## Doctrine
The user has established a strict "Invisible Intelligence" rule for the
operator-facing surface:
- No model names.
- No provider names.
- No agent names.
- No token/cost metrics.
- No LLM-branded phrasing ("AI says…", "Claude thinks…", etc.).

Field supervisors, PMs, and executives should experience the platform
as **operational intelligence**, not "an AI tool". The intelligence is
present because it improves the work — never because it advertises
itself.

## Enforcement Mechanism
Permanent lock test: `backend/tests/test_dr_roi_001e_invisible_intelligence.py`

Scans the five intelligence surface files:
- `frontend/src/pages/PmOperationalIntelligence.jsx`
- `frontend/src/pages/AdminOperationalIntelligence.jsx`
- `frontend/src/pages/ExecutiveOperationalIntelligence.jsx`
- `frontend/src/components/ods/HorizonPrimitives.jsx`
- `frontend/src/lib/odsIntelligenceApi.js`

For any occurrence of (case-insensitive):
`claude`, `anthropic`, `gpt-`, `gpt5`, `gpt 5`, `openai`, `gemini`,
`nano banana`, `sonnet `, `opus `, `haiku`, `llm`, `model:`, `provider:`,
`token cost`, `tokens used`, `cost per token`, `ai agent`,
`prompt tokens`, `completion tokens`.

Plus positive assertions:
- `"What Happened"`, `"What Is Happening"`, `"What Needs Attention"`
  must all appear on every dashboard file.
- `EvidenceFooter` must be imported/used on every dashboard.
- No chart library imports (`recharts`, `chart.js`, `@nivo/*`, `victory`).
- No mock-data markers (`MOCK_DATA`, `SAMPLE_DATA`, `DEMO_ROWS`,
  `lorem ipsum`).

## Backend Sibling Guardrail
`test_dr_roi_001e_intelligence.py::test_no_provider_names_leak_in_route_module`
asserts that `routes/ods_intelligence.py` never emits `"model":`,
`"provider":`, `"api_key"`, `anthropic-sdk`, `claude-`, or `openai/gpt-`
in any response body.

## Practical Consequence
Any future PR that tries to add "Powered by Claude Sonnet 4.5" or a
token-cost meter to these dashboards fails the lock test at CI time.
Invisible Intelligence is now a structural invariant.
