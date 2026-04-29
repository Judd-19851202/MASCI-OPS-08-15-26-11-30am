"""
outage_alerts.py — Resend-backed outage email alerts.

Used by:
  • POST /api/admin/alert-outage  (called by SystemHealthBadge when it goes red)
  • Scheduled health monitor       (server-side periodic check, future hook)

Constraints we're honest about:
  • If the FastAPI process is fully dead (Cloudflare 520 / OOM kill), this
    helper can't fire — it lives inside that same process. For full-down
    coverage, an external pinger (UptimeRobot etc.) is required.
  • This helper covers the ~80% case: partial failures, slow endpoints,
    DB blips, individual collection errors. The browser badge sees them
    instantly and POSTs here, and we email Jaymn.

Cooldown:
  • At most one email per OUTAGE_ALERT_COOLDOWN_MINUTES per "issue key".
    Prevents inbox spam if the badge keeps re-firing every 60s while the
    same outage drags on.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Module-level cooldown tracker — survives across requests within one
# backend process. {issue_key: datetime_last_sent_utc}
_LAST_ALERT_SENT: dict[str, datetime] = {}


def _cooldown_minutes() -> int:
    try:
        return int(os.environ.get("OUTAGE_ALERT_COOLDOWN_MINUTES", "15"))
    except ValueError:
        return 15


def _alert_to() -> str:
    return (os.environ.get("OUTAGE_ALERT_TO") or "").strip()


def _on_cooldown(issue_key: str) -> bool:
    last = _LAST_ALERT_SENT.get(issue_key)
    if not last:
        return False
    minutes = (datetime.now(timezone.utc) - last).total_seconds() / 60.0
    return minutes < _cooldown_minutes()


async def send_outage_alert(
    *,
    issue_key: str,
    subject: str,
    summary: str,
    details_html: str = "",
) -> dict:
    """Send a one-line outage email via Resend (cooldown-gated).

    Returns a dict {sent: bool, reason: str, ...}. Never raises.
    """
    to = _alert_to()
    if not to:
        return {"sent": False, "reason": "OUTAGE_ALERT_TO not set"}

    api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    if not api_key:
        return {"sent": False, "reason": "RESEND_API_KEY missing"}

    if _on_cooldown(issue_key):
        return {
            "sent": False,
            "reason": f"on cooldown ({_cooldown_minutes()} min) for issue_key={issue_key}",
        }

    sender = (os.environ.get("SENDER_EMAIL") or "noreply@mascidocs.com").strip()
    reply_to = (os.environ.get("REPLY_TO_EMAIL") or "").strip()
    timestamp = datetime.now(timezone.utc).isoformat()

    html = f"""
<!doctype html><html><body style="font-family:system-ui,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#0f172a">
  <div style="background:#dc2626;color:white;padding:14px 18px;border-radius:8px;margin-bottom:18px">
    <div style="font-size:11px;letter-spacing:.2em;text-transform:uppercase;opacity:.85">MASCI Hub</div>
    <div style="font-size:20px;font-weight:900;margin-top:2px">⚠ Outage Detected</div>
  </div>
  <p style="margin:0 0 12px">{summary}</p>
  {details_html}
  <hr style="border:0;border-top:1px solid #e2e8f0;margin:18px 0">
  <p style="font-size:12px;color:#64748b;margin:0">
    Issue key: <code>{issue_key}</code><br>
    Detected at: <code>{timestamp}</code><br>
    Cooldown: {_cooldown_minutes()} min — duplicate alerts suppressed during this window.
  </p>
</body></html>
""".strip()

    plain = f"""MASCI Hub — Outage detected.

{summary}

Issue key: {issue_key}
Detected at: {timestamp}
""".strip()

    try:
        import resend  # type: ignore
        resend.api_key = api_key
        params = {
            "from": sender,
            "to": [to],
            "subject": subject,
            "html": html,
            "text": plain,
        }
        if reply_to:
            params["reply_to"] = reply_to
        result = await asyncio.to_thread(resend.Emails.send, params)
        rid = (result or {}).get("id")
        _LAST_ALERT_SENT[issue_key] = datetime.now(timezone.utc)
        logger.info(f"[outage-alert] sent to={to} resend_id={rid} issue_key={issue_key}")
        return {"sent": True, "to": to, "resend_id": rid, "ts": timestamp}
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[outage-alert] send failed: {e}")
        return {"sent": False, "reason": f"resend exception: {e}"}


def reset_cooldown(issue_key: Optional[str] = None) -> int:
    """Clear cooldown tracker. Returns number of entries cleared."""
    if issue_key:
        n = 1 if _LAST_ALERT_SENT.pop(issue_key, None) else 0
    else:
        n = len(_LAST_ALERT_SENT)
        _LAST_ALERT_SENT.clear()
    return n
