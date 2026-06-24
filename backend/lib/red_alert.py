"""TRACK 15.76A · Red Alert Hook.

Send **exactly one** operator email when the platform Trust Score
band transitions to RED. Uses cooldown persisted in
``red_alert_state`` so we never spam the operator.

Rules (per the spec):
  * No alert spam.
  * Cooldown persisted (default 60 minutes).
  * One alert per RED transition (only when previous_band != "red").
  * Body includes top RED reason, affected workflow(s), Trust Center
    link, remediation summary.
  * If already RED and the underlying reason is unchanged inside the
    cooldown window → do NOT send.

Returns one of: ``"sent"`` | ``"cooldown"`` | ``"unchanged"`` |
``"not_red"`` | ``"disabled"`` | ``"error"``.

Best-effort: never raises. A failed alert must never mask the
underlying RED condition on the dashboard.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("red_alert")

ALERT_DOC_ID = "platform_band"
DEFAULT_COOLDOWN_MIN = 60


async def maybe_send(
    db,
    *,
    current_band: str,
    score: int,
    score_reason: str,
    workflows: List[Dict[str, Any]],
    trust_center_url: str,
    now: Optional[datetime] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Send a red alert if the band just flipped to RED.

    Returns ``{result, sent_to, cooldown_until, previous_band, ...}``.
    """
    now = now or datetime.now(timezone.utc)
    try:
        state = await db.red_alert_state.find_one(
            {"_id": ALERT_DOC_ID}
        ) or {}
        previous_band: str = state.get("band") or "unknown"
        last_alert_at: Optional[str] = state.get("last_alert_at")
        last_reason: str = state.get("last_reason") or ""
        cooldown_until: Optional[str] = state.get("cooldown_until")

        # Always update the latest observed band so the dashboard +
        # subsequent invocations see truth — regardless of whether
        # an alert is actually sent below.
        await db.red_alert_state.update_one(
            {"_id": ALERT_DOC_ID},
            {"$set": {
                "band": current_band,
                "score": int(score),
                "score_reason": score_reason,
                "last_seen_at": now.isoformat(),
            }, "$setOnInsert": {"_id": ALERT_DOC_ID}},
            upsert=True,
        )

        # Only fire when current is red.
        if current_band != "red":
            return {
                "result": "not_red",
                "previous_band": previous_band,
                "cooldown_until": cooldown_until,
            }

        # If previous was already red AND we are inside cooldown AND
        # the underlying reason is unchanged → suppress.
        if (
            previous_band == "red"
            and cooldown_until
            and now.isoformat() < cooldown_until
            and last_reason == score_reason
        ):
            return {
                "result": "cooldown",
                "previous_band": previous_band,
                "cooldown_until": cooldown_until,
            }

        # If previous was already red, reason unchanged, but cooldown
        # expired → still suppress as "unchanged" (we don't re-alert
        # for the same condition).
        if previous_band == "red" and last_reason == score_reason:
            return {
                "result": "unchanged",
                "previous_band": previous_band,
                "cooldown_until": cooldown_until,
            }

        if os.environ.get("AUTO_EMAIL_REPORTS", "false").lower() != "true":
            # Mark as sent-state to avoid re-triggering once we DO turn
            # email on, but report the disabled status truthfully.
            await _record_attempt(db, now, current_band, score_reason, [])
            return {
                "result": "disabled",
                "previous_band": previous_band,
                "cooldown_until": cooldown_until,
                "reason": (
                    "AUTO_EMAIL_REPORTS is not 'true' — alert recorded "
                    "but not sent."
                ),
            }

        if not os.environ.get("RESEND_API_KEY"):
            await _record_attempt(db, now, current_band, score_reason, [])
            return {
                "result": "disabled",
                "previous_band": previous_band,
                "cooldown_until": cooldown_until,
                "reason": "RESEND_API_KEY is not set",
            }

        recipients = _resolve_alert_recipients()
        if dry_run:
            await _record_attempt(db, now, current_band, score_reason, recipients)
            return {
                "result": "sent",
                "previous_band": previous_band,
                "sent_to": recipients,
                "dry_run": True,
                "cooldown_until": (now + timedelta(minutes=DEFAULT_COOLDOWN_MIN)).isoformat(),
            }

        red_workflows = [
            w.get("workflow") for w in workflows if w.get("band") == "red"
        ]
        body = _render_body(
            score=score,
            score_reason=score_reason,
            red_workflows=red_workflows,
            trust_center_url=trust_center_url,
        )

        try:
            import resend  # noqa: PLC0415
            resend.api_key = os.environ["RESEND_API_KEY"]
            from_addr = os.environ.get(
                "RESEND_FROM", "alerts@mascigc.com"
            )
            resend.Emails.send({
                "from": from_addr,
                "to": recipients,
                "subject": (
                    "[MASCI Operations Trust Center] "
                    "Platform band flipped RED"
                ),
                "html": body,
            })
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "[red_alert] resend failed band=%s err=%s", current_band, exc
            )
            # Set cooldown anyway so we don't hammer Resend with the same
            # broken request on every endpoint call. The dashboard band
            # still reflects truth — only the email side is suppressed.
            await _record_attempt(db, now, current_band, score_reason, [])
            return {
                "result": "error",
                "error": str(exc)[:200],
                "previous_band": previous_band,
                "cooldown_until": (
                    now + timedelta(minutes=DEFAULT_COOLDOWN_MIN)
                ).isoformat(),
            }

        await _record_attempt(db, now, current_band, score_reason, recipients)
        return {
            "result": "sent",
            "previous_band": previous_band,
            "sent_to": recipients,
            "cooldown_until": (
                now + timedelta(minutes=DEFAULT_COOLDOWN_MIN)
            ).isoformat(),
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("[red_alert] maybe_send failed: %s", exc)
        return {"result": "error", "error": str(exc)[:200]}


def _resolve_alert_recipients() -> List[str]:
    raw = (
        os.environ.get("OPS_ALERT_TO")
        or os.environ.get("ADMIN_DEAD_LETTER_EMAIL")
        or os.environ.get("ADMIN_EMAIL")
        or ""
    )
    return [
        a.strip() for a in raw.split(",") if a.strip() and "@" in a
    ]


def _render_body(
    *,
    score: int,
    score_reason: str,
    red_workflows: List[str],
    trust_center_url: str,
) -> str:
    affected = ", ".join(red_workflows[:6]) or "—"
    return (
        f"<div style='font-family: -apple-system, system-ui, sans-serif;"
        f" font-size: 14px; color: #0f172a;'>"
        f"<h2 style='margin: 0 0 12px 0; color: #c8102e;'>"
        f"⚠ MASCI Operations Trust Center — Platform band flipped RED"
        f"</h2>"
        f"<p>Trust score: <strong>{score}</strong> · "
        f"Reason: <em>{score_reason}</em></p>"
        f"<p>Affected workflow(s): <code>{affected}</code></p>"
        f"<p>Open the Operations Trust Center to view the exact failing "
        f"records and remediation steps:</p>"
        f"<p><a href='{trust_center_url}' style='display:inline-block;"
        f"background:#c8102e;color:white;padding:8px 14px;border-radius:"
        f"6px;text-decoration:none;font-weight:600;'>Open Trust Center</a></p>"
        f"<p style='color:#64748b;font-size:12px;margin-top:24px;'>This "
        f"is an automated alert from the MASCI Operations Trust Center. "
        f"You will not receive another alert for the same condition "
        f"within the next {DEFAULT_COOLDOWN_MIN} minutes.</p>"
        f"</div>"
    )


async def _record_attempt(
    db, now: datetime, band: str, reason: str, recipients: List[str]
) -> None:
    cooldown_until = (now + timedelta(minutes=DEFAULT_COOLDOWN_MIN)).isoformat()
    await db.red_alert_state.update_one(
        {"_id": ALERT_DOC_ID},
        {"$set": {
            "band": band,
            "last_reason": reason,
            "last_alert_at": now.isoformat(),
            "last_alert_to": recipients,
            "cooldown_until": cooldown_until,
        }, "$setOnInsert": {"_id": ALERT_DOC_ID}},
        upsert=True,
    )
