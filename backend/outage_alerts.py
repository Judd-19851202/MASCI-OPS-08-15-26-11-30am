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


def _env_tag() -> str:
    """ALERT-ENV-001 · Return the canonical environment label for
    operator-facing alert emails. Reads `APP_ENV` then `ENVIRONMENT`
    then defaults to `PRODUCTION` (matches the server.py default at
    line 837 and `_storage.py` after APP-ENV-001).

    Always returns an uppercase token: PRODUCTION or PREVIEW. Any
    non-`preview` value normalises to PRODUCTION so that operators only
    ever see two possibilities in their inbox.
    """
    raw = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "production").strip().lower()
    return "PREVIEW" if raw == "preview" else "PRODUCTION"


def _decorate_subject(subject: str, tag: str) -> str:
    """Prepend `[TAG]` to subject. Idempotent — if the subject already
    begins with `[TAG]` we leave it alone (so callers that pre-tag won't
    end up with two prefixes)."""
    s = subject or ""
    expected = f"[{tag}]"
    return s if s.lstrip().startswith(expected) else f"{expected} {s}".strip()


_ENV_BANNER_COLORS = {
    "PRODUCTION": ("#0f172a", "#fef2f2", "#dc2626"),   # slate text, light-red bg, red accent
    "PREVIEW":    ("#0f172a", "#fef9c3", "#a16207"),   # slate text, light-yellow bg, amber accent
}


def render_env_banner_html(tag: Optional[str] = None) -> str:
    """ALERT-ENV-001 · Standardised env banner injected at the top of
    HTML alert bodies. Mobile-readable (560px max-width container is
    assumed; the banner uses 100% width and inline styles)."""
    t = (tag or _env_tag()).upper()
    text_c, bg_c, accent = _ENV_BANNER_COLORS.get(t, _ENV_BANNER_COLORS["PRODUCTION"])
    return (
        f"<div style='margin:0 0 14px;padding:10px 14px;border-left:4px solid {accent};"
        f"background:{bg_c};color:{text_c};border-radius:4px;font:600 12px/1.4 system-ui,sans-serif;"
        f"letter-spacing:.12em;text-transform:uppercase'>"
        f"Environment: <span style='color:{accent}'>{t}</span>"
        "</div>"
    )


def render_env_banner_text(tag: Optional[str] = None) -> str:
    t = (tag or _env_tag()).upper()
    return f"Environment: {t}"


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

    # ALERT-ENV-001 · Decorate subject with [PRODUCTION] / [PREVIEW] and
    # inject an env banner into the HTML + plain text so operators can
    # instantly tell which environment fired the alert.
    env_tag = _env_tag()
    subject = _decorate_subject(subject, env_tag)
    env_banner_html = render_env_banner_html(env_tag)
    env_banner_text = render_env_banner_text(env_tag)

    html = f"""
<!doctype html><html><body style="font-family:system-ui,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#0f172a">
  {env_banner_html}
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

{env_banner_text}

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
