"""
Integration Center · imports_exports.py — manual CSV in/out fallback
so MASCI can begin mapping work BEFORE Motive/MaintainX credentials
land.

Imports accept ID-only rows (the simplest possible shape — operator
pastes a CSV with `masci_id, provider_id` columns and we wire the
mapping). Exports stream a CSV download of every mapping doc or every
unmapped record so admins can hand a list to the Motive/MaintainX
account manager.
"""
from __future__ import annotations
import csv
import io
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from ._storage import now_iso, write_sync_log

logger = logging.getLogger(__name__)


VALID_KINDS = (
    "motive_vehicles",      # rows: masci_equipment_id, motive_vehicle_id, motive_asset_id, motive_device_id
    "motive_drivers",       # rows: masci_employee_id, motive_driver_id, motive_driver_name, motive_email
    "maintainx_assets",     # rows: masci_equipment_id, maintainx_asset_id, maintainx_location_id
    "maintainx_users",      # rows: masci_employee_id, maintainx_user_id, maintainx_name, maintainx_email
)


def _csv_response(filename: str, header: List[str], rows: List[List[str]]) -> StreamingResponse:
    def gen():
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(header)
        for r in rows:
            w.writerow(r)
            if buf.tell() > 32 * 1024:
                yield buf.getvalue()
                buf.seek(0)
                buf.truncate()
        if buf.tell():
            yield buf.getvalue()

    return StreamingResponse(
        gen(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


def register_import_export_routes(
    api_router: APIRouter, db, require_admin,
) -> None:

    # ════════════════════════════════════════════════════════════════
    # IMPORT
    # ════════════════════════════════════════════════════════════════
    @api_router.post(
        "/admin/integrations/import-csv", dependencies=[Depends(require_admin)],
    )
    async def import_csv(
        kind: str = Form(...),
        file: UploadFile = File(...),
    ):
        if kind not in VALID_KINDS:
            raise HTTPException(400, f"kind must be one of {VALID_KINDS}")
        raw = await file.read()
        if not raw:
            raise HTTPException(400, "Empty file")
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            raise HTTPException(400, "CSV has no rows")

        created = updated = skipped = failed = 0
        errors: list[str] = []

        for i, row in enumerate(rows, start=2):  # +1 for header, +1 for 1-index
            try:
                if kind in ("motive_vehicles", "maintainx_assets"):
                    masci_id = (row.get("masci_equipment_id") or "").strip()
                    if not masci_id:
                        skipped += 1
                        errors.append(f"Row {i}: missing masci_equipment_id")
                        continue
                    eq = await db.equipment_master.find_one(
                        {"id": masci_id},
                        {"_id": 0, "id": 1, "unit_number": 1, "name": 1, "equipment_type": 1},
                    )
                    if not eq:
                        skipped += 1
                        errors.append(f"Row {i}: equipment {masci_id} not found")
                        continue
                    existing = await db.asset_mappings.find_one({"masci_equipment_id": masci_id})
                    patch: dict = {"updated_at": now_iso()}
                    if kind == "motive_vehicles":
                        patch["motive.vehicle_id"] = (row.get("motive_vehicle_id") or "").strip()
                        patch["motive.asset_id"] = (row.get("motive_asset_id") or "").strip()
                        patch["motive.device_id"] = (row.get("motive_device_id") or "").strip()
                        patch["motive.mapping_status"] = "Mapped" if (
                            patch["motive.vehicle_id"] or patch["motive.asset_id"]
                        ) else "Unmapped"
                    else:
                        patch["maintainx.asset_id"] = (row.get("maintainx_asset_id") or "").strip()
                        patch["maintainx.location_id"] = (row.get("maintainx_location_id") or "").strip()
                        patch["maintainx.mapping_status"] = "Mapped" if patch["maintainx.asset_id"] else "Unmapped"
                    if existing:
                        await db.asset_mappings.update_one({"id": existing["id"]}, {"$set": patch})
                        updated += 1
                    else:
                        import uuid as _uuid  # noqa: PLC0415
                        doc = {
                            "id": str(_uuid.uuid4()),
                            "masci_equipment_id": masci_id,
                            "masci_unit_number": eq.get("unit_number") or "",
                            "masci_equipment_name": eq.get("name") or "",
                            "masci_equipment_type": eq.get("equipment_type") or "",
                            "motive": {"vehicle_id": "", "asset_id": "", "driver_id": "", "device_id": "",
                                       "gps_enabled": False, "dashcam_enabled": False,
                                       "last_sync_at": None, "mapping_status": "Unmapped"},
                            "maintainx": {"asset_id": "", "location_id": "", "pm_schedule_id": "",
                                          "last_sync_at": None, "mapping_status": "Unmapped"},
                            "mapping_confidence": "medium",
                            "mapping_notes": f"Created by CSV import ({kind})",
                            "active": True,
                            "created_at": now_iso(),
                            "updated_at": now_iso(),
                        }
                        # Apply patch BEFORE insert so dotted-paths land correctly
                        for k, v in patch.items():
                            if "." in k:
                                a, b = k.split(".", 1)
                                doc.setdefault(a, {})[b] = v
                            else:
                                doc[k] = v
                        await db.asset_mappings.insert_one(doc)
                        created += 1

                elif kind in ("motive_drivers", "maintainx_users"):
                    masci_id = (row.get("masci_employee_id") or "").strip()
                    if not masci_id:
                        skipped += 1
                        errors.append(f"Row {i}: missing masci_employee_id")
                        continue
                    emp = await db.employees.find_one(
                        {"id": masci_id},
                        {"_id": 0, "id": 1, "name": 1, "email": 1, "trade": 1, "role": 1},
                    )
                    if not emp:
                        skipped += 1
                        errors.append(f"Row {i}: employee {masci_id} not found")
                        continue
                    existing = await db.employee_mappings.find_one({"masci_employee_id": masci_id})
                    patch: dict = {"updated_at": now_iso()}
                    if kind == "motive_drivers":
                        patch["motive.driver_id"] = (row.get("motive_driver_id") or "").strip()
                        patch["motive.driver_name"] = (row.get("motive_driver_name") or "").strip()
                        patch["motive.email"] = (row.get("motive_email") or "").strip()
                        patch["motive.mapping_status"] = "Mapped" if patch["motive.driver_id"] else "Unmapped"
                    else:
                        patch["maintainx.user_id"] = (row.get("maintainx_user_id") or "").strip()
                        patch["maintainx.name"] = (row.get("maintainx_name") or "").strip()
                        patch["maintainx.email"] = (row.get("maintainx_email") or "").strip()
                        patch["maintainx.mapping_status"] = "Mapped" if patch["maintainx.user_id"] else "Unmapped"
                    if existing:
                        await db.employee_mappings.update_one({"id": existing["id"]}, {"$set": patch})
                        updated += 1
                    else:
                        import uuid as _uuid  # noqa: PLC0415
                        doc = {
                            "id": str(_uuid.uuid4()),
                            "masci_employee_id": masci_id,
                            "masci_employee_name": emp.get("name") or "",
                            "masci_employee_trade": emp.get("trade") or "",
                            "masci_employee_role": emp.get("role") or "",
                            "masci_employee_email": emp.get("email") or "",
                            "motive": {"driver_id": "", "driver_name": "", "email": "",
                                       "safety_score": None, "last_sync_at": None,
                                       "mapping_status": "Unmapped"},
                            "maintainx": {"user_id": "", "name": "", "email": "", "role": "",
                                          "last_sync_at": None, "mapping_status": "Unmapped"},
                            "mapping_notes": f"Created by CSV import ({kind})",
                            "active": True,
                            "created_at": now_iso(),
                            "updated_at": now_iso(),
                        }
                        for k, v in patch.items():
                            if "." in k:
                                a, b = k.split(".", 1)
                                doc.setdefault(a, {})[b] = v
                            else:
                                doc[k] = v
                        await db.employee_mappings.insert_one(doc)
                        created += 1
            except Exception as e:  # noqa: BLE001
                failed += 1
                errors.append(f"Row {i}: {e}")

        await write_sync_log(
            db,
            integration="motive" if kind.startswith("motive_") else "maintainx",
            sync_type=f"csv_import:{kind}",
            status="Success" if not failed else "Partial Success",
            records_created=created, records_updated=updated,
            records_skipped=skipped, records_failed=failed,
            notes=("; ".join(errors[:10]))[:500],
        )
        return {
            "ok": True,
            "kind": kind,
            "records_created": created,
            "records_updated": updated,
            "records_skipped": skipped,
            "records_failed": failed,
            "errors": errors[:25],
        }

    # ════════════════════════════════════════════════════════════════
    # EXPORT
    # ════════════════════════════════════════════════════════════════
    @api_router.get(
        "/admin/integrations/export/asset-mappings",
        dependencies=[Depends(require_admin)],
    )
    async def export_asset_mappings(provider: Optional[str] = None):
        q: dict = {}
        if provider == "motive":
            q["motive.vehicle_id"] = {"$ne": ""}
        elif provider == "maintainx":
            q["maintainx.asset_id"] = {"$ne": ""}
        elif provider == "unmapped":
            q = {"$nor": [{"motive.vehicle_id": {"$ne": ""}}, {"maintainx.asset_id": {"$ne": ""}}]}
        docs = await db.asset_mappings.find(q, {"_id": 0}).to_list(10000)
        header = [
            "masci_equipment_id", "masci_unit_number", "masci_equipment_name",
            "motive_vehicle_id", "motive_asset_id", "motive_device_id",
            "maintainx_asset_id", "maintainx_location_id", "maintainx_pm_schedule_id",
            "mapping_confidence", "mapping_notes",
        ]
        rows = [[
            d.get("masci_equipment_id", ""),
            d.get("masci_unit_number", ""),
            d.get("masci_equipment_name", ""),
            (d.get("motive") or {}).get("vehicle_id", ""),
            (d.get("motive") or {}).get("asset_id", ""),
            (d.get("motive") or {}).get("device_id", ""),
            (d.get("maintainx") or {}).get("asset_id", ""),
            (d.get("maintainx") or {}).get("location_id", ""),
            (d.get("maintainx") or {}).get("pm_schedule_id", ""),
            d.get("mapping_confidence", ""),
            d.get("mapping_notes", ""),
        ] for d in docs]
        return _csv_response("masci_asset_mappings.csv", header, rows)

    @api_router.get(
        "/admin/integrations/export/employee-mappings",
        dependencies=[Depends(require_admin)],
    )
    async def export_employee_mappings(provider: Optional[str] = None):
        q: dict = {}
        if provider == "motive":
            q["motive.driver_id"] = {"$ne": ""}
        elif provider == "maintainx":
            q["maintainx.user_id"] = {"$ne": ""}
        elif provider == "unmapped":
            q = {"$nor": [{"motive.driver_id": {"$ne": ""}}, {"maintainx.user_id": {"$ne": ""}}]}
        docs = await db.employee_mappings.find(q, {"_id": 0}).to_list(10000)
        header = [
            "masci_employee_id", "masci_employee_name", "masci_employee_trade",
            "motive_driver_id", "motive_driver_name", "motive_email",
            "maintainx_user_id", "maintainx_name", "maintainx_email", "maintainx_role",
            "mapping_notes",
        ]
        rows = [[
            d.get("masci_employee_id", ""),
            d.get("masci_employee_name", ""),
            d.get("masci_employee_trade", ""),
            (d.get("motive") or {}).get("driver_id", ""),
            (d.get("motive") or {}).get("driver_name", ""),
            (d.get("motive") or {}).get("email", ""),
            (d.get("maintainx") or {}).get("user_id", ""),
            (d.get("maintainx") or {}).get("name", ""),
            (d.get("maintainx") or {}).get("email", ""),
            (d.get("maintainx") or {}).get("role", ""),
            d.get("mapping_notes", ""),
        ] for d in docs]
        return _csv_response("masci_employee_mappings.csv", header, rows)

    @api_router.get(
        "/admin/integrations/export/unmapped-equipment",
        dependencies=[Depends(require_admin)],
    )
    async def export_unmapped_equipment():
        mapped_ids = await db.asset_mappings.distinct("masci_equipment_id")
        cursor = db.equipment_master.find(
            {"id": {"$nin": mapped_ids}, "active": {"$ne": False}}, {"_id": 0},
        )
        docs = await cursor.to_list(10000)
        header = ["id", "unit_number", "name", "equipment_type", "make", "model", "year", "vin", "license_plate"]
        rows = [[
            d.get("id", ""), d.get("unit_number", ""), d.get("name", ""),
            d.get("equipment_type", ""), d.get("make", ""), d.get("model", ""),
            str(d.get("year", "") or ""), d.get("vin", ""), d.get("license_plate", ""),
        ] for d in docs]
        return _csv_response("masci_unmapped_equipment.csv", header, rows)

    @api_router.get(
        "/admin/integrations/export/unmapped-employees",
        dependencies=[Depends(require_admin)],
    )
    async def export_unmapped_employees():
        mapped_ids = await db.employee_mappings.distinct("masci_employee_id")
        cursor = db.employees.find({"id": {"$nin": mapped_ids}}, {"_id": 0})
        docs = await cursor.to_list(10000)
        header = ["id", "name", "trade", "role", "crew", "email", "phone", "employee_id"]
        rows = [[
            d.get("id", ""), d.get("name", ""), d.get("trade", ""), d.get("role", ""),
            d.get("crew", ""), d.get("email", ""), d.get("phone", ""), d.get("employee_id", ""),
        ] for d in docs]
        return _csv_response("masci_unmapped_employees.csv", header, rows)


__all__ = ["register_import_export_routes", "VALID_KINDS"]
