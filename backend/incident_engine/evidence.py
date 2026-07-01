"""Track 19.16 · Phase A · Incident Intelligence Engine — EVIDENCE ENGINE.

Typed evidence with chain-of-custody. Withdrawal is soft — the evidence
row is never deleted; ``withdrawn=True`` + reason preserved. This is the
Trusted pillar guarantee for evidence provenance.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .constants import (
    COLLECTION_CASE_EVIDENCE,
    EVIDENCE_TYPES,
    EVIDENCE_TYPE_CODES,
)
from .events import emit_event
from .models import EvidenceItem
from .permissions import actor_can, normalize_role


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def evidence_side(evidence_type: str) -> str:
    """Return 'field' | 'safety' | 'either' for a given evidence type."""
    et = (evidence_type or "").strip().lower()
    for code, _en, _es, side in EVIDENCE_TYPES:
        if code == et:
            return side
    return ""


def required_capability_for(evidence_type: str) -> str:
    """Which capability an actor needs to ADD this evidence type."""
    side = evidence_side(evidence_type)
    if side == "field":
        return "evidence.add_field"
    return "evidence.add_safety"


async def add_evidence(
    db,
    *,
    case_id: str,
    evidence_type: str,
    actor: Any,
    label: str = "",
    description: str = "",
    storage_key: str = "",
    external_url: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Add typed evidence to a case. Emits ``evidence.added`` on success."""
    if evidence_type not in EVIDENCE_TYPE_CODES:
        raise ValueError(f"unknown evidence_type: {evidence_type!r}")

    cap = required_capability_for(evidence_type)
    if not actor_can(actor, cap):
        raise PermissionError(
            f"role={normalize_role(actor)!r} cannot add evidence_type={evidence_type!r}"
        )

    role = normalize_role(actor)
    actor_name = ""
    if isinstance(actor, dict):
        actor_name = str(actor.get("name") or actor.get("email") or "")

    item = EvidenceItem(
        case_id=case_id,
        evidence_type=evidence_type,
        label=label.strip(),
        description=description.strip(),
        storage_key=storage_key.strip(),
        external_url=external_url.strip(),
        metadata=dict(metadata or {}),
        added_by=actor_name,
        added_by_role=role,
        custody_chain=[{
            "action": "added",
            "at": _now(),
            "actor_name": actor_name,
            "actor_role": role,
        }],
    )
    doc = item.model_dump()
    await db[COLLECTION_CASE_EVIDENCE].insert_one(doc)
    doc.pop("_id", None)

    await emit_event(
        db,
        case_id=case_id,
        event_type="evidence.added",
        actor=actor,
        payload={"evidence_id": doc["id"], "evidence_type": evidence_type},
    )
    return doc


async def list_evidence(
    db,
    *,
    case_id: str,
    include_withdrawn: bool = True,
) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {"case_id": case_id}
    if not include_withdrawn:
        q["withdrawn"] = False
    cur = db[COLLECTION_CASE_EVIDENCE].find(q, {"_id": 0}).sort("added_at", 1)
    return [d async for d in cur]


async def withdraw_evidence(
    db,
    *,
    evidence_id: str,
    actor: Any,
    reason: str,
) -> Dict[str, Any]:
    """Soft-withdraw evidence. Row is preserved for chain-of-custody."""
    if not actor_can(actor, "evidence.withdraw"):
        raise PermissionError(
            f"role={normalize_role(actor)!r} cannot withdraw evidence"
        )
    if not (reason or "").strip():
        raise ValueError("withdrawal reason required")

    doc = await db[COLLECTION_CASE_EVIDENCE].find_one(
        {"id": evidence_id}, {"_id": 0}
    )
    if not doc:
        raise LookupError(f"evidence {evidence_id} not found")

    now = _now()
    role = normalize_role(actor)
    actor_name = ""
    if isinstance(actor, dict):
        actor_name = str(actor.get("name") or actor.get("email") or "")

    custody = list(doc.get("custody_chain") or [])
    custody.append({
        "action": "withdrawn",
        "at": now,
        "actor_name": actor_name,
        "actor_role": role,
        "reason": reason.strip(),
    })

    await db[COLLECTION_CASE_EVIDENCE].update_one(
        {"id": evidence_id},
        {"$set": {
            "withdrawn":         True,
            "withdrawn_at":      now,
            "withdrawn_by":      actor_name,
            "withdrawal_reason": reason.strip(),
            "custody_chain":     custody,
        }},
    )

    await emit_event(
        db,
        case_id=doc["case_id"],
        event_type="evidence.withdrawn",
        actor=actor,
        reason=reason,
        payload={"evidence_id": evidence_id},
    )
    doc.update({
        "withdrawn":         True,
        "withdrawn_at":      now,
        "withdrawn_by":      actor_name,
        "withdrawal_reason": reason.strip(),
        "custody_chain":     custody,
    })
    return doc


__all__ = [
    "evidence_side",
    "required_capability_for",
    "add_evidence",
    "list_evidence",
    "withdraw_evidence",
]
