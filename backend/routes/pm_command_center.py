"""
routes/pm_command_center.py · FORGEDOPS PM Command Center · Phase 4A.

PM-scoped read-only aggregation that powers the future PM Command
Center UI. Composes Asset Spine + dispatch lifecycle + driver sessions
+ fleet defects + haul cycles + projects + daily reports + incidents
into 7 endpoints under /api/pm/command-center/*.

Doctrine:
  - Asset Spine canonical (no parallel asset store, no road-plate-only
    collection).
  - Road plates are first-class asset type "road_plate" — the
    normalizer recognizes the canonical value AND legacy strings
    (Road Plate, Steel Plate, Plate, Plates, Trench Plate,
    Traffic Plate, Roadplate, ROAD PLATE).
  - Governance project scope is the PM authorization boundary.
  - Every operational row carries the map-ready field set:
    asset_id · project_id · project_number · assignment_id · status ·
    location_ref · timestamp · operational_state · trust_state ·
    source_system.
  - No production data mutation. No new collection.
  - FleetWatcher / MaintainX templates returned `not_connected`.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from lib.enterprise_governance import GovernanceProjectScope, governance_project_scope
from lib.synthetic_corrective_action_filter import apply_synthetic_corrective_action_exclusion
from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion
import dispatch_lifecycle as DLS

logger = logging.getLogger("pm_command_center")


# ════════════════════════════════════════════════════════════════════
# Road Plate canonical normalization
# ════════════════════════════════════════════════════════════════════
ROAD_PLATE_CANONICAL = "road_plate"
ROAD_PLATE_LEGACY_VALUES = {
    "road plate", "steel plate", "plate", "plates",
    "trench plate", "traffic plate", "roadplate", "road_plate",
}

# ════════════════════════════════════════════════════════════════════
# TRACK 15.82 · Roll-Off canonical normalization
# ════════════════════════════════════════════════════════════════════
# Single source of truth for the seven roll-off aliases the operator
# spelled out:
#   rolloff · roll-off · roll off · roll off truck ·
#   roll-off truck · rolloff truck · container truck
# All resolve to the canonical lower-snake key ``roll_off_truck``.
# Display label (for UI) is ``Roll-Off Truck`` to match the taxonomy
# entry in ``services/asset_taxonomy.py``.
ROLL_OFF_CANONICAL = "roll_off_truck"
ROLL_OFF_DISPLAY_LABEL = "Roll-Off Truck"
ROLL_OFF_LEGACY_VALUES = {
    "rolloff", "roll-off", "roll off",
    "roll-offs", "rolloffs",
    "roll off truck", "roll-off truck", "rolloff truck",
    "roll off trucks", "roll-off trucks", "rolloff trucks",
    "container truck", "container trucks",
    "roll_off", "roll_off_truck",
}


def normalize_asset_kind(raw: Optional[str]) -> Optional[str]:
    """Lowercase + map legacy plate / roll-off names to canonical keys.

    Anything else returns the lowercased original (or None when empty)
    so callers can do simple equality comparisons.

    Track 15.82 — Roll-Off aliases collapse to ``roll_off_truck`` so
    map markers, dispatch counts, and filters all key off one value.
    """
    if not raw:
        return None
    v = str(raw).strip().lower()
    if v in ROAD_PLATE_LEGACY_VALUES:
        return ROAD_PLATE_CANONICAL
    if v in ROLL_OFF_LEGACY_VALUES:
        return ROLL_OFF_CANONICAL
    return v


# ════════════════════════════════════════════════════════════════════
# Specialty Asset Family — Phase 4C architecture correction
# ════════════════════════════════════════════════════════════════════
# Road plates are NOT a privileged operational category. They are ONE
# member of the Specialty Asset family. The platform tracks the whole
# family equally; downstream UIs surface family-level counts and let
# operators drill into a specific kind.
#
# Doctrine: Specialty Assets are NON-fleet, NON-driver resources that
# get deployed/recovered/inspected as units. They count as company
# capacity but do not appear in the truck/trailer fleet rosters.
SPECIALTY_ASSET_FAMILY: Dict[str, List[str]] = {
    "trench_safety": [
        "trench_box", "trench box", "trench boxes",
        "end_panel", "end panel", "end panels",
        "spreader", "spreaders",
        "shield", "shields",
        "trench safety", "trench safety component", "trench safety components",
    ],
    "access_protection": [
        ROAD_PLATE_CANONICAL,  # canonical
        "steel plate", "temporary mat", "temporary mats",
        "crossing protection", "crossing protection system",
    ],
    "traffic_control": [
        "arrow_board", "arrow board", "arrow boards",
        "message_board", "message board", "message boards",
        "portable signal", "portable signals",
        "specialty mot", "specialty mot device", "mot device",
    ],
    "support": [
        "pump", "pumps",
        "generator", "generators",
        "fuel_tank", "fuel tank", "fuel tanks",
        "water_tank", "water tank", "water tanks",
        "light tower", "light towers",
        "temporary utility", "temporary utility asset",
        "air compressor", "air compressors",
    ],
}

# Reverse lookup: normalized_kind → family_key. Cheaper than scanning.
_SPECIALTY_KIND_TO_FAMILY: Dict[str, str] = {}
for _fam, _kinds in SPECIALTY_ASSET_FAMILY.items():
    for _k in _kinds:
        _SPECIALTY_KIND_TO_FAMILY[_k.lower()] = _fam


def specialty_family_of(asset_kind: Optional[str]) -> Optional[str]:
    """Return family key (trench_safety/access_protection/traffic_control/
    support) for an asset kind, or None if not a specialty asset."""
    if not asset_kind:
        return None
    k = str(asset_kind).strip().lower()
    return _SPECIALTY_KIND_TO_FAMILY.get(k)


def is_specialty_asset(asset_kind: Optional[str]) -> bool:
    return specialty_family_of(asset_kind) is not None



def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _start_of_utc_day() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _maintainx_tpl() -> Dict[str, Any]:
    return {"connected": False, "status": "not_connected", "work_order_id": None}


def _fleetwatcher_tpl() -> Dict[str, Any]:
    return {"connected": False, "status": "not_connected",
            "ticket_number": None, "tons": None, "loads": None}


def _map_ready(*, asset_id=None, project_id=None, project_number=None,
                assignment_id=None, status=None, location_ref=None,
                timestamp=None, operational_state=None,
                trust_state=None, source_system="forgedops") -> Dict[str, Any]:
    """Mandatory map-ready field set on every operational row."""
    return {
        "asset_id": asset_id,
        "project_id": project_id,
        "project_number": project_number,
        "assignment_id": assignment_id,
        "status": status,
        "location_ref": location_ref,
        "timestamp": timestamp,
        "operational_state": operational_state,
        "trust_state": trust_state,
        "source_system": source_system,
    }


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════

def _scope_filter_q(scope: GovernanceProjectScope, project_number: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the project_number Mongo filter. None when no projects."""
    if scope.is_admin:
        if project_number:
            return {"project_number": project_number}
        return {}
    nums = list(scope.project_numbers or [])
    if not nums:
        return None
    if project_number:
        if project_number not in nums:
            return None
        return {"project_number": project_number}
    return {"project_number": {"$in": nums}}


async def _pm_scope_project_numbers(scope: GovernanceProjectScope,
                                     project_number: Optional[str]) -> List[str]:
    if scope.is_admin and project_number:
        return [project_number]
    if scope.is_admin:
        return []  # admin without filter → return [] = "any"
    nums = list(scope.project_numbers or [])
    if project_number and project_number in nums:
        return [project_number]
    return nums


def _classify_asset_kind(em: Dict[str, Any]) -> str:
    """Asset Spine kind classifier with road-plate normalization."""
    raw = em.get("type") or em.get("asset_type") or em.get("category") or em.get("asset_category") or ""
    k = normalize_asset_kind(raw)
    return k or "unknown"


# ════════════════════════════════════════════════════════════════════
# Track 13.6F · helpers for PM-2 (Holds) and PM-3 (Due Today)
# ════════════════════════════════════════════════════════════════════
def _urlq(value: Any) -> str:
    """Track 13.6G — safe url-quote for deep-link query params.
    Backend owns destination paths; the browser must never reconstruct
    them, so we pre-encode every dynamic segment here."""
    from urllib.parse import quote
    if value is None:
        return ""
    return quote(str(value), safe="")
def _age_days(iso_ts: Optional[str], now: Optional[datetime] = None) -> int:
    if not iso_ts:
        return 0
    try:
        ts = iso_ts.replace("Z", "+00:00") if iso_ts.endswith("Z") else iso_ts
        d = datetime.fromisoformat(ts)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
    except Exception:
        return 0
    n = now or datetime.now(timezone.utc)
    return max(0, (n - d).days)


# ════════════════════════════════════════════════════════════════════
# Track 13.6H · Phase 1 — SLA / Age chip (operational truth only).
# ════════════════════════════════════════════════════════════════════
# Renders a one-phrase operational chip from REAL existing timestamps.
# Strictly factual — no risk scores, no AI priority, no red/yellow/green.
#
# Inputs:
#   - opened_at (iso str) → emits "Held N Days" / "Held Today"
#   - due_date  (yyyy-mm-dd) → emits "Due Today" / "Due In N Days"
#                              / "Overdue N Days"
# Fallback: empty string when neither field is usable.
def _sla_label_hold(opened_at_iso: Optional[str],
                    now: Optional[datetime] = None) -> str:
    if not opened_at_iso:
        return ""
    n = now or datetime.now(timezone.utc)
    days = _age_days(opened_at_iso, n)
    if days <= 0:
        return "Held Today"
    if days == 1:
        return "Held 1 Day"
    return f"Held {days} Days"


def _sla_label_due(due_date_yyyymmdd: Optional[str],
                   now: Optional[datetime] = None) -> str:
    if not due_date_yyyymmdd:
        return ""
    try:
        n = now or datetime.now(timezone.utc)
        today = n.date()
        d = datetime.strptime(str(due_date_yyyymmdd)[:10], "%Y-%m-%d").date()
    except Exception:
        return ""
    delta = (d - today).days
    if delta == 0:
        return "Due Today"
    if delta == 1:
        return "Due Tomorrow"
    if delta > 1:
        return f"Due In {delta} Days"
    overdue = -delta
    if overdue == 1:
        return "Overdue 1 Day"
    return f"Overdue {overdue} Days"




def _constraint_row(c: Dict[str, Any], created: Optional[str],
                    now: datetime,
                    project_id_to_pn: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Project a real operational_constraints doc into the unified
    holds row shape. Preserves source ownership: row.source =
    'operational_constraints', destination_path = '/constraints/<id>'
    (true one-click drill to the source detail page)."""
    pn = None
    if project_id_to_pn and c.get("project_id"):
        pn = project_id_to_pn.get(c["project_id"])
    c_id = c.get("id") or ""
    dest_path = f"/constraints/{c_id}" if c_id else "/constraints"
    title = c.get("title") or "Operational constraint"
    return {
        "kind": "constraint",
        "id": c_id,
        "source": "operational_constraints",
        # ── Track 13.6G · canonical drill fields ─────────────────────
        "source_engine": "operational_constraints",
        "source_id": c_id,
        "destination_path": dest_path,
        "destination_label": f"Open · {title[:48]}",
        # ── Track 13.6H · SLA chip (operational truth, real source) ──
        "sla_label": _sla_label_hold(created, now),
        # ────────────────────────────────────────────────────────────
        "title": title,
        "subtitle": f"{c.get('discipline') or 'other'} · {c.get('kind') or 'other'}",
        "severity": (c.get("severity") or "medium").lower(),
        "project_number": pn,
        "project_id": c.get("project_id"),
        "opened_at": created,
        "age_days": _age_days(created, now),
        "status": c.get("status"),
        **_map_ready(
            project_id=c.get("project_id"),
            project_number=pn,
            status=c.get("status"),
            timestamp=created,
            trust_state="constraint_open",
            source_system="operational_constraints",
        ),
    }


# ════════════════════════════════════════════════════════════════════
# Router factory
# ════════════════════════════════════════════════════════════════════
def build_pm_command_center_router(
    db,
    require_pm_or_admin_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    router = APIRouter(prefix="/api/pm/command-center", tags=["pm-command-center"])

    async def _scope(actor) -> GovernanceProjectScope:
        return await governance_project_scope(db, actor)

    # ────────────────────────────────────────────────────────────
    # /overview — top strip KPIs
    # ────────────────────────────────────────────────────────────
    @router.get("/overview")
    async def overview(
        actor=Depends(require_pm_or_admin_dep),
        project_number: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        scope = await _scope(actor)
        nums = await _pm_scope_project_numbers(scope, project_number)
        if not scope.is_admin and not nums:
            return _empty_overview(project_number)

        pn_filter = {"project_number": {"$in": nums}} if nums else {}
        day_start = _start_of_utc_day().isoformat()

        # Active assignments scoped to project(s)
        assn_q = {"current_state": {"$nin": list(DLS.TERMINAL_STATES)},
                  "cancelled_at": None}
        assn_q.update(pn_filter)
        trucks: set = set()
        drivers: set = set()
        equipment: set = set()
        trailers: set = set()
        active_assns = 0
        active_hauls = 0
        async for a in db.dispatch_assignments.find(assn_q, {
            "_id": 0, "truck_id": 1, "driver_id": 1, "driver_name": 1,
            "trailer_id": 1, "equipment_id": 1, "current_state": 1,
        }):
            active_assns += 1
            if a.get("current_state") not in DLS.TERMINAL_STATES:
                active_hauls += 1
            if a.get("truck_id"): trucks.add(a["truck_id"])
            if a.get("driver_id"): drivers.add(a["driver_id"])
            elif a.get("driver_name"): drivers.add(a["driver_name"])
            if a.get("trailer_id"): trailers.add(a["trailer_id"])
            if a.get("equipment_id"): equipment.add(a["equipment_id"])

        # Equipment assigned via equipment_master.current_project_number
        em_assigned_q: Dict[str, Any] = {}
        if nums:
            em_assigned_q["current_project_number"] = {"$in": nums}
        equipment_assigned = await db.equipment_master.count_documents(em_assigned_q)

        # Road plates assigned (canonical + legacy normalization in code)
        # AND specialty-asset family counts (Phase 4C correction — road
        # plates are ONE member of Specialty Assets, not privileged).
        road_plates_assigned = 0
        specialty_assets_assigned = 0
        specialty_by_family: Dict[str, int] = {
            "trench_safety": 0, "access_protection": 0,
            "traffic_control": 0, "support": 0,
        }
        async for em in db.equipment_master.find(em_assigned_q,
                                                  {"_id": 0, "type": 1, "asset_type": 1,
                                                   "category": 1, "asset_category": 1}):
            kind = _classify_asset_kind(em)
            if kind == ROAD_PLATE_CANONICAL:
                road_plates_assigned += 1
            fam = specialty_family_of(kind)
            if fam:
                specialty_assets_assigned += 1
                specialty_by_family[fam] = specialty_by_family.get(fam, 0) + 1

        # Defects impacting project (via truck_id of recent assignment)
        defects_open = 0
        if nums:
            recent_trucks = await db.dispatch_assignments.distinct("truck_id", pn_filter)
            if recent_trucks:
                defects_open = await db.fleet_defects.count_documents({
                    "status": {"$in": ["open", "acknowledged"]},
                    "truck_unit_number": {"$in": [t for t in recent_trucks if t]},
                })

        # Incidents
        inc_q: Dict[str, Any] = {"resolution_status": {"$ne": "Closed"}}
        if nums: inc_q["project_number"] = {"$in": nums}
        incidents_open = await db.incidents.count_documents(inc_q)

        # CAPAs
        capas_q: Dict[str, Any] = {"status": {"$nin": ["Completed", "Closed", "Cancelled"]}}
        if nums: capas_q["project_number"] = {"$in": nums}
        capas_open = await db.corrective_actions.count_documents(
            apply_synthetic_corrective_action_exclusion(capas_q)
        )

        # Material movement today (daily_reports)
        today_yyyymmdd = datetime.now(timezone.utc).date().isoformat()
        materials_in = 0
        materials_out = 0
        dr_q: Dict[str, Any] = {"report_date": today_yyyymmdd,
                                "deleted_at": {"$in": [None, "", False]}}
        if nums: dr_q["project_number"] = {"$in": nums}
        async for d in db.daily_reports.find(apply_synthetic_dr_exclusion(dr_q),
                                             {"_id": 0, "materials": 1, "outbound_materials": 1}):
            materials_in += len(d.get("materials") or [])
            materials_out += len(d.get("outbound_materials") or [])

        # Loads today
        hc_q: Dict[str, Any] = {"completed_at": {"$gte": day_start}}
        if nums: hc_q["project_number"] = {"$in": nums}
        loads_today_dispatch = await db.haul_cycles.count_documents(hc_q)

        # TRACK 15.62 · K-AGG-1 · also sum loads recorded via Daily
        # Report outbound_materials for today. Without this, foreman-
        # captured hauls were invisible to PMs (the 15.61 finding).
        # Imports kept inline to avoid restructuring the registrar fn.
        from lib.daily_report_rollup import rollup_today as _rollup_today
        dr_today = await _rollup_today(db, project_numbers=nums or None)
        loads_today_dr_out = int(dr_today.get("loads", {}).get("out") or 0)
        loads_today_dr_in = int(dr_today.get("loads", {}).get("in") or 0)
        # Combined live count: dispatch_assignments completions + DR-
        # recorded outbound loads. Reported separately under
        # `loads_today_breakdown` for full transparency to consumers.
        loads_today = int(loads_today_dispatch) + loads_today_dr_out

        return {
            "ok": True,
            "as_of": _now_iso(),
            "project_number_filter": project_number,
            "scoped_projects": nums or "all",
            "counts": {
                "equipment_assigned": int(equipment_assigned),
                "trucks_assigned": len(trucks),
                "drivers_assigned": len(drivers),
                "trailers_assigned": len(trailers),
                "road_plates_assigned": int(road_plates_assigned),
                "specialty_assets_assigned": int(specialty_assets_assigned),
                "specialty_by_family": specialty_by_family,
                "active_assignments": int(active_assns),
                "active_hauls": int(active_hauls),
                "loads_today": int(loads_today),
                "loads_today_breakdown": {
                    "dispatch_haul_cycles": int(loads_today_dispatch),
                    "daily_report_outbound": int(loads_today_dr_out),
                    "daily_report_inbound": int(loads_today_dr_in),
                },
                "defects_open": int(defects_open),
                "incidents_open": int(incidents_open),
                "capas_open": int(capas_open),
                "materials_in_today": int(materials_in),
                "materials_out_today": int(materials_out),
            },
            "integration_readiness": {
                "fleetwatcher": "not_connected",
                "maintainx": "not_connected",
            },
        }

    # ────────────────────────────────────────────────────────────
    # /resources — Section 1
    # ────────────────────────────────────────────────────────────
    @router.get("/resources")
    async def resources(
        actor=Depends(require_pm_or_admin_dep),
        project_number: Optional[str] = Query(default=None),
        kind: Optional[str] = Query(default=None,
            description="filter to one of: equipment|truck|trailer|road_plate|safety|support"),
        limit: int = Query(default=1000, ge=1, le=5000),
    ) -> Dict[str, Any]:
        scope = await _scope(actor)
        nums = await _pm_scope_project_numbers(scope, project_number)
        if not scope.is_admin and not nums:
            return {"ok": True, "rows": [], "counts_by_kind": {}, "as_of": _now_iso()}

        em_q: Dict[str, Any] = {"$or": [
            {"is_active": {"$ne": False}}, {"active": {"$ne": False}},
        ]}
        if nums:
            em_q["current_project_number"] = {"$in": nums}

        # Active assignments per truck (for live driver/job binding)
        assn_q = {"current_state": {"$nin": list(DLS.TERMINAL_STATES)},
                  "cancelled_at": None}
        if nums:
            assn_q["project_number"] = {"$in": nums}
        assn_by_truck: Dict[str, Dict[str, Any]] = {}
        async for a in db.dispatch_assignments.find(assn_q, {"_id": 0}):
            t = a.get("truck_id")
            if t and t not in assn_by_truck:
                assn_by_truck[str(t)] = a

        # Open defects per unit
        defects_by_unit: Dict[str, int] = {}
        async for d in db.fleet_defects.find(
            {"status": {"$in": ["open", "acknowledged"]}},
            {"_id": 0, "truck_unit_number": 1},
        ):
            u = d.get("truck_unit_number")
            if u: defects_by_unit[str(u)] = defects_by_unit.get(str(u), 0) + 1

        rows: List[Dict[str, Any]] = []
        counts_by_kind: Dict[str, int] = {}
        async for em in db.equipment_master.find(em_q, {"_id": 0}).limit(int(limit)):
            unit = em.get("unit_number") or em.get("asset_number")
            if not unit:
                continue
            asset_kind = _classify_asset_kind(em)
            if kind and kind != asset_kind:
                # also allow shorthand
                if not (kind == "equipment" and asset_kind not in {"truck", "trailer", "road_plate", "safety"}):
                    continue
            counts_by_kind[asset_kind] = counts_by_kind.get(asset_kind, 0) + 1
            a = assn_by_truck.get(str(unit))
            map_ready = _map_ready(
                asset_id=em.get("id") or em.get("asset_id"),
                project_id=em.get("current_project_id"),
                project_number=em.get("current_project_number") or (a or {}).get("project_number"),
                assignment_id=(a or {}).get("id"),
                status=em.get("status") or em.get("asset_status") or "unknown",
                location_ref=em.get("current_location") or em.get("yard"),
                timestamp=em.get("updated_at") or em.get("last_modified_at"),
                operational_state=(a or {}).get("current_state") or "no_assignment",
                trust_state=("active_haul" if a else "no_assignment"),
                source_system="asset_spine",
            )
            rows.append({
                "unit_number": unit,
                "asset_kind": asset_kind,
                "make_model": em.get("make_model") or em.get("model"),
                "current_driver_name": (a or {}).get("driver_name") or "no_driver",
                "assigned_crew": em.get("assigned_crew") or "no_crew",
                "last_activity_at": (a or {}).get("last_transition_at")
                    or em.get("updated_at") or "no_recent_activity",
                "open_defect_count": defects_by_unit.get(str(unit), 0),
                "dvir_status": "no_recent_activity",  # joined separately by 4B UI
                "inspection_status": "no_recent_activity",
                "fleetwatcher": _fleetwatcher_tpl(),
                "maintainx": _maintainx_tpl(),
                **map_ready,
            })

        return {"ok": True, "as_of": _now_iso(),
                "project_number_filter": project_number,
                "rows": rows, "counts_by_kind": counts_by_kind}

    # ────────────────────────────────────────────────────────────
    # /hauls — Section 2
    # ────────────────────────────────────────────────────────────
    @router.get("/hauls")
    async def hauls(
        actor=Depends(require_pm_or_admin_dep),
        project_number: Optional[str] = Query(default=None),
        limit: int = Query(default=500, ge=1, le=2000),
    ) -> Dict[str, Any]:
        scope = await _scope(actor)
        nums = await _pm_scope_project_numbers(scope, project_number)
        if not scope.is_admin and not nums:
            return {"ok": True, "rows": [], "as_of": _now_iso()}
        q = {"current_state": {"$nin": list(DLS.TERMINAL_STATES)},
             "cancelled_at": None}
        if nums:
            q["project_number"] = {"$in": nums}
        rows: List[Dict[str, Any]] = []
        async for a in db.dispatch_assignments.find(q, {"_id": 0}).sort("assigned_at", -1).limit(int(limit)):
            rows.append({
                "truck_id": a.get("truck_id") or "no_truck",
                "driver_name": a.get("driver_name") or "no_driver",
                "material": a.get("material") or a.get("liquid_product"),
                "source": a.get("source_location") or a.get("pickup_location"),
                "destination": a.get("destination") or a.get("dropoff_location"),
                "current_state": a.get("current_state"),
                "cycle_count": a.get("load_count") or 0,
                "waiting_plant": (a.get("current_state") == DLS.WAITING and "PLANT" in (a.get("current_wait_reason") or "").upper()),
                "waiting_dump": (a.get("current_state") == DLS.WAITING and any(k in (a.get("current_wait_reason") or "").upper() for k in ("DUMP", "SITE"))),
                "breakdown_impact": a.get("current_state") == DLS.BREAKDOWN,
                "last_activity_at": a.get("last_transition_at"),
                "fleetwatcher": _fleetwatcher_tpl(),
                "source_system": "dispatch_lifecycle",
                **_map_ready(
                    asset_id=a.get("truck_id"),
                    project_number=a.get("project_number"),
                    assignment_id=a.get("id"),
                    status=a.get("current_state"),
                    timestamp=a.get("last_transition_at"),
                    operational_state=a.get("current_state"),
                    trust_state=("breakdown" if a.get("current_state") == DLS.BREAKDOWN
                                  else "active_haul"),
                    source_system="dispatch_lifecycle",
                ),
            })

        # TRACK 15.62 · K-HAUL-1 · UNION Daily-Report outbound rows.
        # Foreman-authored "11 loads of Dirt to 415 yard" entries were
        # entirely missing from this tab (the 15.61 P0 finding). They
        # are now surfaced alongside dispatch-lifecycle rows with a
        # distinct `source_system` so consumers can choose to filter.
        # Bound to last 14 days to keep payload size reasonable; the
        # forensic harness confirms the 60-day corpus has only 4 rows
        # globally, so 14 days is amply generous.
        dr_cutoff = (datetime.now(timezone.utc).date() - timedelta(days=14)).isoformat()
        dr_q: Dict[str, Any] = {"report_date": {"$gte": dr_cutoff},
                                 "deleted_at": {"$in": [None, "", False]},
                                 "outbound_materials.0": {"$exists": True}}
        if nums: dr_q["project_number"] = {"$in": nums}
        async for d in db.daily_reports.find(apply_synthetic_dr_exclusion(dr_q),
            {"_id": 0, "id": 1, "doc_id": 1, "report_date": 1, "project_number": 1,
             "outbound_materials": 1}):
            for m in (d.get("outbound_materials") or []):
                if not isinstance(m, dict):
                    continue
                rows.append({
                    "truck_id": (m.get("hauler") or "no_truck"),
                    "driver_name": "(daily-report)",
                    "material": m.get("material"),
                    "source": d.get("project_number"),
                    "destination": m.get("destination"),
                    "current_state": "RECORDED",
                    "cycle_count": int(m.get("quantity") or 0) if str(m.get("quantity") or "").strip() else 0,
                    "unit": m.get("unit"),
                    "ticket_or_manifest": m.get("ticket_or_manifest"),
                    "report_date": d.get("report_date"),
                    "daily_report_id": d.get("id"),
                    "daily_report_doc_id": d.get("doc_id"),
                    "source_system": "daily_reports",
                    "waiting_plant": False,
                    "waiting_dump": False,
                    "breakdown_impact": False,
                    "fleetwatcher": _fleetwatcher_tpl(),
                    **_map_ready(
                        project_number=d.get("project_number"),
                        status="recorded",
                        timestamp=d.get("report_date"),
                        trust_state="material_out",
                        source_system="daily_reports",
                    ),
                })
        return {"ok": True, "as_of": _now_iso(),
                "project_number_filter": project_number, "rows": rows}

    # ────────────────────────────────────────────────────────────
    # /materials — Section 3
    # ────────────────────────────────────────────────────────────
    @router.get("/materials")
    async def materials(
        actor=Depends(require_pm_or_admin_dep),
        project_number: Optional[str] = Query(default=None),
        days: int = Query(default=7, ge=1, le=90),
    ) -> Dict[str, Any]:
        scope = await _scope(actor)
        nums = await _pm_scope_project_numbers(scope, project_number)
        if not scope.is_admin and not nums:
            return {"ok": True, "as_of": _now_iso(), "rows": [],
                    "totals": {"deliveries": 0, "removals": 0, "hauls": 0}}
        cutoff = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
        dr_q: Dict[str, Any] = {"report_date": {"$gte": cutoff},
                                 "deleted_at": {"$in": [None, "", False]}}
        if nums: dr_q["project_number"] = {"$in": nums}
        rows: List[Dict[str, Any]] = []
        deliveries = 0
        removals = 0
        async for d in db.daily_reports.find(apply_synthetic_dr_exclusion(dr_q),
            {"_id": 0, "report_date": 1, "project_number": 1,
             "materials": 1, "outbound_materials": 1}):
            for m in (d.get("materials") or []):
                deliveries += 1
                rows.append({
                    "report_date": d.get("report_date"),
                    "direction": "in",
                    # TRACK 15.62 · K-MM-1 bug fix — production rows store
                    # the material name on the `material` key, not `type`
                    # or `name`. The 15.61 audit proved this was returning
                    # null for every Daily-Report-sourced row.
                    "material": (m or {}).get("material") or (m or {}).get("type") or (m or {}).get("name"),
                    "quantity": (m or {}).get("quantity"),
                    "unit": (m or {}).get("unit"),
                    "source": (m or {}).get("source") or (m or {}).get("supplier"),
                    "destination": (m or {}).get("destination") or d.get("project_number"),
                    "estimated_quantity": (m or {}).get("quantity"),
                    "actual_quantity": (m or {}).get("actual_quantity"),
                    **_map_ready(project_number=d.get("project_number"),
                                  status="delivered", trust_state="material_in",
                                  timestamp=d.get("report_date"),
                                  source_system="daily_reports"),
                })
            for m in (d.get("outbound_materials") or []):
                removals += 1
                rows.append({
                    "report_date": d.get("report_date"),
                    "direction": "out",
                    "material": (m or {}).get("material") or (m or {}).get("type") or (m or {}).get("name"),
                    "quantity": (m or {}).get("quantity"),
                    "unit": (m or {}).get("unit"),
                    "hauler": (m or {}).get("hauler"),
                    "source": d.get("project_number"),
                    "destination": (m or {}).get("destination"),
                    "estimated_quantity": (m or {}).get("quantity"),
                    "actual_quantity": (m or {}).get("actual_quantity"),
                    **_map_ready(project_number=d.get("project_number"),
                                  status="removed", trust_state="material_out",
                                  timestamp=d.get("report_date"),
                                  source_system="daily_reports"),
                })
        hc_q: Dict[str, Any] = {"completed_at": {"$gte": cutoff}}
        if nums: hc_q["project_number"] = {"$in": nums}
        hauls_count = await db.haul_cycles.count_documents(hc_q)
        return {"ok": True, "as_of": _now_iso(),
                "project_number_filter": project_number, "rows": rows,
                "totals": {"deliveries": deliveries, "removals": removals,
                            "hauls": int(hauls_count)}}

    # ────────────────────────────────────────────────────────────
    # /shop-impact — Section 4
    # ────────────────────────────────────────────────────────────
    @router.get("/shop-impact")
    async def shop_impact(
        actor=Depends(require_pm_or_admin_dep),
        project_number: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        scope = await _scope(actor)
        nums = await _pm_scope_project_numbers(scope, project_number)
        if not scope.is_admin and not nums:
            return {"ok": True, "as_of": _now_iso(), "rows": [],
                    "counts": {"oos": 0, "open_defects": 0, "maintenance_holds": 0}}
        impacted_units: set = set()
        if nums:
            async for a in db.dispatch_assignments.find(
                {"project_number": {"$in": nums}},
                {"_id": 0, "truck_id": 1},
            ):
                if a.get("truck_id"): impacted_units.add(a["truck_id"])
        defects_q: Dict[str, Any] = {"status": {"$in": ["open", "acknowledged"]}}
        if impacted_units:
            defects_q["truck_unit_number"] = {"$in": list(impacted_units)}
        rows: List[Dict[str, Any]] = []
        open_defects = 0
        async for d in db.fleet_defects.find(defects_q, {"_id": 0}):
            open_defects += 1
            rows.append({
                "unit_number": d.get("truck_unit_number"),
                "severity": d.get("severity"),
                "item_text": d.get("item_text"),
                "category": d.get("category"),
                "reported_at": d.get("reported_at"),
                "status": d.get("status"),
                "maintainx": _maintainx_tpl(),
                **_map_ready(asset_id=d.get("truck_unit_number"),
                              status=d.get("status"),
                              timestamp=d.get("reported_at"),
                              trust_state="failed_dvir" if d.get("kind") == "dvir" else "open_defect",
                              source_system="fleet_defects"),
            })
        oos = await db.equipment_master.count_documents({
            "status": {"$in": ["Out of Service", "Down", "Maintenance Hold"]},
            **({"current_project_number": {"$in": nums}} if nums else {}),
        })
        return {"ok": True, "as_of": _now_iso(),
                "project_number_filter": project_number,
                "rows": rows,
                "counts": {"oos": int(oos), "open_defects": open_defects,
                            "maintenance_holds": 0}}

    # ────────────────────────────────────────────────────────────
    # /safety-impact — Section 5
    # ────────────────────────────────────────────────────────────
    @router.get("/safety-impact")
    async def safety_impact(
        actor=Depends(require_pm_or_admin_dep),
        project_number: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        scope = await _scope(actor)
        nums = await _pm_scope_project_numbers(scope, project_number)
        if not scope.is_admin and not nums:
            return {"ok": True, "as_of": _now_iso(),
                    "incidents": [], "capas": [],
                    "counts": {"incidents": 0, "capas": 0}}
        inc_q: Dict[str, Any] = {"resolution_status": {"$ne": "Closed"}}
        if nums: inc_q["project_number"] = {"$in": nums}
        capa_q: Dict[str, Any] = {"status": {"$nin": ["Completed", "Closed", "Cancelled"]}}
        if nums: capa_q["project_number"] = {"$in": nums}
        incidents: List[Dict[str, Any]] = []
        async for i in db.incidents.find(inc_q, {"_id": 0}).limit(200):
            incidents.append({
                "incident_id": i.get("id"),
                "summary": i.get("summary"),
                "severity": i.get("severity"),
                "occurred_at": i.get("occurred_at"),
                "resolution_status": i.get("resolution_status"),
                **_map_ready(project_number=i.get("project_number"),
                              status=i.get("resolution_status"),
                              timestamp=i.get("occurred_at"),
                              trust_state="incident_open",
                              source_system="incidents"),
            })
        capas: List[Dict[str, Any]] = []
        async for c in db.corrective_actions.find(capa_q, {"_id": 0}).limit(200):
            capas.append({
                "capa_id": c.get("id"),
                "summary": c.get("summary") or c.get("description"),
                "status": c.get("status"),
                "due_at": c.get("due_at"),
                **_map_ready(project_number=c.get("project_number"),
                              status=c.get("status"),
                              timestamp=c.get("due_at"),
                              trust_state="capa_open",
                              source_system="corrective_actions"),
            })
        return {"ok": True, "as_of": _now_iso(),
                "project_number_filter": project_number,
                "incidents": incidents, "capas": capas,
                "counts": {"incidents": len(incidents), "capas": len(capas)}}

    # ────────────────────────────────────────────────────────────
    # /timeline — Section 6
    # ────────────────────────────────────────────────────────────
    @router.get("/timeline")
    async def timeline(
        actor=Depends(require_pm_or_admin_dep),
        project_number: Optional[str] = Query(default=None),
        days: int = Query(default=7, ge=1, le=90),
        limit: int = Query(default=300, ge=1, le=1000),
    ) -> Dict[str, Any]:
        scope = await _scope(actor)
        nums = await _pm_scope_project_numbers(scope, project_number)
        if not scope.is_admin and not nums:
            return {"ok": True, "as_of": _now_iso(), "events": []}
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        events: List[Dict[str, Any]] = []

        # Asset transfers
        try:
            xt_q: Dict[str, Any] = {"created_at": {"$gte": cutoff}}
            if nums:
                xt_q["$or"] = [{"to_project_number": {"$in": nums}},
                                {"from_project_number": {"$in": nums}}]
            async for t in db.asset_transfers.find(xt_q, {"_id": 0}).limit(limit):
                events.append({
                    "kind": "asset_transfer",
                    "timestamp": t.get("created_at"),
                    "summary": f"{t.get('kind') or 'TRANSFER'} · {t.get('unit_number') or t.get('asset_id')}",
                    **_map_ready(asset_id=t.get("asset_id"),
                                  project_number=t.get("to_project_number") or t.get("from_project_number"),
                                  timestamp=t.get("created_at"),
                                  trust_state="asset_transfer",
                                  source_system="asset_transfers"),
                })
        except Exception as _exc:  # noqa: BLE001
            logger.warning("[ops-feed] source skipped: %s", _exc)

        # Dispatch state events
        try:
            de_q: Dict[str, Any] = {"recorded_at": {"$gte": cutoff}}
            if nums:
                de_q["project_number"] = {"$in": nums}
            async for e in db.dispatch_state_events.find(de_q, {"_id": 0}).sort("recorded_at", -1).limit(limit):
                events.append({
                    "kind": "dispatch_state",
                    "timestamp": e.get("recorded_at"),
                    "summary": f"{e.get('to_state')} · {e.get('truck_id') or e.get('driver_name') or 'haul'}",
                    **_map_ready(asset_id=e.get("truck_id"),
                                  assignment_id=e.get("assignment_id"),
                                  project_number=e.get("project_number"),
                                  status=e.get("to_state"),
                                  timestamp=e.get("recorded_at"),
                                  trust_state="dispatch_state_event",
                                  source_system="dispatch_state_events"),
                })
        except Exception as _exc:  # noqa: BLE001
            logger.warning("[ops-feed] source skipped: %s", _exc)

        # Incidents
        try:
            inc_q: Dict[str, Any] = {"occurred_at": {"$gte": cutoff}}
            if nums: inc_q["project_number"] = {"$in": nums}
            async for i in db.incidents.find(inc_q, {"_id": 0}).limit(limit):
                events.append({
                    "kind": "incident",
                    "timestamp": i.get("occurred_at"),
                    "summary": i.get("summary") or "incident",
                    **_map_ready(project_number=i.get("project_number"),
                                  status=i.get("resolution_status"),
                                  timestamp=i.get("occurred_at"),
                                  trust_state="incident",
                                  source_system="incidents"),
                })
        except Exception as _exc:  # noqa: BLE001
            logger.warning("[ops-feed] source skipped: %s", _exc)

        events.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
        events = events[:limit]
        return {"ok": True, "as_of": _now_iso(),
                "project_number_filter": project_number,
                "events": events}

    # ════════════════════════════════════════════════════════════════
    # Track 13.6F · Phase 3 — PM-2 · Unified Holds Aggregation Engine
    # ════════════════════════════════════════════════════════════════
    # Aggregates REAL existing hold engines into one PM-scoped surface.
    # No new collections. No invented data. Every row traces to a real
    # source and points to the real PM-facing workflow route.
    #
    # Sources (real, currently-existing engines only):
    #   • equipment_master.status ∈ {Maintenance Hold, Safety Hold,
    #       Out of Service, Down}             →  /pm/fleet
    #   • operational_constraints.status ∈ {open, monitoring}
    #       scoped via project_id → jobs_master.id  →  /constraints
    #   • fleet_defects.status ∈ {open, acknowledged}
    #       on trucks bound to PM-scoped projects   →  /pm/fleet
    #
    # Doctrine:
    #   - PM scope preserved via compute_pm_scope (project_number set).
    #   - Empty PM scope → empty rows, never all-data leak.
    #   - source_system on every row preserves trace-back.
    #   - destination_path on every row preserves "real workflow open".
    # ────────────────────────────────────────────────────────────
    @router.get("/holds")
    async def unified_holds(
        actor=Depends(require_pm_or_admin_dep),
        project_number: Optional[str] = Query(default=None),
        limit: int = Query(default=300, ge=1, le=1000),
    ) -> Dict[str, Any]:
        scope = await _scope(actor)
        nums = await _pm_scope_project_numbers(scope, project_number)
        empty_payload = {
            "ok": True,
            "as_of": _now_iso(),
            "project_number_filter": project_number,
            "scoped_projects": [] if (not scope.is_admin) else "all",
            "counts": {
                "total": 0,
                "equipment_holds": 0,
                "constraint_holds": 0,
                "fleet_defects": 0,
            },
            "rows": [],
        }
        if not scope.is_admin and not nums:
            return empty_payload

        now = datetime.now(timezone.utc)
        rows: List[Dict[str, Any]] = []
        equipment_count = 0
        constraint_count = 0
        defect_count = 0

        # ── 1. Equipment holds ──────────────────────────────────────
        EQUIPMENT_HOLD_STATUSES = [
            "Maintenance Hold", "Safety Hold",
            "Out of Service", "Down",
        ]
        em_q: Dict[str, Any] = {"status": {"$in": EQUIPMENT_HOLD_STATUSES}}
        if nums:
            em_q["current_project_number"] = {"$in": nums}
        async for em in db.equipment_master.find(em_q, {"_id": 0}).limit(int(limit)):
            opened_at = em.get("updated_at") or em.get("last_modified_at") or em.get("created_at")
            em_id = em.get("id") or em.get("asset_id") or em.get("unit_number")
            unit = em.get("unit_number") or em.get("asset_id") or em_id
            # Deep-link: /pm/fleet with focus params so the page can
            # auto-select / scroll-to the exact unit.
            dest_path = f"/pm/fleet?focus_unit={_urlq(unit)}&focus_asset_id={_urlq(em_id)}"
            rows.append({
                "kind": "equipment_hold",
                "id": em_id,
                "source": "equipment_master",
                # ── Track 13.6G · canonical drill fields ─────────────
                "source_engine": "equipment_master",
                "source_id": em_id,
                "destination_path": dest_path,
                "destination_label": f"Open {unit}" if unit else "Open equipment",
                # ── Track 13.6H · SLA chip (operational truth) ───────
                "sla_label": _sla_label_hold(opened_at, now),
                # ────────────────────────────────────────────────────
                "title": f"{unit or 'Equipment'} · {em.get('status')}",
                "subtitle": (em.get("make_model") or em.get("model")
                             or em.get("type") or em.get("asset_type") or "Equipment"),
                "severity": "high" if em.get("status") == "Safety Hold" else "medium",
                "project_number": em.get("current_project_number"),
                "opened_at": opened_at,
                "age_days": _age_days(opened_at, now),
                "status": em.get("status"),
                **_map_ready(
                    asset_id=em_id,
                    project_number=em.get("current_project_number"),
                    status=em.get("status"),
                    timestamp=opened_at,
                    trust_state="equipment_hold",
                    source_system="equipment_master",
                ),
            })
            equipment_count += 1

        # ── 2. Operational constraints ──────────────────────────────
        # Scope: scope.project_numbers → jobs_master.id list → project_id
        constraint_status_filter = {"$in": ["open", "monitoring"]}
        if scope.is_admin and not project_number:
            # Admin · no project filter — pull everything.
            con_q: Dict[str, Any] = {"status": constraint_status_filter}
            async for c in db.operational_constraints.find(con_q, {"_id": 0}) \
                    .sort("created_at", -1).limit(int(limit)):
                created = c.get("created_at")
                rows.append(_constraint_row(c, created, now))
                constraint_count += 1
        else:
            # Resolve project_id list from scoped project_numbers.
            scoped_pn = nums if nums else ([project_number] if project_number else [])
            if scoped_pn:
                project_ids: List[str] = []
                project_id_to_pn: Dict[str, str] = {}
                async for j in db.jobs_master.find(
                    {"project_number": {"$in": scoped_pn}, "deleted_at": {"$in": [None, ""]}},
                    {"_id": 0, "id": 1, "project_number": 1},
                ):
                    j_id = j.get("id")
                    j_pn = j.get("project_number")
                    if j_id:
                        project_ids.append(j_id)
                        if j_pn:
                            project_id_to_pn[j_id] = j_pn
                if project_ids:
                    con_q = {
                        "status": constraint_status_filter,
                        "project_id": {"$in": project_ids},
                    }
                    async for c in db.operational_constraints.find(con_q, {"_id": 0}) \
                            .sort("created_at", -1).limit(int(limit)):
                        created = c.get("created_at")
                        rows.append(_constraint_row(c, created, now,
                                                     project_id_to_pn=project_id_to_pn))
                        constraint_count += 1

        # ── 3. Fleet defects on PM-impacted trucks ──────────────────
        # Filter is in effect when caller is a PM OR admin passed a
        # project_number — in either case, defects must be narrowed to
        # the trucks impacted by the scoped projects.
        filter_in_effect = (not scope.is_admin) or bool(project_number)
        impacted_trucks: set = set()
        if filter_in_effect:
            scoped_pn = nums if nums else ([project_number] if project_number else [])
            if scoped_pn:
                async for a in db.dispatch_assignments.find(
                    {"project_number": {"$in": scoped_pn}},
                    {"_id": 0, "truck_id": 1},
                ):
                    if a.get("truck_id"):
                        impacted_trucks.add(str(a["truck_id"]))
        defect_q: Optional[Dict[str, Any]] = {
            "status": {"$in": ["open", "acknowledged"]},
        }
        if filter_in_effect:
            if impacted_trucks:
                defect_q["truck_unit_number"] = {"$in": list(impacted_trucks)}
            else:
                # Filter in effect but zero impacted trucks → no rows.
                defect_q = None
        if defect_q is not None:
            async for d in db.fleet_defects.find(defect_q, {"_id": 0}).limit(int(limit)):
                opened_at = d.get("reported_at") or d.get("created_at")
                d_id = d.get("id") or ""
                truck = d.get("truck_unit_number") or ""
                dest_path = (
                    f"/pm/fleet?focus_defect_id={_urlq(d_id)}"
                    + (f"&focus_unit={_urlq(truck)}" if truck else "")
                )
                rows.append({
                    "kind": "fleet_defect",
                    "id": d_id,
                    "source": "fleet_defects",
                    # ── Track 13.6G · canonical drill fields ─────────
                    "source_engine": "fleet_defects",
                    "source_id": d_id,
                    "destination_path": dest_path,
                    "destination_label": (
                        f"Open defect on {truck}" if truck else "Open defect"
                    ),
                    # ── Track 13.6H · SLA chip ──────────────────────
                    "sla_label": _sla_label_hold(opened_at, now),
                    # ────────────────────────────────────────────────
                    "title": f"{truck or 'Truck'} · {d.get('item_text') or 'defect'}",
                    "subtitle": d.get("category") or "fleet defect",
                    "severity": (d.get("severity") or "medium").lower(),
                    "project_number": None,
                    "opened_at": opened_at,
                    "age_days": _age_days(opened_at, now),
                    "status": d.get("status"),
                    **_map_ready(
                        asset_id=truck or None,
                        status=d.get("status"),
                        timestamp=opened_at,
                        trust_state="open_defect",
                        source_system="fleet_defects",
                    ),
                })
                defect_count += 1

        # Newest-first overall.
        rows.sort(key=lambda r: r.get("opened_at") or "", reverse=True)
        rows = rows[: int(limit)]

        # ── Track 13.6I · Phase 1 — oldest-age secondary metric ─────
        # Pure derivation from real opened_at timestamps already on each row.
        def _max_age(kind: str) -> int:
            ages = [r.get("age_days") or 0 for r in rows if r.get("kind") == kind]
            return max(ages) if ages else 0
        oldest = {
            "equipment_holds": _max_age("equipment_hold"),
            "constraint_holds": _max_age("constraint"),
            "fleet_defects": _max_age("fleet_defect"),
            "total": max((r.get("age_days") or 0) for r in rows) if rows else 0,
        }
        oldest_labels = {
            k: (f"Oldest Held {v} Days" if v > 1
                else ("Oldest Held 1 Day" if v == 1
                      else ("Held Today" if (rows and k != "total"
                                              and any(r.get("kind", "").startswith(k.rstrip("s")) for r in rows))
                            else "")))
            for k, v in oldest.items()
        }

        return {
            "ok": True,
            "as_of": _now_iso(),
            "project_number_filter": project_number,
            "scoped_projects": nums if (not scope.is_admin or nums) else "all",
            "counts": {
                "total": len(rows),
                "equipment_holds": equipment_count,
                "constraint_holds": constraint_count,
                "fleet_defects": defect_count,
            },
            "oldest_age_days": oldest,
            "oldest_age_label": oldest_labels,
            "rows": rows,
        }

    # ════════════════════════════════════════════════════════════════
    # Track 13.6F · Phase 4 — PM-3 · Due Today Aggregation Engine
    # ════════════════════════════════════════════════════════════════
    # Aggregates items with a REAL existing due date / expiration /
    # required-submission date matching today (UTC) from real engines.
    # No invented urgency. No invented deadlines.
    #
    # Sources (real, currently-existing fields only):
    #   • corrective_actions.due_date == today AND status not closed
    #       →  /pm/incidents?tab=capas
    #   • daily_reports.report_date == today AND
    #       lifecycle_state == 'PENDING_REVIEW'  →  /pm/daily
    #
    # Project-centric scoping. PM with zero projects → empty rows.
    # ────────────────────────────────────────────────────────────
    @router.get("/due-today")
    async def due_today(
        actor=Depends(require_pm_or_admin_dep),
        project_number: Optional[str] = Query(default=None),
        limit: int = Query(default=300, ge=1, le=1000),
    ) -> Dict[str, Any]:
        scope = await _scope(actor)
        nums = await _pm_scope_project_numbers(scope, project_number)
        today_yyyymmdd = datetime.now(timezone.utc).date().isoformat()
        empty_payload = {
            "ok": True,
            "as_of": _now_iso(),
            "as_of_date": today_yyyymmdd,
            "project_number_filter": project_number,
            "scoped_projects": [] if (not scope.is_admin) else "all",
            "counts": {
                "total": 0,
                "capas_due_today": 0,
                "daily_reports_pending_today": 0,
            },
            "rows": [],
        }
        if not scope.is_admin and not nums:
            return empty_payload

        rows: List[Dict[str, Any]] = []
        capa_count = 0
        dr_count = 0

        # ── 1. CAPAs due today ───────────────────────────────────────
        ca_q: Dict[str, Any] = {
            "due_date": today_yyyymmdd,
            "status": {"$nin": ["Closed", "Completed", "Verified", "Cancelled"]},
        }
        if nums:
            ca_q["project_number"] = {"$in": nums}
        async for c in db.corrective_actions.find(ca_q, {"_id": 0}).limit(int(limit)):
            c_id = c.get("id") or ""
            # CAPAs anchor on the PM Incidents Dashboard (single
            # surface housing CAPAs) — pre-select with focus_capa.
            dest_path = f"/pm/incidents?tab=capas&focus_capa={_urlq(c_id)}"
            title = c.get("title") or c.get("summary") or "Corrective Action"
            rows.append({
                "kind": "capa",
                "id": c_id,
                "source": "corrective_actions",
                # ── Track 13.6G · canonical drill fields ─────────────
                "source_engine": "corrective_actions",
                "source_id": c_id,
                "destination_path": dest_path,
                "destination_label": f"Open CAPA · {title[:48]}",
                # ── Track 13.6H · SLA chip (real due_date) ──────────
                "sla_label": _sla_label_due(c.get("due_date")),
                # ────────────────────────────────────────────────────
                "title": title,
                "subtitle": (c.get("linked_employee_name") or c.get("employee_name")
                             or "Open corrective action"),
                "due_date": c.get("due_date"),
                "project_number": c.get("project_number") or None,
                "status": c.get("status"),
                **_map_ready(
                    project_number=c.get("project_number") or None,
                    status=c.get("status"),
                    timestamp=c.get("due_date"),
                    trust_state="capa_due_today",
                    source_system="corrective_actions",
                ),
            })
            capa_count += 1

        # ── 2. Daily reports pending review for today ────────────────
        dr_q: Dict[str, Any] = {
            "report_date": today_yyyymmdd,
            "lifecycle_state": "PENDING_REVIEW",
            "deleted_at": {"$in": [None, "", False]},
        }
        if nums:
            dr_q["project_number"] = {"$in": nums}
        async for d in db.daily_reports.find(apply_synthetic_dr_exclusion(dr_q), {"_id": 0}).limit(int(limit)):
            dr_id = d.get("id") or d.get("doc_id") or ""
            # /pm/daily/:id is a real React route — true one-click drill.
            dest_path = f"/pm/daily/{_urlq(dr_id)}" if dr_id else "/pm/daily"
            pn = d.get("project_number") or None
            rows.append({
                "kind": "daily_report_pending",
                "id": dr_id,
                "source": "daily_reports",
                # ── Track 13.6G · canonical drill fields ─────────────
                "source_engine": "daily_reports",
                "source_id": dr_id,
                "destination_path": dest_path,
                "destination_label": f"Open report · {pn or 'project'}",
                # ── Track 13.6H · SLA chip (real report_date) ───────
                "sla_label": _sla_label_due(today_yyyymmdd),
                # ────────────────────────────────────────────────────
                "title": f"Daily Report · {pn or 'project'}",
                "subtitle": (d.get("project_name") or d.get("foreman_name")
                             or "Awaiting PM verify"),
                "due_date": today_yyyymmdd,
                "project_number": pn,
                "status": d.get("lifecycle_state"),
                **_map_ready(
                    project_number=d.get("project_number"),
                    status=d.get("lifecycle_state"),
                    timestamp=d.get("report_date"),
                    trust_state="daily_report_pending_review",
                    source_system="daily_reports",
                ),
            })
            dr_count += 1

        return {
            "ok": True,
            "as_of": _now_iso(),
            "as_of_date": today_yyyymmdd,
            "project_number_filter": project_number,
            "scoped_projects": nums if (not scope.is_admin or nums) else "all",
            "counts": {
                "total": len(rows),
                "capas_due_today": capa_count,
                "daily_reports_pending_today": dr_count,
            },
            # ── Track 13.6I · Phase 1 — oldest-age secondary metric ─
            # All Due Today rows by definition fall today → label "Due Today".
            "oldest_age_label": {
                "capas_due_today": "Due Today" if capa_count else "",
                "daily_reports_pending_today": "Due Today" if dr_count else "",
                "total": "Due Today" if (capa_count or dr_count) else "",
            },
            "rows": rows,
        }

    return router


def _empty_overview(project_number: Optional[str]) -> Dict[str, Any]:
    return {
        "ok": True,
        "as_of": _now_iso(),
        "project_number_filter": project_number,
        "scoped_projects": [],
        "counts": {
            "equipment_assigned": 0, "trucks_assigned": 0,
            "drivers_assigned": 0, "trailers_assigned": 0,
            "road_plates_assigned": 0, "active_assignments": 0,
            "specialty_assets_assigned": 0,
            "specialty_by_family": {"trench_safety": 0, "access_protection": 0,
                                      "traffic_control": 0, "support": 0},
            "active_hauls": 0, "loads_today": 0, "defects_open": 0,
            "incidents_open": 0, "capas_open": 0,
            "materials_in_today": 0, "materials_out_today": 0,
        },
        "integration_readiness": {"fleetwatcher": "not_connected",
                                    "maintainx": "not_connected"},
    }


__all__ = ["build_pm_command_center_router", "normalize_asset_kind",
           "ROAD_PLATE_CANONICAL", "ROAD_PLATE_LEGACY_VALUES",
           "SPECIALTY_ASSET_FAMILY", "specialty_family_of",
           "is_specialty_asset"]
