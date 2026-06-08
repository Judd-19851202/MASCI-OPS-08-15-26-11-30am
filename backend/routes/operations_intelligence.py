"""
OIS-1 · Operations Intelligence Aggregator (read-only)
=======================================================

Single-pane backend endpoint that aggregates already-classified Motive
data into role-specific intelligence payloads. NO new collections, NO
new event streams, NO workflow side-effects. Just joins.

Powers:
  • OIS-1E · Operations Center single-pane intelligence
  • OIS-1D · Shop operations panel
  • OIS-1F · GPS health bands (reusable across surfaces)

Exposed routes:
  GET  /api/operations/intelligence            — full single-pane payload
  GET  /api/operations/intelligence/shop       — shop-only slice
  GET  /api/operations/intelligence/fleet-gps  — per-asset GPS band map
  GET  /api/operations/intelligence/driver/{driver_id} — driver intel
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends


# OIS-1F · GPS health band thresholds (used everywhere)
GPS_GREEN_MAX_MIN = 30        # < 30 min  → green
GPS_AMBER_MAX_MIN = 24 * 60   # < 24 hr   → amber
                              # else      → red


def _gps_band(located_at: str | None) -> Dict[str, Any]:
    """Compute the green / amber / red band for a Motive located_at."""
    if not located_at:
        return {"band": "red", "minutes": None, "label": "Not Reporting"}
    try:
        ts = datetime.fromisoformat(located_at.replace("Z", "+00:00"))
        mins = int((datetime.now(timezone.utc) - ts).total_seconds() / 60)
        if mins < GPS_GREEN_MAX_MIN:
            return {"band": "green", "minutes": mins, "label": f"GPS Active · {mins} min ago"}
        if mins < GPS_AMBER_MAX_MIN:
            hrs = mins // 60
            return {"band": "amber", "minutes": mins, "label": f"GPS Stale · {hrs} hr ago"}
        days = mins // (60 * 24)
        return {"band": "red", "minutes": mins, "label": f"Not Reporting · {days}d"}
    except Exception:  # noqa: BLE001
        return {"band": "red", "minutes": None, "label": "Not Reporting"}


def register_operations_intelligence_routes(api_router: APIRouter, db, require_admin) -> None:

    @api_router.get(
        "/operations/intelligence",
        dependencies=[Depends(require_admin)],
    )
    async def operations_intelligence():
        """OIS-1E · Single-pane Operations Center payload.

        Each field is derived from already-synced Motive data plus
        already-classified motive_events. No external API calls. No
        automation. Pure read-side aggregation."""
        now = datetime.now(timezone.utc)
        cut_24h = (now - timedelta(hours=24)).isoformat()
        cut_7d = (now - timedelta(days=7)).isoformat()
        cut_30min = (now - timedelta(minutes=30)).isoformat()

        # Fleet-wide GPS rollups (OIS-1F · single source of truth)
        gps_total = await db.asset_mappings.count_documents(
            {"provider": "motive", "motive.gps_enabled": True}
        )
        moving = await db.asset_mappings.count_documents({
            "provider": "motive", "motive.gps_enabled": True,
            "motive.speed_kph": {"$gt": 5},
            "motive.located_at": {"$gte": cut_30min},
        })
        idle = await db.asset_mappings.count_documents({
            "provider": "motive", "motive.gps_enabled": True,
            "motive.speed_kph": {"$lte": 5},
            "motive.located_at": {"$gte": cut_30min},
        })
        not_reporting = await db.asset_mappings.count_documents({
            "provider": "motive", "motive.gps_enabled": True,
            "$or": [
                {"motive.located_at": {"$lt": cut_24h}},
                {"motive.located_at": None},
            ],
        })

        # Driver visibility
        drivers_active = await db.employee_mappings.count_documents(
            {"provider": "motive", "motive.status": "active"}
        )
        drivers_deact = await db.employee_mappings.count_documents(
            {"provider": "motive", "motive.status": "deactivated"}
        )
        hos_24h = await db.motive_events.count_documents(
            {"event_family": "hos_violation", "received_at": {"$gte": cut_24h}}
        )

        # Equipment health
        faults_open_24h = await db.motive_events.count_documents({
            "event_family": "fault_code", "severity": "critical",
            "received_at": {"$gte": cut_24h},
        })
        gateways_offline = await db.motive_events.count_documents({
            "event_family": "gateway_disconnected",
            "received_at": {"$gte": cut_24h},
        })
        dvir_critical = await db.motive_events.count_documents({
            "event_family": "dvir", "severity": "critical",
            "received_at": {"$gte": cut_24h},
        })

        # Safety
        safety_24h = await db.motive_events.count_documents({
            "event_family": "harsh_event",
            "severity": {"$in": ["high", "critical"]},
            "received_at": {"$gte": cut_24h},
        })

        # DSI-1D · Active dispatch context
        active_assignments = await db.dispatch_assignments.count_documents({
            "current_state": {"$nin": ["COMPLETE", "CANCELLED"]},
        })
        active_drivers_dispatch = len(await db.dispatch_assignments.distinct(
            "driver_id",
            {"current_state": {"$nin": ["COMPLETE", "CANCELLED"]},
             "driver_id": {"$nin": [None, ""]}},
        ))
        active_equipment_dispatch = len(await db.dispatch_assignments.distinct(
            "truck_id",
            {"current_state": {"$nin": ["COMPLETE", "CANCELLED"]},
             "truck_id": {"$nin": [None, ""]}},
        ))

        # Geofence presence (assets currently inside any geofence —
        # approximated by their last-known-position being inside a
        # geofence polygon · cheap heuristic via category counts of
        # last 24h enter events minus exit events)
        active_geo = await db.motive_events.count_documents({
            "event_family": {"$in": ["geofence_enter", "asset_geofence_enter"]},
            "received_at": {"$gte": cut_7d},
        })
        active_geo_exits = await db.motive_events.count_documents({
            "event_family": {"$in": ["geofence_exit", "asset_geofence_exit"]},
            "received_at": {"$gte": cut_7d},
        })

        # Recent Motive events for the executive feed (top 8 high-priority)
        recent = []
        async for r in db.motive_events.find({
            "priority": {"$in": ["critical", "high"]},
            "received_at": {"$gte": cut_7d},
            "is_demo": {"$ne": True},
        }, {"_id": 0}).sort("received_at", -1).limit(8):
            recent.append({
                "event_family": r.get("event_family"),
                "severity": r.get("severity"),
                "priority": r.get("priority"),
                "received_at": r.get("received_at"),
                "vehicle_id": r.get("vehicle_id"),
            })

        return {
            "as_of": now.isoformat(),
            "fleet": {
                "gps_total": gps_total,
                "moving": moving,
                "idle": idle,
                "not_reporting": not_reporting,
            },
            "drivers": {
                "active": drivers_active,
                "deactivated_in_motive": drivers_deact,
                "hos_violations_24h": hos_24h,
            },
            "equipment": {
                "critical_faults_open_24h": faults_open_24h,
                "gateways_offline_24h": gateways_offline,
                "dvir_critical_24h": dvir_critical,
            },
            "safety": {
                "high_severity_events_24h": safety_24h,
            },
            "dispatch": {
                "active_assignments": active_assignments,
                "active_drivers": active_drivers_dispatch,
                "active_equipment": active_equipment_dispatch,
            },
            "geofences": {
                "enters_7d": active_geo,
                "exits_7d": active_geo_exits,
                "net_inside_7d": max(0, active_geo - active_geo_exits),
            },
            "recent_high_priority": recent,
            "gps_band_thresholds": {
                "green_max_minutes": GPS_GREEN_MAX_MIN,
                "amber_max_minutes": GPS_AMBER_MAX_MIN,
            },
        }

    @api_router.get(
        "/operations/intelligence/shop",
        dependencies=[Depends(require_admin)],
    )
    async def shop_intelligence():
        """OIS-1D · Shop operations panel slice.

        Sorted by severity. Read-only. Each entry has the asset's
        unit_number / make_model for the existing Shop Hub list to
        render without further joins."""
        now = datetime.now(timezone.utc)
        cut_30d = (now - timedelta(days=30)).isoformat()

        # Critical faults (open) — newest first
        crit_faults: List[Dict[str, Any]] = []
        async for r in db.motive_events.find({
            "event_family": "fault_code", "severity": "critical",
            "received_at": {"$gte": cut_30d},
            "is_demo": {"$ne": True},
        }, {"_id": 0}).sort("received_at", -1).limit(50):
            crit_faults.append(r)

        # Gateway offline
        gw_off: List[Dict[str, Any]] = []
        async for r in db.motive_events.find({
            "event_family": "gateway_disconnected",
            "received_at": {"$gte": cut_30d},
            "is_demo": {"$ne": True},
        }, {"_id": 0}).sort("received_at", -1).limit(50):
            gw_off.append(r)

        # DVIR defects/OOS
        dvir_def: List[Dict[str, Any]] = []
        async for r in db.motive_events.find({
            "event_family": "dvir",
            "severity": {"$in": ["high", "critical"]},
            "received_at": {"$gte": cut_30d},
            "is_demo": {"$ne": True},
        }, {"_id": 0}).sort("received_at", -1).limit(50):
            dvir_def.append(r)

        # Recent fault closures
        fault_closed: List[Dict[str, Any]] = []
        async for r in db.motive_events.find({
            "event_family": "fault_code_closed",
            "received_at": {"$gte": cut_30d},
            "is_demo": {"$ne": True},
        }, {"_id": 0}).sort("received_at", -1).limit(50):
            fault_closed.append(r)

        # Equipment not reporting (>24h) · DSI-1E enriched
        # Pre-fetch active assigned operator per truck.
        driver_by_truck: Dict[str, Dict[str, str]] = {}
        async for a in db.dispatch_assignments.find(
            {"current_state": {"$nin": ["COMPLETE", "CANCELLED"]},
             "truck_id": {"$nin": [None, ""]}},
            {"_id": 0, "truck_id": 1, "driver_name": 1, "driver_id": 1},
        ).sort("last_transition_at", -1):
            key = str(a.get("truck_id") or "").strip().upper()
            if key and key not in driver_by_truck:
                driver_by_truck[key] = {
                    "driver_name": a.get("driver_name") or "",
                    "driver_id": a.get("driver_id") or "",
                }

        not_reporting: List[Dict[str, Any]] = []
        cut_24h = (now - timedelta(hours=24)).isoformat()
        async for am in db.asset_mappings.find({
            "provider": "motive", "motive.gps_enabled": True,
            "$or": [
                {"motive.located_at": {"$lt": cut_24h}},
                {"motive.located_at": None},
            ],
        }, {"_id": 0, "masci_equipment_id": 1, "masci_unit_number": 1,
            "motive.number": 1, "motive.located_at": 1,
            "motive.city": 1, "motive.state": 1,
            "motive.location_summary": 1}).limit(100):
            mv = am.get("motive") or {}
            unit = am.get("masci_unit_number") or mv.get("number") or ""
            asgn = driver_by_truck.get(str(unit).strip().upper())
            loc = mv.get("location_summary") or (
                f"{mv.get('city') or ''}{', ' if mv.get('city') and mv.get('state') else ''}{mv.get('state') or ''}".strip(", ")
            )
            not_reporting.append({
                "masci_equipment_id": am.get("masci_equipment_id") or "",
                "unit_number": unit,
                "last_seen": mv.get("located_at"),
                "band": _gps_band(mv.get("located_at"))["band"],
                "last_known_location": loc or None,
                "assigned_operator": (asgn or {}).get("driver_name") or None,
                "assigned_operator_id": (asgn or {}).get("driver_id") or None,
            })

        return {
            "as_of": now.isoformat(),
            "critical_faults_open": crit_faults,
            "gateway_offline": gw_off,
            "dvir_defects": dvir_def,
            "recent_fault_closures": fault_closed,
            "equipment_not_reporting": not_reporting,
            "counts": {
                "critical_faults_open": len(crit_faults),
                "gateway_offline": len(gw_off),
                "dvir_defects": len(dvir_def),
                "recent_fault_closures": len(fault_closed),
                "equipment_not_reporting": len(not_reporting),
            },
        }

    @api_router.get(
        "/operations/intelligence/fleet-gps",
        dependencies=[Depends(require_admin)],
    )
    async def fleet_gps_health():
        """OIS-1A · Per-asset GPS health band map (DSI-1A enriched).

        Powers DispatchBoard row badges + Equipment cards. Each row
        now also carries:
          - gateway_status  → "online" | "offline"
          - fault_status    → "normal"  | "critical"
          - dvir_status     → "pass"    | "needs_attention"
          - last_event      → {family, headline, severity, received_at}
          - assigned_driver → {employee_id, name} or null

        Read-only. No writes, no automation."""
        now_iso_ = datetime.now(timezone.utc).isoformat()
        cut_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        cut_72h = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()

        # Pre-build per-vehicle lookups via aggregation (only newest event
        # per family per vehicle in the last 72h).
        family_status: Dict[str, Dict[str, Dict[str, Any]]] = {
            "gateway_disconnected": {},
            "gateway_reconnected": {},
            "fault_code": {},
            "fault_code_closed": {},
            "dvir": {},
            "_any": {},
        }
        async for ev in db.motive_events.find(
            {
                "received_at": {"$gte": cut_72h},
                "is_demo": {"$ne": True},
                "vehicle_id": {"$nin": [None, ""]},
            },
            {"_id": 0, "vehicle_id": 1, "event_family": 1, "severity": 1,
             "received_at": 1, "headline": 1, "decorated_label": 1, "priority": 1},
        ).sort("received_at", -1):
            vid = str(ev.get("vehicle_id"))
            fam = ev.get("event_family") or ""
            if fam in family_status and vid not in family_status[fam]:
                family_status[fam][vid] = ev
            if vid not in family_status["_any"]:
                family_status["_any"][vid] = ev

        # Pre-build per-vehicle current driver lookup from dispatch
        # (most recent active assignment per truck).
        driver_by_truck: Dict[str, Dict[str, str]] = {}
        async for a in db.dispatch_assignments.find(
            {"current_state": {"$nin": ["COMPLETE", "CANCELLED"]},
             "truck_id": {"$nin": [None, ""]}},
            {"_id": 0, "truck_id": 1, "driver_id": 1, "driver_name": 1,
             "project_number": 1, "project_name": 1, "last_transition_at": 1},
        ).sort("last_transition_at", -1):
            key = str(a.get("truck_id") or "").strip().upper()
            if key and key not in driver_by_truck:
                driver_by_truck[key] = {
                    "employee_id": a.get("driver_id") or "",
                    "name": a.get("driver_name") or "",
                    "project_number": a.get("project_number") or "",
                    "project_name": a.get("project_name") or "",
                }

        rows: List[Dict[str, Any]] = []
        async for am in db.asset_mappings.find(
            {"provider": "motive"},
            {
                "_id": 0,
                "masci_equipment_id": 1,
                "masci_unit_number": 1,
                "motive.vehicle_id": 1,
                "motive.asset_id": 1,
                "motive.number": 1,
                "motive.located_at": 1,
                "motive.speed_kph": 1,
                "motive.gps_enabled": 1,
                "motive.location_summary": 1,
                "motive.city": 1,
                "motive.state": 1,
            },
        ):
            mv = am.get("motive") or {}
            located = mv.get("located_at")
            band = _gps_band(located)
            speed = mv.get("speed_kph")
            moving = isinstance(speed, (int, float)) and speed > 5 and band["band"] == "green"
            vid = str(mv.get("vehicle_id") or "")

            # Gateway: offline iff the latest event in 72h is disconnected
            gw_off_ev = family_status["gateway_disconnected"].get(vid)
            gw_on_ev = family_status["gateway_reconnected"].get(vid)
            gateway_status = "online"
            if gw_off_ev and (not gw_on_ev or gw_off_ev.get("received_at", "") > gw_on_ev.get("received_at", "")):
                gateway_status = "offline"

            # Fault: critical iff there's an open critical fault not since
            # closed.
            fault_open = family_status["fault_code"].get(vid)
            fault_closed_ev = family_status["fault_code_closed"].get(vid)
            fault_status = "normal"
            if fault_open and (fault_open.get("severity") == "critical") and \
                (not fault_closed_ev or fault_open.get("received_at", "") > fault_closed_ev.get("received_at", "")):
                fault_status = "critical"

            # DVIR: needs_attention iff the most recent DVIR in 72h has
            # severity high/critical.
            dvir_ev = family_status["dvir"].get(vid)
            dvir_status = "pass"
            if dvir_ev and dvir_ev.get("severity") in ("high", "critical"):
                dvir_status = "needs_attention"

            last_ev = family_status["_any"].get(vid)
            last_event = None
            if last_ev:
                last_event = {
                    "family": last_ev.get("event_family"),
                    "headline": last_ev.get("headline") or last_ev.get("decorated_label"),
                    "severity": last_ev.get("severity"),
                    "received_at": last_ev.get("received_at"),
                }

            unit = (am.get("masci_unit_number") or mv.get("number") or "").strip()
            key_up = unit.upper()
            asgn = driver_by_truck.get(key_up)

            rows.append({
                "masci_equipment_id": am.get("masci_equipment_id") or "",
                "unit_number": unit,
                "vehicle_id": vid,
                "asset_id": mv.get("asset_id") or "",
                "band": band["band"],
                "label": band["label"],
                "minutes": band["minutes"],
                "located_at": located,
                "location_summary": mv.get("location_summary") or
                    (f"{mv.get('city') or ''}{', ' if mv.get('city') and mv.get('state') else ''}{mv.get('state') or ''}".strip(", ") or ""),
                "speed_kph": speed,
                "moving": bool(moving),
                "gps_enabled": bool(mv.get("gps_enabled")),
                # DSI-1A · enriched per-asset intel
                "gateway_status": gateway_status,
                "fault_status": fault_status,
                "dvir_status": dvir_status,
                "last_event": last_event,
                "assigned_driver": asgn,
            })
        return {
            "as_of": now_iso_,
            "assets": rows,
            "count": len(rows),
            "gps_band_thresholds": {
                "green_max_minutes": GPS_GREEN_MAX_MIN,
                "amber_max_minutes": GPS_AMBER_MAX_MIN,
            },
        }

    @api_router.get(
        "/operations/intelligence/driver/{driver_key}",
        dependencies=[Depends(require_admin)],
    )
    async def driver_intel(driver_key: str):
        """OIS-1C · Driver Command profile intel.

        `driver_key` accepts either the Motive user_id or the linked
        masci_employee_id. Returns the driver mapping plus a 30-day
        rollup of HOS, harsh events, and DVIR linked to this driver
        via motive_events.driver_id."""
        now = datetime.now(timezone.utc)
        cut_30d = (now - timedelta(days=30)).isoformat()
        cut_24h = (now - timedelta(hours=24)).isoformat()

        # Resolve mapping (lookup by motive user_id OR masci_employee_id)
        mapping = await db.employee_mappings.find_one(
            {
                "provider": "motive",
                "$or": [
                    {"motive.user_id": driver_key},
                    {"motive.id": driver_key},
                    {"masci_employee_id": driver_key},
                ],
            },
            {"_id": 0},
        )

        motive_user_id = ""
        if mapping:
            mv = mapping.get("motive") or {}
            motive_user_id = str(mv.get("user_id") or mv.get("id") or "")

        # Build event lookup using all known driver identifiers
        driver_ids = [d for d in [driver_key, motive_user_id] if d]
        ev_match: Dict[str, Any] = {"received_at": {"$gte": cut_30d}}
        if driver_ids:
            ev_match["driver_id"] = {"$in": driver_ids}

        async def _count(family, cut=cut_30d, sev=None):
            q = dict(ev_match)
            q["event_family"] = family
            q["received_at"] = {"$gte": cut}
            if sev:
                q["severity"] = sev
            return await db.motive_events.count_documents(q) if driver_ids else 0

        hos_30d = await _count("hos_violation")
        hos_24h = await _count("hos_violation", cut=cut_24h)
        harsh_30d = await _count("harsh_event")
        harsh_24h_high = 0
        if driver_ids:
            harsh_24h_high = await db.motive_events.count_documents({
                **ev_match,
                "event_family": "harsh_event",
                "severity": {"$in": ["high", "critical"]},
                "received_at": {"$gte": cut_24h},
            })
        dvir_30d = await _count("dvir")

        # Recent events feed (top 10, newest first)
        recent: List[Dict[str, Any]] = []
        if driver_ids:
            async for r in db.motive_events.find(
                ev_match, {"_id": 0}
            ).sort("received_at", -1).limit(10):
                recent.append({
                    "event_family": r.get("event_family"),
                    "severity": r.get("severity"),
                    "priority": r.get("priority"),
                    "received_at": r.get("received_at"),
                    "vehicle_id": r.get("vehicle_id"),
                    "headline": r.get("headline") or r.get("decorated_label"),
                })

        return {
            "as_of": now.isoformat(),
            "driver_key": driver_key,
            "mapping": mapping,
            "motive_user_id": motive_user_id,
            "counts_30d": {
                "hos_violations": hos_30d,
                "harsh_events": harsh_30d,
                "dvir_inspections": dvir_30d,
            },
            "counts_24h": {
                "hos_violations": hos_24h,
                "harsh_events_high": harsh_24h_high,
            },
            "recent_events": recent,
        }


__all__ = ["register_operations_intelligence_routes", "_gps_band", "GPS_GREEN_MAX_MIN", "GPS_AMBER_MAX_MIN"]
