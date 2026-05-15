"""
fire_ext_attachments.py — Iter135. Attachment + printable-history endpoints
bolted onto the Fire Extinguisher register so the unit row carries its
inspection paperwork, photos, and a printable record together.

Storage: hybrid (R2 when configured, base64 inline otherwise) — reuses
`safety_doc_storage` so we don't ship a second storage layer. Max 10 MB
per file, 5 attachments per unit to keep the embedded array bounded.

Schema additions on `db.fire_extinguishers`:
  attachments: [
    { id, filename, content_type, file_size, file_data (doc:// or data:),
      storage_backend, kind (paperwork|photo|other), uploaded_by, uploaded_at }
  ]

Endpoints (mounted under /api):
  POST   /safety/fire-extinguishers/{fe_id}/attachments
  DELETE /safety/fire-extinguishers/{fe_id}/attachments/{att_id}
  GET    /safety/fire-extinguishers/{fe_id}/attachments/{att_id}
  GET    /safety/fire-extinguishers/{fe_id}/history.pdf
"""
from __future__ import annotations

import base64
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Callable

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse

import safety_doc_storage

logger = logging.getLogger(__name__)

MAX_ATT_BYTES = 10 * 1024 * 1024
MAX_ATT_PER_UNIT = 25
VALID_KINDS = {"paperwork", "photo", "other"}


def _render_history_html(fe: dict) -> str:
    """Printable unit history — header, register info, inspection log,
    attachment list. Uses the shared MASCI PDF chrome."""
    from pdf_branding import wrap_pdf_html  # noqa: PLC0415

    inspections = sorted(
        (fe.get("inspections") or []),
        key=lambda x: x.get("inspection_date") or "",
        reverse=True,
    )
    rows_html = ""
    for ins in inspections:
        status = ins.get("status", "")
        status_cls = "status-pass" if status == "Pass" else ("status-fail" if status == "Fail" else "status-other")
        rows_html += (
            f"<tr><td>{ins.get('inspection_date', '')}</td>"
            f"<td class='{status_cls}'>{status}</td>"
            f"<td>{ins.get('inspector_name', '')}</td>"
            f"<td>{ins.get('notes', '') or '—'}</td></tr>"
        )
    if not rows_html:
        rows_html = "<tr><td colspan='4' class='muted'>No inspections logged yet.</td></tr>"

    atts_html = ""
    for a in (fe.get("attachments") or []):
        size_kb = (a.get("file_size") or 0) / 1024
        atts_html += (
            f"<li><strong>{a.get('filename', '—')}</strong> "
            f"<span class='muted'>· {a.get('kind', 'other')} · {size_kb:.1f} KB · "
            f"{a.get('uploaded_at', '')[:10]}</span></li>"
        )
    if not atts_html:
        atts_html = "<li class='muted'>No attachments on file.</li>"

    body = f"""
<table style="margin: 0 0 16pt 0;">
  <tr><td style="width:50%;padding:0;border:none;"><div class="muted" style="font-family:'Courier New',monospace;font-size:8pt;letter-spacing:0.14em;text-transform:uppercase;">Type / Size</div><div style="font-weight:700;">{fe.get('type', '—')} · {fe.get('size', '—')}</div></td>
      <td style="padding:0;border:none;"><div class="muted" style="font-family:'Courier New',monospace;font-size:8pt;letter-spacing:0.14em;text-transform:uppercase;">Serial Number</div><div style="font-weight:700;">{fe.get('serial_number', '—') or '—'}</div></td></tr>
  <tr><td style="padding:6pt 0 0 0;border:none;"><div class="muted" style="font-family:'Courier New',monospace;font-size:8pt;letter-spacing:0.14em;text-transform:uppercase;">Location</div><div style="font-weight:700;">{fe.get('location_value', '—')} <span class="muted" style="font-weight:400;">({fe.get('location_kind', '')})</span></div></td>
      <td style="padding:6pt 0 0 0;border:none;"><div class="muted" style="font-family:'Courier New',monospace;font-size:8pt;letter-spacing:0.14em;text-transform:uppercase;">Assigned Truck / Project</div><div style="font-weight:700;">{fe.get('truck', '') or '—'} · {fe.get('project_number', '') or '—'}</div></td></tr>
  <tr><td style="padding:6pt 0 0 0;border:none;"><div class="muted" style="font-family:'Courier New',monospace;font-size:8pt;letter-spacing:0.14em;text-transform:uppercase;">Last Inspection</div><div style="font-weight:700;">{fe.get('last_inspection_date', '—') or '—'} · {fe.get('last_status', '—')}</div></td>
      <td style="padding:6pt 0 0 0;border:none;"><div class="muted" style="font-family:'Courier New',monospace;font-size:8pt;letter-spacing:0.14em;text-transform:uppercase;">Next Due</div><div style="font-weight:700;">{fe.get('next_due_date', '—') or '—'}</div></td></tr>
</table>

<h2>Inspection Log</h2>
<table>
  <thead><tr><th>Date</th><th>Status</th><th>Inspector</th><th>Notes</th></tr></thead>
  <tbody>{rows_html}</tbody>
</table>

<h2>Attachments on File</h2>
<ul>{atts_html}</ul>
"""
    return wrap_pdf_html(
        body,
        title=f"Unit {fe.get('unit_id', '—')} — Inspection History",
        kicker="SAFETY · FIRE EXTINGUISHER RECORD",
    )


def register_fire_ext_attachment_routes(
    api_router: APIRouter, db, require_safety_token: Callable,
) -> None:

    @api_router.post("/safety/fire-extinguishers/{fe_id}/attachments")
    async def add_fe_attachment(
        fe_id: str,
        file: UploadFile = File(...),
        kind: str = Form("other"),
        user: dict = Depends(require_safety_token),
    ):
        fe = await db.fire_extinguishers.find_one({"id": fe_id}, {"_id": 0})
        if not fe:
            raise HTTPException(404, "Fire extinguisher not found")
        if len(fe.get("attachments") or []) >= MAX_ATT_PER_UNIT:
            raise HTTPException(409, f"Max {MAX_ATT_PER_UNIT} attachments per unit reached")
        if kind not in VALID_KINDS:
            kind = "other"
        raw = await file.read()
        if not raw:
            raise HTTPException(400, "Empty file")
        if len(raw) > MAX_ATT_BYTES:
            raise HTTPException(413, f"File too large. Max {MAX_ATT_BYTES // (1024 * 1024)} MB.")

        content_type = file.content_type or "application/octet-stream"
        filename = (file.filename or "attachment").strip()
        att_id = str(uuid.uuid4())

        storage_backend = "inline"
        if safety_doc_storage.is_configured():
            try:
                ref = await safety_doc_storage.upload_doc_bytes(
                    raw, doc_id=f"fe-{fe_id}-{att_id}", filename=filename, content_type=content_type,
                )
                file_data = ref
                storage_backend = "r2"
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[fe-att] R2 upload failed, falling back to inline: {e}")
                try:
                    await db.r2_degraded_events.insert_one({
                        "at": datetime.now(timezone.utc),
                        "module": "fire_ext_attachments",
                        "doc_id": att_id,
                        "filename": filename,
                        "size_bytes": len(raw),
                        "error": str(e)[:240],
                    })
                except Exception:  # noqa: BLE001
                    pass
                file_data = f"data:{content_type};base64,{base64.b64encode(raw).decode('ascii')}"
        else:
            file_data = f"data:{content_type};base64,{base64.b64encode(raw).decode('ascii')}"

        att = {
            "id": att_id,
            "filename": filename,
            "content_type": content_type,
            "file_size": len(raw),
            "file_data": file_data,
            "storage_backend": storage_backend,
            "kind": kind,
            "uploaded_by_name": user.get("name") or "",
            "uploaded_by_email": user.get("email") or "",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.fire_extinguishers.update_one(
            {"id": fe_id},
            {"$push": {"attachments": att}, "$set": {"updated_at": att["uploaded_at"]}},
        )
        # Return without the heavy file_data blob
        meta = {k: v for k, v in att.items() if k != "file_data"}
        return meta

    @api_router.delete("/safety/fire-extinguishers/{fe_id}/attachments/{att_id}")
    async def delete_fe_attachment(
        fe_id: str, att_id: str, _: dict = Depends(require_safety_token),
    ):
        fe = await db.fire_extinguishers.find_one({"id": fe_id}, {"_id": 0, "attachments": 1})
        if not fe:
            raise HTTPException(404, "Fire extinguisher not found")
        target = next((a for a in (fe.get("attachments") or []) if a.get("id") == att_id), None)
        if not target:
            raise HTTPException(404, "Attachment not found")
        # Best-effort R2 delete
        try:
            await safety_doc_storage.delete_doc(target.get("file_data"))
        except Exception:  # noqa: BLE001
            pass
        await db.fire_extinguishers.update_one(
            {"id": fe_id},
            {"$pull": {"attachments": {"id": att_id}}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        return {"ok": True, "deleted": att_id}

    @api_router.get("/safety/fire-extinguishers/{fe_id}/attachments/{att_id}")
    async def download_fe_attachment(
        fe_id: str, att_id: str, _: dict = Depends(require_safety_token),
    ):
        fe = await db.fire_extinguishers.find_one({"id": fe_id}, {"_id": 0, "attachments": 1})
        if not fe:
            raise HTTPException(404, "Fire extinguisher not found")
        target = next((a for a in (fe.get("attachments") or []) if a.get("id") == att_id), None)
        if not target:
            raise HTTPException(404, "Attachment not found")
        try:
            data = await safety_doc_storage.read_doc_bytes(target.get("file_data") or "")
        except Exception as e:  # noqa: BLE001
            raise HTTPException(500, f"Could not read attachment: {e}") from e
        return Response(
            content=data,
            media_type=target.get("content_type") or "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{target.get("filename", "attachment")}"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    @api_router.get("/safety/fire-extinguishers/{fe_id}/history.pdf")
    async def fe_history_pdf(fe_id: str, _: dict = Depends(require_safety_token)):
        fe = await db.fire_extinguishers.find_one({"id": fe_id}, {"_id": 0})
        if not fe:
            raise HTTPException(404, "Fire extinguisher not found")
        try:
            from weasyprint import HTML  # noqa: PLC0415
        except ImportError as e:
            raise HTTPException(500, f"weasyprint missing: {e}") from e
        html = _render_history_html(fe)
        pdf_bytes = HTML(string=html).write_pdf()
        unit_id_safe = "".join(c if c.isalnum() else "_" for c in (fe.get("unit_id") or fe_id))[:60]
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="fe_{unit_id_safe}_history.pdf"'},
        )


__all__ = ["register_fire_ext_attachment_routes"]
