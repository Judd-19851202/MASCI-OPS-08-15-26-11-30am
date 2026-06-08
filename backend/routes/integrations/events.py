"""
Integration Center · events.py — placeholder read endpoints for
Motive driver-safety events + MaintainX work orders.

Reads accept Safety / HR / Admin tokens via the multi-role gate so the
respective portals can render integration-ready cards TODAY without
any provider-specific auth knowledge.

Demo mode behaviour: when `integration_settings[provider].demo_mode`
is True, GET endpoints stitch in static demo records at the top of the
list so admins can take screenshots / show stakeholders what the
populated UI will look like once the API is wired.
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends

from ._storage import demo_motive_events, demo_maintainx_work_orders


async def _provider_demo_mode(db, provider: str) -> bool:
    doc = await db.integration_settings.find_one(
        {"provider": provider}, {"_id": 0, "demo_mode": 1},
    )
    return bool((doc or {}).get("demo_mode"))


# P1-F · Decorator that maps stored Motive event rows to the consumer
# (IntegrationEventsCard) field shape. Reuse-first: no new fields are
# persisted; the join is done at read-time using the existing
# `asset_mappings` + `employee_mappings` collections already hydrated
# by the Motive sync.
_EVENT_TYPE_LABELS = {
    "vehicle_gps": "GPS Update",
    "vehicle_location_received": "GPS Update",
    "hard_braking": "Hard Braking",
    "speeding": "Speeding",
    "harsh_acceleration": "Harsh Acceleration",
    "harsh_cornering": "Harsh Cornering",
    "seatbelt_violation": "Seatbelt Violation",
}


async def _decorate_motive_event_rows(db, rows: list) -> list:
    # Bulk-fetch vehicle + driver context once per page
    vids = sorted({(r.get("vehicle_id") or "").strip() for r in rows if r.get("vehicle_id")})
    veh_by_id: dict = {}
    if vids:
        async for am in db.asset_mappings.find(
            {"provider": "motive", "motive.vehicle_id": {"$in": vids}},
            {"_id": 0, "motive.vehicle_id": 1, "motive.number": 1,
             "masci_unit_number": 1, "masci_equipment_id": 1},
        ):
            mv = am.get("motive") or {}
            veh_by_id[(mv.get("vehicle_id") or "")] = {
                "unit_number": am.get("masci_unit_number") or mv.get("number") or "",
                "masci_equipment_id": am.get("masci_equipment_id") or "",
            }
        driver_by_vid: dict = {}
        async for em in db.employee_mappings.find(
            {"provider": "motive", "motive.current_vehicle_id": {"$in": vids}},
            {"_id": 0, "motive.current_vehicle_id": 1,
             "motive.first_name": 1, "motive.last_name": 1,
             "masci_employee_name": 1},
        ):
            mv = em.get("motive") or {}
            cv = mv.get("current_vehicle_id")
            if cv:
                driver_by_vid[str(cv)] = em.get("masci_employee_name") or " ".join(
                    filter(None, [mv.get("first_name"), mv.get("last_name")])
                ).strip()
    else:
        driver_by_vid = {}

    decorated = []
    for r in rows:
        vid = (r.get("vehicle_id") or "").strip()
        ctx = veh_by_id.get(vid, {})
        skph = r.get("speed_kph")
        skph_num = skph if isinstance(skph, (int, float)) else None
        kind = r.get("event_kind") or r.get("event_type") or ""
        city = r.get("city") or ""
        state = r.get("state") or ""
        addr = (((r.get("raw") or {}).get("current_location") or {}).get("current_location")
                or ", ".join(p for p in [city, state] if p)
                or "")
        decorated.append({
            **r,
            "event_type": kind,
            "event_type_label": _EVENT_TYPE_LABELS.get(kind, kind.replace("_", " ").title()),
            "severity": r.get("severity") or ("info" if kind in ("vehicle_gps", "vehicle_location_received") else "medium"),
            "driver_name": driver_by_vid.get(vid, ""),
            "unit_number": ctx.get("unit_number", ""),
            "masci_equipment_id": ctx.get("masci_equipment_id", ""),
            "speed_mph": round(skph_num * 0.621371, 1) if skph_num is not None else None,
            "location": {"address": addr, "lat": r.get("lat"), "lon": r.get("lon")},
            "coaching_required": bool(r.get("coaching_required")),
        })
    return decorated


def register_event_routes(
    api_router: APIRouter, db, require_safety_or_hr_or_admin,
) -> None:

    @api_router.get(
        "/integrations/motive/events",
        dependencies=[Depends(require_safety_or_hr_or_admin)],
    )
    async def list_motive_events(
        limit: int = 50,
        severity: Optional[str] = None,
        coaching_only: bool = False,
    ):
        q: dict = {"is_demo": {"$ne": True}}
        if severity:
            q["severity"] = severity
        if coaching_only:
            q["coaching_required"] = True
        limit = max(1, min(limit, 500))
        real = await db.motive_events.find(q, {"_id": 0}).sort("event_at", -1).to_list(limit)

        # P1-F · Bridge stored Motive event shape → consumer card shape.
        # `IntegrationEventsCard.MotiveRow` expects:
        #   event_type · severity · driver_name · unit_number · location.address · speed_mph
        # Stored vehicle_gps rows carry: event_kind · vehicle_id (numeric)
        # · lat/lon · speed_kph · city · state. Map them in-place so
        # rows render instead of blank.
        if real:
            real = await _decorate_motive_event_rows(db, real)

        if await _provider_demo_mode(db, "motive"):
            demo = demo_motive_events()
            if severity:
                demo = [d for d in demo if d.get("severity") == severity]
            if coaching_only:
                demo = [d for d in demo if d.get("coaching_required")]
            return demo + real
        return real

    @api_router.get(
        "/integrations/maintainx/work-orders",
        dependencies=[Depends(require_safety_or_hr_or_admin)],
    )
    async def list_maintainx_work_orders(
        status: Optional[str] = None,
        priority: Optional[str] = None,
        safety_only: bool = False,
        equipment_down_only: bool = False,
        limit: int = 50,
    ):
        q: dict = {"is_demo": {"$ne": True}}
        if status:
            q["status"] = status
        if priority:
            q["priority"] = priority
        if safety_only:
            q["safety_related"] = True
        if equipment_down_only:
            q["equipment_down"] = True
        limit = max(1, min(limit, 500))
        real = await db.maintainx_work_orders.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)
        if await _provider_demo_mode(db, "maintainx"):
            demo = demo_maintainx_work_orders()
            if status:
                demo = [d for d in demo if d.get("status") == status]
            if priority:
                demo = [d for d in demo if d.get("priority") == priority]
            if safety_only:
                demo = [d for d in demo if d.get("safety_related")]
            if equipment_down_only:
                demo = [d for d in demo if d.get("equipment_down")]
            return demo + real
        return real

    # P1-G · Motive geofence visibility
    # Returns the 67 ingested geofences enriched with two cheap joins
    # already in Mongo: "linked assets" (count of `asset_mappings.motive.lat/lon`
    # currently inside the polygon — point-in-polygon ray-cast) and
    # "last activity" (max event_at across `motive_events` for vehicles
    # currently inside). NO new collection.
    @api_router.get(
        "/integrations/motive/geofences",
        dependencies=[Depends(require_safety_or_hr_or_admin)],
    )
    async def list_motive_geofences(
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 200,
    ):
        q: dict = {}
        if status:
            q["status"] = status
        if category:
            q["category"] = category
        limit = max(1, min(limit, 500))
        rows = await db.motive_geofences.find(q, {"_id": 0}).sort("name", 1).to_list(limit)

        # Build a small index of vehicle positions for point-in-polygon
        veh_pos = []
        async for am in db.asset_mappings.find(
            {"provider": "motive", "motive.lat": {"$ne": None}, "motive.lon": {"$ne": None}},
            {"_id": 0, "motive.lat": 1, "motive.lon": 1, "motive.vehicle_id": 1,
             "motive.number": 1, "motive.located_at": 1, "masci_unit_number": 1},
        ):
            mv = am.get("motive") or {}
            veh_pos.append({
                "vehicle_id": mv.get("vehicle_id") or "",
                "unit_number": am.get("masci_unit_number") or mv.get("number") or "",
                "lat": mv.get("lat"),
                "lon": mv.get("lon"),
                "located_at": mv.get("located_at"),
            })

        for g in rows:
            poly = g.get("location_points") or []
            inside = []
            if isinstance(poly, list) and len(poly) >= 3:
                pts = [(p.get("lon"), p.get("lat")) for p in poly if p.get("lat") is not None and p.get("lon") is not None]
                for v in veh_pos:
                    if v["lat"] is None or v["lon"] is None:
                        continue
                    if _point_in_polygon(v["lon"], v["lat"], pts):
                        inside.append({
                            "vehicle_id": v["vehicle_id"],
                            "unit_number": v["unit_number"],
                            "located_at": v["located_at"],
                        })
            g["linked_assets_count"] = len(inside)
            g["linked_assets"] = inside[:25]
            g["last_activity_at"] = max((v["located_at"] for v in inside if v["located_at"]), default=None)
        return rows


def _point_in_polygon(x: float, y: float, poly: list) -> bool:
    """Standard ray-cast. `poly` is a list of (lon, lat) tuples; (x, y)
    must be (lon, lat) too. Closes the polygon automatically."""
    n = len(poly)
    if n < 3:
        return False
    inside = False
    x0, y0 = poly[-1]
    for x1, y1 in poly:
        if ((y1 > y) != (y0 > y)) and (
            x < (x0 - x1) * (y - y1) / ((y0 - y1) or 1e-12) + x1
        ):
            inside = not inside
        x0, y0 = x1, y1
    return inside


__all__ = ["register_event_routes"]
