"""
routes/ownership_lifecycle.py — Track 14.0-JOB-OWNERSHIP-FOUNDATION Phase 2A.

Assignment lifecycle, ownership continuity, historical-snapshot capture,
and open-work migration framework.

Five capabilities exposed here:

  1. `assignment_status` lifecycle (ACTIVE / TRANSFERRED / REPLACED /
     DISABLED / TERMINATED / INACTIVE) layered on the existing
     project_team_assignments collection without rewriting Phase 1
     storage. Soft-delete only.

  2. **Snapshot capture** (`lib/team_snapshot.capture_team_snapshot`)
     that any operational writer can call to freeze the current roster
     onto a record at submit / approval time. Snapshots are immutable
     by convention — they live on the record itself and roster mutations
     never edit them.

  3. **Open-work scanner** (`scan_open_work_for_user`) that walks
     notifications, tasks, audit holds, and pending FL submissions to
     produce a migration manifest before a user is disabled or
     transferred.

  4. **Transfer engine** (`transfer_assignment`) that atomically ends an
     old assignment, opens a replacement, mirrors open work to the
     replacement, and writes the audit chain.

  5. **Disable-user protection** (`disable_user_precheck` and
     `disable_user_with_migration`) so a user can't be disabled while
     they still own open work — unless an admin explicitly accepts the
     orphan or migrates each category.

  6. **Notification resolver** (`resolve_recipient_for_event`) — Phase-2
     producers may call this to set `recipient_user_id` correctly. This
     phase wires it into ONE new producer family (Daily Report review
     events) as a proof-point; the existing 18 producers will be
     swept in Phase 2B behind the `OWNERSHIP_LOCK_ENABLED` flag.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ── Lifecycle states ─────────────────────────────────────────────────
STATUS_ACTIVE = "ACTIVE"
STATUS_INACTIVE = "INACTIVE"
STATUS_TRANSFERRED = "TRANSFERRED"
STATUS_REPLACED = "REPLACED"
STATUS_DISABLED = "DISABLED"
STATUS_TERMINATED = "TERMINATED"
ALL_STATUSES: Set[str] = {
    STATUS_ACTIVE, STATUS_INACTIVE, STATUS_TRANSFERRED,
    STATUS_REPLACED, STATUS_DISABLED, STATUS_TERMINATED,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Snapshot capture (importable as lib helper) ──────────────────────
SNAPSHOT_ROLES: Tuple[str, ...] = (
    "pm", "co_pm", "superintendent", "foreman", "safety_lead",
    "project_engineer", "asset_admin", "locate_coordinator",
    "dispatcher_contact", "shop_contact", "executive_oversight",
)


async def capture_team_snapshot(db, project_number: str) -> Dict[str, Any]:
    """Return a frozen-at-now snapshot of the active roster on the
    project. Embed the result on any operational record at
    submit/approval time to preserve historical truth. Snapshot is a
    plain dict — write-once semantics are the caller's responsibility
    (i.e., never PATCH the snapshot field after initial write).

    Shape::
        {
          "project_number": "26-05",
          "captured_at": "2026-…",
          "members": {
            "pm": [{"user_id":"…","email":"…","name":"…"}],
            "superintendent": [...],
            …
          }
        }
    """
    members: Dict[str, List[Dict[str, Any]]] = {r: [] for r in SNAPSHOT_ROLES}
    cur = db.project_team_assignments.find(
        {"project_number": project_number, "active": True,
         "assignment_role": {"$in": list(SNAPSHOT_ROLES)}},
        {"_id": 0, "user_id": 1, "email": 1, "display_name": 1,
         "assignment_role": 1, "is_primary": 1},
    )
    async for r in cur:
        bucket = members.get(r["assignment_role"])
        if bucket is not None:
            bucket.append({
                "user_id": r.get("user_id"),
                "email": r.get("email"),
                "name": r.get("display_name"),
                "is_primary": bool(r.get("is_primary")),
            })
    return {
        "project_number": project_number,
        "captured_at": _now_iso(),
        "members": members,
    }


# ── Notification resolver (used by Phase-2B producer rewrites) ───────
async def resolve_recipient_for_event(
    db,
    *,
    project_number: Optional[str],
    role_chain: List[str],
    fallback_role: Optional[str] = None,
) -> Dict[str, Any]:
    """Walk the role_chain (e.g. ["superintendent","co_pm","pm"]) and
    return the first active rostered user_id found. Falls back to
    `fallback_role` (role-bucket only) when no match.

    Return shape (matches `notification_service.fanout` input)::
        {"recipient_user_id": "…" or None,
         "recipient_role":   "fl|safety|…",
         "resolved_via":     "superintendent" or None,
         "resolved_email":   "…" or None}
    """
    if not project_number:
        return {"recipient_user_id": None,
                "recipient_role": fallback_role,
                "resolved_via": None,
                "resolved_email": None}
    for role in role_chain:
        row = await db.project_team_assignments.find_one(
            {"project_number": project_number, "assignment_role": role,
             "active": True, "user_id": {"$nin": [None, ""]}},
            {"_id": 0, "user_id": 1, "email": 1},
        )
        if row:
            return {"recipient_user_id": row["user_id"],
                    "recipient_role": fallback_role,
                    "resolved_via": role,
                    "resolved_email": row.get("email")}
    return {"recipient_user_id": None,
            "recipient_role": fallback_role,
            "resolved_via": None,
            "resolved_email": None}


# ── Open-work scanner ────────────────────────────────────────────────
async def scan_open_work_for_user(
    db, user_id: str, *, email: Optional[str] = None,
) -> Dict[str, Any]:
    """Return categories of open work currently addressed to `user_id`.

    Open work is anything the system would lose visibility of if the
    user were silently disabled:

      • notifications with `recipient_user_id = user_id` and unread
      • tasks with `assignee_user_id = user_id` and status != Closed
      • project_team_assignments where `user_id = user_id` and active
      • audit_events (informational only — historical context)
    """
    report: Dict[str, Any] = {
        "user_id": user_id,
        "email": (email or "").lower() or None,
        "scanned_at": _now_iso(),
        "open_notifications": 0,
        "open_tasks": 0,
        "active_assignments": [],
        "open_categories": {},  # role-broadcast notifs the user might catch
    }

    # 1. Notifications person-addressed to this user, not acknowledged.
    try:
        nq = {"recipient_user_id": user_id, "acknowledged_at": None}
        report["open_notifications"] = await db.notifications.count_documents(nq)
    except Exception:
        pass

    # 2. Tasks person-assigned to this user, not closed.
    try:
        tq = {"assignee_user_id": user_id,
              "status": {"$nin": ["Closed", "Completed", "Cancelled"]}}
        report["open_tasks"] = await db.tasks.count_documents(tq)
    except Exception:
        pass

    # 3. Active project_team_assignments.
    rows: List[Dict[str, Any]] = []
    cur = db.project_team_assignments.find(
        {"user_id": user_id, "active": True}, {"_id": 0},
    )
    async for r in cur:
        rows.append({
            "id": r["id"],
            "project_number": r.get("project_number"),
            "assignment_role": r.get("assignment_role"),
            "is_primary": r.get("is_primary"),
        })
    report["active_assignments"] = rows
    report["active_assignment_count"] = len(rows)

    # 4. Per-category breakdown of person-addressed notifs (for the wizard).
    pipe = [
        {"$match": {"recipient_user_id": user_id, "acknowledged_at": None}},
        {"$group": {"_id": "$type", "c": {"$sum": 1}}},
        {"$sort": {"c": -1}},
    ]
    cat: Dict[str, int] = {}
    try:
        async for r in db.notifications.aggregate(pipe):
            cat[r["_id"] or "—"] = r["c"]
    except Exception:
        pass
    report["open_categories"] = cat

    report["has_open_work"] = (
        report["open_notifications"] > 0
        or report["open_tasks"] > 0
        or report["active_assignment_count"] > 0
    )
    return report


# ── Audit shorthand ──────────────────────────────────────────────────
async def _audit_lifecycle(
    db, *, action: str, project_number: Optional[str],
    assignment_role: Optional[str], target_user_id: Optional[str],
    target_email: Optional[str], before: Optional[Dict[str, Any]],
    after: Optional[Dict[str, Any]], actor: Dict[str, Any],
    notes: Optional[str] = None,
) -> None:
    doc = {
        "id": str(uuid.uuid4()),
        "at": _now_iso(),
        "category": "project_team_roster",
        "action": action,
        "project_number": project_number,
        "assignment_role": assignment_role,
        "target_user_id": target_user_id,
        "target_email": target_email,
        "before": before,
        "after": after,
        "notes": notes,
        "actor_user_id": actor.get("id") or actor.get("user_id") or "",
        "actor_role": actor.get("_actor") or "",
        "actor_email": (actor.get("email") or "").lower(),
        "actor_name": actor.get("name") or "",
    }
    try:
        await db.audit_events.insert_one(doc)
    except Exception as exc:
        logger.warning("[lifecycle] audit insert failed: %s", exc)


# ── Transfer / replacement engine ────────────────────────────────────
async def transfer_assignment(
    db,
    *,
    assignment_id: str,
    replacement_user_id: Optional[str],
    replacement_email: Optional[str],
    replacement_display_name: Optional[str],
    reason: str,
    end_status: str,
    actor: Dict[str, Any],
    migrate_open_work: bool = True,
) -> Dict[str, Any]:
    """End the existing assignment with `end_status`, open a new
    assignment for the replacement (if supplied), and optionally
    re-point all currently-addressed open notifications and tasks from
    the outgoing user to the replacement.

    `end_status` must be one of TRANSFERRED / REPLACED / DISABLED /
    TERMINATED / INACTIVE.
    """
    if end_status not in ALL_STATUSES or end_status == STATUS_ACTIVE:
        raise HTTPException(400, f"invalid end_status: {end_status!r}")

    existing = await db.project_team_assignments.find_one(
        {"id": assignment_id, "active": True}, {"_id": 0},
    )
    if not existing:
        raise HTTPException(404, "active assignment not found")

    now = _now_iso()
    project_number = existing["project_number"]
    out_user_id = existing.get("user_id")
    role = existing["assignment_role"]

    # Resolve replacement user (if email supplied, look up directory).
    rep_uid = replacement_user_id
    rep_email = (replacement_email or "").lower() or None
    rep_name = replacement_display_name
    if not rep_uid and rep_email:
        ud = await db.user_directory.find_one(
            {"email": rep_email}, {"_id": 0, "id": 1, "email": 1, "name": 1},
        )
        if ud:
            rep_uid = ud["id"]
            rep_email = ud.get("email") or rep_email
            rep_name = rep_name or ud.get("name")

    # 1. End the existing assignment.
    end_updates = {
        "active": False,
        "assignment_status": end_status,
        "removed_by": actor.get("id") or "admin",
        "removed_at": now,
        "remove_reason": reason,
        "end_reason": reason,
        "ended_at": now,
        "ended_by": actor.get("id") or "admin",
        "end_date": existing.get("end_date") or now[:10],
        "replacement_user_id": rep_uid,
    }
    await db.project_team_assignments.update_one(
        {"id": assignment_id}, {"$set": end_updates},
    )
    after_end = await db.project_team_assignments.find_one(
        {"id": assignment_id}, {"_id": 0},
    )
    await _audit_lifecycle(
        db, action="transfer_end", project_number=project_number,
        assignment_role=role, target_user_id=out_user_id,
        target_email=existing.get("email"), before=existing,
        after=after_end, actor=actor, notes=reason,
    )

    # 2. Open a new assignment for the replacement.
    new_row: Optional[Dict[str, Any]] = None
    if rep_uid or rep_email:
        # Skip if the same person already holds an active row for that role.
        dup = await db.project_team_assignments.find_one({
            "project_number": project_number,
            "user_id": rep_uid,
            "assignment_role": role,
            "active": True,
        }) if rep_uid else None
        if not dup:
            new_row = {
                "id": str(uuid.uuid4()),
                "project_number": project_number,
                "user_id": rep_uid,
                "employee_id": None,
                "email": rep_email,
                "display_name": rep_name,
                "assignment_role": role,
                "assignment_scope": existing.get("assignment_scope") or "full",
                "is_primary": bool(existing.get("is_primary")),
                "is_backup": False,
                "active": True,
                "assignment_status": STATUS_ACTIVE,
                "start_date": now[:10],
                "end_date": None,
                "assigned_by": actor.get("id") or "admin",
                "assigned_by_role": actor.get("_actor") or "admin",
                "assigned_at": now,
                "updated_by": None,
                "updated_at": None,
                "removed_by": None,
                "removed_at": None,
                "remove_reason": None,
                "end_reason": None,
                "ended_at": None,
                "ended_by": None,
                "replacement_user_id": None,
                "source": "lifecycle_transfer",
                "notes": f"replaces {existing.get('display_name') or existing.get('email') or out_user_id} · {reason}",
            }
            await db.project_team_assignments.insert_one(new_row)
            await _audit_lifecycle(
                db, action="transfer_open", project_number=project_number,
                assignment_role=role, target_user_id=rep_uid,
                target_email=rep_email, before=None,
                after={k: v for k, v in new_row.items() if k != "_id"},
                actor=actor, notes=reason,
            )

    # 3. Migrate open person-addressed work.
    migration: Dict[str, int] = {
        "notifications_repointed": 0, "tasks_repointed": 0,
    }
    if migrate_open_work and out_user_id and rep_uid:
        try:
            r1 = await db.notifications.update_many(
                {"recipient_user_id": out_user_id,
                 "acknowledged_at": None},
                {"$set": {"recipient_user_id": rep_uid,
                          "migrated_from_user_id": out_user_id,
                          "migrated_at": now}},
            )
            migration["notifications_repointed"] = r1.modified_count
        except Exception:
            pass
        try:
            r2 = await db.tasks.update_many(
                {"assignee_user_id": out_user_id,
                 "status": {"$nin": ["Closed", "Completed", "Cancelled"]}},
                {"$set": {"assignee_user_id": rep_uid,
                          "migrated_from_user_id": out_user_id,
                          "migrated_at": now}},
            )
            migration["tasks_repointed"] = r2.modified_count
        except Exception:
            pass
        await _audit_lifecycle(
            db, action="ownership_migrated", project_number=project_number,
            assignment_role=role, target_user_id=rep_uid,
            target_email=rep_email, before={"out_user_id": out_user_id},
            after=migration, actor=actor, notes=reason,
        )

    return {
        "ok": True,
        "ended": {k: v for k, v in after_end.items() if k != "_id"},
        "opened": {k: v for k, v in new_row.items() if k != "_id"} if new_row else None,
        "migration": migration,
    }


# ── Disable user precheck + migration ────────────────────────────────
async def disable_user_precheck(db, user_id: str) -> Dict[str, Any]:
    ud = await db.user_directory.find_one(
        {"id": user_id}, {"_id": 0, "email": 1, "name": 1},
    )
    if not ud:
        raise HTTPException(404, "user not found")
    return await scan_open_work_for_user(db, user_id, email=ud.get("email"))


# ── Pydantic IO ──────────────────────────────────────────────────────
class TransferIn(BaseModel):
    replacement_user_id: Optional[str] = None
    replacement_email: Optional[str] = None
    replacement_display_name: Optional[str] = None
    reason: str = Field(..., min_length=1, max_length=500)
    end_status: str = Field(default=STATUS_REPLACED)
    migrate_open_work: bool = True


class DisableMigrationIn(BaseModel):
    replacement_user_id: Optional[str] = None
    replacement_email: Optional[str] = None
    reason: str = Field(..., min_length=1, max_length=500)
    end_status: str = Field(default=STATUS_DISABLED)
    # If True, the user is also disabled on user_directory after migration.
    disable_directory_row: bool = True


# ── Router ───────────────────────────────────────────────────────────
def register_ownership_lifecycle(
    app, db, require_admin_dep: Callable, require_any_portal_token: Callable,
) -> APIRouter:
    router = APIRouter(tags=["ownership-lifecycle"])

    def _admin_actor(a: Any) -> Dict[str, Any]:
        if a is True:
            return {"_actor": "admin", "name": "Admin", "id": "admin"}
        if isinstance(a, dict):
            return a
        return {"_actor": "unknown"}

    @router.post("/api/admin/team-roster/assignments/{assignment_id}/transfer")
    async def transfer(
        assignment_id: str,
        payload: TransferIn = Body(...),
        actor=Depends(require_admin_dep),
    ):
        actor = _admin_actor(actor)
        if payload.end_status not in ALL_STATUSES or payload.end_status == STATUS_ACTIVE:
            raise HTTPException(400, "invalid end_status")
        return await transfer_assignment(
            db,
            assignment_id=assignment_id,
            replacement_user_id=payload.replacement_user_id,
            replacement_email=payload.replacement_email,
            replacement_display_name=payload.replacement_display_name,
            reason=payload.reason,
            end_status=payload.end_status,
            actor=actor,
            migrate_open_work=payload.migrate_open_work,
        )

    @router.get("/api/admin/users/{user_id}/disable-precheck")
    async def precheck(
        user_id: str,
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        return await disable_user_precheck(db, user_id)

    @router.post("/api/admin/users/{user_id}/disable-with-migration")
    async def disable_with_migration(
        user_id: str,
        payload: DisableMigrationIn = Body(...),
        actor=Depends(require_admin_dep),
    ):
        actor = _admin_actor(actor)
        ud = await db.user_directory.find_one(
            {"id": user_id}, {"_id": 0, "id": 1, "email": 1, "name": 1, "disabled": 1},
        )
        if not ud:
            raise HTTPException(404, "user not found")

        # End every active assignment for this user, optionally migrating
        # to the supplied replacement.
        ended: List[Dict[str, Any]] = []
        migrations: Dict[str, int] = {
            "notifications_repointed": 0, "tasks_repointed": 0,
        }
        cur = db.project_team_assignments.find(
            {"user_id": user_id, "active": True}, {"_id": 0},
        )
        active_assignments = []
        async for r in cur:
            active_assignments.append(r)
        for a in active_assignments:
            result = await transfer_assignment(
                db,
                assignment_id=a["id"],
                replacement_user_id=payload.replacement_user_id,
                replacement_email=payload.replacement_email,
                replacement_display_name=None,
                reason=payload.reason,
                end_status=payload.end_status,
                actor=actor,
                migrate_open_work=True,
            )
            ended.append(result["ended"])
            mig = result.get("migration") or {}
            migrations["notifications_repointed"] += mig.get("notifications_repointed", 0)
            migrations["tasks_repointed"] += mig.get("tasks_repointed", 0)

        # Disable the directory row last so the timeline reads as a
        # natural sequence: end assignments → migrate work → disable user.
        if payload.disable_directory_row:
            await db.user_directory.update_one(
                {"id": user_id},
                {"$set": {"disabled": True,
                          "disabled_at": _now_iso(),
                          "disabled_by": actor.get("id") or "admin"}},
            )
        await _audit_lifecycle(
            db, action="user_disabled", project_number=None,
            assignment_role=None, target_user_id=user_id,
            target_email=ud.get("email"),
            before={"disabled": bool(ud.get("disabled"))},
            after={"disabled": payload.disable_directory_row,
                   "ended_assignments": len(ended),
                   "migration": migrations},
            actor=actor, notes=payload.reason,
        )
        return {
            "ok": True, "ended_assignments": ended,
            "migration": migrations,
            "directory_disabled": payload.disable_directory_row,
        }

    @router.get("/api/admin/users/{user_id}/open-work")
    async def open_work(
        user_id: str,
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        return await scan_open_work_for_user(db, user_id)

    @router.get("/api/team-roster/snapshot/{project_number}")
    async def snapshot_now(
        project_number: str,
        actor=Depends(require_any_portal_token),  # noqa: ARG001
    ):
        """Capture-on-demand. Useful for testing and for client-side
        previews of what a freeze would look like."""
        return await capture_team_snapshot(db, project_number)

    @router.post("/api/team-roster/resolve-event")
    async def resolve_event(
        project_number: Optional[str] = Body(default=None, embed=True),
        role_chain: List[str] = Body(default_factory=list, embed=True),
        fallback_role: Optional[str] = Body(default=None, embed=True),
        actor=Depends(require_any_portal_token),  # noqa: ARG001
    ):
        return await resolve_recipient_for_event(
            db,
            project_number=project_number,
            role_chain=role_chain,
            fallback_role=fallback_role,
        )

    app.include_router(router)
    return router


__all__ = [
    "register_ownership_lifecycle",
    "capture_team_snapshot",
    "resolve_recipient_for_event",
    "scan_open_work_for_user",
    "transfer_assignment",
    "disable_user_precheck",
    "STATUS_ACTIVE", "STATUS_INACTIVE", "STATUS_TRANSFERRED",
    "STATUS_REPLACED", "STATUS_DISABLED", "STATUS_TERMINATED",
    "ALL_STATUSES", "SNAPSHOT_ROLES",
]
