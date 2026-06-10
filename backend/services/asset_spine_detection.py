"""
services/asset_spine_detection.py · FORGEDOPS P0.1 · Read-only detectors.

Pure functions over the operational collections. NEVER writes. Returns
structured findings the AssetSpine health-scan persists into
`asset_spine_health_runs` for audit.

Detectors:
  - duplicates (vin / serial / unit_number)
  - retired_but_active (active=false + recent motive event)
  - orphaned (active=true + no activity in 30 days)
  - unsynced (active=true + no asset_mappings entry)
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


async def detect_duplicates(db) -> List[Dict[str, Any]]:
    """Return groups of equipment_master docs sharing vin / serial / unit."""
    findings: List[Dict[str, Any]] = []
    for field, label in (("vin_serial_number", "vin"), ("serial_number", "serial"), ("unit_number", "unit_number")):
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        cur = db.equipment_master.find(
            {field: {"$exists": True, "$ne": None, "$ne": ""}},
            {"_id": 0, "id": 1, "unit_number": 1, "label": 1, field: 1, "is_active": 1, "active": 1},
        )
        async for doc in cur:
            v = (doc.get(field) or "").strip().lower()
            if not v:
                continue
            groups[v].append(doc)
        for v, docs in groups.items():
            if len(docs) > 1:
                findings.append({
                    "field": label,
                    "value": v,
                    "asset_ids": [d.get("id") for d in docs],
                    "unit_numbers": [d.get("unit_number") for d in docs],
                    "active_flags": [bool(d.get("is_active") if d.get("is_active") is not None else d.get("active", True)) for d in docs],
                })
    return findings


async def detect_retired_but_active(db) -> List[Dict[str, Any]]:
    """active=false in equipment_master, but Motive event within last 72 h."""
    findings: List[Dict[str, Any]] = []
    cutoff = _iso(_now() - timedelta(hours=72))
    # Retired assets.
    cur = db.equipment_master.find(
        {"$or": [{"is_active": False}, {"active": False}, {"asset_status": "RETIRED"}, {"status": "RETIRED"}]},
        {"_id": 0, "id": 1, "unit_number": 1, "label": 1},
    )
    retired_ids: List[Dict[str, Any]] = []
    async for d in cur:
        retired_ids.append(d)
    if not retired_ids:
        return findings
    # For each, check Motive mapping → recent events.
    for asset in retired_ids:
        unit = asset.get("unit_number")
        aid = asset.get("id")
        mapping = await db.asset_mappings.find_one({
            "$or": [{"masci_equipment_id": aid}, {"masci_unit_number": unit}]
        })
        if not mapping:
            continue
        motive_id = mapping.get("motive_asset_id")
        if not motive_id:
            continue
        recent = await db.motive_events.find_one({
            "motive_asset_id": motive_id,
            "event_at": {"$gte": cutoff},
        })
        if recent:
            findings.append({
                "asset_id": aid,
                "unit_number": unit,
                "asset_name": asset.get("label"),
                "motive_asset_id": motive_id,
                "last_event_at": recent.get("event_at"),
                "severity": "high",
            })
    return findings


async def detect_orphaned(db) -> List[Dict[str, Any]]:
    """active=true + no Motive event in 30 days + no inspection in 30 days."""
    findings: List[Dict[str, Any]] = []
    cutoff = _iso(_now() - timedelta(days=30))
    cur = db.equipment_master.find(
        {"$and": [
            {"$or": [{"is_active": True}, {"active": True}, {"is_active": {"$exists": False}}]},
            {"$or": [{"retired_at": None}, {"retired_at": {"$exists": False}}]},
        ]},
        {"_id": 0, "id": 1, "unit_number": 1, "label": 1},
    )
    active_assets: List[Dict[str, Any]] = []
    async for d in cur:
        active_assets.append(d)
    for asset in active_assets:
        unit = asset.get("unit_number")
        aid = asset.get("id")
        # Mapping → events.
        mapping = await db.asset_mappings.find_one({
            "$or": [{"masci_equipment_id": aid}, {"masci_unit_number": unit}]
        })
        has_recent_event = False
        if mapping and mapping.get("motive_asset_id"):
            ev = await db.motive_events.find_one({
                "motive_asset_id": mapping["motive_asset_id"],
                "event_at": {"$gte": cutoff},
            })
            has_recent_event = bool(ev)
        # Inspections.
        insp = await db.equipment_inspections.find_one({
            "$or": [{"unit_number": unit}, {"asset_id": aid}],
            "created_at": {"$gte": cutoff},
        })
        has_recent_inspection = bool(insp)
        # Dispatches.
        assn = await db.dispatch_assignments.find_one({
            "$or": [{"truck_id": unit}, {"truck_id": aid}, {"asset_id": aid}],
            "assigned_at": {"$gte": cutoff},
        })
        has_recent_assignment = bool(assn)
        if not (has_recent_event or has_recent_inspection or has_recent_assignment):
            findings.append({
                "asset_id": aid,
                "unit_number": unit,
                "asset_name": asset.get("label"),
                "since_days": 30,
                "severity": "medium",
            })
    return findings


async def detect_unsynced(db) -> List[Dict[str, Any]]:
    """Active assets with no entry in asset_mappings (i.e. not mapped to Motive)."""
    findings: List[Dict[str, Any]] = []
    cur = db.equipment_master.find(
        {"$and": [
            {"$or": [{"is_active": True}, {"active": True}, {"is_active": {"$exists": False}}]},
            {"$or": [{"retired_at": None}, {"retired_at": {"$exists": False}}]},
        ]},
        {"_id": 0, "id": 1, "unit_number": 1, "label": 1, "type": 1, "category": 1},
    )
    async for asset in cur:
        unit = asset.get("unit_number")
        aid = asset.get("id")
        mapping = await db.asset_mappings.find_one({
            "$or": [{"masci_equipment_id": aid}, {"masci_unit_number": unit}]
        })
        if not mapping:
            findings.append({
                "asset_id": aid,
                "unit_number": unit,
                "asset_name": asset.get("label"),
                "type": asset.get("type") or asset.get("category"),
                "severity": "low",
            })
    return findings


async def run_detectors(db) -> Dict[str, List[Dict[str, Any]]]:
    """Run all detectors. Each is read-only and isolated."""
    return {
        "duplicates": await detect_duplicates(db),
        "retired_but_active": await detect_retired_but_active(db),
        "orphaned": await detect_orphaned(db),
        "unsynced": await detect_unsynced(db),
    }
