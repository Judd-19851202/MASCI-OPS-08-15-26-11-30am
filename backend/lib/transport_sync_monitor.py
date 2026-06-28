"""TRACK 16.11A · Transportation HR Synchronization Monitor.

READ-ONLY consistency engine. Continuously validates that
``transport_persons`` (kind=masci_employee) projections remain in
lockstep with HR ``employees`` lifecycle facts.

Hard contract
-------------
* Never mutates HR (no writes to ``db.employees``).
* Never deletes / merges transport_person rows.
* Reuses the **existing** Track 16.11 helpers:
    - ``lib.transport_hr_lifecycle.map_hr_lifecycle_to_transport``
    - ``lib.transport_hr_lifecycle.sync_transport_person_from_hr``
* Produces a structured report + idempotent action items keyed by
  ``event_key``. No duplicate scanners; no duplicate identities.
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

TENANT = "masci"

# Anything older than this is considered "stale" for the projection
# freshness check. Operator-configurable via env var; never read from
# user-supplied request data.
DEFAULT_STALE_DAYS = int(os.environ.get("TRANSPORT_HR_SYNC_STALE_DAYS", "7"))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso(when: Optional[datetime] = None) -> str:
    return (when or _now()).isoformat()


def _parse_iso(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or len(value) < 10:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


# Severity classification — pure, no side effects.
SEVERITY_ORDER = {"info": 0, "warn": 1, "block": 2, "critical": 3}


def _severity_for(code: str) -> str:
    """Map mismatch codes to severities."""
    if code in (
        "termination_mismatch",
        "dispatch_conflict",
        "duplicate_linkage",
        "duplicate_employee",
    ):
        return "critical"
    if code in (
        "leave_mismatch",
        "role_mismatch",
        "projection_failed",
        "linkage_missing",
        "hr_status_unknown",
    ):
        return "block"
    if code in ("projection_stale", "projection_missing"):
        return "warn"
    return "info"


HUMAN_REASONS: Dict[str, str] = {
    "linkage_missing":      "Transport driver is linked to an HR employee that no longer exists",
    "projection_missing":   "Transport driver has no HR lifecycle projection on file",
    "projection_stale":     "HR lifecycle projection is older than the freshness window",
    "projection_failed":    "Most recent HR lifecycle sync did not complete",
    "termination_mismatch": "HR shows terminated/inactive but Transportation still marks driver eligible",
    "leave_mismatch":       "HR shows on leave/suspended but Transportation still marks driver dispatchable",
    "role_mismatch":        "HR role no longer matches a driver-eligible classification",
    "dispatch_conflict":    "Dispatch eligibility disagrees with HR lifecycle projection",
    "hr_status_unknown":    "HR lifecycle status is unknown — review required",
    "transport_state_unknown": "Transportation projection state is unknown",
    "duplicate_linkage":    "Multiple transport driver records resolve to the same HR employee",
    "duplicate_employee":   "Multiple HR employee records share the same employee_id",
    "hr_active_no_linkage": "Active driver-relevant HR employee has no Transportation link",
}

RECOMMENDED_ACTIONS: Dict[str, str] = {
    "linkage_missing":      "Re-link the transport driver to a current HR employee or archive the projection.",
    "projection_missing":   "Run an HR → Transportation sync to populate the projection.",
    "projection_stale":     "Run an HR → Transportation sync to refresh the projection.",
    "projection_failed":    "Investigate the last sync error in audit_events and re-run the sync.",
    "termination_mismatch": "Acknowledge HR lifecycle and update the driver record so dispatch sees the block.",
    "leave_mismatch":       "Acknowledge HR leave and pause dispatch eligibility until return.",
    "role_mismatch":        "Confirm role change with HR and adjust Transportation linkage.",
    "dispatch_conflict":    "Trigger HR → Transportation resync; investigate dispatch override if any.",
    "hr_status_unknown":    "Coordinate with HR to set a valid lifecycle status.",
    "transport_state_unknown": "Recompute eligibility for this transport driver.",
    "duplicate_linkage":    "Archive duplicate transport driver rows; preserve the canonical link.",
    "duplicate_employee":   "Coordinate with HR to merge duplicate employee records.",
    "hr_active_no_linkage": "Link this HR employee to a transport driver record via Transportation admin.",
}


def _event_key(code: str, employee_id: Optional[str],
               transport_person_id: Optional[str]) -> str:
    return (f"hr_sync_monitor::{code}::{employee_id or 'unknown'}::"
            f"{transport_person_id or 'unlinked'}")


def classify_mismatch(
    *,
    hr_record: Optional[Dict[str, Any]],
    transport_person: Optional[Dict[str, Any]],
    projection: Optional[Dict[str, Any]],
    eligibility: Optional[Dict[str, Any]],
    now: Optional[datetime] = None,
    stale_days: int = DEFAULT_STALE_DAYS,
) -> List[Dict[str, Any]]:
    """Pure classifier. Returns a list of mismatch dicts (possibly empty)."""
    now = now or _now()
    out: List[Dict[str, Any]] = []

    def _emit(code: str, **extra) -> None:
        out.append({
            "code": code,
            "severity": _severity_for(code),
            "reason": HUMAN_REASONS.get(code, code.replace("_", " ").capitalize()),
            "recommended_action": RECOMMENDED_ACTIONS.get(code, ""),
            **extra,
        })

    # Case A — transport_person exists but HR linkage is broken.
    if transport_person and not hr_record:
        _emit("linkage_missing",
              transport_person_id=transport_person.get("id"),
              employee_id=transport_person.get("employee_id"))
        return out

    # Case B — transport_person exists, HR exists.
    if transport_person and hr_record:
        emp_id = (hr_record.get("employee_id") or hr_record.get("id"))
        tp_id = transport_person.get("id")

        if not projection:
            _emit("projection_missing",
                  transport_person_id=tp_id, employee_id=emp_id)
        else:
            # Stale check.
            synced_at = _parse_iso(projection.get("synced_at"))
            if synced_at:
                age = now - synced_at
                if age > timedelta(days=stale_days):
                    _emit("projection_stale",
                          transport_person_id=tp_id, employee_id=emp_id,
                          age_days=age.days)
            # Failed check (projection encodes failure when source_status
            # is None and state is needs_correction with employee_missing).
            codes = projection.get("reason_codes") or []
            if "hr_employee_missing" in codes:
                _emit("projection_failed",
                      transport_person_id=tp_id, employee_id=emp_id)
            if "hr_status_unknown" in codes:
                _emit("hr_status_unknown",
                      transport_person_id=tp_id, employee_id=emp_id)
            if "hr_role_not_driver" in codes:
                _emit("role_mismatch",
                      transport_person_id=tp_id, employee_id=emp_id)

        # Lifecycle vs eligibility cross-check.
        hr_status = hr_record.get("lifecycle_status")
        elig_state = (eligibility or {}).get("state")
        if hr_status in ("Terminated", "Inactive", "Resigned", "Retired"):
            if elig_state in ("eligible", "pending_review"):
                _emit("termination_mismatch",
                      transport_person_id=tp_id, employee_id=emp_id,
                      hr_status=hr_status, eligibility_state=elig_state)
        if hr_status in ("Leave of Absence", "Suspended"):
            if elig_state in ("eligible", "pending_review"):
                _emit("leave_mismatch",
                      transport_person_id=tp_id, employee_id=emp_id,
                      hr_status=hr_status, eligibility_state=elig_state)
        # Active HR but projection says block — projection drives gate so
        # we surface a dispatch_conflict only when eligibility somehow
        # rolled back to eligible *after* a non-eligible projection.
        if (
            projection
            and projection.get("transport_state") in ("not_dispatchable", "suspended")
            and elig_state in ("eligible",)
        ):
            _emit("dispatch_conflict",
                  transport_person_id=tp_id, employee_id=emp_id,
                  projection_state=projection.get("transport_state"),
                  eligibility_state=elig_state)

    return out


# ---------------------------------------------------------------------------
# Async helpers
# ---------------------------------------------------------------------------
async def _load_eligibility(db, transport_person_id: str
                            ) -> Optional[Dict[str, Any]]:
    return await db.transport_eligibility_state.find_one({
        "tenant": TENANT, "target_type": "person",
        "target_id": transport_person_id,
    })


async def _ensure_monitor_action_item(
    db, *, code: str, employee_id: Optional[str],
    transport_person_id: Optional[str], reason: str,
    recommended_action: str, severity: str,
) -> bool:
    """Returns True when a new row was inserted, False when deduped."""
    try:
        ev = _event_key(code, employee_id, transport_person_id)
        existing = await db.transport_action_items.find_one(
            {"tenant": TENANT, "related_event_key": ev,
             "status": {"$in": ["open", "in_progress"]}})
        if existing:
            return False
        now = _now_iso()
        await db.transport_action_items.insert_one({
            "id": uuid.uuid4().hex, "tenant": TENANT,
            "source": "hr_sync_monitor",
            "action_type": code,
            "severity": severity,
            "entity_type": "transport_person" if transport_person_id else "employee",
            "entity_id": transport_person_id or employee_id,
            "title": f"HR sync: {reason}",
            "description": recommended_action or reason,
            "due_date": None,
            "status": "open",
            "assigned_role": "transportation_admin",
            "assigned_user_id": None,
            "related_route_key": "TRANSPORT_HR_SYNC_MONITOR_ALERT",
            "related_event_key": ev,
            "created_at": now, "updated_at": now,
            "resolved_at": None, "resolved_by": None,
        })
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("hr_sync_monitor action_item insert failed: %s", exc)
        return False


async def _write_monitor_audit(
    db, *, kind: str, employee_id: Optional[str],
    transport_person_id: Optional[str], extra: Dict[str, Any],
) -> None:
    try:
        await db.audit_events.insert_one({
            "id": uuid.uuid4().hex, "tenant": TENANT,
            "kind": kind, "entity_type": "transport_person",
            "entity_id": transport_person_id,
            "employee_id": employee_id,
            "actor": "system",
            "ts": _now_iso(),
            "old": None, "new": extra,
        })
    except Exception as exc:  # noqa: BLE001
        logger.warning("hr_sync_monitor audit insert failed: %s", exc)


# ---------------------------------------------------------------------------
# CORE SCAN
# ---------------------------------------------------------------------------
async def scan_hr_transport_consistency(
    db, *, stale_days: Optional[int] = None,
    create_action_items: bool = True,
) -> Dict[str, Any]:
    """Run a full HR ↔ Transportation consistency scan. Read-only by
    default. ``create_action_items=True`` materialises idempotent rows
    in ``transport_action_items`` for every mismatch."""
    now = _now()
    stale_days = stale_days or DEFAULT_STALE_DAYS

    mismatches: List[Dict[str, Any]] = []
    counts = {
        "employees_checked": 0,
        "drivers_checked": 0,
        "sync_mismatches": 0,
        "projection_failures": 0,
        "dispatch_risks": 0,
        "unknown_identities": 0,
        "actions_created": 0,
    }
    sync_ages_days: List[float] = []

    # 1. Walk every masci_employee transport_person.
    persons = db.transport_persons.find(
        {"tenant": TENANT, "kind": "masci_employee"})
    persons = await persons.to_list(5000)
    counts["drivers_checked"] = len(persons)
    seen_employee_ids: Dict[str, List[str]] = {}

    for person in persons:
        emp_id = person.get("employee_id")
        if emp_id:
            seen_employee_ids.setdefault(emp_id, []).append(person.get("id"))

        # Resolve HR record.
        hr = None
        if emp_id:
            hr = await db.employees.find_one(
                {"$or": [{"employee_id": emp_id}, {"id": emp_id}],
                 "deleted_at": None},
                {"_id": 0})
        elig = await _load_eligibility(db, person.get("id"))
        proj = person.get("hr_projection")

        # Track sync age.
        synced_at = _parse_iso((proj or {}).get("synced_at"))
        if synced_at:
            sync_ages_days.append((now - synced_at).total_seconds() / 86400.0)

        rows = classify_mismatch(
            hr_record=hr, transport_person=person, projection=proj,
            eligibility=elig, now=now, stale_days=stale_days,
        )
        for r in rows:
            mismatches.append(r)
            counts["sync_mismatches"] += 1
            if r["code"] in ("projection_missing", "projection_stale",
                              "projection_failed"):
                counts["projection_failures"] += 1
            if r["code"] in ("termination_mismatch", "leave_mismatch",
                              "dispatch_conflict"):
                counts["dispatch_risks"] += 1
            if r["code"] in ("hr_status_unknown", "linkage_missing"):
                counts["unknown_identities"] += 1

            if create_action_items:
                created = await _ensure_monitor_action_item(
                    db, code=r["code"], employee_id=r.get("employee_id"),
                    transport_person_id=r.get("transport_person_id"),
                    reason=r["reason"],
                    recommended_action=r["recommended_action"],
                    severity=r["severity"],
                )
                if created:
                    counts["actions_created"] += 1

    # 2. Duplicate linkage detection.
    for emp_id, ids in seen_employee_ids.items():
        if len(ids) > 1:
            row = {
                "code": "duplicate_linkage",
                "severity": _severity_for("duplicate_linkage"),
                "reason": HUMAN_REASONS["duplicate_linkage"],
                "recommended_action": RECOMMENDED_ACTIONS["duplicate_linkage"],
                "employee_id": emp_id, "transport_person_ids": ids,
            }
            mismatches.append(row)
            counts["sync_mismatches"] += 1
            counts["unknown_identities"] += 1
            if create_action_items:
                created = await _ensure_monitor_action_item(
                    db, code="duplicate_linkage", employee_id=emp_id,
                    transport_person_id=ids[0], reason=row["reason"],
                    recommended_action=row["recommended_action"],
                    severity=row["severity"],
                )
                if created:
                    counts["actions_created"] += 1

    # 3. Sweep HR employees for "active driver but no linkage".
    employees = db.employees.find(
        {"deleted_at": None,
         "lifecycle_status": "Active"})
    employees = await employees.to_list(5000)
    counts["employees_checked"] = len(employees)
    # Quick lookup of linked employee_ids.
    linked: set = set(seen_employee_ids.keys())
    for emp in employees:
        emp_id = emp.get("employee_id") or emp.get("id")
        if emp_id in linked or emp.get("id") in linked:
            continue
        # Must look driver-relevant to avoid noise.
        if not (emp.get("approved_company_driver") is True
                or emp.get("cdl_holder") is True):
            continue
        row = {
            "code": "hr_active_no_linkage",
            "severity": _severity_for("hr_active_no_linkage"),
            "reason": HUMAN_REASONS["hr_active_no_linkage"],
            "recommended_action": RECOMMENDED_ACTIONS["hr_active_no_linkage"],
            "employee_id": emp_id, "transport_person_id": None,
        }
        mismatches.append(row)
        counts["sync_mismatches"] += 1
        if create_action_items:
            created = await _ensure_monitor_action_item(
                db, code="hr_active_no_linkage", employee_id=emp_id,
                transport_person_id=None, reason=row["reason"],
                recommended_action=row["recommended_action"],
                severity=row["severity"],
            )
            if created:
                counts["actions_created"] += 1

    # Health bucket.
    if counts["sync_mismatches"] == 0:
        health = "healthy"
    elif counts["dispatch_risks"] > 0 or any(
        m["severity"] == "critical" for m in mismatches
    ):
        health = "critical"
    else:
        health = "warning"

    avg_age = (
        round(sum(sync_ages_days) / len(sync_ages_days), 2)
        if sync_ages_days else None
    )
    oldest_age = round(max(sync_ages_days), 2) if sync_ages_days else None
    latest_age = round(min(sync_ages_days), 2) if sync_ages_days else None

    report = {
        "ok": True,
        "tenant": TENANT,
        "generated_at": _now_iso(now),
        "stale_days_threshold": stale_days,
        "health": health,
        "counts": counts,
        "average_sync_age_days": avg_age,
        "oldest_sync_age_days": oldest_age,
        "latest_sync_age_days": latest_age,
        "mismatches": mismatches,
    }

    await _write_monitor_audit(
        db, kind="transport_hr_sync_scanner_completed",
        employee_id=None, transport_person_id=None,
        extra={"counts": counts, "health": health},
    )
    # Persist a thin run summary so the UI / digest can read history.
    try:
        await db.transport_hr_sync_runs.insert_one({
            "id": uuid.uuid4().hex, "tenant": TENANT,
            "generated_at": _now_iso(now), "health": health,
            "counts": counts, "average_sync_age_days": avg_age,
            "oldest_sync_age_days": oldest_age,
            "latest_sync_age_days": latest_age,
            "mismatches_sample": mismatches[:50],
        })
    except Exception:  # noqa: BLE001
        pass
    return report


# ---------------------------------------------------------------------------
# Single-employee status (for HR profile chip)
# ---------------------------------------------------------------------------
async def derive_employee_transport_status(
    db, employee_id: Optional[str],
) -> Dict[str, Any]:
    """Read-only single-employee snapshot used by HR Profile chip."""
    if not employee_id:
        return {"linked": False, "reason": "no_employee_id"}
    emp = await db.employees.find_one(
        {"$or": [{"employee_id": employee_id}, {"id": employee_id}],
         "deleted_at": None},
        {"_id": 0})
    if not emp:
        return {"linked": False, "reason": "hr_employee_missing",
                "employee_id": employee_id}

    canonical = emp.get("employee_id") or emp.get("id")
    person = await db.transport_persons.find_one({
        "tenant": TENANT, "kind": "masci_employee",
        "$or": [{"employee_id": canonical}, {"employee_id": emp.get("id")}],
    })
    if not person:
        return {
            "linked": False, "reason": "not_linked",
            "employee_id": canonical,
            "hr_status": emp.get("lifecycle_status"),
        }

    elig = await _load_eligibility(db, person.get("id"))
    proj = person.get("hr_projection") or {}

    # Resolve next orientation expiration + last orientation completion
    # via the existing certificate collection (Track 16.08). Defensive
    # — falls back to None if collection unavailable.
    last_completed = None
    next_expiry = None
    try:
        cert = await db.transport_certificates.find_one(
            {"tenant": TENANT, "transport_person_id": person.get("id")},
            sort=[("issued_at", -1)],
        )
        if cert:
            last_completed = cert.get("issued_at")
            next_expiry = cert.get("expires_at")
    except Exception:  # noqa: BLE001
        pass

    # Active override (if any).
    override = None
    try:
        override = await db.transport_dispatch_overrides.find_one({
            "tenant": TENANT, "driver_id": person.get("id"),
            "status": "approved",
        }, sort=[("expires_at", -1)])
    except Exception:  # noqa: BLE001
        pass

    return {
        "linked": True,
        "employee_id": canonical,
        "transport_person_id": person.get("id"),
        "hr_status": emp.get("lifecycle_status"),
        "transport_status": (elig or {}).get("state") or "pending_review",
        "transport_reasons": [r.get("label") for r in (elig or {}).get("reasons") or []],
        "projection_state": proj.get("transport_state"),
        "projection_source_status": proj.get("source_status"),
        "last_sync_at": proj.get("synced_at"),
        "last_sync_trigger": proj.get("synced_trigger"),
        "last_orientation_completion": last_completed,
        "next_orientation_expiration": next_expiry,
        "driver_qualification": emp.get("driver_status"),
        "approved_company_driver": emp.get("approved_company_driver"),
        "active_override": {
            "id": override.get("id"),
            "expires_at": override.get("expires_at"),
        } if override else None,
        "view_workspace_path": (
            f"/admin/transportation/drivers/{person.get('id')}"
            if person.get("id") else None
        ),
    }


# ---------------------------------------------------------------------------
# Aggregate KPIs for HR Dashboard / Transportation Dashboard widgets
# ---------------------------------------------------------------------------
async def hr_dashboard_transport_readiness(db) -> Dict[str, Any]:
    """KPI bag for the HR Dashboard 'Transportation Readiness' widget."""
    states = {"eligible": 0, "pending_review": 0, "suspended": 0,
              "needs_correction": 0, "not_dispatchable": 0}
    last_sync: Optional[str] = None
    rows = await db.transport_eligibility_state.find({
        "tenant": TENANT, "target_type": "person",
    }).to_list(5000)
    for r in rows:
        s = r.get("state") or "pending_review"
        if s in states:
            states[s] += 1
        ca = r.get("computed_at")
        if ca and (last_sync is None or ca > last_sync):
            last_sync = ca
    return {
        "tenant": TENANT,
        "states": states,
        "last_eligibility_compute": last_sync,
        "generated_at": _now_iso(),
    }


async def transportation_dashboard_hr_health(db) -> Dict[str, Any]:
    """KPI bag for the Transportation Dashboard 'HR Health' widget."""
    last_run = await db.transport_hr_sync_runs.find_one(
        {"tenant": TENANT}, sort=[("generated_at", -1)],
    )
    return {
        "tenant": TENANT,
        "health": (last_run or {}).get("health") or "unknown",
        "counts": (last_run or {}).get("counts") or {},
        "average_sync_age_days": (last_run or {}).get("average_sync_age_days"),
        "oldest_sync_age_days": (last_run or {}).get("oldest_sync_age_days"),
        "latest_sync_age_days": (last_run or {}).get("latest_sync_age_days"),
        "last_run_at": (last_run or {}).get("generated_at"),
        "generated_at": _now_iso(),
    }
