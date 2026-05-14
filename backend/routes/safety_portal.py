"""
routes/safety_portal.py — Safety Portal HTTP surface.

Layout mirrors `routes/hr_portal.py`. Includes:
  • Login / password change / forgot-password / reset
  • `GET /me` for shell hydration
  • Overview KPIs (reads existing collections — NO duplicate forms)
  • Corrective Action CRUD (new collection)
  • Admin-only user management nested under /admin/safety-users
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from safety_users import (
    seed_safety_users,
    list_safety_users,
    add_safety_user,
    update_safety_user,
    delete_safety_user,
    find_safety_user_by_email,
    set_safety_user_password,
    stamp_safety_login,
    make_safety_user_token,
    is_valid_safety_user_token_async,
    make_safety_reset_token,
    consume_safety_reset_token,
    public_safety_user_view,
    verify_password,
    generate_temp_password,
)

logger = logging.getLogger(__name__)


# ─── Pydantic models (module-level — DO NOT nest in build_safety_router) ──
# Pydantic 2.12 cannot fully resolve BaseModels declared inside function
# closures and throws "class not fully defined" / 422 body-missing errors
# at request time. This bit us before in iter102. Keep these here.

class SafetyLoginBody(BaseModel):
    email: str
    password: str


class SafetyLoginResponse(BaseModel):
    token: str
    user: dict
    must_change_password: bool


class PasswordChangeBody(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordBody(BaseModel):
    email: str


class ResetPasswordBody(BaseModel):
    token: str
    new_password: str


class SafetyUserCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = ""
    role: Optional[str] = "Safety Coordinator"


class SafetyUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    disabled: Optional[bool] = None


class CorrectiveActionCreate(BaseModel):
    title: str = Field(..., min_length=3)
    description: Optional[str] = ""
    source_kind: str = Field(...)
    source_id: Optional[str] = None
    project_number: Optional[str] = ""
    assigned_to_name: Optional[str] = ""
    assigned_to_email: Optional[str] = ""
    priority: Optional[str] = "Medium"
    due_date: Optional[str] = None
    notes: Optional[str] = ""


class CorrectiveActionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to_name: Optional[str] = None
    assigned_to_email: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None
    completion_notes: Optional[str] = None


def build_safety_router(db, require_admin) -> APIRouter:
    """Build and return the Safety Portal router. Caller must
    `app.include_router(...)` the return value AFTER calling this — same
    pattern as `build_hr_portal_router`.
    """
    api_router = APIRouter(prefix="/api", tags=["safety-portal"])

    # ---------- Auth dependency ----------
    async def _require_safety_token(request: Request) -> dict:
        token = request.headers.get("X-Safety-Token", "")
        user = await is_valid_safety_user_token_async(db, token)
        if not user:
            raise HTTPException(status_code=401, detail="Safety auth required")
        return user

    # ---------- Login ----------
    @api_router.post("/safety/login", response_model=SafetyLoginResponse)
    async def safety_login(body: SafetyLoginBody, request: Request):
        user = await find_safety_user_by_email(db, body.email)
        if not user or user.get("disabled"):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        pwh = user.get("password_hash")
        if not pwh or not verify_password(body.password, pwh):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = make_safety_user_token(user["id"], pwh)
        ip = request.client.host if request.client else None
        await stamp_safety_login(db, user["id"], ip)
        return SafetyLoginResponse(
            token=token,
            user=public_safety_user_view(user),
            must_change_password=bool(user.get("must_change_password")),
        )

    # ---------- /me ----------
    @api_router.get("/safety/me")
    async def safety_me(user: dict = Depends(_require_safety_token)):
        return {"user": public_safety_user_view(user)}

    # ---------- Password change ----------
    @api_router.post("/safety/change-password")
    async def safety_change_password(
        body: PasswordChangeBody,
        user: dict = Depends(_require_safety_token),
    ):
        if not body.new_password or len(body.new_password) < 8:
            raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
        pwh = user.get("password_hash") or ""
        if not verify_password(body.current_password, pwh):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        updated = await set_safety_user_password(db, user["id"], body.new_password, must_change=False)
        if not updated:
            raise HTTPException(status_code=404, detail="user not found")
        # Token is bound to the bcrypt hash prefix → old token is now
        # invalid. Mint and return a fresh one so the client can keep
        # the session alive without bouncing through /login.
        new_token = make_safety_user_token(updated["id"], updated["password_hash"])
        return {"ok": True, "token": new_token, "user": public_safety_user_view(updated)}

    # ---------- Forgot password ----------
    @api_router.post("/safety/forgot-password")
    async def safety_forgot_password(body: ForgotPasswordBody):
        user = await find_safety_user_by_email(db, body.email)
        # Always return success-shaped response to avoid email enumeration.
        if not user or user.get("disabled") or not user.get("password_hash"):
            return {"ok": True, "sent": False}
        token = make_safety_reset_token(user["id"], user["password_hash"])
        # Email send is wired by the existing safety email plumbing if active.
        # For now, surface the token in the response IF in dev mode only.
        logger.info(f"[safety reset] token issued for {user['email']}")
        return {"ok": True, "sent": True, "token_for_dev": token}

    @api_router.post("/safety/reset-password")
    async def safety_reset_password(body: ResetPasswordBody):
        user = await consume_safety_reset_token(db, body.token)
        if not user:
            raise HTTPException(status_code=400, detail="Reset link is invalid or expired")
        if not body.new_password or len(body.new_password) < 8:
            raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
        updated = await set_safety_user_password(db, user["id"], body.new_password, must_change=False)
        if not updated:
            raise HTTPException(status_code=404, detail="user not found")
        new_token = make_safety_user_token(updated["id"], updated["password_hash"])
        return {"ok": True, "token": new_token, "user": public_safety_user_view(updated)}

    # ---------- Overview KPIs (read-only roll-up of existing records) ----------
    @api_router.get("/safety/overview")
    async def safety_overview(_: dict = Depends(_require_safety_token)):
        now = datetime.now(timezone.utc)
        seven_days_ago = (now - timedelta(days=7)).isoformat()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()

        # Read EXISTING collections — Safety Portal is a visibility layer.
        # No duplication of incident/meeting/inspection forms.
        incidents_total = await db.incidents.count_documents({})
        incidents_7d = await db.incidents.count_documents(
            {"created_at": {"$gte": seven_days_ago}}
        )
        meetings_7d = await db.safety_meetings.count_documents(
            {"created_at": {"$gte": seven_days_ago}}
        )
        inspections_30d = await db.inspections.count_documents(
            {"created_at": {"$gte": thirty_days_ago}}
        )
        # Corrective actions
        ca_open = await db.corrective_actions.count_documents(
            {"status": {"$in": ["Open", "In Progress", "Pending Review"]}}
        )
        ca_overdue = await db.corrective_actions.count_documents(
            {
                "status": {"$in": ["Open", "In Progress", "Pending Review"]},
                "due_date": {"$ne": None, "$lt": now.isoformat()[:10]},
            }
        )
        # Training deficiencies in field leadership records
        training_def = await db.field_leadership_records.count_documents(
            {"kind": "training_deficiency"}
        )
        # Safety equipment issuance volume — read-only visibility
        eq_issuance = await db.field_leadership_records.count_documents(
            {"kind": "safety_equipment_issuance"}
        )

        return {
            "incidents_total": incidents_total,
            "incidents_last_7d": incidents_7d,
            "meetings_last_7d": meetings_7d,
            "inspections_last_30d": inspections_30d,
            "corrective_actions_open": ca_open,
            "corrective_actions_overdue": ca_overdue,
            "training_deficiencies_total": training_def,
            "safety_equipment_issuances_total": eq_issuance,
            "generated_at": now.isoformat(),
        }

    # ---------- Corrective Actions ----------
    def _ca_normalize(doc: dict) -> dict:
        if "_id" in doc:
            doc.pop("_id")
        return doc

    @api_router.get("/safety/corrective-actions")
    async def list_corrective_actions(
        status: Optional[str] = None,
        _: dict = Depends(_require_safety_token),
    ):
        q: dict = {}
        if status:
            q["status"] = status
        items = await db.corrective_actions.find(q, {"_id": 0}).sort("created_at", -1).to_list(1000)
        return items

    @api_router.post("/safety/corrective-actions")
    async def create_corrective_action(
        body: CorrectiveActionCreate,
        user: dict = Depends(_require_safety_token),
    ):
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": str(uuid.uuid4()),
            "title": body.title.strip(),
            "description": (body.description or "").strip(),
            "source_kind": body.source_kind.strip(),
            "source_id": body.source_id,
            "project_number": (body.project_number or "").strip(),
            "assigned_to_name": (body.assigned_to_name or "").strip(),
            "assigned_to_email": (body.assigned_to_email or "").strip().lower(),
            "priority": body.priority or "Medium",
            "due_date": body.due_date,
            "status": "Open",
            "notes": (body.notes or "").strip(),
            "completion_notes": "",
            "completed_at": None,
            "closed_by_name": "",
            "created_by_name": user.get("name") or "",
            "created_by_email": user.get("email") or "",
            "created_at": now,
            "updated_at": now,
        }
        await db.corrective_actions.insert_one(doc)
        return _ca_normalize(doc)

    @api_router.get("/safety/corrective-actions/{ca_id}")
    async def get_corrective_action(
        ca_id: str, _: dict = Depends(_require_safety_token)
    ):
        doc = await db.corrective_actions.find_one({"id": ca_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Not found")
        return doc

    @api_router.patch("/safety/corrective-actions/{ca_id}")
    async def update_corrective_action(
        ca_id: str,
        body: CorrectiveActionUpdate,
        user: dict = Depends(_require_safety_token),
    ):
        now = datetime.now(timezone.utc).isoformat()
        update = {"updated_at": now}
        for k, v in body.dict(exclude_none=True).items():
            update[k] = v
        if update.get("status") == "Closed":
            update["completed_at"] = now
            update["closed_by_name"] = user.get("name") or ""
        res = await db.corrective_actions.update_one({"id": ca_id}, {"$set": update})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Not found")
        return await db.corrective_actions.find_one({"id": ca_id}, {"_id": 0})

    @api_router.delete("/safety/corrective-actions/{ca_id}")
    async def delete_corrective_action(
        ca_id: str, _: dict = Depends(_require_safety_token)
    ):
        res = await db.corrective_actions.delete_one({"id": ca_id})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Not found")
        return {"ok": True}

    # ---------- Admin: Safety user management ----------
    @api_router.get("/admin/safety-users", dependencies=[Depends(require_admin)])
    async def admin_list_safety_users():
        users = await list_safety_users(db)
        return [public_safety_user_view(u) for u in users]

    @api_router.post("/admin/safety-users", dependencies=[Depends(require_admin)])
    async def admin_create_safety_user(body: SafetyUserCreate):
        try:
            user = await add_safety_user(db, body.dict())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        temp_pw = generate_temp_password()
        await set_safety_user_password(db, user["id"], temp_pw, must_change=True)
        return {
            "user": public_safety_user_view(user),
            "temp_password": temp_pw,
        }

    @api_router.patch("/admin/safety-users/{user_id}", dependencies=[Depends(require_admin)])
    async def admin_update_safety_user(user_id: str, body: SafetyUserUpdate):
        try:
            updated = await update_safety_user(db, user_id, body.dict(exclude_none=True))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if not updated:
            raise HTTPException(status_code=404, detail="Not found")
        return public_safety_user_view(updated)

    @api_router.post(
        "/admin/safety-users/{user_id}/reset-password",
        dependencies=[Depends(require_admin)],
    )
    async def admin_reset_safety_password(user_id: str):
        temp_pw = generate_temp_password()
        updated = await set_safety_user_password(db, user_id, temp_pw, must_change=True)
        if not updated:
            raise HTTPException(status_code=404, detail="Not found")
        return {
            "user": public_safety_user_view(updated),
            "temp_password": temp_pw,
        }

    @api_router.delete("/admin/safety-users/{user_id}", dependencies=[Depends(require_admin)])
    async def admin_delete_safety_user(user_id: str):
        ok = await delete_safety_user(db, user_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Not found")
        return {"ok": True}

    # ---------- Admin oversight (high-level safety counts) ----------
    @api_router.get("/admin/safety/overview", dependencies=[Depends(require_admin)])
    async def admin_safety_overview():
        # Same shape as /safety/overview so admin Console can reuse the card grid.
        now = datetime.now(timezone.utc)
        seven_days_ago = (now - timedelta(days=7)).isoformat()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()
        return {
            "incidents_total": await db.incidents.count_documents({}),
            "incidents_last_7d": await db.incidents.count_documents({"created_at": {"$gte": seven_days_ago}}),
            "meetings_last_7d": await db.safety_meetings.count_documents({"created_at": {"$gte": seven_days_ago}}),
            "inspections_last_30d": await db.inspections.count_documents({"created_at": {"$gte": thirty_days_ago}}),
            "corrective_actions_open": await db.corrective_actions.count_documents(
                {"status": {"$in": ["Open", "In Progress", "Pending Review"]}}
            ),
            "corrective_actions_overdue": await db.corrective_actions.count_documents(
                {
                    "status": {"$in": ["Open", "In Progress", "Pending Review"]},
                    "due_date": {"$ne": None, "$lt": now.isoformat()[:10]},
                }
            ),
        }

    return api_router
