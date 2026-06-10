"""
scripts/p0_trust_audit.py · FORGEDOPS P0 Trust Sprint · A+C+D combined audit.

READ-ONLY. Executes under the existing preview MONGO_URL using
admin_db_user (which is the very credential being audited).

Outputs:
  - /app/memory/p0_audit_atlas_users.json     (P0-A)
  - /app/memory/p0_audit_production_truth.json (P0-C)
  - /app/memory/p0_audit_truth_gap.json        (P0-D)

This audit is authorized by the operator directive:
    "FORGEDOPS · P0 CRITICAL · ... · Use production only."
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import OperationFailure

load_dotenv("/app/backend/.env")
sys.path.insert(0, "/app/backend")
from routes.pm_command_center import (  # noqa: E402
    normalize_asset_kind, specialty_family_of, ROAD_PLATE_CANONICAL,
)

PREVIEW_DB = "masci_safety_preview"
PROD_DB = "masci_safety"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def audit_atlas_users(client) -> dict:
    """P0-A · enumerate Atlas users visible to this credential."""
    info = {"as_of": _now(), "users": [], "errors": []}
    try:
        result = await client["admin"].command("usersInfo")
        for u in result.get("users", []):
            info["users"].append({
                "user": u.get("user"),
                "db": u.get("db"),
                "roles": [{"role": r.get("role"), "db": r.get("db")}
                           for r in u.get("roles", [])],
            })
    except OperationFailure as e:
        info["errors"].append(f"usersInfo failed: {e.details.get('errmsg', str(e))[:200]}")

    # Connection metadata
    try:
        cs = await client["admin"].command("connectionStatus")
        info["authenticated_as"] = cs.get("authInfo", {}).get("authenticatedUsers", [])
        info["authenticated_roles"] = cs.get("authInfo", {}).get("authenticatedUserRoles", [])
    except Exception as e:
        info["errors"].append(f"connectionStatus failed: {str(e)[:200]}")
    return info


async def count_kinds(db, prefix_label: str) -> dict:
    """Bucket equipment_master into PEOPLE-FLEET-EQUIPMENT-SPECIALTY-OPERATIONS counts."""
    FLEET = {"truck", "dump trucks", "dump truck", "haul truck",
              "tractor trailer trucks", "service trucks", "flatbed trucks",
              "pickup trucks", "water trucks", "misc trucks",
              "supervisor / mgmt trucks", "trailer", "trailers", "semi", "semis"}
    HEAVY = {"excavator", "excavators", "loader", "loaders",
              "dozer", "dozers", "grader", "graders", "road grader", "road graders",
              "roller", "rollers", "paver", "pavers", "paving equipment",
              "mill", "mills", "milling", "milling machine",
              "skid steer", "skid steers", "compactor", "compactors", "backhoe", "backhoes"}

    out = {
        "label": prefix_label,
        "fleet": {"trucks": 0, "trailers": 0, "pickup_trucks": 0,
                  "service_trucks": 0, "semis": 0, "misc_trucks": 0},
        "heavy_equipment": {k: 0 for k in
                             ["excavators", "dozers", "loaders", "rollers",
                              "graders", "pavers", "mills", "skid_steers",
                              "compactors", "backhoes", "misc"]},
        "specialty": {"trench_boxes": 0, "road_plates": 0, "end_panels": 0,
                      "spreaders": 0, "shields": 0, "arrow_boards": 0,
                      "message_boards": 0, "portable_signals": 0,
                      "water_tanks": 0, "fuel_tanks": 0,
                      "generators": 0, "pumps": 0, "light_towers": 0,
                      "air_compressors": 0},
        "by_family": {"trench_safety": 0, "access_protection": 0,
                       "traffic_control": 0, "support": 0},
        "motive_mapped": 0, "motive_unmapped": 0,
        "total_assets": 0,
        "unknown_kind": 0,
    }

    async for em in db.equipment_master.find(
        {"$or": [{"is_active": {"$ne": False}}, {"active": {"$ne": False}}]},
        {"_id": 0, "type": 1, "asset_type": 1, "category": 1, "motive_truck_id": 1},
    ):
        out["total_assets"] += 1
        raw = em.get("type") or em.get("asset_type") or em.get("category") or ""
        k = (normalize_asset_kind(raw) or "").lower()

        # Motive
        if em.get("motive_truck_id"): out["motive_mapped"] += 1
        else: out["motive_unmapped"] += 1

        # Fleet
        if k in FLEET:
            if k in ("truck", "dump trucks", "dump truck", "haul truck",
                      "tractor trailer trucks", "misc trucks", "supervisor / mgmt trucks",
                      "water trucks"):
                out["fleet"]["trucks"] += 1
            elif k in ("pickup trucks",): out["fleet"]["pickup_trucks"] += 1
            elif k in ("service trucks", "flatbed trucks"): out["fleet"]["service_trucks"] += 1
            elif k in ("trailer", "trailers"): out["fleet"]["trailers"] += 1
            elif k in ("semi", "semis"): out["fleet"]["semis"] += 1
            else: out["fleet"]["misc_trucks"] += 1
        # Heavy
        elif k in HEAVY:
            if "excavator" in k: out["heavy_equipment"]["excavators"] += 1
            elif "dozer" in k: out["heavy_equipment"]["dozers"] += 1
            elif "loader" in k: out["heavy_equipment"]["loaders"] += 1
            elif "roller" in k: out["heavy_equipment"]["rollers"] += 1
            elif "grader" in k: out["heavy_equipment"]["graders"] += 1
            elif "paver" in k: out["heavy_equipment"]["pavers"] += 1
            elif "mill" in k: out["heavy_equipment"]["mills"] += 1
            elif "skid" in k: out["heavy_equipment"]["skid_steers"] += 1
            elif "compactor" in k: out["heavy_equipment"]["compactors"] += 1
            elif "backhoe" in k: out["heavy_equipment"]["backhoes"] += 1
            else: out["heavy_equipment"]["misc"] += 1
        else:
            # Specialty
            fam = specialty_family_of(k)
            if fam:
                out["by_family"][fam] += 1
                if k == ROAD_PLATE_CANONICAL: out["specialty"]["road_plates"] += 1
                elif "trench" in k: out["specialty"]["trench_boxes"] += 1
                elif "end" in k and "panel" in k: out["specialty"]["end_panels"] += 1
                elif "spreader" in k: out["specialty"]["spreaders"] += 1
                elif "shield" in k: out["specialty"]["shields"] += 1
                elif "arrow" in k: out["specialty"]["arrow_boards"] += 1
                elif "message" in k: out["specialty"]["message_boards"] += 1
                elif "signal" in k: out["specialty"]["portable_signals"] += 1
                elif "water" in k: out["specialty"]["water_tanks"] += 1
                elif "fuel" in k: out["specialty"]["fuel_tanks"] += 1
                elif "generator" in k: out["specialty"]["generators"] += 1
                elif "pump" in k: out["specialty"]["pumps"] += 1
                elif "light" in k: out["specialty"]["light_towers"] += 1
                elif "compressor" in k: out["specialty"]["air_compressors"] += 1
            else:
                out["unknown_kind"] += 1
    return out


async def count_people_and_ops(db, label: str) -> dict:
    out = {"label": label}
    out["employees"] = await db.employees.count_documents({})
    # Drivers: employees with role "driver" or attached to dispatch
    out["drivers_in_employees"] = await db.employees.count_documents(
        {"$or": [{"role": "driver"}, {"position": {"$regex": "driver", "$options": "i"}}]})
    out["pms_in_jobs"] = len(await db.jobs_master.distinct("pm_email", {}))
    out["projects_active"] = await db.jobs_master.count_documents(
        {"$or": [{"is_active": {"$ne": False}}, {"active": {"$ne": False}}],
          "deleted_at": {"$in": [None, "", False]}})
    out["projects_inactive"] = await db.jobs_master.count_documents(
        {"$or": [{"is_active": False}, {"active": False}]})
    try:
        out["active_dispatches"] = await db.dispatch_assignments.count_documents(
            {"current_state": {"$nin": ["delivered", "completed", "cancelled", "failed"]},
              "cancelled_at": None})
    except Exception:
        out["active_dispatches"] = "n/a"
    out["incidents_open"] = await db.incidents.count_documents(
        {"resolution_status": {"$ne": "Closed"}})
    out["capas_open"] = await db.corrective_actions.count_documents(
        {"status": {"$nin": ["Completed", "Closed", "Cancelled"]}})
    out["defects_open"] = await db.fleet_defects.count_documents(
        {"status": {"$in": ["open", "acknowledged"]}})
    return out


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])

    # P0-A
    user_audit = await audit_atlas_users(client)
    open("/app/memory/p0_audit_atlas_users.json", "w").write(json.dumps(user_audit, indent=2))

    # P0-C — read PRODUCTION (the very risk being audited; explicit per directive)
    prod_db = client[PROD_DB]
    preview_db = client[PREVIEW_DB]
    prod_assets = await count_kinds(prod_db, "production:masci_safety")
    preview_assets = await count_kinds(preview_db, "preview:masci_safety_preview")
    prod_ops = await count_people_and_ops(prod_db, "production")
    preview_ops = await count_people_and_ops(preview_db, "preview")

    production_truth = {
        "as_of": _now(),
        "audit_authorized_by": "operator OMEGA directive · P0 Trust Sprint · 2026-02-10",
        "method": "READ-ONLY · production DB read from preview pod via shared admin_db_user "
                   "credential (the very gap being audited; this audit is the one-time authorized "
                   "exception per directive).",
        "production": {"assets": prod_assets, "ops": prod_ops},
        "preview": {"assets": preview_assets, "ops": preview_ops},
    }
    open("/app/memory/p0_audit_production_truth.json", "w").write(
        json.dumps(production_truth, indent=2, default=str))

    # P0-D — gap analysis (preview vs production)
    def diff(a, b):
        out = {}
        for k in set(a.keys()) | set(b.keys()):
            av = a.get(k, 0); bv = b.get(k, 0)
            if isinstance(av, (int, float)) and isinstance(bv, (int, float)):
                out[k] = {"preview": av, "production": bv, "delta": bv - av}
            else:
                out[k] = {"preview": av, "production": bv}
        return out

    gaps = {
        "as_of": _now(),
        "fleet_gap": diff(preview_assets["fleet"], prod_assets["fleet"]),
        "heavy_equipment_gap": diff(preview_assets["heavy_equipment"], prod_assets["heavy_equipment"]),
        "specialty_gap": diff(preview_assets["specialty"], prod_assets["specialty"]),
        "by_family_gap": diff(preview_assets["by_family"], prod_assets["by_family"]),
        "totals": {
            "preview_total": preview_assets["total_assets"],
            "production_total": prod_assets["total_assets"],
            "preview_motive_mapped": preview_assets["motive_mapped"],
            "production_motive_mapped": prod_assets["motive_mapped"],
            "preview_motive_unmapped": preview_assets["motive_unmapped"],
            "production_motive_unmapped": prod_assets["motive_unmapped"],
        },
        "ops_gap": diff(preview_ops, prod_ops),
    }
    open("/app/memory/p0_audit_truth_gap.json", "w").write(
        json.dumps(gaps, indent=2, default=str))

    # Console summary
    print(json.dumps({
        "atlas_users_found": len(user_audit.get("users", [])),
        "authenticated_as": user_audit.get("authenticated_as"),
        "user_errors": user_audit.get("errors"),
        "preview_total_assets": preview_assets["total_assets"],
        "production_total_assets": prod_assets["total_assets"],
        "preview_motive_mapped": preview_assets["motive_mapped"],
        "production_motive_mapped": prod_assets["motive_mapped"],
        "production_specialty_by_family": prod_assets["by_family"],
        "production_ops": prod_ops,
    }, indent=2, default=str))
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
