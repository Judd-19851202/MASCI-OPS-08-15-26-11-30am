"""
master_lookup.py — Iter137. Single-source-of-truth lookup helpers.

Cross-portal records (incidents, corrective actions, inspections, fire
extinguishers) often store equipment + employee references as free-text
("T-101", "Mike Johnson") instead of the master collection's `id` UUID.
This makes joins fuzzy and prevents rename propagation.

This module exposes typeahead lookups so the FE can resolve free-text
to a master id at the moment of record creation. Existing records can
be backfilled via `POST /api/master-lookup/backfill/equipment` (admin).

Endpoints (mounted under /api):
  GET  /master-lookup/equipment?q=…   — typeahead, returns top 20 matches
  GET  /master-lookup/employees?q=…   — typeahead, returns top 20 matches
  POST /master-lookup/backfill/equipment  — admin: try to attach
       equipment_master_id to records that have only free-text refs
  POST /master-lookup/backfill/employees  — admin: same for employees
"""
from __future__ import annotations

import logging
import re
from typing import Any, Callable, Dict, List

from fastapi import APIRouter, Depends, Query

logger = logging.getLogger(__name__)


def _safe_regex(q: str) -> Dict[str, Any]:
    """Case-insensitive partial match, regex-escaped."""
    return {"$regex": re.escape(q.strip()), "$options": "i"}


def build_master_lookup_router(db, require_admin: Callable) -> APIRouter:
    router = APIRouter(prefix="/api/master-lookup", tags=["master-lookup"])

    # ── Equipment typeahead ──────────────────────────────────────
    @router.get("/equipment")
    async def lookup_equipment(
        q: str = Query("", description="Partial match against unit_number / make_model / VIN / serial"),
        limit: int = Query(20, ge=1, le=100),
    ):
        if not q.strip():
            return {"q": q, "items": []}
        regex = _safe_regex(q)
        cursor = db.equipment_master.find(
            {
                "$and": [
                    {"$or": [{"deleted_at": {"$exists": False}}, {"deleted_at": None}]},
                    {"$or": [
                        {"unit_number": regex},
                        {"make_model": regex},
                        {"vin": regex},
                        {"serial_number": regex},
                    ]},
                ]
            },
            {"_id": 0, "id": 1, "unit_number": 1, "make_model": 1,
             "category": 1, "vin": 1, "serial_number": 1},
        ).limit(limit)
        items = [doc async for doc in cursor]
        return {"q": q, "items": items, "count": len(items)}

    # iter139 — lookup-by-id, used by the FE typeahead on re-open to
    # populate the freetext display when only the master id is stored.
    @router.get("/equipment/by-id/{master_id}")
    async def lookup_equipment_by_id(master_id: str):
        doc = await db.equipment_master.find_one(
            {"id": master_id},
            {"_id": 0, "id": 1, "unit_number": 1, "make_model": 1,
             "category": 1, "vin": 1, "serial_number": 1},
        )
        if not doc:
            return {"id": master_id, "found": False, "item": None}
        return {"id": master_id, "found": True, "item": doc}

    # ── Employee typeahead ───────────────────────────────────────
    @router.get("/employees")
    async def lookup_employees(
        q: str = Query("", description="Partial match against name / email / employee_id"),
        limit: int = Query(20, ge=1, le=100),
    ):
        if not q.strip():
            return {"q": q, "items": []}
        regex = _safe_regex(q)
        cursor = db.employees.find(
            {
                "$and": [
                    {"$or": [{"deleted_at": {"$exists": False}}, {"deleted_at": None}]},
                    {"$or": [
                        {"name": regex},          # schema A: single 'name' field
                        {"first_name": regex},    # schema B: first/last split
                        {"last_name": regex},
                        {"email": regex},
                        {"employee_id": regex},
                        {"display_name": regex},
                    ]},
                ]
            },
            {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "name": 1,
             "email": 1, "employee_id": 1, "role": 1, "display_name": 1, "trade": 1},
        ).limit(limit)
        items = [doc async for doc in cursor]
        return {"q": q, "items": items, "count": len(items)}

    # iter139 — employee lookup-by-id helper for typeahead re-open
    @router.get("/employees/by-id/{master_id}")
    async def lookup_employee_by_id(master_id: str):
        doc = await db.employees.find_one(
            {"id": master_id},
            {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "name": 1,
             "email": 1, "employee_id": 1, "role": 1, "display_name": 1, "trade": 1},
        )
        if not doc:
            return {"id": master_id, "found": False, "item": None}
        return {"id": master_id, "found": True, "item": doc}

    # ── Backfill: equipment ──────────────────────────────────────
    @router.post("/backfill/equipment", dependencies=[Depends(require_admin)])
    async def backfill_equipment(dry_run: bool = Query(default=True)):
        """For each cross-portal record that has freetext equipment
        ('equipment_unit', 'unit_number', 'truck') but no
        'equipment_master_id', try to resolve against equipment_master
        by unit_number and attach the id. Returns a per-collection
        summary. Dry-run by default."""
        # Build a lookup map: unit_number(upper) → master id
        master_by_unit: Dict[str, str] = {}
        async for d in db.equipment_master.find(
            {"$or": [{"deleted_at": {"$exists": False}}, {"deleted_at": None}]},
            {"_id": 0, "id": 1, "unit_number": 1},
        ):
            un = (d.get("unit_number") or "").strip().upper()
            if un:
                master_by_unit[un] = d["id"]

        report: Dict[str, Dict[str, Any]] = {}
        targets = [
            ("equipment_inspections", ["equipment_unit", "unit_number"]),
            ("fire_extinguishers",    ["truck", "unit_number"]),
            ("incidents",             ["equipment_unit"]),
            ("corrective_actions",    ["equipment_unit"]),
        ]
        for coll_name, fields in targets:
            total = await db[coll_name].count_documents({})
            attached = 0
            unresolved = 0
            async for r in db[coll_name].find(
                {"$and": [
                    {"$or": [{"equipment_master_id": {"$exists": False}}, {"equipment_master_id": ""}]},
                    {"$or": [{f: {"$exists": True, "$ne": ""}} for f in fields]},
                ]},
                {"_id": 0, "id": 1, **{f: 1 for f in fields}},
            ):
                raw = next((r.get(f) for f in fields if r.get(f)), "")
                key = str(raw).strip().upper()
                master_id = master_by_unit.get(key)
                if master_id:
                    if not dry_run:
                        await db[coll_name].update_one(
                            {"id": r["id"]},
                            {"$set": {"equipment_master_id": master_id}},
                        )
                    attached += 1
                else:
                    unresolved += 1
            report[coll_name] = {
                "total": total,
                "attached": attached,
                "unresolved": unresolved,
            }
        return {"dry_run": dry_run, "report": report,
                "master_units_indexed": len(master_by_unit)}

    # ── Backfill: employees ──────────────────────────────────────
    @router.post("/backfill/employees", dependencies=[Depends(require_admin)])
    async def backfill_employees(dry_run: bool = Query(default=True)):
        """Same shape as the equipment backfill but for employees,
        matching by email (canonical) then by 'employee_name' freetext
        against first+last."""
        emp_by_email: Dict[str, str] = {}
        emp_by_eid: Dict[str, str] = {}
        emp_by_full_name: Dict[str, str] = {}
        async for d in db.employees.find(
            {"$or": [{"deleted_at": {"$exists": False}}, {"deleted_at": None}]},
            {"_id": 0, "id": 1, "email": 1, "employee_id": 1,
             "first_name": 1, "last_name": 1, "name": 1},
        ):
            em = (d.get("email") or "").strip().lower()
            if em:
                emp_by_email[em] = d["id"]
            eid = (d.get("employee_id") or "").strip()
            if eid:
                emp_by_eid[eid] = d["id"]
            # Support both schemas: single 'name' OR first/last
            name_combo = d.get("name") or f"{d.get('first_name','').strip()} {d.get('last_name','').strip()}".strip()
            full = name_combo.strip().lower()
            if full:
                emp_by_full_name[full] = d["id"]

        report: Dict[str, Dict[str, Any]] = {}
        targets = ["incidents", "corrective_actions", "safety_training_records"]
        for coll_name in targets:
            total = await db[coll_name].count_documents({})
            attached = 0
            unresolved = 0
            async for r in db[coll_name].find(
                {"$and": [
                    {"$or": [{"employee_master_id": {"$exists": False}}, {"employee_master_id": ""}]},
                    {"$or": [
                        {"employee_email": {"$exists": True, "$ne": ""}},
                        {"employee_id": {"$exists": True, "$ne": ""}},
                        {"employee_name": {"$exists": True, "$ne": ""}},
                    ]},
                ]},
                {"_id": 0, "id": 1, "employee_email": 1, "employee_id": 1, "employee_name": 1},
            ):
                resolved = None
                em = (r.get("employee_email") or "").strip().lower()
                if em and em in emp_by_email:
                    resolved = emp_by_email[em]
                if not resolved:
                    eid = (r.get("employee_id") or "").strip()
                    if eid in emp_by_eid:
                        resolved = emp_by_eid[eid]
                if not resolved:
                    nm = (r.get("employee_name") or "").strip().lower()
                    if nm in emp_by_full_name:
                        resolved = emp_by_full_name[nm]
                if resolved:
                    if not dry_run:
                        await db[coll_name].update_one(
                            {"id": r["id"]},
                            {"$set": {"employee_master_id": resolved}},
                        )
                    attached += 1
                else:
                    unresolved += 1
            report[coll_name] = {
                "total": total,
                "attached": attached,
                "unresolved": unresolved,
            }
        return {"dry_run": dry_run, "report": report,
                "employees_indexed": len(emp_by_email) + len(emp_by_eid) + len(emp_by_full_name)}

    # ── Audit summary: report current SOT coverage ───────────────
    @router.get("/audit", dependencies=[Depends(require_admin)])
    async def sot_audit():
        eq_master_total = await db.equipment_master.count_documents({})
        emp_total = await db.employees.count_documents({})

        coverage: Dict[str, Dict[str, Any]] = {}
        eq_targets = ["equipment_inspections", "fire_extinguishers", "incidents", "corrective_actions"]
        for coll_name in eq_targets:
            total = await db[coll_name].count_documents({})
            referenced = await db[coll_name].count_documents({"equipment_master_id": {"$exists": True, "$ne": ""}})
            coverage[coll_name] = {
                "total": total,
                "with_master_ref": referenced,
                "pct": int(100 * referenced / total) if total else 100,
            }
        emp_targets = ["incidents", "corrective_actions", "safety_training_records"]
        emp_coverage: Dict[str, Dict[str, Any]] = {}
        for coll_name in emp_targets:
            total = await db[coll_name].count_documents({})
            referenced = await db[coll_name].count_documents({"employee_master_id": {"$exists": True, "$ne": ""}})
            emp_coverage[coll_name] = {
                "total": total,
                "with_master_ref": referenced,
                "pct": int(100 * referenced / total) if total else 100,
            }
        return {
            "equipment_master_total": eq_master_total,
            "employees_total": emp_total,
            "equipment_coverage": coverage,
            "employee_coverage": emp_coverage,
        }

    return router


__all__ = ["build_master_lookup_router"]
