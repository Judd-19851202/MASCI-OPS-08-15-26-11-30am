"""TRACK 16.10A · Monday-morning Transportation Command Digest.

One internal weekly email summarising the current Transportation
Command Queue for Dispatch / Safety / Transportation Admin /
Operations Leadership. Email-only. No SMS. No external recipients.

Public API:
    build_transport_command_digest(db, *, now=None)
    send_transport_command_digest(db, *, now=None, dry_run=False,
                                   force=False, triggered_by="scheduler")
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
TENANT = "masci"
ROUTE_KEY = "TRANSPORT_COMMAND_DIGEST_WEEKLY"

DIGEST_LINKS = [
    ("Transportation Command Queue", "/admin/transportation/command-queue"),
    ("Document Center", "/admin/transportation/documents"),
    ("Inspection Center", "/admin/transportation/inspections"),
    ("Orientation Center", "/admin/transportation/orientation"),
    ("Email Pilot Panel", "/admin/transportation/orientation/emails"),
]


def _now_iso(now: Optional[datetime] = None) -> str:
    return (now or datetime.now(timezone.utc)).isoformat()


def _week_key(now: Optional[datetime] = None) -> str:
    now = now or datetime.now(timezone.utc)
    iso = now.isocalendar()
    return f"transport_command_digest:{iso.year}-{iso.week:02d}"


def _week_start_label(now: Optional[datetime] = None) -> str:
    now = now or datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())
    return monday.date().isoformat()


# ============================================================================
# Builder
# ============================================================================
async def build_transport_command_digest(db, *, now: Optional[datetime] = None
                                          ) -> Dict[str, Any]:
    """Read-only. Produces the digest payload + plain text + HTML."""
    now = now or datetime.now(timezone.utc)
    week_start = _week_start_label(now)
    horizon = now + timedelta(days=7)

    # 1. Open action items.
    actions = await db.transport_action_items.find(
        {"tenant": TENANT, "status": "open"}).to_list(2000)
    by_severity: Dict[str, List[Dict[str, Any]]] = {
        "blocking": [], "urgent": [], "action_required": [],
        "advisory": [], "info": [],
    }
    overdue: List[Dict[str, Any]] = []
    due_this_week: List[Dict[str, Any]] = []
    for a in actions:
        sev = a.get("severity") or "info"
        if sev in by_severity:
            by_severity[sev].append(a)
        # Overdue / due-this-week buckets.
        due = a.get("due_date")
        try:
            d = datetime.fromisoformat(str(due).replace("Z", "+00:00")) if due else None
        except Exception:  # noqa: BLE001
            d = None
        if d:
            # Coerce naive → UTC so comparisons never raise.
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            if d < now:
                overdue.append(a)
            elif d <= horizon:
                due_this_week.append(a)

    # 2. Email route health (TRANSPORT_* only).
    routes = await db.email_routes.find(
        {"tenant_key": TENANT, "route_key": {"$regex": "^TRANSPORT_"}}
    ).to_list(100)
    routes_active = []
    routes_audit_only = []
    routes_needs_config = []
    for r in routes:
        enabled = bool(r.get("enabled"))
        has_recipients = bool((r.get("to") or []) or (r.get("cc") or []) or (r.get("bcc") or []))
        if enabled and has_recipients:
            routes_active.append(r["route_key"])
        elif enabled and not has_recipients:
            routes_needs_config.append(r["route_key"])
        else:
            routes_audit_only.append(r["route_key"])

    summary = {
        "open_total": len(actions),
        "blocking": len(by_severity["blocking"]),
        "urgent": len(by_severity["urgent"]),
        "action_required": len(by_severity["action_required"]),
        "due_this_week": len(due_this_week),
        "overdue": len(overdue),
        "routes_needs_configuration": len(routes_needs_config),
        "routes_active": len(routes_active),
        "routes_audit_only": len(routes_audit_only),
    }

    # 3. Top items per section (cap to 10 each — keep email scannable).
    def _top(items: List[Dict[str, Any]], n: int = 10) -> List[Dict[str, Any]]:
        cleaned = []
        for it in sorted(items, key=lambda x: x.get("due_date") or "")[:n]:
            c = dict(it)
            c.pop("_id", None)
            cleaned.append(c)
        return cleaned

    sections = {
        "blocking_items": _top(by_severity["blocking"]),
        "urgent_items": _top(by_severity["urgent"]),
        "action_required_items": _top(by_severity["action_required"]),
        "expiring_soon_items": _top(due_this_week),
        "overdue_items": _top(overdue),
    }

    body_text = _render_text(summary, sections, week_start)
    body_html = _render_html(summary, sections, week_start, routes_active,
                             routes_audit_only, routes_needs_config)

    return {
        "week_key": _week_key(now),
        "week_start": week_start,
        "generated_at": _now_iso(now),
        "summary": summary,
        "sections": sections,
        "routes_active": routes_active,
        "routes_audit_only": routes_audit_only,
        "routes_needs_configuration": routes_needs_config,
        "subject": f"MASCI Transportation Command Digest — Week of {week_start}",
        "body_text": body_text,
        "body_html": body_html,
        "links": DIGEST_LINKS,
        "internal_only": True,
    }


def _item_line(a: Dict[str, Any]) -> str:
    title = a.get("title") or "Action"
    due = (a.get("due_date") or "")[:10]
    owner = a.get("assigned_role") or "transportation_admin"
    return f"  · {title}  (due {due}, owner: {owner})"


def _render_text(summary: Dict[str, Any], sections: Dict[str, List[Dict[str, Any]]],
                 week_start: str) -> str:
    lines: List[str] = []
    lines.append(f"MASCI Transportation Command Digest — Week of {week_start}")
    lines.append("=" * 64)
    lines.append("")
    lines.append("EXECUTIVE SUMMARY")
    lines.append(f"  Open action items: {summary['open_total']}")
    lines.append(f"  Blocking: {summary['blocking']}  ·  Urgent: {summary['urgent']}  ·  Action required: {summary['action_required']}")
    lines.append(f"  Due this week: {summary['due_this_week']}  ·  Overdue: {summary['overdue']}")
    lines.append(f"  Email routes needing configuration: {summary['routes_needs_configuration']}")
    lines.append("")
    for key, label in (("blocking_items", "BLOCKING ITEMS"),
                        ("urgent_items", "URGENT / ACTION REQUIRED"),
                        ("expiring_soon_items", "EXPIRING SOON (next 7 days)"),
                        ("overdue_items", "OVERDUE")):
        items = sections.get(key) or []
        if not items:
            continue
        lines.append(label)
        for a in items:
            lines.append(_item_line(a))
        lines.append("")
    lines.append("DIRECT LINKS")
    for label, url in DIGEST_LINKS:
        lines.append(f"  · {label}: {url}")
    lines.append("")
    lines.append("Internal MASCI Operations digest. Reply with any "
                 "questions; this email does not request credentials.")
    return "\n".join(lines)


def _render_html(summary, sections, week_start, routes_active,
                 routes_audit_only, routes_needs_config):
    def _ul(items):
        if not items:
            return ("<div style='color:#64748b;font-size:13px;font-style:italic'>"
                    "Nothing to report.</div>")
        return ("<ul style='padding-left:18px;margin:0'>" + "".join(
            f"<li style='margin:3px 0;font-size:13px'>{a.get('title','')} "
            f"<span style='color:#64748b'>(due {(a.get('due_date') or '')[:10]}, "
            f"owner {a.get('assigned_role') or 'transportation_admin'})</span></li>"
            for a in items
        ) + "</ul>")

    def _route_chip(label, items, tone):
        if not items:
            return ""
        chips = "".join(
            f"<code style='display:inline-block;background:{tone}10;color:{tone};"
            f"border:1px solid {tone}40;border-radius:4px;padding:1px 6px;"
            f"font-size:11px;margin:2px'>{r}</code>"
            for r in items
        )
        return (f"<div style='margin:6px 0'><strong style='font-size:12px;"
                f"color:{tone}'>{label}</strong><div>{chips}</div></div>")

    sections_html = "".join((
        "<h3 style='font-size:14px;color:#92400e;border-bottom:1px solid #fde68a;"
        "padding-bottom:4px;margin:18px 0 8px'>Blocking</h3>", _ul(sections["blocking_items"]),
        "<h3 style='font-size:14px;color:#9a3412;border-bottom:1px solid #fed7aa;"
        "padding-bottom:4px;margin:18px 0 8px'>Urgent / Action required</h3>",
        _ul(sections["urgent_items"]),
        _ul(sections["action_required_items"]),
        "<h3 style='font-size:14px;color:#0369a1;border-bottom:1px solid #bae6fd;"
        "padding-bottom:4px;margin:18px 0 8px'>Expiring soon (next 7 days)</h3>",
        _ul(sections["expiring_soon_items"]),
        "<h3 style='font-size:14px;color:#dc2626;border-bottom:1px solid #fecaca;"
        "padding-bottom:4px;margin:18px 0 8px'>Overdue</h3>",
        _ul(sections["overdue_items"]),
    ))

    links_html = "".join(
        f"<li style='margin:4px 0;font-size:13px'><a href='{u}' "
        f"style='color:#92400e;text-decoration:underline'>{n}</a></li>"
        for n, u in DIGEST_LINKS
    )

    return f"""
<div style="font-family:Helvetica,Arial,sans-serif;max-width:680px;margin:0 auto;
            padding:24px;border:1px solid #e2e8f0;border-radius:8px;color:#0f172a">
  <h2 style="color:#92400e;margin:0 0 4px">MASCI Transportation Command Digest</h2>
  <div style="color:#64748b;font-size:13px;margin-bottom:18px">Week of {week_start}</div>

  <div style="background:#fef3c7;border:1px solid #fde68a;border-radius:6px;
              padding:12px;margin-bottom:18px">
    <strong style="font-size:13px">Executive summary</strong>
    <div style="font-size:13px;margin-top:6px">
      Open action items: <strong>{summary['open_total']}</strong><br>
      Blocking: <strong>{summary['blocking']}</strong>
      &nbsp;·&nbsp; Urgent: <strong>{summary['urgent']}</strong>
      &nbsp;·&nbsp; Action required: <strong>{summary['action_required']}</strong><br>
      Due this week: <strong>{summary['due_this_week']}</strong>
      &nbsp;·&nbsp; Overdue: <strong>{summary['overdue']}</strong><br>
      Email routes needing configuration: <strong>{summary['routes_needs_configuration']}</strong>
    </div>
  </div>

  {sections_html}

  <h3 style="font-size:14px;color:#475569;border-bottom:1px solid #e2e8f0;
             padding-bottom:4px;margin:18px 0 8px">Email route health</h3>
  {_route_chip("Active send", routes_active, "#047857")}
  {_route_chip("Audit only / dry-run", routes_audit_only, "#475569")}
  {_route_chip("Needs configuration", routes_needs_config, "#b45309")}

  <h3 style="font-size:14px;color:#475569;border-bottom:1px solid #e2e8f0;
             padding-bottom:4px;margin:18px 0 8px">Direct links</h3>
  <ul style="padding-left:18px;margin:0">{links_html}</ul>

  <hr style="border:none;border-top:1px solid #e2e8f0;margin:18px 0" />
  <div style="font-size:11px;color:#64748b">
    Internal MASCI Operations digest. This message summarises tracked
    transportation compliance items so dispatch can plan the week.
    Action required does not imply punitive action — it indicates a
    requirement that needs attention to maintain dispatch eligibility.
  </div>
</div>
""".strip()


# ============================================================================
# Sender
# ============================================================================
async def send_transport_command_digest(
    db, *, now: Optional[datetime] = None,
    dry_run: bool = False, force: bool = False,
    triggered_by: str = "scheduler",
) -> Dict[str, Any]:
    """Resolve the weekly digest route through Email Routing v2 and fire
    real SMTP when the route is enabled + configured. Dedupe via the
    deterministic week_key so only one live digest per ISO week unless
    ``force=True``."""
    now = now or datetime.now(timezone.utc)
    week_key = _week_key(now)
    # Dedupe — live runs only.
    if not dry_run and not force:
        existing = await db.transport_command_digest_runs.find_one(
            {"tenant": TENANT, "week_key": week_key,
              "dry_run": False, "status": {"$in": ["sent", "needs_configuration"]}})
        if existing:
            return {"ok": True, "status": "already_sent_this_week",
                    "week_key": week_key, "dry_run": False,
                    "skipped": True}
    digest = await build_transport_command_digest(db, now=now)
    # Audit + resolve via routing v2.
    route_doc = await db.email_routes.find_one(
        {"tenant_key": TENANT, "route_key": ROUTE_KEY})
    enabled = bool((route_doc or {}).get("enabled"))
    effective_dry_run = dry_run or (not enabled)

    try:
        from email_routing_v2 import resolve_and_audit  # noqa: PLC0415
        resolution = await resolve_and_audit(
            db, route_key=ROUTE_KEY, legacy_provider=None,
            subject=digest["subject"],
            calling_module="transport_command_digest",
            dry_run=effective_dry_run,
        )
    except Exception as e:  # noqa: BLE001
        return _persist_run(db, week_key=week_key, status="errored",
                             dry_run=effective_dry_run, error=str(e)[:200],
                             triggered_by=triggered_by, summary=digest["summary"])

    recipients = list(resolution.to) if resolution and resolution.to else []
    if not recipients:
        try:
            await db.email_routing_audit_v2.insert_one({
                "route_key": ROUTE_KEY, "tenant_key": TENANT,
                "source": "transport_command_digest",
                "resolved_to_count": 0,
                "subject": digest["subject"][:240],
                "status": "needs_configuration",
                "calling_module": "transport_command_digest",
                "dry_run": True, "ts": _now_iso(now),
            })
        except Exception:  # noqa: BLE001
            pass
        return await _persist_run(
            db, week_key=week_key, status="needs_configuration",
            dry_run=True, triggered_by=triggered_by,
            summary=digest["summary"], digest=digest, recipients=0)

    if effective_dry_run:
        return await _persist_run(
            db, week_key=week_key, status="dry_run",
            dry_run=True, triggered_by=triggered_by,
            summary=digest["summary"], digest=digest,
            recipients=len(recipients))

    try:
        from lib.fsi_email_sender import fsi_send_email  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        return await _persist_run(
            db, week_key=week_key, status="errored",
            dry_run=False, error=str(e)[:200],
            triggered_by=triggered_by, summary=digest["summary"])

    sent_ids: List[str] = []
    last_error: Optional[str] = None
    for to in recipients:
        try:
            provider = await fsi_send_email(
                to, digest["subject"], digest["body_html"], db=db)
            sent_ids.append((provider or {}).get("id"))
            await db.email_routing_audit_v2.insert_one({
                "route_key": ROUTE_KEY, "tenant_key": TENANT,
                "source": "transport_command_digest",
                "resolved_to_count": 1,
                "subject": digest["subject"][:240],
                "status": "sent",
                "resend_message_id": (provider or {}).get("id"),
                "calling_module": "transport_command_digest",
                "dry_run": False, "ts": _now_iso(now),
            })
        except Exception as e:  # noqa: BLE001
            last_error = str(e)[:200]
            await db.email_routing_audit_v2.insert_one({
                "route_key": ROUTE_KEY, "tenant_key": TENANT,
                "source": "transport_command_digest",
                "resolved_to_count": 1,
                "subject": digest["subject"][:240],
                "status": "errored",
                "error": last_error,
                "calling_module": "transport_command_digest",
                "dry_run": False, "ts": _now_iso(now),
            })
    return await _persist_run(
        db, week_key=week_key,
        status="sent" if not last_error else "partial_error",
        dry_run=False, error=last_error,
        triggered_by=triggered_by,
        summary=digest["summary"], digest=digest,
        recipients=len(recipients), resend_ids=sent_ids)


async def _persist_run(db, *, week_key, status, dry_run, triggered_by,
                       summary, digest=None, recipients: int = 0,
                       resend_ids=None, error: Optional[str] = None
                       ) -> Dict[str, Any]:
    doc = {
        "id": uuid.uuid4().hex, "tenant": TENANT,
        "week_key": week_key, "status": status,
        "dry_run": dry_run, "triggered_by": triggered_by,
        "ts": _now_iso(),
        "summary": summary,
        "recipients_count": recipients,
        "resend_ids": resend_ids or [],
        "error": error,
        "subject": (digest or {}).get("subject"),
    }
    try:
        await db.transport_command_digest_runs.insert_one(doc.copy())
    except Exception:  # noqa: BLE001
        pass
    doc.pop("_id", None)
    return doc
