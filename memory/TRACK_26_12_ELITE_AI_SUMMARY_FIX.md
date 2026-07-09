# TRACK 26.12 — ELITE AI DAILY REPORT SUMMARY FIX (SHIPPED · 2026-07-09)

**User P0 (weeks-long):** AI summary in the Daily Report form was "trash" — sparse deterministic template, ignored photos, Regenerate produced the same output. User had flipped every AI flag to true in production and added real OpenAI/Anthropic keys with zero effect.

## Root causes (proven by reproduction in preview — this was NEVER a flags problem)

| # | Root cause | Proof |
|---|---|---|
| 1 | **Raw base64 photo data URLs were JSON-dumped INTO the Claude text prompt** (~1M tokens for 8 photos). Every provider call failed instantly → silent fallback to deterministic template. | Repro: synthesize with 8 photos → `ai_available=false, fallback=llm_call_failed` in 1.0s. With flags TRUE + working key. |
| 2 | **Frontend hard timeout 15s** while narrative alone takes ~15-20s → abort → deterministic fallback even WITHOUT photos. | Repro: no-photo synthesize succeeded at 15.4s — 0.4s past the timeout. |
| 3 | **Photo vision only ran post-submit** via background reconciler + strict tenant-resolver gates → draft-time summary could never cite photos by design. | `services/photo_intelligence/pipeline.py` reconciler; enqueue on submit only. |
| 4 | **`provider_meta().ai_available` checked ONLY `EMERGENT_LLM_KEY`** — production's direct ANTHROPIC/OPENAI keys were invisible → whole path reported unavailable. | `services/dr_ai/factory.py:37` (old). |
| 5 | **Invalid vision model `gpt-5.2-vision`** (does not exist) in task router + env. | Integration playbook: valid = gpt-5.4 (recommended). |
| 6 | **Form field groups silently dropped before the AI**: frontend sent `constraints_cards` (not a DraftPayload field → Pydantic dropped it); `production` rows, `day_impacts` (delay/weather Yes/No + notes), `narrative_sections` (tomorrow plan + PM needs) were never forwarded at all. | DraftPayload vs `toEvidenceDraft` key diff. |

## Fixes shipped

**Backend**
- NEW `services/dr_ai/vision.py` — inline draft-time photo vision. Extracts base64 photos from `photos[]`, material `ticket_photos[]`, sub `photos[]` (cap 10); one gpt-5.4 vision call per photo in parallel via gateway `dispatch_vision(task="photo_vision")`; strict grounded JSON (summary · observations · ticket_text transcription for delivery/scale tickets); results cached per content-sha256 in `dr_v2_photo_vision_cache` (Regenerate = cache hit, no re-pay).
- `routes/dr_v2.py` — synthesize now runs vision FIRST, merges observations into `photo_observations`, THEN builds the evidence bundle + hash; response carries `photo_observations_used`. `_v2_ai_enabled()` now default-TRUE (explicit false disables). DraftPayload gained `production`, `constraints`, `day_impacts`, `narrative_sections`.
- `services/dr_ai/evidence.py` — `build_evidence_bundle` converts `photos` to metadata refs (`{ref, sha12, caption}`) and recursively strips any base64/data-URL/oversized string. No raw binary can ever reach a text prompt again. Whitelist gained production/constraints/day_impacts/narrative_sections.
- `services/dr_ai/factory.py` — `ai_available` = ANY usable key (EMERGENT_LLM_KEY OR ANTHROPIC/OPENAI/GOOGLE direct key).
- `services/dr_ai/agents.py` — `day_narrative` rewritten: superintendent-grade prose, explicit COVERAGE CONTRACT over every field group (crew hours, sub headcount/hours/notes, equipment, production stations/% verbatim, materials + carriers + ticket numbers, outbound, visitors, constraints/delays, safety, excavation/CP, photo observations incl. ticket_text, attachments, tomorrow plan + PM needs, general notes). 120-450 words scaled to evidence. Rule 9 now instructs citing photo_observations as field-verified evidence.
- `services/ai_gateway/task_router.py` + `env.py` + `.env` — photo_vision → `("openai", "gpt-5.4")`.

**Frontend**
- `DailySummaryAssist.jsx` — timeout 15s → 60s; `toEvidenceDraft` now forwards production, `constraint_cards` (fixed key), day_impacts, tomorrow_readiness `{tomorrow_plan, pm_needs}` from narrative_sections, safety_quality mapped from V1 Yes/No fields; `hasEnoughEvidence` counts photos/materials/subs/production; effect deps track photos length + production + subs + tomorrow/PM fields; status shows "analyzing photos & writing summary…" when photos exist.
- `daily-report-v3/sections.jsx` — crew name keystroke auto-resolve now fires only on EXACT roster match (was: single partial match replaced the value MID-TYPING → "Jaymn Juddmn Judd" + max-update-depth errors).
- `JobPicker.jsx` — unique React keys (`j.id || project_number-idx`), kills 100+ duplicate-key console warnings.

## Verification
- API E2E (main agent): full draft + 3 real photos → 38s, `ai_available=true`, `photo_observations_used=3`, 1758-char narrative citing photo content verbatim (read "ELEMENTARY SCHOOL LOOP" striping off the pavement), all sections covered. Regen 22s (vision cached).
- Testing agent (iteration_track_2612.json): backend 6/6; browser V3 form → real narrative in 19s, deterministic template GONE, fallback label ABSENT, Regenerate + Accept work. New reusable suite: `backend/tests/test_dr_v2_track_2612.py`.
- Follow-up fixes verified live: crew typing stays exact, status flow `writing summary… → ready → accepted`.
- Regression: frontend jest 233/233 · targeted backend AI/DR suites 66 + 90 pass. Stale tests updated: 15s-timeout lock (now 30-90s), gpt-5.2-vision refs → gpt-5.4, `constraints_cards` → `constraint_cards` + production/day_impacts.

## PRODUCTION DEPLOY NOTES (user must redeploy)
- Fixes ship on next deploy. Production env: keys already set (Anthropic + OpenAI). `DR_V2_AI_ENABLED` now defaults ON. Emergent key no longer required when direct keys exist.
- Narrative = Claude (anthropic key or emergent key). Photo vision = OpenAI gpt-5.4 (openai key or emergent key).
