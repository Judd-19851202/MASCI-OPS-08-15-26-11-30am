"""
MASCI Crew Hub — Phase 2 + 3 tools: Message Board, To-dos, Schedule,
Docs & Files (with MASCI-specific categories), Hill Charts.

Every endpoint is project-scoped and requires the caller to be a member
of that project (or be an owner/admin). Writes that target someone else's
content (delete/edit) additionally require the current user to be the
author OR an owner/admin.
"""
from __future__ import annotations

import uuid
import base64 as _b64
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from phase4 import log_activity, process_mentions, notify_user

logger = logging.getLogger(__name__)

# MASCI-specific doc categories visible on every project.
# (Basecamp is flat; MASCI wants these fixed top-level buckets.)
DOC_CATEGORIES = [
    "Submittals",
    "Plans & Specs",
    "Safety",
    "Daily Logs",
    "Pictures & Drone",
    "Locate Tickets",
    "General",
]


# ------------------------- Pydantic models -------------------------
class AuthorStub(BaseModel):
    user_id: str
    name: str
    email: str


class MessagePost(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=20000)


class MessageUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    body: Optional[str] = Field(None, min_length=1, max_length=20000)


class Message(BaseModel):
    id: str
    project_id: str
    author: AuthorStub
    title: str
    body: str
    comment_count: int = 0
    created_at: str
    updated_at: Optional[str] = None


class CommentPost(BaseModel):
    body: str = Field(..., min_length=1, max_length=10000)


class Comment(BaseModel):
    id: str
    message_id: str
    author: AuthorStub
    body: str
    created_at: str


class TodoListPost(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)


class TodoList(BaseModel):
    id: str
    project_id: str
    name: str
    description: Optional[str] = ""
    archived: bool = False
    created_at: str
    created_by: str
    open_count: int = 0
    done_count: int = 0


class TodoItemPost(BaseModel):
    list_id: str
    title: str = Field(..., min_length=1, max_length=500)
    assignee_id: Optional[str] = None
    due_date: Optional[str] = None  # ISO date string


class TodoItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    assignee_id: Optional[str] = None
    due_date: Optional[str] = None
    completed: Optional[bool] = None


class TodoItem(BaseModel):
    id: str
    list_id: str
    project_id: str
    title: str
    assignee: Optional[AuthorStub] = None
    due_date: Optional[str] = None
    completed_at: Optional[str] = None
    completed_by: Optional[str] = None
    created_at: str
    created_by: str


class EventPost(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    starts_at: str  # ISO datetime
    ends_at: Optional[str] = None
    all_day: bool = False
    location: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = Field(None, max_length=5000)


class EventModel(BaseModel):
    id: str
    project_id: str
    title: str
    starts_at: str
    ends_at: Optional[str] = None
    all_day: bool = False
    location: Optional[str] = ""
    description: Optional[str] = ""
    created_at: str
    created_by: str


class DocUpload(BaseModel):
    category: str
    filename: str = Field(..., min_length=1, max_length=300)
    file_data: str  # data URL
    notes: Optional[str] = Field(None, max_length=2000)


class Doc(BaseModel):
    id: str
    project_id: str
    category: str
    filename: str
    mime: str
    size_bytes: int
    notes: Optional[str] = ""
    uploaded_at: str
    uploaded_by: AuthorStub


class HillScopePost(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    position: int = Field(0, ge=0, le=100)  # 0-50 figuring out, 50-100 making it happen


class HillScopeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    position: Optional[int] = Field(None, ge=0, le=100)
    note: Optional[str] = Field(None, max_length=500)  # Optional update note


class HillScope(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str] = ""
    position: int
    last_update: Optional[str] = None
    last_note: Optional[str] = ""
    created_at: str
    created_by: str


# ------------------------- helpers -------------------------
def _data_url_to_bytes(data_url: str):
    if not data_url or "," not in data_url:
        raise HTTPException(400, "file_data must be a data URL")
    head, b64 = data_url.split(",", 1)
    mime = "application/octet-stream"
    if head.startswith("data:") and ";base64" in head:
        mime = head[5:].split(";", 1)[0] or mime
    try:
        raw = _b64.b64decode(b64)
    except Exception as e:
        raise HTTPException(400, f"base64 decode failed: {e}")
    return raw, mime


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ------------------------- router builder -------------------------
def build_tools_router(db, get_current_user, require_admin_or_owner):
    r = APIRouter(prefix="/api")
    HQ = "hq"

    async def _author_stub(user_id: str) -> AuthorStub:
        u = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not u:
            return AuthorStub(user_id=user_id, name="Unknown", email="")
        return AuthorStub(user_id=u["id"], name=u.get("name", ""), email=u["email"])

    async def _check_member(project_id: str, user: dict):
        if user.get("role") in {"owner", "admin"}:
            return
        if project_id == HQ:
            return
        m = await db.project_members.find_one(
            {"project_id": project_id, "user_id": user["id"]}
        )
        if not m:
            raise HTTPException(403, "Not a member of this project")

    async def _project_member_ids(project_id: str) -> List[str]:
        if project_id == HQ:
            docs = await db.users.find({"is_active": True}, {"_id": 0, "id": 1}).to_list(500)
            return [d["id"] for d in docs]
        rows = await db.project_members.find(
            {"project_id": project_id}, {"_id": 0, "user_id": 1}
        ).to_list(500)
        return [r["user_id"] for r in rows]

    async def _load_project(project_id: str):
        p = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not p:
            raise HTTPException(404, "Project not found")
        return p

    # ============================================================
    # MESSAGE BOARD
    # ============================================================
    @r.get("/projects/{project_id}/messages", response_model=List[Message])
    async def list_messages(project_id: str, user: dict = Depends(get_current_user)):
        await _load_project(project_id)
        await _check_member(project_id, user)
        docs = await db.messages.find(
            {"project_id": project_id}, {"_id": 0}
        ).sort("created_at", -1).to_list(500)
        out: List[Message] = []
        for d in docs:
            author = await _author_stub(d["author_id"])
            cc = await db.message_comments.count_documents({"message_id": d["id"]})
            out.append(Message(
                id=d["id"], project_id=d["project_id"], author=author,
                title=d["title"], body=d["body"],
                comment_count=cc,
                created_at=d["created_at"], updated_at=d.get("updated_at"),
            ))
        return out

    @r.post("/projects/{project_id}/messages", response_model=Message)
    async def create_message(project_id: str, body: MessagePost, user: dict = Depends(get_current_user)):
        await _load_project(project_id)
        await _check_member(project_id, user)
        doc = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "author_id": user["id"],
            "title": body.title.strip(),
            "body": body.body,
            "created_at": _now(),
        }
        await db.messages.insert_one(doc)
        doc.pop("_id", None)
        author = await _author_stub(user["id"])
        await log_activity(
            db, project_id, "message", "posted", user,
            target_id=doc["id"], target_label=doc["title"], preview=doc["body"][:200],
        )
        # Notify every other member of the project (new post) + @mentions
        members = await _project_member_ids(project_id)
        for uid in members:
            await notify_user(db, uid, "post", project_id, user,
                              "message", doc["id"], doc["title"], doc["body"])
        await process_mentions(db, doc["body"], project_id, user,
                               "message", doc["id"], doc["title"])
        return Message(
            id=doc["id"], project_id=project_id, author=author,
            title=doc["title"], body=doc["body"], comment_count=0,
            created_at=doc["created_at"],
        )

    @r.get("/messages/{message_id}", response_model=Message)
    async def get_message(message_id: str, user: dict = Depends(get_current_user)):
        d = await db.messages.find_one({"id": message_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Message not found")
        await _check_member(d["project_id"], user)
        author = await _author_stub(d["author_id"])
        cc = await db.message_comments.count_documents({"message_id": message_id})
        return Message(
            id=d["id"], project_id=d["project_id"], author=author,
            title=d["title"], body=d["body"], comment_count=cc,
            created_at=d["created_at"], updated_at=d.get("updated_at"),
        )

    @r.delete("/messages/{message_id}")
    async def delete_message(message_id: str, user: dict = Depends(get_current_user)):
        d = await db.messages.find_one({"id": message_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Message not found")
        if d["author_id"] != user["id"] and user.get("role") not in {"owner", "admin"}:
            raise HTTPException(403, "Only the author or an owner/admin can delete")
        await db.messages.delete_one({"id": message_id})
        await db.message_comments.delete_many({"message_id": message_id})
        return {"ok": True}

    @r.get("/messages/{message_id}/comments", response_model=List[Comment])
    async def list_comments(message_id: str, user: dict = Depends(get_current_user)):
        m = await db.messages.find_one({"id": message_id}, {"_id": 0})
        if not m:
            raise HTTPException(404, "Message not found")
        await _check_member(m["project_id"], user)
        docs = await db.message_comments.find(
            {"message_id": message_id}, {"_id": 0}
        ).sort("created_at", 1).to_list(500)
        out: List[Comment] = []
        for d in docs:
            author = await _author_stub(d["author_id"])
            out.append(Comment(
                id=d["id"], message_id=message_id, author=author,
                body=d["body"], created_at=d["created_at"],
            ))
        return out

    @r.post("/messages/{message_id}/comments", response_model=Comment)
    async def post_comment(message_id: str, body: CommentPost, user: dict = Depends(get_current_user)):
        m = await db.messages.find_one({"id": message_id}, {"_id": 0})
        if not m:
            raise HTTPException(404, "Message not found")
        await _check_member(m["project_id"], user)
        doc = {
            "id": str(uuid.uuid4()),
            "message_id": message_id,
            "author_id": user["id"],
            "body": body.body,
            "created_at": _now(),
        }
        await db.message_comments.insert_one(doc)
        author = await _author_stub(user["id"])
        await log_activity(
            db, m["project_id"], "comment", "commented", user,
            target_id=message_id, target_label=m.get("title", ""), preview=doc["body"][:200],
        )
        await process_mentions(db, doc["body"], m["project_id"], user,
                               "comment", message_id, m.get("title", ""))
        return Comment(
            id=doc["id"], message_id=message_id, author=author,
            body=doc["body"], created_at=doc["created_at"],
        )

    # ============================================================
    # TO-DOS
    # ============================================================
    @r.get("/projects/{project_id}/todo-lists", response_model=List[TodoList])
    async def list_todo_lists(project_id: str, user: dict = Depends(get_current_user)):
        await _load_project(project_id)
        await _check_member(project_id, user)
        docs = await db.todo_lists.find(
            {"project_id": project_id, "archived": {"$ne": True}}, {"_id": 0}
        ).sort("created_at", 1).to_list(500)
        out: List[TodoList] = []
        for d in docs:
            items = await db.todos.find({"list_id": d["id"]}, {"_id": 0}).to_list(1000)
            open_c = sum(1 for i in items if not i.get("completed_at"))
            done_c = sum(1 for i in items if i.get("completed_at"))
            out.append(TodoList(
                id=d["id"], project_id=d["project_id"], name=d["name"],
                description=d.get("description", ""), archived=d.get("archived", False),
                created_at=d["created_at"], created_by=d["created_by"],
                open_count=open_c, done_count=done_c,
            ))
        return out

    @r.post("/projects/{project_id}/todo-lists", response_model=TodoList)
    async def create_todo_list(project_id: str, body: TodoListPost, user: dict = Depends(get_current_user)):
        await _load_project(project_id)
        await _check_member(project_id, user)
        doc = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "name": body.name.strip(),
            "description": body.description or "",
            "archived": False,
            "created_at": _now(),
            "created_by": user["id"],
        }
        await db.todo_lists.insert_one(doc)
        return TodoList(
            id=doc["id"], project_id=project_id, name=doc["name"],
            description=doc["description"], archived=False,
            created_at=doc["created_at"], created_by=user["id"],
            open_count=0, done_count=0,
        )

    @r.delete("/todo-lists/{list_id}")
    async def delete_todo_list(list_id: str, user: dict = Depends(get_current_user)):
        lst = await db.todo_lists.find_one({"id": list_id}, {"_id": 0})
        if not lst:
            raise HTTPException(404, "List not found")
        if lst["created_by"] != user["id"] and user.get("role") not in {"owner", "admin"}:
            raise HTTPException(403, "Only the creator or an owner/admin can delete")
        await db.todo_lists.delete_one({"id": list_id})
        await db.todos.delete_many({"list_id": list_id})
        return {"ok": True}

    @r.get("/todo-lists/{list_id}/items", response_model=List[TodoItem])
    async def list_todos(list_id: str, user: dict = Depends(get_current_user)):
        lst = await db.todo_lists.find_one({"id": list_id}, {"_id": 0})
        if not lst:
            raise HTTPException(404, "List not found")
        await _check_member(lst["project_id"], user)
        docs = await db.todos.find({"list_id": list_id}, {"_id": 0}).sort(
            [("completed_at", 1), ("created_at", 1)]
        ).to_list(2000)
        out: List[TodoItem] = []
        for d in docs:
            assignee = None
            if d.get("assignee_id"):
                assignee = await _author_stub(d["assignee_id"])
            out.append(TodoItem(
                id=d["id"], list_id=list_id, project_id=lst["project_id"],
                title=d["title"], assignee=assignee, due_date=d.get("due_date"),
                completed_at=d.get("completed_at"),
                completed_by=d.get("completed_by"),
                created_at=d["created_at"], created_by=d["created_by"],
            ))
        return out

    @r.post("/todos", response_model=TodoItem)
    async def create_todo(body: TodoItemPost, user: dict = Depends(get_current_user)):
        lst = await db.todo_lists.find_one({"id": body.list_id}, {"_id": 0})
        if not lst:
            raise HTTPException(404, "List not found")
        await _check_member(lst["project_id"], user)
        doc = {
            "id": str(uuid.uuid4()),
            "list_id": body.list_id,
            "project_id": lst["project_id"],
            "title": body.title.strip(),
            "assignee_id": body.assignee_id,
            "due_date": body.due_date,
            "completed_at": None,
            "completed_by": None,
            "created_at": _now(),
            "created_by": user["id"],
        }
        await db.todos.insert_one(doc)
        assignee = await _author_stub(body.assignee_id) if body.assignee_id else None
        await log_activity(
            db, lst["project_id"], "todo", "added", user,
            target_id=doc["id"], target_label=doc["title"],
        )
        if body.assignee_id and body.assignee_id != user["id"]:
            await notify_user(
                db, body.assignee_id, "todo_assigned", lst["project_id"], user,
                "todo", doc["id"], doc["title"],
            )
        return TodoItem(
            id=doc["id"], list_id=doc["list_id"], project_id=doc["project_id"],
            title=doc["title"], assignee=assignee, due_date=doc["due_date"],
            completed_at=None, completed_by=None,
            created_at=doc["created_at"], created_by=doc["created_by"],
        )

    @r.put("/todos/{todo_id}", response_model=TodoItem)
    async def update_todo(todo_id: str, body: TodoItemUpdate, user: dict = Depends(get_current_user)):
        d = await db.todos.find_one({"id": todo_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "To-do not found")
        await _check_member(d["project_id"], user)
        patch: dict = {}
        if body.title is not None:
            patch["title"] = body.title.strip()
        if body.assignee_id is not None:
            patch["assignee_id"] = body.assignee_id or None
        if body.due_date is not None:
            patch["due_date"] = body.due_date or None
        if body.completed is not None:
            if body.completed:
                patch["completed_at"] = _now()
                patch["completed_by"] = user["id"]
            else:
                patch["completed_at"] = None
                patch["completed_by"] = None
        if patch:
            await db.todos.update_one({"id": todo_id}, {"$set": patch})
        nd = await db.todos.find_one({"id": todo_id}, {"_id": 0})
        assignee = None
        if nd.get("assignee_id"):
            assignee = await _author_stub(nd["assignee_id"])
        return TodoItem(
            id=nd["id"], list_id=nd["list_id"], project_id=nd["project_id"],
            title=nd["title"], assignee=assignee, due_date=nd.get("due_date"),
            completed_at=nd.get("completed_at"), completed_by=nd.get("completed_by"),
            created_at=nd["created_at"], created_by=nd["created_by"],
        )

    @r.delete("/todos/{todo_id}")
    async def delete_todo(todo_id: str, user: dict = Depends(get_current_user)):
        d = await db.todos.find_one({"id": todo_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "To-do not found")
        if d["created_by"] != user["id"] and user.get("role") not in {"owner", "admin"}:
            raise HTTPException(403, "Only the creator or an owner/admin can delete")
        await db.todos.delete_one({"id": todo_id})
        return {"ok": True}

    # "My To-dos" — every todo assigned to the current user across all projects
    @r.get("/me/todos", response_model=List[TodoItem])
    async def my_todos(user: dict = Depends(get_current_user)):
        docs = await db.todos.find(
            {"assignee_id": user["id"], "completed_at": None}, {"_id": 0}
        ).sort("due_date", 1).to_list(1000)
        me = await _author_stub(user["id"])
        return [
            TodoItem(
                id=d["id"], list_id=d["list_id"], project_id=d["project_id"],
                title=d["title"], assignee=me, due_date=d.get("due_date"),
                completed_at=None, completed_by=None,
                created_at=d["created_at"], created_by=d["created_by"],
            )
            for d in docs
        ]

    # ============================================================
    # SCHEDULE
    # ============================================================
    @r.get("/projects/{project_id}/events", response_model=List[EventModel])
    async def list_events(project_id: str, user: dict = Depends(get_current_user)):
        await _load_project(project_id)
        await _check_member(project_id, user)
        docs = await db.events.find(
            {"project_id": project_id}, {"_id": 0}
        ).sort("starts_at", 1).to_list(1000)
        return [EventModel(**d) for d in docs]

    @r.post("/projects/{project_id}/events", response_model=EventModel)
    async def create_event(project_id: str, body: EventPost, user: dict = Depends(get_current_user)):
        await _load_project(project_id)
        await _check_member(project_id, user)
        doc = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "title": body.title.strip(),
            "starts_at": body.starts_at,
            "ends_at": body.ends_at,
            "all_day": body.all_day,
            "location": body.location or "",
            "description": body.description or "",
            "created_at": _now(),
            "created_by": user["id"],
        }
        await db.events.insert_one(doc)
        doc.pop("_id", None)
        await log_activity(db, project_id, "event", "added", user,
                           target_id=doc["id"], target_label=doc["title"])
        return EventModel(**doc)

    @r.delete("/events/{event_id}")
    async def delete_event(event_id: str, user: dict = Depends(get_current_user)):
        d = await db.events.find_one({"id": event_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Event not found")
        if d["created_by"] != user["id"] and user.get("role") not in {"owner", "admin"}:
            raise HTTPException(403, "Only the creator or an owner/admin can delete")
        await db.events.delete_one({"id": event_id})
        return {"ok": True}

    # ============================================================
    # DOCS & FILES
    # ============================================================
    @r.get("/doc-categories")
    async def doc_categories():
        return {"categories": DOC_CATEGORIES}

    @r.get("/projects/{project_id}/docs", response_model=List[Doc])
    async def list_docs(
        project_id: str,
        category: Optional[str] = None,
        user: dict = Depends(get_current_user),
    ):
        await _load_project(project_id)
        await _check_member(project_id, user)
        q: dict = {"project_id": project_id}
        if category:
            q["category"] = category
        docs = await db.docs.find(q, {"_id": 0, "file_data": 0}).sort("uploaded_at", -1).to_list(2000)
        out: List[Doc] = []
        for d in docs:
            uploader = await _author_stub(d["uploaded_by"])
            out.append(Doc(
                id=d["id"], project_id=d["project_id"], category=d["category"],
                filename=d["filename"], mime=d.get("mime", ""),
                size_bytes=d.get("size_bytes", 0), notes=d.get("notes", ""),
                uploaded_at=d["uploaded_at"], uploaded_by=uploader,
            ))
        return out

    @r.post("/projects/{project_id}/docs", response_model=Doc)
    async def upload_doc(project_id: str, body: DocUpload, user: dict = Depends(get_current_user)):
        await _load_project(project_id)
        await _check_member(project_id, user)
        if body.category not in DOC_CATEGORIES:
            raise HTTPException(400, f"category must be one of {DOC_CATEGORIES}")
        raw, mime = _data_url_to_bytes(body.file_data)
        if len(raw) > 30 * 1024 * 1024:
            raise HTTPException(413, f"File too large ({len(raw)//1024} KB). Max 30 MB.")
        doc = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "category": body.category,
            "filename": body.filename.strip(),
            "file_data": body.file_data,
            "mime": mime,
            "size_bytes": len(raw),
            "notes": body.notes or "",
            "uploaded_at": _now(),
            "uploaded_by": user["id"],
        }
        await db.docs.insert_one(doc)
        uploader = await _author_stub(user["id"])
        image_url = None
        if (doc.get("mime") or "").startswith("image/"):
            image_url = f"/api/docs/{doc['id']}/file"
        await log_activity(
            db, project_id, "doc", "uploaded", user,
            target_id=doc["id"], target_label=doc["filename"],
            preview=f"{doc['category']} · {doc['size_bytes']//1024} KB",
            image_url=image_url,
        )
        return Doc(
            id=doc["id"], project_id=project_id, category=doc["category"],
            filename=doc["filename"], mime=doc["mime"],
            size_bytes=doc["size_bytes"], notes=doc["notes"],
            uploaded_at=doc["uploaded_at"], uploaded_by=uploader,
        )

    @r.get("/docs/{doc_id}/file")
    async def download_doc(doc_id: str, user: dict = Depends(get_current_user)):
        d = await db.docs.find_one({"id": doc_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "File not found")
        await _check_member(d["project_id"], user)
        # Two storage backends:
        #   • Inline data URL  → small files, <12 MB raw (fits in BSON)
        #   • file_path on disk → big plan sets / photo bundles (up to ~500 MB).
        #     Used by the Basecamp-import script for files >11.5 MB.
        media_type = d.get("mime") or "application/octet-stream"
        safe = "".join(c if c.isalnum() or c in ("-", "_", ".", " ") else "_" for c in d["filename"])
        disp = "inline" if media_type == "application/pdf" else "attachment"
        if d.get("file_path"):
            from fastapi.responses import FileResponse
            import os as _os
            if not _os.path.isfile(d["file_path"]):
                raise HTTPException(410, "File missing on server")
            return FileResponse(
                d["file_path"],
                media_type=media_type,
                filename=safe,
                headers={
                    "Content-Disposition": f'{disp}; filename="{safe}"',
                    "X-Content-Type-Options": "nosniff",
                },
            )
        raw, mime = _data_url_to_bytes(d.get("file_data") or "")
        media_type = d.get("mime") or mime or "application/octet-stream"
        return Response(
            content=raw,
            media_type=media_type,
            headers={
                "Content-Disposition": f'{disp}; filename="{safe}"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    @r.delete("/docs/{doc_id}")
    async def delete_doc(doc_id: str, user: dict = Depends(get_current_user)):
        d = await db.docs.find_one({"id": doc_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "File not found")
        if d["uploaded_by"] != user["id"] and user.get("role") not in {"owner", "admin"}:
            raise HTTPException(403, "Only the uploader or an owner/admin can delete")
        await db.docs.delete_one({"id": doc_id})
        return {"ok": True}

    # ============================================================
    # HILL CHARTS
    # ============================================================
    @r.get("/projects/{project_id}/hill-scopes", response_model=List[HillScope])
    async def list_hill_scopes(project_id: str, user: dict = Depends(get_current_user)):
        await _load_project(project_id)
        await _check_member(project_id, user)
        docs = await db.hill_scopes.find(
            {"project_id": project_id, "archived": {"$ne": True}}, {"_id": 0}
        ).sort("created_at", 1).to_list(500)
        return [HillScope(**d) for d in docs]

    @r.post("/projects/{project_id}/hill-scopes", response_model=HillScope)
    async def create_hill_scope(project_id: str, body: HillScopePost, user: dict = Depends(get_current_user)):
        await _load_project(project_id)
        await _check_member(project_id, user)
        doc = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "title": body.title.strip(),
            "description": body.description or "",
            "position": body.position,
            "last_update": _now(),
            "last_note": "",
            "archived": False,
            "created_at": _now(),
            "created_by": user["id"],
        }
        await db.hill_scopes.insert_one(doc)
        doc.pop("_id", None)
        await log_activity(db, project_id, "hill", "added", user,
                           target_id=doc["id"], target_label=doc["title"])
        return HillScope(**doc)

    @r.put("/hill-scopes/{scope_id}", response_model=HillScope)
    async def update_hill_scope(scope_id: str, body: HillScopeUpdate, user: dict = Depends(get_current_user)):
        d = await db.hill_scopes.find_one({"id": scope_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Scope not found")
        await _check_member(d["project_id"], user)
        patch: dict = {"last_update": _now()}
        if body.title is not None:
            patch["title"] = body.title.strip()
        if body.description is not None:
            patch["description"] = body.description
        if body.position is not None:
            patch["position"] = body.position
        if body.note is not None:
            patch["last_note"] = body.note
        await db.hill_scopes.update_one({"id": scope_id}, {"$set": patch})
        nd = await db.hill_scopes.find_one({"id": scope_id}, {"_id": 0})
        await log_activity(
            db, d["project_id"], "hill", "updated", user,
            target_id=scope_id, target_label=nd["title"],
            preview=body.note or f"Moved to {nd['position']}%",
        )
        return HillScope(**nd)

    @r.delete("/hill-scopes/{scope_id}")
    async def delete_hill_scope(scope_id: str, user: dict = Depends(get_current_user)):
        d = await db.hill_scopes.find_one({"id": scope_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Scope not found")
        if d["created_by"] != user["id"] and user.get("role") not in {"owner", "admin"}:
            raise HTTPException(403, "Only the creator or an owner/admin can delete")
        await db.hill_scopes.delete_one({"id": scope_id})
        return {"ok": True}

    return r


async def create_tools_indexes(db) -> None:
    try:
        await db.messages.create_index([("project_id", 1), ("created_at", -1)])
        await db.message_comments.create_index([("message_id", 1), ("created_at", 1)])
        await db.todo_lists.create_index([("project_id", 1), ("created_at", 1)])
        await db.todos.create_index([("list_id", 1), ("created_at", 1)])
        await db.todos.create_index([("assignee_id", 1), ("completed_at", 1)])
        await db.events.create_index([("project_id", 1), ("starts_at", 1)])
        await db.docs.create_index([("project_id", 1), ("category", 1), ("uploaded_at", -1)])
        await db.hill_scopes.create_index([("project_id", 1), ("created_at", 1)])
    except Exception as e:
        logger.warning(f"tools indexes: {e}")


async def get_scorecard(db, project_id: str):
    """Aggregated snapshot of all 5 tool surfaces for a project — used on
    the project home scorecard to avoid 5 separate round trips."""
    now_iso = datetime.now(timezone.utc).isoformat()

    # Latest 3 messages
    msgs = await db.messages.find(
        {"project_id": project_id}, {"_id": 0}
    ).sort("created_at", -1).limit(3).to_list(3)
    msg_out = []
    for m in msgs:
        u = await db.users.find_one({"id": m["author_id"]}, {"_id": 0}) or {}
        msg_out.append({
            "id": m["id"], "title": m["title"],
            "body_preview": (m.get("body") or "")[:140],
            "author_name": u.get("name", "Unknown"),
            "author_id": m["author_id"],
            "comment_count": await db.message_comments.count_documents({"message_id": m["id"]}),
            "created_at": m["created_at"],
        })

    # Next 2 upcoming events
    events = await db.events.find(
        {"project_id": project_id, "starts_at": {"$gte": now_iso[:10]}},
        {"_id": 0, "id": 1, "title": 1, "starts_at": 1, "ends_at": 1,
         "all_day": 1, "location": 1},
    ).sort("starts_at", 1).limit(2).to_list(2)

    # Todo counts
    all_todos = await db.todos.find(
        {"project_id": project_id}, {"_id": 0, "completed_at": 1}
    ).to_list(5000)
    open_count = sum(1 for t in all_todos if not t.get("completed_at"))

    # 2 latest docs
    docs = await db.docs.find(
        {"project_id": project_id}, {"_id": 0, "file_data": 0}
    ).sort("uploaded_at", -1).limit(2).to_list(2)
    doc_out = []
    for d in docs:
        u = await db.users.find_one({"id": d["uploaded_by"]}, {"_id": 0}) or {}
        doc_out.append({
            "id": d["id"], "filename": d["filename"], "category": d["category"],
            "size_bytes": d.get("size_bytes", 0),
            "uploaded_at": d["uploaded_at"],
            "uploaded_by_name": u.get("name", "Unknown"),
        })

    # Top 3 hill scopes (most recently updated)
    scopes = await db.hill_scopes.find(
        {"project_id": project_id, "archived": {"$ne": True}},
        {"_id": 0, "id": 1, "title": 1, "position": 1, "last_update": 1,
         "last_note": 1},
    ).sort("last_update", -1).limit(3).to_list(3)

    return {
        "messages": msg_out,
        "events": events,
        "todos": {"open": open_count, "done": len(all_todos) - open_count, "total": len(all_todos)},
        "docs": doc_out,
        "hill_scopes": scopes,
    }
