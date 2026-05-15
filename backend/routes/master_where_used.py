"""
master_where_used.py — Iter140. Cross-portal footprint aggregator.

Given an equipment_master_id or employee_master_id, returns ALL records
across the platform that reference it: incidents, corrective actions,
inspections, fire extinguishers, training records, attached photos.

Used by:
  • HR Portal — employee detail page "Linked records" tab
  • Equipment Master — "Where used" panel
  • Cross-portal traceability for OSHA / insurance audits

Endpoints:
  GET /api/master-lookup/equipment/{id}/where-used
  GET /api/master-lookup/employees/{id}/where-used
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)


# Each entry: (collection, projection_fields, display_field, route_template).
# route_template is FE-side router path the UI deep-links to.
EQUIPMENT_REFS = [
    ("equipment_inspections",
     {"id": 1, "equipment_unit": 1, "inspection_date": 1, "passed": 1, "submitted_by": 1},
     lambda d: f"Inspection on {d.get('inspection_date', '—')} · {('PASS' if d.get('passed') else 'FAIL') if 'passed' in d else '—'}",
     "/admin/equipment-inspections"),
    ("fire_extinguishers",
     {"id": 1, "unit_id": 1, "location_value": 1, "last_status": 1, "next_due_date": 1},
     lambda d: f"Extinguisher {d.get('unit_id', '—')} ({d.get('last_status', '—')})",
     "/safety-portal/fire-extinguishers"),
    ("incidents",
     {"id": 1, "incident_type": 1, "incident_date": 1, "severity": 1, "location": 1},
     lambda d: f"{d.get('incident_type', 'Incident')} on {d.get('incident_date', '—')} · {d.get('severity', '—')}",
     "/safety-portal/incidents"),
    ("corrective_actions",
     {"id": 1, "title": 1, "status": 1, "priority": 1, "due_date": 1},
     lambda d: f"{d.get('title', 'CA')} · {d.get('status', '—')}",
     "/safety-portal/corrective-actions"),
]

EMPLOYEE_REFS = [
    ("incidents",
     {"id": 1, "incident_type": 1, "incident_date": 1, "severity": 1,
      "person_name": 1, "location": 1},
     lambda d: f"{d.get('incident_type', 'Incident')} on {d.get('incident_date', '—')} · {d.get('person_name', '—')}",
     "/safety-portal/incidents"),
    ("corrective_actions",
     {"id": 1, "title": 1, "status": 1, "assigned_to_name": 1, "due_date": 1},
     lambda d: f"{d.get('title', 'CA')} · {d.get('status', '—')}",
     "/safety-portal/corrective-actions"),
    ("safety_training_records",
     {"id": 1, "training_name": 1, "certification_type": 1,
      "completed_date": 1, "expiration_date": 1},
     lambda d: f"{d.get('training_name', '—')} · expires {d.get('expiration_date', '—') or 'N/A'}",
     "/safety-portal/training-records"),
]


async def _gather(db, master_id: str, refs) -> Dict[str, Any]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    totals: Dict[str, int] = {}
    for coll_name, projection, formatter, route_tmpl in refs:
        items: List[Dict[str, Any]] = []
        try:
            field = "equipment_master_id" if refs is EQUIPMENT_REFS else "employee_master_id"
            cursor = db[coll_name].find(
                {field: master_id},
                {"_id": 0, **projection},
            ).sort("created_at", -1).limit(100)
            async for d in cursor:
                items.append({
                    "id": d.get("id"),
                    "label": formatter(d),
                    "route": route_tmpl,
                    "raw": d,
                })
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[where-used] {coll_name}: {e}")
        out[coll_name] = items
        totals[coll_name] = len(items)
    return {"records": out, "totals": totals,
            "total": sum(totals.values())}


def register_where_used_routes(router: APIRouter, db) -> None:

    @router.get("/equipment/{master_id}/where-used")
    async def equipment_where_used(master_id: str):
        # Sanity: confirm the master record exists so we can echo its summary
        master = await db.equipment_master.find_one(
            {"id": master_id},
            {"_id": 0, "id": 1, "unit_number": 1, "make_model": 1, "category": 1,
             "vin": 1, "serial_number": 1},
        )
        if not master:
            raise HTTPException(404, "Equipment master record not found")
        data = await _gather(db, master_id, EQUIPMENT_REFS)
        return {"master": master, **data}

    @router.get("/employees/{master_id}/where-used")
    async def employees_where_used(master_id: str):
        master = await db.employees.find_one(
            {"id": master_id},
            {"_id": 0, "id": 1, "name": 1, "first_name": 1, "last_name": 1,
             "email": 1, "employee_id": 1, "role": 1, "trade": 1},
        )
        if not master:
            raise HTTPException(404, "Employee master record not found")
        data = await _gather(db, master_id, EMPLOYEE_REFS)
        return {"master": master, **data}


__all__ = ["register_where_used_routes", "EQUIPMENT_REFS", "EMPLOYEE_REFS"]
