"""TRACK 16.11 · Transportation HR Lifecycle Integration.

Read-only projection of MASCI HR lifecycle facts into Transportation
eligibility for MASCI employee drivers.

HARD CONTRACT
-------------
* HR (`db.employees`) is the SOLE source of truth. Nothing in this
  module mutates an employee record.
* No employee duplication. We only update the *existing* matching
  ``transport_persons`` row (kind=``masci_employee``) that operators
  explicitly linked to the employee.
* The mapper is pure — no DB. The sync helper performs ONE upsert
  to the existing transport_person doc plus one audit row + one
  optional action-item row. It never blocks the calling HR write.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

TENANT = "masci"


# ---------------------------------------------------------------------------
# Canonical Transportation projection states.
# These are NOT eligibility states — eligibility derives from these +
# document / orientation / inspection signals downstream.
# ---------------------------------------------------------------------------
TRANSPORT_PROJECTION_STATES = (
    "eligible",          # HR is active and driver-relevant
    "pending_review",    # HR status unknown / needs human eyes
    "suspended",         # HR suspended / on leave
    "not_dispatchable",  # HR terminated / inactive / resigned / retired
    "needs_correction",  # HR linkage broken or role changed away
)

# Human-readable labels for HR-derived reason codes. Forbidden
# vocabulary (rejected/denied/failed) is intentionally absent.
HR_REASON_LABELS: Dict[str, str] = {
    "hr_status_active":           "HR employment is active",
    "hr_status_terminated":       "Employee is terminated in HR",
    "hr_status_inactive":         "Employee is inactive in HR",
    "hr_status_resigned":         "Employee has resigned in HR",
    "hr_status_retired":          "Employee has retired in HR",
    "hr_status_suspended":        "Employee is suspended in HR",
    "hr_status_on_leave":         "Employee is on leave in HR",
    "hr_status_pending_hire":     "Employee is pending hire in HR",
    "hr_status_seasonal":         "Employee is seasonal (active) in HR",
    "hr_status_unknown":          "HR lifecycle status unknown — review required",
    "hr_employee_missing":        "Linked HR employee record not found",
    "hr_linkage_missing":         "Transport driver has no HR employee linkage",
    "hr_role_not_driver":         "Employee role requires Transportation review",
    "hr_sync_stale":              "HR lifecycle sync stale — review required",
    "hr_sync_failed":             "HR lifecycle sync needs attention",
}

# HR statuses that map directly to transport states. Source of truth is
# `routes/employee_lifecycle.py`'s `ALLOWED_LIFECYCLE_STATUSES`. We map
# rather than redefine.
_HR_STATUS_MAP: Dict[str, Tuple[str, str]] = {
    "Active":            ("eligible",         "hr_status_active"),
    "Pending Hire":      ("pending_review",   "hr_status_pending_hire"),
    "Seasonal":          ("eligible",         "hr_status_seasonal"),
    "Leave of Absence":  ("suspended",        "hr_status_on_leave"),
    "Suspended":         ("suspended",        "hr_status_suspended"),
    "Inactive":          ("not_dispatchable", "hr_status_inactive"),
    "Terminated":        ("not_dispatchable", "hr_status_terminated"),
    "Resigned":          ("not_dispatchable", "hr_status_resigned"),
    "Retired":           ("not_dispatchable", "hr_status_retired"),
}

# Lightweight role keyword match — used to detect "driver relevant"
# without inventing a new role taxonomy.
_DRIVER_KEYWORDS = (
    "driver", "truck", "hauler", "haul", "operator", "cdl",
    "tanker", "dump",
)


def _is_driver_role(employee: Dict[str, Any]) -> bool:
    """Best-effort: does the HR record indicate driver/hauler work?

    Checks explicit driver flags first, then keyword-matches the
    role / trade / department fields. Mirrors the wording already
    captured in `employee_lifecycle.py` (cdl_holder /
    approved_company_driver) so we do not invent a new taxonomy.
    """
    if not employee:
        return False
    if employee.get("approved_company_driver") is True:
        return True
    if employee.get("cdl_holder") is True:
        return True
    blob = " ".join(
        str(employee.get(k, "") or "").lower()
        for k in ("role", "trade", "title", "department", "crew")
    )
    return any(kw in blob for kw in _DRIVER_KEYWORDS)


# ---------------------------------------------------------------------------
# PURE MAPPER (no DB)
# ---------------------------------------------------------------------------
def map_hr_lifecycle_to_transport(
    employee_record: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Project an HR employee record into a Transportation-facing
    snapshot. Pure function — never mutates the input."""
    if not employee_record:
        return {
            "hr_active": False,
            "transport_state": "needs_correction",
            "reason_codes": ["hr_employee_missing"],
            "reason_labels": [HR_REASON_LABELS["hr_employee_missing"]],
            "source_status": None,
            "source_fields": {},
        }

    # Snapshot a tight subset of HR fields — no PII expansion beyond
    # identifiers already approved for cross-module reads.
    src_fields = {
        "id": employee_record.get("id"),
        "employee_id": employee_record.get("employee_id"),
        "name": employee_record.get("name"),
        "lifecycle_status": employee_record.get("lifecycle_status"),
        "is_active": employee_record.get("is_active"),
        "role": employee_record.get("role"),
        "trade": employee_record.get("trade"),
        "department": employee_record.get("department"),
        "driver_status": employee_record.get("driver_status"),
        "approved_company_driver": employee_record.get("approved_company_driver"),
        "cdl_holder": employee_record.get("cdl_holder"),
        "termination_date": employee_record.get("termination_date"),
        "leave_start_date": employee_record.get("leave_start_date"),
        "expected_return_date": employee_record.get("expected_return_date"),
        "updated_at": employee_record.get("updated_at"),
    }

    status_raw = employee_record.get("lifecycle_status")
    mapped = _HR_STATUS_MAP.get(status_raw)
    if mapped is None:
        # Legacy / unknown status — never auto-block. Force a review.
        if employee_record.get("is_active") is False:
            transport_state, code = "not_dispatchable", "hr_status_inactive"
        else:
            transport_state, code = "pending_review", "hr_status_unknown"
    else:
        transport_state, code = mapped

    reason_codes = [code]
    # Driver-status sub-signal (CDL suspended / inactive). Only narrows
    # eligibility further — never relaxes the HR top-level decision.
    dstat = (employee_record.get("driver_status") or "").lower()
    if dstat in ("suspended", "inactive", "restricted"):
        if transport_state == "eligible":
            transport_state = "suspended" if dstat == "suspended" else "needs_correction"
        reason_codes.append(f"hr_status_{dstat}" if dstat == "suspended"
                            else "hr_role_not_driver")
    # Active employee but role no longer driver-relevant.
    if (
        transport_state == "eligible"
        and status_raw == "Active"
        and not _is_driver_role(employee_record)
    ):
        transport_state = "needs_correction"
        reason_codes.append("hr_role_not_driver")

    # De-dupe + label.
    seen: List[str] = []
    for c in reason_codes:
        if c and c not in seen:
            seen.append(c)
    labels = [HR_REASON_LABELS.get(c, c.replace("_", " ").capitalize())
              for c in seen]

    return {
        "hr_active": status_raw in ("Active", "Seasonal", "Pending Hire",
                                     "Leave of Absence"),
        "transport_state": transport_state,
        "reason_codes": seen,
        "reason_labels": labels,
        "source_status": status_raw,
        "source_fields": src_fields,
    }


# ---------------------------------------------------------------------------
# Helpers shared by the sync helper.
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _write_audit(db, *, employee_id: Optional[str],
                       transport_person_id: Optional[str],
                       trigger: str, kind: str,
                       prior_state: Optional[str], new_state: Optional[str],
                       source_status: Optional[str],
                       actor: Optional[str], extra: Optional[Dict[str, Any]] = None
                       ) -> None:
    """Best-effort audit write. Never raises."""
    try:
        row = {
            "id": uuid.uuid4().hex,
            "tenant": TENANT,
            "kind": kind,                    # e.g. transport_hr_sync_attempted
            "entity_type": "transport_person",
            "entity_id": transport_person_id,
            "employee_id": employee_id,
            "actor": actor or "system",
            "trigger": trigger,
            "prior_transport_state": prior_state,
            "new_transport_state": new_state,
            "source_hr_status": source_status,
            "ts": _now_iso(),
            "old": None,
            "new": extra or None,
        }
        await db.audit_events.insert_one(row)
    except Exception as exc:  # noqa: BLE001
        logger.warning("transport_hr_lifecycle audit insert failed: %s", exc)


async def _ensure_action_item(
    db, *, employee_id: Optional[str], transport_person_id: Optional[str],
    code: str, title: str, description: str, severity: str = "warn",
) -> None:
    """Create a transport_action_items row keyed by event_key. Idempotent."""
    try:
        event_key = (
            f"hr_lifecycle::{code}::{employee_id or 'unknown'}"
            f"::{transport_person_id or 'unlinked'}"
        )
        existing = await db.transport_action_items.find_one(
            {"tenant": TENANT, "related_event_key": event_key,
             "status": {"$in": ["open", "in_progress"]}}
        )
        if existing:
            return
        now = _now_iso()
        await db.transport_action_items.insert_one({
            "id": uuid.uuid4().hex,
            "tenant": TENANT,
            "source": "hr_lifecycle",
            "action_type": code,
            "severity": severity,
            "entity_type": "transport_person" if transport_person_id else "employee",
            "entity_id": transport_person_id or employee_id,
            "title": title,
            "description": description,
            "due_date": None,
            "status": "open",
            "assigned_role": "transportation_admin",
            "assigned_user_id": None,
            "related_route_key": "TRANSPORT_HR_LIFECYCLE_SYNC_ALERT",
            "related_event_key": event_key,
            "created_at": now,
            "updated_at": now,
            "resolved_at": None,
            "resolved_by": None,
        })
    except Exception as exc:  # noqa: BLE001
        logger.warning("transport_hr_lifecycle action_item insert failed: %s", exc)


# ---------------------------------------------------------------------------
# SYNC HELPER (single entry point for HR hooks)
# ---------------------------------------------------------------------------
async def sync_transport_person_from_hr(
    db,
    employee_id: Optional[str],
    *,
    trigger: str,
    actor: Optional[str] = None,
) -> Dict[str, Any]:
    """Read HR, project, update the matching transport_person snapshot,
    and recompute eligibility. NEVER mutates HR. NEVER raises — failures
    are captured into an action item + audit row so the caller's HR
    write remains atomic.

    Returns:
      {
        "status": "synced" | "not_driver_relevant" | "no_employee_id"
                  | "hr_not_found" | "no_transport_person" | "error",
        "transport_person_id": str | None,
        "projection": {...},  # may be None on early exits
        "action_required": bool,
      }
    """
    out: Dict[str, Any] = {
        "status": "synced",
        "transport_person_id": None,
        "projection": None,
        "action_required": False,
    }
    if not employee_id:
        out["status"] = "no_employee_id"
        await _write_audit(db, employee_id=None, transport_person_id=None,
                           trigger=trigger, kind="transport_hr_sync_skipped",
                           prior_state=None, new_state=None,
                           source_status=None, actor=actor,
                           extra={"reason": "no_employee_id"})
        return out

    try:
        # Locate HR employee. Match on both internal id AND HR
        # employee_id field for safety.
        employee = await db.employees.find_one(
            {"$or": [{"id": employee_id}, {"employee_id": employee_id}],
             "deleted_at": None},
            {"_id": 0},
        )
        if not employee:
            # Sync attempt audit, then action item for HR / transport admin.
            await _write_audit(db, employee_id=employee_id,
                               transport_person_id=None, trigger=trigger,
                               kind="transport_hr_sync_failed",
                               prior_state=None, new_state=None,
                               source_status=None, actor=actor,
                               extra={"reason": "hr_employee_missing"})
            await _ensure_action_item(
                db, employee_id=employee_id, transport_person_id=None,
                code="hr_employee_missing",
                title="HR lifecycle sync needs attention",
                description=(f"Transportation tried to read HR employee "
                             f"{employee_id} but the record could not be "
                             f"found. Review HR linkage."),
                severity="warn",
            )
            out.update({"status": "hr_not_found", "action_required": True})
            return out

        projection = map_hr_lifecycle_to_transport(employee)
        out["projection"] = projection

        # Locate existing transport_person — never create one here.
        # Operators link the projection explicitly via the existing
        # Transportation admin route. Drivers without an existing
        # link are not auto-created (mandate: do not duplicate
        # employees into Transportation).
        canonical_emp_id = employee.get("employee_id") or employee.get("id")
        person = await db.transport_persons.find_one({
            "tenant": TENANT,
            "kind": "masci_employee",
            "$or": [
                {"employee_id": canonical_emp_id},
                {"employee_id": employee.get("id")},
                {"employee_id": employee.get("employee_id")},
            ],
        })
        if not person:
            # Driver-relevant but unlinked → action item ONLY when the
            # employee is currently active and looks like a driver.
            if (
                projection["source_status"] == "Active"
                and _is_driver_role(employee)
            ):
                await _ensure_action_item(
                    db, employee_id=canonical_emp_id, transport_person_id=None,
                    code="hr_linkage_missing",
                    title="HR lifecycle sync needs attention",
                    description=(
                        "Active driver-relevant HR employee "
                        f"{canonical_emp_id} has no transport driver "
                        "linkage. Link via Transportation admin to "
                        "enable eligibility tracking."
                    ),
                    severity="info",
                )
                out["action_required"] = True
            await _write_audit(db, employee_id=canonical_emp_id,
                               transport_person_id=None, trigger=trigger,
                               kind="transport_hr_sync_attempted",
                               prior_state=None,
                               new_state=projection["transport_state"],
                               source_status=projection["source_status"],
                               actor=actor,
                               extra={"reason": "no_transport_person",
                                      "reason_codes": projection["reason_codes"]})
            out["status"] = "no_transport_person"
            return out

        prior_state = person.get("hr_projection", {}).get("transport_state")
        snapshot = {
            **projection,
            "synced_at": _now_iso(),
            "synced_trigger": trigger,
        }
        await db.transport_persons.update_one(
            {"_id": person["_id"]},
            {"$set": {
                "hr_projection": snapshot,
                "updated_at": _now_iso(),
            }},
        )
        out["transport_person_id"] = person["id"]

        # Recompute eligibility — best effort. We import lazily to
        # avoid a circular import at module load.
        try:
            from lib.transport_eligibility import compute_transport_eligibility
            full_record = await db.transport_persons.find_one(
                {"_id": person["_id"]})
            ctx = {
                "hr_lifecycle_active": projection["hr_active"],
                "hr_transport_state": projection["transport_state"],
                "hr_reason_codes": projection["reason_codes"],
                "hr_reason_labels": projection["reason_labels"],
                "hr_source_status": projection["source_status"],
            }
            elig = compute_transport_eligibility("person", full_record or {}, ctx)
            await db.transport_eligibility_state.update_one(
                {"tenant": TENANT, "target_type": "person",
                 "target_id": person["id"]},
                {"$set": {
                    "state": elig["state"],
                    "reasons": elig["reasons"],
                    "computed_at": elig["computed_at"],
                    "stale": False,
                },
                 "$setOnInsert": {
                    "id": uuid.uuid4().hex,
                    "tenant": TENANT,
                    "target_type": "person",
                    "target_id": person["id"],
                    "expires_at": None,
                    "phase": 2,
                 }},
                upsert=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("transport_hr_lifecycle eligibility recompute failed: %s",
                           exc)

        # Action items for derived risks.
        if projection["transport_state"] == "not_dispatchable":
            await _ensure_action_item(
                db, employee_id=canonical_emp_id,
                transport_person_id=person["id"],
                code="hr_dispatch_block",
                title="HR lifecycle change blocks dispatch eligibility",
                description=(
                    f"HR status {projection['source_status'] or 'unknown'} "
                    f"now blocks dispatch for driver {person.get('first_name', '')} "
                    f"{person.get('last_name', '')}."
                ).strip(),
                severity="block",
            )
        elif "hr_role_not_driver" in projection["reason_codes"]:
            await _ensure_action_item(
                db, employee_id=canonical_emp_id,
                transport_person_id=person["id"],
                code="hr_role_not_driver",
                title="Employee role requires Transportation review",
                description=(
                    f"HR role/title for employee {canonical_emp_id} no longer "
                    f"matches a driver-eligible classification. Review the "
                    f"Transportation driver record."
                ),
                severity="warn",
            )

        await _write_audit(db, employee_id=canonical_emp_id,
                           transport_person_id=person["id"], trigger=trigger,
                           kind="transport_hr_sync_succeeded",
                           prior_state=prior_state,
                           new_state=projection["transport_state"],
                           source_status=projection["source_status"],
                           actor=actor,
                           extra={"reason_codes": projection["reason_codes"]})
        return out
    except Exception as exc:  # noqa: BLE001
        # Never raise — HR write must succeed. Capture into action queue.
        logger.warning("sync_transport_person_from_hr failed: %s", exc)
        await _write_audit(db, employee_id=employee_id,
                           transport_person_id=None, trigger=trigger,
                           kind="transport_hr_sync_failed",
                           prior_state=None, new_state=None,
                           source_status=None, actor=actor,
                           extra={"error": str(exc)[:240]})
        await _ensure_action_item(
            db, employee_id=employee_id, transport_person_id=None,
            code="hr_sync_failed",
            title="HR lifecycle sync needs attention",
            description=(f"Transportation sync for HR employee "
                         f"{employee_id} encountered an unexpected error. "
                         f"Operator review required."),
            severity="warn",
        )
        out.update({"status": "error", "action_required": True})
        return out


# ---------------------------------------------------------------------------
# Fire-and-forget shim for HR routes. Keeps HR write paths simple — they
# call this once after a successful write and never await any return.
# ---------------------------------------------------------------------------
async def safe_sync_after_hr_write(
    db, employee_id: Optional[str], *, trigger: str,
    actor: Optional[str] = None,
) -> None:
    """Run :func:`sync_transport_person_from_hr` and swallow any
    exception. Designed for HR route post-write hooks where the sync
    is additive — HR success must NEVER depend on transport sync."""
    try:
        await sync_transport_person_from_hr(
            db, employee_id, trigger=trigger, actor=actor)
    except Exception as exc:  # noqa: BLE001
        logger.warning("safe_sync_after_hr_write swallowed error: %s", exc)
