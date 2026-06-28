"""TRACK 16.09 · Transportation Dispatch Gate.

Pure async helper. Validates dispatch eligibility for a driver / truck /
carrier triple AGAINST the canonical ``transport_eligibility_state``
collection plus a live status check for orientation, packet, inspection,
and safety hold.

* Returns a structured ``{ok, blocked, state, reason_codes, message,
  override_available, override_required, ...}`` envelope.
* NEVER mutates state.
* Honours an optional ``override_id`` that, when valid + active + not
  expired, short-circuits the block — but the underlying eligibility
  row is left untouched (compliance requirement remains).
* Safe for legacy / free-text dispatch — when a target ID has no
  corresponding ``transport_persons`` / ``transport_trucks`` /
  ``carriers`` row we DO NOT block (governance-not-applicable).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

TENANT = "masci"

# Map raw reason codes to operator-facing, non-punitive language.
# Forbidden vocabulary: rejected / denied / failed.
HUMAN_REASONS: Dict[str, str] = {
    # Person
    "orientation_missing": "Orientation incomplete",
    "orientation_expired": "Orientation expired",
    "orientation_quiz_failed": "Orientation quiz needs another attempt",
    "person_status_inactive": "Driver status is inactive",
    "person_status_suspended": "Driver is suspended",
    "person_safety_hold": "Driver safety hold",
    "packet_not_approved": "Carrier packet not approved",
    "rate_not_acknowledged": "Rate schedule not acknowledged",
    "missing_required_docs": "Required documents missing",
    "expired_required_docs": "Required documents expired",
    "docs_needs_correction": "Documents need correction",
    "ppe_issue": "PPE requirement open",
    "hr_lifecycle_terminated": "HR lifecycle marks driver terminated",
    # TRACK 16.11 · HR-lifecycle reason codes surfaced via the
    # eligibility projection. Human-readable, dispatcher-facing.
    "hr_lifecycle_inactive":  "HR employment is not active",
    "hr_status_active":       "HR employment is active",
    "hr_status_terminated":   "Employee is terminated in HR",
    "hr_status_inactive":     "Employee is inactive in HR",
    "hr_status_resigned":     "Employee has resigned in HR",
    "hr_status_retired":      "Employee has retired in HR",
    "hr_status_suspended":    "Employee is suspended in HR",
    "hr_status_on_leave":     "Employee is on leave in HR",
    "hr_status_pending_hire": "Employee is pending hire in HR",
    "hr_status_seasonal":     "Employee is seasonal (active) in HR",
    "hr_status_unknown":      "HR lifecycle status unknown — review required",
    "hr_employee_missing":    "Linked HR employee record not found",
    "hr_linkage_missing":     "Transport driver has no HR employee linkage",
    "hr_role_not_driver":     "Employee role requires Transportation review",
    "hr_sync_stale":          "HR lifecycle sync stale — review required",
    # Truck
    "truck_status_inactive": "Truck status is inactive",
    "truck_status_suspended": "Truck is suspended",
    "truck_safety_hold": "Truck safety hold",
    "inspection_missing": "Truck readiness inspection missing",
    "inspection_expired": "Truck readiness inspection expired",
    "inspection_needs_correction": "Truck readiness inspection needs correction",
    # Carrier
    "carrier_status_inactive": "Carrier status is inactive",
    "carrier_status_suspended": "Carrier is suspended",
    "carrier_packet_not_approved": "Carrier packet not approved",
}

# States that BLOCK assignment.
BLOCKING_STATES = {"not_dispatchable", "suspended", "pending_review",
                    "needs_correction"}


def _human(codes: List[str]) -> List[str]:
    """Map raw reason codes to operator-facing labels."""
    return [HUMAN_REASONS.get(c, c.replace("_", " ").capitalize()) for c in codes]


async def _load_eligibility(db, *, target_type: str, target_id: Optional[str]
                            ) -> Optional[Dict[str, Any]]:
    if not target_id:
        return None
    return await db.transport_eligibility_state.find_one(
        {"tenant": TENANT, "target_type": target_type, "target_id": target_id})


async def _entity_exists(db, *, collection: str, identifier: str) -> bool:
    """True iff a transportation-governed entity row exists for this id."""
    if not identifier:
        return False
    row = await db[collection].find_one(
        {"tenant": TENANT, "id": identifier}, {"_id": 1})
    return row is not None


async def _active_override(db, *, override_id: str, driver_id: Optional[str],
                           truck_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the override row IFF it is active, unexpired, and scoped to
    the driver/truck under consideration. Otherwise ``None``."""
    if not override_id:
        return None
    row = await db.transport_dispatch_overrides.find_one(
        {"id": override_id, "tenant": TENANT})
    if not row:
        return None
    if row.get("status") != "approved":
        return None
    expires = row.get("expires_at")
    if expires and expires < datetime.now(timezone.utc).isoformat():
        return None
    # Must cover the driver and/or truck being assigned.
    covers = False
    if driver_id and row.get("driver_id") == driver_id:
        covers = True
    if truck_id and row.get("truck_id") == truck_id:
        covers = True
    # If override row scopes ONLY by carrier (no driver / truck specified)
    # we treat it as broad — but still capped by expiry.
    if not row.get("driver_id") and not row.get("truck_id"):
        covers = True
    return row if covers else None


async def evaluate_dispatch_gate(
    db,
    *,
    driver_id: Optional[str] = None,
    truck_id: Optional[str] = None,
    carrier_id: Optional[str] = None,
    override_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a structured gate envelope. Pure read; never mutates."""
    reason_codes: List[str] = []
    parts: List[Dict[str, Any]] = []
    state_per_target: Dict[str, str] = {}

    async def _check(kind: str, coll: str, ident: Optional[str]) -> None:
        if not ident:
            return
        # Governance applies only to transportation-managed entities.
        if not await _entity_exists(db, collection=coll, identifier=ident):
            return
        row = await _load_eligibility(db, target_type=kind, target_id=ident)
        state = (row or {}).get("state") or "pending_review"
        state_per_target[kind] = state
        codes = [r["code"] for r in (row or {}).get("reasons") or []]
        if state in BLOCKING_STATES:
            for c in codes:
                if c not in reason_codes:
                    reason_codes.append(c)
        parts.append({"target_type": kind, "target_id": ident,
                      "state": state, "reasons": codes})

    await _check("person", "transport_persons", driver_id)
    await _check("truck", "transport_trucks", truck_id)
    await _check("carrier", "carriers", carrier_id)

    blocking = any(s in BLOCKING_STATES for s in state_per_target.values())

    # Resolve override.
    override_row = await _active_override(
        db, override_id=override_id or "", driver_id=driver_id,
        truck_id=truck_id) if override_id else None
    if blocking and override_row:
        return {
            "ok": True,
            "blocked": False,
            "state": "override_approved",
            "reason_codes": reason_codes,
            "reason_labels": _human(reason_codes),
            "message": ("Override approved. Assignment permitted under audit. "
                        "Compliance requirement remains open."),
            "override_available": True,
            "override_required": True,
            "override_id": override_row["id"],
            "override_expires_at": override_row.get("expires_at"),
            "targets": parts,
        }

    if blocking:
        msg_role = []
        if "person" in state_per_target and state_per_target["person"] in BLOCKING_STATES:
            msg_role.append("Driver")
        if "truck" in state_per_target and state_per_target["truck"] in BLOCKING_STATES:
            msg_role.append("Truck")
        if "carrier" in state_per_target and state_per_target["carrier"] in BLOCKING_STATES:
            msg_role.append("Carrier")
        prefix = " / ".join(msg_role) or "Entity"
        return {
            "ok": False,
            "blocked": True,
            "state": "not_dispatchable",
            "reason_codes": reason_codes,
            "reason_labels": _human(reason_codes),
            "message": (f"{prefix} is not dispatchable until Transportation "
                        f"requirements are current."),
            "override_available": True,
            "override_required": True,
            "targets": parts,
        }

    # Not blocked.
    state = "eligible"
    if any(s == "pending_review" for s in state_per_target.values()):
        state = "pending_review"
    return {
        "ok": True,
        "blocked": False,
        "state": state,
        "reason_codes": [],
        "reason_labels": [],
        "message": "Eligible for dispatch.",
        "override_available": False,
        "override_required": False,
        "targets": parts,
    }
