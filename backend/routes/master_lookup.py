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
from typing import Any, Callable, Dict, List, Tuple

from fastapi import APIRouter, Depends, Query

logger = logging.getLogger(__name__)

EQUIPMENT_BINDING_TARGETS: List[Tuple[str, List[str]]] = [
    ("equipment_inspections", ["equipment_unit", "unit_number"]),
    ("fire_extinguishers", ["truck", "unit_number"]),
    ("incidents", ["equipment_unit"]),
    ("corrective_actions", ["equipment_unit"]),
]

EMPLOYEE_BINDING_TARGETS: List[Tuple[str, List[str]]] = [
    ("incidents", ["employee_email", "employee_id", "employee_name"]),
    ("corrective_actions", ["employee_email", "employee_id", "employee_name"]),
    ("safety_training_records", ["employee_email", "employee_id", "employee_name"]),
]

MASTER_BINDING_SAMPLE_THRESHOLD = 10


def _safe_regex(q: str) -> Dict[str, Any]:
    """Case-insensitive partial match, regex-escaped."""
    return {"$regex": re.escape(q.strip()), "$options": "i"}


async def _binding_coverage_for_targets(
    db,
    *,
    targets: List[Tuple[str, List[str]]],
    canonical_field: str,
    backfill_endpoint: str,
    entity_label: str,
    review_queue_endpoint: str | None = None,
) -> Dict[str, Dict[str, Any]]:
    coverage: Dict[str, Dict[str, Any]] = {}
    for coll_name, source_fields in targets:
        eligible_filter = {
            "$or": [{canonical_field: {"$exists": True, "$ne": ""}}] + [
                {field: {"$exists": True, "$ne": ""}} for field in source_fields
            ]
        }
        eligible_total = await db[coll_name].count_documents(eligible_filter)
        referenced = await db[coll_name].count_documents({canonical_field: {"$exists": True, "$ne": ""}})
        missing = max(0, eligible_total - referenced)
        coverage[coll_name] = {
            "eligible_total": eligible_total,
            "with_master_ref": referenced,
            "missing_master_ref": missing,
            "pct": int(100 * referenced / eligible_total) if eligible_total else 100,
            "canonical_field": canonical_field,
            "source_fields": source_fields,
            "entity_label": entity_label,
            "minimum_sample_threshold": MASTER_BINDING_SAMPLE_THRESHOLD,
            "small_sample": eligible_total < MASTER_BINDING_SAMPLE_THRESHOLD,
            "denominator_definition": (
                f"records with {canonical_field} already present OR at least one source field populated"
            ),
            "backfill_endpoint": backfill_endpoint,
            "review_queue_endpoint": review_queue_endpoint,
            "ambiguous_match_policy": "ambiguous candidates must be routed to a review queue; deterministic matches may be backfilled",
        }
    return coverage


async def build_master_binding_audit(db) -> Dict[str, Any]:
    eq_master_total = await db.equipment_master.count_documents({})
    emp_total = await db.employees.count_documents({})
    equipment_coverage = await _binding_coverage_for_targets(
        db,
        targets=EQUIPMENT_BINDING_TARGETS,
        canonical_field="equipment_master_id",
        backfill_endpoint="/api/master-lookup/backfill/equipment",
        entity_label="equipment",
        review_queue_endpoint=None,
    )
    employee_coverage = await _binding_coverage_for_targets(
        db,
        targets=EMPLOYEE_BINDING_TARGETS,
        canonical_field="employee_master_id",
        backfill_endpoint="/api/master-lookup/backfill/employees",
        entity_label="employee",
        review_queue_endpoint="/api/admin/compliance/employee-link-review-queue",
    )
    return {
        "equipment_master_total": eq_master_total,
        "employees_total": emp_total,
        "equipment_coverage": equipment_coverage,
        "employee_coverage": employee_coverage,
        "sample_threshold": MASTER_BINDING_SAMPLE_THRESHOLD,
    }


def build_master_lookup_router(
    db,
    require_admin: Callable,
    require_any_portal_read: Callable | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/master-lookup", tags=["master-lookup"])
    # TRACK 24.9 Phase B · Employee typeahead auth gate.
    # `/master-lookup/employees` returns HR fields including `email`.
    # Before Track 24.9 this endpoint had no auth guard, so anyone
    # on the internet could enumerate the roster + emails by
    # querying `q=@` — a Track 24.1-class PII leak. All in-tree
    # callers (NewIncident, SafetyTrainingRecords,
    # SafetyCorrectiveActions) are authenticated safety portal
    # pages, so adding the guard does not break any legitimate
    # flow. `by-id` shares the same guard.
    portal_dep = (
        [Depends(require_any_portal_read)] if require_any_portal_read else []
    )
    # iter140 — where-used aggregator (cross-portal footprint)
    from routes.master_where_used import register_where_used_routes  # noqa: PLC0415
    register_where_used_routes(router, db)

    # iter141 — chronological history timeline + CSV/PDF export
    from routes.master_history import register_history_routes  # noqa: PLC0415
    register_history_routes(router, db)

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
    @router.get("/employees", dependencies=portal_dep)
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
    @router.get("/employees/by-id/{master_id}", dependencies=portal_dep)
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
        for coll_name, fields in EQUIPMENT_BINDING_TARGETS:
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
        for coll_name, _fields in EMPLOYEE_BINDING_TARGETS:
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
        audit = await build_master_binding_audit(db)
        audit["kpi_metadata"] = {
            "kpi_name": "Cross-portal Master Binding Coverage",
            "business_definition": "Eligible-record coverage for canonical employee/equipment master bindings across operational collections.",
            "source_of_truth": "master lookup audit helper",
            "api_endpoint": "/api/master-lookup/audit",
            "formula": {
                "denominator": "eligible records with canonical binding present or at least one source field populated",
                "sample_threshold": MASTER_BINDING_SAMPLE_THRESHOLD,
            },
            "confidence": "HIGH",
            "status_reason": "Ambiguous matches must be routed to review queues; deterministic matches may be backfilled.",
            "drilldown_source": "/api/master-lookup/audit",
            "owner": "master-data-integrity",
        }
        return audit

    return router


__all__ = [
    "build_master_lookup_router",
    "build_master_binding_audit",
    "EQUIPMENT_BINDING_TARGETS",
    "EMPLOYEE_BINDING_TARGETS",
    "MASTER_BINDING_SAMPLE_THRESHOLD",
]
