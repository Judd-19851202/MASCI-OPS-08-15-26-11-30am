"""
Integration Center · mappings.py — master asset + master employee mappings.

The mappings DO NOT duplicate `db.equipment_master` / `db.employees`.
Each mapping doc holds a reference to the existing master record plus
provider-specific ID columns. List endpoints denormalise the display
name from the master at read-time so the UI doesn't have to fan out.

Endpoints:
  Asset Mappings (provider="all"|"motive"|"maintainx"):
    GET    /api/admin/integrations/asset-mappings
    POST   /api/admin/integrations/asset-mappings
    PATCH  /api/admin/integrations/asset-mappings/{id}
    DELETE /api/admin/integrations/asset-mappings/{id}
    GET    /api/admin/integrations/asset-mappings/unmapped — equipment without ANY mapping
  Employee Mappings:
    GET    /api/admin/integrations/employee-mappings
    POST   /api/admin/integrations/employee-mappings
    PATCH  /api/admin/integrations/employee-mappings/{id}
    DELETE /api/admin/integrations/employee-mappings/{id}
    GET    /api/admin/integrations/employee-mappings/unmapped
"""
from __future__ import annotations
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ._models import (
    AssetMappingCreate, AssetMappingUpdate,
    EmployeeMappingCreate, EmployeeMappingUpdate,
)
from ._storage import now_iso

logger = logging.getLogger(__name__)


def _is_mapped_asset(doc: dict) -> bool:
    m = doc.get("motive") or {}
    x = doc.get("maintainx") or {}
    return bool(m.get("vehicle_id") or m.get("asset_id") or x.get("asset_id"))


def _is_mapped_employee(doc: dict) -> bool:
    m = doc.get("motive") or {}
    x = doc.get("maintainx") or {}
    return bool(m.get("driver_id") or x.get("user_id"))


def register_mapping_routes(
    api_router: APIRouter, db, require_admin,
) -> None:

    # ════════════════════════════════════════════════════════════════
    # Asset Mappings
    # ════════════════════════════════════════════════════════════════
    @api_router.get(
        "/admin/integrations/asset-mappings", dependencies=[Depends(require_admin)],
    )
    async def list_asset_mappings(provider: Optional[str] = None):
        q: dict = {}
        if provider == "motive":
            q["motive.vehicle_id"] = {"$ne": ""}
        elif provider == "maintainx":
            q["maintainx.asset_id"] = {"$ne": ""}
        elif provider == "unmapped":
            q = {"$nor": [
                {"motive.vehicle_id": {"$exists": True, "$ne": ""}},
                {"maintainx.asset_id": {"$exists": True, "$ne": ""}},
            ]}
        cursor = db.asset_mappings.find(q, {"_id": 0}).sort("updated_at", -1)
        return await cursor.to_list(2000)

    @api_router.post(
        "/admin/integrations/asset-mappings", dependencies=[Depends(require_admin)],
    )
    async def create_asset_mapping(body: AssetMappingCreate):
        # Resolve display fields from equipment_master so the list view
        # doesn't have to fan out per row.
        eq = await db.equipment_master.find_one(
            {"id": body.masci_equipment_id},
            {"_id": 0, "id": 1, "unit_number": 1, "name": 1, "equipment_type": 1,
             "make": 1, "model": 1, "year": 1, "vin": 1, "license_plate": 1},
        )
        if not eq:
            raise HTTPException(404, f"equipment_master.id not found: {body.masci_equipment_id}")
        # 1:1 enforcement — one mapping per master record
        if await db.asset_mappings.find_one({"masci_equipment_id": body.masci_equipment_id}):
            raise HTTPException(409, "Asset mapping already exists for this equipment_master record")
        doc = {
            "id": str(uuid.uuid4()),
            "masci_equipment_id": body.masci_equipment_id,
            "masci_unit_number": eq.get("unit_number") or "",
            "masci_equipment_name": eq.get("name") or "",
            "masci_equipment_type": eq.get("equipment_type") or "",
            "motive": {
                "vehicle_id": (body.motive_vehicle_id or "").strip(),
                "asset_id": (body.motive_asset_id or "").strip(),
                "driver_id": (body.motive_driver_id or "").strip(),
                "device_id": (body.motive_device_id or "").strip(),
                "gps_enabled": bool(body.motive_gps_enabled),
                "dashcam_enabled": bool(body.motive_dashcam_enabled),
                "last_sync_at": None,
                "mapping_status": "Mapped" if (body.motive_vehicle_id or body.motive_asset_id) else "Unmapped",
            },
            "maintainx": {
                "asset_id": (body.maintainx_asset_id or "").strip(),
                "location_id": (body.maintainx_location_id or "").strip(),
                "pm_schedule_id": (body.maintainx_pm_schedule_id or "").strip(),
                "last_sync_at": None,
                "mapping_status": "Mapped" if body.maintainx_asset_id else "Unmapped",
            },
            "mapping_confidence": body.mapping_confidence or "medium",
            "mapping_notes": body.mapping_notes or "",
            "active": True,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        await db.asset_mappings.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.patch(
        "/admin/integrations/asset-mappings/{mapping_id}",
        dependencies=[Depends(require_admin)],
    )
    async def update_asset_mapping(mapping_id: str, body: AssetMappingUpdate):
        existing = await db.asset_mappings.find_one({"id": mapping_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Not found")
        update = {"updated_at": now_iso()}
        for field in ("vehicle_id", "asset_id", "driver_id", "device_id"):
            v = getattr(body, f"motive_{field}", None)
            if v is not None:
                update[f"motive.{field}"] = v.strip()
        if body.motive_gps_enabled is not None:
            update["motive.gps_enabled"] = bool(body.motive_gps_enabled)
        if body.motive_dashcam_enabled is not None:
            update["motive.dashcam_enabled"] = bool(body.motive_dashcam_enabled)
        for field in ("asset_id", "location_id", "pm_schedule_id"):
            v = getattr(body, f"maintainx_{field}", None)
            if v is not None:
                update[f"maintainx.{field}"] = v.strip()
        if body.mapping_confidence is not None:
            update["mapping_confidence"] = body.mapping_confidence
        if body.mapping_notes is not None:
            update["mapping_notes"] = body.mapping_notes
        if body.active is not None:
            update["active"] = bool(body.active)
        await db.asset_mappings.update_one({"id": mapping_id}, {"$set": update})
        doc = await db.asset_mappings.find_one({"id": mapping_id}, {"_id": 0})
        # Re-stamp mapping_status post-merge
        m = doc.get("motive") or {}
        x = doc.get("maintainx") or {}
        await db.asset_mappings.update_one({"id": mapping_id}, {"$set": {
            "motive.mapping_status": "Mapped" if (m.get("vehicle_id") or m.get("asset_id")) else "Unmapped",
            "maintainx.mapping_status": "Mapped" if x.get("asset_id") else "Unmapped",
        }})
        return await db.asset_mappings.find_one({"id": mapping_id}, {"_id": 0})

    @api_router.delete(
        "/admin/integrations/asset-mappings/{mapping_id}",
        dependencies=[Depends(require_admin)],
    )
    async def delete_asset_mapping(mapping_id: str):
        res = await db.asset_mappings.delete_one({"id": mapping_id})
        if res.deleted_count == 0:
            raise HTTPException(404, "Not found")
        return {"ok": True}

    @api_router.get(
        "/admin/integrations/asset-mappings/unmapped",
        dependencies=[Depends(require_admin)],
    )
    async def list_unmapped_equipment():
        """Equipment in db.equipment_master that has NO mapping yet."""
        mappings = await db.asset_mappings.distinct("masci_equipment_id")
        cursor = db.equipment_master.find(
            {"id": {"$nin": mappings}, "active": {"$ne": False}},
            {"_id": 0, "id": 1, "unit_number": 1, "name": 1, "equipment_type": 1,
             "make": 1, "model": 1, "year": 1, "vin": 1, "license_plate": 1, "active": 1},
        )
        return await cursor.to_list(5000)

    # ════════════════════════════════════════════════════════════════
    # Employee Mappings
    # ════════════════════════════════════════════════════════════════
    @api_router.get(
        "/admin/integrations/employee-mappings", dependencies=[Depends(require_admin)],
    )
    async def list_employee_mappings(provider: Optional[str] = None):
        q: dict = {}
        if provider == "motive":
            q["motive.driver_id"] = {"$ne": ""}
        elif provider == "maintainx":
            q["maintainx.user_id"] = {"$ne": ""}
        elif provider == "unmapped":
            q = {"$nor": [
                {"motive.driver_id": {"$exists": True, "$ne": ""}},
                {"maintainx.user_id": {"$exists": True, "$ne": ""}},
            ]}
        cursor = db.employee_mappings.find(q, {"_id": 0}).sort("updated_at", -1)
        return await cursor.to_list(5000)

    @api_router.post(
        "/admin/integrations/employee-mappings", dependencies=[Depends(require_admin)],
    )
    async def create_employee_mapping(body: EmployeeMappingCreate):
        emp = await db.employees.find_one(
            {"id": body.masci_employee_id},
            {"_id": 0, "id": 1, "name": 1, "email": 1, "phone": 1,
             "trade": 1, "role": 1, "crew": 1, "employee_id": 1},
        )
        if not emp:
            raise HTTPException(404, f"employees.id not found: {body.masci_employee_id}")
        if await db.employee_mappings.find_one({"masci_employee_id": body.masci_employee_id}):
            raise HTTPException(409, "Mapping already exists for this employee")
        doc = {
            "id": str(uuid.uuid4()),
            "masci_employee_id": body.masci_employee_id,
            "masci_employee_name": emp.get("name") or "",
            "masci_employee_trade": emp.get("trade") or "",
            "masci_employee_role": emp.get("role") or "",
            "masci_employee_email": emp.get("email") or "",
            "motive": {
                "driver_id": (body.motive_driver_id or "").strip(),
                "driver_name": (body.motive_driver_name or "").strip(),
                "email": (body.motive_email or "").strip(),
                "safety_score": None,
                "last_sync_at": None,
                "mapping_status": "Mapped" if body.motive_driver_id else "Unmapped",
            },
            "maintainx": {
                "user_id": (body.maintainx_user_id or "").strip(),
                "name": (body.maintainx_name or "").strip(),
                "email": (body.maintainx_email or "").strip(),
                "role": (body.maintainx_role or "").strip(),
                "last_sync_at": None,
                "mapping_status": "Mapped" if body.maintainx_user_id else "Unmapped",
            },
            "mapping_notes": body.mapping_notes or "",
            "active": True,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        await db.employee_mappings.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.patch(
        "/admin/integrations/employee-mappings/{mapping_id}",
        dependencies=[Depends(require_admin)],
    )
    async def update_employee_mapping(mapping_id: str, body: EmployeeMappingUpdate):
        existing = await db.employee_mappings.find_one({"id": mapping_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Not found")
        update = {"updated_at": now_iso()}
        for f in ("driver_id", "driver_name", "email"):
            v = getattr(body, f"motive_{f}", None)
            if v is not None:
                update[f"motive.{f}"] = v.strip()
        for f in ("user_id", "name", "email", "role"):
            v = getattr(body, f"maintainx_{f}", None)
            if v is not None:
                update[f"maintainx.{f}"] = v.strip()
        if body.mapping_notes is not None:
            update["mapping_notes"] = body.mapping_notes
        if body.active is not None:
            update["active"] = bool(body.active)
        await db.employee_mappings.update_one({"id": mapping_id}, {"$set": update})
        # Recompute statuses
        doc = await db.employee_mappings.find_one({"id": mapping_id}, {"_id": 0})
        m = doc.get("motive") or {}
        x = doc.get("maintainx") or {}
        await db.employee_mappings.update_one({"id": mapping_id}, {"$set": {
            "motive.mapping_status": "Mapped" if m.get("driver_id") else "Unmapped",
            "maintainx.mapping_status": "Mapped" if x.get("user_id") else "Unmapped",
        }})
        return await db.employee_mappings.find_one({"id": mapping_id}, {"_id": 0})

    @api_router.delete(
        "/admin/integrations/employee-mappings/{mapping_id}",
        dependencies=[Depends(require_admin)],
    )
    async def delete_employee_mapping(mapping_id: str):
        res = await db.employee_mappings.delete_one({"id": mapping_id})
        if res.deleted_count == 0:
            raise HTTPException(404, "Not found")
        return {"ok": True}

    @api_router.get(
        "/admin/integrations/employee-mappings/unmapped",
        dependencies=[Depends(require_admin)],
    )
    async def list_unmapped_employees():
        mapped_ids = await db.employee_mappings.distinct("masci_employee_id")
        cursor = db.employees.find(
            {"id": {"$nin": mapped_ids}},
            {"_id": 0, "id": 1, "name": 1, "email": 1, "phone": 1,
             "trade": 1, "role": 1, "crew": 1, "employee_id": 1},
        )
        return await cursor.to_list(10000)


__all__ = ["register_mapping_routes"]
