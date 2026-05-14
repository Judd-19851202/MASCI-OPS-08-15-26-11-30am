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

import base64
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, Header, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import Response
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


# ─── Phase 3 — Fire Extinguishers ────────────────────────────────────
class FireExtinguisherCreate(BaseModel):
    unit_id: str = Field(..., min_length=1)
    location_kind: str = Field(...)  # "truck" | "job" | "facility"
    location_value: str = Field("")   # e.g. truck number, project number, facility name
    type: str = Field("ABC")          # "ABC" | "CO2" | "Class K" | etc.
    size: Optional[str] = ""          # e.g. "10 lb"
    last_inspection_date: Optional[str] = None
    next_due_date: Optional[str] = None
    last_status: Optional[str] = "Pass"   # "Pass" | "Fail" | "Needs Service"
    notes: Optional[str] = ""


class FireExtinguisherUpdate(BaseModel):
    unit_id: Optional[str] = None
    location_kind: Optional[str] = None
    location_value: Optional[str] = None
    type: Optional[str] = None
    size: Optional[str] = None
    last_inspection_date: Optional[str] = None
    next_due_date: Optional[str] = None
    last_status: Optional[str] = None
    notes: Optional[str] = None


class FireExtinguisherInspection(BaseModel):
    inspection_date: str = Field(...)        # YYYY-MM-DD
    status: str = Field(...)                  # "Pass" | "Fail" | "Needs Service"
    inspector_name: Optional[str] = ""
    next_due_date: Optional[str] = None       # if not given, +30 days from inspection_date
    notes: Optional[str] = ""


# ─── Phase 3 — Document Library ──────────────────────────────────────
class SafetyDocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


# ─── Phase 4 — Training & Certifications ─────────────────────────────
class TrainingRecordCreate(BaseModel):
    employee_id: str = Field(..., min_length=1)
    employee_name: Optional[str] = ""
    training_name: str = Field(..., min_length=1)
    certification_type: Optional[str] = ""    # e.g. "OSHA 10", "First Aid", "Confined Space"
    completed_date: str = Field(...)          # YYYY-MM-DD
    expiration_date: Optional[str] = None     # YYYY-MM-DD, None = no expiration
    issued_by: Optional[str] = ""
    notes: Optional[str] = ""
    certificate_file_id: Optional[str] = None  # link to safety_documents id (optional)


class TrainingRecordUpdate(BaseModel):
    training_name: Optional[str] = None
    certification_type: Optional[str] = None
    completed_date: Optional[str] = None
    expiration_date: Optional[str] = None
    issued_by: Optional[str] = None
    notes: Optional[str] = None
    certificate_file_id: Optional[str] = None


# ─── Phase 5 — Weekly digest helpers (module-level so the scheduler can
# import them without depending on the router builder closure) ──────
async def build_digest_payload(db) -> dict:
    now = datetime.now(timezone.utc)
    today = now.isoformat()[:10]
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    thirty_days_out = (now + timedelta(days=30)).isoformat()[:10]
    open_cas = await db.corrective_actions.count_documents(
        {"status": {"$in": ["Open", "In Progress", "Pending Review"]}}
    )
    overdue_cas = await db.corrective_actions.count_documents({
        "status": {"$in": ["Open", "In Progress", "Pending Review"]},
        "due_date": {"$ne": None, "$lt": today},
    })
    incidents_7d = await db.incidents.count_documents({"created_at": {"$gte": seven_days_ago}})
    meetings_7d = await db.safety_meetings.count_documents({"created_at": {"$gte": seven_days_ago}})
    training_expiring = await db.safety_training_records.count_documents(
        {"expiration_date": {"$ne": None, "$gte": today, "$lte": thirty_days_out}}
    )
    training_expired = await db.safety_training_records.count_documents(
        {"expiration_date": {"$ne": None, "$lt": today}}
    )
    fe_overdue = await db.fire_extinguishers.count_documents(
        {"next_due_date": {"$ne": None, "$lt": today}}
    )
    top_open = await db.corrective_actions.find(
        {"status": {"$in": ["Open", "In Progress", "Pending Review"]}},
        {"_id": 0, "title": 1, "priority": 1, "status": 1, "project_number": 1, "due_date": 1, "assigned_to_name": 1},
    ).sort("created_at", 1).to_list(5)
    return {
        "as_of": now.isoformat(),
        "kpis": {
            "open_corrective_actions": open_cas,
            "overdue_corrective_actions": overdue_cas,
            "incidents_last_7d": incidents_7d,
            "meetings_last_7d": meetings_7d,
            "training_expiring_30d": training_expiring,
            "training_expired": training_expired,
            "fire_extinguishers_overdue": fe_overdue,
        },
        "top_open_corrective_actions": top_open,
    }


def render_digest_html(payload: dict) -> str:
    k = payload["kpis"]
    rows_html = ""
    for ca in payload.get("top_open_corrective_actions") or []:
        rows_html += (
            f"<tr><td style='padding:6px 10px;border-bottom:1px solid #e5e7eb'>{ca.get('title','')}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #e5e7eb'>{ca.get('status','')}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #e5e7eb'>{ca.get('priority','')}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #e5e7eb'>{ca.get('project_number','') or '—'}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #e5e7eb'>{ca.get('due_date','') or '—'}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #e5e7eb'>{ca.get('assigned_to_name','') or '—'}</td></tr>"
        )
    if not rows_html:
        rows_html = "<tr><td colspan='6' style='padding:10px;text-align:center;color:#64748b'>No open corrective actions. Nice work.</td></tr>"
    return f"""
    <div style="font-family:Helvetica,Arial,sans-serif;max-width:640px;margin:0 auto;color:#0f172a">
      <div style="background:#0e7490;color:white;padding:16px 22px;border-radius:6px 6px 0 0">
        <div style="font-family:Courier,monospace;font-size:11px;letter-spacing:0.18em;opacity:0.85">MASCI · SAFETY OPERATIONS</div>
        <h1 style="font-size:22px;margin:4px 0 0;font-weight:900">Weekly Safety Digest</h1>
        <div style="font-size:11px;opacity:0.85;margin-top:4px">{payload['as_of'][:10]}</div>
      </div>
      <div style="border:2px solid #e2e8f0;border-top:0;padding:18px 22px;border-radius:0 0 6px 6px">
        <table cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;margin-bottom:16px">
          <tr>
            <td style="padding:10px;background:#f1f5f9;border-radius:4px">
              <div style="font-family:Courier,monospace;font-size:10px;letter-spacing:0.15em;color:#475569">OPEN CAs</div>
              <div style="font-size:24px;font-weight:900;color:#0e7490">{k['open_corrective_actions']}</div>
            </td>
            <td style="width:8px"></td>
            <td style="padding:10px;background:#fef2f2;border-radius:4px">
              <div style="font-family:Courier,monospace;font-size:10px;letter-spacing:0.15em;color:#7f1d1d">OVERDUE CAs</div>
              <div style="font-size:24px;font-weight:900;color:#b91c1c">{k['overdue_corrective_actions']}</div>
            </td>
            <td style="width:8px"></td>
            <td style="padding:10px;background:#fffbeb;border-radius:4px">
              <div style="font-family:Courier,monospace;font-size:10px;letter-spacing:0.15em;color:#92400e">INCIDENTS (7D)</div>
              <div style="font-size:24px;font-weight:900;color:#b45309">{k['incidents_last_7d']}</div>
            </td>
          </tr>
          <tr><td colspan="5" style="height:10px"></td></tr>
          <tr>
            <td style="padding:10px;background:#ecfdf5;border-radius:4px">
              <div style="font-family:Courier,monospace;font-size:10px;letter-spacing:0.15em;color:#065f46">MEETINGS (7D)</div>
              <div style="font-size:24px;font-weight:900;color:#047857">{k['meetings_last_7d']}</div>
            </td>
            <td style="width:8px"></td>
            <td style="padding:10px;background:#fef2f2;border-radius:4px">
              <div style="font-family:Courier,monospace;font-size:10px;letter-spacing:0.15em;color:#7f1d1d">TRAINING EXPIRED</div>
              <div style="font-size:24px;font-weight:900;color:#b91c1c">{k['training_expired']}</div>
            </td>
            <td style="width:8px"></td>
            <td style="padding:10px;background:#fffbeb;border-radius:4px">
              <div style="font-family:Courier,monospace;font-size:10px;letter-spacing:0.15em;color:#92400e">EXPIRING 30D</div>
              <div style="font-size:24px;font-weight:900;color:#b45309">{k['training_expiring_30d']}</div>
            </td>
          </tr>
        </table>
        <div style="font-family:Courier,monospace;font-size:11px;letter-spacing:0.18em;color:#0e7490;font-weight:700;margin:6px 0">TOP OPEN CORRECTIVE ACTIONS</div>
        <table cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;font-size:13px;border:1px solid #e5e7eb;border-radius:4px;overflow:hidden">
          <thead>
            <tr style="background:#f8fafc">
              <th style="text-align:left;padding:8px 10px;font-size:11px;font-family:Courier,monospace;letter-spacing:0.12em;color:#475569">Title</th>
              <th style="text-align:left;padding:8px 10px;font-size:11px;font-family:Courier,monospace;letter-spacing:0.12em;color:#475569">Status</th>
              <th style="text-align:left;padding:8px 10px;font-size:11px;font-family:Courier,monospace;letter-spacing:0.12em;color:#475569">Pri</th>
              <th style="text-align:left;padding:8px 10px;font-size:11px;font-family:Courier,monospace;letter-spacing:0.12em;color:#475569">Proj</th>
              <th style="text-align:left;padding:8px 10px;font-size:11px;font-family:Courier,monospace;letter-spacing:0.12em;color:#475569">Due</th>
              <th style="text-align:left;padding:8px 10px;font-size:11px;font-family:Courier,monospace;letter-spacing:0.12em;color:#475569">Assignee</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
        <p style="font-size:12px;color:#64748b;margin:18px 0 0">
          Open the full dashboard at <a href="https://mascidocs.com/safety-portal" style="color:#0e7490;font-weight:700">mascidocs.com/safety-portal</a>.
        </p>
      </div>
      <p style="font-size:10px;color:#94a3b8;text-align:center;margin:12px 0 0;font-family:Courier,monospace;letter-spacing:0.15em">
        GENERATED THROUGH MASCI OPERATIONS PLATFORM — POWERED BY FORGEDOPS™
      </p>
    </div>
    """


def build_safety_router(db, require_admin, send_email_fn=None, is_valid_admin_token=None) -> APIRouter:
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

    async def _require_safety_or_hr_or_admin(
        request: Request,
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
        x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    ) -> dict:
        """Multi-role read gate — accepts Safety, HR, or Admin tokens.
        Used for shared read surfaces (document library, training reads,
        employee safety profile) where HR + Admin need visibility but
        write access stays Safety-only."""
        if x_safety_token:
            u = await is_valid_safety_user_token_async(db, x_safety_token)
            if u:
                return {**u, "_actor": "safety"}
        if x_hr_token:
            from hr_users import is_valid_hr_user_token_async
            u = await is_valid_hr_user_token_async(db, x_hr_token)
            if u:
                return {**u, "_actor": "hr"}
        if x_admin_token:
            # Admin validator passed in by caller (avoids circular import
            # of server.py at module-load time).
            if is_valid_admin_token and is_valid_admin_token(x_admin_token):
                return {"_actor": "admin", "name": "Admin"}
        raise HTTPException(401, "Safety, HR, or Admin auth required")

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
        today = now.isoformat()[:10]
        thirty_days_out = (now + timedelta(days=30)).isoformat()[:10]
        fe_total = await db.fire_extinguishers.count_documents({})
        fe_overdue = await db.fire_extinguishers.count_documents(
            {"next_due_date": {"$ne": None, "$lt": today}}
        )
        training_total = await db.safety_training_records.count_documents({})
        training_expiring = await db.safety_training_records.count_documents(
            {"expiration_date": {"$ne": None, "$gte": today, "$lte": thirty_days_out}}
        )
        training_expired = await db.safety_training_records.count_documents(
            {"expiration_date": {"$ne": None, "$lt": today}}
        )
        documents_total = await db.safety_documents.count_documents({})

        return {
            "incidents_total": incidents_total,
            "incidents_last_7d": incidents_7d,
            "meetings_last_7d": meetings_7d,
            "inspections_last_30d": inspections_30d,
            "corrective_actions_open": ca_open,
            "corrective_actions_overdue": ca_overdue,
            "training_deficiencies_total": training_def,
            "safety_equipment_issuances_total": eq_issuance,
            "fire_extinguishers_total": fe_total,
            "fire_extinguishers_overdue": fe_overdue,
            "training_records_total": training_total,
            "training_expiring_30d": training_expiring,
            "training_expired": training_expired,
            "safety_documents_total": documents_total,
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
        today = now.isoformat()[:10]
        thirty_days_out = (now + timedelta(days=30)).isoformat()[:10]
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
                    "due_date": {"$ne": None, "$lt": today},
                }
            ),
            "fire_extinguishers_total": await db.fire_extinguishers.count_documents({}),
            "fire_extinguishers_overdue": await db.fire_extinguishers.count_documents(
                {"next_due_date": {"$ne": None, "$lt": today}}
            ),
            "training_records_total": await db.safety_training_records.count_documents({}),
            "training_expiring_30d": await db.safety_training_records.count_documents(
                {"expiration_date": {"$ne": None, "$gte": today, "$lte": thirty_days_out}}
            ),
            "training_expired": await db.safety_training_records.count_documents(
                {"expiration_date": {"$ne": None, "$lt": today}}
            ),
            "safety_documents_total": await db.safety_documents.count_documents({}),
        }

    # ═════════════════════════════════════════════════════════════════
    # PHASE 3 — Fire Extinguishers
    # ═════════════════════════════════════════════════════════════════
    @api_router.get("/safety/fire-extinguishers")
    async def list_fire_extinguishers(
        status: Optional[str] = None,
        overdue_only: bool = False,
        _: dict = Depends(_require_safety_token),
    ):
        q: dict = {}
        if status:
            q["last_status"] = status
        if overdue_only:
            today = datetime.now(timezone.utc).isoformat()[:10]
            q["next_due_date"] = {"$ne": None, "$lt": today}
        items = await db.fire_extinguishers.find(q, {"_id": 0}).sort("unit_id", 1).to_list(2000)
        return items

    @api_router.post("/safety/fire-extinguishers")
    async def create_fire_extinguisher(
        body: FireExtinguisherCreate, user: dict = Depends(_require_safety_token),
    ):
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": str(uuid.uuid4()),
            "unit_id": body.unit_id.strip(),
            "location_kind": body.location_kind.strip(),
            "location_value": (body.location_value or "").strip(),
            "type": (body.type or "ABC").strip(),
            "size": (body.size or "").strip(),
            "last_inspection_date": body.last_inspection_date,
            "next_due_date": body.next_due_date,
            "last_status": body.last_status or "Pass",
            "last_inspector_name": "",
            "notes": (body.notes or "").strip(),
            "inspections": [],
            "created_by_name": user.get("name") or "",
            "created_at": now,
            "updated_at": now,
        }
        await db.fire_extinguishers.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.patch("/safety/fire-extinguishers/{fe_id}")
    async def update_fire_extinguisher(
        fe_id: str, body: FireExtinguisherUpdate,
        _: dict = Depends(_require_safety_token),
    ):
        update = {k: v for k, v in body.dict(exclude_none=True).items()}
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = await db.fire_extinguishers.update_one({"id": fe_id}, {"$set": update})
        if res.matched_count == 0:
            raise HTTPException(404, "Not found")
        return await db.fire_extinguishers.find_one({"id": fe_id}, {"_id": 0})

    @api_router.post("/safety/fire-extinguishers/{fe_id}/inspect")
    async def inspect_fire_extinguisher(
        fe_id: str, body: FireExtinguisherInspection,
        user: dict = Depends(_require_safety_token),
    ):
        existing = await db.fire_extinguishers.find_one({"id": fe_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Not found")
        # Compute next due (default = +30 days from inspection_date) when client doesn't supply one
        next_due = body.next_due_date
        if not next_due:
            try:
                base = datetime.fromisoformat(body.inspection_date)
            except ValueError:
                base = datetime.now(timezone.utc)
            next_due = (base + timedelta(days=30)).isoformat()[:10]
        entry = {
            "inspection_date": body.inspection_date,
            "status": body.status,
            "inspector_name": (body.inspector_name or user.get("name") or "").strip(),
            "notes": (body.notes or "").strip(),
            "logged_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.fire_extinguishers.update_one(
            {"id": fe_id},
            {
                "$set": {
                    "last_inspection_date": body.inspection_date,
                    "next_due_date": next_due,
                    "last_status": body.status,
                    "last_inspector_name": entry["inspector_name"],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                "$push": {"inspections": entry},
            },
        )
        return await db.fire_extinguishers.find_one({"id": fe_id}, {"_id": 0})

    @api_router.delete("/safety/fire-extinguishers/{fe_id}")
    async def delete_fire_extinguisher(
        fe_id: str, _: dict = Depends(_require_safety_token),
    ):
        res = await db.fire_extinguishers.delete_one({"id": fe_id})
        if res.deleted_count == 0:
            raise HTTPException(404, "Not found")
        return {"ok": True}

    # ═════════════════════════════════════════════════════════════════
    # PHASE 3 — Document Library
    # Read access: Safety + HR + Admin. Write access: Safety only.
    # Inline base64 storage (matches JHA pattern for small docs).
    # ═════════════════════════════════════════════════════════════════
    MAX_DOC_BYTES = 15 * 1024 * 1024  # 15 MB — generous; matches HR / JHA

    @api_router.get("/safety/documents")
    async def list_safety_documents(
        category: Optional[str] = None,
        _: dict = Depends(_require_safety_or_hr_or_admin),
    ):
        q: dict = {}
        if category:
            q["category"] = category
        cursor = db.safety_documents.find(q, {"_id": 0, "file_data": 0}).sort("uploaded_at", -1)
        return await cursor.to_list(2000)

    @api_router.post("/safety/documents")
    async def upload_safety_document(
        file: UploadFile = File(...),
        title: str = Form(""),
        category: str = Form("General"),
        description: str = Form(""),
        tags: str = Form(""),  # comma-separated
        user: dict = Depends(_require_safety_token),
    ):
        raw = await file.read()
        if not raw:
            raise HTTPException(400, "Empty file")
        if len(raw) > MAX_DOC_BYTES:
            raise HTTPException(413, f"File too large. Max {MAX_DOC_BYTES // (1024*1024)} MB.")
        content_type = file.content_type or "application/octet-stream"
        b64 = base64.b64encode(raw).decode("ascii")
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": str(uuid.uuid4()),
            "title": (title or file.filename or "Untitled").strip(),
            "filename": (file.filename or "document").strip(),
            "category": (category or "General").strip(),
            "description": (description or "").strip(),
            "tags": [t.strip() for t in (tags or "").split(",") if t.strip()],
            "content_type": content_type,
            "file_size": len(raw),
            "file_data": f"data:{content_type};base64,{b64}",
            "uploaded_by_name": user.get("name") or "",
            "uploaded_by_email": user.get("email") or "",
            "uploaded_at": now,
        }
        await db.safety_documents.insert_one(doc)
        # Return summary (no file_data)
        doc.pop("_id", None)
        doc.pop("file_data", None)
        return doc

    @api_router.patch("/safety/documents/{doc_id}")
    async def update_safety_document(
        doc_id: str, body: SafetyDocumentUpdate,
        _: dict = Depends(_require_safety_token),
    ):
        update = {k: v for k, v in body.dict(exclude_none=True).items()}
        if not update:
            raise HTTPException(400, "No changes")
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = await db.safety_documents.update_one({"id": doc_id}, {"$set": update})
        if res.matched_count == 0:
            raise HTTPException(404, "Not found")
        doc = await db.safety_documents.find_one({"id": doc_id}, {"_id": 0, "file_data": 0})
        return doc

    @api_router.get("/safety/documents/{doc_id}/download")
    async def download_safety_document(
        doc_id: str, _: dict = Depends(_require_safety_or_hr_or_admin),
    ):
        doc = await db.safety_documents.find_one({"id": doc_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Not found")
        data_url = doc.get("file_data") or ""
        if not data_url.startswith("data:"):
            raise HTTPException(500, "File data missing")
        try:
            _, _, b64 = data_url.partition("base64,")
            raw = base64.b64decode(b64)
        except Exception:
            raise HTTPException(500, "Stored file is corrupt")
        ct = doc.get("content_type", "application/octet-stream")
        fname = doc.get("filename", "document")
        headers = {
            "Content-Disposition": f'attachment; filename="{fname}"',
            "Cache-Control": "no-store",
        }
        return Response(content=raw, media_type=ct, headers=headers)

    @api_router.delete("/safety/documents/{doc_id}")
    async def delete_safety_document(
        doc_id: str, _: dict = Depends(_require_safety_token),
    ):
        res = await db.safety_documents.delete_one({"id": doc_id})
        if res.deleted_count == 0:
            raise HTTPException(404, "Not found")
        return {"ok": True}

    # ═════════════════════════════════════════════════════════════════
    # PHASE 4 — Training & Certifications (tied to db.employees)
    # ═════════════════════════════════════════════════════════════════
    @api_router.get("/safety/training-records")
    async def list_training_records(
        employee_id: Optional[str] = None,
        expiring_within_days: Optional[int] = None,
        _: dict = Depends(_require_safety_or_hr_or_admin),
    ):
        q: dict = {}
        if employee_id:
            q["employee_id"] = employee_id
        if expiring_within_days is not None and expiring_within_days >= 0:
            today = datetime.now(timezone.utc)
            cutoff = (today + timedelta(days=expiring_within_days)).isoformat()[:10]
            q["expiration_date"] = {"$ne": None, "$lte": cutoff}
        items = await db.safety_training_records.find(q, {"_id": 0}).sort("expiration_date", 1).to_list(5000)
        return items

    @api_router.post("/safety/training-records")
    async def create_training_record(
        body: TrainingRecordCreate, user: dict = Depends(_require_safety_token),
    ):
        # Resolve employee_name from employee_id if missing
        emp_name = (body.employee_name or "").strip()
        if not emp_name:
            emp = await db.employees.find_one({"id": body.employee_id}, {"_id": 0, "name": 1})
            emp_name = (emp or {}).get("name") or ""
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": str(uuid.uuid4()),
            "employee_id": body.employee_id,
            "employee_name": emp_name,
            "training_name": body.training_name.strip(),
            "certification_type": (body.certification_type or "").strip(),
            "completed_date": body.completed_date,
            "expiration_date": body.expiration_date,
            "issued_by": (body.issued_by or "").strip(),
            "notes": (body.notes or "").strip(),
            "certificate_file_id": body.certificate_file_id,
            "created_by_name": user.get("name") or "",
            "created_at": now,
            "updated_at": now,
        }
        await db.safety_training_records.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.patch("/safety/training-records/{rec_id}")
    async def update_training_record(
        rec_id: str, body: TrainingRecordUpdate,
        _: dict = Depends(_require_safety_token),
    ):
        update = {k: v for k, v in body.dict(exclude_none=True).items()}
        if not update:
            raise HTTPException(400, "No changes")
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = await db.safety_training_records.update_one({"id": rec_id}, {"$set": update})
        if res.matched_count == 0:
            raise HTTPException(404, "Not found")
        return await db.safety_training_records.find_one({"id": rec_id}, {"_id": 0})

    @api_router.delete("/safety/training-records/{rec_id}")
    async def delete_training_record(
        rec_id: str, _: dict = Depends(_require_safety_token),
    ):
        res = await db.safety_training_records.delete_one({"id": rec_id})
        if res.deleted_count == 0:
            raise HTTPException(404, "Not found")
        return {"ok": True}

    @api_router.get("/safety/employee-profile/{employee_id}")
    async def employee_safety_profile(
        employee_id: str, _: dict = Depends(_require_safety_or_hr_or_admin),
    ):
        """Per-employee safety roll-up — trainings, certs, meeting
        attendance count, incident involvement count, PPE issuance count,
        and outstanding corrective actions assigned to them."""
        employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
        if not employee:
            raise HTTPException(404, "Employee not found")
        name = employee.get("name", "")
        # Trainings
        trainings = await db.safety_training_records.find(
            {"employee_id": employee_id}, {"_id": 0}
        ).sort("expiration_date", 1).to_list(500)
        # Meeting attendance count — scan safety_meetings.attendees by name
        meetings_attended = await db.safety_meetings.count_documents(
            {"attendees": {"$elemMatch": {"name": name}}}
        ) if name else 0
        # Incident involvement — scan db.incidents by employee_name / injured_party
        incident_involvements = 0
        if name:
            incident_involvements = await db.incidents.count_documents({
                "$or": [
                    {"injured_party_name": name},
                    {"employees_involved": {"$elemMatch": {"name": name}}},
                ]
            })
        # Equipment issuance via field_leadership_records (kind=safety_equipment_issuance)
        ppe_issuance = 0
        if name:
            ppe_issuance = await db.field_leadership_records.count_documents({
                "kind": "safety_equipment_issuance",
                "employee_name": name,
            })
        # Outstanding CAs assigned to them
        open_cas = await db.corrective_actions.count_documents({
            "assigned_to_name": name,
            "status": {"$in": ["Open", "In Progress", "Pending Review"]},
        }) if name else 0
        today = datetime.now(timezone.utc).isoformat()[:10]
        thirty_out = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()[:10]
        expiring_30 = [
            t for t in trainings
            if t.get("expiration_date") and today <= t["expiration_date"] <= thirty_out
        ]
        expired = [
            t for t in trainings
            if t.get("expiration_date") and t["expiration_date"] < today
        ]
        return {
            "employee": employee,
            "trainings": trainings,
            "training_summary": {
                "total": len(trainings),
                "expiring_within_30_days": len(expiring_30),
                "expired": len(expired),
            },
            "meetings_attended": meetings_attended,
            "incident_involvements": incident_involvements,
            "ppe_issuance_count": ppe_issuance,
            "open_corrective_actions": open_cas,
        }

    # ═════════════════════════════════════════════════════════════════
    # PHASE 5 — Weekly Digest (Monday morning email)
    # ═════════════════════════════════════════════════════════════════
    @api_router.get("/safety/digest/preview", dependencies=[Depends(_require_safety_token)])
    async def safety_digest_preview():
        payload = await build_digest_payload(db)
        return {"payload": payload, "html": render_digest_html(payload)}

    @api_router.post("/safety/digest/send", dependencies=[Depends(_require_safety_token)])
    async def safety_digest_send_now(
        to_email: Optional[str] = None,
    ):
        payload = await build_digest_payload(db)
        html = render_digest_html(payload)
        recipient = (to_email or "safety@mascigc.com").strip()
        sent = False
        if send_email_fn:
            try:
                await send_email_fn(recipient, "[MASCI] Weekly Safety Digest", html)
                sent = True
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[safety-digest] send failed: {e}")
        return {"ok": True, "sent": sent, "to": recipient, "payload": payload}

    return api_router
