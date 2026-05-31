"""Pillar 1 · Phase 1A-2 · Accountability Projection Layer.

Read-only pure function library. Projects a source workflow row (or a
virtual signal payload) into the canonical AccountabilityProjection
shape defined by:

    /app/memory/ACCOUNTABILITY_ENGINE_ARCHITECTURE.md   §3
    /app/memory/ACCOUNTABILITY_LIFECYCLE_SPEC.md        §4
    /app/memory/ACCOUNTABILITY_TIMELINE_SPEC.md         §3

This module:
    * NEVER writes to any collection.
    * NEVER changes any source row.
    * NEVER emits notifications, tasks, or events.
    * Does not enforce transitions; it only describes the projection.
    * Reserved `escalation_level` is always 0 (Pillar 1B activates it).

Six source modules covered in Phase 1A-2:
    1. tasks                  — db.tasks
    2. safety.corrective_actions
                              — db.corrective_actions
    3. po.requests            — db.po_requests
    4. equipment.dvir         — db.fleet_defects
    5. safety.incidents       — db.incidents
    6. virtual.<signal_kind>  — synthesized from Command Center signal payload

All six produce the same 24-field projection dict; their `timeline_events`
field surfaces native audit/history arrays translated into canonical
event shape (read-only translation; no new collection in this phase).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


# ────────────────────────────────────────────────────────────────────
# Canonical contract
# ────────────────────────────────────────────────────────────────────
CANONICAL_STATUSES = (
    "open",
    "in_progress",
    "pending_review",
    "resolved",
    "closed",
    "cancelled",
)

CANONICAL_EVENT_KINDS = (
    "created",
    "assigned",
    "viewed",
    "updated",
    "commented",
    "status_changed",
    "resolved",
    "closed",
    "reopened",
    # "escalated" reserved · NEVER emitted in Phase 1A-2.
)

ALLOWED_PRIORITIES = ("Low", "Medium", "High", "Critical")


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────
def _parse_ts(v: Any) -> Optional[datetime]:
    """Accept BSON datetime OR ISO-8601 string OR date-only string;
    return tz-aware UTC."""
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if isinstance(v, str):
        try:
            s = v.replace("Z", "+00:00") if v.endswith("Z") else v
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _is_overdue(status: str, due_at: Optional[datetime]) -> bool:
    """Overdue overlay · Lifecycle §8 OD-1."""
    if status not in ("open", "in_progress") or due_at is None:
        return False
    return datetime.now(timezone.utc) > due_at


def _accountability_id(source_module: str, source_record_id: str) -> str:
    """Deterministic hash for non-task sources.

    Architecture §3.1: for `db.tasks` rows the projection caller should
    pass the task `id` directly; for any other source we synthesize a
    deterministic uuid-shaped key from (source_module, source_record_id)
    so the same row always produces the same projection id across reads.
    """
    h = hashlib.sha256(f"{source_module}::{source_record_id}".encode("utf-8")).hexdigest()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def _priority_or_default(v: Any) -> str:
    if v in ALLOWED_PRIORITIES:
        return v  # type: ignore[return-value]
    return "Medium"


def _empty_actor() -> Dict[str, Any]:
    return {"role": "system", "name": "system", "user_id": None, "employee_id": None}


def _actor(role: Optional[str], name: Optional[str] = None,
           user_id: Optional[str] = None,
           employee_id: Optional[str] = None) -> Dict[str, Any]:
    return {
        "role": (role or "system"),
        "name": (name or (role or "system")),
        "user_id": user_id,
        "employee_id": employee_id,
    }


def _canonical_event(*, kind: str, at: Any, actor: Dict[str, Any],
                     from_status: Optional[str] = None,
                     to_status: Optional[str] = None,
                     notes: Optional[str] = None,
                     changes: Optional[Dict[str, Any]] = None,
                     seq: int = 0) -> Dict[str, Any]:
    """Build one canonical timeline event row · Timeline Spec §2.1."""
    return {
        "event_kind": kind,
        "event_seq": seq,
        "actor": actor,
        "at": _iso(_parse_ts(at)),
        "from_status": from_status,
        "to_status": to_status,
        "notes": notes,
        "changes": changes,
        "linked_notification_id": None,
        "system_origin": "projection_readonly",
    }


# ────────────────────────────────────────────────────────────────────
# Status mapping tables · Lifecycle §4
# ────────────────────────────────────────────────────────────────────
_TASK_STATUS_MAP: Dict[str, str] = {
    "Open": "open",
    "In Progress": "in_progress",
    "Pending Review": "pending_review",
    "Completed": "resolved",
    "Closed": "closed",
    "Cancelled": "cancelled",
    # Legacy stored value · Lifecycle §4.1: surface as open + overdue overlay.
    "Overdue": "open",
}

_CA_STATUS_MAP: Dict[str, str] = {
    "Open": "open",
    "In Progress": "in_progress",
    "Pending Review": "pending_review",
    "Verified": "resolved",
    "Closed": "closed",
    "Closed - Verified": "closed",
}

_PO_STATUS_MAP: Dict[str, str] = {
    "Submitted": "open",
    "Pending Approval": "open",
    "Clarification Needed": "in_progress",
    "Approved": "resolved",
    "Pending Receipt": "pending_review",
    "Closed": "closed",
    "Rejected": "cancelled",
    "Cancelled": "cancelled",
    "Overdue Receipt": "pending_review",
}

_FLEET_STATUS_MAP: Dict[str, str] = {
    "open": "open",
    "acknowledged": "in_progress",
    "repaired": "pending_review",
    "cleared": "closed",
}


# ────────────────────────────────────────────────────────────────────
# Incident closure derivation · Lifecycle §4.5
# ────────────────────────────────────────────────────────────────────
async def _incident_is_resolved_via_ca(db: Any, inc_id: str) -> bool:
    if not inc_id:
        return False
    closed = await db.corrective_actions.find_one(
        {
            "$or": [{"source_id": inc_id}, {"incident_id": inc_id}],
            "status": {"$in": ["Closed", "Verified", "Completed", "Closed - Verified"]},
        },
        {"_id": 0, "id": 1},
    )
    return closed is not None


async def _incident_has_open_ca(db: Any, inc_id: str) -> bool:
    if not inc_id:
        return False
    open_ca = await db.corrective_actions.find_one(
        {
            "$or": [{"source_id": inc_id}, {"incident_id": inc_id}],
            "status": {"$in": ["Open", "In Progress", "Pending Review"]},
        },
        {"_id": 0, "id": 1},
    )
    return open_ca is not None


# ────────────────────────────────────────────────────────────────────
# Timeline translators · convert native arrays into canonical events
# ────────────────────────────────────────────────────────────────────
def _translate_task_audit(audit: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """tasks.audit[] → canonical events.

    Native entry shape (tasks_notifications.py:178-182):
        {at, by:{role,name}, action, changes?:{field:{from,to}}}
    """
    out: List[Dict[str, Any]] = []
    for i, entry in enumerate(audit or []):
        action = (entry.get("action") or "").strip().lower()
        by = entry.get("by") or {}
        actor = _actor(by.get("role"), by.get("name"), by.get("user_id"))

        # Canonical kind selection
        if action == "created":
            kind = "created"
        elif action == "updated":
            kind = "updated"
            changes = entry.get("changes") or {}
            # Detect a status transition within the changes payload
            if "status" in changes:
                # Emit BOTH an `updated` and a `status_changed` event at
                # the same `at` — Timeline §3 double-event pattern.
                out.append(_canonical_event(
                    kind="status_changed",
                    at=entry.get("at"),
                    actor=actor,
                    from_status=_TASK_STATUS_MAP.get(
                        changes["status"].get("from") or "", "open"),
                    to_status=_TASK_STATUS_MAP.get(
                        changes["status"].get("to") or "", "open"),
                    seq=i,
                ))
            out.append(_canonical_event(
                kind="updated",
                at=entry.get("at"),
                actor=actor,
                changes=changes or None,
                seq=i,
            ))
            continue
        else:
            kind = action if action in CANONICAL_EVENT_KINDS else "updated"

        out.append(_canonical_event(kind=kind, at=entry.get("at"),
                                    actor=actor, seq=i))
    return out


def _translate_ca_status_history(history: List[Dict[str, Any]]
                                  ) -> List[Dict[str, Any]]:
    """corrective_actions.status_history[] → canonical events.

    Native entry shape (corrective_actions.py:209-220):
        {from, to, by_name, by_email, at, note}
    """
    out: List[Dict[str, Any]] = []
    for i, entry in enumerate(history or []):
        from_native = entry.get("from") or ""
        to_native = entry.get("to") or ""
        actor = _actor("safety", entry.get("by_name") or "Safety", None)
        out.append(_canonical_event(
            kind="status_changed",
            at=entry.get("at"),
            actor=actor,
            from_status=_CA_STATUS_MAP.get(from_native, "open"),
            to_status=_CA_STATUS_MAP.get(to_native, "open"),
            notes=entry.get("note") or None,
            seq=i,
        ))
        # Emit derived resolved/closed events when transitions cross the
        # canonical resolved/closed boundary.
        to_canon = _CA_STATUS_MAP.get(to_native, "")
        if to_canon == "resolved":
            out.append(_canonical_event(
                kind="resolved", at=entry.get("at"), actor=actor,
                notes=entry.get("note") or None, seq=i,
            ))
        elif to_canon == "closed":
            out.append(_canonical_event(
                kind="closed", at=entry.get("at"), actor=actor,
                notes=entry.get("note") or None, seq=i,
            ))
    return out


def _translate_po_audit(audit: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """po_requests.audit[] → canonical events.

    Native entry shape (po_requests.py:175-184):
        {at, by:{role,name}, action, details?}
    """
    out: List[Dict[str, Any]] = []
    for i, entry in enumerate(audit or []):
        action = (entry.get("action") or "").strip().lower()
        by = entry.get("by") or {}
        actor = _actor(by.get("role"), by.get("name"), by.get("user_id"))

        # Map domain actions to canonical kinds.
        if action in ("submitted", "created"):
            kind = "created"
        elif action in ("approved",):
            kind = "resolved"
        elif action in ("rejected", "cancelled"):
            kind = "status_changed"
        elif action in ("clarification_response", "clarification_requested"):
            kind = "commented"
        elif action in ("receipt_uploaded",):
            kind = "updated"
        elif action in ("closed",):
            kind = "closed"
        elif action in ("reassigned", "reassign"):
            kind = "assigned"
        else:
            kind = "updated"

        out.append(_canonical_event(
            kind=kind,
            at=entry.get("at"),
            actor=actor,
            notes=(entry.get("details") or {}).get("note") if isinstance(
                entry.get("details"), dict) else None,
            seq=i,
        ))
    return out


def _synthesize_fleet_defect_timeline(row: Dict[str, Any]
                                       ) -> List[Dict[str, Any]]:
    """fleet_defects has no native array — synthesize events from inline
    timestamps (created/reported, acknowledged, repaired, cleared).
    """
    out: List[Dict[str, Any]] = []
    seq = 0

    created_at = row.get("reported_at") or row.get("created_at")
    if created_at:
        out.append(_canonical_event(
            kind="created", at=created_at,
            actor=_actor("driver", row.get("reported_by_name") or "Driver",
                         employee_id=row.get("reported_by_employee_id")),
            seq=seq,
        ))
        seq += 1

    if row.get("acknowledged_at"):
        actor = _actor("shop", row.get("acknowledged_by_name") or "Shop")
        out.append(_canonical_event(
            kind="status_changed", at=row["acknowledged_at"], actor=actor,
            from_status="open", to_status="in_progress", seq=seq,
        ))
        seq += 1

    if row.get("repaired_at"):
        actor = _actor("shop", row.get("repaired_by_name") or "Shop")
        out.append(_canonical_event(
            kind="status_changed", at=row["repaired_at"], actor=actor,
            from_status="in_progress", to_status="pending_review",
            notes=row.get("repair_notes") or None, seq=seq,
        ))
        seq += 1

    if row.get("cleared_at"):
        actor = _actor("shop", row.get("cleared_by_name") or "Shop")
        out.append(_canonical_event(
            kind="status_changed", at=row["cleared_at"], actor=actor,
            from_status="pending_review", to_status="closed", seq=seq,
        ))
        seq += 1
        out.append(_canonical_event(
            kind="closed", at=row["cleared_at"], actor=actor, seq=seq,
        ))

    return out


def _synthesize_incident_timeline(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Incidents have no own timeline; surface the creation + any
    `corrected_on_site=Yes` resolution. Linked-CA events are NOT pulled
    in here — the caller may merge them in async-aware code path.
    """
    out: List[Dict[str, Any]] = []
    seq = 0

    created_at = row.get("created_at") or row.get("incident_date") or row.get("date_occurred")
    if created_at:
        out.append(_canonical_event(
            kind="created", at=created_at,
            actor=_actor("safety", "Safety"),
            seq=seq,
        ))
        seq += 1

    if str(row.get("corrected_on_site") or "").strip().lower() == "yes":
        # Use updated_at if present, else created_at as the resolution stamp.
        at = row.get("corrected_at") or row.get("updated_at") or created_at
        out.append(_canonical_event(
            kind="resolved", at=at,
            actor=_actor("safety", "Safety"),
            notes="corrected_on_site=Yes", seq=seq,
        ))

    return out


# ────────────────────────────────────────────────────────────────────
# Owner resolution per source
# ────────────────────────────────────────────────────────────────────
def _owner_from_task(row: Dict[str, Any]) -> Dict[str, Any]:
    role = row.get("assignee_role") or "system"
    name = (row.get("assignee_name")
            or (row.get("created_by") or {}).get("name")
            or role.capitalize() if isinstance(role, str) else "system")
    return {
        "owner_role": role,
        "owner_user_id": row.get("assignee_user_id"),
        "owner_employee_id": row.get("assignee_employee_id"),
        "owner_display_name": name,
    }


def _owner_from_ca(row: Dict[str, Any]) -> Dict[str, Any]:
    name = (row.get("assigned_to_name") or "").strip() or "Safety"
    return {
        "owner_role": "safety",
        "owner_user_id": None,  # Audit A-04: native field is email string, no FK.
        "owner_employee_id": (row.get("employee_master_id") or "").strip() or None,
        "owner_display_name": name,
    }


def _owner_from_po(row: Dict[str, Any]) -> Dict[str, Any]:
    """Approver-derived ownership · Audit A-05 / Integration §3.5.

    The PO's actual owner is "the current pending approver". Native
    schema does not surface that today (po_requests.py has no
    `current_approver` field). Per Roadmap Phase 1A-4 a dedicated
    helper resolves it from approval routing rules.

    In Phase 1A-2 we project a best-effort owner:
      - For statuses {Submitted, Pending Approval, Clarification Needed,
        Pending Receipt, Overdue Receipt}: role="approver_per_routing",
        display name="Pending Approver".
      - For statuses {Approved, Closed}: the last `approved_by` in audit
        is treated as the resolver/closer (used elsewhere; here the owner
        is "approver_per_routing" still — the projection's
        `resolved_by` field captures the human).
      - For statuses {Rejected, Cancelled}: requester is the de-facto
        owner since no further action is expected.
    """
    status = row.get("status") or ""
    if status in ("Rejected", "Cancelled"):
        return {
            "owner_role": row.get("requested_by_role") or "leadership",
            "owner_user_id": row.get("requested_by_user_id"),
            "owner_employee_id": row.get("requested_by_employee_id"),
            "owner_display_name": row.get("requested_by_name") or "Requester",
        }
    return {
        "owner_role": "approver_per_routing",
        "owner_user_id": None,
        "owner_employee_id": None,
        "owner_display_name": "Pending Approver",
    }


def _owner_from_fleet_defect(row: Dict[str, Any]) -> Dict[str, Any]:
    """Audit A-02: fleet_defects has no assignee_role field; default to
    shop role + acknowledged_by_name display when present.
    """
    name = (row.get("acknowledged_by_name") or "").strip() or "Shop"
    return {
        "owner_role": "shop",
        "owner_user_id": None,
        "owner_employee_id": None,
        "owner_display_name": name,
    }


def _owner_from_incident(row: Dict[str, Any]) -> Dict[str, Any]:
    """Audit A-01: incidents have no native assignee. Default safety.
    The projection caller may overwrite owner_display_name from a
    linked CA's assignee when present (handled in async project()).
    """
    return {
        "owner_role": "safety",
        "owner_user_id": None,
        "owner_employee_id": None,
        "owner_display_name": "Safety",
    }


# ────────────────────────────────────────────────────────────────────
# Due date resolution
# ────────────────────────────────────────────────────────────────────
def _due_at_for_task(row: Dict[str, Any]) -> Optional[datetime]:
    return _parse_ts(row.get("due_at"))


def _due_at_for_ca(row: Dict[str, Any]) -> Optional[datetime]:
    return _parse_ts(row.get("due_date"))


def _due_at_for_po(row: Dict[str, Any]) -> Optional[datetime]:
    """PO SLA per Command Center thresholds (APP-AMBER min_days=3): the
    projection's due_at is `created_at + 3 days` so an aged PO surfaces
    as overdue without changing the source schema.
    """
    created = _parse_ts(row.get("created_at"))
    if not created:
        return None
    return created + timedelta(days=3)


def _due_at_for_fleet_defect(row: Dict[str, Any]) -> Optional[datetime]:
    """Fleet defect SLA per EQP-OOS-OLD red_hours=72 (OOS units) /
    EQP-OOS-NEW amber_hours=24 (non-OOS-NEW open). For simplicity:
        - OOS severity: created_at + 72h
        - Other open: created_at + 7 days
        - Closed/cleared rows: None (no longer accountable)
    """
    if (row.get("status") or "").lower() in ("cleared",):
        return None
    created = _parse_ts(row.get("reported_at") or row.get("created_at"))
    if not created:
        return None
    sev = (row.get("severity") or "").lower()
    if sev == "oos":
        return created + timedelta(hours=72)
    return created + timedelta(days=7)


def _due_at_for_incident(row: Dict[str, Any]) -> Optional[datetime]:
    """Incident SLA per SAF-CRITICAL-UNRESOLVED red_hours=48 (critical)
    and SAF-OSHA-OPEN red_hours=24.
    """
    created = _parse_ts(row.get("created_at"))
    if not created:
        return None
    if str(row.get("osha_recordable") or "").strip().lower() == "yes":
        return created + timedelta(hours=24)
    sev = (row.get("severity") or "").lower()
    if sev in ("critical", "high", "serious"):
        return created + timedelta(hours=48)
    return None


# ────────────────────────────────────────────────────────────────────
# Status resolution
# ────────────────────────────────────────────────────────────────────
def _status_for_task(row: Dict[str, Any]) -> str:
    native = row.get("status") or "Open"
    return _TASK_STATUS_MAP.get(native, "open")


def _status_for_ca(row: Dict[str, Any]) -> str:
    native = row.get("status") or "Open"
    return _CA_STATUS_MAP.get(native, "open")


def _status_for_po(row: Dict[str, Any]) -> str:
    native = row.get("status") or "Submitted"
    return _PO_STATUS_MAP.get(native, "open")


def _status_for_fleet_defect(row: Dict[str, Any]) -> str:
    native = (row.get("status") or "open").lower()
    return _FLEET_STATUS_MAP.get(native, "open")


async def _status_for_incident(db: Any, row: Dict[str, Any]) -> str:
    """Per Lifecycle §4.5 — derived from corrected_on_site + linked CA."""
    if str(row.get("corrected_on_site") or "").strip().lower() == "yes":
        return "resolved"
    inc_id = row.get("id")
    if await _incident_is_resolved_via_ca(db, inc_id):
        return "resolved"
    if await _incident_has_open_ca(db, inc_id):
        return "in_progress"
    return "open"


# ────────────────────────────────────────────────────────────────────
# Base projection builder
# ────────────────────────────────────────────────────────────────────
def _base_projection(*, source_module: str, source_record_id: str,
                     accountability_id: str, title: str,
                     owner: Dict[str, Any],
                     priority: str,
                     status: str,
                     created_at: Any, due_at: Optional[datetime],
                     last_activity_at: Any,
                     last_activity_kind: str,
                     resolved_at: Optional[datetime] = None,
                     resolved_by: Optional[Dict[str, Any]] = None,
                     resolution_notes: Optional[str] = None,
                     timeline_events: Optional[List[Dict[str, Any]]] = None,
                     ) -> Dict[str, Any]:
    """Build the 24-field canonical projection · Architecture §3.1."""
    return {
        "accountability_id": accountability_id,
        "source_module": source_module,
        "source_record_id": source_record_id,
        "title": (title or "")[:200],
        "owner_role": owner["owner_role"],
        "owner_user_id": owner["owner_user_id"],
        "owner_employee_id": owner["owner_employee_id"],
        "owner_display_name": owner["owner_display_name"],
        "assigned_at": _iso(_parse_ts(created_at)),
        "assigned_by": _empty_actor(),  # Audit A-04/A-05: not consistently captured today
        "due_at": _iso(due_at),
        "status": status,
        "priority": _priority_or_default(priority),
        "first_viewed_at": None,            # Timeline §3 viewed event reserved
        "first_viewed_by": None,
        "last_activity_at": _iso(_parse_ts(last_activity_at)),
        "last_activity_kind": last_activity_kind,
        "escalation_level": 0,              # RESERVED · Pillar 1B
        "resolved_at": _iso(resolved_at),
        "resolved_by": resolved_by,
        "resolution_notes": resolution_notes,
        "overdue": _is_overdue(status, due_at),
        "timeline_events": timeline_events or [],
    }


# ────────────────────────────────────────────────────────────────────
# Public per-source projection functions
# ────────────────────────────────────────────────────────────────────
def project_task(row: Dict[str, Any]) -> Dict[str, Any]:
    """Source: db.tasks · Phase 1A-2 source #1."""
    status = _status_for_task(row)
    timeline = _translate_task_audit(row.get("audit") or [])
    last_activity = (timeline[-1]["at"] if timeline else row.get("updated_at")
                     or row.get("created_at"))
    last_kind = timeline[-1]["event_kind"] if timeline else "created"

    resolved_at = None
    resolution_notes = None
    if status in ("resolved", "closed") and row.get("closed_at"):
        resolved_at = _parse_ts(row.get("closed_at"))
        resolution_notes = row.get("completion_notes") or "(no resolution notes)"

    return _base_projection(
        source_module="tasks",
        source_record_id=row.get("id") or "",
        accountability_id=row.get("id") or "",
        title=row.get("title") or "Task",
        owner=_owner_from_task(row),
        priority=row.get("priority") or "Medium",
        status=status,
        created_at=row.get("created_at"),
        due_at=_due_at_for_task(row),
        last_activity_at=last_activity,
        last_activity_kind=last_kind,
        resolved_at=resolved_at,
        resolved_by=None,
        resolution_notes=resolution_notes,
        timeline_events=timeline,
    )


def project_corrective_action(row: Dict[str, Any]) -> Dict[str, Any]:
    """Source: db.corrective_actions · Phase 1A-2 source #2."""
    status = _status_for_ca(row)
    timeline = _translate_ca_status_history(row.get("status_history") or [])
    last_activity = (timeline[-1]["at"] if timeline else row.get("updated_at")
                     or row.get("created_at"))
    last_kind = timeline[-1]["event_kind"] if timeline else "created"

    resolved_at = None
    resolved_by = None
    if status in ("resolved", "closed"):
        resolved_at = _parse_ts(row.get("verified_at") or row.get("completed_at"))
        verifier = row.get("verified_by_name") or row.get("closed_by_name")
        if verifier:
            resolved_by = _actor("safety", verifier)

    return _base_projection(
        source_module="safety.corrective_actions",
        source_record_id=row.get("id") or "",
        accountability_id=_accountability_id("safety.corrective_actions",
                                              row.get("id") or ""),
        title=row.get("title") or "Corrective Action",
        owner=_owner_from_ca(row),
        priority=row.get("priority") or "Medium",
        status=status,
        created_at=row.get("created_at"),
        due_at=_due_at_for_ca(row),
        last_activity_at=last_activity,
        last_activity_kind=last_kind,
        resolved_at=resolved_at,
        resolved_by=resolved_by,
        resolution_notes=row.get("completion_notes") or None,
        timeline_events=timeline,
    )


def project_po_request(row: Dict[str, Any]) -> Dict[str, Any]:
    """Source: db.po_requests · Phase 1A-2 source #3."""
    status = _status_for_po(row)
    timeline = _translate_po_audit(row.get("audit") or [])
    last_activity = (timeline[-1]["at"] if timeline else row.get("updated_at")
                     or row.get("created_at"))
    last_kind = timeline[-1]["event_kind"] if timeline else "created"

    resolved_at = None
    resolved_by = None
    resolution_notes = None
    if status in ("resolved", "closed"):
        # Last `approved` or `closed` event in audit
        for ev in reversed(timeline):
            if ev["event_kind"] in ("resolved", "closed"):
                resolved_at = _parse_ts(ev["at"])
                resolved_by = ev["actor"]
                resolution_notes = ev.get("notes")
                break

    title = f"PO {row.get('doc_id') or (row.get('id') or '')[:8]} · {row.get('vendor') or '—'}"

    return _base_projection(
        source_module="po.requests",
        source_record_id=row.get("id") or "",
        accountability_id=_accountability_id("po.requests", row.get("id") or ""),
        title=title,
        owner=_owner_from_po(row),
        priority=row.get("urgency") or row.get("priority") or "Medium",
        status=status,
        created_at=row.get("created_at"),
        due_at=_due_at_for_po(row),
        last_activity_at=last_activity,
        last_activity_kind=last_kind,
        resolved_at=resolved_at,
        resolved_by=resolved_by,
        resolution_notes=resolution_notes,
        timeline_events=timeline,
    )


def project_fleet_defect(row: Dict[str, Any]) -> Dict[str, Any]:
    """Source: db.fleet_defects · Phase 1A-2 source #4."""
    status = _status_for_fleet_defect(row)
    timeline = _synthesize_fleet_defect_timeline(row)
    last_activity = (timeline[-1]["at"] if timeline else row.get("reported_at"))
    last_kind = timeline[-1]["event_kind"] if timeline else "created"

    resolved_at = None
    resolved_by = None
    resolution_notes = None
    if status == "closed" and row.get("cleared_at"):
        resolved_at = _parse_ts(row.get("cleared_at"))
        resolved_by = _actor("shop", row.get("cleared_by_name") or "Shop")
        resolution_notes = row.get("repair_notes") or "(cleared)"

    unit = row.get("truck_unit_number") or row.get("trailer_unit_number") or "?"
    title = f"Unit {unit} · {row.get('item_text') or row.get('defect_summary') or 'defect'}"

    return _base_projection(
        source_module="equipment.dvir",
        source_record_id=row.get("id") or "",
        accountability_id=_accountability_id("equipment.dvir", row.get("id") or ""),
        title=title,
        owner=_owner_from_fleet_defect(row),
        priority="Critical" if (row.get("severity") or "").lower() == "oos" else "Medium",
        status=status,
        created_at=row.get("reported_at") or row.get("created_at"),
        due_at=_due_at_for_fleet_defect(row),
        last_activity_at=last_activity,
        last_activity_kind=last_kind,
        resolved_at=resolved_at,
        resolved_by=resolved_by,
        resolution_notes=resolution_notes,
        timeline_events=timeline,
    )


async def project_incident(db: Any, row: Dict[str, Any]) -> Dict[str, Any]:
    """Source: db.incidents · Phase 1A-2 source #5.

    Async because the status derivation queries db.corrective_actions
    (Lifecycle §4.5).
    """
    status = await _status_for_incident(db, row)
    timeline = _synthesize_incident_timeline(row)
    last_activity = (timeline[-1]["at"] if timeline
                     else row.get("updated_at") or row.get("created_at"))
    last_kind = timeline[-1]["event_kind"] if timeline else "created"

    resolved_at = None
    resolved_by = None
    resolution_notes = None
    if status == "resolved":
        for ev in reversed(timeline):
            if ev["event_kind"] == "resolved":
                resolved_at = _parse_ts(ev["at"])
                resolved_by = ev["actor"]
                resolution_notes = ev.get("notes")
                break

    title = (f"Incident {row.get('doc_id') or (row.get('id') or '')[:8]} · "
             f"{(row.get('severity') or 'Unspecified').title()}")

    priority_map = {"critical": "Critical", "high": "High",
                    "serious": "High", "moderate": "Medium",
                    "low": "Low"}
    priority = priority_map.get((row.get("severity") or "").lower(), "Medium")

    return _base_projection(
        source_module="safety.incidents",
        source_record_id=row.get("id") or "",
        accountability_id=_accountability_id("safety.incidents",
                                              row.get("id") or ""),
        title=title,
        owner=_owner_from_incident(row),
        priority=priority,
        status=status,
        created_at=row.get("created_at"),
        due_at=_due_at_for_incident(row),
        last_activity_at=last_activity,
        last_activity_kind=last_kind,
        resolved_at=resolved_at,
        resolved_by=resolved_by,
        resolution_notes=resolution_notes,
        timeline_events=timeline,
    )


def project_virtual_signal(*, signal_kind: str, payload: Dict[str, Any]
                            ) -> Dict[str, Any]:
    """Source: virtual.<signal_kind> · Phase 1A-2 source #6.

    Used by Command Center rules that emit signals which are NOT backed
    by a per-row collection (e.g. JOBS-DR-MISSING, JOBS-ISSUE-NO-PATH
    aggregate, EQP-BACKLOG count).

    `payload` mirrors the Command Center's item dict shape so the
    projection function is fed exactly what the dashboard already
    surfaces.
    """
    role = payload.get("owner_role") or "operations_leadership"
    name = payload.get("owner") or "Operations"

    title = payload.get("what_wrong") or f"Virtual signal · {signal_kind}"
    src_id = payload.get("source_record_id") or signal_kind

    # Virtual signals are always `open` while they surface; if they
    # disappear from the snapshot they implicitly transition to `closed`
    # (the absence becomes the closure). Lifecycle §4.6.
    status = "open"

    return _base_projection(
        source_module=f"virtual.{signal_kind}",
        source_record_id=src_id,
        accountability_id=_accountability_id(f"virtual.{signal_kind}", src_id),
        title=title,
        owner={
            "owner_role": role,
            "owner_user_id": payload.get("owner_user_id"),
            "owner_employee_id": payload.get("owner_employee_id"),
            "owner_display_name": name,
        },
        priority=payload.get("priority") or "Medium",
        status=status,
        created_at=payload.get("created_at"),
        due_at=_parse_ts(payload.get("due_at")),
        last_activity_at=payload.get("created_at"),
        last_activity_kind="created",
        timeline_events=[],
    )


# ────────────────────────────────────────────────────────────────────
# Dispatch
# ────────────────────────────────────────────────────────────────────
async def project(db: Any, source_module: str,
                  row_or_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Single entry point. Returns the canonical 24-field projection.

    Async because incident projection requires a `db.corrective_actions`
    lookup; all other sources delegate to sync helpers.
    """
    sm = (source_module or "").strip()
    if sm == "tasks":
        return project_task(row_or_payload)
    if sm == "safety.corrective_actions":
        return project_corrective_action(row_or_payload)
    if sm == "po.requests":
        return project_po_request(row_or_payload)
    if sm == "equipment.dvir":
        return project_fleet_defect(row_or_payload)
    if sm == "safety.incidents":
        return await project_incident(db, row_or_payload)
    if sm.startswith("virtual."):
        signal_kind = sm.split(".", 1)[1] or "unknown"
        return project_virtual_signal(signal_kind=signal_kind,
                                       payload=row_or_payload)
    raise ValueError(f"unsupported source_module: {sm!r}")


__all__ = [
    "CANONICAL_STATUSES",
    "CANONICAL_EVENT_KINDS",
    "ALLOWED_PRIORITIES",
    "project",
    "project_task",
    "project_corrective_action",
    "project_po_request",
    "project_fleet_defect",
    "project_incident",
    "project_virtual_signal",
]
