"""Track 19.16 · Phase A · Incident Intelligence Engine — EVENT SPINE.

Every mutation writes a structured domain event. The event log is:
    * the authoritative TIMELINE (Universal Timeline pillar)
    * the AUDIT ledger (Trusted pillar)
    * the EVENT SPINE for future subscribers — notifications, dashboards,
      integrations, AI (AI Readiness pillar)

No consumer is coupled here. This module only writes and reads.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .constants import COLLECTION_CASE_EVENTS, EVENT_TYPES_SET
from .models import CaseEvent
from .permissions import normalize_role


async def emit_event(
    db,
    *,
    case_id: str,
    event_type: str,
    actor: Any = None,
    from_state: str = "",
    to_state: str = "",
    reason: str = "",
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Persist a single case event. Returns the stored document (no _id)."""
    if event_type not in EVENT_TYPES_SET:
        raise ValueError(f"unknown event_type: {event_type!r}")

    actor_name = ""
    if isinstance(actor, dict):
        actor_name = str(
            actor.get("name") or actor.get("email") or actor.get("username") or ""
        )

    event = CaseEvent(
        case_id=case_id,
        event_type=event_type,
        actor_name=actor_name,
        actor_role=normalize_role(actor),
        from_state=(from_state or "").upper(),
        to_state=(to_state or "").upper(),
        reason=(reason or "").strip(),
        payload=dict(payload or {}),
    )
    doc = event.model_dump()
    await db[COLLECTION_CASE_EVENTS].insert_one(doc)
    doc.pop("_id", None)
    return doc


async def list_events(
    db,
    *,
    case_id: str,
    limit: int = 500,
    event_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Read the timeline for a case. Chronological ASC."""
    q: Dict[str, Any] = {"case_id": case_id}
    if event_types:
        q["event_type"] = {"$in": list(event_types)}
    cur = (
        db[COLLECTION_CASE_EVENTS]
        .find(q, {"_id": 0})
        .sort("at", 1)
        .limit(max(1, min(int(limit), 2000)))
    )
    return [d async for d in cur]


async def count_events(db, *, case_id: str) -> int:
    return await db[COLLECTION_CASE_EVENTS].count_documents({"case_id": case_id})


__all__ = ["emit_event", "list_events", "count_events"]
