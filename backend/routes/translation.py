"""TRACK 24.3 · Daily Report V3 free-text translation route.

`POST /api/translate/dr-v3-freetext`

Body
----
    {
      "fields": {"excavation.soil_notes": "Suelo tipo B con piedras…", ...},
      "preserve_tokens": ["OXFORD RD", "Alec Perkins", "24-12", ...],
      "dr_id": "optional-client-id-for-audit"
    }

Response
--------
    200  {"ok": true, "translations": {...}, "provider": "openai",
           "model": "gpt-5.2", "latency_ms": 823,
           "translation_metadata": {...}}
    502  {"ok": false, "error": "translation_service_unavailable"} — fail-closed.

Authorization
-------------
This route is called only from the DR V3 submit path. It runs behind the
same rate-limit that guards public POST /api/daily-reports so it cannot
be abused. No admin gate — Daily Reports themselves are FSI-submittable
by supervisors in the field.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from services.translation import translate_es_to_en_bulk

logger = logging.getLogger("track24_3.translate_route")


class TranslateFreeTextBody(BaseModel):
    fields: Dict[str, str] = Field(default_factory=dict)
    preserve_tokens: List[str] = Field(default_factory=list)
    dr_id: Optional[str] = ""


def build_translation_router(db, rate_limit_dep: Callable) -> APIRouter:
    """Build the translation router.

    `db`             — motor database handle.
    `rate_limit_dep` — same public-POST rate limit dependency used by
                       /api/daily-reports so this endpoint can't be
                       hammered by anonymous clients.
    """
    router = APIRouter(prefix="/api", tags=["translation"])

    @router.post("/translate/dr-v3-freetext",
                 dependencies=[Depends(rate_limit_dep)])
    async def translate_dr_v3_freetext(body: TranslateFreeTextBody,
                                       request: Request) -> Dict[str, Any]:
        # Payload size guard · limit total text bytes so the LLM call
        # can't be blown up by an unbounded submit.
        total_chars = sum(len(v or "") for v in body.fields.values())
        if total_chars > 40_000:
            raise HTTPException(
                status_code=413,
                detail={"error": "payload_too_large",
                        "message": "Free-text payload exceeds 40 000 characters."},
            )
        if len(body.fields) > 100:
            raise HTTPException(
                status_code=413,
                detail={"error": "too_many_fields",
                        "message": "More than 100 fields per submit is not supported."},
            )

        # Best-effort actor tag for audit — no auth requirement.
        actor = ""
        try:
            for header_key in ("x-admin-token", "x-hr-token", "x-safety-token",
                               "x-pm-token", "x-fl-token"):
                if request.headers.get(header_key):
                    actor = f"portal:{header_key[2:-6]}"
                    break
            actor = actor or (request.client.host if request.client else "anon")
        except Exception:  # noqa: BLE001
            actor = "anon"

        result = await translate_es_to_en_bulk(
            db,
            fields=dict(body.fields),
            preserve_tokens=set(body.preserve_tokens or []),
            actor=actor,
            dr_id=body.dr_id or "",
        )

        if not result.ok:
            # Fail-closed · operator-visible error surfaced by the
            # frontend. HTTP 502 signals an upstream provider issue so
            # the DR V3 submit flow will block the submit.
            raise HTTPException(
                status_code=502,
                detail={
                    "error": result.error or "translation_service_unavailable",
                    "message": (
                        "Spanish text could not be translated for submission. "
                        "Please try again or switch to English."
                    ),
                    "provider": result.provider,
                    "latency_ms": result.latency_ms,
                },
            )

        translation_metadata = {
            "original_language": "es",
            "translated_to_canonical_language": "en",
            "translation_provider": result.provider,
            "translation_model": result.model,
            "translation_timestamp": datetime.now(timezone.utc).isoformat(),
            "translated_field_paths": sorted(result.translations.keys()),
            "translation_latency_ms": result.latency_ms,
        }
        return {
            "ok": True,
            "translations": result.translations,
            "provider": result.provider,
            "model": result.model,
            "latency_ms": result.latency_ms,
            "translation_metadata": translation_metadata,
        }

    return router
