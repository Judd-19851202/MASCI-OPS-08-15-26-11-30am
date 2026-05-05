"""
Safety Forms — Equipment Issuance & Equipment Use/Care Training.

Used by the MASCI Safety Department to track:
  1. Safety Equipment Checkout/Check-In (financial-accountability form)
  2. Safety Equipment Use & Care Training (compliance training record)

Auth:
    Password-gated via env var ``SAFETY_FORMS_PASSWORD`` (default: 1982).
    Token format mirrors the shop token (HMAC of "epoch=N|safety:<pw>"
    keyed off ``ADMIN_HMAC_SECRET``). Admin tokens also satisfy the
    requirement so the Admin dashboard can list every record without
    re-authenticating.

On submit:
    Auto-emails a generated PDF (WeasyPrint) to the configured
    distribution list (env: ``SAFETY_FORMS_EMAIL_TO``, default
    safety@mascigc.com,jaymn.judd@mascigc.com) via Resend, gated by the
    same ``AUTO_EMAIL_REPORTS`` toggle as the rest of the platform.

Storage:
    ``safety_equipment_issuances`` and ``safety_equipment_trainings``
    Mongo collections. Each document carries an opaque UUID ``id`` field
    so we never expose Mongo ``_id`` to API clients.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("safety_forms")


# ─────────────────────────────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────────────────────────────


def _hmac_secret() -> bytes:
    s = os.environ.get("ADMIN_HMAC_SECRET", "").encode()
    return s or b"masci-fallback-secret"


def _session_epoch() -> str:
    return os.environ.get("ADMIN_SESSION_EPOCH", "1")


def _safety_token_for(password: str) -> str:
    msg = (f"epoch={_session_epoch()}|safety-forms:{password}").encode()
    return hmac.new(_hmac_secret(), msg, hashlib.sha256).hexdigest()


def _is_valid_safety_token(token: Optional[str]) -> bool:
    if not token:
        return False
    pw = os.environ.get("SAFETY_FORMS_PASSWORD", "")
    if not pw:
        return False
    return hmac.compare_digest(token, _safety_token_for(pw))


# ─────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────


class LoginBody(BaseModel):
    password: str

    model_config = ConfigDict(extra="ignore")


class IssuanceItem(BaseModel):
    item_type: str = ""
    item_type_other: Optional[str] = ""  # filled when item_type == "Other"
    description: str = ""
    quantity: float = 0
    unit_value: float = 0
    asset_id: Optional[str] = ""

    model_config = ConfigDict(extra="ignore")


class IssuanceBody(BaseModel):
    employee_name: str
    employee_id: Optional[str] = ""
    position: Optional[str] = ""
    project_name: Optional[str] = ""
    project_number: Optional[str] = ""
    location: Optional[str] = ""
    issued_by: str
    issued_date: str  # YYYY-MM-DD (frontend supplies todayLocalIso)
    items: List[IssuanceItem] = Field(default_factory=list, max_length=30)
    condition: str  # New / Good / Fair / Damaged
    condition_note: Optional[str] = ""  # required when condition == Damaged
    photos: List[str] = Field(default_factory=list, max_length=8)  # data-URIs
    acknowledgment: bool
    employee_signature: str  # data-URI PNG
    supervisor_signature: str  # data-URI PNG
    lang: Optional[str] = "en"

    model_config = ConfigDict(extra="ignore")


class TrainingItem(BaseModel):
    equipment_type: str = ""
    equipment_type_other: Optional[str] = ""
    description: str = ""
    training_type: str = ""  # Initial / Refresher / Retraining
    manufacturer_model: Optional[str] = ""
    notes: Optional[str] = ""

    model_config = ConfigDict(extra="ignore")


class TrainingBody(BaseModel):
    employee_name: str
    employee_id: Optional[str] = ""
    position: Optional[str] = ""
    project_name: Optional[str] = ""
    project_number: Optional[str] = ""
    training_date: str
    instructor_name: str
    training_location: Optional[str] = ""
    items: List[TrainingItem] = Field(default_factory=list, max_length=30)
    topics: List[str] = Field(default_factory=list)  # subset of TOPICS_KEYS
    topic_other: Optional[str] = ""  # filled when "Other" in topics
    acknowledgment: bool
    employee_signature: str
    instructor_signature: str
    lang: Optional[str] = "en"

    model_config = ConfigDict(extra="ignore")


# ─────────────────────────────────────────────────────────────────────
# PDF generation (WeasyPrint, matches MASCI Hub PDF styling)
# ─────────────────────────────────────────────────────────────────────


def _logo_data_uri() -> str:
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "masci-lockup-onlight.png"
    if not p.exists():
        # Fallback to red M mark
        p = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "masci-mark.png"
    if not p.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")


_BASE_CSS = """
@page { size: Letter; margin: 0.55in 0.6in 0.7in 0.6in; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; color: #0f172a; font-size: 10.5pt; line-height: 1.45; }
h1 { font-size: 22pt; font-weight: 900; letter-spacing: -0.5px; margin: 0 0 4px; color: #0f172a; }
.eyebrow { font-family: 'Courier New', monospace; font-size: 8.5pt; letter-spacing: 0.25em; text-transform: uppercase; color: #b91c1c; font-weight: 700; }
.sub { color: #475569; font-size: 10pt; margin: 0 0 14px; }
.head { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #b91c1c; padding-bottom: 14px; margin-bottom: 18px; }
.head .logo img { height: 56px; }
.section { margin: 14px 0; }
.section h2 { font-size: 11pt; font-weight: 800; letter-spacing: 0.18em; text-transform: uppercase; color: #0f172a; border-bottom: 2px solid #cbd5e1; padding-bottom: 4px; margin: 14px 0 8px; }
table { width: 100%; border-collapse: collapse; margin: 6px 0 10px; font-size: 9.5pt; }
th, td { border: 1px solid #cbd5e1; padding: 5px 7px; vertical-align: top; text-align: left; }
th { background: #f1f5f9; font-family: 'Courier New', monospace; font-size: 8pt; letter-spacing: 0.15em; text-transform: uppercase; color: #334155; }
.kv { display: grid; grid-template-columns: 160px 1fr; gap: 4px 14px; }
.kv .k { font-family: 'Courier New', monospace; font-size: 8.5pt; letter-spacing: 0.15em; text-transform: uppercase; color: #475569; font-weight: 700; }
.kv .v { color: #0f172a; }
.legal { background: #fef3c7; border-left: 4px solid #d97706; padding: 10px 12px; font-size: 9pt; line-height: 1.55; margin: 10px 0; }
.sigblock { margin-top: 24px; display: flex; gap: 36px; }
.sigblock .col { flex: 1; }
.sigblock img { max-height: 80px; max-width: 100%; border-bottom: 1.5px solid #0f172a; padding-bottom: 4px; }
.sigblock .name { font-family: 'Courier New', monospace; font-size: 8.5pt; letter-spacing: 0.15em; text-transform: uppercase; color: #475569; margin-top: 6px; }
.photos { display: flex; flex-wrap: wrap; gap: 6px; margin: 6px 0; }
.photos img { max-width: 30%; max-height: 160px; border: 1px solid #cbd5e1; }
.foot { margin-top: 30px; border-top: 1.5px solid #cbd5e1; padding-top: 8px; font-family: 'Courier New', monospace; font-size: 7.5pt; letter-spacing: 0.15em; text-transform: uppercase; color: #94a3b8; text-align: center; }
.totals { display: flex; justify-content: flex-end; margin: 6px 0 12px; }
.totals .box { background: #fef2f2; border: 2px solid #b91c1c; padding: 8px 14px; }
.totals .lbl { font-family: 'Courier New', monospace; font-size: 8pt; letter-spacing: 0.15em; text-transform: uppercase; color: #991b1b; font-weight: 700; }
.totals .val { font-size: 18pt; font-weight: 900; color: #0f172a; }
.checked { color: #166534; font-weight: 700; }
"""


def _safe(s: Optional[str]) -> str:
    if s is None:
        return ""
    import html
    return html.escape(str(s))


def _fmt_money(v) -> str:
    try:
        return f"${float(v):,.2f}"
    except Exception:  # noqa: BLE001
        return "$0.00"


def _resolve_item_type(it: Dict[str, Any]) -> str:
    t = (it.get("item_type") or "").strip()
    if t.lower() == "other" and (it.get("item_type_other") or "").strip():
        return f"Other — {it['item_type_other']}"
    return t


def render_issuance_pdf(rec: Dict[str, Any]) -> bytes:
    from weasyprint import HTML  # local import keeps router importable in tests

    items = rec.get("items") or []
    rows = []
    total = 0.0
    for i, it in enumerate(items, 1):
        qty = float(it.get("quantity") or 0)
        uv = float(it.get("unit_value") or 0)
        line = qty * uv
        total += line
        rows.append(
            f"<tr><td>{i}</td><td>{_safe(_resolve_item_type(it))}</td>"
            f"<td>{_safe(it.get('description'))}</td>"
            f"<td>{_safe(it.get('asset_id') or '—')}</td>"
            f"<td style='text-align:right'>{qty:g}</td>"
            f"<td style='text-align:right'>{_fmt_money(uv)}</td>"
            f"<td style='text-align:right'>{_fmt_money(line)}</td></tr>"
        )
    rows_html = "\n".join(rows) or "<tr><td colspan='7' style='text-align:center;color:#94a3b8'>No items</td></tr>"

    photos_html = ""
    photos = [p for p in (rec.get("photos") or []) if p]
    if photos:
        photos_html = "<div class='section'><h2>Photos</h2><div class='photos'>" + "".join(
            f"<img src='{_safe(p)}' />" for p in photos[:6]
        ) + "</div></div>"

    cond = rec.get("condition") or ""
    cond_note = ""
    if cond.lower() == "damaged" and rec.get("condition_note"):
        cond_note = f" <span style='color:#b91c1c;font-weight:700'>— {_safe(rec['condition_note'])}</span>"

    legal = (
        "I acknowledge that all issued equipment remains the property of MASCI General "
        "Contractors. I agree to use all equipment in accordance with company policy and "
        "OSHA safety requirements. "
        "I understand that I am responsible for the care and return of all issued "
        "equipment. Any equipment that is lost, stolen, misplaced, or damaged due to "
        "negligence or misuse may result in financial responsibility for replacement cost "
        "or fair market value. "
        "Any reimbursement or payroll deduction will be handled in accordance with "
        "applicable Florida law and the Fair Labor Standards Act (FLSA), and will not "
        "occur without proper authorization where required."
    )

    emp_sig = rec.get("employee_signature") or ""
    sup_sig = rec.get("supervisor_signature") or ""

    html_doc = f"""<!doctype html><html><head><meta charset='utf-8'><style>{_BASE_CSS}</style></head>
    <body>
      <div class='head'>
        <div>
          <div class='eyebrow'>MASCI · Safety Department</div>
          <h1>Safety Equipment Issuance &amp; Accountability</h1>
          <p class='sub'>Form Ref: {_safe(rec.get('id'))}</p>
        </div>
        <div class='logo'><img src='{_logo_data_uri()}' /></div>
      </div>

      <div class='section'>
        <h2>Employee</h2>
        <div class='kv'>
          <div class='k'>Name</div><div class='v'>{_safe(rec.get('employee_name'))}</div>
          <div class='k'>Employee ID</div><div class='v'>{_safe(rec.get('employee_id') or '—')}</div>
          <div class='k'>Position</div><div class='v'>{_safe(rec.get('position') or '—')}</div>
          <div class='k'>Project</div><div class='v'>{_safe(rec.get('project_name') or '—')} {('· ' + _safe(rec.get('project_number'))) if rec.get('project_number') else ''}</div>
          <div class='k'>Location</div><div class='v'>{_safe(rec.get('location') or '—')}</div>
        </div>
      </div>

      <div class='section'>
        <h2>Issuance</h2>
        <div class='kv'>
          <div class='k'>Date Issued</div><div class='v'>{_safe(rec.get('issued_date'))}</div>
          <div class='k'>Issued By</div><div class='v'>{_safe(rec.get('issued_by'))}</div>
          <div class='k'>Condition</div><div class='v'><b>{_safe(cond)}</b>{cond_note}</div>
        </div>
      </div>

      <div class='section'>
        <h2>Equipment Issued</h2>
        <table>
          <thead><tr><th>#</th><th>Item Type</th><th>Description</th><th>Asset / Serial</th><th style='text-align:right'>Qty</th><th style='text-align:right'>Unit $</th><th style='text-align:right'>Line $</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>
        <div class='totals'><div class='box'><div class='lbl'>Total Issued Value</div><div class='val'>{_fmt_money(total)}</div></div></div>
      </div>

      {photos_html}

      <div class='section'>
        <h2>Acknowledgment</h2>
        <p style='font-weight:700'><span class='checked'>✓</span> I acknowledge receipt of the listed equipment and accept responsibility.</p>
        <div class='legal'>{legal}</div>
      </div>

      <div class='sigblock'>
        <div class='col'>
          {f"<img src='{_safe(emp_sig)}' />" if emp_sig else "<div style='border-bottom:1.5px solid #0f172a;height:60px'></div>"}
          <div class='name'>Employee Signature · {_safe(rec.get('employee_name'))}</div>
        </div>
        <div class='col'>
          {f"<img src='{_safe(sup_sig)}' />" if sup_sig else "<div style='border-bottom:1.5px solid #0f172a;height:60px'></div>"}
          <div class='name'>Supervisor Signature · {_safe(rec.get('issued_by'))}</div>
        </div>
      </div>

      <div class='foot'>MASCI General Contractors · Generated {_safe(rec.get('created_at') or '')} · Confidential</div>
    </body></html>"""
    return HTML(string=html_doc).write_pdf()


TRAINING_TOPICS = [
    ("proper_use", "Proper Use"),
    ("inspection", "Inspection Requirements"),
    ("maintenance", "Maintenance"),
    ("storage", "Storage"),
    ("limitations", "Limitations of Equipment"),
    ("osha", "OSHA Compliance"),
    ("other", "Other"),
]


def render_training_pdf(rec: Dict[str, Any]) -> bytes:
    from weasyprint import HTML

    items = rec.get("items") or []
    rows = []
    for i, it in enumerate(items, 1):
        rows.append(
            f"<tr><td>{i}</td><td>{_safe(_resolve_item_type({'item_type': it.get('equipment_type'), 'item_type_other': it.get('equipment_type_other')}))}</td>"
            f"<td>{_safe(it.get('description'))}</td>"
            f"<td>{_safe(it.get('training_type'))}</td>"
            f"<td>{_safe(it.get('manufacturer_model') or '—')}</td>"
            f"<td>{_safe(it.get('notes') or '')}</td></tr>"
        )
    rows_html = "\n".join(rows) or "<tr><td colspan='6' style='text-align:center;color:#94a3b8'>No equipment</td></tr>"

    topics_set = set(rec.get("topics") or [])
    topics_html = ""
    for key, label in TRAINING_TOPICS:
        marker = "✓" if key in topics_set else "□"
        cls = "checked" if key in topics_set else ""
        extra = ""
        if key == "other" and (rec.get("topic_other") or "") and key in topics_set:
            extra = f" — {_safe(rec['topic_other'])}"
        topics_html += f"<div><span class='{cls}'>{marker}</span> {label}{extra}</div>"

    emp_sig = rec.get("employee_signature") or ""
    ins_sig = rec.get("instructor_signature") or ""

    html_doc = f"""<!doctype html><html><head><meta charset='utf-8'><style>{_BASE_CSS}
    .topics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px 18px; margin: 4px 0; }}
    </style></head>
    <body>
      <div class='head'>
        <div>
          <div class='eyebrow'>MASCI · Safety Department</div>
          <h1>Equipment Use &amp; Care Training</h1>
          <p class='sub'>Form Ref: {_safe(rec.get('id'))}</p>
        </div>
        <div class='logo'><img src='{_logo_data_uri()}' /></div>
      </div>

      <div class='section'>
        <h2>Employee</h2>
        <div class='kv'>
          <div class='k'>Name</div><div class='v'>{_safe(rec.get('employee_name'))}</div>
          <div class='k'>Employee ID</div><div class='v'>{_safe(rec.get('employee_id') or '—')}</div>
          <div class='k'>Position</div><div class='v'>{_safe(rec.get('position') or '—')}</div>
          <div class='k'>Project</div><div class='v'>{_safe(rec.get('project_name') or '—')} {('· ' + _safe(rec.get('project_number'))) if rec.get('project_number') else ''}</div>
        </div>
      </div>

      <div class='section'>
        <h2>Training</h2>
        <div class='kv'>
          <div class='k'>Date</div><div class='v'>{_safe(rec.get('training_date'))}</div>
          <div class='k'>Instructor</div><div class='v'>{_safe(rec.get('instructor_name'))}</div>
          <div class='k'>Location</div><div class='v'>{_safe(rec.get('training_location') or '—')}</div>
        </div>
      </div>

      <div class='section'>
        <h2>Equipment Trained On</h2>
        <table>
          <thead><tr><th>#</th><th>Equipment</th><th>Description</th><th>Type</th><th>Mfr / Model</th><th>Notes</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>

      <div class='section'>
        <h2>Topics Covered</h2>
        <div class='topics'>{topics_html}</div>
      </div>

      <div class='section'>
        <h2>Acknowledgment</h2>
        <p style='font-weight:700'><span class='checked'>✓</span> I acknowledge that I have received training on the equipment listed above and understand proper use, inspection, and safety requirements.</p>
      </div>

      <div class='sigblock'>
        <div class='col'>
          {f"<img src='{_safe(emp_sig)}' />" if emp_sig else "<div style='border-bottom:1.5px solid #0f172a;height:60px'></div>"}
          <div class='name'>Employee Signature · {_safe(rec.get('employee_name'))}</div>
        </div>
        <div class='col'>
          {f"<img src='{_safe(ins_sig)}' />" if ins_sig else "<div style='border-bottom:1.5px solid #0f172a;height:60px'></div>"}
          <div class='name'>Instructor Signature · {_safe(rec.get('instructor_name'))}</div>
        </div>
      </div>

      <div class='foot'>MASCI General Contractors · Generated {_safe(rec.get('created_at') or '')} · Confidential</div>
    </body></html>"""
    return HTML(string=html_doc).write_pdf()


# ─────────────────────────────────────────────────────────────────────
# Auto-email on submit
# ─────────────────────────────────────────────────────────────────────


def _email_recipients() -> List[str]:
    raw = os.environ.get(
        "SAFETY_FORMS_EMAIL_TO",
        "safety@mascigc.com,jaymn.judd@mascigc.com",
    )
    return [e.strip() for e in raw.split(",") if e.strip()]


def _auto_email_enabled() -> bool:
    flag = (os.environ.get("AUTO_EMAIL_REPORTS", "false") or "").strip().lower()
    has_key = bool((os.environ.get("RESEND_API_KEY") or "").strip())
    return flag == "true" and has_key


async def _dispatch_email(kind: str, rec: Dict[str, Any]) -> None:
    try:
        if not _auto_email_enabled():
            logger.info(f"safety-forms auto-email skipped — {kind} {rec.get('id')}")
            return
        recipients = _email_recipients()
        if not recipients:
            return
        import resend  # noqa: E402
        resend.api_key = os.environ["RESEND_API_KEY"]
        sender = os.environ.get("SENDER_EMAIL", "noreply@mascidocs.com")
        reply_to = (os.environ.get("REPLY_TO_EMAIL") or "").strip()

        if kind == "issuance":
            pdf_bytes = await asyncio.to_thread(render_issuance_pdf, rec)
            title = "Safety Equipment Issuance"
            who = rec.get("employee_name") or "—"
            subject = f"[MASCI] {title} · {who}"
            fname = f"MASCI_Equipment_Issuance_{(who or '').replace(' ', '_')}_{rec.get('issued_date', '')}.pdf"
        else:
            pdf_bytes = await asyncio.to_thread(render_training_pdf, rec)
            title = "Equipment Use & Care Training"
            who = rec.get("employee_name") or "—"
            subject = f"[MASCI] {title} · {who}"
            fname = f"MASCI_Equipment_Training_{(who or '').replace(' ', '_')}_{rec.get('training_date', '')}.pdf"

        params = {
            "from": f"MASCI Safety <{sender}>",
            "to": recipients,
            "subject": subject,
            "html": (
                f"<p>A new <b>{title}</b> form was submitted for "
                f"<b>{who}</b> on <b>{rec.get('issued_date') or rec.get('training_date')}</b>.</p>"
                f"<p>PDF attached. Submitted by {rec.get('issued_by') or rec.get('instructor_name') or '—'}.</p>"
                f"<p style='color:#94a3b8;font-size:11px'>MASCI Hub · Safety Forms · Auto-email</p>"
            ),
            "attachments": [
                {"filename": fname, "content": base64.b64encode(pdf_bytes).decode()}
            ],
        }
        if reply_to:
            params["reply_to"] = reply_to
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"safety-forms email sent: {kind} id={rec.get('id')} to={recipients} resend_id={(result or {}).get('id')}")
    except Exception as e:  # noqa: BLE001
        logger.exception(f"safety-forms auto-email failed for {kind} {rec.get('id')}: {e}")


def _schedule_email(kind: str, rec: Dict[str, Any]) -> None:
    try:
        asyncio.create_task(_dispatch_email(kind, dict(rec)))
    except RuntimeError:
        pass


# ─────────────────────────────────────────────────────────────────────
# Router factory
# ─────────────────────────────────────────────────────────────────────


def build_safety_forms_router(db, _is_valid_admin_token):
    """Mount /api/safety-forms/* routes.

    ``_is_valid_admin_token`` is the existing helper from server.py so we
    can satisfy the same admin token everywhere without duplication.
    """
    router = APIRouter(prefix="/api/safety-forms", tags=["safety-forms"])

    def _require_safety_or_admin(
        x_admin_token: Optional[str] = Header(default=None),
        x_safety_forms_token: Optional[str] = Header(default=None),
    ) -> bool:
        if x_admin_token and _is_valid_admin_token(x_admin_token):
            return True
        if x_safety_forms_token and _is_valid_safety_token(x_safety_forms_token):
            return True
        raise HTTPException(status_code=401, detail="Safety Forms or admin login required")

    def _require_admin(x_admin_token: Optional[str] = Header(default=None)) -> bool:
        if not x_admin_token or not _is_valid_admin_token(x_admin_token):
            raise HTTPException(status_code=401, detail="Admin login required")
        return True

    # ── Login ────────────────────────────────────────────────────────
    @router.post("/login")
    async def safety_forms_login(body: LoginBody, request: Request):
        expected = os.environ.get("SAFETY_FORMS_PASSWORD", "")
        if not expected:
            return {"ok": True, "token": "open-mode"}
        if not hmac.compare_digest(body.password or "", expected):
            raise HTTPException(status_code=401, detail="Wrong password")
        return {"ok": True, "token": _safety_token_for(expected)}

    @router.get("/check")
    async def safety_forms_check(_: bool = Depends(_require_safety_or_admin)):
        return {"ok": True}

    # ── Issuance ─────────────────────────────────────────────────────
    @router.post("/equipment-issuances")
    async def create_issuance(body: IssuanceBody, _: bool = Depends(_require_safety_or_admin)):
        if not body.acknowledgment:
            raise HTTPException(status_code=400, detail="Acknowledgment required")
        if not body.employee_signature or not body.supervisor_signature:
            raise HTTPException(status_code=400, detail="Both signatures required")
        if (body.condition or "").lower() == "damaged" and not (body.condition_note or "").strip():
            raise HTTPException(status_code=400, detail="Damage note required when condition is Damaged")

        # Compute totals server-side for accuracy
        items = [it.model_dump() for it in body.items]
        total = 0.0
        for it in items:
            try:
                total += float(it.get("quantity") or 0) * float(it.get("unit_value") or 0)
            except (TypeError, ValueError):
                pass

        rec = body.model_dump()
        rec["id"] = str(uuid.uuid4())
        rec["items"] = items
        rec["total_value"] = round(total, 2)
        rec["created_at"] = datetime.now(timezone.utc).isoformat()
        rec["updated_at"] = rec["created_at"]
        await db.safety_equipment_issuances.insert_one(dict(rec))
        rec.pop("_id", None)
        _schedule_email("issuance", rec)
        return {"ok": True, "id": rec["id"], "total_value": rec["total_value"]}

    @router.get("/equipment-issuances")
    async def list_issuances(
        q: Optional[str] = Query(default=None),
        employee: Optional[str] = Query(default=None),
        project: Optional[str] = Query(default=None),
        date_from: Optional[str] = Query(default=None),
        date_to: Optional[str] = Query(default=None),
        limit: int = Query(default=100, le=500),
        _: bool = Depends(_require_admin),
    ):
        query: Dict[str, Any] = {}
        if employee:
            query["employee_name"] = {"$regex": employee, "$options": "i"}
        if project:
            query["$or"] = [
                {"project_name": {"$regex": project, "$options": "i"}},
                {"project_number": {"$regex": project, "$options": "i"}},
            ]
        if date_from or date_to:
            d: Dict[str, str] = {}
            if date_from:
                d["$gte"] = date_from
            if date_to:
                d["$lte"] = date_to
            query["issued_date"] = d
        if q:
            query.setdefault("$or", []).extend([
                {"employee_name": {"$regex": q, "$options": "i"}},
                {"project_name": {"$regex": q, "$options": "i"}},
                {"project_number": {"$regex": q, "$options": "i"}},
                {"issued_by": {"$regex": q, "$options": "i"}},
            ])

        cur = db.safety_equipment_issuances.find(
            query,
            {"_id": 0, "employee_signature": 0, "supervisor_signature": 0, "photos": 0},
        ).sort("created_at", -1).limit(int(limit))
        items = [doc async for doc in cur]
        return {"ok": True, "items": items, "count": len(items)}

    @router.get("/equipment-issuances/{rec_id}")
    async def get_issuance(rec_id: str, _: bool = Depends(_require_safety_or_admin)):
        doc = await db.safety_equipment_issuances.find_one({"id": rec_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="not found")
        return doc

    @router.get("/equipment-issuances/{rec_id}/pdf")
    async def issuance_pdf(rec_id: str, _: bool = Depends(_require_safety_or_admin)):
        doc = await db.safety_equipment_issuances.find_one({"id": rec_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="not found")
        pdf = await asyncio.to_thread(render_issuance_pdf, doc)
        fname = f"MASCI_Equipment_Issuance_{(doc.get('employee_name') or '').replace(' ', '_')}_{doc.get('issued_date', '')}.pdf"
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{fname}"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    # ── Training ─────────────────────────────────────────────────────
    @router.post("/equipment-trainings")
    async def create_training(body: TrainingBody, _: bool = Depends(_require_safety_or_admin)):
        if not body.acknowledgment:
            raise HTTPException(status_code=400, detail="Acknowledgment required")
        if not body.employee_signature or not body.instructor_signature:
            raise HTTPException(status_code=400, detail="Both signatures required")

        rec = body.model_dump()
        rec["id"] = str(uuid.uuid4())
        rec["items"] = [dict(it) for it in rec.get("items", [])]
        rec["created_at"] = datetime.now(timezone.utc).isoformat()
        rec["updated_at"] = rec["created_at"]
        await db.safety_equipment_trainings.insert_one(dict(rec))
        rec.pop("_id", None)
        _schedule_email("training", rec)
        return {"ok": True, "id": rec["id"]}

    @router.get("/equipment-trainings")
    async def list_trainings(
        q: Optional[str] = Query(default=None),
        employee: Optional[str] = Query(default=None),
        project: Optional[str] = Query(default=None),
        date_from: Optional[str] = Query(default=None),
        date_to: Optional[str] = Query(default=None),
        limit: int = Query(default=100, le=500),
        _: bool = Depends(_require_admin),
    ):
        query: Dict[str, Any] = {}
        if employee:
            query["employee_name"] = {"$regex": employee, "$options": "i"}
        if project:
            query["$or"] = [
                {"project_name": {"$regex": project, "$options": "i"}},
                {"project_number": {"$regex": project, "$options": "i"}},
            ]
        if date_from or date_to:
            d: Dict[str, str] = {}
            if date_from:
                d["$gte"] = date_from
            if date_to:
                d["$lte"] = date_to
            query["training_date"] = d
        if q:
            query.setdefault("$or", []).extend([
                {"employee_name": {"$regex": q, "$options": "i"}},
                {"project_name": {"$regex": q, "$options": "i"}},
                {"project_number": {"$regex": q, "$options": "i"}},
                {"instructor_name": {"$regex": q, "$options": "i"}},
            ])

        cur = db.safety_equipment_trainings.find(
            query,
            {"_id": 0, "employee_signature": 0, "instructor_signature": 0},
        ).sort("created_at", -1).limit(int(limit))
        items = [doc async for doc in cur]
        return {"ok": True, "items": items, "count": len(items)}

    @router.get("/equipment-trainings/{rec_id}")
    async def get_training(rec_id: str, _: bool = Depends(_require_safety_or_admin)):
        doc = await db.safety_equipment_trainings.find_one({"id": rec_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="not found")
        return doc

    @router.get("/equipment-trainings/{rec_id}/pdf")
    async def training_pdf(rec_id: str, _: bool = Depends(_require_safety_or_admin)):
        doc = await db.safety_equipment_trainings.find_one({"id": rec_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="not found")
        pdf = await asyncio.to_thread(render_training_pdf, doc)
        fname = f"MASCI_Equipment_Training_{(doc.get('employee_name') or '').replace(' ', '_')}_{doc.get('training_date', '')}.pdf"
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{fname}"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    return router
