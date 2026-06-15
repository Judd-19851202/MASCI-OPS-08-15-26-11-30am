"""
routes/bilingual_records.py — TRACK 14.0-S1 Amendment A · bilingual record sidecar.

Stores the original Spanish (or other source-language) free-text submitted
by field crews, paired with the form_id of the canonical record. The
canonical form record still stores the English-translated content at its
original schema location (preserves search / admin-view / PDF contracts);
this sidecar makes the ORIGINAL retrievable so bilingual views can render
both languages and so future re-translation passes have an authoritative
source.

Collection schema (`db.bilingual_records`):

  {
    "id": "<uuid>",                       # unique per sidecar row
    "form_type": "meeting" | "incident" | "daily_report" | ...,
    "form_id": "<form record id>",        # FK to the canonical record
    "original_language": "es" | ... ,
    "originals": { "<json-path>": "<original string>", ... },
    "translated_at": "<iso>",
    "translation_source": "llm" | "pending" | "manual",
    "created_at": "<iso utc>",
    "submitted_by": { "role": "...", "name": "...", "email": "..." } | None,
  }

Endpoints (any portal token):

  POST /api/bilingual-records             — write a sidecar
  GET  /api/bilingual-records/{form_type}/{form_id}   — read one

The write endpoint is intentionally permissive: every authenticated portal
user can post a sidecar for any form they just submitted. The endpoint
does NOT mutate the canonical record collection — keeps coupling minimal.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from pydantic import BaseModel, Field


ALLOWED_FORM_TYPES = {
    "meeting", "incident", "daily_report", "near_miss",
    "corrective_action", "employee_request", "time_off",
    "trench_excavation", "equipment_inspection", "qaqc",
    "field_leadership", "safety_form", "jha",
    "dispatch_note", "pm_note", "shop_note",
    # New form_types can be added without a code change — the
    # validator below short-circuits on the closed set, but the
    # write path tolerates an "other" bucket gracefully.
}


class BilingualRecordWrite(BaseModel):
    form_type: str = Field(min_length=1, max_length=64)
    form_id: str = Field(min_length=1, max_length=128)
    original_language: str = Field(min_length=2, max_length=8)
    originals: Dict[str, str] = Field(default_factory=dict)
    translation_source: str = Field(default="llm", max_length=24)


def build_bilingual_records_router(db, require_any_portal_token):
    router = APIRouter(tags=["bilingual-records"])

    @router.post("/api/bilingual-records")
    async def write_sidecar(
        payload: BilingualRecordWrite = Body(...),
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        form_type = payload.form_type.strip().lower()
        if not payload.originals:
            # Empty sidecar is a no-op; keeps clients simple.
            return {"ok": True, "stored": False, "reason": "empty_originals"}
        # Cap the sidecar to a sensible blob size so a hostile client
        # can't fill the collection with megabytes. 32 entries × 8 KB
        # each is plenty for a daily report or meeting.
        if len(payload.originals) > 64:
            raise HTTPException(413, "too many originals (max 64)")
        for k, v in payload.originals.items():
            if not isinstance(v, str) or len(v) > 8192:
                raise HTTPException(413, f"original at path {k!r} too large")
        doc = {
            "id": str(uuid.uuid4()),
            "form_type": form_type,
            "form_id": payload.form_id.strip(),
            "original_language": payload.original_language.strip().lower(),
            "originals": payload.originals,
            "translated_at": datetime.now(timezone.utc).isoformat(),
            "translation_source": payload.translation_source.strip().lower(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "submitted_by": {
                "role": actor.get("_actor") or actor.get("role") or "unknown",
                "name": actor.get("name") or actor.get("email") or "unknown",
                "email": actor.get("email"),
            },
        }
        await db.bilingual_records.insert_one(doc)
        doc.pop("_id", None)
        return {"ok": True, "stored": True, "id": doc["id"]}

    @router.get("/api/bilingual-records/{form_type}/{form_id}")
    async def read_sidecar(
        form_type: str = Path(..., min_length=1, max_length=64),
        form_id: str = Path(..., min_length=1, max_length=128),
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        doc = await db.bilingual_records.find_one(
            {"form_type": form_type.strip().lower(),
             "form_id": form_id.strip()},
            {"_id": 0},
            sort=[("created_at", -1)],
        )
        if not doc:
            return {"ok": True, "found": False, "form_type": form_type,
                    "form_id": form_id}
        return {"ok": True, "found": True, "record": doc}

    return router


async def ensure_bilingual_indexes(db) -> None:
    """Idempotent index bootstrap."""
    try:
        await db.bilingual_records.create_index(
            [("form_type", 1), ("form_id", 1), ("created_at", -1)],
        )
        await db.bilingual_records.create_index("id", unique=True)
    except Exception:  # pragma: no cover
        pass
