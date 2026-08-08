"""Track 19.16 · Phase A · CASE SERVICE LAYER.

High-level orchestration around the incident_cases collection.
Routes call these functions; they handle event emission, immutability
enforcement, transition validation, cross-linking, and counter refresh.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .constants import (
    CASE_DEFAULT_STATE,
    COLLECTION_CASES,
    COLLECTION_CASE_EVIDENCE,
    CROSS_LINK_KIND_CODES,
    IMMUTABLE_AFTER_STATES,
)
from .corrective_actions import summary_for_case
from .events import emit_event
from .models import CrossLink, FieldBlock, IncidentCase, SafetyBlock
from .permissions import actor_can, normalize_role
from .state_machine import coerce_state, field_block_immutable, validate_transition


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _actor_name(actor: Any) -> str:
    if isinstance(actor, dict):
        return str(actor.get("name") or actor.get("email") or actor.get("username") or "")
    return ""


async def _next_case_number(db) -> str:
    """Simple monotonic case number. YYYY-N format."""
    year = datetime.now(timezone.utc).year
    count = await db[COLLECTION_CASES].count_documents({"case_number": {"$regex": f"^{year}-"}})
    return f"{year}-{count + 1:05d}"


async def create_case(
    db,
    *,
    actor: Any,
    field_block: Dict[str, Any],
    tenant_id: str = "",
) -> Dict[str, Any]:
    if not actor_can(actor, "case.create"):
        raise PermissionError(
            f"role={normalize_role(actor)!r} cannot create incident cases"
        )
    fb = FieldBlock(**dict(field_block or {}))
    case = IncidentCase(
        tenant_id=tenant_id,
        field_block=fb,
        safety_block=SafetyBlock(),
        created_by=_actor_name(actor),
    )
    doc = case.model_dump()
    await db[COLLECTION_CASES].insert_one(doc)
    doc.pop("_id", None)

    await emit_event(
        db,
        case_id=doc["id"],
        event_type="case.created",
        actor=actor,
        to_state=doc["state"],
        payload={"incident_type": fb.incident_type},
    )
    return doc


async def get_case(db, case_id: str) -> Optional[Dict[str, Any]]:
    doc = await db[COLLECTION_CASES].find_one({"id": case_id}, {"_id": 0})
    return doc


async def list_cases(
    db,
    *,
    actor: Any,
    state: Optional[str] = None,
    incident_type: Optional[str] = None,
    query: Optional[str] = None,
    include_archived: bool = False,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    if not (actor_can(actor, "case.read_all") or actor_can(actor, "case.read_own")):
        raise PermissionError(
            f"role={normalize_role(actor)!r} cannot list incident cases"
        )
    q: Dict[str, Any] = {}
    if not include_archived:
        q["archived"] = {"$ne": True}
    if state:
        q["state"] = state.upper()
    if incident_type:
        q["field_block.incident_type"] = incident_type.lower()
    if query:
        rx = {"$regex": str(query).strip(), "$options": "i"}
        q["$or"] = [
            {"case_number": rx},
            {"field_block.job_number": rx},
            {"field_block.location_label": rx},
            {"field_block.reporter_name": rx},
            {"field_block.observed_conditions": rx},
            {"safety_block.root_cause_summary": rx},
        ]
    cur = (
        db[COLLECTION_CASES]
        .find(q, {"_id": 0})
        .sort("created_at", -1)
        .limit(max(1, min(int(limit), 500)))
    )
    return [d async for d in cur]


async def update_field_block(
    db,
    *,
    case_id: str,
    actor: Any,
    patch: Dict[str, Any],
) -> Dict[str, Any]:
    if not actor_can(actor, "field_block.write"):
        raise PermissionError(
            f"role={normalize_role(actor)!r} cannot write field_block"
        )
    doc = await get_case(db, case_id)
    if not doc:
        raise LookupError(f"case {case_id} not found")
    if field_block_immutable(doc.get("state")):
        raise PermissionError("field_block_immutable")

    fb = dict(doc.get("field_block") or {})
    fb.update({k: v for k, v in (patch or {}).items() if v is not None})
    # Validate the merged block.
    FieldBlock(**fb)

    now = _now()
    await db[COLLECTION_CASES].update_one(
        {"id": case_id},
        {"$set": {"field_block": fb, "updated_at": now}},
    )
    await emit_event(
        db,
        case_id=case_id,
        event_type="field_block.updated",
        actor=actor,
        payload={"fields": sorted(list((patch or {}).keys()))},
    )
    doc["field_block"] = fb
    doc["updated_at"] = now
    return doc


async def update_safety_block(
    db,
    *,
    case_id: str,
    actor: Any,
    patch: Dict[str, Any],
) -> Dict[str, Any]:
    if not actor_can(actor, "safety_block.write"):
        raise PermissionError(
            f"role={normalize_role(actor)!r} cannot write safety_block"
        )
    doc = await get_case(db, case_id)
    if not doc:
        raise LookupError(f"case {case_id} not found")

    sb = dict(doc.get("safety_block") or {})
    prev_recordable = sb.get("osha_recordable")
    prev_root = sb.get("root_cause_summary")

    sb.update({k: v for k, v in (patch or {}).items() if v is not None})
    SafetyBlock(**sb)

    now = _now()
    await db[COLLECTION_CASES].update_one(
        {"id": case_id},
        {"$set": {"safety_block": sb, "updated_at": now}},
    )
    await emit_event(
        db,
        case_id=case_id,
        event_type="safety_block.updated",
        actor=actor,
        payload={"fields": sorted(list((patch or {}).keys()))},
    )
    if "osha_recordable" in (patch or {}) and sb.get("osha_recordable") != prev_recordable:
        await emit_event(
            db,
            case_id=case_id,
            event_type="recordability.changed",
            actor=actor,
            payload={"from": prev_recordable, "to": sb.get("osha_recordable")},
        )
    if "root_cause_summary" in (patch or {}) and sb.get("root_cause_summary") != prev_root:
        await emit_event(
            db,
            case_id=case_id,
            event_type="root_cause.updated",
            actor=actor,
            payload={"length": len(sb.get("root_cause_summary") or "")},
        )
    doc["safety_block"] = sb
    doc["updated_at"] = now
    return doc


async def transition_case(
    db,
    *,
    case_id: str,
    to_state: str,
    actor: Any,
    reason: str = "",
) -> Dict[str, Any]:
    doc = await get_case(db, case_id)
    if not doc:
        raise LookupError(f"case {case_id} not found")

    fs = coerce_state(doc.get("state"))
    ok, err = validate_transition(
        from_state=fs, to_state=to_state, actor=actor, reason=reason
    )
    if not ok:
        raise PermissionError(err)

    ts = to_state.strip().upper()
    now = _now()
    update: Dict[str, Any] = {"state": ts, "updated_at": now}

    if ts == "FIELD_SUBMITTED":
        # Assign case number + submitted_at; lock the field block.
        if not doc.get("case_number"):
            update["case_number"] = await _next_case_number(db)
        update["submitted_at"] = now
        update["field_block_locked"] = True
    if ts == "CLOSED":
        update["closed_at"] = now
    if ts == "REOPENED":
        update["reopened_at"] = now
        update["closed_at"] = ""
        update["archived"] = False
        update["archived_at"] = ""
        update["archived_by"] = ""
        update["archived_reason"] = ""

    # Field observations become immutable at every non-DRAFT state.
    if ts in IMMUTABLE_AFTER_STATES:
        update["field_block_locked"] = True

    await db[COLLECTION_CASES].update_one({"id": case_id}, {"$set": update})

    await emit_event(
        db,
        case_id=case_id,
        event_type="case.state_changed",
        actor=actor,
        from_state=fs,
        to_state=ts,
        reason=reason,
    )
    if ts == "FIELD_SUBMITTED":
        await emit_event(
            db,
            case_id=case_id,
            event_type="case.field_submitted",
            actor=actor,
            payload={"case_number": update.get("case_number", doc.get("case_number", ""))},
        )
    if ts == "REOPENED":
        await emit_event(
            db,
            case_id=case_id,
            event_type="case.reopened",
            actor=actor,
            reason=reason,
        )
    if ts == "CLOSED":
        await emit_event(
            db,
            case_id=case_id,
            event_type="case.closed",
            actor=actor,
        )

    doc.update(update)
    return doc


async def archive_case(
    db,
    *,
    case_id: str,
    actor: Any,
    reason: str,
) -> Dict[str, Any]:
    if not actor_can(actor, "transition.close"):
        raise PermissionError("role_not_authorized")
    doc = await get_case(db, case_id)
    if not doc:
        raise LookupError(f"case {case_id} not found")
    if (doc.get("state") or "").upper() != "CLOSED":
        raise ValueError("case_must_be_closed_before_archive")
    now = _now()
    update = {
        "archived": True,
        "archived_at": now,
        "archived_by": _actor_name(actor),
        "archived_reason": str(reason or "").strip(),
        "updated_at": now,
    }
    await db[COLLECTION_CASES].update_one({"id": case_id}, {"$set": update})
    await emit_event(
        db,
        case_id=case_id,
        event_type="case.archived",
        actor=actor,
        reason=update["archived_reason"],
        payload={"archived_at": now},
    )
    doc.update(update)
    return doc


async def add_cross_link(
    db,
    *,
    case_id: str,
    actor: Any,
    kind: str,
    target_id: str,
    target_label: str = "",
) -> Dict[str, Any]:
    if not actor_can(actor, "cross_link.write"):
        raise PermissionError(
            f"role={normalize_role(actor)!r} cannot write cross links"
        )
    if kind.lower() not in CROSS_LINK_KIND_CODES:
        raise ValueError(f"unknown cross_link kind: {kind!r}")
    doc = await get_case(db, case_id)
    if not doc:
        raise LookupError(f"case {case_id} not found")

    link = CrossLink(
        kind=kind.lower(),
        target_id=target_id,
        target_label=target_label,
        added_by=_actor_name(actor),
    )
    link_doc = link.model_dump()
    await db[COLLECTION_CASES].update_one(
        {"id": case_id},
        {"$push": {"cross_links": link_doc}, "$set": {"updated_at": _now()}},
    )
    await emit_event(
        db,
        case_id=case_id,
        event_type="cross_link.attached",
        actor=actor,
        payload={
            "link_id": link_doc["id"],
            "kind": kind.lower(),
            "target_id": target_id,
        },
    )
    return link_doc


async def remove_cross_link(
    db, *, case_id: str, actor: Any, link_id: str,
) -> None:
    if not actor_can(actor, "cross_link.write"):
        raise PermissionError("cross_link.write required")
    result = await db[COLLECTION_CASES].update_one(
        {"id": case_id},
        {"$pull": {"cross_links": {"id": link_id}}, "$set": {"updated_at": _now()}},
    )
    if result.modified_count == 0:
        raise LookupError(f"cross_link {link_id} not found on case {case_id}")
    await emit_event(
        db,
        case_id=case_id,
        event_type="cross_link.removed",
        actor=actor,
        payload={"link_id": link_id},
    )


async def refresh_counters(db, *, case_id: str) -> Dict[str, int]:
    """Refresh the cached counters (evidence + corrective action) on a case."""
    ev_total = await db[COLLECTION_CASE_EVIDENCE].count_documents(
        {"case_id": case_id, "withdrawn": False}
    )
    ca = await summary_for_case(db, case_id=case_id)
    await db[COLLECTION_CASES].update_one(
        {"id": case_id},
        {"$set": {
            "evidence_count":            ev_total,
            "corrective_action_count":   ca["total"],
            "corrective_action_open":    ca["open"],
        }},
    )
    return {
        "evidence_count":          ev_total,
        "corrective_action_count": ca["total"],
        "corrective_action_open":  ca["open"],
    }


async def record_executive_review(
    db, *, case_id: str, actor: Any, notes: str,
) -> Dict[str, Any]:
    if not actor_can(actor, "executive_review.record"):
        raise PermissionError("executive_review.record required")
    doc = await get_case(db, case_id)
    if not doc:
        raise LookupError(f"case {case_id} not found")

    now = _now()
    sb = dict(doc.get("safety_block") or {})
    sb["executive_reviewer"] = _actor_name(actor)
    sb["executive_review_notes"] = (notes or "").strip()

    await db[COLLECTION_CASES].update_one(
        {"id": case_id},
        {"$set": {"safety_block": sb, "updated_at": now}},
    )
    await emit_event(
        db,
        case_id=case_id,
        event_type="executive_review.recorded",
        actor=actor,
        payload={"reviewer": sb["executive_reviewer"]},
    )
    doc["safety_block"] = sb
    doc["updated_at"] = now
    return doc


__all__ = [
    "create_case",
    "get_case",
    "list_cases",
    "update_field_block",
    "update_safety_block",
    "transition_case",
    "add_cross_link",
    "remove_cross_link",
    "refresh_counters",
    "record_executive_review",
]
