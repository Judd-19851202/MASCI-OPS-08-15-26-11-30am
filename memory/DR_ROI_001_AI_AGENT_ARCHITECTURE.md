# DR-ROI-001 · AI Agent Architecture

**Date:** 2026-02-05
**Wiring status:** NOT wired this session. Design contract only.
**Integration playbook trigger:** `integration_playbook_expert_v2` must be called BEFORE any AI code lands (DR-ROI-001C entry point).

## Multi-agent lineup

| Agent | Model | Role | Trigger | Cost tier |
|---|---|---|---|---|
| **Operations Agent** | Claude Sonnet 4.5 | Analyzes activity cards · production quantities · progress · derives operations summary and missing-quantity questions | Debounced on activity_cards / production changes | Light |
| **Equipment Agent** | Claude Sonnet 4.5 | Analyzes equipment hours · breakdowns · idle · productivity/equipment mismatch | Debounced on equipment / activity_cards changes | Light |
| **Delay Agent** | Claude Sonnet 4.5 | Analyzes constraint cards · weather · schedule risk · responsible party · PM action items | Debounced on constraint_cards changes | Light |
| **Safety Agent** | Claude Sonnet 4.5 | Analyzes safety section + escalation flags + JHA/JHP gates · never invents incidents | Debounced on safety-gate changes | Light |
| **Quality Agent** | Claude Sonnet 4.5 | Analyzes quality/inspection issues · rework indicators · flags | Debounced on quality-relevant changes | Light |
| **Photo Vision Agent** | **GPT-5.2 Vision** | Analyzes uploaded photos · detects work types / equipment / materials / safety conditions / quality issues · suggests activity-photo links · never generates final narrative | Explicit "Analyze Photos" or pre-submit only | Heavy |
| **PM Intelligence Agent** | Claude Sonnet 4.5 | Consumes all other agent outputs · produces PM brief · action items · KPI signals · tomorrow-readiness risks | Explicit "Generate PM Brief" or pre-submit | Medium |
| **Narrative Agent** | Claude Sonnet 4.5 | Composes the final draft daily narrative from verified evidence only · outputs sentence-level source references | Explicit "Preview AI Summary" or pre-submit | Medium-Heavy |
| **Confidence & Validation Agent** | Claude Sonnet 4.5 | Scores every AI conclusion · flags uncertainty · requests supervisor clarification when confidence < threshold | Runs at end of every agent invocation | Very light |

## Orchestration

```
                           ┌─── Field-change event stream ───┐
                           │                                 │
Supervisor edits ─────────▶│  Debouncer (300ms · block-scoped)
                           │                                 │
                           └─────────┬───────────────────────┘
                                     │
                        ┌────────────┼────────────┐
                        ▼            ▼            ▼
                   Operations    Equipment      Delay
                    Agent         Agent         Agent
                        │            │            │
                        └──────┬─────┴─────┬──────┘
                               ▼           ▼
                          Safety Agent   Quality Agent
                               │           │
                               └─────┬─────┘
                                     │
                                     ▼
                          Confidence & Validation Agent
                                     │
                                     ▼
                    ┌────────  Explicit trigger  ────────┐
                    │                                    │
              "Preview Summary"                    "Analyze Photos"
                    │                                    │
                    ▼                                    ▼
             Narrative Agent                    Photo Vision Agent
                    │                                    │
                    └────────────┬──── evidence ─────────┘
                                 ▼
                          PM Intelligence Agent
                                 │
                                 ▼
                    Supervisor Approval Panel
                    (accept · edit · regenerate)
                                 │
                                 ▼
                          Submit → Report doc + KPI collection
```

## Evidence trace requirements

Every AI-generated sentence MUST include:
```json
{
  "text": "...",
  "evidence_ids": ["activity_card:uuid1", "constraint_card:uuid2", "photo:ph:abc"],
  "agent": "NarrativeAgent",
  "confidence": 0.92
}
```

If an agent cannot produce evidence-linked output for a candidate sentence, it MUST either:
- Drop the sentence, OR
- Emit an `ai_questions[]` entry: `"You entered 12 loads of base but no activity link. Which activity should this attach to?"`

## Zero-invention guardrails (enforced at code level in Track C)

1. **Structured-facts-only prompt** — Reasoning prompts feed structured JSON (never raw supervisor free text alone).
2. **Evidence-required output schema** — Agent responses are structured JSON with `evidence_ids[]` mandatory; empty `evidence_ids[]` → sentence rejected.
3. **Confidence gate** — Any sentence with confidence < 0.70 is dropped or converted to a question.
4. **Photo-evidence isolation** — Photo Vision Agent output is EVIDENCE fed back into reasoning agents. Vision agent never generates final narrative.
5. **Supervisor-final rule** — `final_approved_narrative` is populated ONLY after `supervisor_ai_approval_state ∈ {"accepted", "edited"}`.
6. **Audit log** — Every AI action + supervisor override → `ai_approval_log[]` entry.

## Model versioning

`ai_source_trace.model_versions` must record the exact model version used for each agent invocation. When models are upgraded (e.g., Claude Sonnet 5.0), historic reports remain readable and their AI trace remains explainable.

## Emergent LLM Key usage

Per Emergent Integrations doctrine:
- Claude Sonnet 4.5 → **Emergent LLM Key** (Universal Key)
- GPT-5.2 Vision → **Emergent LLM Key** (Universal Key covers OpenAI image generation + Vision reads via the emergentintegrations library)

**BEFORE any code lands in Track C:** `integration_playbook_expert_v2` MUST be called for both:
1. `INTEGRATION: Claude Sonnet 4.5 (text) for multi-agent orchestration in a FastAPI backend`
2. `INTEGRATION: GPT-5.2 Vision for photo analysis in a FastAPI backend`

## Rate limiting + cost controls

- **Per-report ceiling:** ≤ 12 lightweight agent calls per report per session
- **Per-report vision budget:** ≤ 1 Photo Vision call (batch all photos in a single request)
- **Per-report narrative budget:** ≤ 3 narrative regeneration cycles
- **Session throttle:** ≤ 30 debounced agent-fires per minute per supervisor
- **Cache key:** SHA-256 of the JSON-canonicalized evidence input → skip identical repeat calls

## Failure modes

| Failure | Behavior |
|---|---|
| LLM API timeout | Show inline "AI temporarily unavailable · you can still submit manually" · never block supervisor |
| LLM returns invalid JSON | Log to `ai_approval_log[]` · retry once with strict prompt · then fall back to "AI unavailable" banner |
| Evidence trace missing | Drop that sentence; do not present it |
| Confidence < 0.70 | Emit question in `ai_questions[]` |
| Vision model fails | Photos remain in place; Photo Intel panel shows "vision temporarily unavailable" |
| Supervisor never approves | Submit is BLOCKED unless supervisor explicitly clicks "Submit without AI summary" (which is logged) |

## Pluggability

Every agent implements a common Python protocol:
```python
class Agent(Protocol):
    name: str
    model_id: str
    async def analyze(self, evidence: Evidence, ctx: AgentContext) -> AgentOutput:
        ...
```

To swap Claude Sonnet 4.5 → Claude Sonnet 5.0 later:
1. Update `model_id` in the agent's config.
2. Bump `ai_source_trace.model_versions`.
3. Zero DR schema change. Zero UI change.

## Attestation

This document is a design contract. No AI code has been written this session. Track C entry point will call `integration_playbook_expert_v2` first, then implement per the returned playbook.
