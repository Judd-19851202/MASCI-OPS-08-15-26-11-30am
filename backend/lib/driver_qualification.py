"""
iter353b · Shared Driver Qualification visibility helper.

Single source of truth for the read-only driver-qualification dashboard
query used by HR, Dispatch, and Field Leadership surfaces. Mirrors the
exact behavior already shipped at
`/api/hr/driver-qualification/dashboard` (defined in
routes/employee_lifecycle.py) so all three portals see identical data,
identical filters, identical summary counts.

NO new collection. NO duplicate source of truth. Pure aggregation over
the existing `employees` collection.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

# Same constants the HR endpoint uses — kept in sync with
# `ALLOWED_DRIVER_STATUSES` and `ALLOWED_CDL_ENDORSEMENTS` declared
# in employee_lifecycle.py. These are the only legal filter values.
ALLOWED_DRIVER_STATUSES = {"active", "suspended", "restricted", "inactive"}
ALLOWED_CDL_ENDORSEMENTS = {"N", "H", "P", "S", "T", "X"}

# Projection shared by every read surface — keeps the wire payload
# small and the contract obviously read-only (no `notes`, no
# `email`, no `phone`, no internal HR-only fields surface).
PROJECTION = {
    "_id": 0,
    "id": 1,
    "name": 1,
    "employee_id": 1,
    "trade": 1,
    "supervisor": 1,
    "lifecycle_status": 1,
    "cdl_holder": 1,
    "approved_company_driver": 1,
    "driver_status": 1,
    "cdl_license_number": 1,
    "cdl_state": 1,
    "cdl_expiration_date": 1,
    "medical_card_expiration_date": 1,
    "cdl_endorsements": 1,
    "cdl_restrictions": 1,
}


def _base_scope() -> Dict[str, Any]:
    """Employees who carry ANY driver-qualification signal at all.

    Mirrors the iter350-hardened base scope used on the HR endpoint —
    explicitly excludes the `None`/`""` sentinel that the HR PATCH
    flow normalizes blank dates to."""
    return {
        "deleted_at": None,
        "$or": [
            {"cdl_holder": True},
            {"approved_company_driver": True},
            {"cdl_expiration_date": {"$nin": [None, ""]}},
            {"medical_card_expiration_date": {"$nin": [None, ""]}},
            {"driver_status": {"$nin": [None, ""]}},
            {"cdl_license_number": {"$nin": [None, ""]}},
        ],
    }


async def fetch_driver_qualification_dashboard(
    db,
    *,
    cdl_holder: Optional[bool] = None,
    approved: Optional[bool] = None,
    driver_status: Optional[str] = None,
    endorsement: Optional[str] = None,
    expiring_cdl_30d: Optional[bool] = None,
    expiring_medical_30d: Optional[bool] = None,
    q: Optional[str] = None,
    limit: int = 500,
) -> Dict[str, Any]:
    """Return the {items, count, summary, as_of} dashboard payload.

    Identical to the HR endpoint output — Dispatch and FL portals
    consume the SAME shape so the frontend can render with one
    component. Raises `ValueError` on invalid filter values (callers
    translate to HTTP 400).
    """
    today = date.today()
    today_iso = today.isoformat()
    cutoff_30d = (today + timedelta(days=30)).isoformat()

    base = _base_scope()
    clauses: List[Dict[str, Any]] = [base]
    if cdl_holder is not None:
        clauses.append({"cdl_holder": cdl_holder})
    if approved is not None:
        clauses.append({"approved_company_driver": approved})
    if driver_status:
        if driver_status not in ALLOWED_DRIVER_STATUSES:
            raise ValueError(
                f"driver_status must be one of {sorted(ALLOWED_DRIVER_STATUSES)}"
            )
        clauses.append({"driver_status": driver_status})
    if endorsement:
        if endorsement not in ALLOWED_CDL_ENDORSEMENTS:
            raise ValueError(
                f"endorsement must be one of {sorted(ALLOWED_CDL_ENDORSEMENTS)}"
            )
        clauses.append({"cdl_endorsements": endorsement})
    if expiring_cdl_30d:
        clauses.append({
            "cdl_expiration_date": {"$gte": today_iso, "$lte": cutoff_30d}
        })
    if expiring_medical_30d:
        clauses.append({
            "medical_card_expiration_date": {"$gte": today_iso, "$lte": cutoff_30d}
        })
    if q:
        clauses.append({"$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"employee_id": {"$regex": q, "$options": "i"}},
            {"cdl_license_number": {"$regex": q, "$options": "i"}},
        ]})

    final = {"$and": clauses}
    safe_limit = max(1, min(int(limit or 500), 2000))
    cur = db.employees.find(final, PROJECTION).sort("name", 1).limit(safe_limit)
    items: List[Dict[str, Any]] = [d async for d in cur]

    async def _count(extra: Dict[str, Any]) -> int:
        return await db.employees.count_documents({"$and": [base, extra]})

    summary = {
        "cdl_expiring_30d": await _count({
            "cdl_expiration_date": {"$gte": today_iso, "$lte": cutoff_30d}
        }),
        "medical_card_expiring_30d": await _count({
            "medical_card_expiration_date": {"$gte": today_iso, "$lte": cutoff_30d}
        }),
        "restricted": await _count({"driver_status": "restricted"}),
        "suspended": await _count({"driver_status": "suspended"}),
        "tanker_capable": await _count({
            "cdl_endorsements": {"$in": ["N", "X"]}
        }),
    }

    return {
        "items": items,
        "count": len(items),
        "summary": summary,
        "as_of": today_iso,
    }
