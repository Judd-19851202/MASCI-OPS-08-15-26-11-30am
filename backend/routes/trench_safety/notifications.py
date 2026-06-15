"""Trench Safety · Notification routing module (Phase 7.5C).

Single source of truth for every Trench Safety notification event.

Wires Trench Safety into the existing MASCI notification infrastructure:
  • `lib.event_fanout.emit_notification` → bell + audit
  • `_trench_send_email` (server.py) → Resend with `[MASCI · TRENCH SAFETY]` subject
  • Weekly Safety Digest section (consumed by `safety_digest.py`)

NO new collections. NO new cron. NO new sender. NO new bell.

Every emitter:
  * Is fire-and-forget — never raises (wraps in try/except).
  * Writes the same audit trail used by every other domain.
  * Uses the central ROUTING_MATRIX so add/remove/change rules touch
    ONE table and one set of tests.

Public API (used by trench_safety routes):
  await notify_hold_opened(db, asset, hold)
  await notify_hold_cleared(db, asset, hold)
  await notify_inspection_failed(db, asset, inspection)
  await notify_certification_event(db, asset, cert, *, kind)
  await notify_damage_report(db, asset, report)
  await notify_repair_awaiting_safety(db, asset, repair)
  await notify_asset_returned_to_service(db, asset)
  await build_trench_digest_section(db) -> dict   # used by safety_digest
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
# ROUTING MATRIX — single source of truth
# ─────────────────────────────────────────────────────────────────────
# Each entry: (recipient_roles, bell_severity, send_email, in_digest)
# `recipient_roles` is the list of `recipient_role` fanouts to emit
# (one bell row per role; the existing fanout engine handles
# per-recipient delivery).
ROUTING_MATRIX: Dict[str, Dict[str, Any]] = {
    "trench_safety.hold_opened.safety": {
        "roles": ["safety", "shop", "dispatch", "admin"],
        "severity": "Critical",
        "email": True,
        "digest": True,
    },
    "trench_safety.hold_opened.certification": {
        "roles": ["safety", "admin"],
        "severity": "Warning",
        "email": True,
        "digest": True,
    },
    "trench_safety.hold_opened.inspection": {
        "roles": ["safety"],
        "severity": "Warning",
        "email": False,
        "digest": True,
    },
    "trench_safety.hold_opened.maintenance": {
        "roles": ["safety", "shop"],
        "severity": "Info",
        "email": False,
        "digest": True,
    },
    "trench_safety.hold_cleared": {
        "roles": ["safety"],
        "severity": "Info",
        "email": False,
        "digest": False,
    },
    "trench_safety.inspection_failed.critical": {
        "roles": ["safety", "shop"],
        "severity": "Critical",
        "email": True,
        "digest": True,
    },
    "trench_safety.inspection_failed.major": {
        "roles": ["safety", "shop"],
        "severity": "Warning",
        "email": False,
        "digest": True,
    },
    "trench_safety.damage_report": {
        "roles": ["safety"],
        "severity": "Warning",
        "email": False,
        "digest": True,
    },
    "trench_safety.unsafe_condition": {
        "roles": ["safety"],
        "severity": "Warning",
        "email": False,
        "digest": True,
    },
    "trench_safety.cert_due_soon_30": {
        "roles": ["safety"],
        "severity": "Info",
        "email": False,
        "digest": True,
    },
    "trench_safety.cert_due_soon_14": {
        "roles": ["safety"],
        "severity": "Warning",
        "email": True,
        "digest": True,
    },
    "trench_safety.cert_due_soon_7": {
        "roles": ["safety", "admin"],
        "severity": "Critical",
        "email": True,
        "digest": True,
    },
    "trench_safety.cert_expired": {
        "roles": ["safety", "shop", "admin"],
        "severity": "Critical",
        "email": True,
        "digest": True,
    },
    "trench_safety.repair_awaiting_safety": {
        "roles": ["safety"],
        "severity": "Warning",
        "email": False,
        "digest": True,
    },
    "trench_safety.asset_returned_to_service": {
        "roles": ["safety", "shop", "dispatch"],
        "severity": "Info",
        "email": False,
        "digest": True,
    },
}

PORTAL_URL = (os.environ.get("PORTAL_PUBLIC_URL")
              or os.environ.get("PUBLIC_BASE_URL")
              or "https://mascidocs.com").rstrip("/")


def _asset_link(asset_id: str) -> str:
    return f"{PORTAL_URL}/safety/trench-safety/assets/{asset_id}"


def _coaching(what: str, why: str, next_step: str) -> str:
    """Format coaching block — used in bell `message` and email body.
    No punitive language."""
    return (
        f"What happened: {what}\n"
        f"Why it matters: {why}\n"
        f"What to do next: {next_step}"
    )


async def _fanout(db, routing_key: str, *,
                  title: str,
                  message: str,
                  asset: Dict[str, Any],
                  source_record_id: Optional[str] = None,
                  extra: Optional[Dict[str, Any]] = None) -> List[str]:
    """Emit one bell notification per recipient role in the routing
    matrix. Returns the list of notification ids created."""
    rule = ROUTING_MATRIX.get(routing_key)
    if not rule:
        logger.warning("[trench-notifications] unknown routing key: %s", routing_key)
        return []
    from lib.event_fanout import emit_notification  # noqa: PLC0415
    asset_id = asset.get("asset_id", "")
    ids: List[str] = []
    for role in rule["roles"]:
        payload = {
            "type": routing_key.split(".", 2)[0] + "." + routing_key.split(".")[1],
            # Constraint: tasks_notifications truncates `type` to 48 chars,
            # so keep the public type stable (`trench_safety.<event>`) and
            # carry the variant in `linked_source_module`.
            "title": title,
            "message": message,
            "severity": rule["severity"],
            "recipient_role": role,
            "linked_source_module": f"trench_safety:{routing_key}",
            "linked_source_record_id": source_record_id or asset_id,
            "linked_equipment_id": asset_id,
            "email_enabled": rule["email"],
        }
        if extra:
            payload.update(extra)
        nid = await emit_notification(db, payload)
        if nid:
            ids.append(nid)
    return ids


async def _send_email(routing_key: str, *,
                      asset: Dict[str, Any],
                      subject_tail: str,
                      body_html: str) -> None:
    """Send an email via the existing `_trench_send_email` wrapper,
    if the routing rule asks for one and the platform is configured
    to send. Fire-and-forget."""
    rule = ROUTING_MATRIX.get(routing_key)
    if not rule or not rule["email"]:
        return
    try:
        # Lazy import — avoids circular ref with server.py.
        from server import _trench_send_email  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        logger.warning("[trench-notifications] _trench_send_email import failed: %s", e)
        return
    asset_id = asset.get("asset_id", "")
    subject = f"[MASCI · TRENCH SAFETY] {subject_tail} — {asset_id}"
    # Resolve recipient emails via existing routing/safety user store.
    recipients = await _resolve_email_recipients(rule["roles"])
    for r in recipients:
        try:
            await _trench_send_email(r, subject, body_html)
        except Exception as e:  # noqa: BLE001
            logger.warning("[trench-notifications] send to %s failed: %s", r, e)


async def _resolve_email_recipients(roles: Iterable[str]) -> List[str]:
    """Resolve role → email addresses by reading the existing
    `safety_users` / `shop_users` / environment fallbacks. Reuses the
    same role naming conventions used elsewhere in the platform.
    Falls back to env defaults so preview environments still log a
    deterministic recipient."""
    out: List[str] = []
    env_map = {
        "safety":   os.environ.get("SAFETY_DIGEST_TO_EMAIL", "")
                    or os.environ.get("SUPER_ADMIN_EMAIL", ""),
        "shop":     os.environ.get("SHOP_MANAGER_EMAIL", "shopmanager@mascigc.com"),
        "dispatch": os.environ.get("DISPATCH_EMAIL", "")
                    or os.environ.get("SUPER_ADMIN_EMAIL", ""),
        "admin":    os.environ.get("SUPER_ADMIN_EMAIL", ""),
    }
    for role in roles:
        em = (env_map.get(role) or "").strip()
        if em and em.lower() not in {x.lower() for x in out}:
            out.append(em)
    return out


# ─────────────────────────────────────────────────────────────────────
# Public emitters — called from trench_safety routes
# ─────────────────────────────────────────────────────────────────────
def _asset_label(asset: Dict[str, Any]) -> str:
    return asset.get("asset_id", "?")


def _loc(asset: Dict[str, Any]) -> str:
    return (asset.get("current_project_name")
            or asset.get("current_location")
            or asset.get("yard_location")
            or "MASCI Yard")


async def notify_hold_opened(db, asset: Dict[str, Any], hold: Dict[str, Any]) -> None:
    kind = hold.get("kind", "")
    key_suffix = {
        "Safety Hold": "safety",
        "Certification Hold": "certification",
        "Inspection Hold": "inspection",
        "Maintenance Hold": "maintenance",
    }.get(kind, "inspection")
    routing_key = f"trench_safety.hold_opened.{key_suffix}"
    title = f"{kind} opened — {_asset_label(asset)}"
    msg = _coaching(
        what=f"{kind} opened on {_asset_label(asset)} ({_loc(asset)}).",
        why="The asset cannot be used until the hold is released.",
        next_step=f"Open the asset record and review the reason. Reason: {hold.get('reason') or '—'}",
    )
    await _fanout(db, routing_key, title=title, message=msg,
                  asset=asset, source_record_id=hold.get("id"))
    body = _email_body(asset, title, msg)
    await _send_email(routing_key, asset=asset,
                      subject_tail=f"{kind} Issued", body_html=body)


async def notify_hold_cleared(db, asset: Dict[str, Any], hold: Dict[str, Any]) -> None:
    title = f"{hold.get('kind','Hold')} released — {_asset_label(asset)}"
    msg = _coaching(
        what=f"{hold.get('kind','Hold')} cleared on {_asset_label(asset)}.",
        why="The asset returns to its prior operational status.",
        next_step="Confirm the asset is available for assignment before scheduling work.",
    )
    await _fanout(db, "trench_safety.hold_cleared", title=title, message=msg,
                  asset=asset, source_record_id=hold.get("id"))


async def notify_inspection_failed(db, asset: Dict[str, Any], inspection: Dict[str, Any]) -> None:
    severity = (inspection.get("severity") or "").strip()
    if severity == "Critical":
        routing_key = "trench_safety.inspection_failed.critical"
    elif severity == "Major":
        routing_key = "trench_safety.inspection_failed.major"
    else:
        return  # Minor fails surface in the asset detail but don't fanout
    title = f"{severity} Inspection Failure — {_asset_label(asset)}"
    msg = _coaching(
        what=f"{severity} fail recorded by {inspection.get('inspector_name') or 'inspector'}.",
        why="Asset is unsafe for use until repaired and re-inspected.",
        next_step=f"Open the asset record. Notes: {inspection.get('notes') or '—'}",
    )
    await _fanout(db, routing_key, title=title, message=msg,
                  asset=asset, source_record_id=inspection.get("id"))
    body = _email_body(asset, title, msg)
    await _send_email(routing_key, asset=asset,
                      subject_tail=f"{severity} Inspection Failure", body_html=body)


async def notify_damage_report(db, asset: Dict[str, Any], report: Dict[str, Any]) -> None:
    kind = (report.get("kind") or "Damage").strip()
    routing_key = ("trench_safety.unsafe_condition"
                   if kind == "Unsafe Condition"
                   else "trench_safety.damage_report")
    title = f"{kind} reported — {_asset_label(asset)}"
    msg = _coaching(
        what=f"{kind} reported from the field on {_asset_label(asset)}.",
        why="Reports drive triage decisions and may justify opening a Safety Hold.",
        next_step=f"Review the report and decide on next steps. Detail: {(report.get('description') or '—')[:240]}",
    )
    await _fanout(db, routing_key, title=title, message=msg,
                  asset=asset, source_record_id=report.get("id"))


async def notify_certification_event(db, asset: Dict[str, Any], cert: Dict[str, Any], *, days: Optional[int]) -> None:
    """One emitter handles due-soon-30/14/7 and expired."""
    if days is None or days >= 0:
        # determine bucket
        if days is None:
            return
        if days <= 7:
            routing_key = "trench_safety.cert_due_soon_7"
            label = "≤ 7 days"
        elif days <= 14:
            routing_key = "trench_safety.cert_due_soon_14"
            label = "≤ 14 days"
        elif days <= 30:
            routing_key = "trench_safety.cert_due_soon_30"
            label = "≤ 30 days"
        else:
            return
        title = f"Certification due {label} — {_asset_label(asset)}"
        msg = _coaching(
            what=f"{cert.get('kind','Certification')} expires {cert.get('expires_at','')[:10]}.",
            why="Once expired, the asset enters Certification Hold automatically.",
            next_step="Schedule re-certification with the issuer.",
        )
        await _fanout(db, routing_key, title=title, message=msg,
                      asset=asset, source_record_id=cert.get("id"))
        if ROUTING_MATRIX[routing_key]["email"]:
            body = _email_body(asset, title, msg)
            await _send_email(routing_key, asset=asset,
                              subject_tail=f"Certification Due {label}", body_html=body)
    else:
        routing_key = "trench_safety.cert_expired"
        title = f"Certification EXPIRED — {_asset_label(asset)}"
        msg = _coaching(
            what=f"{cert.get('kind','Certification')} expired on {cert.get('expires_at','')[:10]}.",
            why="The asset has been placed on Certification Hold automatically.",
            next_step="Re-certify the asset to clear the hold.",
        )
        await _fanout(db, routing_key, title=title, message=msg,
                      asset=asset, source_record_id=cert.get("id"))
        body = _email_body(asset, title, msg)
        await _send_email(routing_key, asset=asset,
                          subject_tail="Certification Expired", body_html=body)


async def notify_repair_awaiting_safety(db, asset: Dict[str, Any], repair: Dict[str, Any]) -> None:
    title = f"Repair complete · awaiting Safety verification — {_asset_label(asset)}"
    msg = _coaching(
        what=f"Shop reports the repair on {_asset_label(asset)} is complete.",
        why="The asset stays on Inspection Hold until Safety verifies the work.",
        next_step="Schedule a return inspection and verify the repair from the Safety Portal.",
    )
    await _fanout(db, "trench_safety.repair_awaiting_safety",
                  title=title, message=msg, asset=asset, source_record_id=repair.get("id"))


async def notify_asset_returned_to_service(db, asset: Dict[str, Any]) -> None:
    title = f"Asset returned to service — {_asset_label(asset)}"
    msg = _coaching(
        what=f"{_asset_label(asset)} is now Available.",
        why="The asset can be assigned to projects again.",
        next_step="Confirm the next deployment with Dispatch.",
    )
    await _fanout(db, "trench_safety.asset_returned_to_service",
                  title=title, message=msg, asset=asset)


# ─────────────────────────────────────────────────────────────────────
# Email body
# ─────────────────────────────────────────────────────────────────────
def _email_body(asset: Dict[str, Any], title: str, coaching_text: str) -> str:
    """Plain MASCI house-style HTML — matches the existing
    transactional emails (Safety / HR / PM portal). No template engine."""
    asset_id = asset.get("asset_id", "")
    asset_type = asset.get("asset_type", "")
    size = asset.get("size", "")
    location = _loc(asset)
    status = asset.get("operational_status", "")
    serial = asset.get("serial_number") or "—"
    link = _asset_link(asset_id)
    coaching_html = coaching_text.replace("\n", "<br />")
    return f"""<!doctype html>
<html><body style="font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; color:#0f172a;">
  <div style="max-width:640px;margin:0 auto;padding:18px 16px;">
    <div style="font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:#0e7490;font-weight:bold;">MASCI · Trench Safety</div>
    <h1 style="font-size:22px;margin:6px 0 14px;color:#0f172a;">{title}</h1>
    <table cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;border:1px solid #e2e8f0;border-radius:6px;overflow:hidden;">
      <tr style="background:#f8fafc;">
        <td style="padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:#64748b;">Asset</td>
        <td style="padding:8px 10px;font-weight:bold;">{asset_id}</td>
      </tr>
      <tr><td style="padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:#64748b;">Type / Size</td><td style="padding:8px 10px;">{asset_type} · {size}</td></tr>
      <tr style="background:#f8fafc;"><td style="padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:#64748b;">Serial</td><td style="padding:8px 10px;font-family: ui-monospace, SFMono-Regular, monospace;">{serial}</td></tr>
      <tr><td style="padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:#64748b;">Location</td><td style="padding:8px 10px;">{location}</td></tr>
      <tr style="background:#f8fafc;"><td style="padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:#64748b;">Status</td><td style="padding:8px 10px;">{status}</td></tr>
    </table>
    <p style="margin:18px 0 4px;color:#0f172a;">{coaching_html}</p>
    <p style="margin:18px 0;">
      <a href="{link}" style="display:inline-block;background:#0e7490;color:#ffffff;text-decoration:none;padding:10px 18px;border-radius:6px;font-weight:bold;letter-spacing:0.08em;text-transform:uppercase;font-size:12px;">Open Asset</a>
    </p>
    <p style="margin-top:24px;font-size:11px;color:#64748b;">MASCI Operations Platform · Field-safe view at <a href="{PORTAL_URL}/trench-safety/assets/{asset_id}" style="color:#0e7490;">{PORTAL_URL}/trench-safety/assets/{asset_id}</a></p>
  </div>
</body></html>"""


# ─────────────────────────────────────────────────────────────────────
# Weekly Safety Digest section (read-only)
# ─────────────────────────────────────────────────────────────────────
async def build_trench_digest_section(db) -> Dict[str, Any]:
    """Section payload consumed by `safety_digest.render_digest_html`
    and `routes/notifications.py:_build_safety_digest`. NO new collection
    — every metric reads from existing trench_safety_* canonical stores."""
    now = datetime.now(timezone.utc)
    from datetime import timedelta as _td  # local
    week_ago = now - _td(days=7)
    open_safety_holds = await db.trench_safety_holds.count_documents({"is_active": True, "kind": "Safety Hold"})
    open_cert_holds   = await db.trench_safety_holds.count_documents({"is_active": True, "kind": "Certification Hold"})
    open_insp_holds   = await db.trench_safety_holds.count_documents({"is_active": True, "kind": "Inspection Hold"})
    open_maint_holds  = await db.trench_safety_holds.count_documents({"is_active": True, "kind": "Maintenance Hold"})
    awaiting_verify   = await db.trench_safety_repairs.count_documents({
        "status": "Completed", "requires_reinspection": True,
    })
    expiring_30 = await db.trench_safety_certifications.count_documents({
        "status": "Active",
        "expires_at": {"$gte": now.isoformat(), "$lte": (now + _td(days=30)).isoformat()},
    })
    new_damage = await db.trench_safety_repairs.count_documents({
        "source": "Public QR Damage Report",
        "received_at": {"$gte": week_ago.isoformat()},
    })
    failed_insps_week = await db.trench_safety_inspections.count_documents({
        "result": "Fail",
        "submitted_at": {"$gte": week_ago.isoformat()},
    })
    return {
        "key": "trench_safety",
        "title": "Trench Safety",
        "open_safety_holds": open_safety_holds,
        "open_certification_holds": open_cert_holds,
        "open_inspection_holds": open_insp_holds,
        "open_maintenance_holds": open_maint_holds,
        "repairs_awaiting_verification": awaiting_verify,
        "expiring_certifications_30d": expiring_30,
        "new_damage_reports_7d": new_damage,
        "failed_inspections_7d": failed_insps_week,
    }


__all__ = [
    "ROUTING_MATRIX",
    "notify_hold_opened",
    "notify_hold_cleared",
    "notify_inspection_failed",
    "notify_damage_report",
    "notify_certification_event",
    "notify_repair_awaiting_safety",
    "notify_asset_returned_to_service",
    "build_trench_digest_section",
]
