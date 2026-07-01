"""Track 19.16 · Phase A · SHARED CORRECTIVE ACTION ENGINE.

Platform primitive — NOT incident-specific. The ``consumer_kind`` +
``consumer_id`` fields let JHP, Daily Reports, QA/QC, Fleet, HR,
Environmental, and Customer modules reuse this engine without a redesign.

For incident cases, ``consumer_kind = 'incident_case'`` and
``consumer_id = case.id``. Every mutation emits a domain event so the
timeline stays authoritative.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .constants import (
    ACTION_CLASS_CODES,
    ACTION_DEFAULT_STATE,
    COLLECTION_CORRECTIVE_ACTIONS,
)
from .events import emit_event
from .models import CorrectiveAction
from .permissions import actor_can, normalize_role


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def create_action(
    db,
    *,
    consumer_kind: str,
    consumer_id: str,
    action_class: str,
    title: str,
    actor: Any,
    description: str = "",
    assigned_to_name: str = "",
    assigned_to_role: str = "",
    due_at: str = "",
) -> Dict[str, Any]:
    if not actor_can(actor, "corrective_action.assign"):
        raise PermissionError(
            f"role={normalize_role(actor)!r} cannot assign corrective actions"
        )
    if action_class not in ACTION_CLASS_CODES:
        raise ValueError(f"unknown action_class: {action_class!r}")
    if not (title or "").strip():
        raise ValueError("title required")

    role = normalize_role(actor)
    actor_name = ""
    if isinstance(actor, dict):
        actor_name = str(actor.get("name") or actor.get("email") or "")

    ca = CorrectiveAction(
        consumer_kind=(consumer_kind or "").strip().lower() or "incident_case",
        consumer_id=consumer_id,
        action_class=action_class,
        title=title.strip(),
        description=description.strip(),
        state="ASSIGNED" if assigned_to_name else ACTION_DEFAULT_STATE,
        assigned_to_name=assigned_to_name.strip(),
        assigned_to_role=assigned_to_role.strip(),
        assigned_at=_now() if assigned_to_name else "",
        due_at=due_at.strip(),
        created_by=actor_name,
    )
    doc = ca.model_dump()
    await db[COLLECTION_CORRECTIVE_ACTIONS].insert_one(doc)
    doc.pop("_id", None)

    # Emit only when consumer is an incident case (other consumers may
    # have their own event spine).
    if doc["consumer_kind"] == "incident_case":
        await emit_event(
            db,
            case_id=consumer_id,
            event_type="corrective_action.assigned",
            actor=actor,
            payload={
                "action_id":    doc["id"],
                "action_class": action_class,
                "title":        doc["title"],
                "assigned_to":  doc["assigned_to_name"],
            },
        )
    return doc


async def verify_action(
    db,
    *,
    action_id: str,
    actor: Any,
    verification_notes: str = "",
) -> Dict[str, Any]:
    if not actor_can(actor, "corrective_action.verify"):
        raise PermissionError(
            f"role={normalize_role(actor)!r} cannot verify corrective actions"
        )
    doc = await db[COLLECTION_CORRECTIVE_ACTIONS].find_one(
        {"id": action_id}, {"_id": 0}
    )
    if not doc:
        raise LookupError(f"corrective_action {action_id} not found")

    now = _now()
    role = normalize_role(actor)
    actor_name = ""
    if isinstance(actor, dict):
        actor_name = str(actor.get("name") or actor.get("email") or "")

    await db[COLLECTION_CORRECTIVE_ACTIONS].update_one(
        {"id": action_id},
        {"$set": {
            "state":              "VERIFIED",
            "verified_at":        now,
            "verified_by":        actor_name,
            "verification_notes": (verification_notes or "").strip(),
        }},
    )

    if doc["consumer_kind"] == "incident_case":
        await emit_event(
            db,
            case_id=doc["consumer_id"],
            event_type="corrective_action.verified",
            actor=actor,
            payload={"action_id": action_id},
        )

    doc.update({
        "state":              "VERIFIED",
        "verified_at":        now,
        "verified_by":        actor_name,
        "verification_notes": (verification_notes or "").strip(),
    })
    return doc


async def cancel_action(
    db,
    *,
    action_id: str,
    actor: Any,
    reason: str,
) -> Dict[str, Any]:
    if not actor_can(actor, "corrective_action.assign"):
        raise PermissionError("cancel requires corrective_action.assign")
    if not (reason or "").strip():
        raise ValueError("cancel reason required")
    doc = await db[COLLECTION_CORRECTIVE_ACTIONS].find_one(
        {"id": action_id}, {"_id": 0}
    )
    if not doc:
        raise LookupError(f"corrective_action {action_id} not found")

    now = _now()
    await db[COLLECTION_CORRECTIVE_ACTIONS].update_one(
        {"id": action_id},
        {"$set": {
            "state":            "CANCELED",
            "canceled_at":      now,
            "canceled_reason":  reason.strip(),
        }},
    )

    if doc["consumer_kind"] == "incident_case":
        await emit_event(
            db,
            case_id=doc["consumer_id"],
            event_type="corrective_action.canceled",
            actor=actor,
            reason=reason,
            payload={"action_id": action_id},
        )

    doc.update({
        "state":            "CANCELED",
        "canceled_at":      now,
        "canceled_reason":  reason.strip(),
    })
    return doc


async def list_actions(
    db,
    *,
    consumer_kind: Optional[str] = None,
    consumer_id: Optional[str] = None,
    state: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if consumer_kind:
        q["consumer_kind"] = consumer_kind
    if consumer_id:
        q["consumer_id"] = consumer_id
    if state:
        q["state"] = state.upper()
    cur = db[COLLECTION_CORRECTIVE_ACTIONS].find(q, {"_id": 0}).sort("created_at", 1)
    return [d async for d in cur]


async def summary_for_case(db, *, case_id: str) -> Dict[str, int]:
    """Counts used by the case list projections. Cheap group-by."""
    q = {"consumer_kind": "incident_case", "consumer_id": case_id}
    total = await db[COLLECTION_CORRECTIVE_ACTIONS].count_documents(q)
    open_ = await db[COLLECTION_CORRECTIVE_ACTIONS].count_documents(
        {**q, "state": {"$in": ["OPEN", "ASSIGNED", "IN_PROGRESS"]}}
    )
    return {"total": total, "open": open_}


__all__ = [
    "create_action",
    "verify_action",
    "cancel_action",
    "list_actions",
    "summary_for_case",
]
