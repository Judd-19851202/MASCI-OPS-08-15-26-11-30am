"""OMEGA · Phase 1A · Universal workflow audit-event writer.

Single source of truth for every state transition across the 6 Phase 1A
workflows. Writes append-only rows to ``workflow_state_events``.

Schema (per row)::

    {
        "id":            "<uuid4>",
        "workflow":      "incident" | "daily_report" | "qaqc_inspection" |
                          "site_inspection" | "payroll_variance" | "jha_ack",
        "record_id":     "<doc.id>",
        "record_doc_id": "<doc.doc_id or ''>",
        "from_state":    "OPEN" | ... | None,
        "to_state":      "UNDER_INVESTIGATION" | ...,
        "actor_role":    "safety" | "admin" | "pm" | "system",
        "actor_id":      "<email or uuid or ''>",
        "actor_name":    "<display name>",
        "reason":        "<free text · optional · required for REOPEN>",
        "evidence":      { ...transition-specific attestation flags... },
        "ip":            "<X-Forwarded-For first hop>",
        "user_agent":    "<truncated 240 chars>",
        "at":            datetime(timezone.utc),
    }

Append-only. Never updated, never deleted. The 7-year retention TTL is
applied by the iter455 deployment migration; for iter451 we just write
rows and ensure indexes exist.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Request


WORKFLOW_STATE_EVENTS = "workflow_state_events"


async def ensure_indexes(db) -> None:
    """Create the index battery used by audit reads + projections.

    Idempotent — safe to call from server startup. Failures are
    swallowed because index creation must never block boot.
    """
    try:
        await db[WORKFLOW_STATE_EVENTS].create_index(
            [("workflow", 1), ("record_id", 1), ("at", -1)],
            name="wse_record_at_desc",
        )
        await db[WORKFLOW_STATE_EVENTS].create_index(
            [("at", -1)],
            name="wse_at_desc",
        )
        await db[WORKFLOW_STATE_EVENTS].create_index(
            [("workflow", 1), ("to_state", 1), ("at", -1)],
            name="wse_workflow_state",
        )
    except Exception:  # pragma: no cover — index races
        pass


def _actor_view(actor: Any) -> Dict[str, str]:
    """Project the heterogeneous actor shape (admin bool, safety dict,
    pm dict) onto a uniform {role, id, name} triple for audit rows."""
    # Admin token returns True / dict with _actor='admin' / dict with role
    if actor is True:
        return {"role": "admin", "id": "", "name": "Admin"}
    if isinstance(actor, dict):
        # Recognize the actor_kind tags that the auth deps attach so that
        # users without a `role` field on their directory row still emit
        # a meaningful audit-row role (iter452 — adds hr/pm/safety mapping).
        kind = actor.get("_actor_kind")
        kind_map = {
            "safety_user": "safety",
            "hr_user": "hr",
            "pm_user": "pm",
            "shop_user": "shop",
            "dispatch_user": "dispatch",
        }
        role = (
            actor.get("_actor")
            or kind_map.get(kind)
            or actor.get("role")
            or "unknown"
        )
        actor_id = (
            actor.get("email")
            or actor.get("id")
            or actor.get("user_id")
            or actor.get("_id")
            or ""
        )
        name = (
            actor.get("name")
            or actor.get("display_name")
            or actor.get("full_name")
            or actor.get("email")
            or ""
        )
        return {"role": str(role)[:32], "id": str(actor_id)[:96], "name": str(name)[:96]}
    return {"role": "unknown", "id": "", "name": ""}


def _request_view(request: Optional[Request]) -> Dict[str, str]:
    if request is None:
        return {"ip": "", "user_agent": ""}
    try:
        ip = (
            (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
            or (request.client.host if request.client else "")
        )
    except Exception:
        ip = ""
    ua = (request.headers.get("user-agent") or "")[:240]
    return {"ip": ip, "user_agent": ua}


async def write_state_event(
    db,
    *,
    workflow: str,
    record_id: str,
    record_doc_id: str = "",
    from_state: Optional[str],
    to_state: str,
    actor: Any,
    reason: str = "",
    evidence: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> Dict[str, Any]:
    """Append a single workflow_state_events row. Returns the inserted
    document (minus ``_id``). Never raises — best-effort audit; the
    caller's state mutation is the durable change."""
    actor_view = _actor_view(actor)
    req_view = _request_view(request)
    doc = {
        "id": str(uuid.uuid4()),
        "workflow": workflow,
        "record_id": record_id,
        "record_doc_id": record_doc_id or "",
        "from_state": from_state,
        "to_state": to_state,
        "actor_role": actor_view["role"],
        "actor_id": actor_view["id"],
        "actor_name": actor_view["name"],
        "reason": (reason or "")[:2000],
        "evidence": dict(evidence or {}),
        "ip": req_view["ip"],
        "user_agent": req_view["user_agent"],
        "at": datetime.now(timezone.utc),
    }
    try:
        await db[WORKFLOW_STATE_EVENTS].insert_one(doc)
    except Exception:  # pragma: no cover — best effort
        pass
    doc.pop("_id", None)
    return doc


async def list_state_events(
    db,
    *,
    workflow: str,
    record_id: str,
    limit: int = 200,
) -> list:
    """Return the transition history for a single record, newest first.
    Excludes ``_id`` to keep the response JSON-serializable."""
    cur = (
        db[WORKFLOW_STATE_EVENTS]
        .find(
            {"workflow": workflow, "record_id": record_id},
            {"_id": 0},
        )
        .sort("at", -1)
        .limit(int(limit))
    )
    rows = await cur.to_list(int(limit))
    for r in rows:
        at = r.get("at")
        if hasattr(at, "isoformat"):
            r["at"] = at.isoformat()
    return rows


__all__ = [
    "WORKFLOW_STATE_EVENTS",
    "ensure_indexes",
    "write_state_event",
    "list_state_events",
]
