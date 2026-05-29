"""
routes/odr/amendments.py — Phase V.1 · M0.2 · Amendment Engine.

Doctrine:
  /app/memory/ODR_FINAL_GOVERNANCE_ADDENDUM.md  (O28 · O29 · O35)
  /app/memory/ODR_DATA_MODEL.md  (G1–G9 addendum)

Edit-window contract:
  - status=draft / returned → owner may edit freely (PATCH /api/odr/{id})
  - status=submitted, within `amend_allowed_until_utc` (default +24h)
      → owner may edit · written as `odr_section_events` only · NO
        `odr_amendments` row (treated as final-pass corrections)
  - status=submitted, AFTER `amend_allowed_until_utc`
      → ONLY Superintendent / Senior Super / Admin may amend ·
        every amendment writes one `odr_amendments` row · reason
        required · old_value/new_value preserved · append-only
  - status=approved
      → ONLY Admin may amend · same audit contract

Hard rules (per O29):
  - No overwrite. The amendment row carries `old_value` + `new_value`.
  - No deletion of `odr_amendments`. Trendline integrity protects.
  - Chronology preserved.

API:
  POST   /api/odr/{id}/amend     Super+ amendment (post-window)
  GET    /api/odr/{id}/amendments  amendment list (audit-trail read)
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from .models import LocalizedString

logger = logging.getLogger(__name__)


def _utc_iso(dt: Optional[datetime] = None) -> str:
    d = dt or datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{d.microsecond // 1000:03d}Z"


def _actor_uid(actor: Dict[str, Any]) -> str:
    if not isinstance(actor, dict):
        return "system"
    return (
        actor.get("id")
        or actor.get("user_id")
        or actor.get("uid")
        or actor.get("email")
        or actor.get("name")
        or "unknown"
    )


def _value_sha256(v: Any) -> str:
    return hashlib.sha256(
        json.dumps(v, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _resolve_role(actor: Dict[str, Any]) -> tuple[str, str]:
    """Returns (role, portal). Roles: foreman · superintendent ·
    senior_superintendent · admin."""
    portal = (actor.get("_actor") or "").lower()
    if portal == "admin":
        return "admin", "admin"
    if portal == "fl":
        r = (actor.get("role") or actor.get("fl_role") or "").lower()
        if "senior" in r:
            return "senior_superintendent", "field_leadership"
        if "superintendent" in r:
            return "superintendent", "field_leadership"
        return "foreman", "field_leadership"
    # PM may not amend (per O22 PM is read-only consumer)
    return "foreman", "field_leadership"


def _path_get(doc: Dict[str, Any], dotted: str) -> Any:
    """Dotted path getter — supports `a.b[0].c` style."""
    cur: Any = doc
    parts: List[str] = []
    tok = ""
    for ch in dotted:
        if ch == "." and "[" not in tok:
            if tok:
                parts.append(tok)
                tok = ""
        elif ch == "[":
            if tok:
                parts.append(tok)
                tok = ""
            parts.append("[")
        elif ch == "]":
            if tok:
                parts.append(tok)
                tok = ""
            parts.append("]")
        else:
            tok += ch
    if tok:
        parts.append(tok)
    # Walk
    i = 0
    while i < len(parts):
        p = parts[i]
        if p == "[":
            i += 1
            idx = int(parts[i])
            cur = cur[idx] if isinstance(cur, list) and 0 <= idx < len(cur) else None
            i += 2  # skip "]"
        else:
            if isinstance(cur, dict):
                cur = cur.get(p)
            else:
                return None
            i += 1
        if cur is None:
            return None
    return cur


def _path_set(doc: Dict[str, Any], dotted: str, value: Any) -> None:
    """Dotted path setter — same syntax as _path_get."""
    parts: List[Any] = []
    tok = ""
    in_bracket = False
    for ch in dotted:
        if ch == "." and not in_bracket:
            if tok:
                parts.append(tok)
                tok = ""
        elif ch == "[":
            if tok:
                parts.append(tok)
                tok = ""
            in_bracket = True
        elif ch == "]":
            parts.append(int(tok))
            tok = ""
            in_bracket = False
        else:
            tok += ch
    if tok:
        parts.append(tok)
    cur: Any = doc
    for p in parts[:-1]:
        if isinstance(p, int):
            cur = cur[p]
        else:
            if p not in cur or cur[p] is None:
                cur[p] = {}
            cur = cur[p]
    last = parts[-1]
    if isinstance(last, int):
        cur[last] = value
    else:
        cur[last] = value


# ── DTOs ─────────────────────────────────────────────────────────────


class AmendBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field_path: str = Field(..., min_length=1, max_length=200)
    new_value: Any
    reason: LocalizedString
    triggers_pdf_rerender: bool = False


# ── Router factory ───────────────────────────────────────────────────


def build_odr_amendments_router(
    db,
    require_actor: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:

    router = APIRouter(prefix="/api/odr", tags=["odr-amendments"])

    @router.post("/{odr_id}/amend")
    async def post_amend(
        odr_id: str,
        body: AmendBody,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        existing = await db.odr.find_one({"id": odr_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "ODR not found")

        status = existing.get("status", "draft")
        if status not in ("submitted", "approved", "returned"):
            raise HTTPException(
                409,
                "Amendments only apply to submitted / approved / returned ODRs.",
            )

        role, portal = _resolve_role(actor)
        now = _utc_iso()

        # Authority gate.
        in_window = False
        if existing.get("amend_allowed_until_utc"):
            try:
                limit_dt = datetime.fromisoformat(
                    existing["amend_allowed_until_utc"].replace("Z", "+00:00")
                )
                in_window = datetime.now(timezone.utc) <= limit_dt
            except Exception:
                in_window = False

        if status == "approved" and role != "admin":
            raise HTTPException(403, "Approved ODRs may only be amended by Admin.")
        if not in_window and role == "foreman":
            raise HTTPException(
                403,
                "Foreman edit window has closed. Request amendment via Superintendent.",
            )
        if role not in ("foreman", "superintendent", "senior_superintendent", "admin"):
            raise HTTPException(403, "Insufficient authority to amend.")

        # Apply mutation.
        old_value = _path_get(existing, body.field_path)
        try:
            mutated = dict(existing)
            _path_set(mutated, body.field_path, body.new_value)
        except Exception as exc:
            raise HTTPException(400, f"Invalid field_path: {exc}")

        update: Dict[str, Any] = {
            body.field_path.split("[")[0].split(".")[0]:
                mutated[body.field_path.split("[")[0].split(".")[0]],
            "last_edited_at": now,
            "last_edited_by_uid": _actor_uid(actor),
        }

        # If amendment happens outside the foreman window, write
        # `odr_amendments` row. Inside the window or for foreman
        # corrections within window, write only `odr_section_events`.
        amendment_id: Optional[str] = None
        writes_amendment_row = (not in_window) or (role != "foreman")

        if writes_amendment_row:
            amendment_id = str(uuid.uuid4())
            amend_doc = {
                "amendment_id": amendment_id,
                "odr_id": odr_id,
                "actor_uid": _actor_uid(actor),
                "actor_role": role,
                "actor_portal": portal,
                "field_path": body.field_path,
                "old_value": old_value,
                "new_value": body.new_value,
                "old_value_sha256": _value_sha256(old_value),
                "new_value_sha256": _value_sha256(body.new_value),
                "reason": body.reason.model_dump(),
                "at_utc": now,
                "triggers_pdf_rerender": body.triggers_pdf_rerender,
            }
            await db.odr_amendments.insert_one(amend_doc)
            update["amendment_count"] = (existing.get("amendment_count") or 0) + 1
            update["last_amended_at_utc"] = now
            update["last_amended_by_uid"] = _actor_uid(actor)

        # Always write section event.
        await db.odr_section_events.insert_one({
            "event_id": str(uuid.uuid4()),
            "odr_id": odr_id,
            "project_id": (existing.get("project") or {}).get("project_id", ""),
            "section": body.field_path,
            "action": "amended" if writes_amendment_row else "patched_in_window",
            "note": (body.reason.text or "")[:500],
            "old_value_sha256": _value_sha256(old_value),
            "new_value_sha256": _value_sha256(body.new_value),
            "at_utc": now,
            "actor_uid": _actor_uid(actor),
            "actor_portal": portal,
            "amendment_id": amendment_id,
        })

        await db.odr.update_one({"id": odr_id}, {"$set": update})
        out: Dict[str, Any] = {
            "ok": True,
            "odr_id": odr_id,
            "amendment_id": amendment_id,
            "amendment_recorded": bool(amendment_id),
            "in_window": in_window,
            "role": role,
            "at_utc": now,
            "amendment_count": update.get("amendment_count", existing.get("amendment_count", 0)),
        }
        return out

    @router.get("/{odr_id}/amendments")
    async def list_amendments(
        odr_id: str,
        limit: int = Query(default=200, ge=1, le=500),
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        odr = await db.odr.find_one(
            {"id": odr_id}, {"_id": 0, "id": 1, "doc_id": 1},
        )
        if not odr:
            raise HTTPException(404, "ODR not found")
        cur = db.odr_amendments.find(
            {"odr_id": odr_id}, {"_id": 0}
        ).sort("at_utc", -1).limit(limit)
        rows = await cur.to_list(length=limit)
        return {
            "odr_id": odr_id,
            "doc_id": odr.get("doc_id"),
            "amendments": rows,
            "count": len(rows),
        }

    return router


__all__ = ["build_odr_amendments_router"]
