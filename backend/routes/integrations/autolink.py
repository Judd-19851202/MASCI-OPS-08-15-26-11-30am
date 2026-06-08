"""
Integration Center · autolink.py — Motive ↔ MASCI auto-linker.

P1-A: vehicles in `asset_mappings` (asset_kind=vehicle) ↔ `equipment_master`
       Match priority (idempotent · safe · highest-confidence first):
         1. VIN exact (case-insensitive, trimmed)
         2. Unit number exact (case-insensitive, trimmed)
P1-A2: Asset Gateway equipment (asset_kind=equipment) ↔ `equipment_master`
       Match priority:
         1. VIN exact
         2. Motive asset.name ↔ equipment_master.unit_number exact

P1-B: drivers in `employee_mappings` ↔ `employees`
       Match priority:
         1. Email exact (case-insensitive, trimmed)
         2. Driver username ↔ employee email (motive usernames are often `first.last`)
         3. Full name exact (`first_name + last_name` ↔ `employees.name`, case-insensitive)

NEVER overwrites a manual mapping. A mapping is considered "manual" when
`masci_equipment_id` / `masci_employee_id` is already non-empty. Auto-link
only fills empty slots. Every link logs to `integration_sync_logs` and
stamps `mapping_confidence` + `mapping_notes` for audit.

Exposed via:
  POST /api/admin/integrations/motive/auto-link?kind=assets|drivers
  GET  /api/admin/integrations/motive/auto-link/preview?kind=assets|drivers
"""
from __future__ import annotations
import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ._storage import now_iso, write_sync_log

logger = logging.getLogger(__name__)

_WS = re.compile(r"\s+")


def _norm(v: Any) -> str:
    return _WS.sub(" ", str(v or "").strip()).upper()


def _norm_email(v: Any) -> str:
    return str(v or "").strip().lower()


async def _build_em_indexes(db) -> Dict[str, Dict[str, Any]]:
    """Index equipment_master by VIN and unit_number for O(1) lookup."""
    by_vin: Dict[str, Dict[str, Any]] = {}
    by_unit: Dict[str, Dict[str, Any]] = {}
    cursor = db.equipment_master.find(
        {},
        {"_id": 0, "id": 1, "unit_number": 1, "vin_serial_number": 1,
         "make_model": 1, "category": 1, "make": 1, "model": 1, "year": 1,
         "display_label": 1},
    )
    async for d in cursor:
        vin = _norm(d.get("vin_serial_number"))
        unit = _norm(d.get("unit_number"))
        if vin and vin not in by_vin:
            by_vin[vin] = d
        if unit and unit not in by_unit:
            by_unit[unit] = d
    return {"by_vin": by_vin, "by_unit": by_unit}


async def _build_employee_indexes(db) -> Dict[str, Dict[str, Any]]:
    by_email: Dict[str, Dict[str, Any]] = {}
    by_name: Dict[str, Dict[str, Any]] = {}
    cursor = db.employees.find(
        {"is_active": {"$ne": False}},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "phone": 1,
         "trade": 1, "role": 1, "crew": 1, "employee_id": 1, "is_active": 1},
    )
    async for d in cursor:
        em = _norm_email(d.get("email"))
        nm = _norm(d.get("name"))
        if em and em not in by_email:
            by_email[em] = d
        if nm and nm not in by_name:
            by_name[nm] = d
    return {"by_email": by_email, "by_name": by_name}


# ── ASSET LINKER ────────────────────────────────────────────────────
async def _propose_asset_links(db) -> List[Dict[str, Any]]:
    idx = await _build_em_indexes(db)
    by_vin, by_unit = idx["by_vin"], idx["by_unit"]
    proposals: List[Dict[str, Any]] = []
    cursor = db.asset_mappings.find(
        {"provider": "motive"},
        {"_id": 0, "id": 1, "asset_kind": 1, "motive": 1,
         "masci_equipment_id": 1, "masci_unit_number": 1},
    )
    async for m in cursor:
        existing_id = (m.get("masci_equipment_id") or "").strip()
        mv = m.get("motive") or {}
        vin = _norm(mv.get("vin"))
        # vehicles use motive.number, Asset Gateway equipment use motive.name
        number_field = mv.get("number") or mv.get("name") or ""
        unit = _norm(number_field)

        hit: Optional[Dict[str, Any]] = None
        method = ""
        confidence = ""

        if vin and vin in by_vin:
            hit, method, confidence = by_vin[vin], "vin", "high"
        elif unit and unit in by_unit:
            hit, method, confidence = by_unit[unit], "unit_number", "high"

        if not hit:
            proposals.append({
                "mapping_id": m["id"],
                "asset_kind": m.get("asset_kind") or "",
                "motive_vehicle_id": mv.get("vehicle_id") or "",
                "motive_asset_id": mv.get("asset_id") or "",
                "motive_number": number_field,
                "motive_vin": mv.get("vin") or "",
                "match_method": "",
                "match_confidence": "",
                "existing_link": existing_id,
                "candidate_equipment_id": "",
                "candidate_unit_number": "",
                "candidate_display": "",
                "decision": "no_match",
            })
            continue

        candidate_id = hit["id"]
        proposals.append({
            "mapping_id": m["id"],
            "asset_kind": m.get("asset_kind") or "",
            "motive_vehicle_id": mv.get("vehicle_id") or "",
            "motive_asset_id": mv.get("asset_id") or "",
            "motive_number": number_field,
            "motive_vin": mv.get("vin") or "",
            "match_method": method,
            "match_confidence": confidence,
            "existing_link": existing_id,
            "candidate_equipment_id": candidate_id,
            "candidate_unit_number": hit.get("unit_number") or "",
            "candidate_display": hit.get("display_label") or hit.get("make_model") or "",
            "decision": (
                "skip_already_linked_same" if existing_id == candidate_id
                else "skip_manual_link" if existing_id
                else "link"
            ),
        })
    return proposals


async def _apply_asset_links(db, proposals: List[Dict[str, Any]], triggered_by: str) -> Dict[str, int]:
    linked = skipped_manual = noop = conflicts = 0
    for p in proposals:
        if p["decision"] == "skip_manual_link":
            skipped_manual += 1
            continue
        if p["decision"] in ("skip_already_linked_same", "no_match"):
            noop += 1
            continue
        # Look up equipment row for denorm
        eq = await db.equipment_master.find_one(
            {"id": p["candidate_equipment_id"]},
            {"_id": 0, "unit_number": 1, "display_label": 1,
             "make_model": 1, "category": 1},
        )
        if not eq:
            conflicts += 1
            continue
        # Final 1:1 guard — refuse if another mapping already owns this equipment
        existing = await db.asset_mappings.find_one(
            {"masci_equipment_id": p["candidate_equipment_id"]},
            {"_id": 0, "id": 1},
        )
        if existing and existing["id"] != p["mapping_id"]:
            conflicts += 1
            continue
        res = await db.asset_mappings.update_one(
            {"id": p["mapping_id"], "$or": [
                {"masci_equipment_id": ""},
                {"masci_equipment_id": {"$exists": False}},
            ]},
            {"$set": {
                "masci_equipment_id": p["candidate_equipment_id"],
                "masci_unit_number": eq.get("unit_number") or "",
                "masci_equipment_name": eq.get("display_label") or eq.get("make_model") or "",
                "masci_equipment_type": eq.get("category") or "",
                "mapping_confidence": p["match_confidence"],
                "mapping_notes": f"Auto-linked by {p['match_method']} match · {triggered_by} · {now_iso()}",
                "motive.mapping_status": "Mapped",
                "updated_at": now_iso(),
            }},
        )
        if res.modified_count:
            linked += 1
        else:
            skipped_manual += 1
    return {"linked": linked, "skipped_manual": skipped_manual,
            "noop": noop, "conflicts": conflicts}


# ── DRIVER LINKER ───────────────────────────────────────────────────
async def _propose_driver_links(db) -> List[Dict[str, Any]]:
    idx = await _build_employee_indexes(db)
    by_email, by_name = idx["by_email"], idx["by_name"]
    proposals: List[Dict[str, Any]] = []
    cursor = db.employee_mappings.find(
        {"provider": "motive"},
        {"_id": 0, "id": 1, "motive": 1, "masci_employee_id": 1},
    )
    async for m in cursor:
        existing_id = (m.get("masci_employee_id") or "").strip()
        mv = m.get("motive") or {}
        email = _norm_email(mv.get("email"))
        username = _norm_email(mv.get("username"))  # motive often `first.last`
        full_name = _WS.sub(" ", f"{mv.get('first_name') or ''} {mv.get('last_name') or ''}").strip()
        nm = _norm(full_name)

        hit: Optional[Dict[str, Any]] = None
        method = ""
        confidence = ""

        if email and email in by_email:
            hit, method, confidence = by_email[email], "email", "high"
        elif username and username in by_email:
            hit, method, confidence = by_email[username], "username_email", "medium"
        elif nm and nm in by_name:
            hit, method, confidence = by_name[nm], "full_name", "medium"

        if not hit:
            proposals.append({
                "mapping_id": m["id"],
                "motive_driver_id": mv.get("driver_id") or "",
                "motive_name": full_name,
                "motive_email": mv.get("email") or "",
                "motive_username": mv.get("username") or "",
                "match_method": "",
                "match_confidence": "",
                "existing_link": existing_id,
                "candidate_employee_id": "",
                "candidate_employee_name": "",
                "decision": "no_match",
            })
            continue

        candidate_id = hit["id"]
        proposals.append({
            "mapping_id": m["id"],
            "motive_driver_id": mv.get("driver_id") or "",
            "motive_name": full_name,
            "motive_email": mv.get("email") or "",
            "motive_username": mv.get("username") or "",
            "match_method": method,
            "match_confidence": confidence,
            "existing_link": existing_id,
            "candidate_employee_id": candidate_id,
            "candidate_employee_name": hit.get("name") or "",
            "decision": (
                "skip_already_linked_same" if existing_id == candidate_id
                else "skip_manual_link" if existing_id
                else "link"
            ),
        })
    return proposals


async def _apply_driver_links(db, proposals: List[Dict[str, Any]], triggered_by: str) -> Dict[str, int]:
    linked = skipped_manual = noop = conflicts = 0
    for p in proposals:
        if p["decision"] == "skip_manual_link":
            skipped_manual += 1
            continue
        if p["decision"] in ("skip_already_linked_same", "no_match"):
            noop += 1
            continue
        emp = await db.employees.find_one(
            {"id": p["candidate_employee_id"]},
            {"_id": 0, "name": 1, "email": 1, "trade": 1, "role": 1},
        )
        if not emp:
            conflicts += 1
            continue
        existing = await db.employee_mappings.find_one(
            {"masci_employee_id": p["candidate_employee_id"]},
            {"_id": 0, "id": 1},
        )
        if existing and existing["id"] != p["mapping_id"]:
            conflicts += 1
            continue
        res = await db.employee_mappings.update_one(
            {"id": p["mapping_id"], "$or": [
                {"masci_employee_id": ""},
                {"masci_employee_id": {"$exists": False}},
            ]},
            {"$set": {
                "masci_employee_id": p["candidate_employee_id"],
                "masci_employee_name": emp.get("name") or "",
                "masci_employee_email": emp.get("email") or "",
                "masci_employee_trade": emp.get("trade") or "",
                "masci_employee_role": emp.get("role") or "",
                "mapping_notes": f"Auto-linked by {p['match_method']} match · {triggered_by} · {now_iso()}",
                "motive.mapping_status": "Mapped",
                "updated_at": now_iso(),
            }},
        )
        if res.modified_count:
            linked += 1
        else:
            skipped_manual += 1
    return {"linked": linked, "skipped_manual": skipped_manual,
            "noop": noop, "conflicts": conflicts}


# ── HTTP routes ─────────────────────────────────────────────────────
def register_autolink_routes(api_router: APIRouter, db, require_admin) -> None:

    @api_router.get(
        "/admin/integrations/motive/auto-link/preview",
        dependencies=[Depends(require_admin)],
    )
    async def preview_autolink(kind: str = Query(..., regex="^(assets|drivers)$")):
        if kind == "assets":
            props = await _propose_asset_links(db)
        else:
            props = await _propose_driver_links(db)
        counts = {"link": 0, "skip_manual_link": 0, "skip_already_linked_same": 0, "no_match": 0}
        for p in props:
            counts[p["decision"]] = counts.get(p["decision"], 0) + 1
        return {"kind": kind, "counts": counts, "proposals": props}

    @api_router.post(
        "/admin/integrations/motive/auto-link",
        dependencies=[Depends(require_admin)],
    )
    async def execute_autolink(kind: str = Query(..., regex="^(assets|drivers)$")):
        if kind == "assets":
            props = await _propose_asset_links(db)
            result = await _apply_asset_links(db, props, triggered_by="admin_autolink")
            sync_type = "autolink_assets"
        else:
            props = await _propose_driver_links(db)
            result = await _apply_driver_links(db, props, triggered_by="admin_autolink")
            sync_type = "autolink_drivers"
        await write_sync_log(
            db, integration="motive", sync_type=sync_type,
            status="Success" if result["conflicts"] == 0 else "Partial",
            triggered_by="admin",
            records_created=0, records_updated=result["linked"],
            records_skipped=result["noop"] + result["skipped_manual"],
            records_failed=result["conflicts"],
            notes=f"linked={result['linked']} manual_skips={result['skipped_manual']} noop={result['noop']} conflicts={result['conflicts']}",
        )
        return {"ok": True, "kind": kind, **result}

    # M-1R · Reliability supervisor state (read-only)
    @api_router.get(
        "/admin/integrations/motive/reliability-state",
        dependencies=[Depends(require_admin)],
    )
    async def get_reliability_state():
        from lib.motive_reliability import reliability_state_snapshot  # noqa: PLC0415
        snap = reliability_state_snapshot()
        # Plus a derived staleness rollup so the existing IC tile can
        # render "X assets stale >24h / >7d / >30d" without any new
        # collection.
        from datetime import datetime, timezone, timedelta  # noqa: PLC0415
        now = datetime.now(timezone.utc)
        stale = {}
        for label, hrs in (("over_24h", 24), ("over_7d", 24 * 7), ("over_30d", 24 * 30)):
            cut = (now - timedelta(hours=hrs)).isoformat()
            stale[label] = await db.asset_mappings.count_documents({
                "provider": "motive",
                "motive.gps_enabled": True,
                "$or": [
                    {"motive.located_at": {"$lt": cut}},
                    {"motive.located_at": None},
                    {"motive.located_at": {"$exists": False}},
                ],
            })
        snap["staleness"] = stale
        snap["total_gps_enabled"] = await db.asset_mappings.count_documents(
            {"provider": "motive", "motive.gps_enabled": True}
        )
        return snap

    # M-1R · Force-tick (preview verification when SCHEDULER_ENABLED=false)
    # Production runs the scheduled loop; this endpoint is the manual
    # equivalent of one cadence tick. NEVER performs workflow side-
    # effects beyond the underlying sync method.
    @api_router.post(
        "/admin/integrations/motive/reliability-tick",
        dependencies=[Depends(require_admin)],
    )
    async def force_reliability_tick(kind: str = Query(..., regex="^(events|assets|users|geofences)$")):
        from lib.motive_reliability import _tick, reliability_state_snapshot  # noqa: PLC0415
        await _tick(db, kind)
        snap = reliability_state_snapshot()
        return {"ok": True, "kind": kind, "tick_state": snap["loops"][kind]}


__all__ = ["register_autolink_routes"]
