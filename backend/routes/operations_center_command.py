"""
routes/operations_center_command.py · FORGEDOPS Operations Center · Phase 4C.

Cross-company command board. Composes (does NOT duplicate):

  - Asset Spine (canonical asset truth)
  - Dispatch Command Center aggregator (dispatch_lifecycle, fleet defects)
  - PM Command Center aggregator (project-scoped slices)
  - Shop Command Feed (defects, OOS, recovery)
  - Safety (incidents, corrective_actions)
  - Materials / Hauls (daily_reports, haul_cycles)
  - Motive (telematics → truck status summary)

10 endpoints under /api/operations-center/command/*:

  1.  /brief           Morning Operations Brief (single rollup tile)
  2.  /project-health  Project Health Board + risk engine (green/yellow/red)
  3.  /allocation      Resource allocation by project (trucks/equipment/
                       road plates/drivers + unassigned/over/oos/unmapped)
  4.  /conflicts       Operational conflicts (duplicate assignments, etc.)
  5.  /road-plates     Road Plate Command View (per-project + global)
  6.  /shop-impact     Shop impacts with production priority (high/med/low)
  7.  /safety-impact   Safety impacts with severity tier (critical/warning/info)
  8.  /telematics      Truck Status Summary (moving/idling/at-job/etc.)
  9.  /timeline        Cross-company operational timeline
 10.  /map-contract    Live operational rows w/ map-ready fields (future map)

Doctrine:
  - Read-only. No mutations. No new collection.
  - require_any_portal_token (any signed-in portal user); executive-mode
    is a UI-side filter, not a backend gate.
  - Road plates surfaced as first-class via the same canonical normalizer
    used by pm_command_center.py.
  - Map-ready field set on every operational row (preps FleetWatcher).
  - FleetWatcher / MaintainX = "not_connected" template.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, Query

from lib.synthetic_corrective_action_filter import apply_synthetic_corrective_action_exclusion
from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion
import dispatch_lifecycle as DLS
from routes.pm_command_center import (
    normalize_asset_kind, ROAD_PLATE_CANONICAL, _map_ready,
    specialty_family_of, is_specialty_asset, SPECIALTY_ASSET_FAMILY,
)

logger = logging.getLogger("operations_center_command")


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _start_of_utc_day() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _fleetwatcher_tpl() -> Dict[str, Any]:
    return {"connected": False, "status": "not_connected",
            "ticket_number": None, "tons": None, "loads": None}


def _maintainx_tpl() -> Dict[str, Any]:
    return {"connected": False, "status": "not_connected", "work_order_id": None}


# ── Shop production priority ───────────────────────────────────────
# Asset kinds that, when OOS / failed-DVIR, halt a crew's day.
HIGH_PRIORITY_KINDS = {
    "paving equipment", "paver", "mill", "milling", "milling machine",
    "dump trucks", "dump truck", "haul truck", "tractor trailer trucks",
    "tractor trailer truck", "excavators", "excavator", "loaders", "loader",
    "dozers", "dozer", "road graders", "road grader",
}
MEDIUM_PRIORITY_KINDS = {
    "pickup trucks", "pickup truck", "service trucks", "service truck",
    "flatbed trucks", "skid steers", "skid steer", "rollers", "roller",
    "compactors", "compactor", "sweepers", "water trucks", "water truck",
}


def _shop_priority(asset_kind: Optional[str], severity: Optional[str]) -> str:
    k = (asset_kind or "").lower()
    if k in HIGH_PRIORITY_KINDS:
        return "high"
    # Severity may bump priority up.
    sev = (severity or "").lower()
    if sev in ("critical", "high"):
        return "high"
    if k in MEDIUM_PRIORITY_KINDS:
        return "medium"
    if sev in ("medium", "moderate"):
        return "medium"
    return "low"


# ── Safety severity tier ───────────────────────────────────────────
def _safety_tier(item: Dict[str, Any]) -> str:
    sev = (item.get("severity") or "").lower()
    if sev in ("lost_time", "lost time", "critical", "fatality", "serious"):
        return "critical"
    status = (item.get("status") or item.get("resolution_status") or "").lower()
    if sev in ("warning", "moderate", "open") or status in ("open", "in progress"):
        return "warning"
    return "informational"


# ── Motive operational state classifier ────────────────────────────
def _motive_state(speed_mph: Optional[float], status: Optional[str],
                  last_seen_iso: Optional[str]) -> str:
    """Classify a truck's operational state from Motive raw fields. Best-
    effort — Motive coverage is partial; unknowns surface explicitly."""
    if not last_seen_iso:
        return "no_gps"
    try:
        ts = datetime.fromisoformat(last_seen_iso.replace("Z", "+00:00"))
        age_min = (datetime.now(timezone.utc) - ts).total_seconds() / 60.0
    except Exception:
        age_min = None
    if age_min is not None and age_min > 60:
        return "offline"
    s = (status or "").lower()
    if "drive" in s or "driving" in s:
        return "moving"
    if "idle" in s or "idling" in s:
        return "idling"
    if speed_mph is not None:
        try:
            spd = float(speed_mph)
            if spd >= 5:
                return "moving"
            if spd > 0:
                return "idling"
        except Exception:
            pass
    return "unknown"


# ════════════════════════════════════════════════════════════════════
# Router factory
# ════════════════════════════════════════════════════════════════════
def build_operations_center_command_router(
    db,
    require_any_portal_token_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    router = APIRouter(prefix="/api/operations-center/command",
                       tags=["operations-center-command"])

    # ─── 1 · /brief ─────────────────────────────────────────────────
    @router.get("/brief")
    async def brief(_actor: Dict[str, Any] = Depends(require_any_portal_token_dep)) -> Dict[str, Any]:
        """Morning Operations Brief — one-glance company-wide rollup."""
        day_start = _start_of_utc_day().isoformat()
        today = datetime.now(timezone.utc).date().isoformat()

        # Active projects
        active_projects = await db.jobs_master.count_documents({
            "$or": [{"is_active": {"$ne": False}}, {"active": {"$ne": False}}],
            "deleted_at": {"$in": [None, "", False]},
        })

        # Active assignments / hauls
        assn_q = {"current_state": {"$nin": list(DLS.TERMINAL_STATES)},
                  "cancelled_at": None}
        active_hauls = await db.dispatch_assignments.count_documents(assn_q)

        # Trucks / drivers / equipment from spine
        equipment_total = await db.equipment_master.count_documents(
            {"$or": [{"is_active": {"$ne": False}}, {"active": {"$ne": False}}]})
        trucks_total = 0
        road_plates_total = 0
        road_plates_deployed = 0
        specialty_assets_total = 0
        specialty_assets_deployed = 0
        async for em in db.equipment_master.find(
            {"$or": [{"is_active": {"$ne": False}}, {"active": {"$ne": False}}]},
            {"_id": 0, "type": 1, "asset_type": 1, "category": 1, "current_project_number": 1},
        ):
            raw = em.get("type") or em.get("asset_type") or em.get("category") or ""
            k = normalize_asset_kind(raw) or ""
            has_proj = bool(em.get("current_project_number"))
            if k in ("truck", "dump trucks", "dump truck", "haul truck",
                      "tractor trailer trucks", "service trucks", "flatbed trucks",
                      "pickup trucks", "water trucks", "misc trucks",
                      "supervisor / mgmt trucks"):
                trucks_total += 1
            if k == ROAD_PLATE_CANONICAL:
                road_plates_total += 1
                if has_proj: road_plates_deployed += 1
            if is_specialty_asset(k):
                specialty_assets_total += 1
                if has_proj: specialty_assets_deployed += 1

        drivers_assigned: Set[str] = set()
        async for a in db.dispatch_assignments.find(assn_q,
                                                     {"_id": 0, "driver_id": 1, "driver_name": 1}):
            if a.get("driver_id"): drivers_assigned.add(a["driver_id"])
            elif a.get("driver_name"): drivers_assigned.add(a["driver_name"])

        # OOS / shop impact
        oos_assets = await db.equipment_master.count_documents({
            "status": {"$in": ["Out of Service", "Down", "Maintenance Hold"]},
        })
        open_defects = await db.fleet_defects.count_documents(
            {"status": {"$in": ["open", "acknowledged"]}})

        # Safety
        incidents_open = await db.incidents.count_documents(
            {"resolution_status": {"$ne": "Closed"}})
        capas_open = await db.corrective_actions.count_documents(
            apply_synthetic_corrective_action_exclusion({"status": {"$nin": ["Completed", "Closed", "Cancelled"]}}))
        # Critical safety events — incidents with severity flagged critical/lost-time.
        critical_safety = await db.incidents.count_documents({
            "resolution_status": {"$ne": "Closed"},
            "severity": {"$in": ["Critical", "critical", "Lost Time", "lost_time", "Fatality"]},
        })

        # Materials today — TRACK 28.02B · apply synthetic-DR exclusion
        # so certification/smoke rows do not inflate the operator brief.
        materials_in = 0
        materials_out = 0
        async for d in db.daily_reports.find(
            apply_synthetic_dr_exclusion(
                {"report_date": today, "deleted_at": {"$in": [None, "", False]}}
            ),
            {"_id": 0, "materials": 1, "outbound_materials": 1},
        ):
            materials_in += len(d.get("materials") or [])
            materials_out += len(d.get("outbound_materials") or [])

        loads_today = await db.haul_cycles.count_documents({"completed_at": {"$gte": day_start}})

        # Conflict count quick proxy — driver double-bookings.
        conflicts_count = await _count_conflicts(db)

        return {
            "ok": True,
            "as_of": _now_iso(),
            "brief": {
                "active_projects": int(active_projects),
                "active_hauls": int(active_hauls),
                "trucks_active": int(trucks_total),
                "drivers_active": len(drivers_assigned),
                "equipment_active": int(equipment_total),
                "road_plates_total": int(road_plates_total),
                "road_plates_deployed": int(road_plates_deployed),
                "specialty_assets_total": int(specialty_assets_total),
                "specialty_assets_deployed": int(specialty_assets_deployed),
                "materials_in_today": int(materials_in),
                "materials_out_today": int(materials_out),
                "loads_today": int(loads_today),
                "open_shop_defects": int(open_defects),
                "oos_assets": int(oos_assets),
                "incidents_open": int(incidents_open),
                "capas_open": int(capas_open),
                "critical_safety_events": int(critical_safety),
                "resource_conflicts": int(conflicts_count),
            },
            "integration_readiness": {
                "fleetwatcher": "not_connected",
                "maintainx": "not_connected",
                "motive": "partial",
            },
        }

    # ─── 2 · /project-health ───────────────────────────────────────
    @router.get("/project-health")
    async def project_health(_actor: Dict[str, Any] = Depends(require_any_portal_token_dep)) -> Dict[str, Any]:
        """Project Health Board + risk engine (green/yellow/red)."""
        # Pull active projects
        proj_cursor = db.jobs_master.find(
            {"$or": [{"is_active": {"$ne": False}}, {"active": {"$ne": False}}],
              "deleted_at": {"$in": [None, "", False]}},
            {"_id": 0, "project_number": 1, "project_name": 1, "name": 1,
              "pm_name": 1, "pm_email": 1, "status": 1},
        )
        projects: List[Dict[str, Any]] = []
        pns: List[str] = []
        async for p in proj_cursor:
            pn = (p.get("project_number") or "").strip()
            if not pn:
                continue
            pns.append(pn)
            projects.append({
                "project_number": pn,
                "project_name": p.get("project_name") or p.get("name") or "",
                "pm_name": p.get("pm_name") or p.get("pm_email") or "",
                "status": p.get("status") or "active",
            })

        # Trucks / Equipment / road plates / specialty assets per project from spine
        em_counts: Dict[str, Dict[str, int]] = {pn: {"trucks": 0, "equipment": 0, "road_plates": 0, "specialty_assets": 0} for pn in pns}
        async for em in db.equipment_master.find(
            {"current_project_number": {"$in": pns}},
            {"_id": 0, "current_project_number": 1, "type": 1, "asset_type": 1, "category": 1},
        ):
            pn = em.get("current_project_number")
            if pn not in em_counts: continue
            raw = em.get("type") or em.get("asset_type") or em.get("category") or ""
            k = normalize_asset_kind(raw) or ""
            em_counts[pn]["equipment"] += 1
            if k == ROAD_PLATE_CANONICAL:
                em_counts[pn]["road_plates"] += 1
            if is_specialty_asset(k):
                em_counts[pn]["specialty_assets"] += 1
            if "truck" in k:
                em_counts[pn]["trucks"] += 1

        # Active hauls per project
        haul_counts: Dict[str, int] = {pn: 0 for pn in pns}
        assn_q = {"current_state": {"$nin": list(DLS.TERMINAL_STATES)},
                  "cancelled_at": None,
                  "project_number": {"$in": pns}}
        async for a in db.dispatch_assignments.find(assn_q, {"_id": 0, "project_number": 1}):
            pn = a.get("project_number")
            if pn in haul_counts: haul_counts[pn] += 1

        # Open defects per project (via truck mapping)
        defect_counts: Dict[str, int] = {pn: 0 for pn in pns}
        truck_to_proj: Dict[str, str] = {}
        async for a in db.dispatch_assignments.find(
            {"project_number": {"$in": pns}},
            {"_id": 0, "truck_id": 1, "project_number": 1},
        ):
            if a.get("truck_id") and a.get("project_number"):
                truck_to_proj.setdefault(a["truck_id"], a["project_number"])
        async for d in db.fleet_defects.find(
            {"status": {"$in": ["open", "acknowledged"]}},
            {"_id": 0, "truck_unit_number": 1},
        ):
            pn = truck_to_proj.get(d.get("truck_unit_number"))
            if pn in defect_counts:
                defect_counts[pn] += 1

        # OOS impacting project
        oos_counts: Dict[str, int] = {pn: 0 for pn in pns}
        async for em in db.equipment_master.find(
            {"current_project_number": {"$in": pns},
              "status": {"$in": ["Out of Service", "Down", "Maintenance Hold"]}},
            {"_id": 0, "current_project_number": 1},
        ):
            pn = em.get("current_project_number")
            if pn in oos_counts: oos_counts[pn] += 1

        # Incidents per project
        inc_counts: Dict[str, int] = {pn: 0 for pn in pns}
        async for i in db.incidents.find(
            {"resolution_status": {"$ne": "Closed"},
              "project_number": {"$in": pns}},
            {"_id": 0, "project_number": 1, "severity": 1},
        ):
            pn = i.get("project_number")
            if pn in inc_counts: inc_counts[pn] += 1

        # Risk engine: red if any critical signal, yellow if any minor.
        def _risk(row_pn: str) -> str:
            hauls = haul_counts.get(row_pn, 0)
            defects = defect_counts.get(row_pn, 0)
            oos = oos_counts.get(row_pn, 0)
            inc = inc_counts.get(row_pn, 0)
            if oos >= 2 or inc >= 1 or defects >= 5:
                return "red"
            if oos == 1 or defects >= 2 or (hauls == 0 and em_counts[row_pn]["trucks"] > 0):
                return "yellow"
            return "green"

        rows: List[Dict[str, Any]] = []
        for p in projects:
            pn = p["project_number"]
            risk = _risk(pn)
            rows.append({
                **p,
                "trucks_assigned": em_counts[pn]["trucks"],
                "equipment_assigned": em_counts[pn]["equipment"],
                "road_plates": em_counts[pn]["road_plates"],
                "specialty_assets": em_counts[pn]["specialty_assets"],
                "active_hauls": haul_counts.get(pn, 0),
                "open_defects": defect_counts.get(pn, 0),
                "oos_assets": oos_counts.get(pn, 0),
                "open_incidents": inc_counts.get(pn, 0),
                "risk": risk,
                **_map_ready(project_number=pn, status=p["status"],
                              trust_state=f"risk_{risk}",
                              source_system="jobs_master",
                              timestamp=_now_iso()),
            })

        # Sort red → yellow → green
        order = {"red": 0, "yellow": 1, "green": 2}
        rows.sort(key=lambda r: (order.get(r["risk"], 9), r["project_number"]))

        return {"ok": True, "as_of": _now_iso(), "rows": rows,
                 "counts": {"red": sum(1 for r in rows if r["risk"] == "red"),
                              "yellow": sum(1 for r in rows if r["risk"] == "yellow"),
                              "green": sum(1 for r in rows if r["risk"] == "green"),
                              "total": len(rows)}}

    # ─── 3 · /allocation ───────────────────────────────────────────
    @router.get("/allocation")
    async def allocation(_actor: Dict[str, Any] = Depends(require_any_portal_token_dep)) -> Dict[str, Any]:
        """Company-wide resource allocation buckets."""
        by_project: Dict[str, Dict[str, int]] = {}
        unassigned = {"trucks": 0, "equipment": 0, "road_plates": 0}
        oos = 0
        unmapped = 0
        async for em in db.equipment_master.find(
            {"$or": [{"is_active": {"$ne": False}}, {"active": {"$ne": False}}]},
            {"_id": 0, "current_project_number": 1, "type": 1, "asset_type": 1,
              "category": 1, "status": 1, "motive_truck_id": 1},
        ):
            pn = em.get("current_project_number")
            raw = em.get("type") or em.get("asset_type") or em.get("category") or ""
            k = normalize_asset_kind(raw) or ""
            kind = ("road_plate" if k == ROAD_PLATE_CANONICAL else
                    "truck" if "truck" in k else "equipment")
            if (em.get("status") or "") in ("Out of Service", "Down", "Maintenance Hold"):
                oos += 1
            if not em.get("motive_truck_id") and "truck" in k:
                unmapped += 1
            if pn:
                bucket = by_project.setdefault(pn, {"trucks": 0, "equipment": 0, "road_plates": 0})
                bucket[kind if kind in bucket else "equipment"] += 1
            else:
                unassigned[kind if kind in unassigned else "equipment"] += 1

        # Driver allocation (active assignments)
        drivers_by_project: Dict[str, Set[str]] = {}
        async for a in db.dispatch_assignments.find(
            {"current_state": {"$nin": list(DLS.TERMINAL_STATES)},
              "cancelled_at": None},
            {"_id": 0, "project_number": 1, "driver_id": 1, "driver_name": 1},
        ):
            pn = a.get("project_number") or "_unassigned"
            d = a.get("driver_id") or a.get("driver_name")
            if d:
                drivers_by_project.setdefault(pn, set()).add(d)

        rows: List[Dict[str, Any]] = []
        for pn, b in by_project.items():
            rows.append({
                "project_number": pn,
                "trucks": b["trucks"],
                "equipment": b["equipment"],
                "road_plates": b["road_plates"],
                "drivers": len(drivers_by_project.get(pn, set())),
                **_map_ready(project_number=pn, status="allocated",
                              trust_state="allocation_row",
                              source_system="equipment_master",
                              timestamp=_now_iso()),
            })
        rows.sort(key=lambda r: -(r["trucks"] + r["equipment"]))
        return {"ok": True, "as_of": _now_iso(),
                 "rows": rows,
                 "unassigned": unassigned,
                 "oos_assets": int(oos),
                 "unmapped_to_motive": int(unmapped)}

    # ─── 4 · /conflicts ────────────────────────────────────────────
    @router.get("/conflicts")
    async def conflicts(_actor: Dict[str, Any] = Depends(require_any_portal_token_dep)) -> Dict[str, Any]:
        rows = await _conflict_rows(db)
        return {"ok": True, "as_of": _now_iso(),
                 "rows": rows,
                 "counts": _conflict_count_buckets(rows)}

    # ─── 5 · /specialty-assets ─────────────────────────────────────
    # Phase 4C architecture correction (2026-02-10): renamed from
    # /road-plates. Road plates are ONE specialty asset kind among many
    # (trench boxes, arrow boards, generators, pumps, etc.). Frontend
    # may still drill into kind=road_plate via the `?family=` /
    # `?kind=` filters.
    @router.get("/specialty-assets")
    async def specialty_assets(
        _actor: Dict[str, Any] = Depends(require_any_portal_token_dep),
        family: Optional[str] = Query(default=None,
            description="Filter to family: trench_safety|access_protection|"
                          "traffic_control|support"),
        kind: Optional[str] = Query(default=None,
            description="Filter to a specific normalized kind, e.g. road_plate, trench_box."),
    ) -> Dict[str, Any]:
        """Specialty Asset Command — global + per-project + per-family.

        Surfaces every non-fleet, non-driver resource the company tracks
        (trench safety, access/protection, traffic control, support).
        Road plates are visible inside `access_protection`.
        """
        total = 0
        assigned = 0
        available = 0
        unassigned = 0
        per_project: Dict[str, int] = {}
        per_family: Dict[str, int] = {k: 0 for k in SPECIALTY_ASSET_FAMILY}
        per_kind: Dict[str, int] = {}
        rows: List[Dict[str, Any]] = []
        async for em in db.equipment_master.find(
            {"$or": [{"is_active": {"$ne": False}}, {"active": {"$ne": False}}]},
            {"_id": 0, "type": 1, "asset_type": 1, "category": 1,
              "current_project_number": 1, "current_project_id": 1,
              "unit_number": 1, "asset_number": 1, "id": 1, "asset_id": 1,
              "status": 1, "updated_at": 1, "current_location": 1, "yard": 1,
              "assigned_to_project_at": 1, "deployed_at": 1},
        ):
            raw = em.get("type") or em.get("asset_type") or em.get("category") or ""
            k = normalize_asset_kind(raw) or ""
            fam = specialty_family_of(k)
            if not fam:
                continue
            # Family / kind filters
            if family and fam != family:
                continue
            if kind and k != kind:
                continue
            total += 1
            per_family[fam] = per_family.get(fam, 0) + 1
            per_kind[k] = per_kind.get(k, 0) + 1
            pn = em.get("current_project_number")
            if pn:
                assigned += 1
                per_project[pn] = per_project.get(pn, 0) + 1
            else:
                if (em.get("status") or "") in ("Out of Service", "Down"):
                    unassigned += 1
                else:
                    available += 1
            rows.append({
                "unit_number": em.get("unit_number") or em.get("asset_number"),
                "asset_id": em.get("id") or em.get("asset_id"),
                "asset_kind": k,
                "family": fam,
                "project_number": pn,
                "status": em.get("status") or "available",
                "location": em.get("current_location") or em.get("yard"),
                "assigned_at": em.get("assigned_to_project_at") or em.get("deployed_at"),
                "last_activity_at": em.get("updated_at"),
                **_map_ready(
                    asset_id=em.get("id") or em.get("asset_id"),
                    project_number=pn,
                    status=em.get("status") or ("assigned" if pn else "available"),
                    location_ref=em.get("current_location") or em.get("yard"),
                    timestamp=em.get("updated_at"),
                    operational_state=("assigned" if pn else "available"),
                    trust_state=("specialty_assigned" if pn else "specialty_available"),
                    source_system="asset_spine",
                ),
            })
        per_project_rows = sorted(
            [{"project_number": k, "count": v} for k, v in per_project.items()],
            key=lambda r: -r["count"],
        )
        return {"ok": True, "as_of": _now_iso(),
                 "totals": {"total": total, "assigned": assigned,
                             "available": available, "unassigned": unassigned},
                 "by_family": per_family,
                 "by_kind": per_kind,
                 "by_project": per_project_rows,
                 "rows": rows,
                 # Backward-compat shim: road_plate count exposed at the
                 # top level so any legacy reader keeps working.
                 "road_plate_count": int(per_kind.get(ROAD_PLATE_CANONICAL, 0))}

    # ─── 6 · /shop-impact ──────────────────────────────────────────
    @router.get("/shop-impact")
    async def shop_impact(_actor: Dict[str, Any] = Depends(require_any_portal_token_dep)) -> Dict[str, Any]:
        # Build asset_kind lookup for priority classification.
        kind_by_unit: Dict[str, str] = {}
        async for em in db.equipment_master.find(
            {"$or": [{"is_active": {"$ne": False}}, {"active": {"$ne": False}}]},
            {"_id": 0, "unit_number": 1, "asset_number": 1,
              "type": 1, "asset_type": 1, "category": 1},
        ):
            unit = em.get("unit_number") or em.get("asset_number")
            if not unit: continue
            raw = em.get("type") or em.get("asset_type") or em.get("category") or ""
            kind_by_unit[str(unit)] = (normalize_asset_kind(raw) or "")

        rows: List[Dict[str, Any]] = []
        counts = {"high": 0, "medium": 0, "low": 0}
        async for d in db.fleet_defects.find(
            {"status": {"$in": ["open", "acknowledged"]}},
            {"_id": 0},
        ):
            unit = d.get("truck_unit_number")
            asset_kind = kind_by_unit.get(str(unit) if unit else "", "")
            pri = _shop_priority(asset_kind, d.get("severity"))
            counts[pri] += 1
            rows.append({
                "unit_number": unit,
                "asset_kind": asset_kind or "unknown",
                "severity": d.get("severity"),
                "category": d.get("category"),
                "item_text": d.get("item_text"),
                "reported_at": d.get("reported_at"),
                "status": d.get("status"),
                "production_priority": pri,
                "maintainx": _maintainx_tpl(),
                **_map_ready(asset_id=unit,
                              status=d.get("status"),
                              timestamp=d.get("reported_at"),
                              trust_state=f"shop_{pri}",
                              source_system="fleet_defects"),
            })
        oos = await db.equipment_master.count_documents(
            {"status": {"$in": ["Out of Service", "Down", "Maintenance Hold"]}})
        rows.sort(key=lambda r: {"high": 0, "medium": 1, "low": 2}.get(r["production_priority"], 9))
        return {"ok": True, "as_of": _now_iso(),
                 "rows": rows,
                 "counts": {**counts, "oos": int(oos), "total_open": sum(counts.values())}}

    # ─── 7 · /safety-impact ────────────────────────────────────────
    @router.get("/safety-impact")
    async def safety_impact(_actor: Dict[str, Any] = Depends(require_any_portal_token_dep)) -> Dict[str, Any]:
        incidents: List[Dict[str, Any]] = []
        capas: List[Dict[str, Any]] = []
        counts = {"critical": 0, "warning": 0, "informational": 0}
        async for i in db.incidents.find(
            {"resolution_status": {"$ne": "Closed"}},
            {"_id": 0},
        ):
            tier = _safety_tier(i)
            counts[tier] += 1
            incidents.append({
                "incident_id": i.get("id"),
                "summary": i.get("summary"),
                "severity": i.get("severity"),
                "tier": tier,
                "occurred_at": i.get("occurred_at"),
                "resolution_status": i.get("resolution_status"),
                "project_number": i.get("project_number"),
                **_map_ready(project_number=i.get("project_number"),
                              status=i.get("resolution_status"),
                              timestamp=i.get("occurred_at"),
                              trust_state=f"incident_{tier}",
                              source_system="incidents"),
            })
        async for c in db.corrective_actions.find(
            apply_synthetic_corrective_action_exclusion({"status": {"$nin": ["Completed", "Closed", "Cancelled"]}}),
            {"_id": 0},
        ):
            tier = _safety_tier({"severity": c.get("severity"), "status": c.get("status")})
            if tier == "informational": tier = "warning"  # CAPAs are at least warning
            counts[tier] += 1
            capas.append({
                "capa_id": c.get("id"),
                "summary": c.get("summary") or c.get("description"),
                "tier": tier,
                "due_at": c.get("due_at"),
                "status": c.get("status"),
                "project_number": c.get("project_number"),
                **_map_ready(project_number=c.get("project_number"),
                              status=c.get("status"),
                              timestamp=c.get("due_at"),
                              trust_state=f"capa_{tier}",
                              source_system="corrective_actions"),
            })
        incidents.sort(key=lambda r: {"critical": 0, "warning": 1, "informational": 2}.get(r["tier"], 9))
        capas.sort(key=lambda r: {"critical": 0, "warning": 1, "informational": 2}.get(r["tier"], 9))
        return {"ok": True, "as_of": _now_iso(),
                 "incidents": incidents, "capas": capas,
                 "counts": counts}

    # ─── 8 · /telematics ───────────────────────────────────────────
    @router.get("/telematics")
    async def telematics(_actor: Dict[str, Any] = Depends(require_any_portal_token_dep)) -> Dict[str, Any]:
        """Truck Status Summary — best-effort from Motive cache.

        FleetWatcher placeholder returned as `not_connected` per OMEGA.
        """
        # Pull mapped trucks (equipment_master.motive_truck_id present).
        mapped = []
        async for em in db.equipment_master.find(
            {"motive_truck_id": {"$nin": [None, ""]}},
            {"_id": 0, "unit_number": 1, "id": 1, "motive_truck_id": 1,
              "current_project_number": 1, "current_location": 1},
        ):
            mapped.append(em)

        # Motive latest snapshot per truck (best effort).
        latest_by_motive: Dict[str, Dict[str, Any]] = {}
        try:
            async for e in db.motive_events.find(
                {"event_type": {"$in": ["location", "vehicle.location",
                                          "vehicle_location", "telemetry"]}},
                {"_id": 0, "vehicle_id": 1, "speed_mph": 1, "status": 1,
                  "timestamp": 1, "lat": 1, "lon": 1},
            ).sort("timestamp", -1).limit(2000):
                vid = e.get("vehicle_id")
                if vid and vid not in latest_by_motive:
                    latest_by_motive[vid] = e
        except Exception:
            pass

        bucket_counts: Dict[str, int] = {
            "moving": 0, "idling": 0, "at_job": 0, "at_plant": 0,
            "at_yard": 0, "at_shop": 0, "offline": 0, "no_gps": 0, "unknown": 0,
        }
        rows: List[Dict[str, Any]] = []
        for em in mapped:
            mid = em.get("motive_truck_id")
            e = latest_by_motive.get(mid) or {}
            state = _motive_state(e.get("speed_mph"), e.get("status"), e.get("timestamp"))
            # If state is "unknown" or "moving"/"idling" with a project, refine to at_job.
            if state in ("moving", "idling") and em.get("current_project_number"):
                # Without geofences, we don't know — leave moving/idling.
                pass
            bucket_counts[state] = bucket_counts.get(state, 0) + 1
            rows.append({
                "unit_number": em.get("unit_number"),
                "asset_id": em.get("id"),
                "motive_truck_id": mid,
                "project_number": em.get("current_project_number"),
                "operational_state": state,
                "speed_mph": e.get("speed_mph"),
                "lat": e.get("lat"),
                "lon": e.get("lon"),
                "last_seen_at": e.get("timestamp"),
                **_map_ready(asset_id=em.get("id"),
                              project_number=em.get("current_project_number"),
                              status=state,
                              location_ref=em.get("current_location"),
                              timestamp=e.get("timestamp"),
                              operational_state=state,
                              trust_state=f"motive_{state}",
                              source_system="motive"),
            })

        # Also count unmapped trucks
        unmapped = 0
        async for em in db.equipment_master.find(
            {"$or": [{"motive_truck_id": None}, {"motive_truck_id": ""}],
              "$nor": [{"type": "road_plate"}, {"type": "Road Plate"}]},
            {"_id": 0, "type": 1, "asset_type": 1, "category": 1},
        ):
            raw = em.get("type") or em.get("asset_type") or em.get("category") or ""
            k = normalize_asset_kind(raw) or ""
            if "truck" in k:
                unmapped += 1

        return {"ok": True, "as_of": _now_iso(),
                 "buckets": bucket_counts,
                 "mapped_trucks": len(mapped),
                 "unmapped_trucks": int(unmapped),
                 "rows": rows[:500],
                 "integration_readiness": {
                     "motive": "active" if mapped else "partial",
                     "fleetwatcher": "not_connected",
                 }}

    # ─── 9 · /timeline ─────────────────────────────────────────────
    @router.get("/timeline")
    async def timeline(
        _actor: Dict[str, Any] = Depends(require_any_portal_token_dep),
        days: int = Query(default=3, ge=1, le=14),
        limit: int = Query(default=400, ge=1, le=1000),
    ) -> Dict[str, Any]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        events: List[Dict[str, Any]] = []
        # asset transfers
        try:
            async for t in db.asset_transfers.find({"created_at": {"$gte": cutoff}},
                                                    {"_id": 0}).sort("created_at", -1).limit(limit):
                events.append({
                    "kind": "asset_transfer", "timestamp": t.get("created_at"),
                    "summary": f"{t.get('kind') or 'TRANSFER'} · {t.get('unit_number') or t.get('asset_id')}",
                    **_map_ready(asset_id=t.get("asset_id"),
                                  project_number=t.get("to_project_number") or t.get("from_project_number"),
                                  timestamp=t.get("created_at"),
                                  trust_state="asset_transfer",
                                  source_system="asset_transfers"),
                })
        except Exception as _exc:  # noqa: BLE001
            logger.warning("[ops-feed] source skipped: %s", _exc)
        # dispatch state events
        try:
            async for e in db.dispatch_state_events.find(
                {"recorded_at": {"$gte": cutoff}}, {"_id": 0},
            ).sort("recorded_at", -1).limit(limit):
                events.append({
                    "kind": "dispatch_state", "timestamp": e.get("recorded_at"),
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
        # incidents
        try:
            async for i in db.incidents.find({"occurred_at": {"$gte": cutoff}},
                                              {"_id": 0}).limit(limit):
                events.append({
                    "kind": "incident", "timestamp": i.get("occurred_at"),
                    "summary": i.get("summary") or "incident",
                    **_map_ready(project_number=i.get("project_number"),
                                  status=i.get("resolution_status"),
                                  timestamp=i.get("occurred_at"),
                                  trust_state=f"incident_{_safety_tier(i)}",
                                  source_system="incidents"),
                })
        except Exception as _exc:  # noqa: BLE001
            logger.warning("[ops-feed] source skipped: %s", _exc)
        events.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
        return {"ok": True, "as_of": _now_iso(),
                 "events": events[:limit]}

    # ─── 10 · /map-contract ────────────────────────────────────────
    @router.get("/map-contract")
    async def map_contract(
        _actor: Dict[str, Any] = Depends(require_any_portal_token_dep),
        limit: int = Query(default=500, ge=1, le=2000),
    ) -> Dict[str, Any]:
        """Map-ready row dump. When FleetWatcher activates, this is the
        single endpoint the Live Operations Map will consume — every row
        already has asset_id / lat / lon / last_location_time /
        location_source / operational_state stamped."""
        rows: List[Dict[str, Any]] = []
        # Mapped trucks first.
        async for em in db.equipment_master.find(
            {"motive_truck_id": {"$nin": [None, ""]}},
            {"_id": 0, "unit_number": 1, "id": 1, "motive_truck_id": 1,
              "current_project_number": 1, "type": 1, "asset_type": 1,
              "category": 1, "status": 1, "updated_at": 1},
        ).limit(limit):
            raw = em.get("type") or em.get("asset_type") or em.get("category") or ""
            k = normalize_asset_kind(raw) or "unknown"
            e = await db.motive_events.find_one(
                {"vehicle_id": em.get("motive_truck_id")},
                {"_id": 0, "lat": 1, "lon": 1, "timestamp": 1, "speed_mph": 1, "status": 1},
                sort=[("timestamp", -1)],
            ) or {}
            op_state = _motive_state(e.get("speed_mph"), e.get("status"), e.get("timestamp"))
            rows.append({
                "asset_id": em.get("id"),
                "unit_number": em.get("unit_number"),
                "asset_kind": k,
                "lat": e.get("lat"),
                "lon": e.get("lon"),
                "last_location_time": e.get("timestamp"),
                "location_source": "motive" if e else "none",
                "operational_state": op_state,
                **_map_ready(asset_id=em.get("id"),
                              project_number=em.get("current_project_number"),
                              status=em.get("status") or op_state,
                              timestamp=e.get("timestamp") or em.get("updated_at"),
                              operational_state=op_state,
                              trust_state=f"map_{op_state}",
                              source_system="motive"),
            })
        return {"ok": True, "as_of": _now_iso(), "rows": rows,
                 "integration_readiness": {
                     "motive": "partial",
                     "fleetwatcher": "not_connected",
                 }}

    return router


# ════════════════════════════════════════════════════════════════════
# Conflict detection helpers
# ════════════════════════════════════════════════════════════════════
async def _conflict_rows(db) -> List[Dict[str, Any]]:
    """Detect operational conflicts. Read-only."""
    rows: List[Dict[str, Any]] = []
    # 1. Truck assigned to multiple ACTIVE projects via dispatch_assignments
    truck_to_projects: Dict[str, Set[str]] = {}
    async for a in db.dispatch_assignments.find(
        {"current_state": {"$nin": list(DLS.TERMINAL_STATES)},
          "cancelled_at": None},
        {"_id": 0, "truck_id": 1, "project_number": 1, "id": 1},
    ):
        t = a.get("truck_id"); pn = a.get("project_number")
        if t and pn:
            truck_to_projects.setdefault(t, set()).add(pn)
    for t, projs in truck_to_projects.items():
        if len(projs) > 1:
            rows.append({"kind": "truck_multi_project",
                          "subject": t, "projects": sorted(projs),
                          **_map_ready(asset_id=t, status="conflict",
                                        trust_state="conflict_truck",
                                        source_system="dispatch_assignments",
                                        timestamp=_now_iso())})
    # 2. Driver assigned to multiple trucks (active)
    driver_to_trucks: Dict[str, Set[str]] = {}
    async for a in db.dispatch_assignments.find(
        {"current_state": {"$nin": list(DLS.TERMINAL_STATES)},
          "cancelled_at": None},
        {"_id": 0, "driver_id": 1, "driver_name": 1, "truck_id": 1},
    ):
        d = a.get("driver_id") or a.get("driver_name")
        t = a.get("truck_id")
        if d and t: driver_to_trucks.setdefault(d, set()).add(t)
    for d, trucks in driver_to_trucks.items():
        if len(trucks) > 1:
            rows.append({"kind": "driver_multi_truck",
                          "subject": d, "trucks": sorted(trucks),
                          **_map_ready(status="conflict",
                                        trust_state="conflict_driver",
                                        source_system="dispatch_assignments",
                                        timestamp=_now_iso())})
    # 3. Haul assigned to inactive project
    inactive_pns: Set[str] = set()
    async for j in db.jobs_master.find(
        {"$or": [{"is_active": False}, {"active": False}]},
        {"_id": 0, "project_number": 1},
    ):
        if j.get("project_number"): inactive_pns.add(j["project_number"])
    if inactive_pns:
        async for a in db.dispatch_assignments.find(
            {"current_state": {"$nin": list(DLS.TERMINAL_STATES)},
              "cancelled_at": None,
              "project_number": {"$in": list(inactive_pns)}},
            {"_id": 0, "id": 1, "truck_id": 1, "project_number": 1},
        ):
            rows.append({"kind": "haul_inactive_project",
                          "subject": a.get("id") or a.get("truck_id"),
                          "project_number": a.get("project_number"),
                          **_map_ready(asset_id=a.get("truck_id"),
                                        project_number=a.get("project_number"),
                                        assignment_id=a.get("id"),
                                        status="conflict",
                                        trust_state="conflict_inactive_project",
                                        source_system="dispatch_assignments",
                                        timestamp=_now_iso())})
    return rows


async def _count_conflicts(db) -> int:
    rows = await _conflict_rows(db)
    return len(rows)


def _conflict_count_buckets(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in rows:
        k = r.get("kind") or "unknown"
        out[k] = out.get(k, 0) + 1
    out["total"] = len(rows)
    return out


__all__ = ["build_operations_center_command_router"]
