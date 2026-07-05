"""DR-ROI-001D · Photo Intelligence store."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


COLL_PHOTO_INTEL = "dr_v2_photo_intelligence"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def ensure_indexes(db) -> None:
    try:
        await db[COLL_PHOTO_INTEL].create_index(
            [("report_id", 1), ("photo_id", 1)],
            unique=True, name="dr_v2_photo_intel_key",
        )
        await db[COLL_PHOTO_INTEL].create_index("evidence_hash", name="dr_v2_photo_intel_hash")
        await db[COLL_PHOTO_INTEL].create_index("project_id", name="dr_v2_photo_intel_project")
    except Exception:  # noqa: BLE001
        pass


async def get_intel(db, *, report_id: str, photo_id: str) -> Optional[Dict[str, Any]]:
    return await db[COLL_PHOTO_INTEL].find_one(
        {"report_id": report_id, "photo_id": photo_id}, {"_id": 0},
    )


async def upsert_intel(
    db, *, report_id: str, photo_id: str,
    project_id: str, tenant_id: str,
    evidence_hash: str, envelope: Dict[str, Any],
    provider: str, model: str,
) -> Dict[str, Any]:
    doc = await db[COLL_PHOTO_INTEL].find_one(
        {"report_id": report_id, "photo_id": photo_id}, {"_id": 0},
    )
    now = _now()
    if doc is None:
        doc = {
            "intel_id": uuid.uuid4().hex,
            "report_id": report_id, "photo_id": photo_id,
            "project_id": project_id, "tenant_id": tenant_id,
            "created_at": now,
        }
    # Attach analysis
    raw = (envelope.get("raw") or {}) if isinstance(envelope, dict) else {}
    observations = raw.get("observations") or envelope.get("observations") or []
    suggested_links = raw.get("suggested_links") or envelope.get("suggested_links") or []
    questions = raw.get("questions") or envelope.get("questions") or []
    conflicts = raw.get("conflicts") or envelope.get("conflicts") or []

    # Ensure every suggested link has an id + default status
    for s in suggested_links:
        s.setdefault("link_id", uuid.uuid4().hex)
        s.setdefault("status", "suggested")
    for q in questions:
        q.setdefault("question_id", uuid.uuid4().hex)
        q.setdefault("status", "open")
    for o in observations:
        o.setdefault("requires_supervisor_confirmation", True)

    doc.update({
        "evidence_hash": evidence_hash,
        "analysis_status": "complete" if envelope.get("ai_available") else "unavailable",
        "provider": provider, "model": model,
        "observations": observations,
        "suggested_links": suggested_links,
        "questions": questions,
        "conflicts": conflicts,
        "confidence": envelope.get("confidence", 0.0),
        "narrative": envelope.get("narrative", ""),
        "updated_at": now,
        "trace_id": envelope.get("trace_id") or uuid.uuid4().hex,
    })
    await db[COLL_PHOTO_INTEL].update_one(
        {"report_id": report_id, "photo_id": photo_id},
        {"$set": doc},
        upsert=True,
    )
    return doc


async def _update_link_status(
    db, *, report_id: str, photo_id: str, link_id: str,
    status: str, reviewed_by: str,
) -> Optional[Dict[str, Any]]:
    doc = await db[COLL_PHOTO_INTEL].find_one(
        {"report_id": report_id, "photo_id": photo_id}, {"_id": 0},
    )
    if not doc:
        return None
    changed = False
    for s in doc.get("suggested_links", []):
        if s.get("link_id") == link_id:
            s["status"] = status
            s["reviewed_by"] = reviewed_by
            s["reviewed_at"] = _now()
            changed = True
    if not changed:
        return None
    await db[COLL_PHOTO_INTEL].update_one(
        {"report_id": report_id, "photo_id": photo_id},
        {"$set": {"suggested_links": doc["suggested_links"], "updated_at": _now()}},
    )
    return doc


async def accept_link(db, *, report_id: str, photo_id: str, link_id: str, reviewed_by: str):
    return await _update_link_status(
        db, report_id=report_id, photo_id=photo_id,
        link_id=link_id, status="accepted", reviewed_by=reviewed_by,
    )


async def dismiss_link(db, *, report_id: str, photo_id: str, link_id: str, reviewed_by: str):
    return await _update_link_status(
        db, report_id=report_id, photo_id=photo_id,
        link_id=link_id, status="dismissed", reviewed_by=reviewed_by,
    )


async def resolve_question(
    db, *, report_id: str, photo_id: str, question_id: str,
    resolution: str, reviewed_by: str,
) -> Optional[Dict[str, Any]]:
    doc = await db[COLL_PHOTO_INTEL].find_one(
        {"report_id": report_id, "photo_id": photo_id}, {"_id": 0},
    )
    if not doc:
        return None
    changed = False
    for q in doc.get("questions", []):
        if q.get("question_id") == question_id:
            q["status"] = "resolved"
            q["resolution"] = resolution
            q["reviewed_by"] = reviewed_by
            q["reviewed_at"] = _now()
            changed = True
    if not changed:
        return None
    await db[COLL_PHOTO_INTEL].update_one(
        {"report_id": report_id, "photo_id": photo_id},
        {"$set": {"questions": doc["questions"], "updated_at": _now()}},
    )
    return doc
