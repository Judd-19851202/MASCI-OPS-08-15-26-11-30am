# ODS-001 · AI Provider Gateway (Model-Agnostic)

The Operational Data Spine sits behind an internal **ForgedOps AI Gateway** that abstracts every LLM provider. No workflow ever imports an Anthropic / OpenAI / Google SDK directly. Every AI-powered flow calls the gateway with a **task type** and receives a canonical `AiEnvelope`.

## Architecture

```
Workflow (DR-V2, PM brief, Photo Vision, ...)
       │
       ▼
services.ai_gateway.get_gateway().dispatch(task_type=…, system=…, user_payload=…)
       │
       ▼
task_router.route(task_type)  →  (provider_name, model_id)
       │
       ▼
Adapter (anthropic | openai | google)  →  provider SDK
       │
       ▼
AiEnvelope { task, narrative, confidence, evidence_refs, sources_used,
             uncertainties, provider, model, generated_at, ai_available, fallback_reason }
```

## Public modules

- `services/ai_gateway/__init__.py` — public exports (`Gateway`, `get_gateway`, `TASK_ROUTES`, `AiEnvelope`, `env_snapshot`).
- `services/ai_gateway/registry.py` — Gateway class + adapter registry + retries + failover.
- `services/ai_gateway/task_router.py` — Task → (provider, model) map, env-override capable.
- `services/ai_gateway/env.py` — All provider-neutral env access.
- `services/ai_gateway/envelope.py` — Canonical `AiEnvelope` dataclass.
- `services/ai_gateway/adapters/anthropic_adapter.py` — Claude via emergentintegrations LlmChat.
- `services/ai_gateway/adapters/openai_adapter.py` — GPT (text real, vision scaffolded).
- `services/ai_gateway/adapters/google_adapter.py` — Gemini scaffold (interface complete, real SDK deferred until `GOOGLE_AI_API_KEY` provisioned).

## Task types (11)

`operational_narrative`, `production_intelligence`, `delay_intelligence`, `safety_intelligence`, `equipment_intelligence`, `photo_vision`, `pm_brief`, `executive_brief`, `confidence_validation`, `evidence_trace`, `future_task`.

## Default routing plan

| Task | Provider | Model |
| --- | --- | --- |
| operational_narrative, pm_brief, executive_brief, delay_intelligence, production_intelligence, safety_intelligence, equipment_intelligence, confidence_validation, evidence_trace | anthropic | claude-sonnet-4-5-20250929 |
| photo_vision | openai | gpt-5.2-vision (scaffold) |
| future_task | anthropic | claude-sonnet-4-5-20250929 |

Override with `AI_TASK_ROUTE__<task>="provider:model"` env var.

## Env vars (all provider-neutral)

`AI_GATEWAY_ENABLED`, `AI_DEFAULT_PROVIDER`, `AI_DEFAULT_TEXT_MODEL`, `AI_DEFAULT_VISION_PROVIDER`, `AI_DEFAULT_VISION_MODEL`, `AI_PROVIDER_TIMEOUT_MS`, `AI_PROVIDER_MAX_RETRIES`, `AI_PROVIDER_FAILOVER_ENABLED`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_AI_API_KEY`, `EMERGENT_LLM_KEY` (universal backstop).

## Failover

When `AI_PROVIDER_FAILOVER_ENABLED=true`, the gateway retries a failed primary provider (max `AI_PROVIDER_MAX_RETRIES`), then attempts the failover order `[anthropic, openai, google]` skipping the failed primary. Any provider without a key is skipped. If everything fails, the workflow receives a valid `AiEnvelope` with `ai_available=false` and a `fallback_reason` — the operational surface never crashes.

## Rules (invariants)

- No API keys in source.
- No provider names shown to field users.
- No AI cost meter in the field UI.
- `env_snapshot()` never leaks raw key values — only `providers_with_keys: { anthropic: bool, ... }`.
- Every workflow output remains evidence-backed, confidence-scored, editable, and supervisor-approved where applicable.
- AI is never the source of truth.
- Structured operational facts (`operational_facts` collection) remain the source of truth.
- AI reads the spine and writes derived intelligence only.

## Backward compatibility

`services/dr_ai/emergent_provider.py::EmergentClaudeProvider` still exists but now delegates through the gateway. Callers unchanged. Existing envelopes (`AiSynthesisResult`) still returned.
