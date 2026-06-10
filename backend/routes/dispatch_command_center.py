"""
routes/dispatch_command_center.py · FORGEDOPS Dispatch Command Center V1 · Phase 1.

Backend aggregation foundation. ONE place that the future Dispatch
Command Center UI will consume — instead of stitching 15 disconnected
queries on the client.

Doctrine (per architecture docs in /app/memory/):
  - Platform-first, tenant-configurable. Every endpoint accepts
    X-Tenant-Id and resolves via _resolve_tenant().
  - No new source-of-truth collections. Asset Spine is canonical for
    assets. dispatch_assignments + dispatch_driver_sessions +
    haul_cycles + fleet_status + fleet_defects + projects + daily_reports
    are read in parallel and composed.
  - FleetWatcher / MaintainX fields are RESERVED (return None /
    "not_connected"). NEVER fake data.
  - SMS provider abstraction (services.sms_provider) is used as-is;
    when Twilio credentials are missing, every send returns
    "skipped" with provider_not_configured semantics.
  - All endpoints are READ-ONLY except POST /broadcast-sms (which
    only writes to dispatch_broadcasts + delivery_log).
  - Audit triple preserved on writes (admin_audit_log + audit_events).

Endpoints (prefix /api/dispatch/command):
  GET  /summary
  GET  /fleet
  GET  /drivers
  GET  /jobs
  GET  /haul
  POST /broadcast-sms      (also writes audit row)

Auth:
  GET  endpoints  → require_any_portal_token   (read across all portals)
  POST /broadcast → require_dispatch_or_admin  (write-class)
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, Field

import dispatch_lifecycle as DLS
from routes.dispatch_lifecycle import DEFAULT_TENANT_ID, _resolve_tenant

logger = logging.getLogger("dispatch_command_center")


# ════════════════════════════════════════════════════════════════════
# Constants — integration readiness
# ════════════════════════════════════════════════════════════════════
NOT_CONNECTED = "not_connected"
PROVIDER_NOT_CONFIGURED = "provider_not_configured"
MOTIVE_STALE_AFTER_MIN = 30          # > 30 min since last event → stale
WAITING_ATTENTION_MIN = 25           # waiting state > 25 min → attention
UNACKED_ATTENTION_MIN = 10           # un-acked > 10 min → attention
BREAKDOWN_ATTENTION_MIN = 1          # any breakdown is immediate attention


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now_utc().isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


def _minutes_since(iso: Optional[str]) -> Optional[int]:
    """Return minutes elapsed since an ISO timestamp; None if invalid."""
    if not iso:
        return None
    try:
        # tolerate trailing Z / +00:00
        s = iso.replace("Z", "+00:00") if iso.endswith("Z") else iso
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = _now_utc() - dt
        return int(delta.total_seconds() // 60)
    except Exception:
        return None


def _start_of_utc_day() -> datetime:
    n = _now_utc()
    return n.replace(hour=0, minute=0, second=0, microsecond=0)


# ════════════════════════════════════════════════════════════════════
# FleetWatcher / MaintainX field templates (always returned, always
# null-safe, NEVER faked)
# ════════════════════════════════════════════════════════════════════
def _fleetwatcher_template() -> Dict[str, Any]:
    return {
        "connected": False,
        "status": NOT_CONNECTED,
        "ticket_number": None,
        "tons": None,
        "loads": None,
        "cycle_time_min": None,
        "plant": None,
        "material": None,
        "delivery_status": None,
    }


def _maintainx_template() -> Dict[str, Any]:
    return {
        "connected": False,
        "status": NOT_CONNECTED,
        "work_order_id": None,
        "work_order_status": None,
        "asset_id": None,
        "scheduled_at": None,
    }


def _motive_template(mapping: Optional[Dict[str, Any]] = None,
                     last_event: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not mapping:
        return {
            "connected": False,
            "mapped": False,
            "motive_vehicle_id": None,
            "motive_asset_id": None,
            "last_event_at": None,
            "stale": None,
            "lat": None,
            "lon": None,
        }
    last_at = (last_event or {}).get("event_at") if last_event else None
    minutes = _minutes_since(last_at)
    return {
        "connected": True,
        "mapped": True,
        "motive_vehicle_id": (mapping.get("motive") or {}).get("vehicle_id"),
        "motive_asset_id": (mapping.get("motive") or {}).get("asset_id"),
        "last_event_at": last_at,
        "stale": (minutes is not None and minutes > MOTIVE_STALE_AFTER_MIN),
        "lat": (last_event or {}).get("location", {}).get("lat") if last_event else None,
        "lon": (last_event or {}).get("location", {}).get("lon") if last_event else None,
    }


# ════════════════════════════════════════════════════════════════════
# Body models
# ════════════════════════════════════════════════════════════════════
class BroadcastSmsBody(BaseModel):
    audience: str = Field(..., description="all_active | project:<num> | drivers:<id1,id2>")
    message: str = Field(..., min_length=1, max_length=280)
    kind: Optional[str] = Field(default="general")
    # iter392 magic-link routes are intentionally NOT reused here — this
    # is a free-form broadcast, not a per-assignment message.


# ════════════════════════════════════════════════════════════════════
# Aggregation primitives — pure async functions over Mongo
# ════════════════════════════════════════════════════════════════════

async def _fleet_status_index(db) -> Dict[str, Dict[str, Any]]:
    """Map unit_number → fleet_status row (latest)."""
    idx: Dict[str, Dict[str, Any]] = {}
    async for row in db.fleet_status.find({}, {"_id": 0}):
        u = row.get("unit_number")
        if u:
            idx[str(u)] = row
    return idx


async def _open_defects_index(db) -> Dict[str, List[Dict[str, Any]]]:
    """unit_number → list of open/acknowledged defects."""
    out: Dict[str, List[Dict[str, Any]]] = {}
    async for d in db.fleet_defects.find(
        {"status": {"$in": ["open", "acknowledged"]}},
        {"_id": 0},
    ):
        u = d.get("truck_unit_number") or d.get("trailer_unit_number")
        if not u:
            continue
        out.setdefault(str(u), []).append(d)
    return out


async def _latest_inspection_index(db) -> Dict[str, Dict[str, Any]]:
    """unit_number → latest equipment_inspections row."""
    idx: Dict[str, Dict[str, Any]] = {}
    cur = db.equipment_inspections.find(
        {}, {"_id": 0, "unit_number": 1, "created_at": 1, "fail_count": 1, "kind": 1},
    ).sort("created_at", -1)
    async for d in cur:
        u = d.get("unit_number")
        if not u:
            continue
        if u not in idx:
            idx[u] = d
    return idx


async def _active_assignments_by_truck(db, tenant_id: str) -> Dict[str, Dict[str, Any]]:
    """truck_id → active (non-terminal, non-cancelled) assignment row."""
    out: Dict[str, Dict[str, Any]] = {}
    cur = db.dispatch_assignments.find(
        {
            "tenant_id": tenant_id,
            "current_state": {"$nin": list(DLS.TERMINAL_STATES)},
            "cancelled_at": None,
        },
        {"_id": 0},
    )
    async for a in cur:
        t = a.get("truck_id")
        if t and t not in out:
            out[str(t)] = a
    return out


async def _motive_mapping_index(db) -> Dict[str, Dict[str, Any]]:
    """unit_number → asset_mappings row (motive). Last-write wins."""
    idx: Dict[str, Dict[str, Any]] = {}
    async for m in db.asset_mappings.find(
        {"provider": "motive"}, {"_id": 0},
    ):
        unit = m.get("masci_unit_number")
        if unit:
            idx[str(unit)] = m
    return idx


async def _latest_motive_event_by_vehicle(
    db, vehicle_ids: List[str],
) -> Dict[str, Dict[str, Any]]:
    """motive_vehicle_id → latest motive_events row."""
    if not vehicle_ids:
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    cur = db.motive_events.find(
        {"motive_vehicle_id": {"$in": vehicle_ids}},
        {"_id": 0},
    ).sort("event_at", -1)
    async for e in cur:
        vid = str(e.get("motive_vehicle_id"))
        if vid and vid not in out:
            out[vid] = e
    return out


# ════════════════════════════════════════════════════════════════════
# Build helpers — fleet / drivers / jobs / haul
# ════════════════════════════════════════════════════════════════════

async def _build_fleet(db, tenant_id: str, limit: int) -> Dict[str, Any]:
    """Compose Live Fleet Board rows."""
    fleet_idx, defect_idx, insp_idx, active_assn_idx, motive_idx = await asyncio.gather(
        _fleet_status_index(db),
        _open_defects_index(db),
        _latest_inspection_index(db),
        _active_assignments_by_truck(db, tenant_id),
        _motive_mapping_index(db),
    )

    # Pull last Motive events for mapped units (in a single query)
    motive_vehicle_ids: List[str] = []
    for m in motive_idx.values():
        vid = (m.get("motive") or {}).get("vehicle_id")
        if vid:
            motive_vehicle_ids.append(str(vid))
    motive_event_idx = await _latest_motive_event_by_vehicle(db, motive_vehicle_ids)

    rows: List[Dict[str, Any]] = []
    counts = {"total": 0, "active": 0, "oos": 0, "in_shop": 0, "unknown": 0,
              "unmapped": 0, "unsynced": 0}

    # Read canonical asset spine docs (active only)
    cur = db.equipment_master.find(
        {"$or": [
            {"is_active": {"$ne": False}},
            {"active": {"$ne": False}},
        ]},
        {"_id": 0},
    ).limit(int(limit))
    async for asset in cur:
        unit = asset.get("unit_number") or asset.get("asset_number") or ""
        if not unit:
            continue
        counts["total"] += 1

        fleet_row = fleet_idx.get(str(unit), {})
        defects = defect_idx.get(str(unit), [])
        insp = insp_idx.get(str(unit))
        active_assn = active_assn_idx.get(str(unit))
        mapping = motive_idx.get(str(unit))
        motive_event = None
        if mapping:
            vid = (mapping.get("motive") or {}).get("vehicle_id")
            if vid:
                motive_event = motive_event_idx.get(str(vid))
        else:
            counts["unmapped"] += 1
            counts["unsynced"] += 1

        status = fleet_row.get("status") or "unknown"
        if status == "oos":
            counts["oos"] += 1
        elif active_assn:
            counts["active"] += 1
        elif status == "defect_open":
            counts["in_shop"] += 1
        else:
            counts["unknown"] += 1

        rows.append({
            "asset_id": asset.get("id") or asset.get("asset_id"),
            "unit_number": unit,
            "asset_type": asset.get("type") or asset.get("asset_type"),
            "asset_category": asset.get("category") or asset.get("asset_category"),
            "make_model": asset.get("make_model") or asset.get("model"),
            "status": status,
            "active_assignment_id": (active_assn or {}).get("id"),
            "current_state": (active_assn or {}).get("current_state"),
            "current_project_number": (active_assn or {}).get("project_number"),
            "current_driver_name": (active_assn or {}).get("driver_name"),
            "current_driver_id": (active_assn or {}).get("driver_id"),
            "last_dvir_kind": (insp or {}).get("kind"),
            "last_dvir_at": (insp or {}).get("created_at"),
            "last_dvir_fail_count": (insp or {}).get("fail_count", 0),
            "open_defect_count": len(defects),
            "fleet_status_open_oos_count": fleet_row.get("open_oos_count", 0),
            "fleet_status_open_monitor_count": fleet_row.get("open_monitor_count", 0),
            "motive": _motive_template(mapping, motive_event),
            "maintainx": _maintainx_template(),
            "fleetwatcher": _fleetwatcher_template(),
        })

    rank = {"oos": 0, "defect_open": 1, "active": 2, "available": 3, "unknown": 4}
    rows.sort(key=lambda r: (rank.get(r["status"], 9), r["unit_number"] or ""))
    return {"counts": counts, "rows": rows}


async def _build_drivers(db, tenant_id: str, limit: int) -> Dict[str, Any]:
    """Compose Live Driver Board rows."""
    # Active sessions (not revoked)
    sessions: List[Dict[str, Any]] = []
    async for s in db.dispatch_driver_sessions.find(
        {"tenant_id": tenant_id, "revoked_at": None},
        {"_id": 0},
    ).limit(int(limit)):
        sessions.append(s)

    if not sessions:
        return {
            "counts": {"shifted": 0, "un_acked": 0, "in_breakdown": 0,
                       "waiting": 0, "off_shift_today": 0},
            "rows": [],
        }

    # Active assignments keyed by driver_id AND by truck_id (driver may
    # come in via truck or driver id depending on iter392 vs iter401).
    active_by_driver: Dict[str, Dict[str, Any]] = {}
    active_by_truck: Dict[str, Dict[str, Any]] = {}
    async for a in db.dispatch_assignments.find(
        {
            "tenant_id": tenant_id,
            "current_state": {"$nin": list(DLS.TERMINAL_STATES)},
            "cancelled_at": None,
        },
        {"_id": 0},
    ):
        if a.get("driver_id") and a["driver_id"] not in active_by_driver:
            active_by_driver[a["driver_id"]] = a
        if a.get("truck_id") and a["truck_id"] not in active_by_truck:
            active_by_truck[a["truck_id"]] = a

    # Latest inspection (per truck) for DVIR badge
    insp_idx = await _latest_inspection_index(db)

    # Off-shift count today (sessions revoked within last day)
    day_start = _start_of_utc_day().isoformat()
    off_shift_today = await db.dispatch_driver_sessions.count_documents({
        "tenant_id": tenant_id,
        "revoked_at": {"$gte": day_start},
    })

    counts = {"shifted": len(sessions), "un_acked": 0,
              "in_breakdown": 0, "waiting": 0,
              "off_shift_today": int(off_shift_today)}
    rows: List[Dict[str, Any]] = []
    for s in sessions:
        driver_id = s.get("driver_id")
        truck_id = s.get("truck_id")
        assn = (active_by_driver.get(driver_id) if driver_id else None) or \
               (active_by_truck.get(truck_id) if truck_id else None)
        state = (assn or {}).get("current_state")
        acked_at = (assn or {}).get("acked_at")
        last_transition_at = (assn or {}).get("last_transition_at")
        since_min = _minutes_since(last_transition_at)
        attention_tag = None
        if state == DLS.BREAKDOWN:
            attention_tag = "BREAKDOWN"
            counts["in_breakdown"] += 1
        elif state == DLS.WAITING and (since_min or 0) > WAITING_ATTENTION_MIN:
            attention_tag = "WAITING_LONG"
            counts["waiting"] += 1
        elif state == DLS.WAITING:
            counts["waiting"] += 1
        elif assn and not acked_at and (
            _minutes_since((assn or {}).get("assigned_at")) or 0
        ) > UNACKED_ATTENTION_MIN:
            attention_tag = "UN_ACKED"
            counts["un_acked"] += 1
        elif assn and not acked_at:
            counts["un_acked"] += 1

        insp = insp_idx.get(truck_id) if truck_id else None
        last_dvir = (insp or {}).get("created_at")
        last_dvir_pass = (insp or {}).get("fail_count", 0) == 0

        rows.append({
            "session_id": s.get("id"),
            "driver_id": driver_id,
            "driver_name": s.get("driver_name"),
            "employee_id": s.get("employee_id"),
            "truck_id": truck_id,
            "trailer_id": s.get("trailer_id"),
            "company": s.get("company"),
            "material": s.get("material"),
            "shift_started_at": s.get("created_at") or s.get("issued_at"),
            "current_assignment_id": (assn or {}).get("id"),
            "current_state": state,
            "current_project_number": (assn or {}).get("project_number"),
            "current_state_since_min": since_min,
            "acked": bool(acked_at),
            "last_dvir_at": last_dvir,
            "last_dvir_pass": last_dvir_pass,
            "communication_status": {
                "last_sms_status": ((assn or {}).get("delivery_log") or [{}])[-1].get("status")
                if (assn or {}).get("delivery_log") else None,
            },
            "attention_tag": attention_tag,
            "safety_flags": [],   # reserved; surfaced via Shop Feed
            "fleetwatcher": _fleetwatcher_template(),
        })

    rank = {"BREAKDOWN": 0, "UN_ACKED": 1, "WAITING_LONG": 2, None: 9}
    rows.sort(key=lambda r: (rank.get(r["attention_tag"], 5),
                              r.get("driver_name") or ""))
    return {"counts": counts, "rows": rows}


async def _build_jobs(db, tenant_id: str, limit: int) -> Dict[str, Any]:
    """Compose Live Job Board rows."""
    day_start = _start_of_utc_day().isoformat()

    # All active assignments today (or any active non-terminal cycle)
    project_aggregate: Dict[str, Dict[str, Any]] = {}
    async for a in db.dispatch_assignments.find(
        {
            "tenant_id": tenant_id,
            "$or": [
                {"current_state": {"$nin": list(DLS.TERMINAL_STATES)}, "cancelled_at": None},
                {"assigned_at": {"$gte": day_start}},
            ],
        },
        {
            "_id": 0, "project_number": 1, "project_name": 1, "truck_id": 1,
            "driver_id": 1, "driver_name": 1, "equipment_id": 1, "trailer_id": 1,
            "current_state": 1, "cancelled_at": 1, "haul_type": 1,
        },
    ):
        pn = (a.get("project_number") or "").strip() or "(unassigned)"
        agg = project_aggregate.setdefault(pn, {
            "project_number": pn,
            "project_name": (a.get("project_name") or "").strip() or pn,
            "trucks": set(), "drivers": set(),
            "equipment": set(), "trailers": set(),
            "assignments_count": 0,
            "in_breakdown": 0, "in_waiting": 0,
        })
        agg["assignments_count"] += 1
        if a.get("truck_id"):
            agg["trucks"].add(a["truck_id"])
        if a.get("driver_id"):
            agg["drivers"].add(a["driver_id"])
        elif a.get("driver_name"):
            agg["drivers"].add(a["driver_name"])
        if a.get("equipment_id"):
            agg["equipment"].add(a["equipment_id"])
        if a.get("trailer_id"):
            agg["trailers"].add(a["trailer_id"])
        if a.get("current_state") == DLS.BREAKDOWN:
            agg["in_breakdown"] += 1
        if a.get("current_state") == DLS.WAITING:
            agg["in_waiting"] += 1

    # Cycles + tons today (per project) — best-effort
    cycles_by_project: Dict[str, int] = {}
    materials_in: Dict[str, int] = {}
    materials_out: Dict[str, int] = {}
    try:
        async for c in db.haul_cycles.find(
            {"tenant_id": tenant_id, "completed_at": {"$gte": day_start}},
            {"_id": 0, "project_number": 1, "haul_type": 1},
        ):
            pn = (c.get("project_number") or "").strip() or "(unassigned)"
            cycles_by_project[pn] = cycles_by_project.get(pn, 0) + 1
    except Exception:
        pass

    # Daily reports (materials in / outbound) today, keyed by project_number
    today_yyyy_mm_dd = _now_utc().date().isoformat()
    try:
        async for d in db.daily_reports.find(
            {"report_date": today_yyyy_mm_dd,
             "deleted_at": {"$in": [None, "", False]}},
            {"_id": 0, "project_number": 1, "materials": 1, "outbound_materials": 1},
        ):
            pn = (d.get("project_number") or "").strip() or "(unassigned)"
            materials_in[pn] = materials_in.get(pn, 0) + len(d.get("materials") or [])
            materials_out[pn] = materials_out.get(pn, 0) + len(d.get("outbound_materials") or [])
    except Exception:
        pass

    # Incidents open per project (best-effort)
    incidents_by_project: Dict[str, int] = {}
    try:
        async for i in db.incidents.find(
            {"resolution_status": {"$ne": "Closed"}},
            {"_id": 0, "project_number": 1},
        ):
            pn = (i.get("project_number") or "").strip() or "(unassigned)"
            incidents_by_project[pn] = incidents_by_project.get(pn, 0) + 1
    except Exception:
        pass

    rows: List[Dict[str, Any]] = []
    for pn, agg in project_aggregate.items():
        loads = int(cycles_by_project.get(pn, 0))
        rows.append({
            "project_number": pn,
            "project_name": agg["project_name"],
            "trucks_today": len(agg["trucks"]),
            "drivers_today": len(agg["drivers"]),
            "equipment_today": len(agg["equipment"]),
            "trailers_today": len(agg["trailers"]),
            "assignments_today": agg["assignments_count"],
            "loads_today": loads,
            "materials_in_count": materials_in.get(pn, 0),
            "materials_out_count": materials_out.get(pn, 0),
            "incidents_open": incidents_by_project.get(pn, 0),
            "breakdowns_today": agg["in_breakdown"],
            "waiting_today": agg["in_waiting"],
            # V1 placeholders (no computation; null-safe)
            "truck_utilization_pct": None,
            "equipment_utilization_pct": None,
            "attention_tag": (
                "BREAKDOWN" if agg["in_breakdown"] > 0
                else "WAITING" if agg["in_waiting"] > 0
                else None
            ),
            "fleetwatcher": _fleetwatcher_template(),
        })
    rows.sort(key=lambda r: (-r["assignments_today"], r["project_number"]))
    rows = rows[:int(limit)]

    counts = {
        "projects_active": len(project_aggregate),
        "projects_attention": sum(1 for r in rows if r["attention_tag"]),
    }
    return {"counts": counts, "rows": rows}


async def _build_haul(db, tenant_id: str, limit: int) -> Dict[str, Any]:
    """Compose Live Haul Board rows.

    Combines:
      • active assignments (in-flight cycles)
      • completed haul_cycles today (for totals)
    """
    day_start = _start_of_utc_day().isoformat()

    # Tenant-wide totals
    loads_today = 0
    equipment_moves_today = 0
    try:
        async for c in db.haul_cycles.find(
            {"tenant_id": tenant_id, "completed_at": {"$gte": day_start}},
            {"_id": 0, "haul_type": 1},
        ):
            loads_today += 1
            if (c.get("haul_type") or "Material") == "Equipment Move":
                equipment_moves_today += 1
    except Exception:
        pass

    active_rows: List[Dict[str, Any]] = []
    waiting_on_plant = 0
    waiting_on_dump = 0
    breakdown_impacts = 0
    cur = db.dispatch_assignments.find(
        {
            "tenant_id": tenant_id,
            "current_state": {"$nin": list(DLS.TERMINAL_STATES)},
            "cancelled_at": None,
        },
        {"_id": 0},
    ).sort("assigned_at", -1).limit(int(limit))
    async for a in cur:
        state = a.get("current_state") or ""
        wait = (a.get("current_wait_reason") or "").upper()
        if state == DLS.BREAKDOWN:
            breakdown_impacts += 1
        if state == DLS.WAITING:
            if "PLANT" in wait:
                waiting_on_plant += 1
            elif "DUMP" in wait or "SITE" in wait:
                waiting_on_dump += 1
        active_rows.append({
            "assignment_id": a.get("id"),
            "material": a.get("material"),
            "liquid_product": a.get("liquid_product"),
            "source": a.get("source_location") or a.get("pickup_location"),
            "destination": a.get("destination") or a.get("dropoff_location"),
            "truck_id": a.get("truck_id"),
            "trailer_id": a.get("trailer_id"),
            "driver_id": a.get("driver_id"),
            "driver_name": a.get("driver_name"),
            "project_number": a.get("project_number"),
            "project_name": a.get("project_name"),
            "haul_type": a.get("haul_type"),
            "load_count": a.get("load_count"),
            "current_state": state,
            "current_state_since_min": _minutes_since(a.get("last_transition_at")),
            "wait_reason": a.get("current_wait_reason"),
            # FleetWatcher-ready fields — reserved, null until activation
            "fleetwatcher": _fleetwatcher_template(),
        })

    counts = {
        "loads_completed_today": loads_today,
        "equipment_moves_completed_today": equipment_moves_today,
        "active_hauls": len(active_rows),
        "waiting_on_plant": waiting_on_plant,
        "waiting_on_dump": waiting_on_dump,
        "breakdown_impacts": breakdown_impacts,
    }

    integration_readiness = {
        "fleetwatcher": NOT_CONNECTED,
        "motive": "available",   # presence inferred; per-row in fleet board
    }

    return {"counts": counts, "rows": active_rows,
            "integration_readiness": integration_readiness}


# ════════════════════════════════════════════════════════════════════
# Router factory
# ════════════════════════════════════════════════════════════════════
def build_dispatch_command_center_router(
    db,
    require_any_portal_token_dep: Callable[..., Awaitable[Dict[str, Any]]],
    require_dispatch_or_admin_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    """Build the Dispatch Command Center V1 backend router."""
    router = APIRouter(prefix="/api/dispatch/command", tags=["dispatch-command-center"])

    # ────────────────────────────────────────────────────────────
    # GET /summary — one-shot rollup the future UI hits on load
    # ────────────────────────────────────────────────────────────
    @router.get("/summary")
    async def get_summary(
        _actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        fleet_limit: int = Query(500, ge=1, le=2000),
        driver_limit: int = Query(500, ge=1, le=2000),
        job_limit: int = Query(200, ge=1, le=1000),
        haul_limit: int = Query(200, ge=1, le=1000),
    ) -> Dict[str, Any]:
        tenant_id = _resolve_tenant(x_tenant_id)
        fleet, drivers, jobs, haul, asset_health, shop = await asyncio.gather(
            _build_fleet(db, tenant_id, fleet_limit),
            _build_drivers(db, tenant_id, driver_limit),
            _build_jobs(db, tenant_id, job_limit),
            _build_haul(db, tenant_id, haul_limit),
            _asset_spine_health(db),
            _shop_feed_counts(db, tenant_id),
        )

        safety = await _safety_counts(db)
        comm = _communication_status()

        return {
            "ok": True,
            "tenant_id": tenant_id,
            "as_of": _now_iso(),
            "fleet": {"counts": fleet["counts"]},
            "drivers": {"counts": drivers["counts"]},
            "jobs": {"counts": jobs["counts"]},
            "haul": {"counts": haul["counts"],
                     "integration_readiness": haul["integration_readiness"]},
            "shop": shop,
            "safety": safety,
            "asset_health": asset_health,
            "communication": comm,
            "integration_readiness": {
                "motive": "available_if_mapped",
                "fleetwatcher": NOT_CONNECTED,
                "maintainx": NOT_CONNECTED,
                "sms_provider": comm["sms_provider"]["status"],
            },
        }

    # ────────────────────────────────────────────────────────────
    # GET /fleet
    # ────────────────────────────────────────────────────────────
    @router.get("/fleet")
    async def get_fleet(
        _actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        limit: int = Query(500, ge=1, le=2000),
    ) -> Dict[str, Any]:
        tenant_id = _resolve_tenant(x_tenant_id)
        data = await _build_fleet(db, tenant_id, limit)
        return {"ok": True, "tenant_id": tenant_id, "as_of": _now_iso(),
                **data}

    # ────────────────────────────────────────────────────────────
    # GET /drivers
    # ────────────────────────────────────────────────────────────
    @router.get("/drivers")
    async def get_drivers(
        _actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        limit: int = Query(500, ge=1, le=2000),
    ) -> Dict[str, Any]:
        tenant_id = _resolve_tenant(x_tenant_id)
        data = await _build_drivers(db, tenant_id, limit)
        return {"ok": True, "tenant_id": tenant_id, "as_of": _now_iso(),
                **data}

    # ────────────────────────────────────────────────────────────
    # GET /jobs
    # ────────────────────────────────────────────────────────────
    @router.get("/jobs")
    async def get_jobs(
        _actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        limit: int = Query(200, ge=1, le=1000),
    ) -> Dict[str, Any]:
        tenant_id = _resolve_tenant(x_tenant_id)
        data = await _build_jobs(db, tenant_id, limit)
        return {"ok": True, "tenant_id": tenant_id, "as_of": _now_iso(),
                **data}

    # ────────────────────────────────────────────────────────────
    # GET /haul
    # ────────────────────────────────────────────────────────────
    @router.get("/haul")
    async def get_haul(
        _actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        limit: int = Query(200, ge=1, le=1000),
    ) -> Dict[str, Any]:
        tenant_id = _resolve_tenant(x_tenant_id)
        data = await _build_haul(db, tenant_id, limit)
        return {"ok": True, "tenant_id": tenant_id, "as_of": _now_iso(),
                **data}

    # ────────────────────────────────────────────────────────────
    # POST /broadcast-sms (dispatch + admin only)
    #
    # Stubs safely when SMS_ENABLED is off or Twilio creds missing —
    # writes audit row regardless, returns per-recipient outcome.
    # ────────────────────────────────────────────────────────────
    @router.post("/broadcast-sms")
    async def broadcast_sms(
        body: BroadcastSmsBody,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ) -> Dict[str, Any]:
        from services.sms_provider import send_sms, sms_enabled  # noqa: PLC0415

        tenant_id = _resolve_tenant(x_tenant_id)
        audience = (body.audience or "").strip()
        if not audience:
            raise HTTPException(400, "audience is required")

        # Resolve recipients (driver_id list with best-effort phone lookup)
        recipients: List[Dict[str, Any]] = []
        target_assn_ids: List[str] = []

        if audience == "all_active":
            cur = db.dispatch_assignments.find(
                {
                    "tenant_id": tenant_id,
                    "current_state": {"$nin": list(DLS.TERMINAL_STATES)},
                    "cancelled_at": None,
                },
                {"_id": 0, "id": 1, "driver_id": 1, "driver_name": 1,
                 "truck_id": 1, "project_number": 1},
            )
            async for a in cur:
                recipients.append({
                    "assignment_id": a.get("id"),
                    "driver_id": a.get("driver_id"),
                    "driver_name": a.get("driver_name"),
                    "truck_id": a.get("truck_id"),
                    "project_number": a.get("project_number"),
                })
                if a.get("id"):
                    target_assn_ids.append(a["id"])
        elif audience.startswith("project:"):
            pn = audience.split(":", 1)[1].strip()
            cur = db.dispatch_assignments.find(
                {
                    "tenant_id": tenant_id,
                    "project_number": pn,
                    "current_state": {"$nin": list(DLS.TERMINAL_STATES)},
                    "cancelled_at": None,
                },
                {"_id": 0, "id": 1, "driver_id": 1, "driver_name": 1,
                 "truck_id": 1, "project_number": 1},
            )
            async for a in cur:
                recipients.append({
                    "assignment_id": a.get("id"),
                    "driver_id": a.get("driver_id"),
                    "driver_name": a.get("driver_name"),
                    "truck_id": a.get("truck_id"),
                    "project_number": pn,
                })
                if a.get("id"):
                    target_assn_ids.append(a["id"])
        elif audience.startswith("drivers:"):
            ids = [s.strip() for s in audience.split(":", 1)[1].split(",") if s.strip()]
            cur = db.dispatch_assignments.find(
                {
                    "tenant_id": tenant_id,
                    "driver_id": {"$in": ids},
                    "current_state": {"$nin": list(DLS.TERMINAL_STATES)},
                    "cancelled_at": None,
                },
                {"_id": 0, "id": 1, "driver_id": 1, "driver_name": 1,
                 "truck_id": 1, "project_number": 1},
            )
            async for a in cur:
                recipients.append({
                    "assignment_id": a.get("id"),
                    "driver_id": a.get("driver_id"),
                    "driver_name": a.get("driver_name"),
                    "truck_id": a.get("truck_id"),
                    "project_number": a.get("project_number"),
                })
                if a.get("id"):
                    target_assn_ids.append(a["id"])
        else:
            raise HTTPException(400, f"Unknown audience prefix in {audience!r}")

        # Best-effort driver phone lookup via employees collection
        async def _phone_for_driver(rcpt: Dict[str, Any]) -> Optional[str]:
            did = rcpt.get("driver_id")
            if not did:
                return None
            emp = await db.employees.find_one(
                {"$or": [{"id": did}, {"employee_id": did}]},
                {"_id": 0, "phone": 1, "mobile_phone": 1, "cell_phone": 1},
            )
            if not emp:
                return None
            return (emp.get("phone") or emp.get("mobile_phone") or
                    emp.get("cell_phone") or None)

        provider_active = sms_enabled()
        provider_status = "active" if provider_active else PROVIDER_NOT_CONFIGURED

        results: List[Dict[str, Any]] = []
        sent = 0
        skipped = 0
        failed = 0
        for r in recipients:
            phone = await _phone_for_driver(r)
            if not provider_active:
                outcome = {
                    "ok": False, "status": "skipped",
                    "provider": None, "provider_message_id": None,
                    "destination_phone_masked": phone[-4:] if phone else "",
                    "triggered_by": "broadcast",
                    "error_summary": PROVIDER_NOT_CONFIGURED,
                }
            else:
                outcome = await send_sms(
                    to_phone=phone,
                    body=body.message,
                    triggered_by="broadcast",
                )
            results.append({**r, "sms_result": outcome})
            status = outcome.get("status")
            if status == "sent":
                sent += 1
            elif status == "skipped":
                skipped += 1
            else:
                failed += 1

        # Persist a single broadcast audit row (always — even when no
        # recipients were resolved, so the operator action is recorded).
        broadcast_id = _new_id()
        try:
            await db.dispatch_broadcasts.insert_one({
                "id": broadcast_id,
                "tenant_id": tenant_id,
                "kind": body.kind or "general",
                "audience": audience,
                "message": body.message,
                "recipient_count": len(recipients),
                "sent": sent, "skipped": skipped, "failed": failed,
                "provider_status": provider_status,
                "issued_by_name": (actor or {}).get("name") or (actor or {}).get("email") or "actor",
                "issued_by_role": (actor or {}).get("_actor") or "actor",
                "issued_at": _now_iso(),
                "results": results,
            })
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[broadcast-sms] dispatch_broadcasts insert failed: {e}")

        # Mirror to admin_audit_log
        try:
            await db.admin_audit_log.insert_one({
                "id": _new_id(),
                "at": _now_iso(),
                "actor": (actor or {}).get("email") or (actor or {}).get("name") or "actor",
                "action": "DISPATCH_BROADCAST_SMS",
                "target_type": "dispatch_broadcasts",
                "target_id": broadcast_id,
                "payload": {
                    "audience": audience, "kind": body.kind or "general",
                    "recipient_count": len(recipients),
                    "sent": sent, "skipped": skipped, "failed": failed,
                    "provider_status": provider_status,
                },
            })
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[broadcast-sms] admin_audit_log insert failed: {e}")

        return {
            "ok": True,
            "broadcast_id": broadcast_id,
            "tenant_id": tenant_id,
            "audience": audience,
            "recipient_count": len(recipients),
            "sent": sent, "skipped": skipped, "failed": failed,
            "provider_status": provider_status,
            "results": results,
        }

    # ────────────────────────────────────────────────────────────
    # GET /broadcasts — recent broadcast SMS history for the Communications tab
    # ────────────────────────────────────────────────────────────
    @router.get("/broadcasts")
    async def list_broadcasts(
        _actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        limit: int = Query(50, ge=1, le=500),
    ) -> Dict[str, Any]:
        tenant_id = _resolve_tenant(x_tenant_id)
        rows: List[Dict[str, Any]] = []
        cur = db.dispatch_broadcasts.find(
            {"tenant_id": tenant_id}, {"_id": 0},
        ).sort("issued_at", -1).limit(int(limit))
        async for d in cur:
            # Strip per-recipient `results` array down to summary fields for
            # the list view (drawer fetches full row on demand).
            rows.append({
                "id": d.get("id"),
                "tenant_id": d.get("tenant_id"),
                "kind": d.get("kind"),
                "audience": d.get("audience"),
                "message": d.get("message"),
                "recipient_count": d.get("recipient_count", 0),
                "sent": d.get("sent", 0),
                "skipped": d.get("skipped", 0),
                "failed": d.get("failed", 0),
                "provider_status": d.get("provider_status"),
                "issued_by_name": d.get("issued_by_name"),
                "issued_by_role": d.get("issued_by_role"),
                "issued_at": d.get("issued_at"),
            })
        # SMS provider snapshot
        comm = _communication_status()
        return {
            "ok": True, "tenant_id": tenant_id, "as_of": _now_iso(),
            "count": len(rows), "rows": rows,
            "provider": comm["sms_provider"],
        }

    return router
# ════════════════════════════════════════════════════════════════════
async def _asset_spine_health(db) -> Dict[str, Any]:
    """Lean snapshot of Asset Spine health — reads only.

    Reuses the AssetSpine.health() projection.
    """
    try:
        from services.asset_spine import AssetSpine  # noqa: PLC0415
        spine = AssetSpine(db)
        h = await spine.health()
        return {
            "total_assets": h.get("total_assets"),
            "active": h.get("active_assets"),
            "retired": h.get("retired_assets"),
            "motive_coverage_pct": h.get("motive_coverage_pct"),
            "unmapped": h.get("unmapped_to_motive"),
            "conflicts": h.get("conflicts"),
            "last_scan_at": h.get("last_scan_at"),
            "last_scan_findings": h.get("last_scan_findings"),
        }
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[command-center asset_spine] {e}")
        return {
            "total_assets": None, "active": None, "retired": None,
            "motive_coverage_pct": None, "unmapped": None,
            "conflicts": None, "last_scan_at": None, "last_scan_findings": None,
        }


async def _shop_feed_counts(db, tenant_id: str) -> Dict[str, Any]:
    """Quick counts mirroring /api/shop/command-feed structure."""
    try:
        defects_open = await db.fleet_defects.count_documents({"status": "open"})
        defects_ack = await db.fleet_defects.count_documents({"status": "acknowledged"})
        # OOS / in-shop computed from fleet_status (existing index)
        oos = await db.fleet_status.count_documents({"status": "oos"})
        defect_open_units = await db.fleet_status.count_documents({"status": "defect_open"})
        # Recovery sub-state breakdowns
        waiting_on_parts = await db.dispatch_assignments.count_documents({
            "tenant_id": tenant_id,
            "breakdown_recovery": "waiting_on_parts",
        })
        active_recovery = await db.dispatch_assignments.count_documents({
            "tenant_id": tenant_id,
            "breakdown_recovery": {"$in": [
                "acknowledged", "diagnosing", "repair_active", "operational_test",
            ]},
        })
        # 7-day returned-to-service
        seven_d_ago = (_now_utc() - timedelta(days=7)).isoformat()
        returned_recent = await db.fleet_defects.count_documents({
            "status": "cleared",
            "cleared_at": {"$gte": seven_d_ago},
        })
        return {
            "defects_open": int(defects_open),
            "defects_acknowledged": int(defects_ack),
            "oos_units": int(oos),
            "defect_open_units": int(defect_open_units),
            "active_recovery": int(active_recovery),
            "waiting_on_parts": int(waiting_on_parts),
            "returned_to_service_7d": int(returned_recent),
            "maintainx": _maintainx_template(),
        }
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[command-center shop_feed] {e}")
        return {
            "defects_open": 0, "defects_acknowledged": 0,
            "oos_units": 0, "defect_open_units": 0,
            "active_recovery": 0, "waiting_on_parts": 0,
            "returned_to_service_7d": 0, "maintainx": _maintainx_template(),
        }


async def _safety_counts(db) -> Dict[str, Any]:
    try:
        incidents_open = await db.incidents.count_documents(
            {"resolution_status": {"$ne": "Closed"}},
        )
        ca_open = await db.corrective_actions.count_documents(
            {"status": {"$nin": ["Completed", "Closed", "Cancelled"]}},
        )
        return {"incidents_open": int(incidents_open),
                "corrective_actions_open": int(ca_open)}
    except Exception:
        return {"incidents_open": 0, "corrective_actions_open": 0}


def _communication_status() -> Dict[str, Any]:
    """Report SMS provider readiness without exposing secrets."""
    try:
        from services.sms_provider import sms_enabled  # noqa: PLC0415
        active = bool(sms_enabled())
    except Exception:
        active = False
    provider_name = (os.environ.get("SMS_PROVIDER") or "twilio").strip().lower()
    status = "active" if active else PROVIDER_NOT_CONFIGURED
    return {
        "sms_provider": {
            "name": provider_name,
            "status": status,
            "preview_safe": True,
        },
    }


__all__ = ["build_dispatch_command_center_router"]
