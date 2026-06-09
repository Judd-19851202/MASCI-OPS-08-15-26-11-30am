"""
_credential_alerts.py — MOTIVE-PROD-INCIDENT-001 permanent detection.

Triggered from the webhook receiver when a provider hit lands without
configured credentials. Records a single open incident per (provider,
kind) and dispatches one email (cooldown-gated via the existing
outage_alerts helper) the first time the condition is observed.

DOCTRINE:
  • Alert only — NEVER auto-remediates credentials.
  • Cooldown re-uses the same OUTAGE_ALERT_COOLDOWN_MINUTES knob.
  • Storage is idempotent: $inc on hit_count, $setOnInsert on first
    discovery, so concurrent webhook hits collapse to one incident row.
  • Resolution is driven from `routes/integrations/config.py` when an
    operator stores the missing credential. No background job needed.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from outage_alerts import send_outage_alert

logger = logging.getLogger(__name__)

_INCIDENT_COLLECTION = "production_incidents"
_KIND = "credential_missing"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _issue_key(provider: str) -> str:
    return f"integration_credential_missing:{provider}"


async def record_credential_missing(db, *, provider: str) -> None:
    """Increment / open the open incident for this provider and fire a
    one-shot email + admin_audit row on FIRST discovery.

    Safe to call on every webhook hit — only the first call in a
    cooldown window actually emails; the rest just increment hit_count.
    Fire-and-forget from the webhook handler.
    """
    try:
        now = _now()
        # Atomic upsert. $setOnInsert distinguishes "first discovery"
        # from "subsequent hit" so we only email + audit once.
        res = await db[_INCIDENT_COLLECTION].update_one(
            {"provider": provider, "kind": _KIND, "resolved": False},
            {
                "$setOnInsert": {
                    "incident_id": f"INC-CRED-{provider.upper()}-{int(datetime.now(timezone.utc).timestamp())}",
                    "provider": provider,
                    "kind": _KIND,
                    "resolved": False,
                    "first_seen_at": now,
                    "opened_by": "credential_missing_monitor",
                    "severity": "high",
                    "title": f"{provider} webhook received with no credentials configured",
                },
                "$set": {"last_seen_at": now},
                "$inc": {"hit_count": 1},
            },
            upsert=True,
        )
        is_first_open = res.upserted_id is not None
        if not is_first_open:
            # Subsequent hit — just bump counters, no email, no audit row
            return

        # First-discovery actions: admin_audit + email
        await db.admin_audit.insert_one({
            "ts": now,
            "actor_email": "system:credential_missing_monitor",
            "action": "integration_credential_missing_detected",
            "target": provider,
            "diff": {
                "provider": provider,
                "kind": _KIND,
                "severity": "high",
                "reason": "Webhook received but integration_settings has no api_key_value / webhook_secret_value.",
            },
            "ip": "internal",
            "user_agent": "credential-missing-monitor",
        })

        # Email (cooldown-gated). Never raises; returns a dict either way.
        await send_outage_alert(
            issue_key=_issue_key(provider),
            subject=f"[MASCI] {provider.title()} webhook received but credentials are MISSING",
            summary=(
                f"Production has begun receiving {provider} webhook deliveries, "
                f"but `integration_settings.{provider}` has no api_key_value or "
                f"webhook_secret_value configured. Every incoming webhook is being "
                f"rejected. No data is being persisted."
            ),
            details_html=(
                "<div style='background:#fef3c7;border:1px solid #fde68a;padding:14px 18px;border-radius:6px;color:#78350f'>"
                f"<b>Action required:</b> open Admin → Integration Center → {provider.title()} and paste the "
                f"API key + webhook secret. No code change needed. This alert was raised once on first detection; "
                f"subsequent rejected webhooks will silently increment the incident's hit_count until you resolve "
                f"it (resolution is automatic when credentials are saved)."
                "</div>"
            ),
        )
    except Exception as e:  # noqa: BLE001
        # NEVER raise from this helper — the webhook receiver must
        # remain available regardless of monitor failures.
        logger.warning(f"[cred-missing-monitor] record failed for {provider}: {e}")


async def mark_resolved(db, *, provider: str, resolved_by: str = "operator") -> int:
    """Close every open credential_missing incident for this provider.
    Called from the integration-settings update path when a secret is
    saved. Returns the count of incidents resolved.
    """
    try:
        now = _now()
        res = await db[_INCIDENT_COLLECTION].update_many(
            {"provider": provider, "kind": _KIND, "resolved": False},
            {"$set": {
                "resolved": True,
                "resolved_at": now,
                "resolved_by": resolved_by,
            }},
        )
        if res.modified_count:
            await db.admin_audit.insert_one({
                "ts": now,
                "actor_email": "system:credential_missing_monitor",
                "action": "integration_credential_missing_resolved",
                "target": provider,
                "diff": {
                    "provider": provider,
                    "kind": _KIND,
                    "resolved_by": resolved_by,
                    "incidents_closed": res.modified_count,
                },
                "ip": "internal",
                "user_agent": "credential-missing-monitor",
            })
        return res.modified_count
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[cred-missing-monitor] resolve failed for {provider}: {e}")
        return 0


__all__ = ["record_credential_missing", "mark_resolved"]
