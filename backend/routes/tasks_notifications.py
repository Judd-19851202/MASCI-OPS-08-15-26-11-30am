"""
routes/tasks_notifications.py — Iter150 (Phase 2.5) · Phase A.

UNIFIED TASK / ACTION ASSIGNMENT ENGINE + NOTIFICATION CENTER.

Shared platform infrastructure used by every other module. Designed to
be modular, scalable, role-aware, permission-safe, fast, and auditable.
Intentionally lightweight — operational accountability, NOT ERP bloat.

Two collections, no duplicates:

  db.tasks            — operational task / action items
  db.notifications    — central notification feed

Both are sized via TTL on `closed_at`/`expires_at` so storage stays
predictable.

Public services exposed to other backend modules:

  from routes.tasks_notifications import task_service, notification_service

  await task_service.create(db, {
      "title": "Close CA-2025-0042",
      "source_module": "safety.corrective_actions",
      "source_record_id": "ca_..._id",
      "linked_employee_id": "emp_id_or_None",
      "linked_equipment_id": None,
      "linked_project_number": None,
      "assignee_role": "safety",
      "due_at": <datetime>,
      "priority": "High",
      "created_by": {"role": "safety", "name": "..."},
  })

  await notification_service.fanout(db, {
      "type": "task.assigned",
      "title": "...",
      "message": "...",
      "severity": "Info",
      "recipient_role": "safety",
      "linked_task_id": <task_id>,
      ...
  })

API endpoints (any portal token):

  GET    /api/tasks                          — list with filters
  GET    /api/tasks/{id}                     — read one
  POST   /api/tasks                          — create
  PATCH  /api/tasks/{id}                     — update status / assignee / notes
  POST   /api/tasks/{id}/comment             — append comment
  GET    /api/tasks/summary                  — counts by status/priority
  GET    /api/notifications                  — current user's bell feed
  POST   /api/notifications/{id}/read        — mark read
  POST   /api/notifications/read-all         — mark all read
  POST   /api/notifications/{id}/acknowledge — acknowledge critical
  GET    /api/notifications/unread-count     — header bell badge
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# TRACK 15.28C — Notification System Canonicalization Remediation
# ──────────────────────────────────────────────────────────────────
# event_id  — uuid stamped on every notification, traceable to the
#             originating producer call.
# idempotency_key — sha256 over (type, linked_source_record_id,
#             linked_task_id, recipient_role, recipient_user_id,
#             linked_request_id, linked_equipment_id). PERMANENT
#             dedupe — same key collapses to one row, ever.
# pm_broadcast — opt-in flag set by producers that genuinely want
#             every PM in the company to see the event. Without it,
#             PMs only see notifications scoped to projects they are
#             actively assigned to via `db.project_team_assignments`.
#
# Operator decision (Track 15.28C):
#   PM scope source        = project_team_assignments only (active rows)
#   PM unscoped behaviour  = suppress unless `pm_broadcast=true`
#   Idempotency window     = permanent (one event → one row, EVER)
#   Migration mode         = in-place
#   Dormant routes         = deleted
# ──────────────────────────────────────────────────────────────────

def compute_idempotency_key(payload: Dict[str, Any]) -> str:
    """Deterministic SHA-256 over the dedupe discriminators. Same payload
    shape → same key → upsert collapses repeats to a single row."""
    parts = [
        str(payload.get("type") or ""),
        str(payload.get("linked_source_record_id") or ""),
        str(payload.get("linked_task_id") or ""),
        str(payload.get("recipient_role") or ""),
        str(payload.get("recipient_user_id") or ""),
        str(payload.get("linked_request_id") or ""),
        str(payload.get("linked_equipment_id") or ""),
        str(payload.get("linked_employee_id") or ""),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

# ──────────────────────────────────────────────────────────────────
# Closed enums — keeping these tight prevents schema rot.
# ──────────────────────────────────────────────────────────────────
ALLOWED_STATUS = {
    "Open", "In Progress", "Pending Review",
    "Completed", "Closed", "Cancelled", "Overdue",
}
ALLOWED_PRIORITY = {"Low", "Medium", "High", "Critical"}
ALLOWED_SEVERITY = {"Info", "Warning", "Critical"}

# Source-module list — append-only; documents which workflow created
# the task. Used for grouping in views.
ALLOWED_SOURCE_MODULES = {
    "safety.corrective_actions",
    "safety.incidents",
    "safety.audits",
    "safety.fire_extinguishers",
    "safety.training",
    "inspections.field",
    "inspections.qaqc",
    "equipment.preop",
    "equipment.maintainx",      # future
    "equipment.motive",         # future
    "po.requests",              # future iter153
    "po.receipts",              # future iter153
    "documents.expiration",     # future iter151
    "hr.employee_lifecycle",    # future iter152
    "hr.offboarding",           # future iter152
    "admin.manual",
}

# Recipient role keys — same list used by Require* guards. "all" is a
# valid value for system-health broadcasts ("admin" only) when explicit
# role is unknown.
#
# Track 14.0-NOTIFY-LOCK widening (2026-06-14):
#   • asset_admin — dedicated routing for asset-administration alerts
#     (document expirations, missing docs, classification review). Asset
#     Admin authenticates via the Shop portal token AND admin token, so
#     widening here unlocks targeted producer fan-out without breaking
#     the existing Shop slice.
#   • superintendent — operational routing for field-supervisor alerts.
#     76 historical superintendent rows were admin-only; new producers
#     may now target the role directly. Superintendent users typically
#     authenticate via PM or Field Leadership tokens.
ALLOWED_ROLES = {
    "admin", "safety", "hr", "pm", "shop", "dispatch", "leadership",
    "asset_admin", "superintendent",
}


# ──────────────────────────────────────────────────────────────────
# Pydantic — payloads
# ──────────────────────────────────────────────────────────────────
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    source_module: str = Field(..., max_length=64)
    source_record_id: Optional[str] = Field(default=None, max_length=64)
    linked_employee_id: Optional[str] = Field(default=None, max_length=64)
    linked_equipment_id: Optional[str] = Field(default=None, max_length=64)
    linked_project_number: Optional[str] = Field(default=None, max_length=64)
    linked_po_id: Optional[str] = Field(default=None, max_length=64)
    assignee_role: Optional[str] = Field(default=None, max_length=24)
    assignee_user_id: Optional[str] = Field(default=None, max_length=64)
    assignee_employee_id: Optional[str] = Field(default=None, max_length=64)
    due_at: Optional[datetime] = None
    priority: str = Field(default="Medium")


class TaskPatch(BaseModel):
    status: Optional[str] = None
    assignee_role: Optional[str] = None
    assignee_user_id: Optional[str] = None
    assignee_employee_id: Optional[str] = None
    priority: Optional[str] = None
    due_at: Optional[datetime] = None
    completion_notes: Optional[str] = Field(default=None, max_length=4000)


class TaskComment(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


# ──────────────────────────────────────────────────────────────────
# Internal services — callable from anywhere in the backend
# ──────────────────────────────────────────────────────────────────
class _TaskService:
    """Backend-internal task service. Other modules import and call:

        from routes.tasks_notifications import task_service
        task_id = await task_service.create(db, {...})
    """

    async def create(self, db, payload: Dict[str, Any]) -> str:
        """Insert a task. Always emits a `task.assigned` notification
        when an assignee_role is present. Returns the task id."""
        now = datetime.now(timezone.utc)
        task = {
            "id": payload.get("id") or str(uuid.uuid4()),
            "title": str(payload["title"])[:200],
            "description": (payload.get("description") or "")[:4000] or None,
            "source_module": payload.get("source_module", "admin.manual"),
            "source_record_id": payload.get("source_record_id"),
            "linked_employee_id": payload.get("linked_employee_id"),
            "linked_equipment_id": payload.get("linked_equipment_id"),
            "linked_project_number": payload.get("linked_project_number"),
            "linked_po_id": payload.get("linked_po_id"),
            "assignee_role": payload.get("assignee_role"),
            "assignee_user_id": payload.get("assignee_user_id"),
            "assignee_employee_id": payload.get("assignee_employee_id"),
            "priority": payload.get("priority", "Medium")
                if payload.get("priority") in ALLOWED_PRIORITY else "Medium",
            "status": "Open",
            "due_at": payload.get("due_at") or payload.get("due_date"),
            "created_at": now,
            "updated_at": now,
            "created_by": payload.get("created_by") or {"role": "system"},
            "comments": [],
            "audit": [{
                "at": now,
                "by": payload.get("created_by") or {"role": "system"},
                "action": "created",
            }],
            "closed_at": None,
            "completion_notes": None,
            # TRACK 15.49 · optional pass-through for aftercare task
            # classification. Lets PDF + enrichment surface "24h
            # welfare check-in" vs "72h witness follow-up" vs "7d
            # investigator review" without parsing the title string.
            "task_key": payload.get("task_key") or None,
        }
        await db.tasks.insert_one(task)

        # Fire-and-forget notification fanout to the assignee role.
        if task["assignee_role"]:
            try:
                await notification_service.fanout(db, {
                    "type": "task.assigned",
                    "title": f"New task: {task['title'][:80]}",
                    "message": (task.get("description") or "")[:200],
                    "severity": "Info" if task["priority"] in ("Low", "Medium") else "Warning",
                    "recipient_role": task["assignee_role"],
                    # Track 15.1 (2026-06-16) — when the task is bound to a
                    # specific user via assignee_user_id, propagate that
                    # through as recipient_user_id so the notification is
                    # person-targeted (hidden from the role broadcast) and
                    # other users in the same role don't see noise.
                    "recipient_user_id": task.get("assignee_user_id"),
                    "linked_task_id": task["id"],
                    "linked_source_module": task["source_module"],
                    "linked_source_record_id": task["source_record_id"],
                    "linked_employee_id": task.get("linked_employee_id"),
                    "linked_project_number": task.get("linked_project_number"),
                })
            except Exception as e:  # pragma: no cover
                logger.warning("task notification fanout failed: %s", e)

        return task["id"]

    async def update(self, db, task_id: str, patch: Dict[str, Any],
                     actor: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = await db.tasks.find_one({"id": task_id}, {"_id": 0})
        if not existing:
            return None
        now = datetime.now(timezone.utc)
        update: Dict[str, Any] = {"updated_at": now}
        audit_changes: Dict[str, Any] = {}
        for k, v in patch.items():
            if v is None:
                continue
            if k == "status" and v not in ALLOWED_STATUS:
                continue
            if k == "priority" and v not in ALLOWED_PRIORITY:
                continue
            if existing.get(k) != v:
                update[k] = v
                audit_changes[k] = {"from": existing.get(k), "to": v}

        if not audit_changes:
            return existing

        if update.get("status") in ("Completed", "Closed", "Cancelled"):
            update["closed_at"] = now

        await db.tasks.update_one(
            {"id": task_id},
            {
                "$set": update,
                "$push": {"audit": {
                    "at": now,
                    "by": actor,
                    "action": "updated",
                    "changes": audit_changes,
                }},
            },
        )
        # Notify on completion
        if update.get("status") in ("Completed", "Closed") and existing.get("assignee_role"):
            try:
                await notification_service.fanout(db, {
                    "type": "task.closed",
                    "title": f"Task closed: {existing['title'][:80]}",
                    "message": f"Closed by {actor.get('name') or actor.get('role') or 'system'}",
                    "severity": "Info",
                    "recipient_role": existing["assignee_role"],
                    "linked_task_id": task_id,
                })
            except Exception as e:  # pragma: no cover
                logger.warning("task closed-notification failed: %s", e)

        return await db.tasks.find_one({"id": task_id}, {"_id": 0})

    async def append_comment(self, db, task_id: str, body: str,
                              actor: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = await db.tasks.find_one({"id": task_id}, {"_id": 0})
        if not existing:
            return None
        comment = {"at": datetime.now(timezone.utc), "by": actor,
                   "body": body[:2000]}
        await db.tasks.update_one(
            {"id": task_id},
            {
                "$push": {
                    "comments": comment,
                    "audit": {
                        "at": comment["at"], "by": actor, "action": "commented",
                    },
                },
                "$set": {"updated_at": comment["at"]},
            },
        )
        return await db.tasks.find_one({"id": task_id}, {"_id": 0})


class _NotificationService:
    """Backend-internal notification service. Fan-outs to a role go to
    `recipient_role` only — individual user delivery rules are owned by
    the frontend (filter by current actor) so we don't pre-materialize
    per-user rows. This keeps storage and query cost flat."""

    async def fanout(self, db, payload: Dict[str, Any]) -> str:
        now = datetime.now(timezone.utc)
        sev = payload.get("severity", "Info")
        if sev not in ALLOWED_SEVERITY:
            sev = "Info"
        # TRACK 15.28C — resolve recipient first so the idempotency
        # key reflects the materialized recipient_user_id.
        resolved_recipient_user_id = payload.get("recipient_user_id") or (
            await _resolve_recipient_user_id(db, payload)
        )
        eff_payload = dict(payload)
        eff_payload["recipient_user_id"] = resolved_recipient_user_id
        eff_payload.setdefault("recipient_role",
                               payload.get("recipient_role") or "admin")
        idem_key = compute_idempotency_key(eff_payload)
        # TRACK 15.28C — permanent dedupe via idempotency_key.
        # If a row with the same key exists, return its id without
        # creating a duplicate. One event → one row, EVER.
        existing = await db.notifications.find_one(
            {"idempotency_key": idem_key},
            {"_id": 0, "id": 1},
        )
        if existing and existing.get("id"):
            return existing["id"]
        notif = {
            "id": str(uuid.uuid4()),
            # TRACK 15.28C — every notification traceable to its
            # originating producer call. Producers may pass their
            # own event_id (preferred); otherwise we mint one.
            "event_id": str(payload.get("event_id") or uuid.uuid4()),
            "idempotency_key": idem_key,
            "type": str(payload.get("type", "system"))[:64],
            "title": str(payload.get("title", ""))[:200],
            "message": (payload.get("message") or "")[:2000] or None,
            "severity": sev,
            "recipient_role": eff_payload["recipient_role"],
            "recipient_user_id": resolved_recipient_user_id,
            # TRACK 15.28C — opt-in flag. PMs only see notifications
            # for projects they are assigned to in
            # `project_team_assignments`. Set `pm_broadcast=True` to
            # surface a notification to all PMs regardless of project.
            "pm_broadcast": bool(payload.get("pm_broadcast", False)),
            "linked_task_id": payload.get("linked_task_id"),
            "linked_source_module": payload.get("linked_source_module"),
            "linked_source_record_id": payload.get("linked_source_record_id"),
            "linked_employee_id": payload.get("linked_employee_id"),
            "linked_equipment_id": payload.get("linked_equipment_id"),
            "linked_project_number": payload.get("linked_project_number"),
            "linked_request_id": payload.get("linked_request_id"),
            "link_url": payload.get("link_url") or _resolve_link_url(eff_payload),
            "created_at": now,
            # Permanent dedupe ⇒ expiry is opt-in. Set when caller
            # provides a TTL or when severity is Info (90d).
            "expires_at": payload.get("expires_at") or (
                now + timedelta(days=90)
            ),
            "read_by": [],
            "acknowledged_by": None,
            "acknowledged_at": None,
            "delivery": {
                "internal": True,
                "email": payload.get("email_enabled", False),
                "push": payload.get("push_enabled", False),
                "sms": False,
            },
        }
        try:
            await db.notifications.insert_one(notif)
        except Exception as exc:  # noqa: BLE001
            # Race: another writer raced us with the same idem_key.
            # Re-read and return the surviving id.
            existing2 = await db.notifications.find_one(
                {"idempotency_key": idem_key},
                {"_id": 0, "id": 1},
            )
            if existing2 and existing2.get("id"):
                return existing2["id"]
            raise exc
        return notif["id"]


task_service = _TaskService()
notification_service = _NotificationService()


# ──────────────────────────────────────────────────────────────────
# Track 14.0-NOTIFY-LOCK-COMPLETION (2026-06-14)
# Deterministic frontend deep-link resolver. Producers already pass
# `linked_source_module` + `linked_source_record_id`, so we centralize
# the route mapping here once and every producer benefits without a
# call-site edit. Returns None when no safe deep route exists; the
# bell drawer falls back to `/tasks?id=<linked_task_id>` (existing
# behavior) which then falls back to the generic `/tasks` queue.
#
# Rules: existing routes only · no invented routes · no admin-console
# routing for non-admin recipients · no RTS-authority grant.
# ──────────────────────────────────────────────────────────────────
_LINK_BY_MODULE: Dict[str, str] = {
    "safety.incidents":            "/admin/incidents/{id}",
    "daily_reports":               "/admin/daily/{id}",
    "qaqc.inspections":            "/qaqc/{id}",
    "field_leadership.records":    "/leadership/records/{id}",
    "safety.meeting":              "/meetings/{id}",
    "po.requests":                 "/po-requests/{id}",
    "po.receipts":                 "/po-requests/{id}",
    "equipment.preop":             "/admin/equipment-issues/{id}",
    "fleet.dvir":                  "/admin/equipment-issues/{id}",
    "fleet.defect.assignment":     "/admin/equipment-issues/{id}",
    "fuel_lube_visit.issue":       "/admin/equipment-issues/{id}",
    "asset.transfer":              "/asset-transfers/{id}",
    "documents.expiration":        "/shop/asset-care",
    "hr.payroll_variance":         "/hr/payroll-variance",
    "safety.fire_extinguishers":   "/safety/forms",
    "safety.jha":                  "/jha",
    "safety.form.issuance":        "/safety/forms",
    "safety.form.return":          "/safety/forms",
    "safety.form.training":        "/safety/forms",
    "safety.inspections":          "/safety-portal",
    "trench_safety:reinspection_requested": "/trench-safety",
    # trench_safety.* type-keyed fallbacks (see resolver below)
}

_LINK_BY_TYPE_PREFIX: Dict[str, str] = {
    "trench_safety.": "/trench-safety/assets/{id}",
    "asset_transfer.": "/asset-transfers/{id}",
    "preop.":          "/admin/equipment-issues/{id}",
    "dvir.":           "/admin/equipment-issues/{id}",
    "qaqc.":           "/qaqc/{id}",
    "incident.":       "/admin/incidents/{id}",
    "daily_report.":   "/admin/daily/{id}",
    "po.":             "/po-requests/{id}",
    "fl.":             "/leadership/records/{id}",
    "meeting.":        "/meetings/{id}",
}


async def _resolve_recipient_user_id(db, payload: Dict[str, Any]) -> Optional[str]:
    """Track 14.0-NOTIFY-OWNERSHIP-LOCK D2 — person-level ownership
    resolver. Returns a specific user_id when ownership data exists on
    the source record, applying the 8-step resolution chain from the
    D1 Ownership Matrix:

      1. assigned_user_id    (explicit single-user assignment)
      2. submitted_by        (record author)
      3. assigned_superintendent_id
      4. assigned_foreman_id
      5. project_owner_user_id  (PM-of-record on linked project)
      6. workflow_reviewer_id
      7. (department role bucket — caller's recipient_role)
      8. (admin fallback     — caller default)

    Returns None when no specific human is resolvable; the caller's
    recipient_role then remains the routing key. Never overrides an
    explicit recipient_user_id already in the payload."""
    if payload.get("recipient_user_id"):
        return payload["recipient_user_id"]
    # Source-record fields the producer may have passed through.
    owner_keys = (
        "assigned_user_id", "submitted_by",
        "assigned_superintendent_id", "assigned_foreman_id",
        "project_owner_user_id", "workflow_reviewer_id",
    )
    for k in owner_keys:
        v = payload.get(k)
        if v:
            return str(v)
    # Project-derived owner: if linked_project_number is set, look up
    # the PM-of-record from the projects collection. Read-only; one
    # bounded query; cached owners arrive in payload to skip this.
    pn = payload.get("linked_project_number")
    if pn:
        try:
            proj = await db.projects.find_one(
                {"project_number": pn},
                {"_id": 0, "pm_user_id": 1, "superintendent_user_id": 1},
            )
            if proj:
                return proj.get("pm_user_id") or proj.get("superintendent_user_id")
        except Exception:
            return None
    return None


def _resolve_link_url(payload: Dict[str, Any]) -> Optional[str]:
    """Best-effort route mapper. Prefers source-module lookup, falls
    back to type prefix. Returns None if no safe deep route is known
    (drawer then falls back to `linked_task_id` → /tasks).

    SAFETY-CONTEXT-CERT (2026-06-15) — when `recipient_role == "safety"`,
    rewrite admin-routed templates to their Safety-portal equivalents so
    Safety users open notifications in Safety chrome (no
    "Back to Admin Overview" leak).
    """
    record_id = payload.get("linked_source_record_id") or payload.get("linked_equipment_id")
    if not record_id:
        return None
    module = payload.get("linked_source_module") or ""
    template = _LINK_BY_MODULE.get(module)
    if not template:
        ntype = (payload.get("type") or "")
        for prefix, t in _LINK_BY_TYPE_PREFIX.items():
            if ntype.startswith(prefix):
                template = t
                break
    if not template:
        return None
    # Portal-context rewrites for safety recipients.
    if (payload.get("recipient_role") or "").lower() == "safety":
        if template.startswith("/admin/incidents/"):
            template = template.replace("/admin/incidents/", "/safety-portal/incidents/")
        elif template == "/meetings/{id}":
            template = "/safety-portal/meetings/{id}"
    try:
        return template.format(id=str(record_id))
    except (KeyError, IndexError, ValueError):
        return None


# ──────────────────────────────────────────────────────────────────
# Index bootstrap
# ──────────────────────────────────────────────────────────────────
async def ensure_tasks_notifications_indexes(db) -> None:
    try:
        await db.tasks.create_index("id", unique=True)
        await db.tasks.create_index([("status", 1), ("priority", 1)])
        await db.tasks.create_index("assignee_role")
        await db.tasks.create_index("linked_employee_id")
        await db.tasks.create_index("linked_equipment_id")
        await db.tasks.create_index("linked_project_number")
        await db.tasks.create_index("source_module")
        await db.tasks.create_index("created_at")
        await db.tasks.create_index("due_at")
        # TTL on closed tasks — 365 days post-close
        await db.tasks.create_index("closed_at", expireAfterSeconds=60 * 60 * 24 * 365)

        await db.notifications.create_index("id", unique=True)
        await db.notifications.create_index([("recipient_role", 1), ("created_at", -1)])
        await db.notifications.create_index([("recipient_user_id", 1), ("created_at", -1)])
        # TRACK 15.28C — permanent dedupe index. Sparse so legacy
        # rows without an idempotency_key don't collide.
        await db.notifications.create_index(
            "idempotency_key", unique=True, sparse=True,
        )
        await db.notifications.create_index("event_id", sparse=True)
        # TRACK 15.28C — PM project-scope read index.
        await db.notifications.create_index(
            [("linked_project_number", 1), ("recipient_role", 1), ("created_at", -1)],
        )
        # TRACK 14.0-NOTIF-NEW-USER-SCOPE — supports eligibility filter
        # on the role-broadcast leg: {recipient_role, created_at>=cutoff,
        # no recipient_user_id}. The existing (recipient_role, created_at)
        # index already serves this query; this is just a documentation
        # marker — no additional index needed.
        await db.notifications.create_index("linked_task_id")
        await db.notifications.create_index("acknowledged_at")
        await db.notifications.create_index("expires_at", expireAfterSeconds=0)
    except Exception as e:  # pragma: no cover
        logger.warning("tasks/notifications index bootstrap failed: %s", e)


def actor_role(actor: Dict[str, Any]) -> str:
    """Public helper · returns the canonical role label for an actor
    dict produced by ``require_any_portal_token``. Module-level so
    tests can call it without spinning the router."""
    return actor.get("_actor") or actor.get("role") or "admin"


def actor_eligibility(actor: Dict[str, Any]) -> Optional[datetime]:
    """TRACK 14.0-NOTIF-NEW-USER-SCOPE — returns the actor's
    notification-eligibility cutoff as a timezone-aware UTC datetime,
    or ``None`` when no cutoff applies.

    Source of truth (priority order):
      1. ``actor["created_at"]`` from the per-portal user document
         (``hr_users.created_at``, ``safety_users.created_at``, …).
      2. ``None`` — admins and any portal actor without a recorded
         join date opt out of the filter (preserves backward compat).

    Direct-user notifications (``recipient_user_id == actor.id``)
    bypass this cutoff entirely — direct addressing always wins.
    """
    if actor_role(actor) == "admin":
        return None
    raw = actor.get("created_at")
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, str):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None
    return None


async def _pm_assigned_project_numbers(
    db, actor: Dict[str, Any],
) -> Set[str]:
    """TRACK 15.28C — returns the set of project_numbers the PM actor
    is actively assigned to in `db.project_team_assignments`. Used by
    the read-side scope filter so PMs no longer see role-broadcast
    notifications for projects they are not on.

    Match strategy: prefer `user_id`, fall back to lowercased email.
    Only `active=True` rows count.
    """
    user_id = actor.get("id") or actor.get("user_id")
    email = (actor.get("email") or "").strip().lower()
    or_clauses: List[Dict[str, Any]] = []
    if user_id:
        or_clauses.append({"user_id": user_id})
    if email:
        or_clauses.append({"email": email})
    if not or_clauses:
        return set()
    q: Dict[str, Any] = {"active": True, "$or": or_clauses}
    projects: Set[str] = set()
    try:
        async for row in db.project_team_assignments.find(
            q, {"_id": 0, "project_number": 1},
        ):
            pn = row.get("project_number")
            if pn:
                projects.add(pn)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[notif-pm-scope] lookup failed: %s", exc)
    return projects


async def build_notif_filter_async(
    db, actor: Dict[str, Any],
) -> Dict[str, Any]:
    """TRACK 15.28C — async read-side notification filter.

    Rules:
      • Admin → ``{}`` (no filter).
      • Person-level routing: ``recipient_user_id == actor.id`` is OR'd
        with the role clause; direct-addressed notifications bypass
        every other constraint (eligibility, project scope).
      • Asset Admin OR-scope: ``asset_admin`` is appended to the role
        list when ``actor.is_asset_admin == True``.
      • Eligibility cutoff: role-broadcast notifications are further
        constrained to ``created_at >= actor_eligibility(actor)``.
      • PM project scope (NEW): when ``actor.role == "pm"``, role-
        broadcast notifications are additionally constrained to:
            linked_project_number ∈ assigned_projects
              OR (linked_project_number IS NULL AND pm_broadcast=True)
        i.e. PMs see project-scoped notifications for their projects,
        plus explicit company-wide PM broadcasts only.
    """
    role = actor_role(actor)
    if role == "admin":
        return {}
    scope_roles = [role]
    if actor.get("is_asset_admin") is True:
        scope_roles.append("asset_admin")
    user_id = actor.get("id") or actor.get("user_id")
    role_clauses: List[Dict[str, Any]] = [
        {"recipient_role": {"$in": scope_roles}},
        {"$or": [
            {"recipient_user_id": None},
            {"recipient_user_id": {"$exists": False}},
        ]},
    ]
    eligibility = actor_eligibility(actor)
    if eligibility is not None:
        role_clauses.append({"created_at": {"$gte": eligibility}})
    if role == "pm":
        assigned = await _pm_assigned_project_numbers(db, actor)
        pm_scope_clauses: List[Dict[str, Any]] = []
        if assigned:
            pm_scope_clauses.append({"linked_project_number": {"$in": list(assigned)}})
        pm_scope_clauses.append({"$and": [
            {"$or": [
                {"linked_project_number": None},
                {"linked_project_number": {"$exists": False}},
            ]},
            {"pm_broadcast": True},
        ]})
        role_clauses.append({"$or": pm_scope_clauses})
    role_clause = {"$and": role_clauses}
    if user_id:
        return {"$or": [role_clause, {"recipient_user_id": user_id}]}
    return role_clause


def build_notif_filter(actor: Dict[str, Any]) -> Dict[str, Any]:
    """Public read-side notification filter (the same logic the router
    uses). Exposed at module scope so regression tests don't have to
    walk into the router closure.

    Rules (composed):
      • Admin → ``{}`` (no filter).
      • Person-level routing: ``recipient_user_id == actor.id`` is OR'd
        with the role clause; direct-addressed notifications bypass
        eligibility.
      • Asset Admin OR-scope: ``asset_admin`` is appended to the role
        list when ``actor.is_asset_admin == True``.
      • Eligibility cutoff (NEW): role-broadcast notifications are
        further constrained to ``created_at >= actor_eligibility(actor)``.
    """
    role = actor_role(actor)
    if role == "admin":
        return {}
    scope_roles = [role]
    if actor.get("is_asset_admin") is True:
        scope_roles.append("asset_admin")
    user_id = actor.get("id") or actor.get("user_id")
    role_clauses: List[Dict[str, Any]] = [
        {"recipient_role": {"$in": scope_roles}},
        {"$or": [
            {"recipient_user_id": None},
            {"recipient_user_id": {"$exists": False}},
        ]},
    ]
    eligibility = actor_eligibility(actor)
    if eligibility is not None:
        role_clauses.append({"created_at": {"$gte": eligibility}})
    role_clause = {"$and": role_clauses}
    if user_id:
        return {"$or": [role_clause, {"recipient_user_id": user_id}]}
    return role_clause


# ──────────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────────
def build_tasks_notifications_router(db, require_any_portal_token):
    router = APIRouter(tags=["tasks-notifications"])

    def _actor_role(actor: Dict[str, Any]) -> str:
        return actor_role(actor)

    def _scope_filter(actor: Dict[str, Any]) -> Dict[str, Any]:
        """Role-aware filter. Admin sees everything; portal users see
        tasks assigned to their role OR created by them OR linked to
        a record in their domain (kept lightweight for v1).

        Track 14.0-NOTIFY-OWNERSHIP-LOCK D3 — Asset Admin first-class:
        actors with the `is_asset_admin` flag (set by the auth
        middleware when the underlying user record carries
        `is_asset_admin=True`) additionally see the `asset_admin`
        scope. This is a strict OR-extension, never a downgrade — Shop
        Managers without the flag continue to see only their shop
        slice. No mechanic noise leaks to asset_admin because
        notifications targeted to asset_admin are filtered by
        recipient_role at write time."""
        role = _actor_role(actor)
        if role == "admin":
            return {}
        extra_roles: List[str] = []
        if actor.get("is_asset_admin") is True:
            extra_roles.append("asset_admin")
        scope_roles = [role] + extra_roles
        return {"$or": [
            {"assignee_role": {"$in": scope_roles}},
            {"created_by.role": role},
            {"assignee_role": {"$in": scope_roles + [None]}},
            # Notification-only doc shape uses `recipient_role`.
            {"recipient_role": {"$in": scope_roles}},
        ]}

    # ── Tasks ────────────────────────────────────────────────────────
    @router.get("/api/tasks")
    async def list_tasks(
        actor: Dict[str, Any] = Depends(require_any_portal_token),
        status: Optional[str] = Query(default=None),
        assignee_role: Optional[str] = Query(default=None),
        priority: Optional[str] = Query(default=None),
        source_module: Optional[str] = Query(default=None),
        linked_employee_id: Optional[str] = Query(default=None),
        linked_equipment_id: Optional[str] = Query(default=None),
        linked_project_number: Optional[str] = Query(default=None),
        q: Optional[str] = Query(default=None, max_length=80),
        limit: int = Query(default=100, ge=1, le=500),
    ) -> Dict[str, Any]:
        filt = _scope_filter(actor)
        and_clauses: List[Dict[str, Any]] = []
        if filt:
            and_clauses.append(filt)
        if status:
            and_clauses.append({"status": status})
        if assignee_role:
            and_clauses.append({"assignee_role": assignee_role})
        if priority:
            and_clauses.append({"priority": priority})
        if source_module:
            and_clauses.append({"source_module": source_module})
        if linked_employee_id:
            and_clauses.append({"linked_employee_id": linked_employee_id})
        if linked_equipment_id:
            and_clauses.append({"linked_equipment_id": linked_equipment_id})
        if linked_project_number:
            and_clauses.append({"linked_project_number": linked_project_number})
        if q:
            and_clauses.append({"title": {"$regex": q, "$options": "i"}})
        final = {"$and": and_clauses} if and_clauses else {}
        cur = db.tasks.find(final, {"_id": 0}).sort("created_at", -1).limit(limit)
        items = []
        async for d in cur:
            items.append(d)
        return {"items": items, "count": len(items)}

    @router.get("/api/tasks/summary")
    async def tasks_summary(
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        filt = _scope_filter(actor)
        now = datetime.now(timezone.utc)
        # Counts by status
        pipeline = [
            {"$match": filt} if filt else {"$match": {}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        by_status: Dict[str, int] = {}
        async for d in db.tasks.aggregate(pipeline):
            by_status[d["_id"] or "Open"] = d["count"]
        # Overdue = due_at < now and status open-ish
        overdue_filt = dict(filt) if filt else {}
        overdue_clauses = [
            {"due_at": {"$lt": now}},
            {"status": {"$in": ["Open", "In Progress", "Pending Review"]}},
        ]
        # combine
        if overdue_filt:
            overdue_filt = {"$and": [overdue_filt, *overdue_clauses]}
        else:
            overdue_filt = {"$and": overdue_clauses}
        overdue = await db.tasks.count_documents(overdue_filt)
        return {
            "by_status": by_status,
            "overdue": overdue,
            "open_total": sum(
                v for k, v in by_status.items()
                if k in ("Open", "In Progress", "Pending Review")
            ),
        }

    @router.get("/api/tasks/{task_id}")
    async def get_task(
        task_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        doc = await db.tasks.find_one({"id": task_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Task not found")
        return doc

    @router.post("/api/tasks")
    async def create_task(
        payload: TaskCreate,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        data = payload.model_dump()
        data["created_by"] = {
            "role": _actor_role(actor),
            "name": actor.get("name") or actor.get("email"),
            "user_id": actor.get("id"),
        }
        task_id = await task_service.create(db, data)
        doc = await db.tasks.find_one({"id": task_id}, {"_id": 0})
        return doc

    @router.patch("/api/tasks/{task_id}")
    async def patch_task(
        task_id: str,
        payload: TaskPatch,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        updated = await task_service.update(
            db, task_id, payload.model_dump(exclude_none=True),
            actor={"role": _actor_role(actor),
                   "name": actor.get("name") or actor.get("email")},
        )
        if not updated:
            raise HTTPException(404, "Task not found")
        return updated

    @router.post("/api/tasks/{task_id}/comment")
    async def comment_task(
        task_id: str,
        payload: TaskComment,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        updated = await task_service.append_comment(
            db, task_id, payload.body,
            actor={"role": _actor_role(actor),
                   "name": actor.get("name") or actor.get("email")},
        )
        if not updated:
            raise HTTPException(404, "Task not found")
        return updated

    def _actor_eligibility(actor: Dict[str, Any]) -> Optional[datetime]:
        """Inner shim → delegates to module-level :func:`actor_eligibility`.

        Kept for callers inside this factory that reference the local
        name; the real logic lives at module scope so it is testable
        without spinning up the router.
        """
        return actor_eligibility(actor)

    def _notif_filter(actor: Dict[str, Any]) -> Dict[str, Any]:
        """Inner shim → delegates to module-level :func:`build_notif_filter`.

        TRACK 14.0-NOTIF-NEW-USER-SCOPE made the logic module-level so
        regression tests can verify it without walking closures.
        """
        return build_notif_filter(actor)

    async def _notif_filter_async(actor: Dict[str, Any]) -> Dict[str, Any]:
        """TRACK 15.28C — async shim that includes PM project-scope.

        Used by the bell read endpoints so PMs only see notifications
        for projects they are actively assigned to.
        """
        return await build_notif_filter_async(db, actor)

    # ── Notifications ────────────────────────────────────────────────
    @router.get("/api/notifications")
    async def list_notifications(
        actor: Dict[str, Any] = Depends(require_any_portal_token),
        unread_only: bool = Query(default=False),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> Dict[str, Any]:
        role = _actor_role(actor)
        filt = await _notif_filter_async(actor)
        cur = db.notifications.find(filt, {"_id": 0}).sort("created_at", -1).limit(limit)
        items: List[Dict[str, Any]] = []
        async for d in cur:
            is_read = bool(d.get("read_by") and any(
                (r.get("role") == role or r.get("user_id") == actor.get("id"))
                for r in d.get("read_by", [])
            ))
            if unread_only and is_read:
                continue
            d["is_read"] = is_read
            items.append(d)
        return {"items": items, "count": len(items)}

    @router.get("/api/notifications/unread-count")
    async def unread_count(
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        role = _actor_role(actor)
        filt = await _notif_filter_async(actor)
        # Approximate: not-acknowledged & role-marker absent from read_by
        cnt = 0
        cur = db.notifications.find(
            {**filt, "acknowledged_at": None}, {"_id": 0, "read_by": 1, "id": 1}
        )
        async for d in cur:
            already = any(
                (r.get("role") == role or r.get("user_id") == actor.get("id"))
                for r in d.get("read_by", []) or []
            )
            if not already:
                cnt += 1
        return {"unread": cnt}

    @router.post("/api/notifications/{notif_id}/read")
    async def mark_read(
        notif_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        role = _actor_role(actor)
        marker = {
            "role": role,
            "user_id": actor.get("id"),
            "at": datetime.now(timezone.utc),
        }
        res = await db.notifications.update_one(
            {"id": notif_id, "read_by.role": {"$ne": role}},
            {"$push": {"read_by": marker}},
        )
        return {"ok": True, "matched": res.matched_count}

    @router.post("/api/notifications/read-all")
    async def mark_all_read(
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        role = _actor_role(actor)
        marker = {
            "role": role,
            "user_id": actor.get("id"),
            "at": datetime.now(timezone.utc),
        }
        # Use the same D2/D3-aware filter as the list endpoint so users
        # can only mark-read what they can actually see.
        filt: Dict[str, Any] = await _notif_filter_async(actor)
        if filt:
            filt = {"$and": [filt, {"read_by.role": {"$ne": role}}]}
        else:
            filt = {"read_by.role": {"$ne": role}}
        res = await db.notifications.update_many(
            filt, {"$push": {"read_by": marker}},
        )
        return {"ok": True, "marked": res.modified_count}

    @router.post("/api/notifications/{notif_id}/acknowledge")
    async def acknowledge(
        notif_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        role = _actor_role(actor)
        res = await db.notifications.update_one(
            {"id": notif_id},
            {"$set": {
                "acknowledged_at": datetime.now(timezone.utc),
                "acknowledged_by": {
                    "role": role,
                    "user_id": actor.get("id"),
                    "name": actor.get("name") or actor.get("email"),
                },
            }},
        )
        if res.matched_count == 0:
            raise HTTPException(404, "Notification not found")
        return {"ok": True}

    return router


__all__ = [
    "build_tasks_notifications_router",
    "ensure_tasks_notifications_indexes",
    "task_service",
    "notification_service",
    "ALLOWED_STATUS", "ALLOWED_PRIORITY", "ALLOWED_SEVERITY",
    "ALLOWED_SOURCE_MODULES", "ALLOWED_ROLES",
]
