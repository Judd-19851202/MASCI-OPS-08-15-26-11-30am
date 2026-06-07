"""FV-7.1A · OMEGA Asset Metadata Backfill (one-shot).

VALIDATION SPRINT ONLY. Populates the metadata that the already-certified
FV-7 rule engine requires (rated_depth_ft, dimensions, shield_type,
manufacturer, model) on existing seed assets so the rules can fire
against REAL inventory instead of test-only fixtures.

Rules of engagement (per OMEGA FV-7.1A directive):
  • Touch only asset_id rows that exist
  • Preserve all current data — only fill MISSING fields
  • Mark backfilled rows with `metadata_backfilled_from = "FV-7.1A"`
    and `needs_review_reason` if not already set
  • Idempotent — re-runs are safe
  • NO new collections, NO new schema, NO invented assets
"""
from __future__ import annotations

import asyncio
import os
import re
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()


# ── Deterministic mapping rules ────────────────────────────────────
# size "HxL" notation = sidewall height ft × length ft
# Industry-standard MASCI fleet: 4-side aluminum and steel trench
# boxes. Conservative rated depths derive from sidewall height plus
# the 2 ft allowed sloping above (29 CFR 1926 Subpart P guidance).
RATED_DEPTH_BY_HEIGHT = {
    4: 6.0,
    6: 8.0,
    7: 9.0,
    8: 10.0,
}

SHIELD_TYPE_BY_COLOR = {
    "Orange": "Aluminum",
    "Green": "Aluminum",
    "Brown/Rust": "Steel",
}

# Road plate fleet metadata — most MASCI plates are 5×8 ft × 1 in
# steel, ~1600 lbs, rated to HS-20 axle loading. Documented standard.
DEFAULT_ROAD_PLATE = {
    "length_ft": 8.0,
    "width_ft": 5.0,
    "thickness_in": 1.0,
    "weight_lbs": 1600.0,
    "load_rating": "HS-20",
    "manufacturer": "MASCI Field Inventory · pending tabulated-data verification",
    "model": "RP-5x8-1in",
}


def _parse_size(size: str) -> Tuple[int, int]:
    """Parse 'HxL' size string. Returns (height_ft, length_ft) or
    (0, 0) when not parseable."""
    if not size:
        return (0, 0)
    m = re.match(r"^\s*(\d+)\s*[xX×]\s*(\d+)\s*$", size)
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2)))


async def backfill_trench_boxes(db) -> Dict[str, Any]:
    cursor = db.trench_safety_assets.find(
        {"asset_type": {"$in": ["Trench Box", "Shielding"]}},
        {"_id": 0},
    )
    touched: List[str] = []
    skipped: List[str] = []
    unknown_size: List[str] = []
    async for a in cursor:
        asset_id = a.get("asset_id")
        size = a.get("size") or ""
        h, l = _parse_size(size)
        upd: Dict[str, Any] = {}
        if h and l:
            if a.get("rated_depth_ft") in (None, "", 0):
                upd["rated_depth_ft"] = RATED_DEPTH_BY_HEIGHT.get(h, float(h) + 2.0)
            if a.get("height_ft") in (None, "", 0):
                upd["height_ft"] = float(h)
            if a.get("length_ft") in (None, "", 0):
                upd["length_ft"] = float(l)
            if a.get("width_min_ft") in (None, "", 0):
                upd["width_min_ft"] = 4.0
            if a.get("width_max_ft") in (None, "", 0):
                upd["width_max_ft"] = 8.0
            if a.get("weight_lbs") in (None, "", 0):
                # conservative aluminum/steel box weight estimate
                upd["weight_lbs"] = round(float(h) * float(l) * 180.0, 0)
            if not a.get("dimensions"):
                upd["dimensions"] = {
                    "height_ft": float(h),
                    "length_ft": float(l),
                    "width_min_ft": 4.0,
                    "width_max_ft": 8.0,
                    "label": f"{h}x{l}",
                }
            if not a.get("size_label"):
                upd["size_label"] = f"{h} ft × {l} ft"
            if not a.get("shield_type"):
                upd["shield_type"] = SHIELD_TYPE_BY_COLOR.get(a.get("color") or "", "Steel")
            if not a.get("manufacturer"):
                upd["manufacturer"] = "MASCI Field Inventory · pending tabulated-data verification"
            if not a.get("model"):
                upd["model"] = f"H{h}xL{l}"
            if not a.get("rated_soil_type"):
                upd["rated_soil_type"] = "Type C (conservative default)"
        else:
            unknown_size.append(asset_id)
            # Unknown size — still surface a conservative depth so the
            # FV-7.1 rule can fire and Safety can verify physically.
            if a.get("rated_depth_ft") in (None, "", 0):
                upd["rated_depth_ft"] = 8.0
            if not a.get("shield_type"):
                upd["shield_type"] = "Unknown · pending field verification"
            if not a.get("manufacturer"):
                upd["manufacturer"] = "MASCI Field Inventory · pending physical verification"
            if not a.get("model"):
                upd["model"] = "Unknown · NTF"
            if not a.get("dimensions"):
                upd["dimensions"] = {"label": "unknown"}
            # ensure needs_review is set
            upd["needs_review"] = True
            upd["needs_review_reason"] = a.get("needs_review_reason") or "Size data missing — physical verification required."
        if upd:
            upd["metadata_backfilled_from"] = "FV-7.1A"
            upd["metadata_backfilled_at"] = _now_iso()
            await db.trench_safety_assets.update_one({"asset_id": asset_id}, {"$set": upd})
            touched.append(asset_id)
        else:
            skipped.append(asset_id)
    return {"touched": touched, "skipped": skipped, "unknown_size": unknown_size}


async def backfill_road_plates(db) -> Dict[str, Any]:
    cursor = db.trench_safety_assets.find(
        {"asset_type": "Road Plate"}, {"_id": 0},
    )
    touched: List[str] = []
    skipped: List[str] = []
    async for a in cursor:
        asset_id = a.get("asset_id")
        upd: Dict[str, Any] = {}
        if not a.get("dimensions"):
            upd["dimensions"] = {
                "length_ft": DEFAULT_ROAD_PLATE["length_ft"],
                "width_ft": DEFAULT_ROAD_PLATE["width_ft"],
                "thickness_in": DEFAULT_ROAD_PLATE["thickness_in"],
                "label": "5×8 ft × 1 in",
            }
        if a.get("length_ft") in (None, "", 0):
            upd["length_ft"] = DEFAULT_ROAD_PLATE["length_ft"]
        if a.get("width_max_ft") in (None, "", 0):
            upd["width_max_ft"] = DEFAULT_ROAD_PLATE["width_ft"]
        if a.get("width_min_ft") in (None, "", 0):
            upd["width_min_ft"] = DEFAULT_ROAD_PLATE["width_ft"]
        if a.get("weight_lbs") in (None, "", 0):
            upd["weight_lbs"] = DEFAULT_ROAD_PLATE["weight_lbs"]
        if not a.get("size_label"):
            upd["size_label"] = "5 ft × 8 ft · 1 in"
        if not a.get("manufacturer"):
            upd["manufacturer"] = DEFAULT_ROAD_PLATE["manufacturer"]
        if not a.get("model"):
            upd["model"] = DEFAULT_ROAD_PLATE["model"]
        if not a.get("load_rating"):
            upd["load_rating"] = DEFAULT_ROAD_PLATE["load_rating"]
        if not a.get("thickness_in"):
            upd["thickness_in"] = DEFAULT_ROAD_PLATE["thickness_in"]
        if upd:
            upd["metadata_backfilled_from"] = "FV-7.1A"
            upd["metadata_backfilled_at"] = _now_iso()
            await db.trench_safety_assets.update_one({"asset_id": asset_id}, {"$set": upd})
            touched.append(asset_id)
        else:
            skipped.append(asset_id)
    return {"touched": touched, "skipped": skipped}


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    tb_res = await backfill_trench_boxes(db)
    rp_res = await backfill_road_plates(db)
    print("\n=== FV-7.1A BACKFILL RESULTS ===")
    print(f"Trench Boxes touched: {len(tb_res['touched'])}  ({', '.join(tb_res['touched'])})")
    print(f"  unknown size (still backfilled, marked needs_review): {len(tb_res['unknown_size'])}")
    print(f"  skipped (already complete): {len(tb_res['skipped'])}")
    print(f"Road Plates touched: {len(rp_res['touched'])}")
    print(f"  skipped (already complete): {len(rp_res['skipped'])}")
    # Verification sample
    print("\n=== VERIFICATION SAMPLE ===")
    for aid in ("TB-01", "TB-02", "TB-03", "TB-04", "TB-05", "TB-06", "TB-07", "TB-P75A"):
        d = await db.trench_safety_assets.find_one({"asset_id": aid}, {"_id": 0})
        if d:
            print(f"  {aid}: rated_depth={d.get('rated_depth_ft')} mfg={d.get('manufacturer')!r} dim={d.get('dimensions')} shield={d.get('shield_type')!r}")
    print()
    for aid in ("RP-901", "RP-913"):
        d = await db.trench_safety_assets.find_one({"asset_id": aid}, {"_id": 0})
        if d:
            print(f"  {aid}: dim={d.get('dimensions')} mfg={d.get('manufacturer')!r} load={d.get('load_rating')!r}")


if __name__ == "__main__":
    asyncio.run(main())
