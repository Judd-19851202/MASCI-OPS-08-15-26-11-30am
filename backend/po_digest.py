"""po_digest.py — iter246 F3 · Weekly Monday PO Request digest.

Mirrors iter120 safety_digest.py architecture exactly. Long-running
asyncio task that sleeps until the next Monday 14:00 UTC slot, builds
a per-recipient payload (PMs scoped to their assigned jobs · HR sees
all), renders a lightweight HTML email, and dispatches via Resend.

Stabilization invariants honored:
  - Reuses iter238 [MASCI · TAG] subject prefix pattern (literal subject
    since digests are not record-tied — same approach as iter120 Safety).
  - Reuses safety_digest's _seconds_until_next_send() cron rhythm — no
    new notification architecture.
  - Reuses pm_auth.compute_pm_scope's job-set semantics — no parallel
    scope filter.
  - Single send per slot · per-recipient · no duplicate-fire risk.

Configuration via env (all optional):
  PO_DIGEST_ENABLED       (default "true")
  PO_DIGEST_HOUR_UTC      (default 14)
  PO_DIGEST_WEEKDAY       (default 0 = Mon)
  AUTO_EMAIL_REPORTS      (must be "true" for the helper to actually send)
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, List, Optional

logger = logging.getLogger(__name__)

EmailFn = Callable[[str, str, str], Awaitable[bool]]

PO_OPEN_STATUSES = (
    "Submitted",
    "Pending Approval",
    "Clarification Needed",
    "Approved",
    "Pending Receipt",
    "Overdue Receipt",
)

DIGEST_SUBJECT = "[MASCI \u00b7 PO] Weekly Request PO Digest"


def _enabled() -> bool:
    return (os.environ.get("PO_DIGEST_ENABLED") or "true").strip().lower() in (
        "1", "true", "yes", "on",
    )


def _seconds_until_next_send() -> float:
    try:
        hour = int(os.environ.get("PO_DIGEST_HOUR_UTC", "14"))
        weekday = int(os.environ.get("PO_DIGEST_WEEKDAY", "0"))
    except ValueError:
        hour, weekday = 14, 0
    hour = max(0, min(23, hour))
    weekday = max(0, min(6, weekday))
    now = datetime.now(timezone.utc)
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    days_ahead = (weekday - now.weekday()) % 7
    if days_ahead == 0 and target <= now:
        days_ahead = 7
    target = target + timedelta(days=days_ahead)
    return (target - now).total_seconds()


async def _summarize_pos(db, *, project_numbers: Optional[List[str]] = None) -> dict:
    """Counts + top vendors over scoped open POs.

    project_numbers=None  -> all jobs (HR/admin).
    project_numbers=[...] -> restricted (PM scope).
    project_numbers=[]    -> explicit empty -> zero POs.
    """
    base: dict = {}
    if project_numbers is not None:
        if not project_numbers:
            return {
                "total_open": 0, "by_status": {},
                "pending_approval": 0, "pending_receipt": 0,
                "overdue_receipt": 0, "top_vendors": [],
                "scoped_to_jobs": 0,
            }
        base["project_number"] = {"$in": list(project_numbers)}

    coll = db.po_requests
    by_status: dict = {}
    for status in PO_OPEN_STATUSES:
        q = dict(base)
        q["status"] = status
        by_status[status] = await coll.count_documents(q)
    total_open = sum(by_status.values())

    pipeline = [
        {"$match": {**base, "status": {"$in": list(PO_OPEN_STATUSES)}}},
        {"$group": {"_id": "$vendor", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},
        {"$limit": 5},
    ]
    top_vendors = []
    async for row in coll.aggregate(pipeline):
        name = row.get("_id") or ""
        if not name:
            continue
        top_vendors.append({"vendor": name, "count": int(row.get("count") or 0)})

    return {
        "total_open": total_open,
        "by_status": by_status,
        "pending_approval": by_status.get("Pending Approval", 0)
                            + by_status.get("Clarification Needed", 0),
        "pending_receipt": by_status.get("Pending Receipt", 0)
                           + by_status.get("Approved", 0),
        "overdue_receipt": by_status.get("Overdue Receipt", 0),
        "top_vendors": top_vendors,
        "scoped_to_jobs": len(project_numbers) if project_numbers is not None else None,
    }


async def build_pm_digest_payload(db, pm: dict) -> dict:
    """Per-PM payload — scoped to PM's assigned jobs (primary + co-PM)."""
    email = (pm.get("email") or "").strip().lower()
    cursor = db.jobs_master.find(
        {"$or": [{"pm_email": email}, {"co_pm_emails": email}],
         "deleted_at": {"$in": [None, ""]}},
        {"_id": 0, "project_number": 1},
    )
    nums = []
    async for j in cursor:
        pn = (j.get("project_number") or "").strip()
        if pn:
            nums.append(pn)
    summary = await _summarize_pos(db, project_numbers=nums)
    return {
        "recipient_role": "pm",
        "recipient_name": pm.get("name") or email,
        "recipient_email": email,
        "as_of": datetime.now(timezone.utc).isoformat(),
        **summary,
    }


async def build_hr_digest_payload(db, hr_user: dict) -> dict:
    """Per-HR payload — sees all POs (HR has cross-portal read access)."""
    summary = await _summarize_pos(db, project_numbers=None)
    return {
        "recipient_role": "hr",
        "recipient_name": hr_user.get("name") or hr_user.get("email") or "",
        "recipient_email": (hr_user.get("email") or "").strip().lower(),
        "as_of": datetime.now(timezone.utc).isoformat(),
        **summary,
    }


def render_po_digest_html(payload: dict, *, portal_url: str = "") -> str:
    """Lightweight Monday-morning-triage layout in indigo (PM brand)."""
    name = payload.get("recipient_name") or ""
    role = payload.get("recipient_role") or "pm"
    role_label = "Project Manager" if role == "pm" else "HR"
    scope_blurb = ""
    nums = payload.get("scoped_to_jobs")
    if role == "pm" and nums is not None:
        scope_blurb = f"Scoped to your <strong>{nums}</strong> assigned job(s)."
    elif role == "hr":
        scope_blurb = "Platform-wide visibility (HR cross-portal scope)."

    bs = payload.get("by_status") or {}
    rows = ""
    for status in PO_OPEN_STATUSES:
        n = bs.get(status, 0)
        if n == 0:
            continue
        rows += (
            "<tr>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #e5e7eb'>{status}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #e5e7eb;text-align:right;font-family:Menlo,Courier,monospace'><strong>{n}</strong></td>"
            "</tr>"
        )
    if not rows:
        rows = ("<tr><td colspan='2' style='padding:10px;text-align:center;color:#64748b'>"
                "No open PO requests in your scope this week. Clean slate.</td></tr>")

    vrows = ""
    for v in payload.get("top_vendors") or []:
        vrows += (
            "<tr>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #e5e7eb'>{v['vendor']}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #e5e7eb;text-align:right;font-family:Menlo,Courier,monospace'><strong>{v['count']}</strong></td>"
            "</tr>"
        )
    if not vrows:
        vrows = ("<tr><td colspan='2' style='padding:10px;text-align:center;color:#64748b'>"
                 "No vendor activity this week.</td></tr>")

    cta = ""
    if portal_url:
        link = portal_url.rstrip("/") + "/po-requests"
        cta = (
            "<div style='margin:18px 0 0;text-align:center'>"
            f"<a href='{link}' style='display:inline-block;background:#4338ca;color:white;"
            "text-decoration:none;font-weight:700;font-size:13px;padding:10px 22px;"
            "border-radius:4px;letter-spacing:0.04em;text-transform:uppercase'>"
            "Open PO Requests &rarr;</a></div>"
        )

    return (
        '<div style="font-family:Helvetica,Arial,sans-serif;max-width:640px;margin:0 auto;color:#0f172a">'
        '<div style="background:#4338ca;color:white;padding:16px 22px;border-radius:6px 6px 0 0">'
        '<div style="font-family:Courier,monospace;font-size:11px;letter-spacing:0.18em;opacity:0.85">MASCI &middot; PO OPERATIONS</div>'
        '<h1 style="font-size:22px;margin:4px 0 0;font-weight:900">Weekly Request PO Digest</h1>'
        f'<div style="font-size:11px;opacity:0.85;margin-top:4px">{payload["as_of"][:10]} &middot; {role_label}: {name}</div>'
        '</div>'
        '<div style="background:white;border:1px solid #e5e7eb;border-top:none;padding:18px 22px;border-radius:0 0 6px 6px">'
        f'<p style="margin:0 0 14px;font-size:13px;color:#475569;line-height:1.5">{scope_blurb}</p>'
        '<table cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;margin:0 0 6px"><tr>'
        '<td style="width:50%;padding:8px 10px;background:#eef2ff;border:1px solid #c7d2fe;border-radius:4px 0 0 4px">'
        '<div style="font-family:Courier,monospace;font-size:10px;letter-spacing:0.18em;color:#3730a3;font-weight:700;text-transform:uppercase">Pending Approval</div>'
        f'<div style="font-size:26px;font-weight:900;color:#3730a3;line-height:1.1;margin-top:4px">{payload.get("pending_approval", 0)}</div></td>'
        '<td style="width:50%;padding:8px 10px;background:#fef3c7;border:1px solid #fde68a;border-radius:0 4px 4px 0">'
        '<div style="font-family:Courier,monospace;font-size:10px;letter-spacing:0.18em;color:#92400e;font-weight:700;text-transform:uppercase">Pending Receipt</div>'
        f'<div style="font-size:26px;font-weight:900;color:#92400e;line-height:1.1;margin-top:4px">{payload.get("pending_receipt", 0)}</div></td>'
        '</tr></table>'
        '<table cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;margin:6px 0 18px"><tr>'
        '<td style="width:50%;padding:8px 10px;background:#fee2e2;border:1px solid #fecaca;border-radius:4px 0 0 4px">'
        '<div style="font-family:Courier,monospace;font-size:10px;letter-spacing:0.18em;color:#991b1b;font-weight:700;text-transform:uppercase">Overdue Receipt</div>'
        f'<div style="font-size:26px;font-weight:900;color:#991b1b;line-height:1.1;margin-top:4px">{payload.get("overdue_receipt", 0)}</div></td>'
        '<td style="width:50%;padding:8px 10px;background:#f1f5f9;border:1px solid #e2e8f0;border-radius:0 4px 4px 0">'
        '<div style="font-family:Courier,monospace;font-size:10px;letter-spacing:0.18em;color:#334155;font-weight:700;text-transform:uppercase">Total Open</div>'
        f'<div style="font-size:26px;font-weight:900;color:#0f172a;line-height:1.1;margin-top:4px">{payload.get("total_open", 0)}</div></td>'
        '</tr></table>'
        '<h2 style="font-size:13px;margin:18px 0 6px;color:#0f172a;font-family:Courier,monospace;letter-spacing:0.18em;text-transform:uppercase">Status Breakdown</h2>'
        f'<table cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:4px">{rows}</table>'
        '<h2 style="font-size:13px;margin:18px 0 6px;color:#0f172a;font-family:Courier,monospace;letter-spacing:0.18em;text-transform:uppercase">Top Vendors &middot; Open POs</h2>'
        f'<table cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:4px">{vrows}</table>'
        f'{cta}'
        '<p style="margin:22px 0 0;font-size:11px;color:#94a3b8;line-height:1.5;border-top:1px solid #f1f5f9;padding-top:10px">'
        'MASCI Operations Platform &middot; Weekly Request PO Digest &middot; Mondays. '
        'Field Leadership submits the request; PM, Co-PMs, HR, and Admin issue the official PO.'
        '</p></div></div>'
    )


async def _active_pm_recipients(db) -> List[dict]:
    out: List[dict] = []
    cursor = db.project_managers.find(
        {"disabled": {"$in": [None, False]}},
        {"_id": 0, "id": 1, "name": 1, "email": 1},
    )
    async for d in cursor:
        em = (d.get("email") or "").strip().lower()
        if em and "@" in em:
            out.append({"id": d.get("id"), "name": d.get("name"), "email": em})
    return out


async def _active_hr_recipients(db) -> List[dict]:
    out: List[dict] = []
    cursor = db.hr_users.find(
        {"disabled": {"$in": [None, False]}, "is_active": {"$ne": False}},
        {"_id": 0, "id": 1, "name": 1, "email": 1},
    )
    async for d in cursor:
        em = (d.get("email") or "").strip().lower()
        if em and "@" in em:
            out.append({"id": d.get("id"), "name": d.get("name"), "email": em})
    return out


async def send_po_digest_once(
    db,
    send_email_fn: Optional[EmailFn],
    *,
    portal_url: str = "",
    dry_run: bool = False,
) -> dict:
    """Build + render + (optionally) send for every PM and HR user.

    Returns per-recipient summary so admin /preview endpoint + tests
    can verify exactly who got what without burning Resend quota.
    """
    results = {"pm": [], "hr": [], "subject": DIGEST_SUBJECT, "dry_run": dry_run}

    pms = await _active_pm_recipients(db)
    for pm in pms:
        try:
            payload = await build_pm_digest_payload(db, pm)
            html = render_po_digest_html(payload, portal_url=portal_url)
            sent = False
            if send_email_fn and not dry_run:
                try:
                    sent = bool(await send_email_fn(pm["email"], DIGEST_SUBJECT, html))
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"[po-digest] PM send failed for {pm['email']}: {e}")
                    sent = False
            results["pm"].append({
                "email": pm["email"], "name": pm.get("name"),
                "scoped_jobs": payload.get("scoped_to_jobs"),
                "total_open": payload.get("total_open"),
                "sent": sent,
            })
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[po-digest] PM build crashed for {pm.get('email')}: {e}")

    hrs = await _active_hr_recipients(db)
    for hr in hrs:
        try:
            payload = await build_hr_digest_payload(db, hr)
            html = render_po_digest_html(payload, portal_url=portal_url)
            sent = False
            if send_email_fn and not dry_run:
                try:
                    sent = bool(await send_email_fn(hr["email"], DIGEST_SUBJECT, html))
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"[po-digest] HR send failed for {hr['email']}: {e}")
                    sent = False
            results["hr"].append({
                "email": hr["email"], "name": hr.get("name"),
                "total_open": payload.get("total_open"),
                "sent": sent,
            })
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[po-digest] HR build crashed for {hr.get('email')}: {e}")

    return results


async def po_digest_scheduler_loop(
    db,
    send_email_fn: Optional[EmailFn],
    *,
    portal_url: str = "",
) -> None:
    """Long-running cron. Designed to never raise out. Single-fire-per-slot
    is guaranteed by the sleep-until-next-slot mechanic (same approach
    as iter120 safety_digest — no separate dedup table needed)."""
    while True:
        try:
            if not _enabled():
                await asyncio.sleep(3600)
                continue
            wait_s = _seconds_until_next_send()
            logger.info(f"[po-digest] sleeping {wait_s/3600:.1f}h until next send")
            await asyncio.sleep(max(60.0, wait_s))
            results = await send_po_digest_once(
                db, send_email_fn, portal_url=portal_url, dry_run=False
            )
            n_pm = sum(1 for r in results["pm"] if r.get("sent"))
            n_hr = sum(1 for r in results["hr"] if r.get("sent"))
            logger.info(
                f"[po-digest] sent. PMs={n_pm}/{len(results['pm'])} "
                f"HR={n_hr}/{len(results['hr'])}"
            )
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[po-digest] loop iteration crashed: {e}")
            await asyncio.sleep(600)
