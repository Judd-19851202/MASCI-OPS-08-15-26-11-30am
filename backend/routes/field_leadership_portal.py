"""
field_leadership_portal.py — Field Leadership Portal (iter314)
==============================================================
Self-contained portal mirroring the HR/PM/Shop patterns. Field
Leadership users get OPERATIONAL access to field workflows
(Daily Reports, Safety Meetings, JHAs, Pre-Ops/DVIRs, Fleet/Dispatch
visibility, Incidents, Driver Qualification dashboard) but are
EXPLICITLY blocked from HR admin, payroll, system settings, admin
governance, and platform configuration.

Endpoints (under /api):

PUBLIC (with X-FL-Token):
  POST   /field-leadership/portal/login                 — email+password → token
  POST   /field-leadership/portal/change-password       — first login or admin reset
  POST   /field-leadership/portal/forgot-password       — issue reset email
  POST   /field-leadership/portal/reset/{token}         — consume reset token
  GET    /field-leadership/portal/me                    — current FL user
  GET    /field-leadership/portal/dispatch-today        — today/tomorrow only · read-only
  GET    /field-leadership/portal/driver-qualification  — proxy to dashboard · read-only

NOTE · iter314 path collision resolution: the legacy
`/api/field-leadership/login` shared-password document-viewer gate
remains intact under `routes/field_leadership.py`. This new portal
lives under `/field-leadership/portal/*` to keep the two systems
running side-by-side without destabilizing the legacy one.

ADMIN/HR (X-Admin-Token OR X-HR-Token):
  GET    /admin/field-leadership-users             — roster
  POST   /admin/field-leadership-users             — create + temp password + email
  PATCH  /admin/field-leadership-users/{id}        — edit fields
  POST   /admin/field-leadership-users/{id}/reset-password
  POST   /admin/field-leadership-users/{id}/resend-welcome
  DELETE /admin/field-leadership-users/{id}        — remove

The admin/* routes accept EITHER an admin token OR an HR token via
the bundled dependency. This implements operator iter314 mandate:
"HR and Admin must BOTH be able to create field leadership users".
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion

from auth_must_change import enforce_password_change_required

import field_leadership_users as fl
from branded_portal_emails import render_portal_email
from field_leadership_users import (
    ALLOWED_FL_ROLES, FL_CANONICAL_ROLES, _canonical_role,
    add_fl_user, consume_fl_reset_token, delete_fl_user,
    find_fl_user_by_email, generate_temp_password, is_valid_fl_user_token_async,
    list_fl_users, make_fl_reset_token, make_fl_user_token,
    public_fl_user_view, set_fl_user_password, stamp_fl_login, update_fl_user,
    verify_password,
)
from hr_users import is_valid_hr_user_token_async

logger = logging.getLogger(__name__)


# ----- Pydantic payloads (mirror HR patterns) --------------------------

class FLLoginPayload(BaseModel):
    email: str
    password: str


class FLChangePasswordPayload(BaseModel):
    current_password: Optional[str] = None
    new_password: str = Field(min_length=8, max_length=128)


class FLForgotPasswordPayload(BaseModel):
    email: str


class FLResetPasswordPayload(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class FLUserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=200)
    phone: Optional[str] = ""
    role: str = "Superintendent"
    delivery: str = Field(default="email")
    custom_password: Optional[str] = None


class FLUserPatch(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    disabled: Optional[bool] = None


def _client_ip(req: Request) -> str:
    try:
        fwd = req.headers.get("x-forwarded-for") or req.headers.get("x-real-ip")
        if fwd:
            return fwd.split(",")[0].strip()
        return req.client.host if req.client else ""
    except Exception:
        return ""


def build_field_leadership_portal_router(
    db,
    require_admin_dep: Callable,
    send_email_fn: Optional[Callable] = None,
    directory_admin_minter: Optional[Callable] = None,
) -> APIRouter:
    """Assemble the Field Leadership portal router."""
    router = APIRouter(prefix="/api", tags=["field-leadership-portal"])

    # ─── FL token resolver ───────────────────────────────────────────
    async def require_fl_user(
        request: Request,
        x_fl_token: Optional[str] = Header(default=None, alias="X-FL-Token"),
    ) -> Dict[str, Any]:
        if not x_fl_token:
            raise HTTPException(401, "Field leadership login required")
        user = await is_valid_fl_user_token_async(db, x_fl_token)
        if not user:
            raise HTTPException(401, "Field leadership session expired or invalid")
        # Track 15.14A Layer 3 — temp-password backstop.
        enforce_password_change_required(request, user)
        return {**user, "_actor_kind": "fl_user"}

    # ─── HR-or-Admin combined gate (operator iter314 mandate: HR and
    #     Admin must both be able to manage FL users) ─────────────────
    async def require_hr_or_admin(
        request: Request,
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),
    ) -> Dict[str, Any]:
        # Admin path
        if x_admin_token:
            try:
                await require_admin_dep(
                    request=request, x_admin_token=x_admin_token, x_pm_token=None,
                )
                return {"_actor_kind": "admin"}
            except HTTPException:
                pass
            except Exception:  # noqa: BLE001
                pass
        # HR path
        if x_hr_token:
            user = await is_valid_hr_user_token_async(db, x_hr_token)
            if user:
                enforce_password_change_required(request, user)
                return {**user, "_actor_kind": "hr_user"}
        raise HTTPException(401, "Admin or HR login required")

    # ─────────────────────────────────────────────────────────────────
    # AUTH endpoints (mirror HR exactly)
    # ─────────────────────────────────────────────────────────────────
    @router.post("/field-leadership/portal/login")
    async def fl_login(payload: FLLoginPayload, request: Request):
        email = (payload.email or "").strip().lower()
        if not email or not payload.password:
            raise HTTPException(400, "email and password required")
        # ── Path 1 · per-user FL identity (field_leadership_users) ──
        user = await find_fl_user_by_email(db, email)
        if user and not user.get("disabled") and user.get("is_active", True):
            pwh = user.get("password_hash")
            if pwh and verify_password(payload.password, pwh):
                token = make_fl_user_token(user["id"], pwh)
                await stamp_fl_login(db, user["id"], _client_ip(request))
                try:
                    from session_timeout import reset_session_activity
                    await reset_session_activity(
                        db, token, "ADMIN_FL",
                        user_id=user.get("id"), email=user.get("email"),
                        actor_label="field_leadership", ip=_client_ip(request),
                        user_agent=request.headers.get("user-agent") or "",
                    )
                except Exception:  # noqa: BLE001
                    pass
                return {
                    "ok": True, "token": token, "kind": "fl",
                    "user": public_fl_user_view(user),
                    "must_change_password": bool(user.get("must_change_password")),
                }
        # ── Path 3 · iter345 · FL Phase B Hybrid · directory-granted FL
        #   For any directory user with `field_leadership` portal grant
        #   (PM/HR/Safety/Shop/Dispatch/etc. who have been granted FL
        #   access by Admin Access Control), mint an X-FL-Token bound
        #   to their MASTER user_directory password_hash. One person,
        #   one master password, multiple approved portal accesses.
        #   No duplicate field_leadership_users row created.
        if directory_admin_minter is not None:
            try:
                import user_directory as _ud  # noqa: WPS433
                row = await _ud.authenticate(db, email=email, password=payload.password)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"fl_login directory fallback error: {e}")
                row = None
            if row and not row.get("disabled"):
                row_portals = row.get("portals") or []
                # Path 3 · directory-granted FL → FL token tied to master pwh
                if "field_leadership" in row_portals:
                    pwh = row.get("password_hash") or ""
                    fl_tok = make_fl_user_token(row["id"], pwh)
                    try:
                        from session_timeout import reset_session_activity
                        await reset_session_activity(
                            db, fl_tok, "ADMIN_FL",
                            user_id=row.get("id"), email=row.get("email"),
                            actor_label="field_leadership_via_directory",
                            ip=_client_ip(request),
                            user_agent=request.headers.get("user-agent") or "",
                        )
                    except Exception:  # noqa: BLE001
                        pass
                    # Build a calm public view bridging directory shape
                    # to the FL UI's expected user object.
                    pub = _ud.public_view(row)
                    return {
                        "ok": True, "token": fl_tok, "kind": "fl",
                        "user": {
                            "id": pub.get("id"),
                            "email": pub.get("email"),
                            "name": pub.get("name") or pub.get("email"),
                            "role": "Cross-Portal Grant",
                            "is_active": True,
                            "disabled": bool(pub.get("disabled")),
                            "must_change_password": False,
                            "directory_user": True,
                            "granted_portals": pub.get("portals") or [],
                        },
                        "must_change_password": False,
                    }
        # ── Final · calm rejection ─────────────────────────────────
        raise HTTPException(401, "Invalid email or password")

    @router.post("/field-leadership/portal/change-password")
    async def fl_change_password(
        payload: FLChangePasswordPayload, actor=Depends(require_fl_user)
    ):
        if actor.get("_directory_user") or actor.get("directory_user"):
            try:
                import user_directory as _ud  # noqa: WPS433
                ok = await _ud.self_change_password(
                    db,
                    user_id=actor["id"],
                    current_password=payload.current_password or "",
                    new_password=payload.new_password,
                )
            except ValueError as ve:
                raise HTTPException(400, str(ve))
            if not ok:
                raise HTTPException(401, "Current password is incorrect")
            fresh_row = await _ud.find_by_id(db, actor["id"])
            if not fresh_row or not fresh_row.get("password_hash"):
                raise HTTPException(404, "user not found")
            new_token = make_fl_user_token(fresh_row["id"], fresh_row["password_hash"])
            try:
                from session_timeout import reset_session_activity  # noqa: PLC0415
                await reset_session_activity(
                    db, new_token, "ADMIN_FL",
                    user_id=fresh_row.get("id"), email=fresh_row.get("email"),
                    actor_label="field_leadership_via_directory",
                )
            except Exception:  # noqa: BLE001
                pass
            return {
                "ok": True,
                "token": new_token,
                "user": {
                    "id": fresh_row.get("id"),
                    "email": fresh_row.get("email"),
                    "name": fresh_row.get("name") or fresh_row.get("email"),
                    "role": "Cross-Portal Grant",
                    "is_active": True,
                    "disabled": bool(fresh_row.get("disabled")),
                    "must_change_password": False,
                    "directory_user": True,
                    "granted_portals": fresh_row.get("portals") or [],
                },
            }
        pwh = actor.get("password_hash") or ""
        if payload.current_password:
            if not pwh or not verify_password(payload.current_password, pwh):
                raise HTTPException(401, "Current password is incorrect")
        updated = await set_fl_user_password(
            db, actor["id"], payload.new_password, must_change=False
        )
        if not updated:
            raise HTTPException(404, "user not found")
        new_token = make_fl_user_token(updated["id"], updated["password_hash"])
        try:
            from session_timeout import reset_session_activity  # noqa: PLC0415
            await reset_session_activity(
                db, new_token, "ADMIN_FL",
                user_id=updated.get("id"), email=updated.get("email"),
                actor_label="field_leadership",
            )
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True, "token": new_token, "user": public_fl_user_view(updated)}

    @router.post("/field-leadership/portal/forgot-password")
    async def fl_forgot_password(payload: FLForgotPasswordPayload):
        email = (payload.email or "").strip().lower()
        if email:
            user = await find_fl_user_by_email(db, email)
            if user and not user.get("disabled") and user.get("password_hash"):
                token = make_fl_reset_token(user["id"], user["password_hash"])
                base = os.environ.get(
                    "PUBLIC_APP_URL", "https://mascidocs.com"
                ).rstrip("/")
                reset_url = f"{base}/field-leadership/portal/reset/{token}"
                if send_email_fn:
                    try:
                        body_html = (
                            f"<p style='margin:0 0 12px'>Hi {user.get('name')},</p>"
                            f"<p style='margin:0 0 12px'>We received a request to reset your "
                            f"MASCI Field Leadership Portal password. Click the button below "
                            f"to choose a new one. <strong>The link expires in 30 minutes.</strong></p>"
                            f"<p style='margin:18px 0 6px'>"
                            f"<a href='{reset_url}' style='display:inline-block;padding:11px 22px;"
                            f"background:#7e22ce;color:#fff;text-decoration:none;font-weight:700;"
                            f"border-radius:4px;font-size:13px'>Reset password</a></p>"
                            f"<p style='margin:12px 0 0;font-size:12px;color:#475569'>"
                            f"Or paste this URL into your browser:</p>"
                            f"<p style='margin:4px 0 0;font-family:Courier New,monospace;font-size:11px;"
                            f"color:#475569;word-break:break-all'>{reset_url}</p>"
                            f"<p style='margin:18px 0 0;font-size:12px;color:#94a3b8'>"
                            f"If you didn't request this, you can safely ignore this email.</p>"
                        )
                        html = render_portal_email(
                            portal="Field Leadership",
                            headline="Reset your password",
                            body_inner_html=body_html,
                        )
                        await send_email_fn(
                            user["email"],
                            "[MASCI] Reset your Field Leadership password",
                            html,
                        )
                    except Exception as e:  # noqa: BLE001
                        logger.warning(f"fl forgot-password email failed: {e}")
                else:
                    logger.info(f"[FL reset] {user['email']} → {reset_url}")
        return {"ok": True}

    @router.post("/field-leadership/portal/reset/{token}")
    async def fl_consume_reset(token: str, payload: FLResetPasswordPayload):
        user = await consume_fl_reset_token(db, token)
        if not user:
            raise HTTPException(400, "Reset link is invalid or expired")
        updated = await set_fl_user_password(
            db, user["id"], payload.new_password, must_change=False
        )
        new_token = make_fl_user_token(updated["id"], updated["password_hash"])
        try:
            from session_timeout import reset_session_activity  # noqa: PLC0415
            await reset_session_activity(
                db, new_token, "ADMIN_FL",
                user_id=updated.get("id"), email=updated.get("email"),
                actor_label="field_leadership",
            )
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True, "token": new_token, "user": public_fl_user_view(updated)}

    @router.get("/field-leadership/portal/me")
    async def fl_me(actor=Depends(require_fl_user)):
        return {"ok": True, "user": public_fl_user_view(actor)}

    # ─────────────────────────────────────────────────────────────────
    # OPERATIONAL VISIBILITY (bounded, read-only, FL-scoped)
    # ─────────────────────────────────────────────────────────────────
    @router.get("/field-leadership/portal/dispatch-today")
    async def fl_dispatch_today(actor=Depends(require_fl_user)):
        """Read-only dispatch visibility — TODAY and TOMORROW only,
        per operator iter314 bounded mandate. Field Leadership cannot
        see future-week dispatch (that lives in PM/Admin surfaces)."""
        from datetime import date, timedelta
        today = date.today()
        tomorrow = today + timedelta(days=1)
        target_dates = [today.isoformat(), tomorrow.isoformat()]
        items: List[Dict[str, Any]] = []
        async for d in db.dispatch_assignments.find(
            {"date": {"$in": target_dates}},
            {"_id": 0},
        ).sort("date", 1):
            items.append(d)
        return {
            "ok": True,
            "items": items,
            "count": len(items),
            "window": {"today": today.isoformat(), "tomorrow": tomorrow.isoformat()},
        }

    @router.get("/field-leadership/portal/driver-qualification")
    async def fl_driver_qualification(
        actor=Depends(require_fl_user),
        cdl_holder: Optional[bool] = Query(default=None),
        approved: Optional[bool] = Query(default=None),
        driver_status: Optional[str] = Query(default=None),
        endorsement: Optional[str] = Query(default=None),
        expiring_cdl_30d: Optional[bool] = Query(default=None),
        expiring_medical_30d: Optional[bool] = Query(default=None),
        available_now: Optional[bool] = Query(default=None),
        q: Optional[str] = Query(default=None, max_length=80),
        limit: int = Query(default=500, ge=1, le=2000),
    ):
        """iter353b · Read-only driver-qualification dashboard for FL.
        Uses the SAME shared helper as HR + Dispatch — identical
        data, identical filters, identical summary. FL has zero
        write authority on this surface (no PATCH peer exists)."""
        from lib.driver_qualification import fetch_driver_qualification_dashboard  # noqa: PLC0415
        try:
            payload = await fetch_driver_qualification_dashboard(
                db,
                cdl_holder=cdl_holder, approved=approved,
                driver_status=driver_status, endorsement=endorsement,
                expiring_cdl_30d=expiring_cdl_30d,
                expiring_medical_30d=expiring_medical_30d,
                available_now=available_now,
                q=q, limit=limit,
            )
        except ValueError as e:
            raise HTTPException(400, str(e))
        return {"ok": True, **payload, "viewer_role": "field_leadership"}

    # ═══════════════════════════════════════════════════════════════════
    # iter353d · FL Operational Accountability Expansion
    # ───────────────────────────────────────────────────────────────────
    # FL has been DQ-aware since iter353b but operationally blind to
    # the same employee's training/PPE/incidents/expirations. These
    # read-only endpoints close the audit gap WITHOUT granting FL any
    # HR write authority, Safety governance authority, or admin
    # authority. All endpoints are read-only — no write peers.
    # ═══════════════════════════════════════════════════════════════════

    @router.get("/field-leadership/portal/employee/{emp_id}/snapshot")
    async def fl_employee_snapshot(
        emp_id: str,
        actor=Depends(require_fl_user),
    ):
        """Compact accountability snapshot for ONE employee — the
        operational payload behind the FL Accountability Mini-Widget.
        Returns: CDL/medical readiness · training currency · PPE
        last-issued · recent incident count · expirations. Strictly
        a read aggregation; mutations happen in HR / Safety only."""
        emp = await db.employees.find_one({"id": emp_id, "deleted_at": None},
                                          {"_id": 0, "id": 1, "name": 1,
                                           "trade": 1, "crew": 1,
                                           "employee_id": 1,
                                           "lifecycle_status": 1,
                                           "cdl_holder": 1,
                                           "approved_company_driver": 1,
                                           "driver_status": 1,
                                           "cdl_expiration_date": 1,
                                           "medical_card_expiration_date": 1,
                                           "cdl_endorsements": 1})
        if not emp:
            raise HTTPException(404, "Employee not found")

        # Iter350 employee-linkage standard: match by employee_id OR
        # normalized name+email.
        ename = (emp.get("name") or "").strip()
        link_or = [{"employee_id": emp_id}, {"employee_master_id": emp_id}]
        if ename:
            link_or.append({"employee_name": ename})

        today = datetime.now(timezone.utc).isoformat()[:10]
        cutoff_30d = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()[:10]
        cutoff_90d = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()[:10]

        # Training currency
        training = []
        async for r in db.safety_training_records.find(
            {"$or": link_or},
            {"_id": 0, "id": 1, "training_name": 1, "certification_type": 1,
             "completed_date": 1, "expiration_date": 1, "notes": 1},
        ).sort("completed_date", -1).limit(50):
            training.append(r)
        # Track records (HR-curated)
        track = []
        async for r in db.training_track_records.find(
            {"$or": link_or},
            {"_id": 0, "id": 1, "training_name": 1, "completed_date": 1,
             "expiration_date": 1},
        ).sort("completed_date", -1).limit(20):
            track.append(r)

        # PPE
        ppe = []
        async for r in db.safety_equipment_issuances.find(
            {"$or": link_or},
            {"_id": 0, "id": 1, "equipment_type": 1, "issued_date": 1,
             "size": 1, "condition": 1},
        ).sort("issued_date", -1).limit(20):
            ppe.append(r)

        # Recent incidents — incidents store `person_name` string only
        incidents_count = 0
        if ename:
            incidents_count = await db.incidents.count_documents({
                "person_name": {"$regex": f"^{re.escape(ename)}$", "$options": "i"},
                "incident_date": {"$gte": (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()[:10]},
            })

        # Expirations summary
        expiring_30d = []
        expired = []
        for r in training + track:
            exp = r.get("expiration_date") or ""
            if not exp:
                continue
            if exp < today:
                expired.append({"title": r.get("training_name") or r.get("certification_type") or "Training",
                                "expiration_date": exp})
            elif exp <= cutoff_30d:
                expiring_30d.append({"title": r.get("training_name") or r.get("certification_type") or "Training",
                                     "expiration_date": exp})
        cdl_exp = emp.get("cdl_expiration_date") or ""
        med_exp = emp.get("medical_card_expiration_date") or ""
        if cdl_exp and cdl_exp < today:
            expired.append({"title": "CDL", "expiration_date": cdl_exp})
        elif cdl_exp and cdl_exp <= cutoff_30d:
            expiring_30d.append({"title": "CDL", "expiration_date": cdl_exp})
        if med_exp and med_exp < today:
            expired.append({"title": "Medical Card", "expiration_date": med_exp})
        elif med_exp and med_exp <= cutoff_30d:
            expiring_30d.append({"title": "Medical Card", "expiration_date": med_exp})

        # Readiness gate (same predicate as iter353b-availability)
        ready = (
            emp.get("driver_status") == "active"
            and emp.get("approved_company_driver") is True
            and (not emp.get("cdl_holder") or (cdl_exp and cdl_exp >= today))
            and (not med_exp or med_exp >= today)
            and not expired
        )

        return {
            "ok": True,
            "viewer_role": "field_leadership",
            "employee": emp,
            "readiness": {
                "available_now": bool(ready),
                "expired_count": len(expired),
                "expiring_within_30d": len(expiring_30d),
                "training_record_count": len(training),
                "track_record_count": len(track),
                "ppe_record_count": len(ppe),
                "incident_count_last_365d": incidents_count,
            },
            "training": training[:10],
            "ppe": ppe[:10],
            "expiring_30d": expiring_30d,
            "expired": expired,
            "as_of": today,
        }

    @router.get("/field-leadership/portal/incidents-recent")
    async def fl_incidents_recent(
        actor=Depends(require_fl_user),
        days: int = Query(default=14, ge=1, le=90),
        limit: int = Query(default=100, ge=1, le=500),
    ):
        """iter353d · FL read-only window into recent incidents.
        Default 14d, max 90d. No filter / closeout / edit authority."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()[:10]
        items = []
        async for r in db.incidents.find(
            {"incident_date": {"$gte": cutoff}},
            {"_id": 0, "id": 1, "incident_date": 1, "person_name": 1,
             "incident_type": 1, "severity": 1, "project_name": 1,
             "description": 1, "status": 1},
        ).sort("incident_date", -1).limit(limit):
            items.append(r)
        return {"ok": True, "items": items, "count": len(items),
                "window_days": days, "viewer_role": "field_leadership"}

    @router.get("/field-leadership/portal/notifications-recent")
    async def fl_notifications_recent(
        actor=Depends(require_fl_user),
        limit: int = Query(default=50, ge=1, le=200),
    ):
        """iter353d · FL read-only notifications view. Returns the
        last N notifications where recipient_role is `fl` OR
        `safety` OR `pm` (FL needs operational situational awareness
        on what the rest of the team is being notified about)."""
        items = []
        async for r in db.notifications.find(
            {"recipient_role": {"$in": ["fl", "safety", "pm"]}},
            {"_id": 0},
        ).sort("created_at", -1).limit(limit):
            items.append(r)
        return {"ok": True, "items": items, "count": len(items),
                "viewer_role": "field_leadership"}

    # ═══════════════════════════════════════════════════════════════════
    # iter Phase 5 · W5 closeout — FL Training/PPE aggregate visibility
    # ───────────────────────────────────────────────────────────────────
    # Closes the final field-leadership operational blind spot identified
    # by FINAL_OPERATIONAL_COMMUNICATION_VERIFICATION.md (Gap W5). FL has
    # had per-employee snapshot since iter353d; these endpoints provide
    # the cross-crew aggregate view FL needs to make crew-assignment
    # decisions ("who is expired/expiring/missing?").
    #
    # Strictly read-only · no writes · no new collections · mirrors the
    # PM crew pattern (`/api/pm/crew/training-records`,
    # `/api/pm/crew/ppe`) without the PM scope filter (FL portal is
    # company-wide read by design — see iter353d).
    # ═══════════════════════════════════════════════════════════════════

    @router.get("/field-leadership/portal/crew/training-records")
    async def fl_crew_training_records(
        actor=Depends(require_fl_user),
        status: Optional[str] = Query(
            default=None,
            description="Filter: 'expired' · 'expiring_30d' · None (all)",
        ),
        limit: int = Query(default=200, ge=1, le=500),
    ):
        """Phase 5 · W5 · FL read-only training records aggregate.
        Returns the last N training records across all crew; supports
        an optional ``status`` filter for expired or expiring-within-30d.
        No write peer — FL cannot create or edit training records."""
        today = datetime.now(timezone.utc).isoformat()[:10]
        cutoff_30d = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()[:10]
        q: Dict[str, Any] = {}
        if status == "expired":
            q = {"expiration_date": {"$lt": today, "$ne": ""}}
        elif status == "expiring_30d":
            q = {"expiration_date": {"$gte": today, "$lte": cutoff_30d}}
        items = []
        async for r in db.safety_training_records.find(
            q,
            {"_id": 0, "id": 1, "employee_id": 1, "employee_name": 1,
             "training_name": 1, "certification_type": 1,
             "completed_date": 1, "expiration_date": 1, "notes": 1,
             "created_by_role": 1},
        ).sort("expiration_date", 1).limit(limit):
            items.append(r)
        return {
            "ok": True,
            "items": items,
            "count": len(items),
            "filter": status or "all",
            "viewer_role": "field_leadership",
            "as_of": today,
        }

    @router.get("/field-leadership/portal/crew/ppe")
    async def fl_crew_ppe(
        actor=Depends(require_fl_user),
        limit: int = Query(default=200, ge=1, le=500),
    ):
        """Phase 5 · W5 · FL read-only PPE issuance aggregate. Most-
        recently issued PPE across all crew (helps FL spot crew members
        who haven't been issued PPE recently). No write peer."""
        items = []
        async for r in db.safety_equipment_issuances.find(
            {},
            {"_id": 0, "id": 1, "employee_name": 1, "equipment_type": 1,
             "issued_date": 1, "size": 1, "condition": 1},
        ).sort("issued_date", -1).limit(limit):
            items.append(r)
        return {
            "ok": True,
            "items": items,
            "count": len(items),
            "viewer_role": "field_leadership",
        }

    @router.get("/field-leadership/portal/crew/training-summary")
    async def fl_crew_training_summary(actor=Depends(require_fl_user)):
        """Phase 5 · W5 · FL crew-readiness summary roll-up.
        Returns one-glance counts: expired training · expiring within
        30d · PPE records on file. Drives the FL "is this crew safe to
        deploy?" decision without exposing individual employee detail."""
        today = datetime.now(timezone.utc).isoformat()[:10]
        cutoff_30d = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()[:10]
        expired_count = await db.safety_training_records.count_documents({
            "expiration_date": {"$lt": today, "$ne": ""}
        })
        expiring_30d_count = await db.safety_training_records.count_documents({
            "expiration_date": {"$gte": today, "$lte": cutoff_30d}
        })
        ppe_records = await db.safety_equipment_issuances.count_documents({})
        # Employees with any active driver readiness (active drivers).
        active_drivers = await db.employees.count_documents({
            "driver_status": "active",
            "approved_company_driver": True,
            "deleted_at": None,
        })
        return {
            "ok": True,
            "viewer_role": "field_leadership",
            "as_of": today,
            "expired_count": expired_count,
            "expiring_within_30d_count": expiring_30d_count,
            "ppe_records": ppe_records,
            "active_company_drivers": active_drivers,
        }

    # ═══════════════════════════════════════════════════════════════════
    # Phase 5 · W3 closeout — FL read-only daily-report visibility
    # ───────────────────────────────────────────────────────────────────
    # FL needs to see daily reports so they can verify crew continuity
    # ("did the crew show up today? · was there an incident? · what
    # subs were on site?"). Read-only company-wide — same access scope
    # as the existing iter353d FL portal surfaces. No write peer.
    # ═══════════════════════════════════════════════════════════════════
    @router.get("/field-leadership/portal/daily-reports")
    async def fl_daily_reports(
        actor=Depends(require_fl_user),
        days: int = Query(default=7, ge=1, le=30),
        limit: int = Query(default=200, ge=1, le=500),
    ):
        """Phase 5 · W3 · FL read-only daily-report visibility.
        Default 7-day window, max 30 days. Projects crew/subcontractor/
        incident-flag fields only — FL doesn't need labor cost or
        incident-narrative detail (those belong to PM/Safety)."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()[:10]
        # TRACK 28.02B · exclude synthetic rows from the FL portal DR view.
        pipeline = [
            {"$match": apply_synthetic_dr_exclusion({"report_date": {"$gte": cutoff}})},
            {"$sort": {"report_date": -1, "created_at": -1}},
            {"$limit": limit},
            {"$project": {
                "_id": 0, "id": 1, "project_name": 1, "project_number": 1,
                "location": 1, "report_date": 1, "prepared_by": 1,
                "superintendent": 1, "weather_summary": 1,
                "schedule_delays": 1, "weather_impact": 1,
                "safety_incidents_today": 1, "injuries_reported": 1,
                "created_at": 1,
                "crew_count":     {"$size": {"$ifNull": ["$masci_crews", []]}},
                "sub_count":      {"$size": {"$ifNull": ["$subcontractors", []]}},
                "visitor_count":  {"$size": {"$ifNull": ["$visitors", []]}},
            }},
        ]
        items = await db.daily_reports.aggregate(pipeline).to_list(limit)
        return {
            "ok": True,
            "items": items,
            "count": len(items),
            "window_days": days,
            "viewer_role": "field_leadership",
        }

    # ─────────────────────────────────────────────────────────────────
    # ADMIN/HR — FL user management (HR + Admin both can manage)
    # ─────────────────────────────────────────────────────────────────
    async def _send_welcome_email(user_email: str, name: str, temp_password: str):
        if not send_email_fn:
            logger.info(f"[FL welcome] {user_email} → {temp_password}")
            return
        base = os.environ.get("PUBLIC_APP_URL", "https://mascidocs.com").rstrip("/")
        login_url = f"{base}/field-leadership/portal/login"
        body_html = (
            f"<p style='margin:0 0 12px'>Hi {name},</p>"
            f"<p style='margin:0 0 12px'>Your MASCI Field Leadership Portal "
            f"account has been created. This portal is for "
            f"<strong>approved Field Leadership personnel only</strong> — "
            f"Superintendents, Foremen, Truck Bosses, and Working Supervisors. "
            f"Sign in with your work email and the temporary password below — "
            f"<strong>you'll be asked to choose your own password on first "
            f"login.</strong></p>"
            f"<table style='margin:14px 0;border-collapse:collapse;width:100%;'>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;"
            f"text-transform:uppercase;letter-spacing:0.18em;font-size:10px;"
            f"color:#475569;font-weight:bold;width:42%'>Sign-in URL</td>"
            f"      <td style='padding:6px 0;font-size:13px;'>"
            f"<a href='{login_url}' style='color:#7e22ce;font-weight:600'>{login_url}</a></td></tr>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;"
            f"text-transform:uppercase;letter-spacing:0.18em;font-size:10px;"
            f"color:#475569;font-weight:bold;'>Email</td>"
            f"      <td style='padding:6px 0;font-family:Courier New,monospace;"
            f"font-size:13px;color:#0f172a'>{user_email}</td></tr>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;"
            f"text-transform:uppercase;letter-spacing:0.18em;font-size:10px;"
            f"color:#475569;font-weight:bold;'>Temporary password</td>"
            f"      <td style='padding:6px 0;font-family:Courier New,monospace;"
            f"font-size:14px;color:#0f172a;background:#f8fafc;border:1px dashed #94a3b8;"
            f"padding-left:8px;border-radius:4px'><strong>{temp_password}</strong></td></tr>"
            f"</table>"
            f"<p style='margin:14px 0 6px'>"
            f"<a href='{login_url}' style='display:inline-block;padding:11px 22px;"
            f"background:#7e22ce;color:#fff;text-decoration:none;font-weight:700;"
            f"border-radius:4px;font-size:13px'>Sign in &amp; set password</a></p>"
            f"<p style='margin:18px 0 0;font-size:12px;color:#94a3b8'>"
            f"For security, please change your password immediately after signing in. "
            f"This portal is operationally bounded — it does not include HR admin, "
            f"payroll, or system configuration surfaces.</p>"
        )
        html = render_portal_email(
            portal="Field Leadership",
            headline="Your MASCI Field Leadership account",
            body_inner_html=body_html,
        )
        try:
            await send_email_fn(
                user_email,
                "[MASCI] Your Field Leadership account — temporary password inside",
                html,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"fl welcome email failed: {e}")

    @router.get(
        "/admin/field-leadership-users",
        dependencies=[Depends(require_hr_or_admin)],
    )
    async def admin_list_fl():
        users = await list_fl_users(db)
        return {
            "ok": True,
            "users": [public_fl_user_view(u) for u in users],
            "allowed_roles": sorted(ALLOWED_FL_ROLES),
        }

    @router.post(
        "/admin/field-leadership-users",
        dependencies=[Depends(require_hr_or_admin)],
    )
    async def admin_create_fl(payload: FLUserCreate):
        try:
            user = await add_fl_user(db, payload.dict())
        except ValueError as e:
            raise HTTPException(400, str(e))
        delivery = (payload.delivery or "email").lower()
        if delivery == "custom" and payload.custom_password:
            temp = payload.custom_password
        else:
            temp = generate_temp_password()
        await set_fl_user_password(db, user["id"], temp, must_change=True)
        if delivery == "email":
            await _send_welcome_email(user["email"], user["name"], temp)
        fresh = await db.field_leadership_users.find_one(
            {"id": user["id"]}, {"_id": 0}
        )
        return {
            "ok": True,
            "user": public_fl_user_view(fresh),
            "temp_password": temp if delivery != "email" else None,
        }

    @router.patch(
        "/admin/field-leadership-users/{user_id}",
        dependencies=[Depends(require_hr_or_admin)],
    )
    async def admin_patch_fl(user_id: str, payload: FLUserPatch):
        try:
            updated = await update_fl_user(
                db, user_id, payload.dict(exclude_unset=True)
            )
        except ValueError as e:
            raise HTTPException(400, str(e))
        if not updated:
            raise HTTPException(404, "user not found")
        return {"ok": True, "user": public_fl_user_view(updated)}

    @router.post(
        "/admin/field-leadership-users/{user_id}/reset-password",
        dependencies=[Depends(require_hr_or_admin)],
    )
    async def admin_reset_fl_password(
        user_id: str, request: Request, body: Dict[str, Any] = Body(default={})
    ):
        delivery = (body.get("delivery") or "email").lower()
        custom = body.get("custom_password")
        temp = str(custom) if delivery == "custom" and custom else generate_temp_password()
        updated = await set_fl_user_password(db, user_id, temp, must_change=True)
        if not updated:
            raise HTTPException(404, "user not found")
        if delivery == "email":
            await _send_welcome_email(updated["email"], updated["name"], temp)
        # iter502 · OMEGA IAM Enterprise Phase B+C
        try:
            from lib.iam_password_audit import stamp_and_audit_temp_password, audit_welcome_email_sent
            await stamp_and_audit_temp_password(
                db,
                collection_name="field_leadership_users",
                user_filter={"id": user_id},
                target_email=str(updated.get("email") or ""),
                portal="field_leadership",
                delivery=delivery,
                request=request,
            )
            if delivery == "email":
                await audit_welcome_email_sent(
                    db, target_email=str(updated.get("email") or ""), portal="field_leadership", request=request,
                )
        except Exception:
            pass
        return {
            "ok": True,
            "user": public_fl_user_view(updated),
            "temp_password": temp if delivery != "email" else None,
        }

    @router.post(
        "/admin/field-leadership-users/{user_id}/resend-welcome",
        dependencies=[Depends(require_hr_or_admin)],
    )
    async def admin_resend_welcome_fl(user_id: str, request: Request):
        """Issue a fresh temp password AND re-send the welcome email."""
        temp = generate_temp_password()
        updated = await set_fl_user_password(db, user_id, temp, must_change=True)
        if not updated:
            raise HTTPException(404, "user not found")
        await _send_welcome_email(updated["email"], updated["name"], temp)
        # iter502 · OMEGA IAM Enterprise Phase B+C
        try:
            from lib.iam_password_audit import stamp_and_audit_temp_password, audit_welcome_email_sent
            await stamp_and_audit_temp_password(
                db,
                collection_name="field_leadership_users",
                user_filter={"id": user_id},
                target_email=str(updated.get("email") or ""),
                portal="field_leadership",
                delivery="email",
                request=request,
            )
            await audit_welcome_email_sent(
                db, target_email=str(updated.get("email") or ""), portal="field_leadership", request=request,
            )
        except Exception:
            pass
        return {
            "ok": True,
            "user": public_fl_user_view(updated),
            "temp_password": None,  # always email-only for resend
        }

    @router.delete(
        "/admin/field-leadership-users/{user_id}",
        dependencies=[Depends(require_hr_or_admin)],
    )
    async def admin_delete_fl(user_id: str):
        ok = await delete_fl_user(db, user_id)
        if not ok:
            raise HTTPException(404, "user not found")
        return {"ok": True}

    # ─────────────────────────────────────────────────────────────────
    # PUBLIC roster (name + role only)
    # ─────────────────────────────────────────────────────────────────
    # Phase V.2 · Daily Report Field-Logic Refinement (2026-05-29):
    # the foreman-facing Daily Report (/daily/new) is a public form,
    # so its Prepared By + Superintendent role pickers cannot require
    # admin / HR / FL auth.  This endpoint returns only the minimum
    # data the picker needs (name + role + active flag) and strips
    # ALL contact / login / session fields.  Doctrine:
    #   - REPORT_ROLE_PICKER_CERTIFICATION.md
    @router.get("/field-leadership-roster")
    async def public_fl_roster(
        role: Optional[str] = Query(default=None),
    ):
        users = await list_fl_users(db, only_active=True)
        items: List[Dict[str, Any]] = []
        for u in users:
            raw_role = (u.get("role") or "").strip()
            canon = _canonical_role(raw_role)
            # Optional server-side filter — accept canonical OR label OR raw.
            if role:
                want = role.strip().lower()
                if want not in (canon["value"], canon["label"].lower(),
                                raw_role.lower()):
                    continue
            items.append({
                "name": (u.get("name") or "").strip(),
                "role_value": canon["value"],     # canonical key
                "role_label": canon["label"],     # display label
                "role_raw":   raw_role,           # what's stored in DB
                "role_uncertain": canon["uncertain"],
                "role_uncertain_note": canon["uncertain_note"],
                "is_active": bool(u.get("is_active", True)),
                # Legacy "role" key preserved so older clients keep working
                "role": canon["label"],
            })
        return {
            "items": items,
            "count": len(items),
            "canonical_roles": [
                {"value": v, "label": l}
                for v, l in FL_CANONICAL_ROLES.items()
            ],
            # Back-compat: existing pickers consuming `allowed_roles`
            # still receive the legacy set so old wire-format clients
            # don't break.
            "allowed_roles": sorted(ALLOWED_FL_ROLES),
        }

    return router
