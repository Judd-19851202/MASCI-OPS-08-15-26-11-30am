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


def build_hr_portal_router(db, require_admin_dep: Callable, send_email_fn: Optional[Callable] = None) -> APIRouter:
    """Assemble the HR portal router. `db` = motor db; `require_admin_dep`
    = the FastAPI admin-only dependency from server.py; `send_email_fn`
    = optional `async (to, subject, html) -> None` for credential
    delivery — falls back to log-only when not provided."""
    router = APIRouter(prefix="/api", tags=["hr-portal"])

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
        if not user or user.get("disabled") or not user.get("is_active", True):
            raise HTTPException(401, "Invalid email or password")
        pwh = user.get("password_hash")
        if not pwh or not verify_password(payload.password, pwh):
            raise HTTPException(401, "Invalid email or password")
        token = make_hr_user_token(user["id"], pwh)
        await stamp_hr_login(db, user["id"], _client_ip(request))
        # Initiative 4 fix — HR tokens are deterministic per
        # (user_id, password_hash). Reset session_activity so a
        # post-idle re-login doesn't inherit a stale row.
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
            "user": public_hr_user_view(user),
            "must_change_password": bool(user.get("must_change_password")),
        }

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

        # Training records (training_track_records collection)
        trainings: List[Dict[str, Any]] = []
        async for t in db.training_track_records.find({"employee_name": rx}, {"_id": 0}).sort("completed_at", -1).limit(200):
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
    # TRAINING RECORDS
    # ─────────────────────────────────────────────────────────────────
    @router.get("/hr/training-records")
    async def hr_training_records(
        actor=Depends(require_hr_user),
        employee: Optional[str] = None,
        track: Optional[str] = None,
        limit: int = 500,
    ):
        query: Dict[str, Any] = {}
        if employee:
            query["employee_name"] = {"$regex": employee, "$options": "i"}
        if track:
            query["track_slug"] = track
        out = []
        async for d in db.training_track_records.find(query, {"_id": 0}).sort("completed_at", -1).limit(min(limit, 1000)):
            out.append(d)
        return {"ok": True, "items": out, "count": len(out)}

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
