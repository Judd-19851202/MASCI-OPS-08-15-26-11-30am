"""Phase 9B — Report Automation & Distribution.

Three persistent surfaces (each a single new collection following the
existing audit/snapshot pattern):
  • trench_safety_report_presets        — saved filter sets per user
  • trench_safety_report_subscriptions  — user → report → schedule
  • trench_safety_leadership_digests    — generated digest snapshots

Distribution uses the EXISTING certified Resend wrapper
(`server._trench_send_email`) and the EXISTING audit engine.

Public API:
  Presets:
    GET   /reports/presets
    POST  /reports/presets
    PUT   /reports/presets/{preset_id}
    DELETE /reports/presets/{preset_id}

  Subscriptions:
    GET   /reports/subscriptions
    POST  /reports/subscriptions
    PUT   /reports/subscriptions/{sub_id}
    DELETE /reports/subscriptions/{sub_id}
    POST  /reports/subscriptions/{sub_id}/run         (manual fire)
    POST  /reports/subscriptions/install-road-plate-package  (Road Plate Leadership Package seed)
    POST  /reports/subscriptions/run-due              (cron entrypoint — invoked by existing scheduler)

  Leadership Digest:
    POST  /reports/digest/generate?send=bool
    GET   /reports/digest/current
    GET   /reports/digest/history?limit=52
    GET   /reports/digest/{digest_id}
    GET   /reports/digest/{digest_id}/html
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from ._helpers import now_iso, write_audit
from .pulse import build_pulse_snapshot, _RATING_COLOR

# TRACK 27.03 · Phase 2b · Localise every operator-visible timestamp
# in trench-safety Leadership Digests + subscription-delivery emails.
from lib.platform_time import format_platform_stamp

logger = logging.getLogger(__name__)

PREFIX = "/trench-safety/reports"

VALID_REPORT_IDS = {
    "executive", "road-plate", "inspection-compliance", "repair-backlog",
    "holds", "utilization", "missing-data", "project-assets", "activity",
}

VALID_FORMATS = {"csv", "xlsx", "pdf"}
VALID_FREQUENCIES = {"weekly", "monthly"}


# ────────────────────────────────────────────────────────────────────────
# Pydantic payloads
# ────────────────────────────────────────────────────────────────────────

class PresetCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(min_length=1, max_length=80)
    report_id: str
    filters: Dict[str, Any] = Field(default_factory=dict)


class PresetUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class SubscriptionCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(min_length=1, max_length=80)
    report_id: str
    frequency: str = "weekly"
    format: str = "pdf"
    recipients: List[str] = Field(default_factory=list)
    filters: Dict[str, Any] = Field(default_factory=dict)
    preset_id: Optional[str] = None
    enabled: bool = True


class SubscriptionUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    frequency: Optional[str] = None
    format: Optional[str] = None
    recipients: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    preset_id: Optional[str] = None
    enabled: Optional[bool] = None


# ────────────────────────────────────────────────────────────────────────
# Leadership Digest renderer
# ────────────────────────────────────────────────────────────────────────

def render_leadership_digest_html(snapshot: Dict[str, Any]) -> str:
    """Pulse-style HTML focused on leadership headline metrics + links."""
    health = snapshot.get("health", {})
    score = health.get("score", 0)
    rating = health.get("rating", "—")
    rcolor, rbg = _RATING_COLOR.get(rating, ("#0f172a", "#f1f5f9"))
    rp = snapshot.get("road_plate_program", {})
    ih = snapshot.get("inspection_health", {})
    ra = snapshot.get("repair_activity", {})
    ha = snapshot.get("hold_activity", {})
    top_alerts = snapshot.get("top_alerts", [])
    week = snapshot.get("week_of", "")

    def _stat(label, value, color="#0f172a"):
        return (f'<tr><td style="padding:6px 0;color:#64748b;font-size:11px;letter-spacing:.08em;text-transform:uppercase;">{label}</td>'
                f'<td style="padding:6px 0;color:{color};font-size:15px;font-weight:700;text-align:right;font-family:Menlo,monospace;">{value}</td></tr>')

    risks_html = ""
    for a in top_alerts:
        risks_html += (
            f'<li style="margin:0 0 4px 0;color:#0f172a;font-size:13px;">'
            f'<b>{a["key"].replace("_"," ").title()}</b> · '
            f'<span style="color:#92400e;font-family:Menlo,monospace;font-weight:700;">{a["count"]}</span></li>'
        )
    if not risks_html:
        risks_html = '<li style="color:#10b981;font-size:13px;">No active risks.</li>'

    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a;">
<div style="max-width:640px;margin:0 auto;background:#ffffff;border:1px solid #e2e8f0;">
  <div style="background:#0e7490;color:white;padding:18px 22px;">
    <div style="font-size:11px;letter-spacing:.18em;text-transform:uppercase;opacity:.85;">MASCI · Leadership Digest</div>
    <h1 style="margin:6px 0 0;font-size:22px;letter-spacing:-.01em;">Trench Safety Leadership Digest</h1>
    <div style="font-size:13px;opacity:.85;margin-top:4px;">Week of {week}</div>
  </div>
  <div style="padding:18px 22px;">
    <div style="background:{rbg};border:1px solid {rcolor};border-radius:6px;padding:14px;">
      <div style="font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:{rcolor};font-weight:700;">Operational Health Score</div>
      <div style="font-size:42px;font-weight:900;color:{rcolor};line-height:1;margin-top:4px;">{score}<span style="font-size:18px;color:{rcolor};opacity:.7;"> / 100</span></div>
      <div style="font-size:15px;font-weight:700;color:{rcolor};margin-top:2px;">{rating}</div>
    </div>
    <h2 style="font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:#0e7490;margin:18px 0 6px;">Top 3 Risks</h2>
    <ul style="margin:0;padding:0 0 0 20px;">{risks_html}</ul>
    <h2 style="font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:#0e7490;margin:18px 0 6px;">Headline Metrics</h2>
    <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;">
      {_stat("Open Repairs", ra.get("open", 0), "#92400e" if ra.get("open",0)>0 else "#0f172a")}
      {_stat("Active Holds", ha.get("total_open", 0), "#991b1b" if ha.get("total_open",0)>0 else "#0f172a")}
      {_stat("Inspections Due", ih.get("inspections_due", 0), "#92400e" if ih.get("inspections_due",0)>0 else "#0f172a")}
      {_stat("Inspections Failed · 7d", ih.get("failed_7d", 0), "#991b1b" if ih.get("failed_7d",0)>0 else "#0f172a")}
      {_stat("Road Plates · On Hold", rp.get("on_hold", 0))}
      {_stat("Road Plates · Missing Capacity", rp.get("missing_capacity", 0))}
      {_stat("Asset Availability", snapshot.get("counts_by_status", {}).get("Available", 0), "#065f46")}
      {_stat("Recent Activity · 7d", snapshot.get("activity_7d_total", 0), "#0e7490")}
    </table>
    <h2 style="font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:#0e7490;margin:18px 0 6px;">Reports</h2>
    <p style="font-size:12px;color:#475569;margin:0 0 6px;">Drill in via the Safety Portal → Trench Safety → Reports.</p>
    <ul style="margin:0;padding:0 0 0 18px;font-size:12px;color:#0e7490;">
      <li>Executive Asset Health</li>
      <li>Road Plate Command</li>
      <li>Inspection Compliance</li>
      <li>Repair Backlog</li>
      <li>Hold Management</li>
    </ul>
    <div style="margin-top:24px;padding-top:12px;border-top:1px solid #e2e8f0;font-size:11px;color:#94a3b8;">
      Generated {format_platform_stamp(snapshot.get("generated_at",""))} · MASCI Trench Safety Operations System · Phase 9B
    </div>
  </div>
</div></body></html>"""


# ────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────

async def _resolve_default_recipients() -> List[str]:
    out: List[str] = []
    for em in (os.environ.get("SAFETY_DIGEST_TO_EMAIL", ""),
               os.environ.get("SUPER_ADMIN_EMAIL", "")):
        em = (em or "").strip()
        if em and em.lower() not in {x.lower() for x in out}:
            out.append(em)
    return out


def _validate_report(report_id: str) -> None:
    if report_id not in VALID_REPORT_IDS:
        raise HTTPException(400, f"Unknown report_id {report_id!r}")


def _validate_format(fmt: str) -> None:
    if fmt not in VALID_FORMATS:
        raise HTTPException(400, f"Unknown format {fmt!r}")


def _validate_frequency(freq: str) -> None:
    if freq not in VALID_FREQUENCIES:
        raise HTTPException(400, f"Unknown frequency {freq!r}")


async def _generate_and_email_report(
    db, *, report_id: str, fmt: str, filters: Dict[str, Any],
    recipients: List[str], subject_tail: str,
) -> Dict[str, Any]:
    """Generate a report payload, render the requested format, and ship
    via the existing _trench_send_email wrapper. Returns a delivery dict
    {status, recipient_count, errors}."""
    from .reports import _REPORT_REGISTRY, _flatten_for_csv, Filters as _F  # noqa: PLC0415
    from .report_export import render_xlsx, render_pdf  # noqa: PLC0415
    fn = _REPORT_REGISTRY.get(report_id)
    if not fn:
        return {"status": "unknown_report", "recipient_count": 0, "errors": ["report missing"]}
    flt_obj = _F(
        filters.get("date_from"), filters.get("date_to"),
        filters.get("asset_type"), filters.get("project_id"),
        filters.get("location"), filters.get("status"),
        filters.get("condition"),
    )
    payload = await fn(db, flt_obj)
    rows = _flatten_for_csv(report_id, payload)

    # Build attachment
    if fmt == "csv":
        import csv as _csv
        import io as _io  # noqa: PLC0415
        buf = _io.StringIO()
        w = _csv.writer(buf)
        for r in rows:
            w.writerow(r)
        attachment_bytes = buf.getvalue().encode("utf-8")
        ext = "csv"
        mime = "text/csv"
    elif fmt == "xlsx":
        attachment_bytes = render_xlsx(report_id, rows, "scheduled").getvalue()
        ext = "xlsx"
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:  # pdf
        attachment_bytes = render_pdf(report_id, rows, "scheduled", filters).getvalue()
        ext = "pdf"
        mime = "application/pdf"

    # Send via the existing wrapper. Most wrappers accept attachments
    # via a kw arg; we degrade gracefully if the wrapper signature is
    # tighter.
    delivery = {"status": "skipped", "recipient_count": 0, "errors": []}
    try:
        from server import _trench_send_email  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        delivery["errors"].append(f"import: {e}")
        return delivery

    subject = f"[MASCI · TRENCH SAFETY] {subject_tail}"
    body_html = (
        f"<p style='font-family:Arial,sans-serif;color:#0f172a;'>"
        f"Your scheduled Trench Safety report — <b>{report_id}</b> — is attached "
        f"as <code>{ext.upper()}</code>. Generated {format_platform_stamp(now_iso())}.</p>"
    )
    from lib.platform_time import resolve_tz as _rt  # noqa: PLC0415
    filename = f"trench_safety_{report_id}_{datetime.now(_rt()).strftime('%Y%m%d_%H%M')}.{ext}"

    sent = 0
    for r in recipients or []:
        try:
            # Attempt full-signature call first
            try:
                ok = await _trench_send_email(
                    r, subject, body_html,
                    attachments=[{"filename": filename, "content": attachment_bytes, "content_type": mime}],
                )
            except TypeError:
                ok = await _trench_send_email(r, subject, body_html)
            if ok:
                sent += 1
        except Exception as e:  # noqa: BLE001
            delivery["errors"].append(f"{r}: {e}")
    delivery["recipient_count"] = sent
    delivery["status"] = "sent" if sent else ("skipped" if recipients else "no_recipients")
    return delivery


def _next_due_at(last_run_at: Optional[str], frequency: str) -> str:
    base = datetime.now(timezone.utc)
    if last_run_at:
        try:
            base = datetime.fromisoformat(last_run_at.replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            pass
    delta = timedelta(days=7) if frequency == "weekly" else timedelta(days=30)
    return (base + delta).isoformat()


# ────────────────────────────────────────────────────────────────────────
# Route registration
# ────────────────────────────────────────────────────────────────────────

def register_distribution_routes(
    api_router: APIRouter,
    db,
    *,
    require_safety_or_admin,
) -> None:

    # ── Presets ─────────────────────────────────────────────────────
    @api_router.get(PREFIX + "/presets")
    async def list_presets(actor: dict = Depends(require_safety_or_admin)):
        email = (actor or {}).get("email") or "system"
        query = {"$or": [{"owner": email}, {"shared": True}]}
        items = await db.trench_safety_report_presets.find(
            query, {"_id": 0},
        ).sort("created_at", -1).to_list(200)
        total = await db.trench_safety_report_presets.count_documents(query)
        return {"items": items, "count": len(items), "total": total}

    @api_router.post(PREFIX + "/presets")
    async def create_preset(body: PresetCreate, actor: dict = Depends(require_safety_or_admin)):
        _validate_report(body.report_id)
        email = (actor or {}).get("email") or "system"
        doc = {
            "id": str(uuid.uuid4()),
            "owner": email,
            "name": body.name.strip(),
            "report_id": body.report_id,
            "filters": dict(body.filters or {}),
            "shared": False,
            "created_at": now_iso(),
            "last_used_at": None,
        }
        await db.trench_safety_report_presets.insert_one(doc)
        doc.pop("_id", None)
        await write_audit(db, kind="trench_report_preset_created",
                          asset_id="(preset)", actor=actor,
                          detail={"preset_id": doc["id"], "report_id": body.report_id, "name": body.name})
        return doc

    @api_router.put(PREFIX + "/presets/{preset_id}")
    async def update_preset(preset_id: str, body: PresetUpdate, actor: dict = Depends(require_safety_or_admin)):
        existing = await db.trench_safety_report_presets.find_one({"id": preset_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Preset not found")
        patch: Dict[str, Any] = {"updated_at": now_iso()}
        if body.name is not None:
            patch["name"] = body.name.strip()
        if body.filters is not None:
            patch["filters"] = dict(body.filters)
        await db.trench_safety_report_presets.update_one({"id": preset_id}, {"$set": patch})
        await write_audit(db, kind="trench_report_preset_updated",
                          asset_id="(preset)", actor=actor,
                          detail={"preset_id": preset_id, "patch_keys": list(patch.keys())})
        doc = await db.trench_safety_report_presets.find_one({"id": preset_id}, {"_id": 0})
        return doc

    @api_router.delete(PREFIX + "/presets/{preset_id}")
    async def delete_preset(preset_id: str, actor: dict = Depends(require_safety_or_admin)):
        r = await db.trench_safety_report_presets.delete_one({"id": preset_id})
        if r.deleted_count == 0:
            raise HTTPException(404, "Preset not found")
        await write_audit(db, kind="trench_report_preset_deleted",
                          asset_id="(preset)", actor=actor,
                          detail={"preset_id": preset_id})
        return {"ok": True, "deleted": preset_id}

    # ── Subscriptions ───────────────────────────────────────────────
    @api_router.get(PREFIX + "/subscriptions")
    async def list_subscriptions(actor: dict = Depends(require_safety_or_admin)):
        items = await db.trench_safety_report_subscriptions.find(
            {}, {"_id": 0},
        ).sort("created_at", -1).to_list(500)
        total = await db.trench_safety_report_subscriptions.count_documents({})
        return {"items": items, "count": len(items), "total": total}

    @api_router.post(PREFIX + "/subscriptions")
    async def create_subscription(body: SubscriptionCreate, actor: dict = Depends(require_safety_or_admin)):
        _validate_report(body.report_id)
        _validate_format(body.format)
        _validate_frequency(body.frequency)
        email = (actor or {}).get("email") or "system"
        recipients = body.recipients or await _resolve_default_recipients()
        doc = {
            "id": str(uuid.uuid4()),
            "owner": email,
            "name": body.name.strip(),
            "report_id": body.report_id,
            "frequency": body.frequency,
            "format": body.format,
            "recipients": list(recipients),
            "filters": dict(body.filters or {}),
            "preset_id": body.preset_id,
            "enabled": bool(body.enabled),
            "created_at": now_iso(),
            "last_run_at": None,
            "last_status": None,
            "next_due_at": _next_due_at(None, body.frequency),
        }
        await db.trench_safety_report_subscriptions.insert_one(doc)
        doc.pop("_id", None)
        await write_audit(db, kind="trench_report_subscription_created",
                          asset_id="(subscription)", actor=actor,
                          detail={"sub_id": doc["id"], "report_id": body.report_id,
                                   "frequency": body.frequency, "format": body.format,
                                   "recipient_count": len(doc["recipients"])})
        return doc

    @api_router.put(PREFIX + "/subscriptions/{sub_id}")
    async def update_subscription(sub_id: str, body: SubscriptionUpdate, actor: dict = Depends(require_safety_or_admin)):
        existing = await db.trench_safety_report_subscriptions.find_one({"id": sub_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Subscription not found")
        patch: Dict[str, Any] = {"updated_at": now_iso()}
        if body.name is not None:
            patch["name"] = body.name.strip()
        if body.frequency is not None:
            _validate_frequency(body.frequency)
            patch["frequency"] = body.frequency
            patch["next_due_at"] = _next_due_at(existing.get("last_run_at"), body.frequency)
        if body.format is not None:
            _validate_format(body.format)
            patch["format"] = body.format
        if body.recipients is not None:
            patch["recipients"] = list(body.recipients)
        if body.filters is not None:
            patch["filters"] = dict(body.filters)
        if body.preset_id is not None:
            patch["preset_id"] = body.preset_id
        if body.enabled is not None:
            patch["enabled"] = bool(body.enabled)
        await db.trench_safety_report_subscriptions.update_one({"id": sub_id}, {"$set": patch})
        await write_audit(db, kind="trench_report_subscription_updated",
                          asset_id="(subscription)", actor=actor,
                          detail={"sub_id": sub_id, "patch_keys": list(patch.keys())})
        return await db.trench_safety_report_subscriptions.find_one({"id": sub_id}, {"_id": 0})

    @api_router.delete(PREFIX + "/subscriptions/{sub_id}")
    async def delete_subscription(sub_id: str, actor: dict = Depends(require_safety_or_admin)):
        r = await db.trench_safety_report_subscriptions.delete_one({"id": sub_id})
        if r.deleted_count == 0:
            raise HTTPException(404, "Subscription not found")
        await write_audit(db, kind="trench_report_subscription_deleted",
                          asset_id="(subscription)", actor=actor,
                          detail={"sub_id": sub_id})
        return {"ok": True, "deleted": sub_id}

    @api_router.post(PREFIX + "/subscriptions/{sub_id}/run")
    async def run_subscription(sub_id: str, actor: dict = Depends(require_safety_or_admin)):
        sub = await db.trench_safety_report_subscriptions.find_one({"id": sub_id}, {"_id": 0})
        if not sub:
            raise HTTPException(404, "Subscription not found")
        delivery = await _generate_and_email_report(
            db,
            report_id=sub["report_id"], fmt=sub["format"], filters=sub.get("filters") or {},
            recipients=sub.get("recipients") or [],
            subject_tail=f"{sub['name']} · {sub['report_id']}",
        )
        await db.trench_safety_report_subscriptions.update_one(
            {"id": sub_id},
            {"$set": {
                "last_run_at": now_iso(),
                "last_status": delivery["status"],
                "next_due_at": _next_due_at(now_iso(), sub.get("frequency") or "weekly"),
            }},
        )
        await write_audit(
            db,
            kind="trench_report_subscription_run" if delivery["status"] == "sent"
                else "trench_report_subscription_run_failed",
            asset_id="(subscription)", actor=actor,
            detail={"sub_id": sub_id, "delivery": delivery},
        )
        return {"subscription_id": sub_id, "delivery": delivery}

    @api_router.post(PREFIX + "/subscriptions/install-road-plate-package")
    async def install_road_plate_package(actor: dict = Depends(require_safety_or_admin)):
        """Phase 9B Feature 10 — Road Plate Leadership Package.

        Installs four weekly PDF subscriptions filtered to Road Plate
        (or scoped to road-plate-relevant data) for Safety/Shop/Ops
        leadership. Idempotent — if any subscription with the same
        package name already exists, it is left alone.
        """
        email = (actor or {}).get("email") or "system"
        recipients = await _resolve_default_recipients()
        package = [
            {"name": "Road Plate Leadership · Command",      "report_id": "road-plate",   "filters": {}},
            {"name": "Road Plate Leadership · Missing Data", "report_id": "missing-data", "filters": {"asset_type": "Road Plate"}},
            {"name": "Road Plate Leadership · Repairs",      "report_id": "repair-backlog","filters": {"asset_type": "Road Plate"}},
            {"name": "Road Plate Leadership · Holds",        "report_id": "holds",        "filters": {"asset_type": "Road Plate"}},
        ]
        created = []
        skipped = []
        for spec in package:
            exists = await db.trench_safety_report_subscriptions.find_one(
                {"name": spec["name"]}, {"_id": 0, "id": 1},
            )
            if exists:
                skipped.append(exists["id"])
                continue
            doc = {
                "id": str(uuid.uuid4()),
                "owner": email,
                "name": spec["name"],
                "report_id": spec["report_id"],
                "frequency": "weekly",
                "format": "pdf",
                "recipients": list(recipients),
                "filters": spec["filters"],
                "preset_id": None,
                "enabled": True,
                "created_at": now_iso(),
                "last_run_at": None,
                "last_status": None,
                "next_due_at": _next_due_at(None, "weekly"),
                "package": "road_plate_leadership",
            }
            await db.trench_safety_report_subscriptions.insert_one(doc)
            doc.pop("_id", None)
            created.append(doc)
        await write_audit(db, kind="trench_report_package_installed",
                          asset_id="(subscription)", actor=actor,
                          detail={"package": "road_plate_leadership",
                                   "created_count": len(created),
                                   "skipped_count": len(skipped)})
        return {"created": created, "created_count": len(created),
                "skipped": skipped, "skipped_count": len(skipped)}

    @api_router.post(PREFIX + "/subscriptions/run-due")
    async def run_due(actor: dict = Depends(require_safety_or_admin)):
        """Phase 9B Feature 6 — manual cron entrypoint. Iterates every
        enabled subscription whose `next_due_at` <= now and ships the
        report. Designed to be invoked by the existing weekly cron in
        server.py with one extra line; held per OMEGA STOP."""
        now = datetime.now(timezone.utc).isoformat()
        subs = await db.trench_safety_report_subscriptions.find(
            {"enabled": True, "next_due_at": {"$lte": now}},
            {"_id": 0},
        ).to_list(500)
        results = []
        for sub in subs:
            delivery = await _generate_and_email_report(
                db, report_id=sub["report_id"], fmt=sub["format"],
                filters=sub.get("filters") or {},
                recipients=sub.get("recipients") or [],
                subject_tail=f"{sub['name']} · {sub['report_id']}",
            )
            await db.trench_safety_report_subscriptions.update_one(
                {"id": sub["id"]},
                {"$set": {
                    "last_run_at": now_iso(),
                    "last_status": delivery["status"],
                    "next_due_at": _next_due_at(now_iso(), sub.get("frequency") or "weekly"),
                }},
            )
            results.append({"sub_id": sub["id"], "delivery": delivery})
        await write_audit(db, kind="trench_report_cron_ran",
                          asset_id="(subscription)", actor=actor,
                          detail={"processed_count": len(results)})
        return {"processed": results, "count": len(results)}

    # ── Leadership Digest ───────────────────────────────────────────
    @api_router.post(PREFIX + "/digest/generate")
    async def generate_digest(
        send: bool = Query(default=False),
        actor: dict = Depends(require_safety_or_admin),
    ):
        snapshot = await build_pulse_snapshot(db)
        html = render_leadership_digest_html(snapshot)
        digest_id = str(uuid.uuid4())
        subject = f"MASCI Leadership Digest — Week of {snapshot['week_of']}"
        recipients = await _resolve_default_recipients()
        delivery = {"status": "not_sent", "recipient_count": 0, "errors": []}
        if send:
            try:
                from server import _trench_send_email  # noqa: PLC0415
            except Exception as e:  # noqa: BLE001
                _trench_send_email = None
                delivery["errors"].append(f"import: {e}")
            if _trench_send_email and recipients:
                sent = 0
                for r in recipients:
                    try:
                        ok = await _trench_send_email(r, subject, html)
                        if ok:
                            sent += 1
                    except Exception as e:  # noqa: BLE001
                        delivery["errors"].append(f"{r}: {e}")
                delivery["recipient_count"] = sent
                delivery["status"] = "sent" if sent else "skipped"
            elif not recipients:
                delivery["status"] = "no_recipients"
            else:
                delivery["status"] = "email_disabled"
        doc = {
            "id": digest_id,
            "generated_at": snapshot["generated_at"],
            "week_of": snapshot["week_of"],
            "generated_by": (actor or {}).get("email") or "system",
            "subject": subject,
            "snapshot": snapshot,
            "delivery": delivery,
            "score": snapshot["health"]["score"],
            "rating": snapshot["health"]["rating"],
        }
        await db.trench_safety_leadership_digests.insert_one(doc)
        doc.pop("_id", None)
        await write_audit(db, kind="trench_leadership_digest_generated",
                          asset_id="(digest)", actor=actor,
                          detail={"digest_id": digest_id, "send": send,
                                   "delivery_status": delivery["status"],
                                   "recipient_count": delivery["recipient_count"],
                                   "score": doc["score"], "rating": doc["rating"]})
        return doc

    @api_router.get(PREFIX + "/digest/current")
    async def digest_current(_actor: dict = Depends(require_safety_or_admin)):
        latest = await db.trench_safety_leadership_digests.find_one({}, {"_id": 0}, sort=[("generated_at", -1)])
        if latest:
            return latest
        snapshot = await build_pulse_snapshot(db)
        return {
            "id": None, "generated_at": snapshot["generated_at"],
            "week_of": snapshot["week_of"], "snapshot": snapshot,
            "score": snapshot["health"]["score"],
            "rating": snapshot["health"]["rating"],
            "delivery": {"status": "live_preview", "recipient_count": 0},
            "subject": f"MASCI Leadership Digest — Week of {snapshot['week_of']}",
            "generated_by": "live",
        }

    @api_router.get(PREFIX + "/digest/history")
    async def digest_history(
        limit: int = Query(default=52, ge=1, le=200),
        _actor: dict = Depends(require_safety_or_admin),
    ):
        items = await db.trench_safety_leadership_digests.find(
            {}, {"_id": 0, "snapshot": 0},
        ).sort("generated_at", -1).limit(limit).to_list(limit)
        return {"items": items, "count": len(items),
                "total": await db.trench_safety_leadership_digests.count_documents({})}

    @api_router.get(PREFIX + "/digest/{digest_id}")
    async def digest_detail(digest_id: str, _actor: dict = Depends(require_safety_or_admin)):
        doc = await db.trench_safety_leadership_digests.find_one({"id": digest_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Digest not found")
        return doc

    @api_router.get(PREFIX + "/digest/{digest_id}/html")
    async def digest_html(digest_id: str, _actor: dict = Depends(require_safety_or_admin)):
        from fastapi.responses import HTMLResponse  # noqa: PLC0415
        doc = await db.trench_safety_leadership_digests.find_one({"id": digest_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Digest not found")
        return HTMLResponse(render_leadership_digest_html(doc.get("snapshot", {})))
