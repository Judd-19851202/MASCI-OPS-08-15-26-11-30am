# DR-UNIFY-004 · AI Certification

## Doctrine (invariants under lock)

- **AI is optional per tenant, per module, per provider.**
- Platform runs 100% with every AI flag off and every provider key
  blank.
- Field UI is byte-identical whether AI is on or off (Invisible
  Intelligence).
- No AI vocabulary in field UI or wire payloads.
- Provider API keys never committed to git; pasted via Emergent
  Secrets UI at deploy time.

## Resolver contract

`resolve_ai_capabilities(db, tenant_id, module)` — the single
authoritative gate. Five-link chain:

1. `AI_GATEWAY_ENABLED` (deployment global)
2. Tenant AI enabled (Mongo `tenant_ai_capabilities` doc, else
   `TENANT_AI_ENABLED` env default)
3. Deployment module flag (`AI_<MODULE>_ENABLED`)
4. Tenant module flag (Mongo override, else `TENANT_AI_<MODULE>_ENABLED`)
5. Selected provider ready (`AI_PROVIDER_<X>_ENABLED` AND
   `<X>_API_KEY` non-empty)

Every link's failure yields a machine-readable `reason_disabled`
code. UI never surfaces the code — it maps to a warm non-alarming
message.

## Admin surface

`/admin/ai-configuration` (admin-strict) exposes:

- System Status (gateway + 3 providers + failover)
- Provider Routing (read-only defaults)
- Tenant selector
- Tenant AI Enablement (master + 6 module toggles)
- Disabled-Mode Guarantees panel (always-true invariants)
- Audit Log

## Live disabled-mode proof

On preview: `TENANT_AI_ENABLED=false`. Live curl:

```
POST /api/daily-reports/summary/draft
{ payload: {...} }
→ HTTP 200
{ ok: true, enabled: false, reason_disabled: "tenant_ai_disabled",
  summary_text: null, ... }
```

Never a 5xx. Submit continues. Daily report saves. Emails send.
Photos upload. ODS emits facts.

## Modules

| Module                  | Deployment flag                      | Tenant flag                                     |
| ----------------------- | ------------------------------------ | ------------------------------------------------ |
| Daily Report Summary    | `AI_DAILY_REPORT_SUMMARY_ENABLED`    | `TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED`         |
| Photo Intelligence      | `AI_PHOTO_VISION_ENABLED`            | `TENANT_AI_PHOTO_INTELLIGENCE_ENABLED`           |
| PM Intelligence         | `AI_PM_INTELLIGENCE_ENABLED`         | `TENANT_AI_PM_INTELLIGENCE_ENABLED`              |
| Admin Intelligence      | `AI_ADMIN_INTELLIGENCE_ENABLED`      | `TENANT_AI_ADMIN_INTELLIGENCE_ENABLED`           |
| Safety Intelligence     | `AI_SAFETY_INTELLIGENCE_ENABLED`     | `TENANT_AI_SAFETY_INTELLIGENCE_ENABLED`          |
| Translation             | `AI_TRANSLATION_ENABLED`             | `TENANT_AI_TRANSLATION_ENABLED`                  |

Every flag ships `false` by default. Real values populated via
Emergent Secrets UI.

## Providers

| Provider           | Flag                              | Key env             |
| ------------------ | --------------------------------- | ------------------- |
| Claude / Anthropic | `AI_PROVIDER_ANTHROPIC_ENABLED`   | `ANTHROPIC_API_KEY` |
| OpenAI             | `AI_PROVIDER_OPENAI_ENABLED`      | `OPENAI_API_KEY`    |
| Google Gemini      | `AI_PROVIDER_GOOGLE_ENABLED`      | `GOOGLE_AI_API_KEY` |

Failover, timeouts, and retries configurable via env.

## Deterministic composer (DR-CUTOVER-002)

- Composes summary from literal payload fields only.
- Never invents facts.
- Never calls an LLM in this deployment.
- Future live-LLM polish is deferred (P2); requires a "never introduce
  a new fact" cross-check.

**Verdict:** AI subsystem fully switchboarded, disabled by default,
tested end-to-end. Certified.
