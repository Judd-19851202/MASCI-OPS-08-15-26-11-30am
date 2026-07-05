"""ODS-001 · KPI snapshot builder.

Precomputes daily/project rollups from `operational_facts`. Callers read
snapshots for fast dashboards; heavy aggregations never happen on hot
read paths.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from .model import now_iso
from .store import COLL_FACTS, COLL_SNAPSHOTS


async def compute_kpi_snapshot(
    db, *, tenant_id: str, project_id: str, date: str, window: str = "day",
    source_run_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Aggregate is_current facts for (project, date) into a snapshot."""
    q = {
        "tenant_id": tenant_id, "project_id": project_id,
        "date": date, "is_current": True,
    }
    labor_hours = 0.0
    equipment_hours = 0.0
    production_by_cost_code: Dict[str, float] = {}
    delay_hours_by_category: Dict[str, float] = {}
    loads_in = 0
    loads_out = 0
    safety_flag_count = 0
    quality_flag_count = 0
    photo_count = 0
    readiness_blocker_count = 0
    intelligence_approved = False

    async for f in db[COLL_FACTS].find(q, {"_id": 0}):
        p = f.get("payload") or {}
        t = f.get("fact_type")
        if t == "labor_fact":
            labor_hours += float(p.get("hours") or 0)
        elif t == "equipment_fact":
            equipment_hours += float(p.get("hours_used") or 0)
        elif t == "production_fact":
            code = p.get("cost_code") or p.get("activity") or "uncoded"
            production_by_cost_code[code] = production_by_cost_code.get(code, 0.0) + float(p.get("quantity") or 0)
        elif t == "delay_fact":
            cat = p.get("delay_category") or "other"
            delay_hours_by_category[cat] = delay_hours_by_category.get(cat, 0.0) + float(p.get("duration_hours") or 0)
        elif t == "material_fact":
            loads_in += int(p.get("loads_in") or 0)
            loads_out += int(p.get("loads_out") or 0)
        elif t == "safety_fact":
            safety_flag_count += 1
        elif t == "quality_fact":
            quality_flag_count += 1
        elif t == "photo_evidence_fact":
            photo_count += 1
        elif t == "readiness_fact":
            if (p.get("status") or "") in {"at_risk", "blocker"}:
                readiness_blocker_count += 1
        elif t == "intelligence_fact":
            intelligence_approved = True

    snapshot = {
        "snapshot_id": uuid.uuid4().hex,
        "tenant_id": tenant_id,
        "project_id": project_id,
        "date": date,
        "window": window,
        "labor_hours": round(labor_hours, 2),
        "equipment_hours": round(equipment_hours, 2),
        "production_by_cost_code": {k: round(v, 3) for k, v in production_by_cost_code.items()},
        "delay_hours_by_category": {k: round(v, 2) for k, v in delay_hours_by_category.items()},
        "material_loads": {"in": loads_in, "out": loads_out},
        "safety_flag_count": safety_flag_count,
        "quality_flag_count": quality_flag_count,
        "photo_count": photo_count,
        "readiness_blocker_count": readiness_blocker_count,
        "intelligence_approved": intelligence_approved,
        "computed_at": now_iso(),
        "source_run_ids": source_run_ids or [],
    }

    await db[COLL_SNAPSHOTS].update_one(
        {"tenant_id": tenant_id, "project_id": project_id, "date": date, "window": window},
        {"$set": snapshot},
        upsert=True,
    )
    return snapshot


async def get_snapshot(
    db, *, tenant_id: str, project_id: str, date: str, window: str = "day",
) -> Optional[Dict[str, Any]]:
    return await db[COLL_SNAPSHOTS].find_one(
        {"tenant_id": tenant_id, "project_id": project_id, "date": date, "window": window},
        {"_id": 0},
    )
