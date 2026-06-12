"""
Track 13.7C · Preview-only seed for Shop Recovery Map proof.

THIS SCRIPT WRITES ONLY TO THE PREVIEW DATABASE.

It inserts the minimum number of seed records to exercise both
attention_reason paths (maintenance + inspection) inside the existing
/api/operations-map/snapshot logic, using ONLY the existing collections
and the existing schema shapes. No new collections. No schema changes.
No application code changes.

Every seed row is tagged with:

    _seed_track: "13_7c_preview_proof"

so a single deleteMany() per collection rolls the seed back cleanly.

Usage:
    python3 /app/scripts/preview_seed_13_7c.py seed
    python3 /app/scripts/preview_seed_13_7c.py rollback

Safety guards:
- Refuses to run if APP_ENV != preview OR DB_NAME != masci_safety_preview.
- All writes are idempotent: deletes any prior seed for this track first.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

SEED_TAG = "13_7c_preview_proof"

# Two real Motive-mapped assets selected from the preview DB. Both already
# carry masci_equipment_id and motive.vehicle_id; we add fresh GPS events
# + a defect (A) + an inspection (B) so the snapshot's attention_reason
# branch fires for each.
ASSET_A = {  # maintenance path
    "unit_number": "DPT002-6387",
    "masci_equipment_id": "7b2580e9-87bb-4030-9abd-f34a3f64ed1d",
    "vehicle_id": "1438250",
    "lat": 28.93, "lon": -80.94, "city": "Titusville", "state": "FL",
}
ASSET_B = {  # inspection path
    "unit_number": "DPT007-8803",
    "masci_equipment_id": "095ba9f1-1ad5-4794-81ab-0fa77fcb2736",
    "vehicle_id": "1438252",
    "lat": 29.1201794, "lon": -80.9763211, "city": "Port Orange", "state": "FL",
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def _assert_preview(db) -> None:
    app_env = os.environ.get("APP_ENV", "")
    db_name = os.environ.get("DB_NAME", "")
    if app_env != "preview" or db_name != "masci_safety_preview":
        raise RuntimeError(
            f"Refusing to run · APP_ENV={app_env!r} DB_NAME={db_name!r} · "
            f"this script ONLY runs against the preview DB."
        )
    print(f"[guard] APP_ENV={app_env!r} DB_NAME={db_name!r} · OK")


async def rollback(db) -> None:
    """Delete every seed row tagged with this track."""
    for coll in ("motive_events", "fleet_defects", "equipment_inspections"):
        res = await db[coll].delete_many({"_seed_track": SEED_TAG})
        print(f"[rollback] {coll}: deleted {res.deleted_count}")


async def seed(db) -> None:
    """Insert the minimum proof records."""
    # 0. Always clear previous seed before re-inserting (idempotent).
    await rollback(db)

    now = _now_utc()

    # 1. Fresh motive GPS events that land in band=red (age 3h → ∈ (1h,24h]).
    #    One per vehicle. Sort order: descending event_at — _load_assets_and_events
    #    picks the FIRST event per vehicle_id, so a fresh event wins over stale.
    event_a_at = (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    event_b_at = (now - timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    events = [
        {
            "id": str(uuid.uuid4()),
            "provider": "motive",
            "event_kind": "vehicle_gps",
            "source": "poll",
            "event_at": event_a_at,
            "received_at": now.isoformat(),
            "vehicle_id": ASSET_A["vehicle_id"],
            "lat": ASSET_A["lat"], "lon": ASSET_A["lon"],
            "speed_kph": 0, "bearing": 0,
            "city": ASSET_A["city"], "state": ASSET_A["state"],
            "_seed_track": SEED_TAG,
        },
        {
            "id": str(uuid.uuid4()),
            "provider": "motive",
            "event_kind": "vehicle_gps",
            "source": "poll",
            "event_at": event_b_at,
            "received_at": now.isoformat(),
            "vehicle_id": ASSET_B["vehicle_id"],
            "lat": ASSET_B["lat"], "lon": ASSET_B["lon"],
            "speed_kph": 0, "bearing": 0,
            "city": ASSET_B["city"], "state": ASSET_B["state"],
            "_seed_track": SEED_TAG,
        },
    ]
    res = await db.motive_events.insert_many(events)
    print(f"[seed] motive_events: inserted {len(res.inserted_ids)} (band=red expected)")

    # 2. Open defect tied to ASSET_A.unit_number → triggers attention_reason=maintenance.
    defect = {
        "id": str(uuid.uuid4()),
        "doc_id": "PREVIEW-13.7C-DEFECT",
        "inspection_id": "preview-13_7c-inspection",
        "inspection_kind": "dvir",
        "truck_unit_number": ASSET_A["unit_number"],
        "trailer_unit_number": None,
        "item_text": "Preview-only seed · brake check (TRACK 13.7C)",
        "category": "lights",
        "severity": "oos",
        "status": "open",
        "note": "Preview-only seed for Shop Recovery Map proof.",
        "photos": [],
        "reported_by_employee_id": "",
        "reported_by_name": "Preview Seed (Track 13.7C)",
        "reported_at": now.isoformat(),
        "acknowledged_at": None,
        "acknowledged_by_name": None,
        "repaired_at": None,
        "repaired_by_name": None,
        "repair_notes": "",
        "repair_photos": [],
        "cleared_at": None,
        "cleared_by_name": None,
        "external_refs": {"motive_id": None, "maintainx_work_order_id": None},
        "_seed_track": SEED_TAG,
    }
    await db.fleet_defects.insert_one(defect)
    print(f"[seed] fleet_defects: inserted 1 (unit_number={ASSET_A['unit_number']!r})")

    # 3. Open equipment_inspection tied to ASSET_B.masci_equipment_id.
    #    The snapshot's aggregator groups by `$equipment_id` (operations_map_v1.py
    #    line 339), so we set BOTH the existing schema field `equipment_master_id`
    #    AND the snapshot-expected `equipment_id` so the aggregator can match.
    insp = {
        "id": str(uuid.uuid4()),
        "doc_id": "PREVIEW-13.7C-INSP",
        "kind": "pre_op",
        "inspection_date": now.date().isoformat(),
        "inspection_time": now.strftime("%H:%M"),
        "equipment_master_id": ASSET_B["masci_equipment_id"],
        "equipment_id": ASSET_B["masci_equipment_id"],   # matches snapshot aggregator
        "equipment_type": "Truck",
        "equipment_unit": ASSET_B["unit_number"],
        "equipment_make": "",
        "equipment_model": "",
        "equipment_serial": "",
        "form_type": "pre_op",
        "status": "open",          # status MUST NOT be in {closed,completed,passed}
        "checklist": {},
        "corrective_actions": "Preview-only seed (TRACK 13.7C).",
        "deficiency_notes": "Seed row for Shop Recovery Map preview proof.",
        "fail_count": 1,
        "pass_count": 0,
        "na_count": 0,
        "hour_meter": "",
        "odometer": "",
        "location": "Preview",
        "operator_name": "Preview Seed (Track 13.7C)",
        "operator_signature": "",
        "out_of_service": "Yes",
        "project_name": "Preview",
        "project_number": "PREVIEW",
        "photos": [],
        "created_at": now.isoformat(),
        "_seed_track": SEED_TAG,
    }
    await db.equipment_inspections.insert_one(insp)
    print(f"[seed] equipment_inspections: inserted 1 (equipment_id={ASSET_B['masci_equipment_id']!r})")

    # 4. Echo the contract back so the operator can re-verify by inspection.
    print("")
    print("=== SEED COMPLETE ===")
    print(f"  ASSET A · {ASSET_A['unit_number']} (vehicle_id={ASSET_A['vehicle_id']}) · should produce attention_reason=maintenance")
    print(f"  ASSET B · {ASSET_B['unit_number']} (vehicle_id={ASSET_B['vehicle_id']}) · should produce attention_reason=inspection")
    print(f"  Tag on every row: _seed_track = {SEED_TAG!r}")
    print("  Rollback:  python3 /app/scripts/preview_seed_13_7c.py rollback")


async def main(action: str) -> None:
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]
    await _assert_preview(db)
    try:
        if action == "seed":
            await seed(db)
        elif action == "rollback":
            await rollback(db)
        else:
            raise SystemExit(f"unknown action {action!r}; expected 'seed' or 'rollback'")
    finally:
        cli.close()


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "seed"
    asyncio.run(main(action))
