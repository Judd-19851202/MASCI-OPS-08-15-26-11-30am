"""TRACK 15.73 SLICE 1 · Equipment Trust Restoration · Master Data Audit.

Read-only investigation. Preview DB only.

Schema-aware version — uses ACTUAL field names discovered via Mongo
introspection on 2026-02-11:

  equipment_master        unit_number
  asset_mappings          masci_unit_number, masci_equipment_id, motive.raw.number
  motive_events           raw.number, vehicle_id
  fleet_status            unit_number
  equipment_units         unit_label  (legacy, separate ID space)
  equipment_inspections   equipment_unit, equipment_master_id
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
TARGET_UNIT = "RG007-0869"

if "prod" in DB_NAME.lower() and "preview" not in DB_NAME.lower():
    print(f"REFUSING — DB_NAME={DB_NAME} looks like production")
    sys.exit(2)


def main() -> dict:
    db = MongoClient(MONGO_URL)[DB_NAME]

    # ---------- equipment_master ----------
    em: dict[str, dict] = {}
    em_by_id: dict[str, dict] = {}
    for d in db.equipment_master.find({}, {"_id": 0}):
        u = (d.get("unit_number") or "").strip()
        if u:
            em[u] = d
        if d.get("id"):
            em_by_id[d["id"]] = d

    # ---------- asset_mappings (Motive/MaintainX bridge) ----------
    am_motive_numbers: dict[str, dict] = {}     # by raw.number
    am_masci_units: dict[str, dict] = {}        # by masci_unit_number
    am_masci_ids: dict[str, dict] = {}          # by masci_equipment_id
    am_with_masci_unit = 0
    am_with_masci_id_only = 0
    am_orphan = 0
    for d in db.asset_mappings.find({}, {"_id": 0}):
        masci_unit = (d.get("masci_unit_number") or "").strip()
        masci_id = (d.get("masci_equipment_id") or "").strip()
        motive_number = ""
        motive = d.get("motive") or {}
        if isinstance(motive, dict):
            raw = motive.get("raw") or {}
            if isinstance(raw, dict):
                motive_number = (raw.get("number") or "").strip()
        if motive_number:
            am_motive_numbers[motive_number] = d
        if masci_unit:
            am_masci_units[masci_unit] = d
            am_with_masci_unit += 1
        elif masci_id:
            am_masci_ids[masci_id] = d
            am_with_masci_id_only += 1
        else:
            am_orphan += 1

    # ---------- motive_events ----------
    me_numbers: set[str] = set()
    for d in db.motive_events.find({}, {"_id": 0, "raw": 1, "vehicle_id": 1}).limit(10000):
        raw = d.get("raw") or {}
        if isinstance(raw, dict):
            n = (raw.get("number") or "").strip()
            if n:
                me_numbers.add(n)

    # ---------- fleet_status ----------
    fs_units: set[str] = set()
    fs_real: set[str] = set()  # non-test
    for d in db.fleet_status.find({}, {"_id": 0, "unit_number": 1}):
        u = (d.get("unit_number") or "").strip()
        if u:
            fs_units.add(u)
            if not u.upper().startswith("TEST-") and not u.startswith("COMBO-") and not u.startswith("D51-DT-"):
                fs_real.add(u)

    # ---------- equipment_units (separate ID space — no unit_number) ----------
    eu_count = db.equipment_units.estimated_document_count()

    # ---------- equipment_inspections (Pre-Op submissions) ----------
    ei_units: dict[str, int] = {}
    ei_unit_to_em_id: dict[str, set[str]] = {}
    ei_with_em_id = 0
    ei_without_em_id = 0
    for d in db.equipment_inspections.find(
        {}, {"_id": 0, "equipment_unit": 1, "equipment_master_id": 1}
    ):
        u = (d.get("equipment_unit") or "").strip()
        if u:
            ei_units[u] = ei_units.get(u, 0) + 1
            mid = d.get("equipment_master_id") or ""
            if mid:
                ei_unit_to_em_id.setdefault(u, set()).add(mid)
                ei_with_em_id += 1
            else:
                ei_without_em_id += 1

    # ---------- Universe sets ----------
    em_set = set(em.keys())
    fs_set = fs_units

    # ---------- Gap analysis ----------
    gaps = {
        # Units inspected (real Pre-Op submissions) but NOT in equipment_master:
        "ei_units_not_in_em": sorted(list(set(ei_units.keys()) - em_set)),
        # Motive vehicles whose number is not in equipment_master:
        "motive_numbers_not_in_em": sorted(list(me_numbers - em_set)),
        # asset_mappings rows that link a Motive vehicle to NO masci_unit_number:
        "asset_mappings_with_motive_no_masci_unit": [
            {"motive_number": k, "masci_equipment_id": v.get("masci_equipment_id")}
            for k, v in am_motive_numbers.items()
            if not (v.get("masci_unit_number") or "").strip()
        ][:50],
        # fleet_status units (excluding test) not in equipment_master:
        "fleet_status_real_not_in_em": sorted(list(fs_real - em_set)),
    }

    # ---------- Equipment master coverage of asset_mappings ----------
    am_masci_id_in_em = sum(1 for mid in am_masci_ids if mid in em_by_id)
    am_masci_unit_in_em = sum(1 for u in am_masci_units if u in em_set)

    # ---------- Target unit forensics ----------
    em_doc = em.get(TARGET_UNIT)
    target = {
        "unit": TARGET_UNIT,
        "in_equipment_master": TARGET_UNIT in em,
        "equipment_master_doc": em_doc,
        "in_asset_mappings_as_masci_unit": TARGET_UNIT in am_masci_units,
        "in_asset_mappings_as_motive_number": TARGET_UNIT in am_motive_numbers,
        "asset_mapping_via_em_id": (
            em_doc and em_doc.get("id") in am_masci_ids
        ) if em_doc else False,
        "in_motive_events_raw_number": TARGET_UNIT in me_numbers,
        "in_fleet_status": TARGET_UNIT in fs_units,
        "in_equipment_inspections": TARGET_UNIT in ei_units,
        "inspection_count": ei_units.get(TARGET_UNIT, 0),
    }

    # ---------- Per-category samples ----------
    category_samples: dict[str, list[dict]] = {}
    cat_filters = {
        "Road Graders / Motor Grader": {"$or": [
            {"category": {"$regex": "grader", "$options": "i"}},
            {"preop_equipment_type": {"$regex": "grader", "$options": "i"}},
        ]},
        "Excavators": {"$or": [
            {"category": {"$regex": "excavator", "$options": "i"}},
            {"preop_equipment_type": {"$regex": "excavator", "$options": "i"}},
        ]},
        "Rollers": {"$or": [
            {"category": {"$regex": "roller", "$options": "i"}},
            {"preop_equipment_type": {"$regex": "roller|compactor", "$options": "i"}},
        ]},
        "Pavers": {"$or": [
            {"category": {"$regex": "paver", "$options": "i"}},
            {"preop_equipment_type": {"$regex": "paver", "$options": "i"}},
        ]},
        "Trucks": {"$or": [
            {"category": {"$regex": "truck", "$options": "i"}},
            {"preop_equipment_type": {"$regex": "truck", "$options": "i"}},
        ]},
    }
    for cat, query in cat_filters.items():
        rows = list(
            db.equipment_master.find(
                query,
                {"_id": 0, "id": 1, "unit_number": 1, "category": 1, "company": 1,
                 "make": 1, "model": 1, "preop_equipment_type": 1},
            ).limit(5)
        )
        for r in rows:
            u = (r.get("unit_number") or "").strip()
            mid = r.get("id")
            r["pre_ops_submitted"] = ei_units.get(u, 0)
            r["in_motive_events"] = u in me_numbers
            r["asset_mapping_motive_link"] = u in am_motive_numbers or (
                mid and mid in am_masci_ids
            )
            r["in_fleet_status"] = u in fs_units
        category_samples[cat] = rows

    # ---------- Authority chain analysis ----------
    # Pre-Op lookup chain (from routes/asset_spine.py):
    #   1. equipment_master.find_one({"id": <input>})
    #   2. equipment_master.find_one({"unit_number": <input>})  (case-insensitive)
    # => equipment_master IS authoritative. Other collections are mirrors/audit.
    # 
    # Question: is equipment_master populated reliably? Are external systems
    # forming new units that bypass equipment_master?

    report = {
        "track": "15.73 SLICE 1",
        "db_name": DB_NAME,
        "schema_aware": True,
        "collection_counts": {
            "equipment_master": db.equipment_master.estimated_document_count(),
            "equipment_units": eu_count,
            "asset_mappings": db.asset_mappings.estimated_document_count(),
            "motive_events": db.motive_events.estimated_document_count(),
            "fleet_status": db.fleet_status.estimated_document_count(),
            "equipment_inspections": db.equipment_inspections.estimated_document_count(),
            "safety_equipment_issuances": db.safety_equipment_issuances.estimated_document_count(),
            "safety_equipment_trainings": db.safety_equipment_trainings.estimated_document_count(),
            "maintainx_work_orders": db.maintainx_work_orders.estimated_document_count(),
        },
        "unique_unit_counts": {
            "equipment_master": len(em),
            "asset_mappings_with_motive_number": len(am_motive_numbers),
            "asset_mappings_with_masci_unit_number": len(am_masci_units),
            "asset_mappings_with_masci_id_only": am_with_masci_id_only,
            "asset_mappings_no_masci_link": am_orphan,
            "motive_events_unique_numbers": len(me_numbers),
            "fleet_status_total": len(fs_units),
            "fleet_status_real": len(fs_real),
            "equipment_inspections_unique_units": len(ei_units),
            "equipment_inspections_with_em_id_resolved": ei_with_em_id,
            "equipment_inspections_without_em_id": ei_without_em_id,
        },
        "asset_mappings_em_coverage": {
            "by_masci_unit": f"{am_masci_unit_in_em}/{len(am_masci_units)}",
            "by_masci_id": f"{am_masci_id_in_em}/{len(am_masci_ids)}",
        },
        "target_unit_forensics": target,
        "gaps": {k: {"count": len(v), "examples": v[:25]} for k, v in gaps.items()},
        "category_samples": category_samples,
        "authority_chain": [
            "Pre-Op / DVIR forms call GET /api/asset-spine/taxonomy/by-unit/{u}",
            "Endpoint reads equipment_master only (id then unit_number)",
            "equipment_master IS authoritative source-of-truth",
            "asset_mappings = Motive/MaintainX cross-walk (not consulted by Pre-Op)",
            "motive_events = telemetry only (no equipment registry function)",
            "fleet_status = aggregated DVIR/Pre-Op summary (consumer, not source)",
            "equipment_inspections = Pre-Op submissions (downstream consumer)",
        ],
    }
    return report


if __name__ == "__main__":
    out = main()
    out_path = Path("/app/test_reports/track_15_73_slice1_equipment_audit.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, default=str, indent=2))
    print(f"DB: {out['db_name']}")
    print(json.dumps(out["unique_unit_counts"], indent=2))
    print()
    print(f"TARGET {TARGET_UNIT}:")
    t = out["target_unit_forensics"]
    for k, v in t.items():
        if k == "equipment_master_doc":
            continue
        print(f"  {k}: {v}")
    print()
    print("GAPS:")
    for k, v in out["gaps"].items():
        ex = v["examples"][:10]
        print(f"  {k}: {v['count']} (eg: {ex})")
    print()
    print("CATEGORY SAMPLES (showing field-system coverage):")
    for cat, rows in out["category_samples"].items():
        print(f"  {cat}: {len(rows)} units")
        for r in rows:
            print(f"    {r.get('unit_number', '?'):20s} pre_ops={r.get('pre_ops_submitted',0):3d} motive={r['in_motive_events']:1} amap_motive={r['asset_mapping_motive_link']:1} fleet={r['in_fleet_status']:1}")
    print()
    print(f"Full JSON: {out_path}")
