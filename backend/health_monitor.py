"""
health_monitor.py — Iter132 lightweight synthetic monitor.

Polls /api/admin/system-health every 60 s. If `overall == "red"` AND
the same red subsystem has been red for ≥2 consecutive checks (no
single-blip false alarms), fires a Resend alert. Includes 30-minute
per-subsystem cooldown so an outage doesn't spam 30+ emails.

Every check is logged to db.health_monitor_runs (lightweight — just
{at, overall, red_keys, alerted}). No PII. No verbose payloads.

Alert recipients: env var HEALTH_ALERT_RECIPIENTS (comma-separated).
Falls back to BACKUP_EMAIL_TO or safety@mascigc.com.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 60
COOLDOWN_MINUTES = 30
DEBOUNCE_REQUIRED_FAILURES = 2  # need 2 in a row before alerting


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def _recipients() -> List[str]:
    raw = os.environ.get("HEALTH_ALERT_RECIPIENTS", "").strip()
    if raw:
        return [s.strip() for s in raw.split(",") if s.strip()]
    fallback = (os.environ.get("BACKUP_EMAIL_TO") or "safety@mascigc.com").strip()
    return [fallback]


async def _send_alert(red_cards: List[Dict[str, Any]], overall: str) -> bool:
    """Send a single Resend email summarizing the red subsystems."""
    if os.environ.get("AUTO_EMAIL_REPORTS", "false").lower() not in ("true", "1", "yes"):
        return False
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        return False

    sender = os.environ.get("SENDER_EMAIL", "noreply@mascidocs.com")
    env_label = os.environ.get("DEPLOY_ENV", "production")
    dashboard = os.environ.get(
        "DEPLOY_PUBLIC_URL",
        "https://mascidocs.com",
    ).rstrip("/") + "/admin/system-health"
    when = _iso(_now())

    rows = "".join(
        f'<tr><td style="padding:6px 10px;font-weight:700;border-bottom:1px solid #e5e7eb;color:#7f1d1d;">{c["label"]}</td>'
        f'<td style="padding:6px 10px;border-bottom:1px solid #e5e7eb;color:#1e293b;">{c.get("detail", "—")}</td></tr>'
        for c in red_cards
    )
    html = f"""
    <div style="font-family:system-ui,-apple-system,sans-serif;max-width:600px;margin:0 auto;color:#0f172a;">
      <div style="border-bottom:4px solid #b91c1c;padding-bottom:10px;margin-bottom:15px;">
        <strong style="color:#b91c1c;letter-spacing:.15em;font-size:11px;text-transform:uppercase">
          MASCI Operations Platform · Health Alert
        </strong>
      </div>
      <p style="font-size:15px;margin:0 0 10px;">
        <strong style="color:#b91c1c;">System Health: {overall.upper()}</strong> ·
        <span style="color:#475569;">{env_label} · {when}</span>
      </p>
      <p style="font-size:14px;margin:0 0 14px;color:#334155;">
        The following subsystems have been failing on at least 2 consecutive checks:
      </p>
      <table style="width:100%;border-collapse:collapse;font-size:13px;border:1px solid #e5e7eb;border-radius:4px;">
        <thead><tr style="background:#fef2f2;">
          <th style="text-align:left;padding:6px 10px;color:#7f1d1d;font-size:11px;letter-spacing:.1em;text-transform:uppercase">Subsystem</th>
          <th style="text-align:left;padding:6px 10px;color:#7f1d1d;font-size:11px;letter-spacing:.1em;text-transform:uppercase">Detail</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="margin:20px 0 8px;">
        <a href="{dashboard}" style="display:inline-block;background:#b91c1c;color:white;padding:10px 18px;text-decoration:none;border-radius:4px;font-weight:700;font-size:13px;letter-spacing:.05em">
          OPEN HEALTH DASHBOARD
        </a>
      </p>
      <p style="font-size:11px;color:#64748b;margin-top:14px;">
        Synthetic monitor · iter132 · 60-second poll · 30-minute cooldown per subsystem
      </p>
    </div>
    """
    subject = f"[MASCI] System Health {overall.upper()} — {len(red_cards)} subsystem(s) failing"

    try:
        import httpx  # noqa: PLC0415
        async with httpx.AsyncClient(timeout=10) as client:
            for to in _recipients():
                await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": sender,
                        "to": [to],
                        "subject": subject,
                        "html": html,
                    },
                )
        return True
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[health_monitor] Resend send failed: {e}")
        return False


def start_health_monitor_loop(
    db,
    system_health_fn: Callable,
) -> asyncio.Task:
    """Spin up the background task. Idempotent — call once at startup.

    `system_health_fn` is the actual coroutine that returns the same
    `{overall, cards, checked_at}` payload as `GET /api/admin/system-health`.
    We pass the function in (not the HTTP path) so we don't pay an HTTP
    round-trip to ourselves.
    """
    consecutive: Dict[str, int] = {}
    last_alerted: Dict[str, datetime] = {}

    async def loop():
        # Stagger initial start so multiple workers don't all alert at once
        await asyncio.sleep(15)
        logger.info("[health_monitor] iter132 synthetic monitor armed (60s poll, 30m cooldown)")
        while True:
            try:
                payload = await system_health_fn()
                overall = payload.get("overall", "yellow")
                cards = payload.get("cards", [])
                red_cards = [c for c in cards if c.get("status") == "red"]
                red_keys: Set[str] = {c.get("key") or c.get("label") or "?" for c in red_cards}

                # Log every run (lightweight)
                try:
                    await db.health_monitor_runs.insert_one({
                        "at": _iso(_now()),
                        "overall": overall,
                        "red_keys": list(red_keys),
                        "alerted": False,
                    })
                except Exception:  # noqa: BLE001
                    pass

                # Reset counters for subsystems that recovered
                for k in list(consecutive.keys()):
                    if k not in red_keys:
                        consecutive.pop(k, None)

                # Find subsystems that have stayed red long enough AND are out of cooldown
                to_alert: List[Dict[str, Any]] = []
                now = _now()
                for c in red_cards:
                    key = c.get("key") or c.get("label") or "?"
                    consecutive[key] = consecutive.get(key, 0) + 1
                    if consecutive[key] < DEBOUNCE_REQUIRED_FAILURES:
                        continue
                    last = last_alerted.get(key)
                    if last and (now - last) < timedelta(minutes=COOLDOWN_MINUTES):
                        continue
                    to_alert.append(c)
                    last_alerted[key] = now

                if to_alert:
                    sent = await _send_alert(to_alert, overall)
                    # Stamp the last run as alerted=True
                    try:
                        await db.health_monitor_runs.update_one(
                            {}, {"$set": {"alerted": sent}}, sort=[("at", -1)],
                        )
                    except Exception:  # noqa: BLE001
                        pass
                    logger.warning(
                        f"[health_monitor] ALERT sent={sent} subsystems={[c.get('key') for c in to_alert]}"
                    )

            except Exception as e:  # noqa: BLE001
                logger.warning(f"[health_monitor] poll failed: {e}")

            await asyncio.sleep(POLL_INTERVAL_SEC)

    return asyncio.create_task(loop())


__all__ = ["start_health_monitor_loop", "POLL_INTERVAL_SEC", "COOLDOWN_MINUTES"]
