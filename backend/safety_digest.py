"""
safety_digest.py — weekly Monday-morning safety digest scheduler.

Mirrors backup_verification.verification_scheduler_loop. Runs forever on
an asyncio task; sleeps until the next configured send time, builds the
digest payload, emails it to safety@mascigc.com.

Configuration via env:
  SAFETY_DIGEST_ENABLED       (default "true") — toggle the whole cron
  SAFETY_DIGEST_TO_EMAIL      (default "safety@mascigc.com")
  SAFETY_DIGEST_HOUR_UTC      (default 14 — 14:00 UTC == 9:00 ET, Monday)
  SAFETY_DIGEST_WEEKDAY       (default 0 — Mon. 0=Mon..6=Sun)
  AUTO_EMAIL_REPORTS          (must be "true" for the email helper to actually send)
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Callable, Awaitable, Optional

logger = logging.getLogger(__name__)

EmailFn = Callable[[str, str, str], Awaitable[None]]


def _enabled() -> bool:
    return (os.environ.get("SAFETY_DIGEST_ENABLED") or "true").strip().lower() in (
        "1", "true", "yes", "on"
    )


def _seconds_until_next_send() -> float:
    """Compute seconds until the next configured (weekday, hour) UTC slot."""
    try:
        hour = int(os.environ.get("SAFETY_DIGEST_HOUR_UTC", "14"))
        weekday = int(os.environ.get("SAFETY_DIGEST_WEEKDAY", "0"))
    except ValueError:
        hour, weekday = 14, 0
    hour = max(0, min(23, hour))
    weekday = max(0, min(6, weekday))
    now = datetime.now(timezone.utc)
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    # Roll forward to the next matching weekday
    days_ahead = (weekday - now.weekday()) % 7
    if days_ahead == 0 and target <= now:
        days_ahead = 7
    target = target + timedelta(days=days_ahead)
    return (target - now).total_seconds()


async def safety_digest_scheduler_loop(
    db,
    build_payload: Callable[[], Awaitable[dict]],
    render_html: Callable[[dict], str],
    send_email_fn: Optional[EmailFn],
) -> None:
    """Long-running cron. Designed to never raise out — if anything goes
    wrong it logs and sleeps until the next slot."""
    while True:
        try:
            if not _enabled():
                # Disabled — sleep 1 hour and re-check (lets ops flip env)
                await asyncio.sleep(3600)
                continue
            wait_s = _seconds_until_next_send()
            logger.info(f"[safety-digest] sleeping {wait_s/3600:.1f}h until next send")
            await asyncio.sleep(max(60.0, wait_s))
            payload = await build_payload()
            html = render_html(payload)
            recipient = (os.environ.get("SAFETY_DIGEST_TO_EMAIL") or "safety@mascigc.com").strip()
            if send_email_fn:
                try:
                    await send_email_fn(recipient, "[MASCI] Weekly Safety Digest", html)
                    logger.info(f"[safety-digest] sent to {recipient}")
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"[safety-digest] email send failed: {e}")
            else:
                logger.info(f"[safety-digest] (no email fn) payload={payload['kpis']}")
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[safety-digest] loop iteration crashed: {e}")
            # Sleep a bit to avoid tight crash loops
            await asyncio.sleep(600)
