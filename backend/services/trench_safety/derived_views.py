"""TRACK 23.10-C · Derived (read-time) views over the 7 physical facts.

Per user directive 2B — these four "companion" views are NOT emitted as
new fact_types. They are computed at read time so consumers of ODS
don't need to reason about extra source-of-truth surfaces.

* `deployment_view`             — active + historical deployment windows
                                  from `db.trench_safety_deployments`,
                                  passed through the project linker for
                                  consistency; NEVER a separate fact.
* `trench_asset_utilization`    — days-in-use per asset per project,
                                  computed from deployment windows.
* `trench_release_view`         — the moment a repair became
                                  `safe_to_use_verified` OR a hold was
                                  cleared — derived from
                                  `trench_verification_fact` and
                                  `trench_hold_fact.cleared_at`.
* `excavation_activity_view`    — per-project rolling window of the
                                  physical facts — used by PM /
                                  Safety Portal readiness surfaces.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.ods_spine.store import COLL_FACTS
from .facts_emitter import SOURCE_TYPE_TRENCH
from .project_linker import resolve_project


async def deployment_view(
    db, project_number: Optional[str] = None,
    asset_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Deployments as authoritative rows — filter by project + asset."""
    q: Dict[str, Any] = {}
    if project_number:
        q["$or"] = [
            {"project_number": str(project_number)},
            {"project_id": str(project_number)},
        ]
    if asset_id:
        q["$and"] = q.get("$and", []) + [{"$or": [
            {"asset_id": asset_id}, {"asset_uuid": asset_id},
        ]}]
    cursor = db.trench_safety_deployments.find(q, {"_id": 0}).sort(
        "assigned_at", -1,
    )
    return await cursor.to_list(2000)


async def trench_asset_utilization(
    db, project_number: str,
) -> List[Dict[str, Any]]:
    """Per-asset days-in-use for a given project.

    Computed live from deployments; no fact type needed.
    """
    if not project_number:
        return []
    depls = await deployment_view(db, project_number=project_number)
    now = datetime.now(timezone.utc)
    out: Dict[str, Dict[str, Any]] = {}
    for d in depls:
        aid = d.get("asset_id") or d.get("asset_uuid")
        if not aid:
            continue
        try:
            start = datetime.fromisoformat(
                (d.get("assigned_at") or "").replace("Z", "+00:00"),
            )
        except Exception:
            continue
        try:
            end = datetime.fromisoformat(
                (d.get("returned_at") or "").replace("Z", "+00:00"),
            ) if d.get("returned_at") else now
        except Exception:
            end = now
        days = max(0, (end - start).days + (1 if end.date() != start.date() else 0))
        rec = out.setdefault(aid, {
            "asset_id": aid,
            "asset_uuid": d.get("asset_uuid"),
            "project_number": project_number,
            "deployment_count": 0,
            "total_days_in_use": 0,
            "active": False,
            "last_assigned_at": None,
        })
        rec["deployment_count"] += 1
        rec["total_days_in_use"] += days
        if not d.get("returned_at"):
            rec["active"] = True
        if not rec["last_assigned_at"] or d.get("assigned_at", "") > rec["last_assigned_at"]:
            rec["last_assigned_at"] = d.get("assigned_at")
    return sorted(out.values(), key=lambda r: (
        0 if r["active"] else 1, -r["total_days_in_use"],
    ))


async def trench_release_view(
    db, project_number: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """Release events derived from:
        * `trench_verification_fact` (repair → safe_to_use_verified),
        * `trench_hold_fact` with `cleared_at IS NOT NULL`.
    """
    events: List[Dict[str, Any]] = []
    q_base = {
        "source_type": SOURCE_TYPE_TRENCH,
        "source_id": "trench_safety",
        "is_current": True,
    }
    if project_number:
        q_base["project_id"] = str(project_number)

    cursor = db[COLL_FACTS].find(
        {**q_base, "fact_type": "trench_verification_fact"},
        {"_id": 0},
    )
    async for f in cursor:
        pl = f.get("payload") or {}
        events.append({
            "kind": "repair_safe_to_use",
            "at": pl.get("verified_at") or f.get("date"),
            "asset_id": pl.get("asset_id"),
            "repair_id": pl.get("repair_id"),
            "project_number": (pl.get("linkage") or {}).get("project_number"),
            "source_fact_id": f.get("fact_id"),
        })

    cursor = db[COLL_FACTS].find(
        {**q_base, "fact_type": "trench_hold_fact",
         "payload.cleared_at": {"$ne": None}},
        {"_id": 0},
    )
    async for f in cursor:
        pl = f.get("payload") or {}
        events.append({
            "kind": "hold_cleared",
            "at": pl.get("cleared_at") or f.get("date"),
            "asset_id": pl.get("asset_id"),
            "hold_id": pl.get("hold_id"),
            "hold_kind": pl.get("kind"),
            "project_number": (pl.get("linkage") or {}).get("project_number"),
            "source_fact_id": f.get("fact_id"),
        })

    events.sort(key=lambda e: e.get("at") or "", reverse=True)
    return events[:limit]


async def excavation_activity_view(
    db, project_number: str,
    since_date: Optional[str] = None, until_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Rolling per-day excavation activity for a project — used by the
    PM operational-intelligence surface + Safety Portal readiness card.
    """
    if not project_number:
        return {"project_number": None, "days": []}
    q = {
        "source_type": SOURCE_TYPE_TRENCH,
        "source_id": "trench_safety",
        "project_id": str(project_number),
        "fact_type": "excavation_day_fact",
        "is_current": True,
    }
    if since_date or until_date:
        clause: Dict[str, str] = {}
        if since_date:
            clause["$gte"] = since_date[:10]
        if until_date:
            clause["$lte"] = until_date[:10]
        q["date"] = clause
    days: Dict[str, Dict[str, Any]] = {}
    cursor = db[COLL_FACTS].find(q, {"_id": 0})
    async for f in cursor:
        pl = f.get("payload") or {}
        d = f.get("date", "")
        rec = days.setdefault(d, {
            "date": d, "excavation_count": 0, "inspections_completed": 0,
            "holds_issued": 0, "max_depth_ft": 0.0,
            "protective_systems": [],
        })
        rec["excavation_count"] += 1
        if pl.get("inspection_completed"):
            rec["inspections_completed"] += 1
        if pl.get("hold_issued"):
            rec["holds_issued"] += 1
        try:
            md = float(pl.get("max_depth_ft") or 0)
            if md > rec["max_depth_ft"]:
                rec["max_depth_ft"] = md
        except (TypeError, ValueError):
            pass
        ps = pl.get("protective_system")
        if ps and ps not in rec["protective_systems"]:
            rec["protective_systems"].append(ps)
    return {
        "project_number": project_number,
        "days": sorted(days.values(), key=lambda r: r["date"]),
    }
