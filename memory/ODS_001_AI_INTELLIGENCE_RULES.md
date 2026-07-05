# ODS-001 · AI / Intelligence Integration Rules

## First principles

1. **AI is never the source of truth.** Supervisor-entered operational facts are.
2. **AI reads the spine, writes derived intelligence.** All AI outputs are stored as `intelligence_fact` records with `sources_facts: [fact_id]` traceability.
3. **AI outputs are always evidence-backed.** Every claim cites specific fields on the source draft; missing facts appear as `uncertainties`.
4. **AI outputs are confidence-scored.** `confidence ∈ [0, 1]`; UI shows aggregate = min of per-agent for weakest-link honesty.
5. **AI outputs are editable and supervisor-approved.** Nothing auto-approves.
6. **Provider names, model names, and cost/token meters are never shown to field users.** Provider/model metadata is stored in audit logs and admin telemetry only.
7. **The AI Gateway is the ONLY entry point.** Workflows call `Gateway.dispatch(task_type=…)`. Concrete SDKs are behind adapters.
8. **Any provider can be swapped without changing schemas.** Anthropic ↔ OpenAI ↔ Gemini all return the same `AiEnvelope`.
9. **Photo Vision is pluggable.** Interface identical to text; concrete OpenAI/Gemini vision adapters land in DR-ROI-001D.
10. **`intelligence_fact` cannot cite another `intelligence_fact`.** Prevents recursive AI-on-AI drift.

## Audience-scoped intelligence

`intelligence_fact.payload.audience ∈ { supervisor, pm, admin, executive }`. A single project can carry parallel narratives for each audience — same facts, different lens. Supervisor narrative is generated pre-submit; PM and executive briefs are generated post-submit and never gate the field workflow.

## Failure semantics

- If the AI Gateway is disabled or all providers fail, the workflow receives a valid `AiEnvelope` with `ai_available=false` and continues.
- The supervisor can always submit manually.

## Audit

Every AI-derived fact records `model`, `provider`, `generated_at`, `confidence`, `approved_by`, `approved_at`, and its `sources_facts` list. Admin telemetry surfaces these; the field UI never does.
