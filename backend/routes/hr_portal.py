"""
hr_portal.py — HR Portal (iter71)
================================
Self-contained portal mirroring the Shop/PM patterns. HR users get
read-only visibility into Field Leadership records, employee
accountability, training records, and Daily-Report-derived employee
hours. They are EXPLICITLY blocked from PM/Shop/Admin/Financial
surfaces.

Endpoints (under /api):

PUBLIC (with X-HR-Token):
  POST   /hr/login                         — email+password → token
  POST   /hr/change-password               — first login or admin reset
  POST   /hr/forgot-password               — issue reset email
  POST   /hr/reset/{token}                 — consume reset token
  GET    /hr/me                            — current HR user
  GET    /hr/field-leadership              — read-only FL records list
  GET    /hr/field-leadership/{id}         — read single FL record
  GET    /hr/field-leadership/{id}/pdf     — PDF (uses existing renderer)
  GET    /hr/employee-accountability       — search by employee name
  GET    /hr/time-verification             — supervisor-reported hours
                                              from Daily Reports
  GET    /hr/training-records              — training_track_records

ADMIN (X-Admin-Token):
  GET    /admin/hr-users                   — roster
  POST   /admin/hr-users                   — create + temp password + email
  PATCH  /admin/hr-users/{id}              — edit fields
  POST   /admin/hr-users/{id}/reset-password — issue new temp pw + email
  DELETE /admin/hr-users/{id}              — remove
"""
from __future__ import annotations

import logging
import os
import re
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

import hr_users
from branded_portal_emails import render_portal_email
from hr_users import (
    add_hr_user, delete_hr_user, find_hr_user_by_email,
    generate_temp_password, hash_password, is_valid_hr_user_token_async,
    list_hr_users, make_hr_user_token, public_hr_user_view, set_hr_user_password,
    stamp_hr_login, update_hr_user, verify_password,
    make_hr_reset_token, consume_hr_reset_token,
)

logger = logging.getLogger(__name__)


class LoginPayload(BaseModel):
    email: str
    password: str


class ChangePasswordPayload(BaseModel):
    current_password: Optional[str] = None
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordPayload(BaseModel):
    email: str


class ResetPasswordPayload(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class HRUserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=200)
    phone: Optional[str] = ""
    role: str = "HR Coordinator"
    delivery: str = Field(default="email")  # email | screen | custom
    custom_password: Optional[str] = None


class HRUserPatch(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    disabled: Optional[bool] = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _client_ip(req: Request) -> str:
    try:
        fwd = req.headers.get("x-forwarded-for") or req.headers.get("x-real-ip")
        if fwd:
            return fwd.split(",")[0].strip()
        return req.client.host if req.client else ""
    except Exception:
        return ""


def build_hr_portal_router(db, require_admin_dep: Callable, send_email_fn: Optional[Callable] = None, directory_admin_minter: Optional[Callable] = None, require_safety_or_hr_or_admin_dep: Optional[Callable] = None) -> APIRouter:
    """Assemble the HR portal router. `db` = motor db; `require_admin_dep`
    = the FastAPI admin-only dependency from server.py; `send_email_fn`
    = optional `async (to, subject, html) -> None` for credential
    delivery — falls back to log-only when not provided.

    iter346-B · `directory_admin_minter` (optional) enables the universal
    super-admin login fallback: if native HR login fails and the email
    belongs to a `user_directory` row with the `admin` portal grant +
    correct master password, mint an admin token (kind:"admin"). Same
    pattern that iter344 introduced on the FL portal — extended here so
    super-admin can sign in via any portal login screen."""
    router = APIRouter(prefix="/api", tags=["hr-portal"])

    # ─── Shared accountability gate (iter353c) ───────────────────────
    # Accepts HR, Safety, or Admin tokens. Either injected by server.py
    # (preferred — uses the same minter as the safety portal) or built
    # locally so the router stays self-contained for tests.
    if require_safety_or_hr_or_admin_dep is not None:
        require_safety_or_hr_or_admin = require_safety_or_hr_or_admin_dep
    else:
        from routes.safety_portal._deps import make_require_safety_or_hr_or_admin  # noqa: PLC0415
        require_safety_or_hr_or_admin = make_require_safety_or_hr_or_admin(db)

    # ─── HR token resolver (used by every HR endpoint) ───────────────
    async def require_hr_user(
        x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),
    ) -> Dict[str, Any]:
        if not x_hr_token:
            raise HTTPException(401, "HR login required")
        user = await is_valid_hr_user_token_async(db, x_hr_token)
        if not user:
            raise HTTPException(401, "HR session expired or invalid")
        return {**user, "_actor_kind": "hr_user"}

    # ─────────────────────────────────────────────────────────────────
    # AUTH endpoints
    # ─────────────────────────────────────────────────────────────────
    @router.post("/hr/login")
    async def hr_login(payload: LoginPayload, request: Request):
        email = (payload.email or "").strip().lower()
        if not email or not payload.password:
            raise HTTPException(400, "email and password required")
        user = await find_hr_user_by_email(db, email)
        # ── Path 1 · per-user HR identity ────────────────────────────
        if user and not user.get("disabled") and user.get("is_active", True):
            pwh = user.get("password_hash")
            if pwh and verify_password(payload.password, pwh):
                token = make_hr_user_token(user["id"], pwh)
                await stamp_hr_login(db, user["id"], _client_ip(request))
                try:
                    from session_timeout import reset_session_activity
                    await reset_session_activity(
                        db, token, "ADMIN_HR",
                        user_id=user.get("id"),
                        email=user.get("email"),
                        actor_label="hr",
                        ip=_client_ip(request),
                        user_agent=request.headers.get("user-agent") or "",
                    )
                except Exception:  # noqa: BLE001
                    pass
                return {
                    "ok": True,
                    "token": token,
                    "kind": "hr",
                    "user": public_hr_user_view(user),
                    "must_change_password": bool(user.get("must_change_password")),
                }
        # ── Path 2 · iter346-B · universal super-admin fallback ──────
        # If native HR login didn't authenticate, check the master
        # `user_directory`. A user with the `admin` portal grant whose
        # master password verifies is signed in as Admin (same admin
        # token /api/admin/* routes accept). Only `admin` grant unlocks
        # the fallback — non-admin directory users still get 401.
        if directory_admin_minter is not None:
            try:
                import user_directory as _ud  # noqa: WPS433
                row = await _ud.authenticate(db, email=email, password=payload.password)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"hr_login directory fallback error: {e}")
                row = None
            if row and not row.get("disabled") and "admin" in (row.get("portals") or []):
                admin_tok = directory_admin_minter(row)
                if admin_tok:
                    try:
                        from session_timeout import reset_session_activity
                        await reset_session_activity(
                            db, admin_tok, "ADMIN_HR",
                            user_id=row.get("id"), email=row.get("email"),
                            actor_label="admin_via_hr",
                            ip=_client_ip(request),
                            user_agent=request.headers.get("user-agent") or "",
                        )
                    except Exception:  # noqa: BLE001
                        pass
                    return {
                        "ok": True,
                        "token": admin_tok,
                        "kind": "admin",
                        "user": _ud.public_view(row),
                        "must_change_password": False,
                    }
        raise HTTPException(401, "Invalid email or password")

    @router.post("/hr/change-password")
    async def hr_change_password(payload: ChangePasswordPayload, actor=Depends(require_hr_user)):
        # If a current_password is supplied, validate. Otherwise trust
        # the bearer token (admin just reset; user must change now).
        pwh = actor.get("password_hash") or ""
        if payload.current_password:
            if not pwh or not verify_password(payload.current_password, pwh):
                raise HTTPException(401, "Current password is incorrect")
        updated = await set_hr_user_password(db, actor["id"], payload.new_password, must_change=False)
        if not updated:
            raise HTTPException(404, "user not found")
        new_token = make_hr_user_token(updated["id"], updated["password_hash"])
        return {"ok": True, "token": new_token, "user": public_hr_user_view(updated)}

    @router.post("/hr/forgot-password")
    async def hr_forgot_password(payload: ForgotPasswordPayload):
        # Always return ok=True to avoid leaking valid email enumeration.
        email = (payload.email or "").strip().lower()
        if email:
            user = await find_hr_user_by_email(db, email)
            if user and not user.get("disabled") and user.get("password_hash"):
                token = make_hr_reset_token(user["id"], user["password_hash"])
                base = os.environ.get("PUBLIC_APP_URL", "https://mascidocs.com").rstrip("/")
                reset_url = f"{base}/hr/reset/{token}"
                if send_email_fn:
                    try:
                        body_html = (
                            f"<p style='margin:0 0 12px'>Hi {user.get('name')},</p>"
                            f"<p style='margin:0 0 12px'>We received a request to reset your MASCI HR Portal password. "
                            f"Click the button below to choose a new one. <strong>The link expires in 30 minutes.</strong></p>"
                            f"<p style='margin:18px 0 6px'>"
                            f"<a href='{reset_url}' style='display:inline-block;padding:11px 22px;background:#7e22ce;color:#fff;text-decoration:none;font-weight:700;border-radius:4px;font-size:13px'>Reset password</a>"
                            f"</p>"
                            f"<p style='margin:12px 0 0;font-size:12px;color:#475569'>"
                            f"Or paste this URL into your browser:</p>"
                            f"<p style='margin:4px 0 0;font-family:Courier New,monospace;font-size:11px;color:#475569;word-break:break-all'>{reset_url}</p>"
                            f"<p style='margin:18px 0 0;font-size:12px;color:#94a3b8'>If you didn't request this, you can safely ignore this email.</p>"
                        )
                        html = render_portal_email(
                            portal="HR",
                            headline="Reset your password",
                            body_inner_html=body_html,
                        )
                        await send_email_fn(user["email"], "[MASCI] Reset your HR Portal password", html)
                    except Exception as e:  # noqa: BLE001
                        logger.warning(f"hr forgot-password email failed: {e}")
                else:
                    logger.info(f"[HR reset] {user['email']} → {reset_url}")
        return {"ok": True}

    @router.post("/hr/reset/{token}")
    async def hr_consume_reset(token: str, payload: ResetPasswordPayload):
        user = await consume_hr_reset_token(db, token)
        if not user:
            raise HTTPException(400, "Reset link is invalid or expired")
        updated = await set_hr_user_password(db, user["id"], payload.new_password, must_change=False)
        new_token = make_hr_user_token(updated["id"], updated["password_hash"])
        return {"ok": True, "token": new_token, "user": public_hr_user_view(updated)}

    @router.get("/hr/me")
    async def hr_me(actor=Depends(require_hr_user)):
        return {"ok": True, "user": public_hr_user_view(actor)}

    # ─────────────────────────────────────────────────────────────────
    # FIELD LEADERSHIP — read-only access for HR.
    # We delegate the heavy lifting to the existing field_leadership
    # router collections directly. HR is read-only; no POST/PATCH/DELETE.
    # ─────────────────────────────────────────────────────────────────
    @router.get("/hr/field-leadership")
    async def hr_list_fl(
        actor=Depends(require_hr_user),
        kind: Optional[str] = None,
        q: Optional[str] = None,
        project_number: Optional[str] = None,
        limit: int = 200,
    ):
        query: Dict[str, Any] = {}
        if kind:
            query["kind"] = kind
        else:
            # Iter103 — Time Off Requests have their own dedicated dashboard at
            # /hr/time-off. Exclude them from the generic FL records list so
            # they don't appear in two places.
            query["kind"] = {"$ne": "time_off_request"}
        if project_number:
            query["project_number"] = project_number
        if q:
            needle = q.strip()
            query["$or"] = [
                {"employee_name": {"$regex": needle, "$options": "i"}},
                {"supervisor_name": {"$regex": needle, "$options": "i"}},
                {"project_number": {"$regex": needle, "$options": "i"}},
                {"project_name": {"$regex": needle, "$options": "i"}},
            ]
        out = []
        cursor = db.field_leadership_records.find(query, {"_id": 0}).sort("occurred_at", -1).limit(min(limit, 500))
        async for d in cursor:
            out.append(d)
        return {"ok": True, "items": out, "count": len(out)}

    @router.get("/hr/field-leadership/{record_id}")
    async def hr_get_fl(record_id: str, actor=Depends(require_hr_user)):
        d = await db.field_leadership_records.find_one({"id": record_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "record not found")
        return d

    @router.get("/hr/field-leadership/{record_id}/pdf")
    async def hr_fl_pdf(record_id: str, actor=Depends(require_hr_user)):
        from fastapi.responses import Response
        d = await db.field_leadership_records.find_one({"id": record_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "record not found")
        try:
            # iter331 · pre-deploy hot-fix · offload sync PDF render to a
            # thread pool so the FastAPI event loop stays responsive while
            # the render runs. Production worker observed at 15-20s for a
            # single FL PDF on cold-start; blocking the loop that long
            # cascades into HTTP 520 (Cloudflare) for every other /api/*
            # request hitting the same worker. asyncio.to_thread matches
            # the pattern already used by safety_forms PDF endpoints.
            from field_leadership_pdf import render_field_leadership_pdf
            pdf = await asyncio.to_thread(render_field_leadership_pdf, d)
        except Exception as e:
            raise HTTPException(500, f"PDF render failed: {e}")
        title_seg = (d.get("employee_name") or d.get("kind") or "record")[:40]
        safe = "".join(c if c.isalnum() else "_" for c in title_seg).strip("_") or "record"
        filename = f"MASCI_FL_{safe}_{record_id[:8]}.pdf"
        return Response(content=pdf, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    # ─────────────────────────────────────────────────────────────────
    # iter332 · HR READ-ONLY DAILY REPORTS REVIEW
    # ─────────────────────────────────────────────────────────────────
    # HR needs visibility into daily reports for payroll cross-checks,
    # employee labor verification, and subcontractor/vendor attendance —
    # WITHOUT being granted PM scope, edit/delete/submit/email, or
    # approval rights. Read-only namespace under /hr/* mirrors the
    # /hr/field-leadership pattern. Filters: date_from · date_to ·
    # project · employee · subcontractor · vendor · report_number.
    @router.get("/hr/daily-reports")
    async def hr_list_daily_reports(
        actor=Depends(require_hr_user),
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        project: Optional[str] = None,
        employee: Optional[str] = None,
        subcontractor: Optional[str] = None,
        vendor: Optional[str] = None,
        report_number: Optional[str] = None,
        limit: int = 200,
    ):
        match: Dict[str, Any] = {}
        # Date range — daily reports store ISO date in `report_date`.
        if date_from or date_to:
            rng: Dict[str, Any] = {}
            if date_from:
                rng["$gte"] = date_from
            if date_to:
                rng["$lte"] = date_to
            match["report_date"] = rng
        if project:
            needle = project.strip()
            match["$or"] = [
                {"project_name": {"$regex": needle, "$options": "i"}},
                {"project_number": {"$regex": needle, "$options": "i"}},
            ]
        if report_number:
            match["report_number"] = {"$regex": report_number.strip(), "$options": "i"}
        if employee:
            # Employee names are nested inside masci_crews[].members[].name
            # — match if any crew member's name contains the needle.
            match["masci_crews.members.name"] = {"$regex": employee.strip(), "$options": "i"}
        if subcontractor:
            match["subcontractors.name"] = {"$regex": subcontractor.strip(), "$options": "i"}
        if vendor:
            match["visitors.name"] = {"$regex": vendor.strip(), "$options": "i"}

        pipeline = [
            {"$match": match},
            {"$sort": {"report_date": -1, "created_at": -1}},
            {"$limit": min(limit, 500)},
            {"$project": {
                "_id": 0, "id": 1, "project_name": 1, "project_number": 1,
                "report_number": 1, "report_date": 1, "prepared_by": 1,
                "location": 1, "weather_summary": 1, "created_at": 1,
                "photo_count":   {"$size": {"$ifNull": ["$photos", []]}},
                "crew_count":    {"$size": {"$ifNull": ["$masci_crews", []]}},
                "sub_count":     {"$size": {"$ifNull": ["$subcontractors", []]}},
                "visitor_count": {"$size": {"$ifNull": ["$visitors", []]}},
            }},
        ]
        items = await db.daily_reports.aggregate(pipeline).to_list(500)
        return {"ok": True, "items": items, "count": len(items)}

    @router.get("/hr/daily-reports/{report_id}")
    async def hr_get_daily_report(report_id: str, actor=Depends(require_hr_user)):
        doc = await db.daily_reports.find_one({"id": report_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "daily report not found")
        # Read-only view — return the document as-is so HR can see labor
        # crews, subcontractor names, vendor visits, weather, photos, and
        # all narrative fields the PM authored. No edit affordance.
        return doc

    # ─────────────────────────────────────────────────────────────────
    # EMPLOYEE ACCOUNTABILITY — search by name → consolidated record set
    # ─────────────────────────────────────────────────────────────────
    @router.get("/hr/employee-accountability")
    async def hr_employee_accountability(
        actor=Depends(require_hr_user),
        employee: str = Query(default="", min_length=2),
    ):
        name = (employee or "").strip()
        if not name:
            raise HTTPException(400, "employee name required")
        rx = {"$regex": name, "$options": "i"}

        fl_records: List[Dict[str, Any]] = []
        async for d in db.field_leadership_records.find({"employee_name": rx}, {"_id": 0}).sort("occurred_at", -1).limit(500):
            fl_records.append(d)

        # Outstanding equipment: every equipment_checkout row where this
        # employee has at least one un-returned line.
        outstanding: List[Dict[str, Any]] = []
        async for rec in db.field_leadership_records.find({"kind": "equipment_checkout", "employee_name": rx}, {"_id": 0}).limit(200):
            for idx, line in enumerate((rec.get("details") or {}).get("equipment_lines") or []):
                if line and not line.get("returned"):
                    outstanding.append({
                        "checkout_id": rec["id"], "line_index": idx,
                        "name": line.get("name"), "serial": line.get("serial"),
                        "qty": line.get("qty"), "checkout_date": rec.get("occurred_at"),
                        "project_number": rec.get("project_number"),
                    })

        # Training records — UNION of Safety source-of-truth
        # (safety_training_records) + legacy HR curriculums
        # (training_track_records). Before iter350 this only read
        # training_track_records, so OSHA/CPR/AED/equipment training
        # entered by Safety was INVISIBLE to HR.
        trainings: List[Dict[str, Any]] = []
        async for t in db.safety_training_records.find({"employee_name": rx}, {"_id": 0}).sort("completed_date", -1).limit(200):
            t["source"] = "safety"
            trainings.append(t)
        async for t in db.training_track_records.find({"employee_name": rx}, {"_id": 0}).sort("completed_at", -1).limit(200):
            t["source"] = "track"
            trainings.append(t)

        # Safety form equipment-issuance records
        safety_issuances: List[Dict[str, Any]] = []
        async for s in db.safety_forms.find({"form_type": "equipment_issuance", "employee_name": rx}, {"_id": 0}).sort("submitted_at", -1).limit(200):
            safety_issuances.append(s)

        counts = {
            "fl_records": len(fl_records),
            "outstanding_equipment": len(outstanding),
            "trainings": len(trainings),
            "safety_issuances": len(safety_issuances),
        }
        # Breakdown of FL kinds for the badge strip on the HR detail page.
        by_kind: Dict[str, int] = {}
        active_writeups = 0
        terminations = 0
        for r in fl_records:
            k = r.get("kind") or "other"
            by_kind[k] = by_kind.get(k, 0) + 1
            if k == "write_up":
                active_writeups += 1
            if k == "employee_termination":
                terminations += 1
        counts["active_writeups"] = active_writeups
        counts["terminations"] = terminations

        return {
            "ok": True,
            "employee": name,
            "counts": counts,
            "by_kind": by_kind,
            "fl_records": fl_records,
            "outstanding_equipment": outstanding,
            "trainings": trainings,
            "safety_issuances": safety_issuances,
        }

    # ─────────────────────────────────────────────────────────────────
    # iter353c · UNIFIED EMPLOYEE ACCOUNTABILITY TIMELINE
    # ─────────────────────────────────────────────────────────────────
    # This is the operational system of record for one employee.
    # Aggregates from 8+ source collections; source systems remain
    # authoritative. NEVER duplicates data into a new collection —
    # every read is live. Linkage uses the iter350 standard
    # (employee_id → employee_master_id → name+email → name).
    #
    # RBAC: HR + Admin + Safety can view. Operator policy: Safety is
    # shared accountability owner (iter353a). PM / Dispatch / Shop /
    # FL still blocked at this endpoint — they go through their own
    # portal-specific surfaces.
    @router.get("/hr/employees/{emp_id}/accountability/timeline")
    async def hr_employee_accountability_timeline(
        emp_id: str,
        actor: Dict[str, Any] = Depends(require_safety_or_hr_or_admin),
    ):
        from lib.employee_linkage import normalize_name, normalize_email  # noqa: PLC0415

        emp = await db.employees.find_one({"id": emp_id}, {"_id": 0})
        if not emp:
            emp = await db.employees.find_one({"employee_id": emp_id}, {"_id": 0})
        if not emp:
            raise HTTPException(404, "Employee not found")

        ename = emp.get("name") or ""
        n_norm = normalize_name(ename)
        e_norm = normalize_email(emp.get("email"))
        name_rx = {"$regex": f"^{re.escape(ename)}$" if ename else "", "$options": "i"} if ename else None

        # Tolerant linkage filter — applied to every source.
        def _emp_filter(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            ors = [
                {"employee_id": emp_id},
                {"employee_id": emp.get("employee_id") or "__none__"},
                {"employee_master_id": emp_id},
            ]
            if ename:
                ors.append({"employee_name": name_rx})
            if e_norm:
                ors.append({"employee_email": {"$regex": f"^{re.escape(e_norm)}$", "$options": "i"}})
            base: Dict[str, Any] = {"$or": ors}
            if extra:
                base.update(extra)
            return base

        events: List[Dict[str, Any]] = []

        def _push(*, ts, kind, category, title, description="", source,
                  source_id=None, status=None, expiration_date=None,
                  attachment=None, src_doc: Optional[Dict[str, Any]] = None):
            sd = src_doc or {}
            events.append({
                "id": f"{kind}-{source_id or ''}-{ts or ''}"[:120],
                "ts": ts,
                "kind": kind,
                "category": category,
                "title": title,
                "description": description,
                "source": source,
                "source_id": source_id,
                "status": status,
                "expiration_date": expiration_date,
                "attachment": attachment,
                "created_by": sd.get("created_by") or sd.get("created_by_name"),
                "created_by_role": (sd.get("created_by_role") or "legacy").lower(),
                "originating_portal": (sd.get("originating_portal") or sd.get("created_by_role") or "legacy").lower(),
                "updated_by": sd.get("updated_by"),
                "updated_by_role": (sd.get("updated_by_role") or "").lower() or None,
                "linkage_method": sd.get("linkage_method"),
                "archived": (
                    (sd.get("category") == "Archived")
                    or "[archived " in (sd.get("notes") or "")
                    or "[archived " in (sd.get("description") or "")
                ),
            })

        q = _emp_filter()

        # 1 · Safety training records
        async for d in db.safety_training_records.find(q, {"_id": 0}).limit(500):
            _push(
                ts=d.get("completed_date") or d.get("created_at"),
                kind="safety_training", category="Training",
                title=d.get("training_name") or "Training Record",
                description=d.get("certification_type") or "",
                source="safety_training_records", source_id=d.get("id"),
                expiration_date=d.get("expiration_date"),
                attachment=d.get("certificate_file_id"),
                src_doc=d,
            )

        # 2 · Training track records (HR curriculums)
        async for d in db.training_track_records.find(q, {"_id": 0}).limit(500):
            _push(
                ts=(d.get("completed_at") or "")[:10] or d.get("created_at"),
                kind="training_track", category="Training",
                title=d.get("track_name") or d.get("track_slug") or "Training Track",
                description=d.get("certification_type") or "",
                source="training_track_records", source_id=d.get("id"),
                expiration_date=d.get("expiration_date"),
                src_doc=d,
            )

        # 3 · PPE / equipment issuance (safety_equipment_issuances)
        async for d in db.safety_equipment_issuances.find(q, {"_id": 0}).limit(500):
            items = d.get("items") or []
            item_summary = ", ".join((i.get("description") or "") for i in items if i.get("description"))[:140]
            _push(
                ts=d.get("issued_date") or d.get("created_at"),
                kind="ppe_issuance", category="PPE & Equipment",
                title="PPE Issued",
                description=item_summary,
                source="safety_equipment_issuances", source_id=d.get("id"),
                src_doc=d,
            )

        # 4 · Equipment use-and-care training
        async for d in db.safety_equipment_trainings.find(q, {"_id": 0}).limit(500):
            _push(
                ts=d.get("trained_date") or d.get("created_at"),
                kind="equipment_training", category="Training",
                title=d.get("equipment_name") or "Equipment Training",
                description="Use & care acknowledgment",
                source="safety_equipment_trainings", source_id=d.get("id"),
                src_doc=d,
            )

        # 5 · Incidents
        try:
            async for d in db.incidents.find(q, {"_id": 0}).limit(500):
                _push(
                    ts=d.get("incident_date") or d.get("created_at"),
                    kind="incident", category="Incidents",
                    title=d.get("incident_type") or "Incident",
                    description=(d.get("description") or "")[:200],
                    source="incidents", source_id=d.get("id"),
                    status=d.get("status"),
                    src_doc=d,
                )
        except Exception:  # collection may not exist in all envs
            pass

        # 6 · Field Leadership records (write-ups, terminations, approved-driver forms, equipment checkouts, etc.)
        try:
            async for d in db.field_leadership_records.find(q, {"_id": 0}).limit(500):
                _push(
                    ts=d.get("occurred_at") or d.get("created_at"),
                    kind=f"fl_{d.get('kind') or 'record'}",
                    category="Field Leadership",
                    title=(d.get("kind") or "FL Record").replace("_", " ").title(),
                    description=(d.get("notes") or "")[:200],
                    source="field_leadership_records", source_id=d.get("id"),
                    src_doc=d,
                )
        except Exception:
            pass

        # 7 · CDL / driver-qualification status snapshot (from employee doc)
        # NOT a per-event row — but we surface the CDL fields in current_state.
        # We also add expiration-tied virtual events when CDL/medical card
        # has an expiration date so they appear on the timeline.
        if emp.get("cdl_expiration_date"):
            _push(
                ts=emp.get("cdl_expiration_date"),
                kind="cdl_expiration", category="Driver Qualification",
                title="CDL Expiration",
                description=f"State {emp.get('cdl_state') or '—'} · License {emp.get('cdl_license_number') or '—'}",
                source="employees", source_id=emp.get("id"),
                expiration_date=emp.get("cdl_expiration_date"),
                status="active" if (emp.get("cdl_holder") and emp.get("cdl_expiration_date", "")) >= datetime.now(timezone.utc).isoformat()[:10] else "expired",
                src_doc={"created_by_role": "hr"},
            )
        if emp.get("medical_card_expiration_date"):
            _push(
                ts=emp.get("medical_card_expiration_date"),
                kind="medical_card_expiration", category="Driver Qualification",
                title="Medical Card Expiration",
                description="DOT medical card expiration tracked on roster",
                source="employees", source_id=emp.get("id"),
                expiration_date=emp.get("medical_card_expiration_date"),
                src_doc={"created_by_role": "hr"},
            )

        # 8 · Status history on the employee doc (HR lifecycle audit chain)
        for h in (emp.get("status_history") or []):
            _push(
                ts=h.get("ts"),
                kind="status_change", category="HR Lifecycle",
                title=(h.get("kind") or "Status Change").replace("_", " ").title(),
                description=", ".join(h.get("fields") or []),
                source="employees.status_history", source_id=h.get("ts"),
                src_doc={
                    "created_by": h.get("actor"),
                    "created_by_role": h.get("actor_role") or "hr",
                },
            )

        # Sort DESC by ts (string ISO-8601 sort is stable for dates)
        events.sort(key=lambda e: (e.get("ts") or ""), reverse=True)

        # Compute current_state + expirations + counts
        today = datetime.now(timezone.utc).isoformat()[:10]
        in_30 = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()[:10]
        in_90 = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()[:10]

        expiring = [
            e for e in events
            if e.get("expiration_date") and today <= e["expiration_date"] <= in_90
        ]
        expired = [
            e for e in events
            if e.get("expiration_date") and e["expiration_date"] < today
        ]

        # Category counts
        cat_counts: Dict[str, int] = {}
        for e in events:
            cat_counts[e["category"]] = cat_counts.get(e["category"], 0) + 1

        current_state = {
            "lifecycle_status": emp.get("lifecycle_status"),
            "is_active": emp.get("is_active") if "is_active" in emp else True,
            "cdl_holder": bool(emp.get("cdl_holder")),
            "approved_company_driver": bool(emp.get("approved_company_driver")),
            "driver_status": emp.get("driver_status") or None,
            "cdl_state": emp.get("cdl_state") or None,
            "cdl_license_number": emp.get("cdl_license_number") or None,
            "cdl_expiration_date": emp.get("cdl_expiration_date") or None,
            "medical_card_expiration_date": emp.get("medical_card_expiration_date") or None,
            "cdl_endorsements": emp.get("cdl_endorsements") or [],
            "cdl_restrictions": emp.get("cdl_restrictions") or [],
            "expiring_within_90d": len(expiring),
            "expired": len(expired),
            "last_training": next((e["ts"] for e in events if e["category"] == "Training" and not e.get("archived")), None),
            "last_ppe_issuance": next((e["ts"] for e in events if e["kind"] == "ppe_issuance"), None),
            "last_incident": next((e["ts"] for e in events if e["kind"] == "incident"), None),
        }

        return {
            "ok": True,
            "employee": {
                "id": emp.get("id"),
                "name": emp.get("name"),
                "employee_id": emp.get("employee_id"),
                "email": emp.get("email"),
                "trade": emp.get("trade"),
                "department": emp.get("department"),
                "supervisor": emp.get("supervisor"),
                "crew": emp.get("crew"),
                "hire_date": emp.get("hire_date"),
                "lifecycle_status": emp.get("lifecycle_status"),
            },
            "current_state": current_state,
            "category_counts": cat_counts,
            "total_events": len(events),
            "events": events,
            "expiring_within_90d": expiring,
            "expired_items": expired,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "viewer": {
                "actor": actor.get("email") or actor.get("name") or "unknown",
                "role": (actor.get("_actor") or actor.get("role") or "").lower(),
            },
        }

    # iter353c · HR Compliance Brief PDF — first-class export.
    # Uses the same timeline data; renders to a portable reportlab PDF
    # suitable for OSHA / DOT / insurance / FAA / legal / onboarding
    # verification. NEVER mutates source collections.
    @router.get("/hr/employees/{emp_id}/accountability/brief.pdf")
    async def hr_employee_compliance_brief_pdf(
        emp_id: str,
        actor: Dict[str, Any] = Depends(require_safety_or_hr_or_admin),
    ):
        from fastapi.responses import Response  # noqa: PLC0415
        from io import BytesIO  # noqa: PLC0415
        from reportlab.lib.pagesizes import letter  # noqa: PLC0415
        from reportlab.lib import colors  # noqa: PLC0415
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # noqa: PLC0415
        from reportlab.lib.units import inch  # noqa: PLC0415
        from reportlab.platypus import (  # noqa: PLC0415
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
        )

        # Reuse the timeline handler logic by calling it directly so the
        # PDF stays in lockstep with the API. We pass `actor` so RBAC
        # is consistent.
        payload = await hr_employee_accountability_timeline(emp_id, actor=actor)
        emp = payload["employee"]
        cs = payload["current_state"]
        events = payload["events"]

        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=letter,
            leftMargin=0.6 * inch, rightMargin=0.6 * inch,
            topMargin=0.6 * inch, bottomMargin=0.6 * inch,
            title=f"HR Compliance Brief — {emp.get('name') or emp_id}",
        )
        styles = getSampleStyleSheet()
        h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#5b21b6"), spaceAfter=4)
        h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=11, textColor=colors.HexColor("#1e293b"), spaceBefore=12, spaceAfter=4, fontName="Helvetica-Bold")
        body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9, leading=12)
        small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=7.5, leading=10, textColor=colors.HexColor("#64748b"))

        story = []
        story.append(Paragraph("HR Compliance Brief", h1))
        story.append(Paragraph(
            f"<b>{emp.get('name') or '—'}</b> · "
            f"{emp.get('trade') or '—'} · "
            f"Employee ID {emp.get('employee_id') or emp.get('id') or '—'}",
            body,
        ))
        story.append(Paragraph(
            f"Generated {payload['generated_at'][:19].replace('T',' ')} UTC · "
            f"Viewer: {payload['viewer']['actor']} ({payload['viewer']['role']})",
            small,
        ))
        story.append(Spacer(1, 8))

        # Section 1 · Employee profile
        story.append(Paragraph("1 · Employee Profile", h2))
        profile_rows = [
            ["Lifecycle Status", emp.get("lifecycle_status") or "—",
             "Department", emp.get("department") or "—"],
            ["Trade", emp.get("trade") or "—",
             "Supervisor", emp.get("supervisor") or "—"],
            ["Email", emp.get("email") or "—",
             "Hire Date", emp.get("hire_date") or "—"],
        ]
        t1 = Table(profile_rows, colWidths=[1.1 * inch, 2.4 * inch, 1.1 * inch, 2.4 * inch])
        t1.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f1f5f9")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(t1)

        # Section 2 · Driver Qualification / CDL
        story.append(Paragraph("2 · Driver Qualification / CDL", h2))
        dq_rows = [
            ["CDL Holder", "Yes" if cs["cdl_holder"] else "No",
             "Approved Driver", "Yes" if cs["approved_company_driver"] else "No"],
            ["Driver Status", cs["driver_status"] or "—",
             "State", cs["cdl_state"] or "—"],
            ["License #", cs["cdl_license_number"] or "—",
             "Endorsements", ", ".join(cs["cdl_endorsements"]) or "—"],
            ["CDL Expiration", cs["cdl_expiration_date"] or "—",
             "Medical Card Expiration", cs["medical_card_expiration_date"] or "—"],
        ]
        t2 = Table(dq_rows, colWidths=[1.4 * inch, 2.1 * inch, 1.4 * inch, 2.1 * inch])
        t2.setStyle(t1.style)
        story.append(t2)

        # Section 3 · Expiration Watch
        story.append(Paragraph("3 · Expiration Watch (next 90 days · expired)", h2))
        exp = payload.get("expiring_within_90d", []) + payload.get("expired_items", [])
        if exp:
            exp_data = [["Item", "Date", "Category", "Status"]]
            for e in exp[:30]:
                today = datetime.now(timezone.utc).isoformat()[:10]
                status = "EXPIRED" if e["expiration_date"] < today else "Expiring"
                exp_data.append([e.get("title", "")[:40], e.get("expiration_date", ""), e.get("category", ""), status])
            te = Table(exp_data, colWidths=[3.0 * inch, 1.0 * inch, 1.6 * inch, 1.4 * inch])
            te.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef3c7")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
            ]))
            story.append(te)
        else:
            story.append(Paragraph("No items expiring within 90 days. ✓", body))

        # Section 4..N · Per-category timeline
        section_n = 4
        for cat in ("Training", "PPE & Equipment", "Incidents", "Field Leadership", "HR Lifecycle"):
            cat_events = [e for e in events if e.get("category") == cat]
            if not cat_events:
                continue
            story.append(Paragraph(f"{section_n} · {cat}", h2))
            section_n += 1
            data = [["Date", "Title", "Status / Detail", "Entered By"]]
            for e in cat_events[:50]:
                role = (e.get("created_by_role") or "—").upper()
                status = e.get("expiration_date") or e.get("status") or ""
                title = e.get("title", "")
                if e.get("archived"):
                    title = f"{title} (ARCHIVED)"
                data.append([
                    (e.get("ts") or "")[:10], title[:55],
                    f"{e.get('description', '')[:50]} {status}".strip(),
                    role,
                ])
            tb = Table(data, colWidths=[0.9 * inch, 2.7 * inch, 2.4 * inch, 0.9 * inch])
            tb.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ede9fe")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(tb)

        story.append(Spacer(1, 16))
        story.append(Paragraph(
            "MASCI Operations Platform · Compliance Brief is a point-in-time snapshot. "
            "Source records remain authoritative. For corrections, contact HR or Safety.",
            small,
        ))
        doc.build(story)
        buf.seek(0)
        return Response(
            content=buf.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f'attachment; filename="HR_Compliance_Brief_{(emp.get("name") or emp_id).replace(" ", "_")}.pdf"',
                "Cache-Control": "no-store",
            },
        )

    # ─────────────────────────────────────────────────────────────────
    # TIME VERIFICATION — supervisor-reported hours from Daily Reports
    # ─────────────────────────────────────────────────────────────────
    @router.get("/hr/time-verification")
    async def hr_time_verification(
        actor=Depends(require_hr_user),
        week_ending: Optional[str] = None,
        employee: Optional[str] = None,
        project_number: Optional[str] = None,
        supervisor: Optional[str] = None,
    ):
        """Read-only view of MASCI employee hours pulled from
        ``masci_crews`` rows in daily_reports. Returns a flat list of
        per-employee-per-day entries plus a per-employee weekly rollup.

        The spec restricts visible columns to employee name, date, job,
        supervisor, regular hrs, overtime hrs, lunch duration, total
        hrs, daily-report submission timestamp. We deliberately strip
        out everything else (notes, photos, equipment, materials,
        delays, etc.) before returning so HR cannot accidentally see
        non-payroll info.
        """
        # Resolve the date window. If a week_ending is supplied we use
        # Mon–Sun ending that date; otherwise default to the current week
        # (Mon → today UTC). Field crews are not on UTC, but the date
        # math is intentionally relative to the report_date string which
        # is stored as a YYYY-MM-DD local date, so timezone drift here
        # is harmless.
        if week_ending:
            try:
                end = datetime.strptime(week_ending, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(400, "week_ending must be YYYY-MM-DD")
        else:
            end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=6)

        query: Dict[str, Any] = {
            "report_date": {"$gte": start.isoformat(), "$lte": end.isoformat()},
        }
        if project_number:
            query["project_number"] = project_number
        if supervisor:
            query["$or"] = [
                {"prepared_by": {"$regex": supervisor, "$options": "i"}},
                {"superintendent": {"$regex": supervisor, "$options": "i"}},
            ]

        emp_filter = (employee or "").strip().lower()

        # Per-day rows + per-employee rollup keyed on lowercase name.
        rows: List[Dict[str, Any]] = []
        weekly: Dict[str, Dict[str, Any]] = {}

        async for d in db.daily_reports.find(query, {"_id": 0}).sort("report_date", 1).limit(1000):
            day = d.get("report_date") or ""
            job = d.get("project_name") or ""
            job_num = d.get("project_number") or ""
            supe = d.get("prepared_by") or d.get("superintendent") or ""
            crews = d.get("masci_crews") or []
            submitted_at = d.get("created_at") or d.get("submitted_at") or ""
            for c in crews:
                if not c:
                    continue
                name = (c.get("name") or "").strip()
                if not name:
                    continue
                if emp_filter and emp_filter not in name.lower():
                    continue
                # Total hours per spec: prefer explicit `hours`, fallback
                # to (stop - start - lunch). Keep this simple and trust
                # the supervisor's entered `hours` first.
                hours = c.get("hours")
                try:
                    hours = float(hours) if hours not in (None, "") else 0.0
                except (TypeError, ValueError):
                    hours = 0.0
                # Iter99 — Weekly OT, NOT daily OT.
                # Per FLSA + MASCI payroll policy: overtime is anything
                # over 40 hrs IN THE WEEK, regardless of how the hours
                # were distributed across days. So a guy who works
                # 12/10/14/4/10 = 50 hrs gets 40 reg + 10 OT (not the
                # 12 daily-OT figure the old code produced).
                #
                # We therefore DON'T split reg/OT at the per-day row
                # here; we carry total_hours through and split at the
                # weekly rollup stage below. Per-day rows show 0 reg
                # / 0 OT and the full `total_hours` so HR can verify
                # the source data. The weekly rollup is what payroll
                # actually uses.
                lunch_min = c.get("lunch_minutes")
                try:
                    lunch_hrs = round(float(lunch_min) / 60.0, 2) if lunch_min not in (None, "") else 0.0
                except (TypeError, ValueError):
                    lunch_hrs = 0.0
                row = {
                    "employee_name": name,
                    "trade": c.get("trade") or "",
                    "date": day,
                    "project_number": job_num,
                    "project_name": job,
                    "supervisor": supe,
                    "start_time": c.get("start_time") or "",
                    "stop_time": c.get("stop_time") or "",
                    # Daily reg/OT both render as 0; payroll uses the
                    # weekly figures only. Kept as columns so existing
                    # CSV consumers don't break.
                    "regular_hours": 0.0,
                    "overtime_hours": 0.0,
                    "lunch_hours": lunch_hrs,
                    "total_hours": round(hours, 2),
                    "daily_report_id": d.get("id"),
                    "submitted_at": submitted_at,
                    # Future-ready Exact payroll fields — null until wired
                    "exact_employee_id": None,
                    "exact_total_hours": None,
                    "variance_hours": None,
                    "variance_flag": None,
                    "review_status": None,
                }
                rows.append(row)
                key = name.lower()
                if key not in weekly:
                    weekly[key] = {
                        "employee_name": name,
                        "days": [],
                        "regular_hours": 0.0,
                        "overtime_hours": 0.0,
                        "lunch_hours": 0.0,
                        "total_hours": 0.0,
                        "jobs": set(),
                        "supervisors": set(),
                    }
                w = weekly[key]
                w["days"].append({
                    "date": day, "job": job, "job_number": job_num,
                    "supervisor": supe, "hours": round(hours, 2),
                    "lunch_hours": lunch_hrs,
                    # Same reasoning: daily reg/OT are 0 — see note above.
                    "regular_hours": 0.0,
                    "overtime_hours": 0.0,
                })
                w["lunch_hours"] += lunch_hrs
                w["total_hours"] += hours
                if job_num:
                    w["jobs"].add(job_num)
                if supe:
                    w["supervisors"].add(supe)

        # Iter99 — Weekly OT split happens HERE, once per employee, at
        # the end of the week. anything over 40 hrs in the week = OT,
        # remainder = regular. Threshold env-overridable so a different
        # state/contract can be applied later.
        try:
            ot_threshold = float(os.environ.get("OT_WEEKLY_THRESHOLD", "40") or 40)
        except (TypeError, ValueError):
            ot_threshold = 40.0
        for w in weekly.values():
            total = float(w["total_hours"] or 0.0)
            ot = max(total - ot_threshold, 0.0)
            reg = total - ot
            w["regular_hours"] = reg
            w["overtime_hours"] = ot

        # JSON-safe: sets → lists, round floats.
        weekly_list = []
        for w in weekly.values():
            weekly_list.append({
                "employee_name": w["employee_name"],
                "days": sorted(w["days"], key=lambda x: x["date"]),
                "regular_hours": round(w["regular_hours"], 2),
                "overtime_hours": round(w["overtime_hours"], 2),
                "lunch_hours": round(w["lunch_hours"], 2),
                "total_hours": round(w["total_hours"], 2),
                "jobs": sorted(w["jobs"]),
                "supervisors": sorted(w["supervisors"]),
                "missing_lunch": any((d.get("lunch_hours") or 0) == 0 and (d.get("hours") or 0) >= 6 for d in w["days"]),
            })
        weekly_list.sort(key=lambda w: w["employee_name"].lower())

        return {
            "ok": True,
            "week_start": start.isoformat(),
            "week_end": end.isoformat(),
            "rows": rows,
            "weekly": weekly_list,
            # iter178 fix: summary cards must sum the WEEKLY rollup, not
            # the per-day rows. Per-day rows intentionally carry
            # regular_hours=0 / overtime_hours=0 because OT is split at
            # the weekly stage per FLSA + MASCI policy (see comments
            # ~line 420). Summing those zeros produced the 0.00 Reg/OT
            # bug HR caught while cross-checking payroll. Total Hours
            # is also computed off the same weekly rollup so the
            # invariant Total Hours == Regular + Overtime holds
            # exactly (it would have held before too, since per-day
            # total_hours sum equals weekly total_hours sum — but
            # sourcing both from the same place removes any drift
            # risk if rounding ever changes).
            "summary": {
                "total_rows": len(rows),
                "total_employees": len(weekly_list),
                "total_hours": round(sum(w["total_hours"] for w in weekly_list), 2),
                "total_regular": round(sum(w["regular_hours"] for w in weekly_list), 2),
                "total_overtime": round(sum(w["overtime_hours"] for w in weekly_list), 2),
                "total_lunch": round(sum(w["lunch_hours"] for w in weekly_list), 2),
            },
        }

    @router.get("/hr/time-verification.csv")
    async def hr_time_verification_csv(
        actor=Depends(require_hr_user),
        week_ending: Optional[str] = None,
        employee: Optional[str] = None,
        project_number: Optional[str] = None,
        supervisor: Optional[str] = None,
    ):
        """CSV export of the time-verification view — payroll-review ready."""
        import csv as _csv
        import io as _io
        from fastapi.responses import Response
        data = await hr_time_verification(actor=actor, week_ending=week_ending,
                                          employee=employee, project_number=project_number,
                                          supervisor=supervisor)
        buf = _io.StringIO()
        w = _csv.writer(buf)
        w.writerow([
            "Date", "Employee", "Trade", "Project #", "Project Name",
            "Supervisor", "Start", "Stop", "Lunch (hrs)", "Regular Hrs",
            "Overtime Hrs", "Total Hrs", "Submitted At", "Daily Report ID",
        ])
        for r in data["rows"]:
            w.writerow([
                r["date"], r["employee_name"], r["trade"], r["project_number"],
                r["project_name"], r["supervisor"], r["start_time"], r["stop_time"],
                r["lunch_hours"], r["regular_hours"], r["overtime_hours"],
                r["total_hours"], r["submitted_at"], r["daily_report_id"],
            ])
        # iter178 — append per-employee weekly rollup so HR's payroll
        # cross-check sees the FLSA-split Reg/OT figures. The per-day
        # rows above intentionally carry Reg/OT=0 because the split
        # happens once per week (see comments in hr_time_verification).
        # Without this section the CSV would show every Reg/OT cell as
        # 0 even though the week has overtime — same root cause as the
        # summary-card bug.
        w.writerow([])
        w.writerow(["WEEKLY ROLLUP (FLSA-split, payroll-ready)"])
        w.writerow([
            "Employee", "Jobs", "Supervisor(s)",
            "Regular Hrs", "Overtime Hrs", "Lunch Hrs", "Total Hrs",
        ])
        for wk in data["weekly"]:
            w.writerow([
                wk["employee_name"],
                "; ".join(wk.get("jobs") or []),
                "; ".join(wk.get("supervisors") or []),
                wk["regular_hours"], wk["overtime_hours"],
                wk["lunch_hours"], wk["total_hours"],
            ])
        s = data.get("summary") or {}
        w.writerow([])
        w.writerow([
            "TOTALS", "", "",
            s.get("total_regular", 0), s.get("total_overtime", 0),
            s.get("total_lunch", 0), s.get("total_hours", 0),
        ])
        filename = f"MASCI_time_verification_{data['week_start']}_to_{data['week_end']}.csv"
        return Response(content=buf.getvalue().encode("utf-8"), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    # ─────────────────────────────────────────────────────────────────
    # TRAINING RECORDS · iter350 — Live Data Visibility Fix
    # ─────────────────────────────────────────────────────────────────
    # HR's Training Records view must reflect the COMPLETE training
    # picture for accountability and payroll cross-checks. Before
    # iter350, this endpoint ONLY queried `training_track_records`
    # (HR's internal Operational Guidance Center curriculums). Safety
    # writes training certifications (OSHA, CPR/AED, equipment) to
    # `safety_training_records` — these were INVISIBLE to HR despite
    # being the actual source-of-truth for compliance.
    #
    # Fix: UNION both collections + enrich every row with linkage
    # metadata (Primary: employee_id · Fallback: name+email · graceful
    # None) so HR sees every training record tied to every roster
    # employee regardless of which portal wrote it. Read-only —
    # HR cannot mutate safety records, and no write paths exist on
    # /api/hr/training-records.
    @router.get("/hr/training-records")
    async def hr_training_records(
        actor=Depends(require_hr_user),
        employee: Optional[str] = None,
        track: Optional[str] = None,
        source: Optional[str] = None,   # "safety" | "track" | None=both
        limit: int = 500,
    ):
        from lib.employee_linkage import attach_employee_links  # noqa: PLC0415

        cap = min(limit, 1000)

        # ── Safety source-of-truth: safety_training_records ──────────
        safety_rows: List[Dict[str, Any]] = []
        if (source or "").lower() != "track":
            q_safety: Dict[str, Any] = {}
            if employee:
                q_safety["employee_name"] = {"$regex": employee, "$options": "i"}
            async for d in db.safety_training_records.find(
                q_safety, {"_id": 0},
            ).sort("completed_date", -1).limit(cap):
                # Normalize the row to the unified HR shape so the
                # frontend doesn't need a per-source branch.
                safety_rows.append({
                    "id": d.get("id"),
                    "source": "safety",
                    "employee_id": d.get("employee_id"),
                    "employee_master_id": d.get("employee_master_id"),
                    "employee_name": d.get("employee_name"),
                    # Map safety fields → unified shape
                    "training_name": d.get("training_name"),
                    "track_slug": None,
                    "track_name": d.get("training_name"),
                    "certification_type": d.get("certification_type"),
                    "completed_at": d.get("completed_date"),
                    "completed_date": d.get("completed_date"),
                    "expiration_date": d.get("expiration_date"),
                    "issued_by": d.get("issued_by"),
                    "score": None,
                    "certificate_file_id": d.get("certificate_file_id"),
                    "created_by_name": d.get("created_by_name"),
                    "created_at": d.get("created_at"),
                })

        # ── HR legacy source: training_track_records ─────────────────
        track_rows: List[Dict[str, Any]] = []
        if (source or "").lower() != "safety":
            q_track: Dict[str, Any] = {}
            if employee:
                q_track["employee_name"] = {"$regex": employee, "$options": "i"}
            if track:
                q_track["track_slug"] = track
            async for d in db.training_track_records.find(
                q_track, {"_id": 0},
            ).sort("completed_at", -1).limit(cap):
                track_rows.append({
                    "id": d.get("id"),
                    "source": "track",
                    "employee_id": d.get("employee_id"),
                    "employee_master_id": d.get("employee_master_id"),
                    "employee_name": d.get("employee_name"),
                    "training_name": d.get("track_name") or d.get("track_slug"),
                    "track_slug": d.get("track_slug"),
                    "track_name": d.get("track_name"),
                    "certification_type": d.get("certification_type") or "TRACK",
                    "completed_at": d.get("completed_at"),
                    "completed_date": (d.get("completed_at") or "")[:10] if d.get("completed_at") else None,
                    "expiration_date": d.get("expiration_date"),
                    "issued_by": d.get("issued_by"),
                    "score": d.get("score"),
                    "certificate_file_id": None,
                    "created_by_name": d.get("created_by_name"),
                    "created_at": d.get("created_at"),
                })

        # ── Sort union by best-available date desc, then enrich ──────
        union = safety_rows + track_rows
        union.sort(
            key=lambda r: (r.get("completed_at") or r.get("created_at") or ""),
            reverse=True,
        )
        union = union[:cap]
        union = await attach_employee_links(db, union)

        # Tiny source breakdown for the HR header strip.
        counts = {
            "safety": len(safety_rows),
            "track": len(track_rows),
            "total": len(union),
            "unlinked": sum(1 for r in union if r.get("linkage_method") == "unlinked"),
        }
        return {"ok": True, "items": union, "count": len(union), "counts": counts}

    # ─────────────────────────────────────────────────────────────────
    # SAFETY DOCUMENTS · iter350 — Cross-portal read-only HR surface
    # ─────────────────────────────────────────────────────────────────
    # `/api/safety/documents` ALREADY accepts HR tokens via the
    # `require_safety_or_hr_or_admin` gate (see safety_portal/_deps.py)
    # — the `/hr/safety-records` page uses it directly. But for
    # consistency with the iter350 contract (HR has a dedicated
    # read-only namespace under /api/hr/*) we surface a calm, bounded
    # /api/hr/safety-documents alias that proxies the same data with
    # the HR-token-only gate. NO write paths exist here — HR cannot
    # POST, PATCH, or DELETE safety documents from this surface.
    @router.get("/hr/safety-documents")
    async def hr_safety_documents(
        actor=Depends(require_hr_user),
        category: Optional[str] = None,
        q: Optional[str] = None,
        employee: Optional[str] = None,
        limit: int = 500,
    ):
        query: Dict[str, Any] = {}
        if category:
            query["category"] = category
        if q:
            needle = q.strip()
            query["$or"] = [
                {"title":       {"$regex": needle, "$options": "i"}},
                {"description": {"$regex": needle, "$options": "i"}},
                {"filename":    {"$regex": needle, "$options": "i"}},
                {"tags":        {"$regex": needle, "$options": "i"}},
            ]
        # safety_documents are a global library — they don't carry
        # employee_id directly. We expose them all to HR and let the
        # UI filter by category / search. When the `employee` filter
        # is supplied, we narrow to records whose title/description
        # contains the needle (defensive — safety_documents do not
        # have an employee field in the schema).
        if employee:
            emp_needle = employee.strip()
            query.setdefault("$or", []).extend([
                {"title":       {"$regex": emp_needle, "$options": "i"}},
                {"description": {"$regex": emp_needle, "$options": "i"}},
            ])

        items: List[Dict[str, Any]] = []
        # Project file_data OUT — listing is metadata only.
        async for d in db.safety_documents.find(
            query, {"_id": 0, "file_data": 0},
        ).sort("uploaded_at", -1).limit(min(limit, 2000)):
            items.append(d)

        # Tiny summary cards for the HR header strip.
        today = datetime.now(timezone.utc).isoformat()[:10]
        thirty = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()[:10]
        expiring = 0
        expired = 0
        for d in items:
            exp = d.get("expiration_date")
            if not exp:
                continue
            if exp < today:
                expired += 1
            elif exp <= thirty:
                expiring += 1
        return {
            "ok": True, "items": items, "count": len(items),
            "summary": {
                "total": len(items),
                "expiring_30d": expiring,
                "expired": expired,
            },
        }

    @router.get("/hr/safety-documents/{doc_id}/download")
    async def hr_safety_document_download(doc_id: str, actor=Depends(require_hr_user)):
        from fastapi.responses import Response
        import safety_doc_storage  # noqa: PLC0415
        doc = await db.safety_documents.find_one({"id": doc_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "document not found")
        ref = doc.get("file_data") or ""
        try:
            raw = await safety_doc_storage.read_doc_bytes(ref)
        except (ValueError, RuntimeError) as e:
            logger.exception(f"[hr-safety-doc] download read failed for {doc_id}: {e}")
            raise HTTPException(500, "Stored file is unreadable")
        ct = doc.get("content_type", "application/octet-stream")
        fname = doc.get("filename", "document")
        return Response(
            content=raw,
            media_type=ct,
            headers={
                "Content-Disposition": f'attachment; filename="{fname}"',
                "Cache-Control": "no-store",
            },
        )

    # ─────────────────────────────────────────────────────────────────
    # ADMIN — HR user management
    # ─────────────────────────────────────────────────────────────────
    async def _send_welcome_email(user_email: str, name: str, temp_password: str):
        if not send_email_fn:
            logger.info(f"[HR welcome] {user_email} → {temp_password}")
            return
        base = os.environ.get("PUBLIC_APP_URL", "https://mascidocs.com").rstrip("/")
        login_url = f"{base}/hr/login"
        body_html = (
            f"<p style='margin:0 0 12px'>Hi {name},</p>"
            f"<p style='margin:0 0 12px'>Your MASCI HR Portal account has been created. "
            f"Sign in with your work email and the temporary password below — "
            f"<strong>you'll be asked to choose your own password on first login.</strong></p>"
            f"<table style='margin:14px 0;border-collapse:collapse;width:100%;'>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;text-transform:uppercase;letter-spacing:0.18em;font-size:10px;color:#475569;font-weight:bold;width:42%'>Sign-in URL</td>"
            f"      <td style='padding:6px 0;font-size:13px;'><a href='{login_url}' style='color:#7e22ce;font-weight:600'>{login_url}</a></td></tr>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;text-transform:uppercase;letter-spacing:0.18em;font-size:10px;color:#475569;font-weight:bold;'>Email</td>"
            f"      <td style='padding:6px 0;font-family:Courier New,monospace;font-size:13px;color:#0f172a'>{user_email}</td></tr>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;text-transform:uppercase;letter-spacing:0.18em;font-size:10px;color:#475569;font-weight:bold;'>Temporary password</td>"
            f"      <td style='padding:6px 0;font-family:Courier New,monospace;font-size:14px;color:#0f172a;background:#f8fafc;border:1px dashed #94a3b8;padding-left:8px;border-radius:4px'><strong>{temp_password}</strong></td></tr>"
            f"</table>"
            f"<p style='margin:14px 0 6px'>"
            f"<a href='{login_url}' style='display:inline-block;padding:11px 22px;background:#7e22ce;color:#fff;text-decoration:none;font-weight:700;border-radius:4px;font-size:13px'>Sign in &amp; set password</a>"
            f"</p>"
            f"<p style='margin:18px 0 0;font-size:12px;color:#94a3b8'>For security, please change your password immediately after signing in.</p>"
        )
        html = render_portal_email(
            portal="HR",
            headline="Your MASCI HR Portal account",
            body_inner_html=body_html,
        )
        try:
            await send_email_fn(user_email, "[MASCI] Your HR Portal account — temporary password inside", html)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"hr welcome email failed: {e}")

    @router.get("/admin/hr-users", dependencies=[Depends(require_admin_dep)])
    async def admin_list_hr():
        users = await list_hr_users(db)
        return {"ok": True, "users": [public_hr_user_view(u) for u in users]}

    @router.post("/admin/hr-users", dependencies=[Depends(require_admin_dep)])
    async def admin_create_hr(payload: HRUserCreate):
        try:
            user = await add_hr_user(db, payload.dict())
        except ValueError as e:
            raise HTTPException(400, str(e))
        # Pick password
        delivery = (payload.delivery or "email").lower()
        if delivery == "custom" and payload.custom_password:
            temp = payload.custom_password
        else:
            temp = generate_temp_password()
        await set_hr_user_password(db, user["id"], temp, must_change=True)
        if delivery == "email":
            await _send_welcome_email(user["email"], user["name"], temp)
        # Pull a fresh doc.
        fresh = await db.hr_users.find_one({"id": user["id"]}, {"_id": 0})
        return {
            "ok": True,
            "user": public_hr_user_view(fresh),
            "temp_password": temp if delivery != "email" else None,
        }

    @router.patch("/admin/hr-users/{user_id}", dependencies=[Depends(require_admin_dep)])
    async def admin_patch_hr(user_id: str, payload: HRUserPatch):
        try:
            updated = await update_hr_user(db, user_id, payload.dict(exclude_unset=True))
        except ValueError as e:
            raise HTTPException(400, str(e))
        if not updated:
            raise HTTPException(404, "user not found")
        return {"ok": True, "user": public_hr_user_view(updated)}

    @router.post("/admin/hr-users/{user_id}/reset-password",
                 dependencies=[Depends(require_admin_dep)])
    async def admin_reset_hr_password(user_id: str, body: Dict[str, Any] = Body(default={})):
        delivery = (body.get("delivery") or "email").lower()
        custom = body.get("custom_password")
        if delivery == "custom" and custom:
            temp = str(custom)
        else:
            temp = generate_temp_password()
        updated = await set_hr_user_password(db, user_id, temp, must_change=True)
        if not updated:
            raise HTTPException(404, "user not found")
        if delivery == "email":
            await _send_welcome_email(updated["email"], updated["name"], temp)
        return {
            "ok": True,
            "user": public_hr_user_view(updated),
            "temp_password": temp if delivery != "email" else None,
        }

    @router.delete("/admin/hr-users/{user_id}", dependencies=[Depends(require_admin_dep)])
    async def admin_delete_hr(user_id: str):
        ok = await delete_hr_user(db, user_id)
        if not ok:
            raise HTTPException(404, "user not found")
        return {"ok": True}

    return router
