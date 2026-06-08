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

        # Equipment not reporting (>24h)
        not_reporting: List[Dict[str, Any]] = []
        cut_24h = (now - timedelta(hours=24)).isoformat()
        async for am in db.asset_mappings.find({
            "provider": "motive", "motive.gps_enabled": True,
            "$or": [
                {"motive.located_at": {"$lt": cut_24h}},
                {"motive.located_at": None},
            ],
        }, {"_id": 0, "masci_equipment_id": 1, "masci_unit_number": 1,
            "motive.number": 1, "motive.located_at": 1}).limit(100):
            not_reporting.append({
                "masci_equipment_id": am.get("masci_equipment_id") or "",
                "unit_number": am.get("masci_unit_number") or (am.get("motive") or {}).get("number") or "",
                "last_seen": (am.get("motive") or {}).get("located_at"),
                "band": _gps_band((am.get("motive") or {}).get("located_at"))["band"],
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
        """OIS-1A · Per-asset GPS health band map.

        Powers DispatchBoard row badges and any per-vehicle band lookup.
        Returns lightweight rows keyed by unit_number (case-insensitive)
        and motive vehicle_id so the consumer can match on either.
        Read-only. No writes, no automation."""
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
            },
        ):
            mv = am.get("motive") or {}
            located = mv.get("located_at")
            band = _gps_band(located)
            speed = mv.get("speed_kph")
            moving = isinstance(speed, (int, float)) and speed > 5 and band["band"] == "green"
            rows.append({
                "masci_equipment_id": am.get("masci_equipment_id") or "",
                "unit_number": (am.get("masci_unit_number") or mv.get("number") or "").strip(),
                "vehicle_id": mv.get("vehicle_id") or "",
                "asset_id": mv.get("asset_id") or "",
                "band": band["band"],
                "label": band["label"],
                "minutes": band["minutes"],
                "located_at": located,
                "speed_kph": speed,
                "moving": bool(moving),
                "gps_enabled": bool(mv.get("gps_enabled")),
            })
        return {
            "as_of": datetime.now(timezone.utc).isoformat(),
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
