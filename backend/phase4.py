"""
MASCI Crew Hub — Phase 4: activity log, notifications, @mentions, email
fan-out via Resend, per-project search, and "Hey!" inbox.

All Phase 2/3 write endpoints in tools.py call `log_activity(db, ...)` and
`process_mentions(db, ...)` to populate the feed + notifications collections.
"""
from __future__ import annotations

import os
import re
import uuid
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Matches @first.last@mascigc.com OR @email (before space/newline/punctuation).
MENTION_RE = re.compile(r"@([A-Za-z0-9._%+-]+@mascigc\.com)", re.IGNORECASE)


class ActivityItem(BaseModel):
    id: str
    project_id: str
    project_name: Optional[str] = ""
    kind: str            # "message" | "comment" | "todo" | "event" | "doc" | "hill"
    verb: str            # "posted" | "commented" | "added" | "completed" | "uploaded" | "updated"
    actor_id: str
    actor_name: str
    target_id: Optional[str] = ""
    target_label: str = ""       # e.g. message title / todo title / doc filename
    preview: Optional[str] = ""  # optional body snippet
    image_url: Optional[str] = None  # for doc uploads that are images
    created_at: str


class Notification(BaseModel):
    id: str
    kind: str            # "mention" | "todo_assigned" | "post"
    project_id: str
    project_name: Optional[str] = ""
    actor_id: str
    actor_name: str
    target_kind: str     # "message" | "comment" | "todo"
    target_id: str
    target_label: str
    preview: Optional[str] = ""
    created_at: str
    read_at: Optional[str] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def log_activity(
    db, project_id: str, kind: str, verb: str, actor: dict,
    target_id: str = "", target_label: str = "", preview: str = "",
    image_url: Optional[str] = None,
) -> None:
    """Best-effort activity write. Never raises."""
    try:
        proj = await db.projects.find_one({"id": project_id}, {"_id": 0, "name": 1})
        await db.activity_log.insert_one({
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "project_name": (proj or {}).get("name", ""),
            "kind": kind,
            "verb": verb,
            "actor_id": actor["id"],
            "actor_name": actor.get("name") or actor.get("email", ""),
            "target_id": target_id or "",
            "target_label": (target_label or "")[:200],
            "preview": (preview or "")[:280],
            "image_url": image_url,
            "created_at": _now(),
        })
    except Exception as e:
        logger.warning(f"activity_log insert failed: {e}")


async def notify_user(
    db, user_id: str, kind: str, project_id: str, actor: dict,
    target_kind: str, target_id: str, target_label: str, preview: str = "",
) -> Optional[dict]:
    """TRACK 15.28C — rewritten to use canonical `emit_notification`.

    The legacy crew-hub bell was retired with the canonicalization
    track. This wrapper preserves the call-sites in tools.py
    (messages, todos, @mentions) but routes them through the
    canonical fanout so they land in the single source of truth
    (`db.notifications`, type/recipient_role/recipient_user_id),
    are idempotent (no duplicate posts), and reach the unified bell.

    Returns a minimal echo dict for compatibility with the legacy
    return shape used by `process_mentions` (only `project_name` is
    consumed downstream)."""
    if user_id == actor["id"]:
        return None
    try:
        from lib.event_fanout import emit_notification  # noqa: PLC0415
        proj = await db.projects.find_one({"id": project_id}, {"_id": 0, "name": 1, "project_number": 1}) or {}
        title_map = {
            "mention": f"You were mentioned in {target_label[:80]}",
            "post":    f"New post: {target_label[:80]}",
            "todo_assigned": f"To-do assigned: {target_label[:80]}",
        }
        actor_name = actor.get("name") or actor.get("email") or "Someone"
        await emit_notification(db, {
            "type": f"crew.{kind}",
            "title": title_map.get(kind, f"{kind}: {target_label[:80]}"),
            "message": preview[:280] or f"{actor_name} · {proj.get('name','')}",
            "severity": "Info",
            "recipient_role": "admin",
            "recipient_user_id": user_id,
            "linked_source_module": f"crew.{target_kind}",
            "linked_source_record_id": target_id,
            "linked_project_number": proj.get("project_number"),
        })
        return {"project_name": proj.get("name", "")}
    except Exception as e:
        logger.warning(f"notify_user canonical fanout failed: {e}")
        return None


async def parse_mentions(db, body: str) -> List[dict]:
    """Scan body for @email@mascigc.com mentions, return the matching user docs."""
    if not body:
        return []
    emails = list({m.lower() for m in MENTION_RE.findall(body)})
    if not emails:
        return []
    users = await db.users.find(
        {"email": {"$in": emails}, "is_active": True},
        {"_id": 0, "id": 1, "email": 1, "name": 1},
    ).to_list(50)
    return users


async def process_mentions(
    db, body: str, project_id: str, actor: dict,
    target_kind: str, target_id: str, target_label: str,
) -> List[dict]:
    """Find @-mentions in `body`, notify each mentioned user, dispatch email."""
    mentioned = await parse_mentions(db, body)
    notified = []
    for u in mentioned:
        n = await notify_user(
            db, u["id"], "mention", project_id, actor,
            target_kind, target_id, target_label, body,
        )
        if n:
            await _dispatch_email(
                to=u["email"], subject=f'You were mentioned — {target_label[:60]}',
                actor=actor.get("name") or actor.get("email"),
                project_name=n.get("project_name", ""),
                target_label=target_label, preview=body[:600],
            )
            notified.append(u)
    return notified


async def _dispatch_email(to: str, subject: str, actor: str, project_name: str, target_label: str, preview: str) -> None:
    """Fire-and-forget email via Resend. No-op if AUTO_EMAIL_REPORTS=false or RESEND_API_KEY missing."""
    if os.environ.get("AUTO_EMAIL_REPORTS", "false").lower() not in ("true", "1", "yes"):
        return
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        return
    sender = os.environ.get("SENDER_EMAIL", "noreply@mascidocs.com")
    reply_to = os.environ.get("REPLY_TO_EMAIL") or None
    html = (
        f'<div style="font-family:system-ui,-apple-system,sans-serif;max-width:520px;margin:0 auto;">'
        f'<div style="border-bottom:4px solid #b91c1c;padding-bottom:10px;margin-bottom:15px;">'
        f'<strong style="color:#b91c1c;letter-spacing:.15em;font-size:11px;text-transform:uppercase">MASCI · CREW HUB</strong>'
        f'</div>'
        f'<p style="color:#0f172a;margin:0 0 8px;font-size:15px;"><strong>{actor}</strong> on <em>{project_name}</em>:</p>'
        f'<p style="color:#0f172a;font-weight:700;margin:0 0 6px;font-size:16px;">{target_label}</p>'
        f'<blockquote style="margin:0 0 15px;padding:10px 14px;border-left:3px solid #cbd5e1;color:#334155;background:#f8fafc;font-size:14px;white-space:pre-wrap;">{preview}</blockquote>'
        f'<a href="https://mascidocs.com/app" style="display:inline-block;background:#b91c1c;color:white;padding:10px 18px;text-decoration:none;border-radius:4px;font-weight:700;font-size:13px;letter-spacing:.05em">OPEN IN CREW HUB</a>'
        f'</div>'
    )
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            payload: Dict[str, Any] = {
                "from": sender, "to": [to], "subject": subject, "html": html,
            }
            if reply_to:
                payload["reply_to"] = reply_to
            await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
    except Exception as e:
        logger.warning(f"Resend email failed ({to}): {e}")


# ------------------------- router -------------------------
def build_phase4_router(db, get_current_user):
    r = APIRouter(prefix="/api")
    HQ = "hq"

    async def _member_project_ids(user: dict) -> List[str]:
        if user.get("role") in {"owner", "admin"}:
            docs = await db.projects.find({"archived": {"$ne": True}}, {"_id": 0, "id": 1}).to_list(2000)
            return [d["id"] for d in docs]
        rows = await db.project_members.find(
            {"user_id": user["id"]}, {"_id": 0, "project_id": 1}
        ).to_list(2000)
        ids = {r["project_id"] for r in rows}
        ids.add(HQ)
        return list(ids)

    async def _ensure_member(project_id: str, user: dict):
        if user.get("role") in {"owner", "admin"}:
            return
        if project_id == HQ:
            return
        m = await db.project_members.find_one(
            {"project_id": project_id, "user_id": user["id"]}
        )
        if not m:
            raise HTTPException(403, "Not a member of this project")

    @r.get("/projects/{project_id}/activity", response_model=List[ActivityItem])
    async def project_activity(
        project_id: str,
        limit: int = Query(50, ge=1, le=200),
        user: dict = Depends(get_current_user),
    ):
        await _ensure_member(project_id, user)
        docs = await db.activity_log.find(
            {"project_id": project_id}, {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        return [ActivityItem(**d) for d in docs]

    @r.get("/me/activity", response_model=List[ActivityItem])
    async def my_activity(
        limit: int = Query(50, ge=1, le=200),
        user: dict = Depends(get_current_user),
    ):
        ids = await _member_project_ids(user)
        docs = await db.activity_log.find(
            {"project_id": {"$in": ids}}, {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        return [ActivityItem(**d) for d in docs]

    # TRACK 15.28C (2026-02) — Notification system canonicalization.
    # The legacy crew-hub bell endpoints (/api/me/notifications,
    # /api/me/notifications/{id}/read, /api/me/notifications/mark-all-read)
    # were retired with this track. The single source of truth is now
    # the canonical bell at /api/notifications (routes/tasks_notifications.py).
    # phase4.notify_user has been deleted; @-mention notifications now flow
    # through the canonical fanout (tools.py uses the new path).

    @r.get("/projects/{project_id}/search")
    async def search_project(
        project_id: str,
        q: str = Query(..., min_length=2),
        user: dict = Depends(get_current_user),
    ):
        await _ensure_member(project_id, user)
        needle = re.escape(q.strip())
        rx = {"$regex": needle, "$options": "i"}
        # Parallel scan
        msg_task = db.messages.find(
            {"project_id": project_id, "$or": [{"title": rx}, {"body": rx}]},
            {"_id": 0, "id": 1, "title": 1, "body": 1, "created_at": 1, "author_id": 1},
        ).limit(20).to_list(20)
        todo_task = db.todos.find(
            {"project_id": project_id, "title": rx},
            {"_id": 0, "id": 1, "title": 1, "list_id": 1, "completed_at": 1},
        ).limit(20).to_list(20)
        doc_task = db.docs.find(
            {"project_id": project_id, "$or": [{"filename": rx}, {"notes": rx}, {"category": rx}]},
            {"_id": 0, "id": 1, "filename": 1, "category": 1, "uploaded_at": 1},
        ).limit(20).to_list(20)
        event_task = db.events.find(
            {"project_id": project_id, "$or": [{"title": rx}, {"location": rx}, {"description": rx}]},
            {"_id": 0, "id": 1, "title": 1, "starts_at": 1, "location": 1},
        ).limit(20).to_list(20)
        msgs, todos, docs, events = await asyncio.gather(msg_task, todo_task, doc_task, event_task)
        return {"messages": msgs, "todos": todos, "docs": docs, "events": events}

    @r.get("/users/directory")
    async def users_directory(user: dict = Depends(get_current_user)):
        """Simple directory for @-mention autocomplete — all active users."""
        docs = await db.users.find(
            {"is_active": True}, {"_id": 0, "id": 1, "email": 1, "name": 1}
        ).sort("name", 1).to_list(200)
        return docs

    return r


async def create_phase4_indexes(db) -> None:
    try:
        await db.activity_log.create_index([("project_id", 1), ("created_at", -1)])
        await db.notifications.create_index([("user_id", 1), ("read_at", 1), ("created_at", -1)])
    except Exception as e:
        logger.warning(f"phase4 indexes: {e}")
