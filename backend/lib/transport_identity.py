"""TRACK 16.04 · Transportation identity resolver (Phase 1).

Prevents duplicate driver projections; reuses existing MASCI HR
employee identity instead of duplicating it.
"""
from __future__ import annotations
from typing import Any, Dict, Optional


async def find_existing_employee_projection(
    db, *, tenant: str, employee_id: str,
) -> Optional[Dict[str, Any]]:
    """Return an existing active transport_person row for the given
    employee_id under this tenant, or None."""
    return await db.transport_persons.find_one({
        "tenant": tenant,
        "kind": "masci_employee",
        "employee_id": employee_id,
        "status": {"$ne": "inactive"},
    })


async def find_existing_leased_driver(
    db, *, tenant: str, carrier_id: str, license_number: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Return an existing active leased driver under the same carrier
    with the same license_number; None when license is unset."""
    if not license_number:
        return None
    return await db.transport_persons.find_one({
        "tenant": tenant,
        "kind": "leased_driver",
        "carrier_id": carrier_id,
        "license_number": license_number,
        "status": {"$ne": "inactive"},
    })


def display_name(person: Dict[str, Any]) -> str:
    fn = (person or {}).get("first_name") or ""
    ln = (person or {}).get("last_name") or ""
    return (fn + " " + ln).strip() or (person or {}).get("email") or "Unknown driver"
