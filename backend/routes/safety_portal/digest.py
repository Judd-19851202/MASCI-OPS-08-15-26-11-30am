"""
Safety Portal · digest.py — Phase 5 weekly Monday digest helpers +
endpoints.

Helpers are module-level so the weekly cron in `safety_digest.py` can
import them WITHOUT instantiating a router (and without entangling the
scheduler in FastAPI dependency machinery).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)


# ─── Build payload (used by /preview, /send, and the cron) ──────────
async def build_digest_payload(db) -> dict:
    now = datetime.now(timezone.utc)
    today = now.isoformat()[:10]
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    thirty_days_out = (now + timedelta(days=30)).isoformat()[:10]
    return {
        "as_of": now.isoformat(),
        "kpis": {
            "open_corrective_actions": await db.corrective_actions.count_documents(
                {"status": {"$in": ["Open", "In Progress", "Pending Review"]}}
            ),
            "overdue_corrective_actions": await db.corrective_actions.count_documents({
                "status": {"$in": ["Open", "In Progress", "Pending Review"]},
                "due_date": {"$ne": None, "$lt": today},
            }),
            "incidents_last_7d": await db.incidents.count_documents(
                {"created_at": {"$gte": seven_days_ago}}
            ),
            "meetings_last_7d": await db.safety_meetings.count_documents(
                {"created_at": {"$gte": seven_days_ago}}
            ),
            "training_expiring_30d": await db.safety_training_records.count_documents(
                {"expiration_date": {"$ne": None, "$gte": today, "$lte": thirty_days_out}}
            ),
            "training_expired": await db.safety_training_records.count_documents(
                {"expiration_date": {"$ne": None, "$lt": today}}
            ),
            "fire_extinguishers_overdue": await db.fire_extinguishers.count_documents(
                {"next_due_date": {"$ne": None, "$lt": today}}
            ),
        },
        "top_open_corrective_actions": await db.corrective_actions.find(
            {"status": {"$in": ["Open", "In Progress", "Pending Review"]}},
            {"_id": 0, "title": 1, "priority": 1, "status": 1, "project_number": 1,
             "due_date": 1, "assigned_to_name": 1},
        ).sort("created_at", 1).to_list(5),
    }


# ─── Render HTML (mailable layout — cyan-700 brand) ─────────────────
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


def register_digest_routes(
    api_router: APIRouter, db, require_safety_token,
    send_email_fn: Optional[Callable] = None,
) -> None:

    @api_router.get("/safety/digest/preview", dependencies=[Depends(require_safety_token)])
    async def safety_digest_preview():
        payload = await build_digest_payload(db)
        return {"payload": payload, "html": render_digest_html(payload)}

    @api_router.post("/safety/digest/send", dependencies=[Depends(require_safety_token)])
    async def safety_digest_send_now(to_email: Optional[str] = None):
        payload = await build_digest_payload(db)
        html = render_digest_html(payload)
        recipient = (to_email or "safety@mascigc.com").strip()
        sent = False
        if send_email_fn:
            try:
                # The wrapper returns True only when Resend was actually
                # invoked (False on preview-env short-circuits) so the
                # client UI can report accurate status.
                result = await send_email_fn(recipient, "[MASCI] Weekly Safety Digest", html)
                sent = bool(result)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[safety-digest] send failed: {e}")
        return {"ok": True, "sent": sent, "to": recipient, "payload": payload}


__all__ = ["register_digest_routes", "build_digest_payload", "render_digest_html"]
