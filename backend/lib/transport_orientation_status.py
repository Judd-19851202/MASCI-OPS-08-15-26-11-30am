"""TRACK 16.08 · Driver orientation status resolver.

Pure async function. No mutations. Reads from
``transport_orientation_assignments`` + ``transport_orientation_modules``
and emits one of ``current | missing | expired | quiz_failed`` for the
given driver. This feeds the eligibility engine's
``ctx['orientation_status']`` value.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

TENANT = "masci"


async def derive_orientation_status(db, transport_person_id: str
                                    ) -> Dict[str, Any]:
    """Return a small dict the eligibility engine can read.

    Shape:
        {
          "orientation_status": "current" | "missing" | "expired" | "quiz_failed",
          "completed_count": int,
          "required_count": int,
          "expiring_soon": bool,
          "latest_completed_at": ISO | None,
          "latest_expires_at": ISO | None,
        }
    """
    if not transport_person_id:
        return {"orientation_status": "missing", "completed_count": 0,
                "required_count": 0, "expiring_soon": False,
                "latest_completed_at": None, "latest_expires_at": None}

    # Required modules (active + required=True).
    modules = await db.transport_orientation_modules.find(
        {"tenant": TENANT, "active": True, "required": True}
    ).to_list(500)
    required_keys = {m["key"] for m in modules}
    required_count = len(required_keys)

    # Latest assignment per required module for this driver.
    assigns = await db.transport_orientation_assignments.find(
        {"tenant": TENANT, "transport_person_id": transport_person_id}
    ).sort("assigned_at", -1).to_list(2000)
    latest_per_module: Dict[str, Dict[str, Any]] = {}
    for a in assigns:
        k = a.get("module_key")
        if k and k not in latest_per_module:
            latest_per_module[k] = a

    now = datetime.now(timezone.utc).isoformat()
    completed = 0
    any_failed = False
    any_expired = False
    latest_completed_at: Optional[str] = None
    latest_expires_at: Optional[str] = None

    for key in required_keys:
        a = latest_per_module.get(key)
        if not a:
            continue
        status = a.get("status")
        expires_at = a.get("expires_at")
        if status == "completed" and expires_at and expires_at < now:
            any_expired = True
            continue
        if status == "completed":
            completed += 1
            ca = a.get("completed_at")
            if ca and (latest_completed_at is None or ca > latest_completed_at):
                latest_completed_at = ca
            if expires_at and (latest_expires_at is None or
                               expires_at > latest_expires_at):
                latest_expires_at = expires_at
        elif status == "quiz_failed":
            any_failed = True

    # Resolve canonical status.
    if required_count == 0:
        status = "missing"
    elif completed == required_count:
        status = "current"
    elif any_expired:
        status = "expired"
    elif any_failed and completed == 0:
        status = "quiz_failed"
    else:
        status = "missing"

    # Expiring soon = any completed assignment expires within 30 days.
    expiring_soon = False
    if latest_expires_at:
        try:
            le = datetime.fromisoformat(latest_expires_at.replace("Z", "+00:00"))
            delta = (le - datetime.now(timezone.utc)).days
            expiring_soon = 0 <= delta <= 30
        except Exception:  # noqa: BLE001
            pass

    return {
        "orientation_status": status,
        "completed_count": completed,
        "required_count": required_count,
        "expiring_soon": expiring_soon,
        "latest_completed_at": latest_completed_at,
        "latest_expires_at": latest_expires_at,
    }
