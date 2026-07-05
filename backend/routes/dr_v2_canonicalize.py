"""DR-ROI-001F-FINAL-REPAIR · Amendment · EN/ES canonicalization.

Field-facing supervisors and crews may work in Spanish, but the
canonical submitted operational record is always English. This route
translates freeform Spanish input on the DR-V2 draft into English via
the AI Provider Gateway, preserves both original and canonical values
in an append-only bilingual audit collection, and returns the canonical
payload.

The endpoint is idempotent: passing an English-language draft is a
no-op except for reading `translations=[]` and `field_language="en"`.

Never called from photo upload, HR crew time, equipment, safety gates,
or the ODS emission pipeline — the schema-typed fields there stay
canonical English by construction. Only freeform text on the draft is
translated. See `/app/memory/DR_ROI_001F_FINAL_REPAIR_EN_ES_MODE.md`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Body

from services.ai_gateway.registry import Gateway, get_gateway
from services.ai_gateway.env import gateway_enabled

BILINGUAL_AUDIT_COLL = "dr_v2_bilingual_audit"

# Fields on the draft (and their subpaths) whose freeform text is
# subject to translation to English on submit.  Every path uses a
# subset of JSONPath: `key[i].sub.subsub`.
TRANSLATABLE_PATHS: List[str] = [
    "activity_cards[].notes",
    "constraint_cards[].what_happened",
    "constraint_cards[].impact",
    "tomorrow_readiness.crew_needs",
    "tomorrow_readiness.equipment_needs",
    "tomorrow_readiness.material_needs",
    "tomorrow_readiness.decisions_needed",
    "safety.quality_notes",
    "day_setup.location_label",
    "accepted_summary",  # supervisor-edited Daily Operational Summary
]


def _walk_get(obj: Any, path: str) -> List[Dict[str, Any]]:
    """Return [{ptr, value}] for every string found at `path`."""
    parts = path.split(".")
    out: List[Dict[str, Any]] = []

    def _rec(node: Any, remaining: List[str], ptr: List[Any]) -> None:
        if not remaining:
            if isinstance(node, str) and node.strip():
                out.append({"ptr": list(ptr), "value": node})
            return
        head, *tail = remaining
        if head.endswith("[]"):
            key = head[:-2]
            if not isinstance(node, dict) or not isinstance(node.get(key), list):
                return
            for i, item in enumerate(node[key]):
                _rec(item, tail, ptr + [key, i])
        else:
            if not isinstance(node, dict) or head not in node:
                return
            _rec(node[head], tail, ptr + [head])

    _rec(obj or {}, parts, [])
    return out


def _walk_set(obj: Any, ptr: List[Any], value: str) -> None:
    cur = obj
    for step in ptr[:-1]:
        cur = cur[step]
    cur[ptr[-1]] = value


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def register_dr_v2_canonicalize_routes(
    api_router: APIRouter, db, *, registry: Optional[Gateway] = None,
) -> None:
    """Register `/api/dr-v2/reports/{report_id}/canonicalize`."""

    @api_router.post("/dr-v2/reports/{report_id}/canonicalize")
    async def dr_v2_canonicalize(
        report_id: str,
        payload: Dict[str, Any] = Body(default_factory=dict),
    ) -> Dict[str, Any]:
        """Translate freeform Spanish text on the draft to canonical English.

        Request payload:
            { "draft": {...}, "field_language": "en"|"es" }
        Response:
            { report_id, canonical_draft, translations[], translation_status,
              needs_supervisor_review, field_language, audit_id }
        """
        draft = payload.get("draft") or {}
        field_language = str(payload.get("field_language") or draft.get("field_language") or "en").lower()

        # No-op fast path for English drafts.
        if field_language != "es":
            audit = {
                "audit_id": str(uuid.uuid4()),
                "report_id": report_id,
                "field_language": "en",
                "translations": [],
                "translation_status": "not_required",
                "needs_supervisor_review": False,
                "created_at": _now_iso(),
                "canonical_draft": draft,
            }
            try:
                await db[BILINGUAL_AUDIT_COLL].insert_one(dict(audit))
            except Exception:  # noqa: BLE001
                pass
            return {
                "report_id": report_id,
                "canonical_draft": draft,
                "translations": [],
                "translation_status": "not_required",
                "needs_supervisor_review": False,
                "field_language": "en",
                "audit_id": audit["audit_id"],
            }

        # Collect every translatable string on the draft.
        candidates: List[Dict[str, Any]] = []
        for path in TRANSLATABLE_PATHS:
            for hit in _walk_get(draft, path):
                candidates.append({"path": path, **hit})

        translations: List[Dict[str, Any]] = []
        canonical_draft: Dict[str, Any] = _deep_copy(draft)
        min_confidence = 1.0
        gw = registry or get_gateway()
        gateway_available = gateway_enabled() and (gw is not None)

        for c in candidates:
            original = c["value"]
            translated = original  # fallback: pass through untouched
            confidence = 1.0
            status = "identity"
            provider = None
            model = None

            if gateway_available:
                try:
                    env = await gw.dispatch(
                        task="translation_es_en",
                        system=(
                            "You are a certified construction translator. "
                            "Translate the user's Spanish text into precise "
                            "American English suitable for a legal / operational "
                            "daily construction report. Preserve every fact, "
                            "quantity, and unit exactly. Do not add commentary."
                        ),
                        user_payload={"es_text": original, "return_only": "en_text"},
                        response_schema={
                            "type": "object",
                            "properties": {
                                "en_text": {"type": "string"},
                                "confidence": {"type": "number"},
                            },
                            "required": ["en_text"],
                        },
                        session_id=f"dr_v2_translate::{report_id}",
                    )
                    body = env.body or {}
                    translated = str(body.get("en_text") or original)
                    confidence = float(body.get("confidence") or (env.confidence or 0.85))
                    status = "translated" if translated != original else "identity"
                    provider = env.provider
                    model = env.model
                except Exception as ex:  # noqa: BLE001
                    translated = original
                    status = f"gateway_error:{type(ex).__name__}"
                    confidence = 0.0
            else:
                status = "gateway_disabled"
                confidence = 0.0

            if status.startswith("gateway_") and status != "gateway_disabled":
                min_confidence = min(min_confidence, 0.0)
            else:
                min_confidence = min(min_confidence, confidence)

            translations.append({
                "field_path": c["path"],
                "pointer": c["ptr"],
                "original_user_text": original,
                "original_user_language": "es",
                "canonical_english_text": translated,
                "translation_status": status,
                "translation_confidence": confidence,
                "translation_provider": provider or "gateway",
                "translated_at": _now_iso(),
                "reviewed_by_user": False,
            })
            _walk_set(canonical_draft, c["ptr"], translated)

        canonical_draft["field_language"] = "es"
        # Canonical fields on the record are English.
        canonical_draft["canonical_language"] = "en"

        needs_review = (
            (min_confidence < 0.7 and len(translations) > 0)
            or any(t["translation_status"].startswith("gateway_error") for t in translations)
        )
        translation_status = (
            "ok" if translations and not needs_review else
            "needs_review" if needs_review else
            "empty"
        )

        audit = {
            "audit_id": str(uuid.uuid4()),
            "report_id": report_id,
            "field_language": "es",
            "canonical_language": "en",
            "translations": translations,
            "translation_status": translation_status,
            "needs_supervisor_review": needs_review,
            "min_confidence": min_confidence if translations else 1.0,
            "created_at": _now_iso(),
            "canonical_draft": canonical_draft,
            "original_draft": draft,
        }
        try:
            await db[BILINGUAL_AUDIT_COLL].insert_one(dict(audit))
        except Exception:  # noqa: BLE001
            pass

        return {
            "report_id": report_id,
            "canonical_draft": canonical_draft,
            "translations": translations,
            "translation_status": translation_status,
            "needs_supervisor_review": needs_review,
            "field_language": "es",
            "canonical_language": "en",
            "audit_id": audit["audit_id"],
        }


def _deep_copy(obj: Any) -> Any:
    """Small, dependency-free deep copy for JSON-friendly payloads."""
    if isinstance(obj, dict):
        return {k: _deep_copy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deep_copy(v) for v in obj]
    return obj
