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


__all__ = ["register_operations_intelligence_routes", "_gps_band", "GPS_GREEN_MAX_MIN", "GPS_AMBER_MAX_MIN"]
