"""
routes/operations_map_contract.py · FORGEDOPS Live Operations Map · Phase 5A.

ONE canonical map contract endpoint. Composes (does NOT own) operational
truth from:
  - Asset Spine (`equipment_master`)
  - Dispatch Command Center (`dispatch_assignments`, `dispatch_state_events`)
  - PM Command Center (project scope via compute_pm_scope)
  - Shop (`fleet_defects`, equipment_master.status OOS)
  - Safety (`incidents`)
  - Motive (`motive_events`, vehicle_id ↔ motive_truck_id)

NO map render. NO FleetWatcher / MaintainX activation. Their slots are
returned as `*_pending` so the consumer can render a calm placeholder.

Single endpoint:
    GET /api/operations-map/contract
        ?scope=operations|dispatch|pm|shop|safety|admin
        ?project_number=<canonical>
        ?asset_kind=<normalized>
        ?asset_family=trench_safety|access_protection|traffic_control|support
        ?status=<status-string>
        ?attention_only=true|false
        ?limit=<int 1..5000>

Every row carries the canonical Phase 5A row schema (~70 fields across 8
buckets: identity / location / assignment / operational / telematics /
fleetwatcher / maintainx / attention / trust).

Phase 5A doctrine: backend-only contract VALIDATION. No UI map renders
this yet. Tests prove the shape is honest, calm, and consumable by every
portal without privileging any one.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query

import dispatch_lifecycle as DLS
from pm_auth import compute_pm_scope
from routes.pm_command_center import (
    normalize_asset_kind, ROAD_PLATE_CANONICAL, _map_ready,
    specialty_family_of, is_specialty_asset, SPECIALTY_ASSET_FAMILY,
)
from routes.operations_center_command import (
    _motive_state, _shop_priority, _safety_tier,
)

logger = logging.getLogger("operations_map_contract")


# Asset kind family classifier (broader than Specialty Assets — includes
# fleet, heavy equipment, project/job entities).
FLEET_KINDS = {
    "truck", "dump trucks", "dump truck", "haul truck",
    "tractor trailer trucks", "tractor trailer truck",
    "service trucks", "service truck",
    "flatbed trucks", "flatbed truck",
    "pickup trucks", "pickup truck",
    "water trucks", "water truck",
    "misc trucks", "supervisor / mgmt trucks",
    "trailer", "trailers", "semi", "semis",
}
HEAVY_EQUIPMENT_KINDS = {
    "excavator", "excavators",
    "loader", "loaders",
    "dozer", "dozers",
    "grader", "graders", "road grader", "road graders",
    "roller", "rollers",
    "paver", "pavers", "paving equipment",
    "mill", "mills", "milling", "milling machine",
    "skid steer", "skid steers",
    "compactor", "compactors",
    "backhoe", "backhoes",
}


def _asset_family(kind: Optional[str]) -> str:
    if not kind: return "unknown"
    k = kind.strip().lower()
    if k in FLEET_KINDS: return "fleet"
    if k in HEAVY_EQUIPMENT_KINDS: return "heavy_equipment"
    fam = specialty_family_of(k)
    if fam: return f"specialty:{fam}"
    return "other"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _human_age(minutes: Optional[float]) -> str:
    """Render a confidence age as a calm human label.

    Used by the Phase T5 confidence model so map markers can show
    "2 min ago" / "1 hr ago" / "unknown" without each consumer
    re-implementing the formatting.
    """
    if minutes is None:
        return "unknown"
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{int(minutes)} min ago"
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)} hr ago"
    days = hours / 24
    return f"{int(days)} day{'s' if days >= 2 else ''} ago"


def _missing(*fields: Optional[Any]) -> List[str]:
    """Return list of field-name keys whose value is None/empty (helper
    for `missing_fields` trust signal)."""
    return [name for name, val in zip(("__placeholder__",), fields)]  # not used


# ════════════════════════════════════════════════════════════════════
# Row builder
# ════════════════════════════════════════════════════════════════════
def _build_row(
    em: Dict[str, Any],
    *,
    assignment: Optional[Dict[str, Any]] = None,
    motive_event: Optional[Dict[str, Any]] = None,
    defect_count: int = 0,
    open_defect_severity: Optional[str] = None,
    incident_count: int = 0,
    project_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build one canonical Phase 5A map-contract row from composed sources.

    The function MUST NOT invent location data. If Motive has no event
    for the asset, lat/lon stay None and location_trust_state becomes
    one of {no_gps, no_location, asset_spine_only}.
    """
    # ─── Identity ────────────────────────────────────────────────────
    unit = em.get("unit_number") or em.get("asset_number")
    raw_kind = em.get("type") or em.get("asset_type") or em.get("category") or ""
    kind = normalize_asset_kind(raw_kind) or ""
    family = _asset_family(kind)

    # ─── Location ────────────────────────────────────────────────────
    lat = (motive_event or {}).get("lat")
    lon = (motive_event or {}).get("lon")
    last_loc_time = (motive_event or {}).get("timestamp")
    location_label = em.get("current_location") or em.get("yard") or None
    # ── Confidence model (Phase T5) ──────────────────────────────────
    # LIVE   = last_loc_time within 5 minutes
    # DELAYED = 5–60 minutes
    # UNKNOWN = no last_loc_time OR > 60 minutes
    confidence = "UNKNOWN"
    confidence_age_minutes: Optional[float] = None
    if last_loc_time:
        try:
            ts = datetime.fromisoformat(str(last_loc_time).replace("Z", "+00:00"))
            confidence_age_minutes = (datetime.now(timezone.utc) - ts).total_seconds() / 60.0
            if confidence_age_minutes <= 5:
                confidence = "LIVE"
            elif confidence_age_minutes <= 60:
                confidence = "DELAYED"
            else:
                confidence = "UNKNOWN"
        except Exception:
            confidence = "UNKNOWN"
    if lat is not None and lon is not None:
        location_source = "motive"
        location_confidence = "high"
        location_trust_state = "live_location" if confidence == "LIVE" else "last_known_location"
    elif last_loc_time:
        location_source = "motive_stale"
        location_confidence = "low"
        location_trust_state = "last_known_location"
    elif em.get("motive_truck_id"):
        location_source = "none"
        location_confidence = "none"
        location_trust_state = "no_gps"
    elif location_label:
        location_source = "asset_spine_label"
        location_confidence = "low"
        location_trust_state = "asset_spine_only"
    else:
        location_source = "none"
        location_confidence = "none"
        location_trust_state = "no_location"

    # ─── Movement / op state ─────────────────────────────────────────
    movement_state = _motive_state(
        (motive_event or {}).get("speed_mph"),
        (motive_event or {}).get("status"),
        last_loc_time,
    ) if em.get("motive_truck_id") else (
        "no_telematics"
    )

    # ─── Shop state ──────────────────────────────────────────────────
    status_em = (em.get("status") or "").lower()
    if status_em in ("out of service", "down"):
        shop_state = "oos"
    elif status_em in ("maintenance hold",):
        shop_state = "maintenance_hold"
    elif defect_count > 0:
        shop_state = "open_defect"
    else:
        shop_state = "ok"

    # ─── Safety / dispatch state ─────────────────────────────────────
    safety_state = "incident_open" if incident_count > 0 else "ok"
    dispatch_state = (assignment or {}).get("current_state") or "no_assignment"

    # ─── Availability ────────────────────────────────────────────────
    if shop_state == "oos": availability_state = "out_of_service"
    elif shop_state == "maintenance_hold": availability_state = "in_shop"
    elif assignment and dispatch_state not in DLS.TERMINAL_STATES:
        availability_state = "assigned"
    else:
        availability_state = "available"

    operational_state = (
        "oos" if shop_state == "oos" else
        "in_shop" if shop_state in ("maintenance_hold", "open_defect") else
        "active_haul" if dispatch_state == "in_motion" else
        movement_state if em.get("motive_truck_id") else
        ("assigned" if assignment else "available")
    )

    # ─── Haul state (placeholder for FleetWatcher) ───────────────────
    haul_state = "active" if assignment and dispatch_state == "in_motion" else (
        "assigned" if assignment else "no_haul")

    # ─── Attention engine ────────────────────────────────────────────
    needs_attention = False
    attention_reason: Optional[str] = None
    attention_severity: Optional[str] = None
    action_label: Optional[str] = None
    action_route: Optional[str] = None
    if shop_state == "oos":
        needs_attention = True
        attention_severity = "high"
        attention_reason = "Out of service"
        action_label = "Open Shop"; action_route = "/shop"
    elif shop_state == "open_defect" and open_defect_severity in ("critical", "high"):
        needs_attention = True; attention_severity = "high"
        attention_reason = f"{defect_count} defect(s)"
        action_label = "Open Shop"; action_route = "/shop"
    elif incident_count > 0:
        needs_attention = True; attention_severity = "high"
        attention_reason = f"{incident_count} open incident(s)"
        action_label = "Open Safety"; action_route = "/admin/safety-portal"
    elif location_trust_state == "no_gps" and family == "fleet":
        needs_attention = True; attention_severity = "medium"
        attention_reason = "Motive mapped but no GPS"
        action_label = "Open Mapping Queue"; action_route = "/admin/mapping-queue"
    elif family == "fleet" and not em.get("motive_truck_id"):
        needs_attention = True; attention_severity = "medium"
        attention_reason = "Not mapped to Motive"
        action_label = "Map Asset"; action_route = "/admin/asset-spine"
    elif shop_state == "open_defect":
        needs_attention = True; attention_severity = "medium"
        attention_reason = f"{defect_count} defect(s)"
        action_label = "Open Shop"; action_route = "/shop"

    # ─── Trust ───────────────────────────────────────────────────────
    missing: List[str] = []
    if lat is None or lon is None: missing.append("lat_lon")
    if not em.get("motive_truck_id") and family == "fleet":
        missing.append("motive_truck_id")
    if not em.get("current_project_number") and family != "specialty:access_protection":
        # specialty assets are commonly unassigned; not a fault.
        if family == "fleet": missing.append("project_assignment")
    if not assignment and family == "fleet" and availability_state == "available":
        missing.append("active_dispatch")
    source_systems: List[str] = ["asset_spine"]
    if motive_event: source_systems.append("motive")
    if assignment: source_systems.append("dispatch_lifecycle")
    if defect_count: source_systems.append("fleet_defects")
    if incident_count: source_systems.append("incidents")

    trust_state = (
        "live_location" if location_trust_state == "live_location" else
        location_trust_state
    )

    project_number = em.get("current_project_number") or (assignment or {}).get("project_number")
    project_id = em.get("current_project_id") or (assignment or {}).get("project_id")

    return {
        # ── Identity ─────────────────────────────────────────────────
        "asset_id": em.get("id") or em.get("asset_id"),
        "asset_number": unit,
        "asset_name": em.get("name") or unit,
        "asset_kind": kind or "unknown",
        "asset_family": family,
        "asset_type": raw_kind,
        "canonical_source": "asset_spine",

        # ── Location ─────────────────────────────────────────────────
        "lat": lat,
        "lon": lon,
        "location_label": location_label,
        "location_source": location_source,
        "last_location_time": last_loc_time,
        "location_confidence": location_confidence,
        "location_trust_state": location_trust_state,
        # Phase T5 — confidence model (LIVE / DELAYED / UNKNOWN)
        "confidence": confidence,
        "confidence_age_minutes": confidence_age_minutes,
        "last_update_human": _human_age(confidence_age_minutes),

        # ── Assignment ───────────────────────────────────────────────
        "project_id": project_id,
        "project_number": project_number,
        "project_name": (project_meta or {}).get("project_name") if project_meta else None,
        "assigned_driver_id": (assignment or {}).get("driver_id"),
        "assigned_driver_name": (assignment or {}).get("driver_name"),
        "assigned_dispatch_id": (assignment or {}).get("id"),
        "assigned_pm": (project_meta or {}).get("pm_name") or
                        (project_meta or {}).get("pm_email") if project_meta else None,
        "assigned_crew": (assignment or {}).get("crew") or None,

        # ── Operational State ────────────────────────────────────────
        "operational_state": operational_state,
        "movement_state": movement_state,
        "haul_state": haul_state,
        "shop_state": shop_state,
        "safety_state": safety_state,
        "dispatch_state": dispatch_state,
        "availability_state": availability_state,

        # ── Telematics ───────────────────────────────────────────────
        "motive_vehicle_id": em.get("motive_truck_id"),
        "motive_driver_id": (motive_event or {}).get("driver_id"),
        "gps_status": "active" if (lat is not None and lon is not None) else (
                        "stale" if last_loc_time else "no_gps"),
        "speed": (motive_event or {}).get("speed_mph"),
        "idle_minutes": (motive_event or {}).get("idle_minutes"),
        "ignition_state": (motive_event or {}).get("ignition") or None,
        "geofence": (motive_event or {}).get("geofence") or None,
        "engine_hours": (motive_event or {}).get("engine_hours") or em.get("engine_hours"),
        "fault_state": (motive_event or {}).get("fault_state") or None,

        # ── FleetWatcher (pending integration) ───────────────────────
        "fleetwatcher_status": "not_connected",
        "ticket_number": None, "material": None,
        "plant": None, "source_location": None, "destination_location": None,
        "tons": None, "load_status": None, "cycle_time_minutes": None,

        # ── MaintainX (pending integration) ──────────────────────────
        "maintainx_status": "not_connected",
        "work_order_id": None, "maintenance_status": None,
        "estimated_return": None, "repair_priority": None,

        # ── Attention ────────────────────────────────────────────────
        "needs_attention": bool(needs_attention),
        "attention_reason": attention_reason,
        "attention_severity": attention_severity,
        "action_label": action_label or "route_pending",
        "action_route": action_route,  # null when no route exists yet

        # ── Trust ────────────────────────────────────────────────────
        "trust_state": trust_state,
        "missing_fields": missing,
        "source_systems": source_systems,
        "updated_at": em.get("updated_at") or _now_iso(),

        # ── Map-ready field set (unchanged contract from prior phases)
        **_map_ready(
            asset_id=em.get("id") or em.get("asset_id"),
            project_number=project_number,
            assignment_id=(assignment or {}).get("id"),
            status=operational_state,
            location_ref=location_label,
            timestamp=last_loc_time or em.get("updated_at"),
            operational_state=operational_state,
            trust_state=trust_state,
            source_system="operations_map_contract",
        ),
    }


# ════════════════════════════════════════════════════════════════════
# Router factory
# ════════════════════════════════════════════════════════════════════
def build_operations_map_contract_router(
    db,
    require_any_portal_token_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    router = APIRouter(prefix="/api/operations-map",
                       tags=["operations-map-contract"])

    @router.get("/contract")
    async def contract(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),
        scope: str = Query(default="operations",
            regex="^(operations|dispatch|pm|shop|safety|admin)$"),
        project_number: Optional[str] = Query(default=None),
        asset_kind: Optional[str] = Query(default=None),
        asset_family: Optional[str] = Query(default=None,
            description="fleet | heavy_equipment | specialty:trench_safety | "
                          "specialty:access_protection | specialty:traffic_control | "
                          "specialty:support | other"),
        status: Optional[str] = Query(default=None),
        attention_only: bool = Query(default=False),
        limit: int = Query(default=2000, ge=1, le=5000),
    ) -> Dict[str, Any]:
        """ONE platform map contract.

        Trust states explain every missing field. No fake location.
        """
        # ─── 1 · Build PM scope when scope=pm ───────────────────────
        pm_scope_pns: Optional[Set[str]] = None
        if scope == "pm":
            ps = await compute_pm_scope(db, actor)
            if ps.is_admin and not project_number:
                # Admin in PM mode without explicit filter — show
                # everything (matches existing PM CC admin doctrine).
                pm_scope_pns = None
            elif not ps.is_admin:
                pm_scope_pns = ps.project_numbers
                # Empty-scope PM → empty contract (no leak).
                if not pm_scope_pns:
                    return _empty_envelope(scope, project_number, asset_kind,
                                              asset_family, attention_only)

        # ─── 2 · Pre-load joins to avoid N+1 ────────────────────────
        # Active assignments
        assn_by_truck: Dict[str, Dict[str, Any]] = {}
        async for a in db.dispatch_assignments.find(
            {"current_state": {"$nin": list(DLS.TERMINAL_STATES)},
              "cancelled_at": None},
            {"_id": 0, "id": 1, "truck_id": 1, "driver_id": 1, "driver_name": 1,
              "project_number": 1, "project_id": 1, "current_state": 1, "crew": 1},
        ):
            if a.get("truck_id"):
                assn_by_truck[a["truck_id"]] = a

        # Latest Motive event per vehicle_id
        latest_by_motive: Dict[str, Dict[str, Any]] = {}
        try:
            async for e in db.motive_events.find(
                {"event_type": {"$in": ["location", "vehicle.location",
                                          "vehicle_location", "telemetry"]}},
                {"_id": 0, "vehicle_id": 1, "speed_mph": 1, "status": 1,
                  "timestamp": 1, "lat": 1, "lon": 1, "driver_id": 1,
                  "idle_minutes": 1, "ignition": 1, "geofence": 1,
                  "engine_hours": 1, "fault_state": 1},
            ).sort("timestamp", -1).limit(5000):
                vid = e.get("vehicle_id")
                if vid and vid not in latest_by_motive:
                    latest_by_motive[vid] = e
        except Exception:
            pass

        # Defect counts per truck unit
        defect_by_unit: Dict[str, Tuple[int, Optional[str]]] = {}
        async for d in db.fleet_defects.find(
            {"status": {"$in": ["open", "acknowledged"]}},
            {"_id": 0, "truck_unit_number": 1, "severity": 1},
        ):
            unit = d.get("truck_unit_number")
            if not unit: continue
            prev = defect_by_unit.get(unit, (0, None))
            sev = d.get("severity") or prev[1]
            defect_by_unit[unit] = (prev[0] + 1, sev)

        # Incident counts per project_number
        inc_by_project: Dict[str, int] = {}
        async for i in db.incidents.find(
            {"resolution_status": {"$ne": "Closed"}},
            {"_id": 0, "project_number": 1},
        ):
            pn = i.get("project_number")
            if pn: inc_by_project[pn] = inc_by_project.get(pn, 0) + 1

        # Project meta lookup (just enough for project_name + pm_name)
        project_meta_by_pn: Dict[str, Dict[str, Any]] = {}
        async for p in db.jobs_master.find(
            {}, {"_id": 0, "project_number": 1, "project_name": 1, "name": 1,
                  "pm_name": 1, "pm_email": 1},
        ):
            pn = p.get("project_number")
            if pn:
                project_meta_by_pn[pn] = {
                    "project_name": p.get("project_name") or p.get("name"),
                    "pm_name": p.get("pm_name"),
                    "pm_email": p.get("pm_email"),
                }

        # ─── 3 · Stream equipment_master & build rows ───────────────
        rows: List[Dict[str, Any]] = []
        em_q: Dict[str, Any] = {
            "$or": [{"is_active": {"$ne": False}}, {"active": {"$ne": False}}],
        }
        if project_number:
            em_q["current_project_number"] = project_number
        elif pm_scope_pns is not None:
            em_q["current_project_number"] = {"$in": list(pm_scope_pns)}

        async for em in db.equipment_master.find(em_q).limit(limit * 2):
            unit = em.get("unit_number") or em.get("asset_number")
            raw_kind = em.get("type") or em.get("asset_type") or em.get("category") or ""
            kind = normalize_asset_kind(raw_kind) or ""
            family = _asset_family(kind)
            # Filter by family / kind
            if asset_family and family != asset_family:
                continue
            if asset_kind and kind != asset_kind:
                continue
            # Scope-specific filters (server-side, calm)
            if scope == "dispatch":
                # only fleet + active assignment OR with motive_id
                if family != "fleet" and family != "heavy_equipment":
                    continue
            elif scope == "shop":
                stat = (em.get("status") or "").lower()
                if stat not in ("out of service", "down", "maintenance hold"):
                    if not defect_by_unit.get(unit):
                        continue
            elif scope == "safety":
                # Show only assets attached to projects with open incidents.
                pn = em.get("current_project_number")
                if not pn or pn not in inc_by_project:
                    continue
            # PM scope already filtered above via em_q.

            assn = assn_by_truck.get(unit) or assn_by_truck.get(em.get("id"))
            mev = (latest_by_motive.get(em.get("motive_truck_id"))
                   if em.get("motive_truck_id") else None)
            dcount, dsev = defect_by_unit.get(unit, (0, None))
            pn = em.get("current_project_number") or (assn or {}).get("project_number")
            icount = inc_by_project.get(pn, 0) if pn else 0
            row = _build_row(
                em,
                assignment=assn,
                motive_event=mev,
                defect_count=dcount,
                open_defect_severity=dsev,
                incident_count=icount,
                project_meta=project_meta_by_pn.get(pn) if pn else None,
            )
            # Server-side status / attention filters (post-build).
            if status and row["operational_state"] != status:
                continue
            if attention_only and not row["needs_attention"]:
                continue
            rows.append(row)
            if len(rows) >= limit:
                break

        # ─── 4 · Counts summary ─────────────────────────────────────
        counts = {
            "total_rows": len(rows),
            "with_live_location": sum(1 for r in rows if r["location_trust_state"] == "live_location"),
            "with_last_known_location": sum(1 for r in rows if r["location_trust_state"] == "last_known_location"),
            "no_location": sum(1 for r in rows if r["location_trust_state"] in ("no_location", "no_gps", "asset_spine_only")),
            "needs_attention": sum(1 for r in rows if r["needs_attention"]),
            "unmapped": sum(1 for r in rows if "motive_truck_id" in r["missing_fields"]),
            "offline": sum(1 for r in rows if r["movement_state"] == "offline"),
            "oos": sum(1 for r in rows if r["shop_state"] == "oos"),
            "active_hauls": sum(1 for r in rows if r["operational_state"] == "active_haul"),
            "specialty_assets": sum(1 for r in rows if r["asset_family"].startswith("specialty:")),
            "trucks": sum(1 for r in rows if r["asset_family"] == "fleet"),
            "equipment": sum(1 for r in rows if r["asset_family"] == "heavy_equipment"),
        }

        return {
            "ok": True,
            "as_of": _now_iso(),
            # Phase T2/T5 — environment stamp on every contract response.
            "environment": (os.environ.get("APP_ENV") or "preview").strip().lower(),
            "database": os.environ.get("DB_NAME") or "unknown",
            "scope": scope,
            "project_number_filter": project_number,
            "asset_family_filter": asset_family,
            "asset_kind_filter": asset_kind,
            "status_filter": status,
            "attention_only": bool(attention_only),
            "rows": rows,
            "counts": counts,
            "integration_readiness": {
                "fleetwatcher": "not_connected",
                "maintainx": "not_connected",
                "motive": "active" if latest_by_motive else "partial",
            },
            "confidence_model": {
                "live_window_minutes": 5,
                "delayed_window_minutes": 60,
                "states": ["LIVE", "DELAYED", "UNKNOWN"],
            },
        }

    return router


def _empty_envelope(scope, project_number, asset_kind, asset_family, attention_only):
    return {
        "ok": True, "as_of": _now_iso(),
        "scope": scope,
        "project_number_filter": project_number,
        "asset_family_filter": asset_family,
        "asset_kind_filter": asset_kind,
        "status_filter": None,
        "attention_only": bool(attention_only),
        "rows": [],
        "counts": {
            "total_rows": 0, "with_live_location": 0,
            "with_last_known_location": 0, "no_location": 0,
            "needs_attention": 0, "unmapped": 0, "offline": 0,
            "oos": 0, "active_hauls": 0, "specialty_assets": 0,
            "trucks": 0, "equipment": 0,
        },
        "integration_readiness": {
            "fleetwatcher": "not_connected",
            "maintainx": "not_connected",
            "motive": "partial",
        },
    }


__all__ = ["build_operations_map_contract_router", "_build_row", "_asset_family"]
