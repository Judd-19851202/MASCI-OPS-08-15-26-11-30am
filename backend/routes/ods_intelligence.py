"""DR-ROI-001E · PM / Admin / Executive Operational Intelligence routes.

Additive `/api/ods/pm/*`, `/api/ods/admin/*`, `/api/ods/executive/*` read
surface. Reads snapshots + operational_facts only. Never mutates source
records. Uses AI Gateway `pm_brief` / `executive_brief` tasks — provider
neutral. No model/provider names leak to callers by default.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from services.ai_gateway import get_gateway
from services.ai_gateway.env import gateway_enabled
from services.ods_spine import ods_enabled

from services.ods_spine.store import COLL_FACTS, COLL_SNAPSHOTS


TENANT_DEFAULT = "masci"


def _preset_to_range(preset: str) -> tuple[str, str]:
    """Map preset to (date_from, date_to) YYYY-MM-DD inclusive."""
    today = datetime.now(timezone.utc).date()
    if preset == "today":
        return today.isoformat(), today.isoformat()
    if preset == "yesterday":
        y = today - timedelta(days=1)
        return y.isoformat(), y.isoformat()
    if preset == "this_week":
        start = today - timedelta(days=today.weekday())
        return start.isoformat(), today.isoformat()
    if preset == "last_week":
        end = today - timedelta(days=today.weekday() + 1)
        start = end - timedelta(days=6)
        return start.isoformat(), end.isoformat()
    if preset == "month":
        start = today.replace(day=1)
        return start.isoformat(), today.isoformat()
    if preset == "last_month":
        first_this = today.replace(day=1)
        end = first_this - timedelta(days=1)
        start = end.replace(day=1)
        return start.isoformat(), end.isoformat()
    if preset == "quarter":
        q = (today.month - 1) // 3
        start = today.replace(month=q * 3 + 1, day=1)
        return start.isoformat(), today.isoformat()
    if preset == "year":
        start = today.replace(month=1, day=1)
        return start.isoformat(), today.isoformat()
    return today.isoformat(), today.isoformat()


def _resolve_range(preset: Optional[str], date_from: Optional[str], date_to: Optional[str]) -> tuple[str, str]:
    if preset and preset != "custom":
        return _preset_to_range(preset)
    return (date_from or ""), (date_to or "")


async def _aggregate_snapshots(
    db, *, project_ids: Optional[List[str]], date_from: str, date_to: str,
) -> Dict[str, Any]:
    """Read pre-computed snapshots (cheap) and aggregate."""
    q: Dict[str, Any] = {"tenant_id": TENANT_DEFAULT, "window": "day"}
    if project_ids is not None:
        q["project_id"] = {"$in": project_ids}
    if date_from or date_to:
        q["date"] = {}
        if date_from:
            q["date"]["$gte"] = date_from
        if date_to:
            q["date"]["$lte"] = date_to

    labor = 0.0
    equipment = 0.0
    prod_by_code: Dict[str, float] = {}
    delay_by_cat: Dict[str, float] = {}
    loads_in = 0
    loads_out = 0
    safety = 0
    quality = 0
    photos = 0
    blockers = 0
    projects_seen = set()
    async for s in db[COLL_SNAPSHOTS].find(q, {"_id": 0}):
        labor += s.get("labor_hours") or 0
        equipment += s.get("equipment_hours") or 0
        for k, v in (s.get("production_by_cost_code") or {}).items():
            prod_by_code[k] = prod_by_code.get(k, 0.0) + float(v or 0)
        for k, v in (s.get("delay_hours_by_category") or {}).items():
            delay_by_cat[k] = delay_by_cat.get(k, 0.0) + float(v or 0)
        loads_in += int((s.get("material_loads") or {}).get("in") or 0)
        loads_out += int((s.get("material_loads") or {}).get("out") or 0)
        safety += int(s.get("safety_flag_count") or 0)
        quality += int(s.get("quality_flag_count") or 0)
        photos += int(s.get("photo_count") or 0)
        blockers += int(s.get("readiness_blocker_count") or 0)
        projects_seen.add(s.get("project_id"))
    return {
        "labor_hours": round(labor, 2),
        "equipment_hours": round(equipment, 2),
        "production_by_cost_code": {k: round(v, 3) for k, v in prod_by_code.items()},
        "delay_hours_by_category": {k: round(v, 2) for k, v in delay_by_cat.items()},
        "material_loads": {"in": loads_in, "out": loads_out},
        "safety_flag_count": safety,
        "quality_flag_count": quality,
        "photo_count": photos,
        "readiness_blocker_count": blockers,
        "projects_included": sorted(x for x in projects_seen if x),
        "date_from": date_from, "date_to": date_to,
    }


async def _project_health_rows(
    db, *, project_ids: Optional[List[str]], date_from: str, date_to: str,
) -> List[Dict[str, Any]]:
    """One row per project for the health table."""
    q: Dict[str, Any] = {"tenant_id": TENANT_DEFAULT, "window": "day"}
    if project_ids is not None:
        q["project_id"] = {"$in": project_ids}
    if date_from or date_to:
        q["date"] = {}
        if date_from:
            q["date"]["$gte"] = date_from
        if date_to:
            q["date"]["$lte"] = date_to
    per: Dict[str, Dict[str, Any]] = {}
    async for s in db[COLL_SNAPSHOTS].find(q, {"_id": 0}):
        pid = s.get("project_id") or ""
        r = per.setdefault(pid, {"project_id": pid, "labor_hours": 0.0, "equipment_hours": 0.0,
                                 "delay_hours": 0.0, "safety_flag_count": 0, "readiness_blocker_count": 0,
                                 "days_reported": 0})
        r["labor_hours"] += s.get("labor_hours") or 0
        r["equipment_hours"] += s.get("equipment_hours") or 0
        r["delay_hours"] += sum((s.get("delay_hours_by_category") or {}).values())
        r["safety_flag_count"] += int(s.get("safety_flag_count") or 0)
        r["readiness_blocker_count"] += int(s.get("readiness_blocker_count") or 0)
        r["days_reported"] += 1
    return sorted(per.values(), key=lambda r: (-r["delay_hours"], -r["safety_flag_count"]))


def _brief_evidence_hash(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


_BRIEFS_COLL = "ods_briefs_cache"


async def _brief_via_gateway(
    db, *, task: str, audience: str, payload: Dict[str, Any], session_id: str,
) -> Dict[str, Any]:
    """Cache-first PM/Executive brief. Every response is confidence-scored."""
    ehash = _brief_evidence_hash(payload)
    cached = await db[_BRIEFS_COLL].find_one(
        {"audience": audience, "evidence_hash": ehash}, {"_id": 0},
    )
    if cached and cached.get("brief"):
        return {"cached": True, "brief": cached["brief"]}

    gw = get_gateway()
    system = (
        "You are an operational intelligence writer for construction "
        "project managers and executives. Never invent numbers. Cite "
        "which snapshot/facts you used. Return STRICT JSON with keys: "
        "narrative, confidence, evidence_refs, sources_used, uncertainties."
    )
    schema = {
        "type": "object",
        "required": ["narrative", "confidence", "evidence_refs", "sources_used"],
        "properties": {
            "narrative": {"type": "string"}, "confidence": {"type": "number"},
            "evidence_refs": {"type": "array"}, "sources_used": {"type": "array"},
            "uncertainties": {"type": "array"},
        },
    }

    env = await gw.dispatch(
        task=task, system=system, user_payload=payload,
        response_schema=schema, session_id=session_id,
    )
    brief = {
        "audience": audience,
        "narrative": env.narrative, "confidence": env.confidence,
        "evidence_refs": env.evidence_refs, "sources_used": env.sources_used,
        "uncertainties": env.uncertainties,
        "ai_available": env.ai_available,
        "generated_at": env.generated_at,
    }
    if env.ai_available:
        await db[_BRIEFS_COLL].update_one(
            {"audience": audience, "evidence_hash": ehash},
            {"$set": {"audience": audience, "evidence_hash": ehash,
                      "brief": brief, "cached_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
    return {"cached": False, "brief": brief}


def register_ods_intelligence_routes(api_router: APIRouter, db) -> None:

    # ----- PM: project intelligence -----------------------------------
    @api_router.get("/ods/pm/projects/{project_id}/kpis")
    async def pm_project_kpis(
        project_id: str,
        preset: Optional[str] = Query(default="today"),
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not ods_enabled():
            return {"enabled": False, "kpis": None}
        df, dt = _resolve_range(preset, date_from, date_to)
        agg = await _aggregate_snapshots(
            db, project_ids=[project_id], date_from=df, date_to=dt,
        )
        return {"enabled": True, "project_id": project_id, "range": {"from": df, "to": dt, "preset": preset}, "kpis": agg}

    @api_router.get("/ods/pm/projects/{project_id}/intelligence")
    async def pm_project_intelligence(
        project_id: str,
        preset: Optional[str] = Query(default="today"),
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = Query(default=25, ge=1, le=200),
    ) -> Dict[str, Any]:
        if not ods_enabled():
            return {"enabled": False}
        df, dt = _resolve_range(preset, date_from, date_to)
        q: Dict[str, Any] = {"tenant_id": TENANT_DEFAULT, "project_id": project_id,
                             "is_current": True}
        if df or dt:
            q["date"] = {}
            if df: q["date"]["$gte"] = df
            if dt: q["date"]["$lte"] = dt
        cursor = db[COLL_FACTS].find(q, {"_id": 0}).sort([("date", -1)]).limit(limit)
        facts = [d async for d in cursor]
        by_type: Dict[str, int] = {}
        for f in facts:
            by_type[f["fact_type"]] = by_type.get(f["fact_type"], 0) + 1
        return {"enabled": True, "project_id": project_id,
                "range": {"from": df, "to": dt, "preset": preset},
                "fact_counts": by_type, "facts": facts}

    @api_router.get("/ods/pm/projects/{project_id}/brief")
    async def pm_project_brief(
        project_id: str,
        preset: Optional[str] = Query(default="today"),
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        df, dt = _resolve_range(preset, date_from, date_to)
        agg = await _aggregate_snapshots(db, project_ids=[project_id], date_from=df, date_to=dt)
        payload = {"role": "pm", "project_id": project_id,
                   "range": {"from": df, "to": dt}, "kpis": agg}
        result = await _brief_via_gateway(
            db, task="pm_brief", audience=f"pm:{project_id}",
            payload=payload, session_id=f"pm-{project_id}-{df}-{dt}",
        )
        return {"project_id": project_id, "range": {"from": df, "to": dt, "preset": preset}, **result}

    @api_router.get("/ods/pm/dashboard")
    async def pm_dashboard(
        project_ids: Optional[str] = Query(default=None, description="csv list"),
        preset: Optional[str] = Query(default="today"),
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        df, dt = _resolve_range(preset, date_from, date_to)
        pids = [p.strip() for p in (project_ids or "").split(",") if p.strip()] or None
        agg = await _aggregate_snapshots(db, project_ids=pids, date_from=df, date_to=dt)
        health = await _project_health_rows(db, project_ids=pids, date_from=df, date_to=dt)
        return {"enabled": ods_enabled(), "role": "pm",
                "range": {"from": df, "to": dt, "preset": preset},
                "kpis": agg, "projects": health}

    # ----- Admin: company-wide ----------------------------------------
    @api_router.get("/ods/admin/dashboard")
    async def admin_dashboard(
        preset: Optional[str] = Query(default="today"),
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        df, dt = _resolve_range(preset, date_from, date_to)
        agg = await _aggregate_snapshots(db, project_ids=None, date_from=df, date_to=dt)
        health = await _project_health_rows(db, project_ids=None, date_from=df, date_to=dt)
        return {"enabled": ods_enabled(), "role": "admin",
                "range": {"from": df, "to": dt, "preset": preset},
                "company_kpis": agg, "projects_health": health}

    @api_router.get("/ods/admin/delays")
    async def admin_delays(
        preset: Optional[str] = Query(default="month"),
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        df, dt = _resolve_range(preset, date_from, date_to)
        q: Dict[str, Any] = {"tenant_id": TENANT_DEFAULT, "fact_type": "delay_fact", "is_current": True}
        if df or dt:
            q["date"] = {}
            if df: q["date"]["$gte"] = df
            if dt: q["date"]["$lte"] = dt
        by_cat: Dict[str, Dict[str, Any]] = {}
        rows = []
        async for f in db[COLL_FACTS].find(q, {"_id": 0}):
            p = f.get("payload") or {}
            cat = p.get("delay_category") or "other"
            d = by_cat.setdefault(cat, {"category": cat, "hours": 0.0, "count": 0})
            d["hours"] += float(p.get("duration_hours") or 0)
            d["count"] += 1
            rows.append({"project_id": f.get("project_id"), "date": f.get("date"),
                         "category": cat, "hours": p.get("duration_hours"),
                         "reason": p.get("reason"), "impact": p.get("impact")})
        return {"range": {"from": df, "to": dt, "preset": preset},
                "by_category": sorted(by_cat.values(), key=lambda r: -r["hours"]),
                "delays": rows[:200]}

    # ----- Executive --------------------------------------------------
    @api_router.get("/ods/executive/brief")
    async def executive_brief(
        preset: Optional[str] = Query(default="month"),
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        df, dt = _resolve_range(preset, date_from, date_to)
        agg = await _aggregate_snapshots(db, project_ids=None, date_from=df, date_to=dt)
        health = await _project_health_rows(db, project_ids=None, date_from=df, date_to=dt)
        payload = {"role": "executive", "range": {"from": df, "to": dt},
                   "kpis": agg, "projects_health": health[:20]}
        result = await _brief_via_gateway(
            db, task="executive_brief", audience="executive",
            payload=payload, session_id=f"exec-{df}-{dt}",
        )
        return {"range": {"from": df, "to": dt, "preset": preset}, **result}

    @api_router.get("/ods/executive/health")
    async def executive_health(
        preset: Optional[str] = Query(default="month"),
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        df, dt = _resolve_range(preset, date_from, date_to)
        health = await _project_health_rows(db, project_ids=None, date_from=df, date_to=dt)
        return {"range": {"from": df, "to": dt, "preset": preset},
                "top_at_risk": health[:10], "total_projects": len(health)}

    # ----- Attention (What Needs Attention horizon) -------------------
    async def _attention_items(
        *, project_ids: Optional[List[str]], date_from: str, date_to: str, limit: int = 50,
    ) -> Dict[str, Any]:
        """Return concrete attention items with evidence traceability.

        Each row carries fact_id + source_type + source_id + date so the
        UI can jump back to the originating operational record. No AI
        reasoning here — this is deterministic fact projection.
        """
        q: Dict[str, Any] = {
            "tenant_id": TENANT_DEFAULT,
            "is_current": True,
            "fact_type": {"$in": ["safety_fact", "quality_fact",
                                  "delay_fact", "readiness_fact"]},
        }
        if project_ids is not None:
            q["project_id"] = {"$in": project_ids}
        if date_from or date_to:
            q["date"] = {}
            if date_from: q["date"]["$gte"] = date_from
            if date_to: q["date"]["$lte"] = date_to
        buckets: Dict[str, List[Dict[str, Any]]] = {
            "safety": [], "quality": [], "delay": [], "readiness": [],
        }
        counts = {"safety": 0, "quality": 0, "delay": 0, "readiness": 0}
        cursor = db[COLL_FACTS].find(q, {"_id": 0}).sort([("date", -1)]).limit(limit * 4)
        async for f in cursor:
            ft = f.get("fact_type") or ""
            key = ft.split("_", 1)[0]
            if key not in buckets:
                continue
            counts[key] += 1
            if len(buckets[key]) >= limit:
                continue
            p = f.get("payload") or {}
            buckets[key].append({
                "fact_id": f.get("fact_id"),
                "project_id": f.get("project_id"),
                "date": f.get("date"),
                "source_type": f.get("source_type"),
                "source_id": f.get("source_id"),
                "source_item_id": f.get("source_item_id"),
                "summary": (
                    p.get("description") or p.get("reason") or p.get("blocker")
                    or p.get("finding") or p.get("category") or ft
                ),
                "severity": p.get("severity") or p.get("impact") or "unknown",
                "category": p.get("category") or p.get("delay_category") or key,
            })
        total = sum(counts.values())
        return {"totals": counts, "total": total, "items": buckets}

    @api_router.get("/ods/admin/attention")
    async def admin_attention(
        preset: Optional[str] = Query(default="this_week"),
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = Query(default=25, ge=1, le=100),
    ) -> Dict[str, Any]:
        if not ods_enabled():
            return {"enabled": False, "items": {}}
        df, dt = _resolve_range(preset, date_from, date_to)
        result = await _attention_items(
            project_ids=None, date_from=df, date_to=dt, limit=limit,
        )
        return {"enabled": True, "role": "admin",
                "range": {"from": df, "to": dt, "preset": preset}, **result}

    @api_router.get("/ods/pm/projects/{project_id}/attention")
    async def pm_project_attention(
        project_id: str,
        preset: Optional[str] = Query(default="this_week"),
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = Query(default=25, ge=1, le=100),
    ) -> Dict[str, Any]:
        if not ods_enabled():
            return {"enabled": False, "items": {}}
        df, dt = _resolve_range(preset, date_from, date_to)
        result = await _attention_items(
            project_ids=[project_id], date_from=df, date_to=dt, limit=limit,
        )
        return {"enabled": True, "role": "pm", "project_id": project_id,
                "range": {"from": df, "to": dt, "preset": preset}, **result}

    @api_router.get("/ods/pm/attention")
    async def pm_attention(
        project_ids: Optional[str] = Query(default=None, description="csv list"),
        preset: Optional[str] = Query(default="this_week"),
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = Query(default=25, ge=1, le=100),
    ) -> Dict[str, Any]:
        if not ods_enabled():
            return {"enabled": False, "items": {}}
        df, dt = _resolve_range(preset, date_from, date_to)
        pids = [p.strip() for p in (project_ids or "").split(",") if p.strip()] or None
        result = await _attention_items(
            project_ids=pids, date_from=df, date_to=dt, limit=limit,
        )
        return {"enabled": True, "role": "pm",
                "range": {"from": df, "to": dt, "preset": preset}, **result}

