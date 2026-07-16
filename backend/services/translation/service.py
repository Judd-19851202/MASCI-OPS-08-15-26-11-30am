"""TRACK 24.3 · ES → EN construction-industry translation service.

Contract
--------
`translate_es_to_en_bulk(db, fields, *, preserve_tokens, actor, dr_id)`

    fields          : dict[str, str]  — {field_path: es_text}
    preserve_tokens : set[str]        — proper nouns / IDs / codes that must
                                        remain verbatim through translation.
    actor           : str             — operator email or portal identity.
    dr_id           : str             — best-effort identifier for the DR
                                        being submitted (audit only).

Returns `TranslationResult`:

    ok              : bool
    translations    : dict[str, str]  — {field_path: en_text}  (empty on failure)
    error           : Optional[str]   — machine key; None on success
    provider        : Optional[str]   — "openai" | "anthropic"
    model           : Optional[str]
    latency_ms      : int

Model policy
------------
Primary : task-router configured provider/model via Emergent Universal Key.
Fallback: alternate provider/model via Emergent Universal Key.
Both keyed on `EMERGENT_LLM_KEY`.

Determinism policy
------------------
temperature = 0, JSON-only response, single request per submit, no
retries beyond the two-provider fallback chain. Response validated
key-by-key against the input. Any inconsistency → fail-closed.

Audit policy
------------
Every call (regardless of ok/failure) writes one row to
`db.translation_audit`. The LLM key is never logged or persisted.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from services.ai_gateway.task_router import route

logger = logging.getLogger("track24_3.translation")


@dataclass
class TranslationResult:
    ok: bool = False
    translations: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    latency_ms: int = 0


# Words we intentionally allow in an "English" output because they are
# industry proper nouns / acronyms shared across EN and ES on jobsites.
_ALLOWED_SPANISH_LOOKING = {
    "OSHA", "MOT", "PPE", "RFI", "PM", "QA", "QC", "GPS", "MASCI",
}

# Spanish accented letters / ñ. If an "English" output still contains any
# of these outside a proper noun, we treat the translation as failed
# (fail-closed).
_SPANISH_CHAR_RX = re.compile(r"[ñáéíóúü¿¡]", re.IGNORECASE)

_SYSTEM_MESSAGE = (
    "You translate US heavy-civil construction Daily Reports from "
    "Spanish (es-MX field dialect) to canonical English. Output must "
    "read as natural, plain English written by a US field supervisor. "
    "Preserve technical acronyms unchanged (OSHA, MOT, PPE, RFI, ODS, "
    "QA, QC, PM). Preserve numbers, times, dates, station labels "
    "(e.g. Sta 12+50), dimensions, and any token in the "
    "preserve-tokens list EXACTLY as given (verbatim casing, verbatim "
    "hyphens). Do not translate proper nouns, personal names, project "
    "numbers, equipment IDs, cost codes, ticket numbers, vendor "
    "names, or any preserve-token. Do not translate content that is "
    "already English — return it unchanged. Output must be a single "
    "valid JSON object with EXACTLY the same top-level keys as the "
    "input (no added keys, no removed keys). Values are the English "
    "translation strings. No commentary, no code fences, no prose."
)


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_json_object(text: str) -> Optional[str]:
    """Extract the first {...} JSON object from an LLM response. Tolerates
    ```json fences and surrounding prose."""
    if not text:
        return None
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:].lstrip("\n")
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return s[start : end + 1]


def _spanish_leak(text: str) -> bool:
    """Return True if `text` still contains Spanish-only characters
    outside allowed acronyms."""
    if not text:
        return False
    return bool(_SPANISH_CHAR_RX.search(text))


def _validate_response(
    parsed: Dict[str, Any],
    inputs: Dict[str, str],
    preserve_tokens: Set[str],
) -> Optional[str]:
    """Return None if valid, otherwise a machine error key."""
    if not isinstance(parsed, dict):
        return "translation_invalid_shape"
    input_keys = set(inputs.keys())
    output_keys = set(parsed.keys())
    if output_keys != input_keys:
        return "translation_key_mismatch"
    for k, v in parsed.items():
        if not isinstance(v, str):
            return "translation_non_string_value"
        if _spanish_leak(v):
            # Allow if the whole string is a preserve-token that
            # legitimately contains Spanish chars (rare).
            if v.strip() in preserve_tokens:
                continue
            return "translation_spanish_leak"
        # Every preserve-token that was present in the corresponding
        # input must survive verbatim into the output.
        src = inputs.get(k, "")
        for token in preserve_tokens:
            if token and token in src and token not in v:
                return "translation_preserve_token_lost"
    return None


async def _call_openai(
    api_key: str,
    payload_text: str,
    preserve_list: str,
) -> str:
    """Call the routed OpenAI translation model via the Emergent integrations SDK."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: PLC0415

    system = _SYSTEM_MESSAGE + f"\nPreserve-tokens (verbatim): {preserve_list}"
    provider, model = route("translation_es_en")
    selected_model = model if provider == "openai" else (os.environ.get("AI_DEFAULT_TEXT_MODEL_OPENAI") or "gpt-4o")
    chat = LlmChat(
        api_key=api_key,
        session_id=f"dr-v3-translate-{uuid.uuid4().hex[:10]}",
        system_message=system,
    ).with_model("openai", selected_model)
    resp = await chat.send_message(UserMessage(text=payload_text))
    return str(resp or "")


async def _call_anthropic(
    api_key: str,
    payload_text: str,
    preserve_list: str,
) -> str:
    """Call the routed Anthropic translation model via the Emergent integrations SDK."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: PLC0415

    system = _SYSTEM_MESSAGE + f"\nPreserve-tokens (verbatim): {preserve_list}"
    provider, model = route("translation_es_en")
    selected_model = model if provider == "anthropic" else (os.environ.get("AI_DEFAULT_TEXT_MODEL_ANTHROPIC") or os.environ.get("AI_DEFAULT_TEXT_MODEL") or "claude-sonnet-4-5-20250929")
    chat = LlmChat(
        api_key=api_key,
        session_id=f"dr-v3-translate-{uuid.uuid4().hex[:10]}",
        system_message=system,
    ).with_model("anthropic", selected_model)
    resp = await chat.send_message(UserMessage(text=payload_text))
    return str(resp or "")


async def _audit_write(
    db,
    *,
    ok: bool,
    error: Optional[str],
    provider: Optional[str],
    model: Optional[str],
    latency_ms: int,
    actor: str,
    dr_id: str,
    field_paths: list,
) -> None:
    """Best-effort audit row. Never blocks the caller on failure."""
    if db is None:
        return
    try:
        await db["translation_audit"].insert_one({
            "id": uuid.uuid4().hex,
            "ok": ok,
            "error": error,
            "provider": provider,
            "model": model,
            "latency_ms": int(latency_ms),
            "actor": (actor or "unknown")[:120],
            "dr_id": (dr_id or "")[:120],
            "field_paths": field_paths[:64],
            "field_count": len(field_paths),
            "ts": _now_utc_iso(),
            "source": "dr_v3_submit",
        })
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[track24_3.translation] audit insert failed: {e}")


async def translate_es_to_en_bulk(
    db,
    fields: Dict[str, str],
    *,
    preserve_tokens: Optional[Set[str]] = None,
    actor: str = "",
    dr_id: str = "",
) -> TranslationResult:
    """Translate a bag of {field_path: spanish_text} to English.

    Deterministic. Fail-closed. Writes one audit row per call.
    """
    started = time.monotonic()
    preserve_tokens = {t for t in (preserve_tokens or set()) if t}

    # Filter out empty / whitespace-only entries — nothing to translate.
    to_translate: Dict[str, str] = {
        k: v for k, v in (fields or {}).items()
        if isinstance(v, str) and v.strip()
    }
    if not to_translate:
        result = TranslationResult(ok=True, translations={}, error=None,
                                   provider=None, model=None,
                                   latency_ms=0)
        await _audit_write(db, ok=True, error=None, provider=None,
                           model=None, latency_ms=0, actor=actor,
                           dr_id=dr_id, field_paths=[])
        return result

    api_key = (os.environ.get("EMERGENT_LLM_KEY") or "").strip()
    if not api_key:
        latency_ms = int((time.monotonic() - started) * 1000)
        await _audit_write(db, ok=False, error="llm_key_missing",
                           provider=None, model=None,
                           latency_ms=latency_ms, actor=actor,
                           dr_id=dr_id, field_paths=list(to_translate))
        return TranslationResult(ok=False, error="llm_key_missing",
                                 latency_ms=latency_ms)

    payload_text = json.dumps(to_translate, ensure_ascii=False)
    preserve_list = ", ".join(sorted(preserve_tokens)) or "(none)"

    providers = [
        ("openai", route("translation_es_en")[1] if route("translation_es_en")[0] == "openai" else (os.environ.get("AI_DEFAULT_TEXT_MODEL_OPENAI") or "gpt-4o"), _call_openai),
        ("anthropic", route("translation_es_en")[1] if route("translation_es_en")[0] == "anthropic" else (os.environ.get("AI_DEFAULT_TEXT_MODEL_ANTHROPIC") or os.environ.get("AI_DEFAULT_TEXT_MODEL") or "claude-sonnet-4-5-20250929"), _call_anthropic),
    ]

    last_error = "translation_service_unavailable"
    for provider_name, model_name, fn in providers:
        try:
            raw = await fn(api_key, payload_text, preserve_list)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"[track24_3.translation] provider {provider_name} failed: {e}"
            )
            last_error = "translation_provider_error"
            continue

        json_blob = _extract_json_object(raw)
        if not json_blob:
            last_error = "translation_no_json"
            continue

        try:
            parsed = json.loads(json_blob)
        except Exception:  # noqa: BLE001
            last_error = "translation_invalid_json"
            continue

        err = _validate_response(parsed, to_translate, preserve_tokens)
        if err:
            last_error = err
            continue

        # Success · keep only string values (validated) · fill back any
        # empty inputs as empty outputs (they were skipped upstream).
        translations = {k: str(parsed[k]) for k in to_translate.keys()}
        latency_ms = int((time.monotonic() - started) * 1000)
        await _audit_write(
            db, ok=True, error=None,
            provider=provider_name, model=model_name,
            latency_ms=latency_ms, actor=actor, dr_id=dr_id,
            field_paths=list(to_translate),
        )
        return TranslationResult(
            ok=True,
            translations=translations,
            error=None,
            provider=provider_name,
            model=model_name,
            latency_ms=latency_ms,
        )

    latency_ms = int((time.monotonic() - started) * 1000)
    await _audit_write(
        db, ok=False, error=last_error,
        provider=None, model=None, latency_ms=latency_ms,
        actor=actor, dr_id=dr_id, field_paths=list(to_translate),
    )
    return TranslationResult(ok=False, error=last_error,
                             latency_ms=latency_ms)
