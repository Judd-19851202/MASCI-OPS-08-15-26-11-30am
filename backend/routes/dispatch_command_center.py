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

from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion
from lib.synthetic_corrective_action_filter import apply_synthetic_corrective_action_exclusion
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


def _summary_kpi_metadata() -> Dict[str, Any]:
    base_sources = [
        "equipment_master",
        "dispatch_assignments",
        "dispatch_driver_sessions",
        "fleet_status",
        "fleet_defects",
        "projects",
        "daily_reports",
    ]
    return {
        "page": {
            "kpi_name": "Dispatch Command Summary",
            "business_definition": "Shared Dispatch operational snapshot consumed by Dispatch, Shop, and leadership readers.",
            "source_of_truth": base_sources,
            "api_endpoint": "/api/dispatch/command/summary",
            "formula": "Server-side aggregation over Dispatch, fleet, haul, shop, safety, and asset-spine facts. No client-side count reconstruction is allowed.",
            "confidence": "HIGH",
            "status_reason": "This snapshot powers multiple portals, so all readers must inherit the same governed count lineage.",
            "drilldown_source": "/dispatch-portal/command",
            "owner": "dispatch-command-center",
            "freshness": "Generated on request.",
        },
        "sections": {
            "drivers_haul": {
                "kpi_name": "Dispatch Driver and Haul Queues",
                "business_definition": "Drivers awaiting acknowledgement plus active and blocked haul-cycle counts.",
                "source_of_truth": ["dispatch_assignments", "dispatch_driver_sessions"],
                "formula": {
                    "drivers_unacked": "active_total assignments without acknowledgement inside the dispatch session flow",
                    "active_hauls": "non-terminal active haul assignments",
                    "waiting_on_plant": "active haul assignments in plant-wait state",
                    "waiting_on_dump": "active haul assignments in dump-wait state",
                    "breakdown_impacts": "active haul assignments blocked by breakdown state",
                },
                "freshness": "Generated on request.",
                "status_reason": "These counts drive the next dispatch action in both dispatcher and leadership views.",
            },
            "fleet_shop": {
                "kpi_name": "Fleet and Shop Snapshot",
                "business_definition": "Fleet availability, in-shop posture, and shop defect pressure for active operations.",
                "source_of_truth": ["equipment_master", "fleet_status", "fleet_defects"],
                "formula": {
                    "fleet_oos": "fleet rows classified out-of-service by the shared status priority chain",
                    "in_shop": "fleet rows currently routed through the shop or maintenance hold",
                    "shop_defects_open": "open shop defects",
                    "active_recovery": "shop recovery rows still in repair",
                    "waiting_on_parts": "shop recovery rows blocked on parts",
                },
                "freshness": "Generated on request.",
                "status_reason": "Dispatch, Shop, and leadership all consume these numbers to understand equipment pressure without inventing alternate tallies.",
            },
            "safety_watch": {
                "kpi_name": "Dispatch Safety Watch",
                "business_definition": "Safety counts surfaced into dispatch-facing workflows because they may block routing or execution.",
                "source_of_truth": ["incidents", "corrective_actions"],
                "formula": {
                    "incidents_open": "operator-visible incidents not in a terminal closed state",
                    "corrective_actions_open": "operator-visible corrective actions not in terminal status",
                },
                "freshness": "Generated on request.",
                "status_reason": "These are shared safety counts, intentionally re-expressed for dispatch and leadership watchlists.",
            },
            "command_strip": {
                "kpi_name": "Dispatch Command Strip",
                "business_definition": "Always-on summary tiles at the top of the Dispatch Command Center.",
                "source_of_truth": base_sources,
                "formula": "Each tile maps directly to a field inside the dispatch command summary payload.",
                "freshness": "Generated on request.",
                "status_reason": "The command strip is the highest-visibility consumer of the summary and must show governed lineage for every count.",
            },
            "shop_recovery": {
                "kpi_name": "Shop Recovery Snapshot",
                "business_definition": "Shop-specific recovery counts reused from the dispatch command summary shop channel.",
                "source_of_truth": ["fleet_defects", "fleet_status"],
                "formula": "Shop hub tiles reuse the shop subsection of the dispatch command summary without local recalculation.",
                "freshness": "Generated on request.",
                "status_reason": "Shop readers must see the same governed counts the dispatch summary exposes to Dispatch and leadership.",
            },
            "overview": {
                "kpi_name": "Dispatch Command Overview Cards",
                "business_definition": "Overview cards inside the command center that mirror fleet, driver, haul, shop, and integration posture.",
                "source_of_truth": base_sources,
                "formula": "Each overview card is a direct read of the shared summary envelope; no alternate frontend calculation is allowed.",
                "freshness": "Generated on request.",
                "status_reason": "The overview cards must stay aligned with the command strip and portal hubs that reuse the same summary endpoint.",
            },
        },
    }


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
    """Compose Live Fleet Board rows.

    Phase 3 operational-truth refactor:
      - Status derived via the 10-rule priority chain (OOS > In Shop >
        Failed DVIR > Maintenance Hold > Active Haul > Assigned Dispatch
        > Active Shift > Available > GPS-Only > Unknown).
      - Phantom trucks (referenced by an active assignment but absent
        from equipment_master) surface as synthetic rows tagged
        `not_in_asset_spine` so the dispatcher can see them.
      - Trust states populate blank values explicitly: no_assignment,
        no_driver, no_job, no_gps, not_mapped.
    """
    fleet_idx, defect_idx, insp_idx, active_assn_idx, motive_idx = await asyncio.gather(
        _fleet_status_index(db),
        _open_defects_index(db),
        _latest_inspection_index(db),
        _active_assignments_by_truck(db, tenant_id),
        _motive_mapping_index(db),
    )

    motive_vehicle_ids: List[str] = []
    for m in motive_idx.values():
        vid = (m.get("motive") or {}).get("vehicle_id")
        if vid:
            motive_vehicle_ids.append(str(vid))
    motive_event_idx = await _latest_motive_event_by_vehicle(db, motive_vehicle_ids)

    # Active driver sessions keyed by truck_id (for "Active Shift" rule)
    sessions_by_truck: Dict[str, Dict[str, Any]] = {}
    async for s in db.dispatch_driver_sessions.find(
        {"tenant_id": tenant_id, "revoked_at": None},
        {"_id": 0, "truck_id": 1, "driver_name": 1, "driver_id": 1, "trailer_id": 1},
    ):
        t = s.get("truck_id")
        if t and t not in sessions_by_truck:
            sessions_by_truck[str(t)] = s

    rows: List[Dict[str, Any]] = []
    seen_units: set = set()
    counts = {
        "total": 0, "active": 0, "oos": 0, "in_shop": 0,
        "available": 0, "unknown": 0,
        "unmapped": 0, "unsynced": 0,
        "needs_mapping": 0, "motive_only": 0, "not_in_spine": 0,
    }

    def _classify_status(*, em_status: str, fleet_status_status: str,
                          last_dvir_fail: int, open_defects: int,
                          maintenance_hold: bool, active_assn: bool,
                          active_session: bool, motive_mapped: bool,
                          in_spine: bool) -> str:
        # Priority chain (per directive §3B)
        if (em_status or "").lower() in ("out of service", "down") or \
           fleet_status_status == "oos":
            return "oos"
        if fleet_status_status == "in_shop" or (em_status or "").lower() == "maintenance hold":
            return "in_shop"
        if last_dvir_fail > 0:
            return "failed_dvir"
        if maintenance_hold:
            return "maintenance_hold"
        if active_assn:
            return "active_haul"
        if active_session:
            return "active_shift"
        if fleet_status_status == "available":
            return "available"
        if motive_mapped and not in_spine:
            return "motive_only"
        if not in_spine:
            return "not_in_spine"
        return "unknown"

    # ── Iterate canonical Asset Spine assets first ────────────────
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
        seen_units.add(str(unit))
        counts["total"] += 1

        fleet_row = fleet_idx.get(str(unit), {})
        defects = defect_idx.get(str(unit), [])
        insp = insp_idx.get(str(unit))
        active_assn = active_assn_idx.get(str(unit))
        session = sessions_by_truck.get(str(unit))
        mapping = motive_idx.get(str(unit))
        motive_event = None
        if mapping:
            vid = (mapping.get("motive") or {}).get("vehicle_id")
            if vid:
                motive_event = motive_event_idx.get(str(vid))
        else:
            counts["unmapped"] += 1
            counts["unsynced"] += 1

        em_status = asset.get("asset_status") or asset.get("status") or ""
        status = _classify_status(
            em_status=em_status,
            fleet_status_status=fleet_row.get("status", ""),
            last_dvir_fail=int((insp or {}).get("fail_count", 0) or 0),
            open_defects=len(defects),
            maintenance_hold=bool(asset.get("maintenance_hold")),
            active_assn=bool(active_assn),
            active_session=bool(session),
            motive_mapped=bool(mapping),
            in_spine=True,
        )

        # KPI buckets (operational truth)
        if status in ("active_haul", "active_shift"):
            counts["active"] += 1
        elif status == "oos":
            counts["oos"] += 1
        elif status in ("in_shop", "failed_dvir", "maintenance_hold"):
            counts["in_shop"] += 1
        elif status == "available":
            counts["available"] += 1
        else:
            counts["unknown"] += 1

        # Derive driver/job using the priority chain
        current_driver_name = (
            (active_assn or {}).get("driver_name")
            or (session or {}).get("driver_name")
            or "no_driver"
        )
        current_driver_id = (
            (active_assn or {}).get("driver_id")
            or (session or {}).get("driver_id")
            or None
        )
        current_project = (active_assn or {}).get("project_number") or "no_job"

        rows.append({
            "asset_id": asset.get("id") or asset.get("asset_id"),
            "unit_number": unit,
            "asset_type": asset.get("type") or asset.get("asset_type"),
            "asset_category": asset.get("category") or asset.get("asset_category"),
            "make_model": asset.get("make_model") or asset.get("model"),
            "in_asset_spine": True,
            "status": status,
            "active_assignment_id": (active_assn or {}).get("id"),
            "current_state": (active_assn or {}).get("current_state"),
            "current_project_number": current_project,
            "current_driver_name": current_driver_name,
            "current_driver_id": current_driver_id,
            "has_active_shift": bool(session),
            "last_dvir_kind": (insp or {}).get("kind"),
            "last_dvir_at": (insp or {}).get("created_at"),
            "last_dvir_fail_count": int((insp or {}).get("fail_count", 0) or 0),
            "open_defect_count": len(defects),
            "fleet_status_raw": fleet_row.get("status") or "no_status",
            "motive": _motive_template(mapping, motive_event),
            "maintainx": _maintainx_template(),
            "fleetwatcher": _fleetwatcher_template(),
            "last_activity_at": (
                (active_assn or {}).get("last_transition_at")
                or (motive_event or {}).get("event_at")
                or (insp or {}).get("created_at")
                or "no_recent_activity"
            ),
        })

    # ── Phantom trucks — referenced by active assignments but absent
    #    from equipment_master. Surface them as synthetic rows so the
    #    dispatcher can see them and the data team can map them.
    for unit, assn in active_assn_idx.items():
        if unit in seen_units:
            continue
        counts["total"] += 1
        counts["not_in_spine"] += 1
        counts["needs_mapping"] += 1
        # Active in dispatch → KPI counts as active
        counts["active"] += 1
        mapping = motive_idx.get(str(unit))
        motive_event = None
        if mapping:
            vid = (mapping.get("motive") or {}).get("vehicle_id")
            if vid:
                motive_event = motive_event_idx.get(str(vid))
        rows.append({
            "asset_id": None,
            "unit_number": unit,
            "asset_type": "needs_mapping",
            "asset_category": "needs_mapping",
            "make_model": None,
            "in_asset_spine": False,
            "status": "not_in_spine",
            "needs_mapping": True,
            "active_assignment_id": assn.get("id"),
            "current_state": assn.get("current_state"),
            "current_project_number": assn.get("project_number") or "no_job",
            "current_driver_name": assn.get("driver_name") or "no_driver",
            "current_driver_id": assn.get("driver_id"),
            "has_active_shift": False,
            "last_dvir_kind": None,
            "last_dvir_at": None,
            "last_dvir_fail_count": 0,
            "open_defect_count": 0,
            "fleet_status_raw": "not_in_spine",
            "motive": _motive_template(mapping, motive_event),
            "maintainx": _maintainx_template(),
            "fleetwatcher": _fleetwatcher_template(),
            "last_activity_at": assn.get("last_transition_at") or "no_recent_activity",
        })

    rank = {
        "oos": 0, "failed_dvir": 1, "in_shop": 2, "maintenance_hold": 3,
        "active_haul": 4, "active_shift": 5, "available": 6,
        "motive_only": 7, "not_in_spine": 8, "unknown": 9,
    }
    rows.sort(key=lambda r: (rank.get(r["status"], 99), r["unit_number"] or ""))
    return {"counts": counts, "rows": rows}


async def _build_drivers(db, tenant_id: str, limit: int) -> Dict[str, Any]:
    """Compose Live Driver Board rows.

    Phase 3 operational-truth refactor: union of
       (active driver_sessions)  ∪  (drivers named on active assignments)
    so that an assignment with `driver_name` but no live session still
    surfaces with explicit `source="assignment_only"` and a
    `needs_session` trust flag.
    """
    # 1) Real sessions
    sessions: List[Dict[str, Any]] = []
    async for s in db.dispatch_driver_sessions.find(
        {"tenant_id": tenant_id, "revoked_at": None},
        {"_id": 0},
    ).limit(int(limit)):
        sessions.append(s)

    # 2) Active assignments
    active_assignments: List[Dict[str, Any]] = []
    async for a in db.dispatch_assignments.find(
        {
            "tenant_id": tenant_id,
            "current_state": {"$nin": list(DLS.TERMINAL_STATES)},
            "cancelled_at": None,
        },
        {"_id": 0},
    ):
        active_assignments.append(a)

    active_by_driver_id: Dict[str, Dict[str, Any]] = {}
    active_by_truck: Dict[str, Dict[str, Any]] = {}
    active_by_driver_name: Dict[str, Dict[str, Any]] = {}
    for a in active_assignments:
        if a.get("driver_id") and a["driver_id"] not in active_by_driver_id:
            active_by_driver_id[a["driver_id"]] = a
        if a.get("truck_id") and a["truck_id"] not in active_by_truck:
            active_by_truck[a["truck_id"]] = a
        if a.get("driver_name") and a["driver_name"] not in active_by_driver_name:
            active_by_driver_name[a["driver_name"]] = a

    insp_idx = await _latest_inspection_index(db)

    # 3) Off-shift today
    day_start = _start_of_utc_day().isoformat()
    off_shift_today = await db.dispatch_driver_sessions.count_documents({
        "tenant_id": tenant_id,
        "revoked_at": {"$gte": day_start},
    })

    rows: List[Dict[str, Any]] = []
    seen_driver_keys: set = set()

    counts = {
        "shifted": 0, "un_acked": 0, "in_breakdown": 0,
        "waiting": 0, "off_shift_today": int(off_shift_today),
        "active_total": 0, "assignment_only": 0, "session_only": 0,
    }

    # ── (a) session-anchored rows ─────────────────────────────────
    for s in sessions:
        driver_id = s.get("driver_id")
        truck_id = s.get("truck_id")
        assn = (active_by_driver_id.get(driver_id) if driver_id else None) or \
               (active_by_truck.get(truck_id) if truck_id else None)
        key = f"sess::{s.get('id')}"
        seen_driver_keys.add(key)
        if driver_id:
            seen_driver_keys.add(f"did::{driver_id}")
        if (s.get("driver_name") or "") in active_by_driver_name:
            seen_driver_keys.add(f"name::{s.get('driver_name')}")

        state = (assn or {}).get("current_state")
        acked_at = (assn or {}).get("acked_at")
        last_transition_at = (assn or {}).get("last_transition_at")
        since_min = _minutes_since(last_transition_at)
        attention_tag = None
        counts["shifted"] += 1
        counts["active_total"] += 1
        counts["session_only"] += 0 if assn else 1
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
        rows.append({
            "source": "session" if assn else "session_only_no_assignment",
            "session_id": s.get("id"),
            "driver_id": driver_id,
            "driver_name": s.get("driver_name") or "no_driver",
            "employee_id": s.get("employee_id"),
            "truck_id": truck_id or "no_truck",
            "trailer_id": s.get("trailer_id") or "no_trailer",
            "company": s.get("company"),
            "material": s.get("material"),
            "shift_started_at": s.get("created_at") or s.get("issued_at"),
            "current_assignment_id": (assn or {}).get("id"),
            "current_state": state or "no_assignment",
            "current_project_number": (assn or {}).get("project_number") or "no_job",
            "current_state_since_min": since_min,
            "acked": bool(acked_at),
            "last_dvir_at": (insp or {}).get("created_at"),
            "last_dvir_pass": (insp or {}).get("fail_count", 0) == 0 if insp else None,
            "communication_status": {
                "last_sms_status": ((assn or {}).get("delivery_log") or [{}])[-1].get("status")
                if (assn or {}).get("delivery_log") else "no_recent_activity",
            },
            "attention_tag": attention_tag,
            "safety_flags": [],
            "fleetwatcher": _fleetwatcher_template(),
        })

    # ── (b) assignment-only rows (driver named but no live session) ─
    for a in active_assignments:
        driver_id = a.get("driver_id")
        driver_name = a.get("driver_name") or "Test Driver"
        if driver_id and f"did::{driver_id}" in seen_driver_keys:
            continue
        if not driver_id and f"name::{driver_name}" in seen_driver_keys:
            continue
        seen_driver_keys.add(f"name::{driver_name}")
        if driver_id:
            seen_driver_keys.add(f"did::{driver_id}")

        state = a.get("current_state")
        since_min = _minutes_since(a.get("last_transition_at"))
        attention_tag = None
        counts["active_total"] += 1
        counts["assignment_only"] += 1
        if state == DLS.BREAKDOWN:
            attention_tag = "BREAKDOWN"
            counts["in_breakdown"] += 1
        elif state == DLS.WAITING:
            counts["waiting"] += 1
            if (since_min or 0) > WAITING_ATTENTION_MIN:
                attention_tag = "WAITING_LONG"
        if not a.get("acked_at"):
            counts["un_acked"] += 1
            attention_tag = attention_tag or "UN_ACKED"

        insp = insp_idx.get(a.get("truck_id")) if a.get("truck_id") else None
        rows.append({
            "source": "assignment_only",      # explicit trust state
            "session_id": None,
            "driver_id": driver_id,
            "driver_name": driver_name,
            "employee_id": None,
            "truck_id": a.get("truck_id") or "no_truck",
            "trailer_id": a.get("trailer_id") or "no_trailer",
            "company": a.get("company") or None,
            "material": a.get("material") or None,
            "shift_started_at": None,         # no_session — explicit
            "needs_session": True,
            "current_assignment_id": a.get("id"),
            "current_state": state,
            "current_project_number": a.get("project_number") or "no_job",
            "current_state_since_min": since_min,
            "acked": bool(a.get("acked_at")),
            "last_dvir_at": (insp or {}).get("created_at") if insp else None,
            "last_dvir_pass": ((insp or {}).get("fail_count", 0) == 0) if insp else None,
            "communication_status": {
                "last_sms_status": ((a.get("delivery_log") or [{}])[-1].get("status"))
                if a.get("delivery_log") else "no_recent_activity",
            },
            "attention_tag": attention_tag,
            "safety_flags": [],
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

    # ── Open defect / OOS impact PER PROJECT (Phase 3 truth join) ─
    # For each open defect, find the active or most-recent assignment
    # for that truck and attribute the defect to that project. This
    # surfaces the "what's broken on my job" question.
    defect_truck_units: List[str] = []
    open_defects: List[Dict[str, Any]] = []
    async for d in db.fleet_defects.find(
        {"status": {"$in": ["open", "acknowledged"]}},
        {"_id": 0, "id": 1, "truck_unit_number": 1, "severity": 1},
    ):
        if d.get("truck_unit_number"):
            defect_truck_units.append(d["truck_unit_number"])
            open_defects.append(d)

    defect_impact_by_project: Dict[str, int] = {}
    if defect_truck_units:
        recent_assn_by_truck: Dict[str, str] = {}
        async for a in db.dispatch_assignments.find(
            {"tenant_id": tenant_id, "truck_id": {"$in": list(set(defect_truck_units))}},
            {"_id": 0, "truck_id": 1, "project_number": 1, "assigned_at": 1},
        ).sort("assigned_at", -1):
            t = a.get("truck_id")
            if t and t not in recent_assn_by_truck and a.get("project_number"):
                recent_assn_by_truck[t] = a["project_number"]
        for d in open_defects:
            t = d.get("truck_unit_number")
            pn = recent_assn_by_truck.get(t)
            if pn:
                defect_impact_by_project[pn] = defect_impact_by_project.get(pn, 0) + 1

    # ── OOS equipment per project (canonical equipment_master) ────
    oos_equip_by_project: Dict[str, int] = {}
    try:
        async for em in db.equipment_master.find(
            {
                "status": {"$in": ["Out of Service", "Down", "Maintenance Hold"]},
                "current_project_number": {"$nin": [None, ""]},
            },
            {"_id": 0, "current_project_number": 1},
        ):
            pn = em.get("current_project_number") or ""
            if pn:
                oos_equip_by_project[pn] = oos_equip_by_project.get(pn, 0) + 1
    except Exception:
        pass

    # Daily reports (materials in / outbound) today, keyed by project_number.
    # TRACK 28.02B — exclude synthetic/certification rows so dispatch
    # per-project rollups match the operator's visible daily-report list.
    today_yyyy_mm_dd = _now_utc().date().isoformat()
    try:
        async for d in db.daily_reports.find(
            apply_synthetic_dr_exclusion({
                "report_date": today_yyyy_mm_dd,
                "deleted_at": {"$in": [None, "", False]},
            }),
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
        defect_impact = int(defect_impact_by_project.get(pn, 0))
        oos_impact = int(oos_equip_by_project.get(pn, 0))
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
            "defects_impacting": defect_impact,
            "oos_equipment_impacting": oos_impact,
            # V1 placeholders (no computation; null-safe)
            "truck_utilization_pct": None,
            "equipment_utilization_pct": None,
            "attention_tag": (
                "BREAKDOWN" if agg["in_breakdown"] > 0
                else "WAITING" if agg["in_waiting"] > 0
                else "DEFECTS" if defect_impact > 0
                else "OOS" if oos_impact > 0
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
            "kpi_metadata": _summary_kpi_metadata(),
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
            apply_synthetic_corrective_action_exclusion({"status": {"$nin": ["Completed", "Closed", "Cancelled"]}}),
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
