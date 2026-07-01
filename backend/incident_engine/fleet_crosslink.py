"""Track 19.16 · Closeout · Fleet / Equipment cross-link.

Read-only. Never writes. Never mutates any incident case. The
Equipment Status Board joins its rows to recent incident cases by
`unit_number` — a flat list the field UI writes onto every case
whenever a picker selects a row from ``equipment_master``.

No new schema. No new collection. No new write path.

The Board displays only:
    * case_id / case_number
    * incident_type
    * state
    * occurred_at
    * severity (if present)

Everything else lives on the Safety Case Workspace — the Board is a
pointer, not a duplicate.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# What is safe to expose on the Board pill. Everything else stays inside
# the Safety Case Workspace / Report Intelligence Engine.
_PROJECTION: Dict[str, int] = {
    "_id": 0,
    "id": 1,
    "case_number": 1,
    "state": 1,
    "field_block.incident_type": 1,
    "field_block.occurred_at_date": 1,
    "field_block.occurred_at_time": 1,
    "field_block.severity": 1,
    "field_block.selected_unit_numbers": 1,
    "submitted_at": 1,
    "created_at": 1,
}


def _summarize(doc: Dict[str, Any]) -> Dict[str, Any]:
    fb = doc.get("field_block") or {}
    return {
        "case_id":       doc.get("id"),
        "case_number":   doc.get("case_number"),
        "state":         doc.get("state"),
        "incident_type": fb.get("incident_type"),
        "occurred_at_date": fb.get("occurred_at_date"),
        "occurred_at_time": fb.get("occurred_at_time"),
        "severity":      fb.get("severity"),
        "submitted_at":  doc.get("submitted_at") or doc.get("created_at"),
    }


async def list_incidents_by_unit(
    db, *, unit_numbers: Optional[List[str]] = None, limit_per_unit: int = 3,
) -> Dict[str, List[Dict[str, Any]]]:
    """Return {unit_number: [<summary>, ...]} for every unit that has
    been touched by an incident case. Never returns raw case bodies.

    Implementation: Mongo scan + Python filter. This is fine at the
    scale of incident cases (dozens per week) and keeps the query
    simple (no `$exists`/`$type` matrix, no array-membership operator
    variance across drivers). The Board hits this endpoint once per
    load; cache upstream if pressure ever appears.
    """
    filter_set = None
    if unit_numbers:
        filter_set = {str(u) for u in unit_numbers if u}

    cursor = db.incident_cases.find({}, _PROJECTION)
    cursor = cursor.sort("submitted_at", -1)
    out: Dict[str, List[Dict[str, Any]]] = {}
    async for doc in cursor:
        fb = doc.get("field_block") or {}
        units = fb.get("selected_unit_numbers") or []
        if not units:
            continue
        for u in units:
            key = str(u)
            if filter_set is not None and key not in filter_set:
                continue
            bucket = out.setdefault(key, [])
            if len(bucket) < limit_per_unit:
                bucket.append(_summarize(doc))
    return out


__all__ = ["list_incidents_by_unit"]
