"""Idempotent seed for MASCI's 7 known trench boxes.

Re-running this is safe. Each TB-id is checked by asset_id; missing ones
are inserted with the documented values; existing ones are left alone
except for the equipment_master mirror, which is upserted.

Per OMEGA DIRECTIVE — no invented assets. Seven physical units only.
"""
from __future__ import annotations

import uuid
from typing import Dict, List

from ._helpers import now_iso, upsert_equipment_master_mirror, write_audit


# Per directive — seed only the documented MASCI fleet.
_SEED_ASSETS: List[Dict] = [
    {
        "asset_id": "TB-01",
        "asset_type": "Trench Box",
        "size": "6x24",
        "serial_number": "C080102",
        "color": "Brown/Rust",
        "condition": "Fair",
    },
    {
        "asset_id": "TB-02",
        "asset_type": "Trench Box",
        "size": "7x8",
        "serial_number": "29809",
        "color": "Orange",
        "condition": "Good",
    },
    {
        "asset_id": "TB-03",
        "asset_type": "Trench Box",
        "size": "4x24",
        "serial_number": "10087437",
        "color": "Green",
        "condition": "Fair",
    },
    {
        "asset_id": "TB-04",
        "asset_type": "Trench Box",
        "size": "8x16",
        "serial_number": "6890902",
        "color": "Brown/Rust",
        "condition": "Fair",
    },
    {
        "asset_id": "TB-05",
        "asset_type": "Trench Box",
        "size": "8x16",
        # Per directive: TB-05 must create a Missing Serial Number /
        # Needs Review alert. We do NOT fabricate a serial number.
        "serial_number": "",
        "color": "Brown/Rust",
        "condition": "Fair",
        "missing_serial_number": True,
        "needs_review": True,
        "needs_review_reason": "Missing serial number — physical plate verification required.",
    },
    {
        "asset_id": "TB-06",
        "asset_type": "Trench Box",
        "size": "4x24",
        "serial_number": "40612",
        "color": "Orange",
        "condition": "Good",
    },
    {
        "asset_id": "TB-07",
        "asset_type": "Trench Box",
        "size": "8x24",
        "serial_number": "C078079",
        "color": "Green",
        "condition": "Fair",
    },
]


def _public_qr_url(asset_id: str) -> str:
    """Public mobile URL embedded in the printed QR label."""
    # No hard-coded host — frontend bundles already serve the same
    # path from any approved origin. The label printer uses this
    # string as the QR payload.
    return f"/trench-safety/assets/{asset_id}"


async def seed_trench_safety_assets(db) -> Dict[str, int]:
    """Seed the 7 MASCI trench boxes if missing. Returns counts.

    Idempotent. Safe to call at every backend boot.
    """
    inserted = 0
    mirrored = 0
    skipped = 0

    for spec in _SEED_ASSETS:
        existing = await db.trench_safety_assets.find_one(
            {"asset_id": spec["asset_id"]},
            {"_id": 0},
        )
        if existing:
            # Re-mirror to keep equipment_master in lockstep
            await upsert_equipment_master_mirror(db, existing)
            mirrored += 1
            skipped += 1
            continue

        doc = _build_seed_doc(spec)
        await db.trench_safety_assets.insert_one(doc)
        # MongoDB mutates the input dict with _id; strip before any reuse
        doc.pop("_id", None)
        await upsert_equipment_master_mirror(db, doc)
        await write_audit(
            db,
            kind="trench_asset_seeded",
            asset_id=doc["asset_id"],
            actor={"_actor": "system", "name": "seed"},
            detail={"source": "phase_2_seed"},
        )
        inserted += 1
        mirrored += 1

    # Defensive: ensure the indexes we rely on exist
    try:
        await db.trench_safety_assets.create_index("asset_id", unique=True)
        await db.trench_safety_assets.create_index("operational_status")
        await db.trench_safety_assets.create_index("asset_type")
        await db.trench_safety_inspections.create_index([("asset_id", 1), ("submitted_at", -1)])
        await db.trench_safety_repairs.create_index([("asset_id", 1), ("status", 1)])
        await db.trench_safety_deployments.create_index([("asset_id", 1), ("assigned_at", -1)])
        await db.trench_safety_qr_scans.create_index([("asset_id", 1), ("scanned_at", -1)])
    except Exception:  # noqa: BLE001 — indexes are best-effort; never fail boot
        pass

    return {"inserted": inserted, "mirrored": mirrored, "skipped": skipped}


def _build_seed_doc(spec: Dict) -> Dict:
    asset_id = spec["asset_id"]
    return {
        "id": str(uuid.uuid4()),
        "asset_id": asset_id,
        "asset_category": "Trench Safety",
        "asset_type": spec.get("asset_type", "Trench Box"),

        # General
        "manufacturer": spec.get("manufacturer", ""),
        "model": spec.get("model", ""),
        "serial_number": spec.get("serial_number", ""),
        "year_manufactured": spec.get("year_manufactured"),
        "owner": "MASCI",
        "purchase_date": None,
        "purchase_cost": None,
        "notes": spec.get("notes", ""),

        # Physical
        "size": spec.get("size", ""),
        "length_ft": spec.get("length_ft"),
        "width_min_ft": spec.get("width_min_ft"),
        "width_max_ft": spec.get("width_max_ft"),
        "height_ft": spec.get("height_ft"),
        "weight_lbs": spec.get("weight_lbs"),
        "rated_depth_ft": spec.get("rated_depth_ft"),
        "rated_soil_type": spec.get("rated_soil_type", ""),
        "adjustable_range": "",
        "capacity": "",

        # Appearance
        "color": spec.get("color", ""),
        "paint_condition": "",
        "corrosion_level": "",

        # Condition / status
        "condition": spec.get("condition", "Good"),
        "operational_status": "Available",

        # Location
        "current_location": "MASCI Yard",
        "current_project_id": None,
        "current_project_name": None,
        "assigned_to_name": None,
        "assigned_to_role": None,
        "yard_location": "MASCI Yard",

        # Manufacturer reference link (not set during seed — phase 3 admin links these)
        "manufacturer_ref_id": None,

        # Tabulated data link
        "tabulated_data_file_id": None,
        "tabulated_data_filename": "",
        "tabulated_data_missing": True,

        # System
        "qr_code_value": asset_id,
        "qr_url": _public_qr_url(asset_id),
        "last_inspection_at": None,
        "next_inspection_due": None,
        "last_repair_at": None,
        "certification_expires_at": None,

        # Data-quality flags
        "missing_serial_number": bool(spec.get("missing_serial_number", False)),
        "missing_manufacturer": bool(spec.get("missing_manufacturer", True)),  # all seeds lack manufacturer
        "needs_review": bool(spec.get("needs_review", True)),  # all seeds need review (no manufacturer / model data yet)
        "needs_review_reason": spec.get(
            "needs_review_reason",
            "Manufacturer and model data not yet captured — physical plate verification required.",
        ),

        # Lifecycle
        "is_active": True,
        "retired_at": None,
        "retired_reason": None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "created_by": "system:seed",
        "updated_by": "system:seed",
    }
