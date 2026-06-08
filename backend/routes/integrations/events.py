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
    "hard_brake": "Hard Braking",
    "hard_braking": "Hard Braking",
    "harsh_acceleration": "Harsh Acceleration",
    "harsh_cornering": "Harsh Cornering",
    "speeding": "Speeding",
    "seatbelt_violation": "Seatbelt Violation",
    "fault_code": "Engine Fault Code",
    "fault_code_closed": "Fault Resolved",
    "dvir_submitted": "DVIR Submitted",
    "dvir_updated": "DVIR Updated",
    "inspection_report_updated": "DVIR Updated",
    "dvir_defect": "DVIR · Defect",
    "dvir_out_of_service": "DVIR · OUT OF SERVICE",
    "dvir_signed": "DVIR · Mechanic Signed",
    "geofence_enter": "Arrived",
    "geofence_exit": "Departed",
    "asset_geofence_enter": "Asset Arrived",
    "asset_geofence_exit": "Asset Departed",
    "hos_violation": "HOS Violation",
    "hos_violation_created": "HOS Violation",
    "hos_violation_updated": "HOS Violation · Updated",
    "vehicle_gateway_disconnected": "Gateway Disconnected",
    "vehicle_gateway_disconnect_ended": "Gateway Restored",
    "gateway_disconnected": "Gateway Disconnected",
    "gateway_reconnected": "Gateway Restored",
    "ai_coach_recap_created": "AI Coach Recap",
    "ai_coach_recap": "AI Coach Recap",
}


def _humanize_event(row: dict, unit_number: str, driver_name: str) -> str:
    """P1.5-G · Operational-language summary for the 5 authorized
    families. NEVER renders raw JSON."""
    fam = row.get("event_family") or ""
    truck = unit_number or row.get("vehicle_id") or "Unknown vehicle"
    drv = driver_name or "Unknown driver"
    if fam == "harsh_event":
        h = row.get("harsh") or {}
        sub = (h.get("subtype") or row.get("event_kind") or "harsh event").replace("_", " ").title()
        spd = h.get("speed_mph")
        spd_str = f" at {spd} mph" if isinstance(spd, (int, float)) else ""
        addr = row.get("address") or ", ".join(p for p in [row.get("city"), row.get("state")] if p)
        return f"{sub}: {drv} in {truck}{spd_str}" + (f" near {addr}" if addr else "")
    if fam == "fault_code":
        f = row.get("fault") or {}
        code = f.get("dtc_code") or "DTC"
        desc = f.get("description") or ""
        mil = " · CHECK-ENGINE ON" if f.get("mil_status") else ""
        return f"Fault {code} on {truck}{mil}" + (f" — {desc}" if desc else "")
    if fam == "dvir":
        d = row.get("dvir") or {}
        if d.get("out_of_service"):
            return f"OUT OF SERVICE: {drv} flagged {truck} ({d.get('defect_count', 0)} defect{'s' if d.get('defect_count', 0) != 1 else ''})"
        if d.get("defect_count", 0) > 0:
            return f"DVIR defect: {drv} flagged {truck} with {d.get('defect_count')} item{'s' if d.get('defect_count') != 1 else ''}"
        if d.get("status") == "signed":
            return f"DVIR signed: {d.get('mechanic_signed_by') or 'Mechanic'} cleared {truck}"
        return f"DVIR submitted: {drv} on {truck}"
    if fam == "geofence_enter":
        g = row.get("geofence") or {}
        site = g.get("name") or "geofence"
        return f"{truck} arrived at {site}" + (f" · {drv}" if drv != "Unknown driver" else "")
    if fam == "geofence_exit":
        g = row.get("geofence") or {}
        site = g.get("name") or "geofence"
        dwell = g.get("dwell_seconds")
        dwell_str = ""
        if isinstance(dwell, (int, float)) and dwell > 0:
            h_, m_ = divmod(int(dwell // 60), 60)
            dwell_str = f" · {h_} h {m_} m on site" if h_ else f" · {m_} m on site"
        return f"{truck} departed {site}{dwell_str}"
    # P1.6 · Asset geofence transitions (construction equipment)
    if fam == "asset_geofence_enter":
        g = row.get("geofence") or {}
        a = row.get("asset") or {}
        name = a.get("name") or truck
        site = g.get("name") or "geofence"
        batt = a.get("battery_level")
        batt_str = f" · battery {batt}%" if isinstance(batt, (int, float)) else ""
        return f"{name} arrived at {site}{batt_str}"
    if fam == "asset_geofence_exit":
        g = row.get("geofence") or {}
        a = row.get("asset") or {}
        name = a.get("name") or truck
        site = g.get("name") or "geofence"
        dwell = g.get("dwell_seconds")
        dwell_str = ""
        if isinstance(dwell, (int, float)) and dwell > 0:
            h_, m_ = divmod(int(dwell // 60), 60)
            dwell_str = f" · {h_} h {m_} m on site" if h_ else f" · {m_} m on site"
        return f"{name} departed {site}{dwell_str}"
    # P1.6 · HOS violation
    if fam == "hos_violation":
        h = row.get("hos") or {}
        vt = (h.get("violation_type") or "HOS").replace("_", " ")
        dname = h.get("driver_name") or drv
        over = h.get("exceeded_by_minutes")
        over_str = f" · exceeded by {over} min" if isinstance(over, (int, float)) else ""
        upd = " (updated)" if h.get("is_update") else ""
        return f"{vt} violation: {dname} on {truck}{over_str}{upd}"
    # P1.6 · Vehicle gateway disconnected / reconnected
    if fam == "gateway_disconnected":
        gw = row.get("gateway") or {}
        addr = gw.get("last_known_address") or row.get("address") or ""
        last = (gw.get("last_reported_at") or "")[:16].replace("T", " ")
        last_str = f" · last reported {last}" if last else ""
        addr_str = f" from {addr}" if addr else ""
        return f"Gateway disconnected on {truck}{last_str}{addr_str}"
    if fam == "gateway_reconnected":
        gw = row.get("gateway") or {}
        off = gw.get("offline_duration_seconds")
        off_str = ""
        if isinstance(off, (int, float)) and off > 0:
            h_, m_ = divmod(int(off // 60), 60)
            off_str = f" · offline for {h_} h {m_} m" if h_ else f" · offline for {m_} m"
        return f"Gateway restored on {truck}{off_str}"
    # P1.6 · AI Coach recap
    if fam == "ai_coach_recap":
        ai = row.get("ai_coach") or {}
        dname = ai.get("driver_name") or drv
        score = ai.get("score")
        delta = ai.get("score_delta")
        trend = ai.get("trend") or ""
        score_str = f" · score {score}/100" if score is not None else ""
        delta_str = ""
        if isinstance(delta, (int, float)) and delta != 0:
            delta_str = f" ({'+' if delta > 0 else ''}{delta})"
        trend_str = f" · {trend}" if trend else ""
        return f"AI Coach recap for {dname}{score_str}{delta_str}{trend_str}"
    # P1.6 · Fault code resolved
    if fam == "fault_code_closed":
        f = row.get("fault") or {}
        code = f.get("dtc_code") or "DTC"
        dur = f.get("duration_seconds")
        dur_str = ""
        if isinstance(dur, (int, float)) and dur > 0:
            h_, m_ = divmod(int(dur // 60), 60)
            dur_str = f" after {h_} h {m_} m" if h_ else f" after {m_} m"
        return f"Fault {code} resolved on {truck}{dur_str}"
    # vehicle_gps + other → fall back to coarse label
    return _EVENT_TYPE_LABELS.get(row.get("event_kind") or "", "Motive event")


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
            "priority": r.get("priority") or "low",
            "driver_name": driver_by_vid.get(vid, "") or (r.get("hos") or {}).get("driver_name") or (r.get("ai_coach") or {}).get("driver_name") or "",
            "unit_number": ctx.get("unit_number", ""),
            "masci_equipment_id": ctx.get("masci_equipment_id", ""),
            "speed_mph": round(skph_num * 0.621371, 1) if skph_num is not None else None,
            "location": {"address": addr, "lat": r.get("lat"), "lon": r.get("lon")},
            "coaching_required": bool((r.get("harsh") or {}).get("coaching_required") or r.get("coaching_required")),
            "notify": _needs_notification(r),
            "summary": _humanize_event(r, ctx.get("unit_number", ""), driver_by_vid.get(vid, "") or (r.get("hos") or {}).get("driver_name") or ""),
        })
    return decorated


def _needs_notification(row: dict) -> bool:
    """P1.6 · Conservative gate for the Notifications bell. Bell fires
    ONLY for: HOS violations · gateway_disconnected · DVIR critical
    (OOS) · high-severity harsh events · red fault codes. Everything
    else flows through the timeline silently — no notification storm."""
    fam = row.get("event_family") or ""
    sev = (row.get("severity") or "").lower()
    if fam == "hos_violation":
        return True
    if fam == "gateway_disconnected":
        return True
    if fam == "dvir" and sev == "critical":
        return True
    if fam == "fault_code" and sev == "critical":
        return True
    if fam == "harsh_event" and sev in ("high", "critical"):
        return True
    if fam == "ai_coach_recap":
        # Only when the recap signals adverse trend
        ai = row.get("ai_coach") or {}
        if (ai.get("trend") or "").lower() in ("declining", "worsening", "negative") or (
            isinstance(ai.get("score_delta"), (int, float)) and ai.get("score_delta") <= -10
        ):
            return True
    return False


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
        family: Optional[str] = None,
        coaching_only: bool = False,
    ):
        q: dict = {"is_demo": {"$ne": True}}
        if severity:
            q["severity"] = severity
        if family:
            q["event_family"] = family
        if coaching_only:
            q["$or"] = [{"coaching_required": True}, {"harsh.coaching_required": True}]
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
            if family:
                # Demo rows pre-date P1.5 family taxonomy — only show
                # them when no family filter is applied. Family-scoped
                # views must always be real data.
                demo = []
            return demo + real
        return real

    # P1.5-H · Per-asset event history (Asset Profile → Events tab)
    # Filters by the MASCI equipment id → resolves to motive vehicle_id
    # via existing asset_mappings, then reads motive_events.
    @api_router.get(
        "/integrations/motive/assets/{masci_equipment_id}/events",
        dependencies=[Depends(require_safety_or_hr_or_admin)],
    )
    async def asset_motive_events(masci_equipment_id: str, limit: int = 50):
        mapping = await db.asset_mappings.find_one(
            {"masci_equipment_id": masci_equipment_id},
            {"_id": 0, "motive.vehicle_id": 1, "motive.asset_id": 1},
        )
        if not mapping:
            return []
        mv = mapping.get("motive") or {}
        vid = (mv.get("vehicle_id") or "").strip()
        aid = (mv.get("asset_id") or "").strip()
        if not vid and not aid:
            return []
        q: dict = {"is_demo": {"$ne": True}}
        if vid and aid:
            q["$or"] = [{"vehicle_id": vid}, {"raw.asset.id": aid}, {"raw.asset.id": int(aid) if aid.isdigit() else aid}]
        elif vid:
            q["vehicle_id"] = vid
        else:
            q["$or"] = [{"raw.asset.id": aid}, {"raw.asset.id": int(aid) if aid.isdigit() else aid}]
        limit = max(1, min(limit, 200))
        rows = await db.motive_events.find(q, {"_id": 0}).sort("event_at", -1).to_list(limit)
        if rows:
            rows = await _decorate_motive_event_rows(db, rows)
        return rows

    # P1.5-H · Per-driver event history (when MASCI Driver Profile screen exists)
    @api_router.get(
        "/integrations/motive/drivers/{masci_employee_id}/events",
        dependencies=[Depends(require_safety_or_hr_or_admin)],
    )
    async def driver_motive_events(masci_employee_id: str, limit: int = 50):
        mapping = await db.employee_mappings.find_one(
            {"masci_employee_id": masci_employee_id},
            {"_id": 0, "motive.driver_id": 1},
        )
        if not mapping:
            return []
        did = ((mapping.get("motive") or {}).get("driver_id") or "").strip()
        if not did:
            return []
        q = {"is_demo": {"$ne": True}, "$or": [
            {"driver_id": did},
            {"raw.driver.id": did},
            {"raw.driver.id": int(did) if did.isdigit() else did},
        ]}
        limit = max(1, min(limit, 200))
        rows = await db.motive_events.find(q, {"_id": 0}).sort("event_at", -1).to_list(limit)
        if rows:
            rows = await _decorate_motive_event_rows(db, rows)
        return rows

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
