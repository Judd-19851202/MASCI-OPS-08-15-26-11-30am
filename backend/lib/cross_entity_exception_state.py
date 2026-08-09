from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


CROSS_ENTITY_EXCEPTION_COLLECTION = "cross_entity_exception_state"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_exception_key(
    *,
    family: str,
    source_collection: str,
    source_record_id: str,
    relationship_type: str,
    source_subkey: str = "",
) -> str:
    return "|".join(
        [
            family.strip(),
            source_collection.strip(),
            source_record_id.strip(),
            relationship_type.strip(),
            source_subkey.strip(),
        ]
    )


async def ensure_exception_indexes(db) -> None:
    await db[CROSS_ENTITY_EXCEPTION_COLLECTION].create_index("key", unique=True)
    await db[CROSS_ENTITY_EXCEPTION_COLLECTION].create_index("family")
    await db[CROSS_ENTITY_EXCEPTION_COLLECTION].create_index("active")
    await db[CROSS_ENTITY_EXCEPTION_COLLECTION].create_index("blocks_gate")


async def upsert_cross_entity_exception(
    db,
    *,
    family: str,
    source_collection: str,
    source_record_id: str,
    relationship_type: str,
    reason_code: str,
    reason_detail: str,
    status: str,
    review_status: str,
    blocks_gate: bool,
    evidence_available: bool,
    source_record_doc_id: str = "",
    source_subkey: str = "",
    source_project_number: str = "",
    source_project_name: str = "",
    entity_type: str = "",
    age_days: Optional[int] = None,
    candidate_matches: Optional[List[Dict[str, Any]]] = None,
    evidence_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    await ensure_exception_indexes(db)
    key = build_exception_key(
        family=family,
        source_collection=source_collection,
        source_record_id=source_record_id,
        relationship_type=relationship_type,
        source_subkey=source_subkey,
    )
    existing = await db[CROSS_ENTITY_EXCEPTION_COLLECTION].find_one({"key": key}, {"_id": 0}) or {}
    now = _now_iso()
    doc = {
        "key": key,
        "family": family,
        "source_collection": source_collection,
        "source_record_id": source_record_id,
        "source_record_doc_id": source_record_doc_id,
        "source_subkey": source_subkey,
        "relationship_type": relationship_type,
        "entity_type": entity_type,
        "reason_code": reason_code,
        "reason_detail": reason_detail,
        "status": status,
        "review_status": review_status,
        "blocks_gate": bool(blocks_gate),
        "evidence_available": bool(evidence_available),
        "source_project_number": source_project_number,
        "source_project_name": source_project_name,
        "age_days": age_days,
        "candidate_matches": candidate_matches or [],
        "evidence_summary": evidence_summary or {},
        "active": True,
        "updated_at": now,
        "resolved_at": None if status not in {"resolved", "excluded_non_operational", "accepted_historical_gap"} else existing.get("resolved_at"),
    }
    await db[CROSS_ENTITY_EXCEPTION_COLLECTION].update_one(
        {"key": key},
        {"$set": doc, "$setOnInsert": {"first_recorded_at": existing.get("first_recorded_at") or now}},
        upsert=True,
    )
    doc["first_recorded_at"] = existing.get("first_recorded_at") or now
    return doc


async def mark_cross_entity_exception_resolved(
    db,
    *,
    family: str,
    source_collection: str,
    source_record_id: str,
    relationship_type: str,
    source_subkey: str = "",
    resolution_note: str = "",
) -> None:
    await ensure_exception_indexes(db)
    key = build_exception_key(
        family=family,
        source_collection=source_collection,
        source_record_id=source_record_id,
        relationship_type=relationship_type,
        source_subkey=source_subkey,
    )
    await db[CROSS_ENTITY_EXCEPTION_COLLECTION].update_one(
        {"key": key},
        {
            "$set": {
                "status": "resolved",
                "review_status": "closed",
                "blocks_gate": False,
                "active": False,
                "resolved_at": _now_iso(),
                "resolution_note": resolution_note,
                "updated_at": _now_iso(),
            }
        },
    )


async def load_active_exception_map(db, *, family: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    query: Dict[str, Any] = {"active": True}
    if family:
        query["family"] = family
    rows = await db[CROSS_ENTITY_EXCEPTION_COLLECTION].find(query, {"_id": 0}).to_list(10000)
    return {str(row.get("key") or ""): row for row in rows if str(row.get("key") or "")}


async def list_cross_entity_exceptions(
    db,
    *,
    active_only: bool = True,
    limit: int = 20000,
) -> List[Dict[str, Any]]:
    await ensure_exception_indexes(db)
    query: Dict[str, Any] = {"active": True} if active_only else {}
    rows = await db[CROSS_ENTITY_EXCEPTION_COLLECTION].find(query, {"_id": 0}).sort([
        ("blocks_gate", -1),
        ("family", 1),
        ("source_collection", 1),
        ("source_record_doc_id", 1),
        ("source_record_id", 1),
    ]).to_list(limit)
    return rows


def exceptions_to_csv(rows: Iterable[Dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "family",
        "source_collection",
        "source_record_id",
        "source_record_doc_id",
        "relationship_type",
        "entity_type",
        "status",
        "review_status",
        "blocks_gate",
        "reason_code",
        "reason_detail",
        "source_project_number",
        "source_project_name",
        "evidence_available",
        "age_days",
        "candidate_match_count",
        "first_recorded_at",
        "updated_at",
    ])
    for row in rows:
        writer.writerow([
            row.get("family") or "",
            row.get("source_collection") or "",
            row.get("source_record_id") or "",
            row.get("source_record_doc_id") or "",
            row.get("relationship_type") or "",
            row.get("entity_type") or "",
            row.get("status") or "",
            row.get("review_status") or "",
            "true" if row.get("blocks_gate") else "false",
            row.get("reason_code") or "",
            row.get("reason_detail") or "",
            row.get("source_project_number") or "",
            row.get("source_project_name") or "",
            "true" if row.get("evidence_available") else "false",
            row.get("age_days") if row.get("age_days") is not None else "",
            len(row.get("candidate_matches") or []),
            row.get("first_recorded_at") or "",
            row.get("updated_at") or "",
        ])
    return buf.getvalue()


__all__ = [
    "CROSS_ENTITY_EXCEPTION_COLLECTION",
    "build_exception_key",
    "ensure_exception_indexes",
    "upsert_cross_entity_exception",
    "mark_cross_entity_exception_resolved",
    "load_active_exception_map",
    "list_cross_entity_exceptions",
    "exceptions_to_csv",
]