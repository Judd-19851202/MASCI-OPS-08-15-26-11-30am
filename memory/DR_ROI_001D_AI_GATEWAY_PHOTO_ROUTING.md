# DR-ROI-001D · AI Gateway · Photo Vision Routing

## Task registration

Task `photo_vision` is already registered in `services/ai_gateway/task_router.py`:

```
"photo_vision": ("openai", "gpt-5.2-vision")
```

Overridable per environment via `AI_TASK_ROUTE__photo_vision="google:gemini-2.0-flash"`.

## Adapter

`services/ai_gateway/adapters/openai_adapter.py::OpenAIAdapter.vision(...)` is now the concrete implementation:

- Accepts `images: List[Union[str, {"content_type", "file_content_base64"}]]`.
- Caps at 6 images per call (matches V1 minimum).
- Uses `emergentintegrations.llm.chat.UserMessage(file_contents=[FileContent(...) | ImageContent(...)])`.
- Returns the same canonical `AiEnvelope`.
- Populates `envelope.raw` with `observations`, `suggested_links`, `conflicts`, `questions` — the Photo Intelligence store unpacks these.

## Gateway dispatch

New `Gateway.dispatch_vision(task, system, images, user, response_schema, session_id)` mirrors `dispatch()` for text tasks, honoring:
- gateway enabled flag
- adapter registration
- key presence
- timeout (`AI_PROVIDER_TIMEOUT_MS`)
- graceful envelope on any failure (never raises)

## Envs

`DR_V2_PHOTO_VISION_ENABLED`, `AI_DEFAULT_VISION_PROVIDER`, `AI_DEFAULT_VISION_MODEL`, `OPENAI_API_KEY`, `GOOGLE_AI_API_KEY`, `AI_PROVIDER_TIMEOUT_MS`, `AI_PROVIDER_MAX_RETRIES`, `AI_PROVIDER_FAILOVER_ENABLED`.

## Failure semantics

- Key missing → `ai_available=false`, `fallback_reason="missing_provider_key"`.
- SDK import fails → `ai_available=false`, `fallback_reason="import_error"`.
- Model returns non-JSON → `ai_available=false`, `fallback_reason="invalid_json"`.
- Any timeout / exception → `ai_available=false`, `fallback_reason="vision_error:<cls>"`.
- In all cases, the store records `analysis_status="unavailable"` — no invented observations.
