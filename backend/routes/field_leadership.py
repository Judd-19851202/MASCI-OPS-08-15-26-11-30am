"""
Field Leadership records — supervisor-facing employee documentation.

Single collection `field_leadership_records` keyed by `kind`:
  write_up, verbal_coaching, attendance, recognition, equipment_checkout,
  new_employee_eval, crew_eval, promotion_recommendation,
  training_deficiency, supervisor_notes
(safety_equipment_issuance is a SEPARATE existing flow — Field Leadership
links to it but does not duplicate.)

Every endpoint requires the Field Leadership password gate (`X-Leadership-Token`)
OR an admin token. Supervisor Notes additionally require admin.

PDF + email routing reuses the existing `pdf_render.py` / Resend pattern.
"""

from __future__ import annotations

import csv
import hmac
import io
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

# ----------------------------------------------------------------------
# Form schemas — drives BOTH backend validation AND PDF rendering.
# Frontend has its own copy in /app/frontend/src/lib/fieldLeadershipSchemas.js
# (kept in sync — the schema is small enough that duplication is cheaper
# than serving a shared JSON manifest).
# ----------------------------------------------------------------------

# Each kind maps to: (title_en, title_es, list of (field_name, kind))
# field_kind ∈ {"text", "textarea", "select", "date", "time", "rating", "yesno"}
FIELD_LEADERSHIP_KINDS: Dict[str, Dict[str, Any]] = {
    "write_up": {
        "title_en": "Employee Write-Up",
        "title_es": "Amonestación al Empleado",
        "needs_signatures": True,
        "allow_refusal": True,
        "allows_photos": True,
    },
    "verbal_coaching": {
        "title_en": "Verbal Coaching Documentation",
        "title_es": "Documentación de Asesoramiento Verbal",
        "needs_signatures": True,
        "employee_signature_optional": True,
        "allow_refusal": False,
        "allows_photos": False,
    },
    "attendance": {
        "title_en": "Attendance / Tardy Documentation",
        "title_es": "Documentación de Asistencia / Tardanza",
        "needs_signatures": True,
        "allow_refusal": True,
        "allows_photos": False,
    },
    "recognition": {
        "title_en": "Employee Recognition / Reward",
        "title_es": "Reconocimiento al Empleado",
        "needs_signatures": False,  # Supervisor only signs
        "supervisor_signature_only": True,
        "allow_refusal": False,
        "allows_photos": True,
    },
    "equipment_checkout": {
        "title_en": "Equipment Checkout & Accountability",
        "title_es": "Asignación y Responsabilidad de Equipo",
        "needs_signatures": True,
        "allow_refusal": False,
        "allows_photos": True,
    },
    "new_employee_eval": {
        "title_en": "New Employee Evaluation",
        "title_es": "Evaluación de Nuevo Empleado",
        "needs_signatures": True,
        "allow_refusal": True,
        "allows_photos": False,
    },
    "crew_eval": {
        "title_en": "Crew Evaluation",
        "title_es": "Evaluación de Cuadrilla",
        "needs_signatures": True,
        "supervisor_signature_only": True,
        "allow_refusal": False,
        "allows_photos": False,
    },
    "promotion_recommendation": {
        "title_en": "Promotion Recommendation",
        "title_es": "Recomendación de Ascenso",
        "needs_signatures": True,
        "supervisor_signature_only": True,
        "allow_refusal": False,
        "allows_photos": False,
    },
    "training_deficiency": {
        "title_en": "Training Deficiency / Retraining",
        "title_es": "Deficiencia de Capacitación / Reentrenamiento",
        "needs_signatures": True,
        "allow_refusal": True,
        "allows_photos": False,
    },
    "supervisor_notes": {
        "title_en": "Supervisor Notes Log",
        "title_es": "Registro de Notas del Supervisor",
        "needs_signatures": False,
        "allow_refusal": False,
        "allows_photos": True,
        "admin_only": True,
    },
}

KIND_ORDER = list(FIELD_LEADERSHIP_KINDS.keys())


# ----------------------------------------------------------------------
# Request / response models — kept loose because field shapes vary by kind.
# We validate kind-specific keys in `_normalize_record`.
# ----------------------------------------------------------------------

class FieldLeadershipCreate(BaseModel):
    kind: str
    job_id: Optional[str] = None
    project_number: Optional[str] = None
    project_name: Optional[str] = None
    location: Optional[str] = None
    client: Optional[str] = None
    assigned_pm: Optional[str] = None
    assigned_pm_email: Optional[str] = None

    employee_id: Optional[str] = None
    employee_name: Optional[str] = ""
    employee_position: Optional[str] = ""
    employee_email: Optional[str] = ""

    supervisor_name: str = ""
    supervisor_email: Optional[str] = ""

    occurred_at: Optional[str] = None  # ISO datetime — when the event happened
    work_area: Optional[str] = ""

    details: Dict[str, Any] = Field(default_factory=dict)
    photos: List[str] = Field(default_factory=list)

    supervisor_signature: Optional[str] = ""  # data URL
    employee_signature: Optional[str] = ""    # data URL OR ""
    employee_refused: bool = False
    witness_name: Optional[str] = ""
    witness_signature: Optional[str] = ""

    language: str = "en"  # "en" or "es" — original submit language
    # If the form was submitted in Spanish, the frontend sends both the
    # original ES text and a backend-translated EN copy for admin/PM viewing.
    details_en: Optional[Dict[str, Any]] = None


class LoginBody(BaseModel):
    password: str


# ----------------------------------------------------------------------
# Token gate — sessionStorage-backed leadership password.
# ----------------------------------------------------------------------

_LEADERSHIP_TOKENS: Dict[str, datetime] = {}
_TOKEN_TTL = timedelta(hours=12)


def _gen_token() -> str:
    return uuid.uuid4().hex + uuid.uuid4().hex


def _check_leadership_token(tok: Optional[str]) -> bool:
    if not tok:
        return False
    exp = _LEADERSHIP_TOKENS.get(tok)
    if not exp:
        return False
    if datetime.now(timezone.utc) > exp:
        _LEADERSHIP_TOKENS.pop(tok, None)
        return False
    return True


def _sweep_expired() -> None:
    """Drop tokens older than TTL — called occasionally to bound memory."""
    now = datetime.now(timezone.utc)
    for tok in [t for t, e in _LEADERSHIP_TOKENS.items() if now > e]:
        _LEADERSHIP_TOKENS.pop(tok, None)


# ----------------------------------------------------------------------

def _normalize_record(payload: FieldLeadershipCreate) -> Dict[str, Any]:
    if payload.kind not in FIELD_LEADERSHIP_KINDS:
        raise HTTPException(status_code=400, detail=f"Unknown kind: {payload.kind}")

    now_iso = datetime.now(timezone.utc).isoformat()
    rec = payload.model_dump()
    rec["id"] = str(uuid.uuid4())
    rec["created_at"] = now_iso
    rec["updated_at"] = now_iso
    rec["deleted_at"] = None
    if not rec.get("occurred_at"):
        rec["occurred_at"] = now_iso
    return rec


def _user_visible_summary(rec: Dict[str, Any]) -> str:
    """One-line summary for emails / admin lists."""
    kind_meta = FIELD_LEADERSHIP_KINDS.get(rec["kind"], {})
    kind_label = kind_meta.get("title_en", rec["kind"])
    emp = rec.get("employee_name") or "—"
    proj = rec.get("project_number") or rec.get("project_name") or "(no job)"
    return f"{kind_label} · {emp} · {proj}"


# ----------------------------------------------------------------------
# Router factory — wired into server.py via attach_routes()
# ----------------------------------------------------------------------

def attach_routes(app, db, require_admin, send_email_async, render_pdf_bytes,
                  compute_pm_scope=None, get_pm_user=None):
    """
    Register Field Leadership routes onto the given FastAPI app.

    Parameters:
      db                   — Motor database
      require_admin        — FastAPI dependency for admin-only routes
      send_email_async     — async (recipients, subject, html, attachments) → bool
      render_pdf_bytes     — sync (record) → bytes  (Field Leadership PDF renderer)
      compute_pm_scope     — optional async (pm_email) → set[project_number] (for PM scoping)
      get_pm_user          — optional FastAPI dep returning the PM user dict (for PM-portal endpoints)
    """
    router = APIRouter(prefix="/api/field-leadership", tags=["field-leadership"])

    # The shared password — simple env override, defaults to MASCIGC.
    LEADERSHIP_PASSWORD = os.environ.get("LEADERSHIP_PASSWORD", "MASCIGC")

    async def _is_authed(
        x_leadership_token: Optional[str] = Header(default=None, alias="X-Leadership-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_pm_token: Optional[str] = Header(default=None, alias="X-PM-Token"),
    ) -> Dict[str, Any]:
        """Returns {role: 'admin' | 'pm' | 'leadership'} — raises 401 otherwise.
        Admin and PM tokens implicitly satisfy the leadership gate."""
        # Cheap check for admin token via the shared validator
        if x_admin_token and await _admin_token_valid(x_admin_token):
            return {"role": "admin", "token": x_admin_token}
        if x_pm_token:
            pm = await _pm_token_valid(x_pm_token)
            if pm:
                return {"role": "pm", "token": x_pm_token, "pm": pm}
        if _check_leadership_token(x_leadership_token):
            return {"role": "leadership", "token": x_leadership_token}
        raise HTTPException(status_code=401, detail="Field Leadership access required")

    async def _admin_token_valid(tok: str) -> bool:
        # Reuse the shared HMAC validator. Sync function so no await needed.
        try:
            from server import _is_valid_admin_token  # type: ignore  # noqa: WPS433
            return bool(_is_valid_admin_token(tok))
        except Exception:
            return False

    async def _pm_token_valid(tok: str) -> Optional[Dict[str, Any]]:
        try:
            from pm_auth import is_valid_pm_user_token_async  # type: ignore  # noqa: WPS433
            return await is_valid_pm_user_token_async(db, tok)
        except Exception:
            return None

    # ------------------------------------------------------------
    # Auth — login + check
    # ------------------------------------------------------------

    @router.post("/login")
    async def login(body: LoginBody):
        if not hmac.compare_digest(body.password or "", LEADERSHIP_PASSWORD):
            raise HTTPException(status_code=401, detail="Invalid password")
        _sweep_expired()
        tok = _gen_token()
        _LEADERSHIP_TOKENS[tok] = datetime.now(timezone.utc) + _TOKEN_TTL
        return {"token": tok, "expires_in_s": int(_TOKEN_TTL.total_seconds())}

    @router.get("/check")
    async def check(auth: Dict[str, Any] = Depends(_is_authed)):
        return {"ok": True, "role": auth["role"]}

    # ------------------------------------------------------------
    # Reference data — jobs, employees, PMs (read-only helpers)
    # ------------------------------------------------------------

    @router.get("/jobs")
    async def list_jobs(auth: Dict[str, Any] = Depends(_is_authed)):
        cursor = db.jobs_master.find(
            {"active": {"$ne": False}},
            {"_id": 0, "id": 1, "project_number": 1, "project_name": 1,
             "location": 1, "client": 1, "project_manager": 1, "pm_email": 1}
        ).sort("project_number", 1)
        items = await cursor.to_list(500)
        return {"items": items, "count": len(items)}

    @router.get("/employees")
    async def list_employees(auth: Dict[str, Any] = Depends(_is_authed)):
        cursor = db.employees.find(
            {"is_active": {"$ne": False}},
            {"_id": 0, "id": 1, "name": 1, "employee_id": 1, "trade": 1,
             "role": 1, "crew": 1, "email": 1, "phone": 1}
        ).sort("name", 1)
        items = await cursor.to_list(2000)
        return {"items": items, "count": len(items)}

    @router.post("/employees")
    async def create_employee_inline(
        body: Dict[str, Any],
        auth: Dict[str, Any] = Depends(_is_authed),
    ):
        """Create a new employee record on the fly when the foreman adds one
        from inside a Field Leadership form. Lightweight — only requires a
        name. Uses the existing employees collection so the new entry shows
        up in HR / Safety dropdowns going forward."""
        name = (body.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Name is required")
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": str(uuid.uuid4()),
            "name": name,
            "employee_id": (body.get("employee_id") or "").strip() or None,
            "trade": (body.get("trade") or "").strip() or None,
            "role": (body.get("role") or "").strip() or None,
            "crew": (body.get("crew") or "").strip() or None,
            "email": (body.get("email") or "").strip() or None,
            "phone": (body.get("phone") or "").strip() or None,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "created_via": "field_leadership_inline",
        }
        await db.employees.insert_one(dict(doc))
        doc.pop("_id", None)
        return doc

    # ------------------------------------------------------------
    # Records — create / list / view / pdf / delete / csv
    # ------------------------------------------------------------

    @router.post("")
    async def create_record(
        payload: FieldLeadershipCreate,
        request: Request,
        auth: Dict[str, Any] = Depends(_is_authed),
    ):
        # Supervisor Notes are admin-only.
        meta = FIELD_LEADERSHIP_KINDS.get(payload.kind, {})
        if meta.get("admin_only") and auth["role"] != "admin":
            raise HTTPException(status_code=403,
                                detail="Supervisor Notes require admin login")

        rec = _normalize_record(payload)
        # Stamp who submitted (best-effort — leadership-only doesn't have a user id)
        rec["submitted_via_role"] = auth["role"]

        await db.field_leadership_records.insert_one(dict(rec))

        # Best-effort email + photo indexer (fire-and-forget)
        try:
            await _send_submit_email(rec)
        except Exception as exc:  # noqa: BLE001
            # Log but never fail the submit
            try:
                from server import logger  # type: ignore  # noqa: WPS433
                logger.warning(f"Field Leadership email failed: {exc}")
            except Exception:
                pass

        rec.pop("_id", None)
        return {"ok": True, "id": rec["id"], "record": rec}

    async def _send_submit_email(rec: Dict[str, Any]) -> None:
        """Email the assigned PM + jaymn + safety with the record summary."""
        recipients: List[str] = []
        always_cc = [
            os.environ.get("LEADERSHIP_ALWAYS_TO_1", "jaymn.judd@mascigc.com"),
            os.environ.get("LEADERSHIP_ALWAYS_TO_2", "safety@mascigc.com"),
        ]
        recipients.extend([r for r in always_cc if r])

        pm_email = (rec.get("assigned_pm_email") or "").strip()
        no_pm_warning = ""
        if pm_email:
            recipients.insert(0, pm_email)
        else:
            no_pm_warning = "<p style='color:#b91c1c;font-weight:600'>⚠ No assigned PM found for this job.</p>"

        # De-dupe + drop empties
        seen = set()
        recipients = [r for r in recipients if r and r.lower() not in seen and not seen.add(r.lower())]
        if not recipients:
            return

        kind_meta = FIELD_LEADERSHIP_KINDS.get(rec["kind"], {})
        kind_label = kind_meta.get("title_en", rec["kind"])

        subject = (
            f"Field Leadership Form Submitted — {kind_label} — "
            f"{rec.get('employee_name') or '—'} — "
            f"{rec.get('project_number') or ''} {rec.get('project_name') or ''}".strip()
        )

        body_html = _email_html(rec, kind_label, no_pm_warning)
        attachments = []
        try:
            pdf_bytes = render_pdf_bytes(rec)
            if pdf_bytes:
                import base64 as _b64
                attachments.append({
                    "filename": _filename_for(rec),
                    "content": _b64.b64encode(pdf_bytes).decode("ascii"),
                    "type": "application/pdf",
                })
        except Exception:  # noqa: BLE001
            pass

        await send_email_async(recipients, subject, body_html, attachments)

    def _filename_for(rec: Dict[str, Any]) -> str:
        kind = rec["kind"]
        emp = (rec.get("employee_name") or "employee").replace(" ", "_")
        date = (rec.get("occurred_at") or "")[:10]
        safe = "".join(c for c in f"{kind}_{emp}_{date}" if c.isalnum() or c in "_-.")
        return f"field-leadership-{safe}.pdf"

    def _email_html(rec: Dict[str, Any], kind_label: str, prefix: str = "") -> str:
        rows = [
            ("Form Type", kind_label),
            ("Employee", rec.get("employee_name") or "—"),
            ("Position", rec.get("employee_position") or "—"),
            ("Job Number", rec.get("project_number") or "—"),
            ("Project Name", rec.get("project_name") or "—"),
            ("Assigned PM", rec.get("assigned_pm") or "(none)"),
            ("Supervisor", rec.get("supervisor_name") or "—"),
            ("Date / Time", (rec.get("occurred_at") or "").replace("T", " ")[:16]),
        ]
        # Add details summary (top 6 details fields)
        details = rec.get("details_en") or rec.get("details") or {}
        details_html = ""
        if details:
            keys = list(details.keys())[:8]
            details_html = "<h3 style='margin-top:24px'>Details</h3><table style='border-collapse:collapse;width:100%'>"
            for k in keys:
                v = details[k]
                if isinstance(v, (list, dict)):
                    v = str(v)
                details_html += (
                    f"<tr><td style='padding:6px 8px;border:1px solid #e2e8f0;background:#f8fafc;font-weight:600;width:40%'>{k.replace('_', ' ').title()}</td>"
                    f"<td style='padding:6px 8px;border:1px solid #e2e8f0'>{(v or '')[:400] if isinstance(v, str) else v}</td></tr>"
                )
            details_html += "</table>"

        meta_rows = "".join(
            f"<tr><td style='padding:6px 8px;border:1px solid #e2e8f0;background:#f8fafc;font-weight:600;width:40%'>{label}</td>"
            f"<td style='padding:6px 8px;border:1px solid #e2e8f0'>{value}</td></tr>"
            for label, value in rows
        )

        return f"""
<!doctype html><html><body style='font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#0f172a;background:#f1f5f9;padding:16px'>
<div style='max-width:680px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden'>
  <div style='background:#0f172a;color:#fff;padding:18px 22px'>
    <div style='font-family:ui-monospace,monospace;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:#cbd5e1'>MASCI HUB · FIELD LEADERSHIP</div>
    <div style='font-size:22px;font-weight:800;margin-top:4px'>{kind_label}</div>
  </div>
  <div style='padding:18px 22px'>
    {prefix}
    <table style='border-collapse:collapse;width:100%;margin-top:8px'>{meta_rows}</table>
    {details_html}
    <p style='margin-top:18px;font-size:12px;color:#475569'>The full PDF is attached. Reply to this email if anything looks off.</p>
  </div>
  <div style='padding:14px 22px;background:#f8fafc;border-top:1px solid #e2e8f0;font-family:ui-monospace,monospace;font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:#64748b'>
    Generated through MASCI HUB — Powered by ForgedOps LLC | © 2026 ForgedOps LLC
  </div>
</div>
</body></html>"""

    async def _scope_filter(auth: Dict[str, Any]) -> Dict[str, Any]:
        """Build a Mongo filter that respects PM scoping."""
        f: Dict[str, Any] = {"deleted_at": None}
        if auth["role"] == "pm" and compute_pm_scope is not None:
            pm = auth.get("pm") or {}
            scope = await compute_pm_scope(pm.get("email"))
            f["project_number"] = {"$in": list(scope or [])}
        return f

    @router.get("")
    async def list_records(
        auth: Dict[str, Any] = Depends(_is_authed),
        kind: Optional[str] = Query(default=None),
        employee: Optional[str] = Query(default=None),
        job: Optional[str] = Query(default=None),
        supervisor: Optional[str] = Query(default=None),
        date_from: Optional[str] = Query(default=None),
        date_to: Optional[str] = Query(default=None),
        q: Optional[str] = Query(default=None),
        limit: int = Query(default=500, le=2000),
    ):
        # Admin-only: Supervisor Notes — explicit guard so a hand-crafted
        # ?kind=supervisor_notes query from a non-admin returns 403 instead
        # of leaking those records.
        if kind == "supervisor_notes" and auth["role"] != "admin":
            raise HTTPException(status_code=403, detail="Supervisor Notes require admin")

        f = await _scope_filter(auth)
        if kind:
            f["kind"] = kind
        elif auth["role"] != "admin":
            f["kind"] = {"$ne": "supervisor_notes"}
        if employee:
            f["employee_name"] = {"$regex": _escape(employee), "$options": "i"}
        if job:
            f["$or"] = [
                {"project_number": {"$regex": _escape(job), "$options": "i"}},
                {"project_name": {"$regex": _escape(job), "$options": "i"}},
            ]
        if supervisor:
            f["supervisor_name"] = {"$regex": _escape(supervisor), "$options": "i"}
        if date_from:
            f.setdefault("occurred_at", {})["$gte"] = date_from
        if date_to:
            f.setdefault("occurred_at", {})["$lte"] = date_to + "T23:59:59"
        if q:
            qf = {"$regex": _escape(q), "$options": "i"}
            f.setdefault("$or", []).extend([
                {"employee_name": qf},
                {"supervisor_name": qf},
                {"project_number": qf},
                {"project_name": qf},
            ])

        cursor = db.field_leadership_records.find(
            f,
            {"_id": 0, "photos": 0, "supervisor_signature": 0,
             "employee_signature": 0, "witness_signature": 0}
        ).sort("occurred_at", -1).limit(limit)
        items = await cursor.to_list(limit)

        # Counts by kind — always run on the SCOPE filter (without the
        # current `kind` selector) so the dashboard tile row reflects the
        # full breakdown the user can see, not just the slice they're
        # currently filtering to.
        scope_only = await _scope_filter(auth)
        if auth["role"] != "admin":
            scope_only["kind"] = {"$ne": "supervisor_notes"}
        counts_pipeline = [{"$match": scope_only}, {"$group": {"_id": "$kind", "n": {"$sum": 1}}}]
        counts: Dict[str, int] = {k: 0 for k in KIND_ORDER}
        try:
            async for row in db.field_leadership_records.aggregate(counts_pipeline):
                counts[row["_id"]] = row["n"]
        except Exception:
            pass

        return {"items": items, "count": len(items), "counts_by_kind": counts}

    @router.get("/{rec_id}")
    async def get_record(rec_id: str, auth: Dict[str, Any] = Depends(_is_authed)):
        f = await _scope_filter(auth)
        f["id"] = rec_id
        rec = await db.field_leadership_records.find_one(f, {"_id": 0})
        if not rec:
            raise HTTPException(status_code=404, detail="Record not found")
        if rec.get("kind") == "supervisor_notes" and auth["role"] != "admin":
            raise HTTPException(status_code=403, detail="Supervisor Notes require admin")
        return rec

    @router.get("/{rec_id}/pdf")
    async def get_pdf(rec_id: str, auth: Dict[str, Any] = Depends(_is_authed)):
        f = await _scope_filter(auth)
        f["id"] = rec_id
        rec = await db.field_leadership_records.find_one(f, {"_id": 0})
        if not rec:
            raise HTTPException(status_code=404, detail="Record not found")
        if rec.get("kind") == "supervisor_notes" and auth["role"] != "admin":
            raise HTTPException(status_code=403, detail="Supervisor Notes require admin")
        try:
            pdf_bytes = render_pdf_bytes(rec)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"PDF render failed: {exc}")
        if not pdf_bytes:
            raise HTTPException(status_code=500, detail="Empty PDF")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{_filename_for(rec)}"',
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "private, max-age=0, must-revalidate",
            },
        )

    @router.delete("/{rec_id}")
    async def soft_delete(rec_id: str, _: bool = Depends(require_admin)):
        res = await db.field_leadership_records.update_one(
            {"id": rec_id, "deleted_at": None},
            {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}},
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Record not found")
        return {"ok": True}

    @router.get("/export/csv")
    async def export_csv(
        auth: Dict[str, Any] = Depends(_is_authed),
        kind: Optional[str] = Query(default=None),
        employee: Optional[str] = Query(default=None),
    ):
        f = await _scope_filter(auth)
        if auth["role"] != "admin":
            f["kind"] = {"$ne": "supervisor_notes"}
        if kind:
            f["kind"] = kind
        if employee:
            f["employee_name"] = {"$regex": _escape(employee), "$options": "i"}

        cursor = db.field_leadership_records.find(
            f, {"_id": 0, "photos": 0, "supervisor_signature": 0,
                "employee_signature": 0, "witness_signature": 0}
        ).sort("occurred_at", -1).limit(5000)

        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow([
            "Date", "Form Type", "Employee", "Position", "Job Number",
            "Project Name", "Assigned PM", "Supervisor", "Summary",
        ])
        async for r in cursor:
            kind_label = FIELD_LEADERSHIP_KINDS.get(r.get("kind", ""), {}).get("title_en", r.get("kind", ""))
            details = r.get("details_en") or r.get("details") or {}
            summary_parts = []
            for k, v in list(details.items())[:3]:
                if isinstance(v, str):
                    summary_parts.append(f"{k}={v[:60]}")
            writer.writerow([
                (r.get("occurred_at") or "")[:16].replace("T", " "),
                kind_label,
                r.get("employee_name") or "",
                r.get("employee_position") or "",
                r.get("project_number") or "",
                r.get("project_name") or "",
                r.get("assigned_pm") or "",
                r.get("supervisor_name") or "",
                "; ".join(summary_parts),
            ])

        return Response(
            content=out.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="field_leadership_records.csv"',
            },
        )

    app.include_router(router)
    return router


def _escape(s: str) -> str:
    """Escape regex special characters so user input doesn't break the query."""
    import re
    return re.escape(s)
