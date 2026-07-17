"""DR-ROI-001D · Photo Analyzer — calls AI Gateway `photo_vision` task."""
from __future__ import annotations

import base64
import hashlib
import json
import asyncio
from typing import Any, Dict, List, Optional


PHOTO_ENVELOPE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["narrative", "confidence", "observations", "suggested_links", "questions"],
    "properties": {
        "narrative": {"type": "string", "maxLength": 2000},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence_refs": {"type": "array", "items": {"type": "string"}},
        "sources_used": {"type": "array", "items": {"type": "string"}},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "description": {"type": "string"},
                    "confidence": {"type": "number"},
                    "severity": {"type": "string"},
                    "category": {"type": "string"},  # work | equipment | material | safety | quality | site
                    "requires_supervisor_confirmation": {"type": "boolean"},
                },
            },
        },
        "suggested_links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "target_type": {"type": "string"},
                    "target_id": {"type": "string"},
                    "target_label": {"type": "string"},
                    "confidence": {"type": "number"},
                    "reason": {"type": "string"},
                },
            },
        },
        "conflicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "conflict_type": {"type": "string"},
                    "photo_observation": {"type": "string"},
                    "entered_data_reference": {"type": "string"},
                    "question": {"type": "string"},
                    "severity": {"type": "string"},
                },
            },
        },
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "reason": {"type": "string"},
                    "suggested_action": {"type": "string"},
                    "severity": {"type": "string"},
                },
            },
        },
    },
}

_SYSTEM = (
    "You are a construction operational photo evidence assistant. "
    "Analyze photos strictly. NEVER invent quantities, activities, "
    "incidents, delays, or safety violations that are not clearly visible. "
    "Every observation must be traceable to what is visible in the image. "
    "For every observation set requires_supervisor_confirmation=true unless "
    "the fact is unambiguous (e.g., a clearly-labeled equipment ID plate). "
    "Return STRICT JSON only, no markdown, no preface."
)

VISION_RETRY_ATTEMPTS = 3
VISION_RETRY_BASE_DELAY_SECONDS = 0.75


def _sha(x: str) -> str:
    return hashlib.sha256(x.encode("utf-8")).hexdigest()


def evidence_hash_for_photo(
    *, photo_ref: str, photo_bytes_b64: Optional[str] = None,
    draft_context_hash: str = "",
) -> str:
    """Deterministic hash used to skip repeat expensive vision calls."""
    if photo_bytes_b64:
        return _sha(_sha(photo_bytes_b64) + "|" + draft_context_hash)
    return _sha(photo_ref + "|" + draft_context_hash)


async def analyze_photo(
    *,
    gateway,
    session_id: str,
    photo_ref: str,
    images: List[Any],
    draft_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Dispatch a `photo_vision` task and return the raw envelope+data.

    `images` is a list of `{content_type, file_content_base64}` dicts
    or raw base64 strings. `draft_context` is a compact struct with
    activity_cards/constraint_cards/equipment_used/masci_crews so the
    model can suggest links against real supervisor entries.
    """
    user_body = (
        "Draft context (json):\n" + json.dumps(draft_context, sort_keys=True, ensure_ascii=False)
        + "\n\nAnalyze the attached photo(s). Produce observations, "
        "suggested_links to any items in draft context that match, and "
        "up to 3 questions the supervisor should verify."
    )
    last_exc = None
    for attempt in range(1, VISION_RETRY_ATTEMPTS + 1):
        try:
            return await gateway.dispatch_vision(
                task="photo_vision",
                system=_SYSTEM,
                images=images,
                user=user_body,
                response_schema=PHOTO_ENVELOPE_SCHEMA,
                session_id=session_id,
            )
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt >= VISION_RETRY_ATTEMPTS:
                raise
            await asyncio.sleep(VISION_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1)))
    raise last_exc  # pragma: no cover
