"""ODS-001 · Read helpers for PM/Admin query surface."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .store import COLL_FACTS


async def list_facts(
    db, *, tenant_id: str, project_id: Optional[str] = None,
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    fact_type: Optional[str] = None, is_current: bool = True,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {"tenant_id": tenant_id, "is_current": is_current}
    if project_id:
        q["project_id"] = project_id
    if fact_type:
        q["fact_type"] = fact_type
    if date_from or date_to:
        q["date"] = {}
        if date_from:
            q["date"]["$gte"] = date_from
        if date_to:
            q["date"]["$lte"] = date_to
    cursor = db[COLL_FACTS].find(q, {"_id": 0}).sort([("date", -1), ("fact_type", 1)]).limit(int(limit))
    return [d async for d in cursor]


async def project_summary(
    db, *, tenant_id: str, project_id: str,
    date_from: Optional[str] = None, date_to: Optional[str] = None,
) -> Dict[str, Any]:
    """Cross-fact-type summary for one project. Cheap read using indexes."""
    q: Dict[str, Any] = {"tenant_id": tenant_id, "project_id": project_id, "is_current": True}
    if date_from or date_to:
        q["date"] = {}
        if date_from:
            q["date"]["$gte"] = date_from
        if date_to:
            q["date"]["$lte"] = date_to

    from collections import defaultdict
    counts: Dict[str, int] = defaultdict(int)
    labor = 0.0
    equipment = 0.0
    production_total = 0.0
    delay_hours = 0.0
    async for f in db[COLL_FACTS].find(q, {"_id": 0, "fact_type": 1, "payload": 1}):
        counts[f["fact_type"]] += 1
        p = f.get("payload") or {}
        if f["fact_type"] == "labor_fact":
            labor += float(p.get("hours") or 0)
        elif f["fact_type"] == "equipment_fact":
            equipment += float(p.get("hours_used") or 0)
        elif f["fact_type"] == "production_fact":
            production_total += float(p.get("quantity") or 0)
        elif f["fact_type"] == "delay_fact":
            delay_hours += float(p.get("duration_hours") or 0)

    return {
        "project_id": project_id,
        "date_from": date_from,
        "date_to": date_to,
        "fact_counts": dict(counts),
        "labor_hours": round(labor, 2),
        "equipment_hours": round(equipment, 2),
        "production_total": round(production_total, 3),
        "delay_hours": round(delay_hours, 2),
    }
