"""
routes/pm_admin.py · iter382 · Phase 4D · PM administration routes.

EXTRACTED FROM server.py (10 endpoints, ≈310 LOC):

  • GET    /admin/project-managers/export        (xlsx export)
  • GET    /admin/project-managers               (list, admin)
  • GET    /project-managers                     (PUBLIC active list — drives
                                                  every PM dropdown)
  • POST   /admin/project-managers               (create, admin)
  • PATCH  /admin/project-managers/{pm_id}       (update + cascade to jobs)
  • DELETE /admin/project-managers/{pm_id}       (delete, w/ job-assignment guard)
  • POST   /admin/project-managers/{pm_id}/set-password    (admin-strict)
  • POST   /admin/project-managers/{pm_id}/welcome-pdf     (admin-strict)
  • POST   /admin/project-managers/{pm_id}/email-welcome   (admin-strict)
  • POST   /admin/project-managers/{pm_id}/disable         (admin-strict)
  • GET    /admin/project-managers/activity               (admin-strict)

Behavior contract (locked by tests/test_iter382_pm_admin_extraction.py):
  byte-identical to pre-extraction. Includes:
    • Cascade-on-email-change to jobs_master (PATCH).
    • Job-assignment guard on DELETE (409 if PM still on jobs).
    • Issue-temp-password generator + must_change_password=true semantics.
    • Email send via Resend with PDF attachment (email-welcome).
    • Per-PM activity rollup across 7 collections in 7-day window.
"""
from __future__ import annotations

import asyncio
import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import Response as _FastAPIResponse
from pydantic import BaseModel, Field


# ─── Body models (mirrored from server.py) ───────────────────────────

class PMIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=300)
    phone: str = ""
    is_active: bool = True


class PMUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class PMSetPasswordBody(BaseModel):
    password: Optional[str] = None


def _portal_url() -> str:
    return (os.environ.get("PORTAL_URL", "").strip()
            or os.environ.get("PRODUCTION_URL", "").strip()
            or "https://mascidocs.com")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_pm_admin_router(
    db,
    require_admin_dep: Callable,
    require_admin_strict_dep: Callable,
    xlsx_response_fn: Callable,
    today_stamp_fn: Callable[[], str],
    active_filter: Dict[str, Any],
    render_portal_email_fn: Callable[..., str],
) -> APIRouter:
    """Build the PM admin + public-list router. See module docstring."""
    router = APIRouter(prefix="/api", tags=["pm-admin"])

    # ─── Public ───────────────────────────────────────────────────
    @router.get("/project-managers")
    async def public_list_active_pms():
        """Public — drives the PM dropdown across the platform.
        Returns ONLY active PMs with name + id + email (no phone)."""
        from project_managers import list_pms  # noqa: PLC0415
        pms = await list_pms(db, only_active=True)
        return {
            "items": [
                {"id": p["id"], "name": p["name"], "email": p["email"]}
                for p in pms
            ]
        }

    # ─── Admin list / export ──────────────────────────────────────
    @router.get("/admin/project-managers",
                dependencies=[Depends(require_admin_dep)])
    async def admin_list_pms():
        from project_managers import list_pms  # noqa: PLC0415
        from pm_auth import public_pm_view  # noqa: PLC0415
        items = await list_pms(db, only_active=False)
        return {"items": [public_pm_view(p) for p in items]}

    @router.get("/admin/project-managers/export",
                dependencies=[Depends(require_admin_dep)])
    async def export_project_managers():
        cursor = db.project_managers.find(active_filter, {"_id": 0}).sort("name", 1)
        docs = await cursor.to_list(2000)
        header = ["Name", "Email", "Phone", "Active"]
        rows = [
            [
                d.get("name", ""),
                d.get("email", ""),
                d.get("phone", ""),
                "Yes" if d.get("active", True) else "No",
            ]
            for d in docs
        ]
        return xlsx_response_fn(rows, header, f"MASCI_pms_{today_stamp_fn()}.xlsx", "PMs")

    # ─── Admin create / update / delete ──────────────────────────
    @router.post("/admin/project-managers",
                 dependencies=[Depends(require_admin_dep)])
    async def admin_add_pm(body: PMIn):
        from project_managers import add_pm  # noqa: PLC0415
        try:
            return await add_pm(db, body.model_dump())
        except ValueError as e:
            raise HTTPException(400, str(e))

    @router.patch("/admin/project-managers/{pm_id}",
                  dependencies=[Depends(require_admin_dep)])
    async def admin_update_pm(pm_id: str, body: PMUpdate):
        from project_managers import update_pm  # noqa: PLC0415
        fields = {k: v for k, v in body.model_dump().items() if v is not None}
        if not fields:
            raise HTTPException(400, "No fields to update")
        try:
            old = await db.project_managers.find_one({"id": pm_id}, {"_id": 0})
            old_email = (old or {}).get("email", "").lower()
            saved = await update_pm(db, pm_id, fields)
            if not saved:
                raise HTTPException(404, "PM not found")
            new_email = (saved.get("email") or "").lower()
            # Cascade email change to every job that referenced the old email.
            if old_email and new_email and old_email != new_email:
                await db.jobs_master.update_many(
                    {"pm_email": old_email},
                    {"$set": {
                        "pm_email": new_email,
                        "project_manager": saved.get("name") or "",
                        "updated_at": _now_iso(),
                    }},
                )
            # Cascade name change to every job referencing this PM by email.
            if "name" in fields and new_email:
                await db.jobs_master.update_many(
                    {"pm_email": new_email},
                    {"$set": {
                        "project_manager": saved.get("name") or "",
                        "updated_at": _now_iso(),
                    }},
                )
            return saved
        except ValueError as e:
            raise HTTPException(400, str(e))

    @router.delete("/admin/project-managers/{pm_id}",
                   dependencies=[Depends(require_admin_dep)])
    async def admin_delete_pm(pm_id: str):
        from project_managers import delete_pm  # noqa: PLC0415
        pm = await db.project_managers.find_one({"id": pm_id}, {"_id": 0})
        if not pm:
            raise HTTPException(404, "PM not found")
        pm_email = (pm.get("email") or "").lower()
        job_count = await db.jobs_master.count_documents({"pm_email": pm_email})
        if job_count > 0:
            raise HTTPException(
                409,
                f"{pm.get('name')} is still assigned to {job_count} job(s). "
                f"Reassign those jobs first, or deactivate the PM instead.",
            )
        ok = await delete_pm(db, pm_id)
        if not ok:
            raise HTTPException(404, "PM not found")
        return {"ok": True}

    # ─── Admin-strict: password + disable + activity ────────────
    @router.post("/admin/project-managers/{pm_id}/set-password",
                 dependencies=[Depends(require_admin_strict_dep)])
    async def admin_set_pm_password(pm_id: str, body: PMSetPasswordBody, request: Request):
        from pm_auth import (  # noqa: PLC0415
            find_pm_by_id, generate_temp_password,
            public_pm_view, set_pm_password,
        )
        pm = await find_pm_by_id(db, pm_id)
        if not pm:
            raise HTTPException(404, "PM not found")
        if body.password and len(body.password) < 6:
            raise HTTPException(400, "Password must be at least 6 characters")
        plain = body.password or generate_temp_password(10)
        updated = await set_pm_password(db, pm_id, plain, must_change=True)
        if not updated:
            raise HTTPException(500, "Failed to set password")
        # iter502 · OMEGA IAM Enterprise Phase B+C
        try:
            from lib.iam_password_audit import stamp_and_audit_temp_password
            await stamp_and_audit_temp_password(
                db,
                collection_name="project_managers",
                user_filter={"id": pm_id},
                target_email=str(updated.get("email") or ""),
                portal="pm",
                delivery="custom" if body.password else "screen",
                request=request,
            )
        except Exception:
            pass
        return {
            "ok": True,
            "pm": public_pm_view(updated),
            "issued_password": plain,
            "generated": body.password is None,
        }

    @router.post("/admin/project-managers/{pm_id}/welcome-pdf",
                 dependencies=[Depends(require_admin_strict_dep)])
    async def admin_pm_welcome_pdf(pm_id: str, body: PMSetPasswordBody):
        from pm_auth import (  # noqa: PLC0415
            find_pm_by_id, generate_temp_password,
            public_pm_view, set_pm_password,
        )
        from pm_welcome_pdf import render_pm_welcome_pdf  # noqa: PLC0415

        pm = await find_pm_by_id(db, pm_id)
        if not pm:
            raise HTTPException(404, "PM not found")
        if body.password and len(body.password) < 6:
            raise HTTPException(400, "Password must be at least 6 characters")
        plain = body.password or generate_temp_password(10)
        updated = await set_pm_password(db, pm_id, plain, must_change=True)
        if not updated:
            raise HTTPException(500, "Failed to set password")
        try:
            pdf_bytes = await asyncio.to_thread(
                render_pm_welcome_pdf,
                public_pm_view(updated),
                temp_password=plain,
                portal_url=_portal_url(),
            )
        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                500, f"Password set, but PDF rendering failed: {e}",
            )
        safe_name = (updated.get("name") or "pm").replace(" ", "_")
        fname = f"MASCI_PM_Welcome_{safe_name}.pdf"
        return _FastAPIResponse(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )

    @router.post("/admin/project-managers/{pm_id}/email-welcome",
                 dependencies=[Depends(require_admin_strict_dep)])
    async def admin_pm_email_welcome(pm_id: str, body: PMSetPasswordBody, request: Request):
        api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
        if not api_key:
            raise HTTPException(
                503,
                "RESEND_API_KEY not configured. "
                "Use 'Generate & Download Welcome PDF' instead, or add the key to backend env.",
            )

        from pm_auth import (  # noqa: PLC0415
            find_pm_by_id, generate_temp_password,
            public_pm_view, set_pm_password,
        )
        from pm_welcome_pdf import render_pm_welcome_pdf  # noqa: PLC0415

        pm = await find_pm_by_id(db, pm_id)
        if not pm:
            raise HTTPException(404, "PM not found")
        pm_email = (pm.get("email") or "").strip()
        pm_name = (pm.get("name") or "").strip() or "Project Manager"
        if not pm_email:
            raise HTTPException(400, "PM has no email address on file")
        if body.password and len(body.password) < 6:
            raise HTTPException(400, "Password must be at least 6 characters")

        plain = body.password or generate_temp_password(10)
        updated = await set_pm_password(db, pm_id, plain, must_change=True)
        if not updated:
            raise HTTPException(500, "Failed to set password")

        portal_url = _portal_url()
        pdf_bytes = await asyncio.to_thread(
            render_pm_welcome_pdf,
            public_pm_view(updated),
            temp_password=plain,
            portal_url=portal_url,
        )

        is_reset = bool(pm.get("password_hash"))
        headline = "Your password has been reset" if is_reset else "Welcome to the MASCI PM Portal"
        body_inner = f"""
          <p style="margin:0 0 12px;font-size:15px;line-height:1.5">Hi {pm_name},</p>
          <p style="margin:0 0 12px;font-size:14px;line-height:1.55;color:#334155">
            {'Your MASCI PM Portal password has been reset. Use the temporary password below to sign in — you will be forced to choose your own on first login.' if is_reset else 'You have a new account on the MASCI PM Portal at <a href="' + portal_url + '/pm/login" style="color:#b91c1c;font-weight:700">' + portal_url + '/pm/login</a>. Use the temporary password below to sign in — you will be forced to choose your own on first login.'}
          </p>

          <table cellpadding="0" cellspacing="0" style="background:#0f172a;color:#f1f5f9;border-radius:6px;padding:18px 22px;margin:16px 0;width:100%;max-width:480px">
            <tr><td>
              <div style="font-family:Courier New,monospace;font-size:9px;letter-spacing:0.22em;color:#94a3b8;text-transform:uppercase;font-weight:700">Account</div>
              <div style="font-family:Courier New,monospace;font-size:13px;font-weight:800;margin-top:3px">{pm_email}</div>
              <div style="font-family:Courier New,monospace;font-size:9px;letter-spacing:0.22em;color:#94a3b8;text-transform:uppercase;font-weight:700;margin-top:14px">Temporary password</div>
              <div style="font-family:Courier New,monospace;font-size:20px;font-weight:800;color:#34d399;letter-spacing:0.05em;margin-top:3px">{plain}</div>
            </td></tr>
          </table>

          <p style="margin:14px 0 6px;font-size:14px;line-height:1.55"><strong>What to do next</strong></p>
          <ol style="margin:0 0 14px 18px;padding:0;font-size:14px;line-height:1.55;color:#334155">
            <li>Open <a href="{portal_url}/pm/login" style="color:#b91c1c;font-weight:700">{portal_url}/pm/login</a></li>
            <li>Sign in with the email + temporary password above</li>
            <li>Pick your own 6+ character password (the temp one stops working immediately)</li>
            <li>You'll only see your assigned jobs — Daily Reports, Inspections, Meetings, Incidents, JHAs, Equipment Pre-Op, QA/QC, and your P&amp;L snapshot all auto-route to you</li>
          </ol>

          <p style="margin:14px 0 0;font-size:13px;color:#64748b;line-height:1.55">
            The attached PDF has the full walkthrough. If you forget your password, just call the office — admin can issue a new temp pw in 30 seconds.
          </p>
        """
        html_body = render_portal_email_fn(
            portal="PM", headline=headline, body_inner_html=body_inner,
        )

        import resend  # noqa: E402,PLC0415
        resend.api_key = api_key
        from branding_resolver import (
            resolve_sender_email as _resolve_sender_email,
            resolve_reply_to_email as _resolve_reply_to_email,
        )
        sender_email = await _resolve_sender_email(db)
        reply_to = (await _resolve_reply_to_email(db)) or ""
        safe_name = pm_name.replace(" ", "_")
        fname = f"MASCI_PM_Welcome_{safe_name}.pdf"

        params: Dict[str, Any] = {
            "from": f"MASCI Operations Platform <{sender_email}>",
            "to": [pm_email],
            "subject": f"[MASCI · ACCESS] {headline}",
            "html": html_body,
            "attachments": [
                {"filename": fname, "content": base64.b64encode(pdf_bytes).decode()}
            ],
        }
        if reply_to:
            params["reply_to"] = reply_to

        try:
            result = await asyncio.to_thread(resend.Emails.send, params)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                502,
                f"Password rotated but email send failed via Resend: {e}. "
                "Use 'Download Welcome PDF' to recover the new temp password.",
            )

        # iter502 · OMEGA IAM Enterprise Phase B+C
        try:
            from lib.iam_password_audit import stamp_and_audit_temp_password, audit_welcome_email_sent
            await stamp_and_audit_temp_password(
                db,
                collection_name="project_managers",
                user_filter={"id": pm_id},
                target_email=pm_email,
                portal="pm",
                delivery="email",
                request=request,
            )
            await audit_welcome_email_sent(
                db, target_email=pm_email, portal="pm", request=request,
            )
        except Exception:
            pass

        return {
            "ok": True,
            "pm": public_pm_view(updated),
            "sent_to": pm_email,
            "resend_id": (result or {}).get("id") if isinstance(result, dict) else None,
        }

    @router.post("/admin/project-managers/{pm_id}/disable",
                 dependencies=[Depends(require_admin_strict_dep)])
    async def admin_set_pm_disabled(pm_id: str, body: dict):
        from pm_auth import public_pm_view, set_pm_disabled  # noqa: PLC0415
        disabled = bool(body.get("disabled", True))
        updated = await set_pm_disabled(db, pm_id, disabled)
        if not updated:
            raise HTTPException(404, "PM not found")
        return {"ok": True, "pm": public_pm_view(updated)}

    @router.get("/admin/project-managers/activity",
                dependencies=[Depends(require_admin_strict_dep)])
    async def admin_pm_activity():
        """Per-PM activity rollup for the admin Activity column."""
        from pm_auth import public_pm_view  # noqa: PLC0415

        pm_cursor = db.project_managers.find({}, {"_id": 0})
        pms: List[dict] = []
        async for p in pm_cursor:
            pms.append(p)

        by_email: dict = {}
        job_cursor = db.jobs_master.find(
            {"deleted_at": {"$in": [None, ""]}},
            {"_id": 0, "pm_email": 1, "co_pm_emails": 1, "project_number": 1, "active": 1},
        )
        async for j in job_cursor:
            pn = (j.get("project_number") or "").strip()
            if not pn:
                continue
            primary = (j.get("pm_email") or "").strip().lower()
            if primary:
                by_email.setdefault(primary, set()).add(pn)
            for e in (j.get("co_pm_emails") or []):
                if isinstance(e, str) and e.strip():
                    by_email.setdefault(e.strip().lower(), set()).add(pn)

        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        collections = [
            "inspections", "meetings", "incidents", "daily_reports",
            "equipment_inspections", "qaqc_inspections", "job_hazard_plans",
        ]
        items = []
        for pm in pms:
            email = (pm.get("email") or "").strip().lower()
            nums = by_email.get(email, set())
            reports_7d = 0
            if nums:
                for coll in collections:
                    try:
                        n = await db[coll].count_documents({
                            "project_number": {"$in": list(nums)},
                            "created_at": {"$gte": cutoff},
                        })
                        reports_7d += n
                    except Exception:  # noqa: BLE001
                        pass
            items.append({
                **public_pm_view(pm),
                "job_count": len(nums),
                "reports_7d": reports_7d,
            })
        return {"items": items, "since": cutoff, "collections": collections}

    return router


__all__ = ["build_pm_admin_router", "PMIn", "PMUpdate", "PMSetPasswordBody"]
