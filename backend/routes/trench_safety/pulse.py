"""Phase 8C — Trench Safety Pulse · Operational Intelligence briefing.

A weekly leadership briefing built ENTIRELY on existing certified
infrastructure:
  • Data source: `trench_safety_assets` + `trench_safety_holds`
    + `trench_safety_repairs` + `trench_safety_inspections`
    + `audit_events` (read-only)
  • Email delivery: `_trench_send_email` (Phase 7.5C, server.py)
  • Bell delivery: `lib.event_fanout.emit_notification`
  • Storage: single new collection `trench_safety_pulses` (history;
    matches the existing audit/snapshot pattern — no analytics db,
    no reporting engine)

Public API:
  • POST /trench-safety/pulse/generate?send=bool  (admin/safety)
  • GET  /trench-safety/pulse/current             (any portal — last 7d snapshot, generated on the fly if none)
  • GET  /trench-safety/pulse/history?limit=52    (any portal)
  • GET  /trench-safety/pulse/{pulse_id}          (any portal)

NO new scheduler — pulse is generated on demand (and from the existing
weekly cron when the operator authorises). NO new email engine.
"""
from __future__ import annotations

import logging
import os
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ._helpers import now_iso, write_audit
from ._models import ASSET_TYPES, OPERATIONAL_STATUSES

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────
# Operational Health Score · deterministic, explainable
# ────────────────────────────────────────────────────────────────────────

def compute_operational_health_score(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Return {score:int 0-100, rating, breakdown}.

    Deterministic weights — NOT AI. Every input is auditable.
    """
    total = max(snapshot.get("total_active_assets", 0), 1)
    al = snapshot.get("alerts", {})

    # Components (each 0-100, then weighted)
    overdue = al.get("inspections_due", 0)
    inspection_score = max(0, 100 - int(100 * overdue / total))

    on_hold = al.get("on_hold", 0)
    hold_score = max(0, 100 - int(100 * on_hold / total))

    open_repairs = al.get("open_repairs", 0)
    repair_score = max(0, 100 - int(100 * open_repairs / total))

    missing_critical = (
        al.get("missing_serial_number", 0)
        + al.get("road_plate_missing_capacity", 0)
        + al.get("missing_tabulated_data", 0)
    )
    data_score = max(0, 100 - int(50 * missing_critical / total))

    cs = snapshot.get("counts_by_status", {})
    availability = cs.get("Available", 0)
    avail_score = min(100, int(100 * availability / total))

    weights = {
        "inspection_compliance": (inspection_score, 0.30),
        "hold_health":           (hold_score,       0.25),
        "repair_backlog":        (repair_score,     0.20),
        "missing_critical_data": (data_score,       0.15),
        "availability":          (avail_score,      0.10),
    }
    score = int(round(sum(v[0] * v[1] for v in weights.values())))
    if score >= 90:
        rating = "Excellent"
    elif score >= 75:
        rating = "Good"
    elif score >= 60:
        rating = "Needs Attention"
    else:
        rating = "Critical"
    return {
        "score": score,
        "rating": rating,
        "breakdown": {k: {"score": v[0], "weight": v[1]} for k, v in weights.items()},
    }


# ────────────────────────────────────────────────────────────────────────
# Snapshot builder · single read pass · zero writes
# ────────────────────────────────────────────────────────────────────────

async def build_pulse_snapshot(db) -> Dict[str, Any]:
    """Gather the full 8-section snapshot used by the pulse email and
    the Hub Pulse Card. Single-query reads against existing
    collections — never writes."""
    docs: List[Dict[str, Any]] = await db.trench_safety_assets.find(
        {}, {"_id": 0}
    ).to_list(5000)

    counts_by_type = {t: 0 for t in ASSET_TYPES}
    counts_by_status = {s: 0 for s in OPERATIONAL_STATUSES}
    active = 0
    missing_serial = 0
    missing_manufacturer = 0
    missing_tabulated = 0
    no_project = 0
    on_hold = 0
    rp_missing_capacity = 0

    for d in docs:
        t = d.get("asset_type") or "Trench Box"
        s = d.get("operational_status") or "Available"
        counts_by_type[t] = counts_by_type.get(t, 0) + 1
        counts_by_status[s] = counts_by_status.get(s, 0) + 1
        if d.get("is_active"):
            active += 1
            if d.get("missing_serial_number"):
                missing_serial += 1
            if d.get("missing_manufacturer"):
                missing_manufacturer += 1
            if d.get("tabulated_data_missing"):
                missing_tabulated += 1
            if not d.get("current_project_id") and not d.get("current_project_name"):
                no_project += 1
            if s in {"Inspection Hold", "Maintenance Hold", "Safety Hold", "Certification Hold"}:
                on_hold += 1
            if d.get("asset_type") == "Road Plate" and not d.get("rated_capacity_lb"):
                rp_missing_capacity += 1

    # Inspection health — overdue vs ever-recorded
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    inspections_due = sum(
        1 for d in docs
        if d.get("is_active")
        and (not d.get("last_inspection_at") or d["last_inspection_at"] < cutoff)
    )
    missing_inspection = sum(
        1 for d in docs if d.get("is_active") and not d.get("last_inspection_at")
    )

    # Inspections in the last 7 days
    seven = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    inspections_completed_7d = await db.trench_safety_inspections.count_documents(
        {"submitted_at": {"$gte": seven}}
    )
    inspections_failed_7d = await db.trench_safety_inspections.count_documents(
        {"submitted_at": {"$gte": seven}, "result": "Fail"}
    )

    # Holds — open + top 5 by days_on_hold
    open_holds = await db.trench_safety_holds.find(
        {"is_active": True}, {"_id": 0}
    ).to_list(2000)
    hold_counts = Counter(h.get("kind") for h in open_holds)
    now_dt = datetime.now(timezone.utc)
    def _days_on_hold(h):
        try:
            opened = datetime.fromisoformat((h.get("opened_at") or "").replace("Z", "+00:00"))
            return max(0, (now_dt - opened).days)
        except Exception:  # noqa: BLE001
            return 0
    enriched_holds = []
    by_asset = {d["asset_id"]: d for d in docs}
    for h in open_holds:
        a = by_asset.get(h.get("asset_id"), {})
        enriched_holds.append({
            "asset_id": h.get("asset_id"),
            "asset_type": a.get("asset_type"),
            "kind": h.get("kind"),
            "reason": h.get("reason"),
            "days_on_hold": _days_on_hold(h),
            "opened_at": h.get("opened_at"),
        })
    enriched_holds.sort(key=lambda x: -x["days_on_hold"])
    top_holds = enriched_holds[:5]

    # Repairs
    open_repairs = await db.trench_safety_repairs.count_documents(
        {"status": {"$in": ["Open", "In Progress", "Waiting on Parts", "Vendor Repair"]}}
    )
    repairs_completed_7d = await db.trench_safety_repairs.count_documents(
        {"status": {"$in": ["Completed", "Closed After Verification"]},
         "closed_at": {"$gte": seven}}
    )
    awaiting_verification = await db.trench_safety_repairs.count_documents(
        {"status": "Completed"}
    )

    # Road Plate sub-program
    rp_docs = [d for d in docs if d.get("asset_type") == "Road Plate" and d.get("is_active")]
    rp_status = Counter(d.get("operational_status") or "Available" for d in rp_docs)
    rp_missing_inspection = sum(
        1 for d in rp_docs if not d.get("last_inspection_at")
    )

    # Activity (last 7d)
    activity_kinds = [
        "trench_asset_created", "trench_asset_edited", "trench_asset_retired",
        "trench_asset_status_changed",
        "trench_asset_inspection_submitted", "trench_asset_inspection_passed",
        "trench_asset_inspection_failed",
        "trench_asset_hold_opened", "trench_asset_hold_cleared",
        "trench_asset_repair_updated", "trench_asset_repair_verified",
        "trench_safety_transport_started", "trench_safety_transport_completed",
        "trench_safety_transport_cancelled",
    ]
    activity = await db.audit_events.aggregate([
        {"$match": {"kind": {"$in": activity_kinds}, "ts": {"$gte": seven}}},
        {"$group": {"_id": "$kind", "n": {"$sum": 1}}},
    ]).to_list(50)
    activity_by_kind = {a["_id"]: a["n"] for a in activity}

    alerts = {
        "missing_serial_number": missing_serial,
        "missing_manufacturer": missing_manufacturer,
        "missing_tabulated_data": missing_tabulated,
        "open_repairs": open_repairs,
        "inspections_due": inspections_due,
        "on_hold": on_hold,
        "no_project_assignment": no_project,
        "road_plate_missing_capacity": rp_missing_capacity,
    }

    snapshot: Dict[str, Any] = {
        "generated_at": now_iso(),
        "week_of": (datetime.now(timezone.utc).date()).isoformat(),
        "total_assets": len(docs),
        "total_active_assets": active,
        "counts_by_status": counts_by_status,
        "counts_by_type": counts_by_type,
        "inspection_health": {
            "inspections_due": inspections_due,
            "missing_inspection": missing_inspection,
            "completed_7d": inspections_completed_7d,
            "failed_7d": inspections_failed_7d,
        },
        "hold_activity": {
            "counts": dict(hold_counts),
            "top_assets_on_hold": top_holds,
            "total_open": len(open_holds),
        },
        "repair_activity": {
            "open": open_repairs,
            "completed_7d": repairs_completed_7d,
            "awaiting_verification": awaiting_verification,
        },
        "road_plate_program": {
            "total": len(rp_docs),
            "available": rp_status.get("Available", 0),
            "assigned": rp_status.get("Assigned", 0),
            "on_hold": sum(rp_status.get(k, 0) for k in (
                "Inspection Hold", "Maintenance Hold",
                "Safety Hold", "Certification Hold",
            )),
            "missing_capacity": rp_missing_capacity,
            "missing_inspection": rp_missing_inspection,
        },
        "alerts": alerts,
        "activity_7d": activity_by_kind,
        "activity_7d_total": sum(activity_by_kind.values()),
    }
    snapshot["health"] = compute_operational_health_score(snapshot)
    # Top 3 alert categories for the email
    top_alerts = sorted(
        [{"key": k, "count": v} for k, v in alerts.items() if v > 0],
        key=lambda x: -x["count"],
    )[:3]
    snapshot["top_alerts"] = top_alerts
    return snapshot


# ────────────────────────────────────────────────────────────────────────
# HTML email renderer · mobile-first inline styles
# ────────────────────────────────────────────────────────────────────────

_RATING_COLOR = {
    "Excellent":       ("#065f46", "#d1fae5"),
    "Good":            ("#1e40af", "#dbeafe"),
    "Needs Attention": ("#92400e", "#fef3c7"),
    "Critical":        ("#991b1b", "#fee2e2"),
}


def _kv_table(rows: List[tuple]) -> str:
    out = ['<table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;">']
    for label, value, *rest in rows:
        color = rest[0] if rest else "#0f172a"
        out.append(
            f'<tr><td style="padding:6px 0;color:#64748b;font-size:12px;letter-spacing:.06em;text-transform:uppercase;">{label}</td>'
            f'<td style="padding:6px 0;color:{color};font-size:16px;font-weight:700;text-align:right;font-family:Menlo,monospace;">{value}</td></tr>'
        )
    out.append("</table>")
    return "".join(out)


def render_pulse_email(snapshot: Dict[str, Any]) -> str:
    week = snapshot.get("week_of", "")
    health = snapshot.get("health", {})
    score = health.get("score", 0)
    rating = health.get("rating", "—")
    rcolor, rbg = _RATING_COLOR.get(rating, ("#0f172a", "#f1f5f9"))

    ih = snapshot.get("inspection_health", {})
    ha = snapshot.get("hold_activity", {})
    ra = snapshot.get("repair_activity", {})
    rp = snapshot.get("road_plate_program", {})
    al = snapshot.get("alerts", {})
    cs = snapshot.get("counts_by_status", {})
    ct = snapshot.get("counts_by_type", {})
    activity = snapshot.get("activity_7d", {})

    top_holds_html = ""
    for h in ha.get("top_assets_on_hold", []) or []:
        days = h.get("days_on_hold", 0)
        sev = "#991b1b" if days >= 14 else ("#92400e" if days >= 3 else "#1e293b")
        top_holds_html += (
            f'<tr><td style="padding:6px 8px;font-family:Menlo,monospace;font-weight:700;color:#0f172a;">{h.get("asset_id","")}</td>'
            f'<td style="padding:6px 8px;font-size:13px;color:#475569;">{h.get("asset_type","")}</td>'
            f'<td style="padding:6px 8px;font-size:13px;color:#0f172a;">{(h.get("kind") or "").replace(" Hold","")}</td>'
            f'<td style="padding:6px 8px;font-size:13px;color:#475569;">{(h.get("reason","") or "")[:80]}</td>'
            f'<td style="padding:6px 8px;font-family:Menlo,monospace;font-weight:700;color:{sev};text-align:right;">{days}d</td></tr>'
        )
    if not top_holds_html:
        top_holds_html = (
            '<tr><td colspan="5" style="padding:10px;text-align:center;color:#10b981;font-size:13px;">'
            'No assets currently on hold — clean.</td></tr>'
        )

    top_alerts_html = ""
    for a in snapshot.get("top_alerts", []):
        top_alerts_html += (
            f'<tr><td style="padding:4px 6px;font-size:13px;color:#0f172a;">{a["key"].replace("_"," ").title()}</td>'
            f'<td style="padding:4px 6px;font-family:Menlo,monospace;font-weight:700;color:#92400e;text-align:right;">{a["count"]}</td></tr>'
        )
    if not top_alerts_html:
        top_alerts_html = '<tr><td colspan="2" style="padding:8px;color:#10b981;">Nothing to flag.</td></tr>'

    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a;">
<div style="max-width:640px;margin:0 auto;background:#ffffff;border:1px solid #e2e8f0;">
  <div style="background:#0e7490;color:white;padding:18px 22px;">
    <div style="font-size:11px;letter-spacing:.18em;text-transform:uppercase;opacity:.85;">MASCI · Operational Intelligence</div>
    <h1 style="margin:6px 0 0;font-size:22px;letter-spacing:-.01em;">Trench Safety Pulse</h1>
    <div style="font-size:13px;opacity:.85;margin-top:4px;">Week of {week}</div>
  </div>

  <div style="padding:18px 22px;">
    <div style="background:{rbg};border:1px solid {rcolor};border-radius:6px;padding:14px;">
      <div style="font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:{rcolor};font-weight:700;">Operational Health Score</div>
      <div style="font-size:42px;font-weight:900;color:{rcolor};line-height:1;margin-top:4px;">{score}<span style="font-size:18px;color:{rcolor};opacity:.7;"> / 100</span></div>
      <div style="font-size:15px;font-weight:700;color:{rcolor};margin-top:2px;">{rating}</div>
    </div>

    <h2 style="font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:#0e7490;margin:18px 0 6px;">1 · Fleet Overview</h2>
    {_kv_table([
      ("Total Assets",      snapshot.get("total_active_assets", 0)),
      ("Available",         cs.get("Available", 0),        "#065f46"),
      ("Assigned",          cs.get("Assigned", 0),         "#1e40af"),
      ("In Transport",      cs.get("In Transport", 0),     "#0e7490"),
      ("On Hold (any)",     al.get("on_hold", 0),          "#991b1b" if al.get("on_hold",0)>0 else "#0f172a"),
      ("Retired",           cs.get("Retired", 0),          "#64748b"),
    ])}

    <h2 style="font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:#0e7490;margin:18px 0 6px;">2 · Asset Type Breakdown</h2>
    {_kv_table([(t, ct.get(t, 0)) for t in ASSET_TYPES])}

    <h2 style="font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:#0e7490;margin:18px 0 6px;">3 · Inspection Health</h2>
    {_kv_table([
      ("Inspections Due",       ih.get("inspections_due", 0),    "#92400e" if ih.get("inspections_due",0)>0 else "#0f172a"),
      ("Missing Inspection",    ih.get("missing_inspection", 0), "#92400e" if ih.get("missing_inspection",0)>0 else "#0f172a"),
      ("Completed (7d)",        ih.get("completed_7d", 0),       "#065f46"),
      ("Failed (7d)",           ih.get("failed_7d", 0),          "#991b1b" if ih.get("failed_7d",0)>0 else "#0f172a"),
    ])}

    <h2 style="font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:#0e7490;margin:18px 0 6px;">4 · Hold Activity</h2>
    {_kv_table([
      ("Safety Holds",      (ha.get("counts") or {}).get("Safety Hold", 0),       "#991b1b"),
      ("Inspection Holds",  (ha.get("counts") or {}).get("Inspection Hold", 0),   "#92400e"),
      ("Maintenance Holds", (ha.get("counts") or {}).get("Maintenance Hold", 0),  "#9a3412"),
      ("Cert Holds",        (ha.get("counts") or {}).get("Certification Hold",0), "#6b21a8"),
    ])}
    <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;margin-top:6px;border-top:1px solid #e2e8f0;">
      <thead><tr style="background:#f8fafc;">
        <th style="text-align:left;padding:6px 8px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#64748b;">Asset</th>
        <th style="text-align:left;padding:6px 8px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#64748b;">Type</th>
        <th style="text-align:left;padding:6px 8px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#64748b;">Hold</th>
        <th style="text-align:left;padding:6px 8px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#64748b;">Reason</th>
        <th style="text-align:right;padding:6px 8px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#64748b;">Days</th>
      </tr></thead>
      <tbody>{top_holds_html}</tbody>
    </table>

    <h2 style="font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:#0e7490;margin:18px 0 6px;">5 · Repair Activity</h2>
    {_kv_table([
      ("Open Repairs",            ra.get("open", 0),                  "#92400e" if ra.get("open",0)>0 else "#0f172a"),
      ("Completed (7d)",          ra.get("completed_7d", 0),          "#065f46"),
      ("Awaiting Verification",   ra.get("awaiting_verification", 0), "#92400e" if ra.get("awaiting_verification",0)>0 else "#0f172a"),
    ])}
    <div style="margin-top:6px;font-size:11px;color:#64748b;font-style:italic;">Repair Complete ≠ Safe To Use. Verification by Safety required.</div>

    <h2 style="font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:#0e7490;margin:18px 0 6px;">6 · Road Plate Program</h2>
    {_kv_table([
      ("Total Road Plates",       rp.get("total", 0)),
      ("Available",               rp.get("available", 0), "#065f46"),
      ("Assigned",                rp.get("assigned", 0),  "#1e40af"),
      ("On Hold",                 rp.get("on_hold", 0),   "#991b1b" if rp.get("on_hold",0)>0 else "#0f172a"),
      ("Missing Capacity Data",   rp.get("missing_capacity", 0), "#92400e" if rp.get("missing_capacity",0)>0 else "#0f172a"),
      ("Missing Inspection",      rp.get("missing_inspection", 0), "#92400e" if rp.get("missing_inspection",0)>0 else "#0f172a"),
    ])}

    <h2 style="font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:#0e7490;margin:18px 0 6px;">7 · Top 3 Operational Alerts</h2>
    <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;">{top_alerts_html}</table>

    <h2 style="font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:#0e7490;margin:18px 0 6px;">8 · Activity Summary · Last 7 Days</h2>
    {_kv_table([
      ("Assets Created",         activity.get("trench_asset_created", 0)),
      ("Assets Edited",          activity.get("trench_asset_edited", 0)),
      ("Status Changes",         activity.get("trench_asset_status_changed", 0)),
      ("Inspections Submitted",  activity.get("trench_asset_inspection_submitted", 0)
                                   + activity.get("trench_asset_inspection_passed", 0)
                                   + activity.get("trench_asset_inspection_failed", 0)),
      ("Holds Opened",           activity.get("trench_asset_hold_opened", 0)),
      ("Holds Cleared",          activity.get("trench_asset_hold_cleared", 0)),
      ("Repair Updates",         activity.get("trench_asset_repair_updated", 0)),
      ("Repair Verifications",   activity.get("trench_asset_repair_verified", 0)),
    ])}

    <div style="margin-top:24px;padding-top:12px;border-top:1px solid #e2e8f0;font-size:11px;color:#94a3b8;">
      Generated {snapshot.get("generated_at","").replace("T"," ")[:19]} UTC · MASCI Trench Safety Operations System · Phase 8C Operational Intelligence
    </div>
  </div>
</div></body></html>"""


# ────────────────────────────────────────────────────────────────────────
# Route registration
# ────────────────────────────────────────────────────────────────────────

def register_pulse_routes(
    api_router: APIRouter,
    db,
    *,
    require_safety_or_admin,
    require_any_portal,
) -> None:
    PREFIX = "/trench-safety/pulse"

    async def _resolve_recipients() -> List[str]:
        env_targets = [
            os.environ.get("SAFETY_DIGEST_TO_EMAIL", ""),
            os.environ.get("SUPER_ADMIN_EMAIL", ""),
        ]
        out: List[str] = []
        for em in env_targets:
            em = (em or "").strip()
            if em and em.lower() not in {x.lower() for x in out}:
                out.append(em)
        return out

    @api_router.post(PREFIX + "/generate")
    async def generate_pulse(
        send: bool = Query(default=False),
        actor: dict = Depends(require_safety_or_admin),
    ):
        snapshot = await build_pulse_snapshot(db)
        pulse_id = str(uuid.uuid4())
        html = render_pulse_email(snapshot)
        subject = f"MASCI Trench Safety Pulse — Week of {snapshot['week_of']}"
        recipients = await _resolve_recipients()
        delivery: Dict[str, Any] = {
            "status": "not_sent",
            "recipient_count": 0,
            "recipients": [],
            "errors": [],
        }
        if send:
            try:
                from server import _trench_send_email  # noqa: PLC0415
            except Exception as e:  # noqa: BLE001
                _trench_send_email = None
                delivery["errors"].append(f"import: {e}")
            if _trench_send_email and recipients:
                sent_count = 0
                for r in recipients:
                    try:
                        ok = await _trench_send_email(r, subject, html)
                        if ok:
                            sent_count += 1
                            delivery["recipients"].append(r)
                    except Exception as e:  # noqa: BLE001
                        delivery["errors"].append(f"{r}: {e}")
                delivery["status"] = "sent" if sent_count > 0 else "skipped"
                delivery["recipient_count"] = sent_count
            elif not recipients:
                delivery["status"] = "no_recipients"
            else:
                delivery["status"] = "email_disabled"
        doc = {
            "id": pulse_id,
            "generated_at": snapshot["generated_at"],
            "week_of": snapshot["week_of"],
            "generated_by": (actor or {}).get("email") or "system",
            "subject": subject,
            "snapshot": snapshot,
            "delivery": delivery,
            "score": snapshot["health"]["score"],
            "rating": snapshot["health"]["rating"],
        }
        await db.trench_safety_pulses.insert_one(doc)
        doc.pop("_id", None)
        await write_audit(
            db, kind="trench_safety_pulse_generated", asset_id="(pulse)",
            actor=actor, detail={
                "pulse_id": pulse_id,
                "send": bool(send),
                "delivery_status": delivery["status"],
                "recipient_count": delivery["recipient_count"],
                "score": doc["score"],
                "rating": doc["rating"],
            },
        )
        return doc

    @api_router.get(PREFIX + "/current")
    async def current_pulse(_actor: dict = Depends(require_any_portal)):
        latest = await db.trench_safety_pulses.find_one(
            {}, {"_id": 0}, sort=[("generated_at", -1)],
        )
        if latest:
            return latest
        # No history yet — build a live snapshot for the Hub Card
        snapshot = await build_pulse_snapshot(db)
        return {
            "id": None,
            "generated_at": snapshot["generated_at"],
            "week_of": snapshot["week_of"],
            "snapshot": snapshot,
            "score": snapshot["health"]["score"],
            "rating": snapshot["health"]["rating"],
            "delivery": {"status": "live_preview", "recipient_count": 0},
            "subject": f"MASCI Trench Safety Pulse — Week of {snapshot['week_of']}",
            "generated_by": "live",
        }

    @api_router.get(PREFIX + "/history")
    async def pulse_history(
        limit: int = Query(default=52, ge=1, le=200),
        _actor: dict = Depends(require_any_portal),
    ):
        items = await db.trench_safety_pulses.find(
            {}, {"_id": 0, "snapshot": 0},  # exclude full snapshot for list
        ).sort("generated_at", -1).limit(limit).to_list(limit)
        return {"items": items, "count": len(items)}

    @api_router.get(PREFIX + "/{pulse_id}")
    async def pulse_detail(
        pulse_id: str,
        _actor: dict = Depends(require_any_portal),
    ):
        doc = await db.trench_safety_pulses.find_one({"id": pulse_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Pulse not found")
        return doc

    @api_router.get(PREFIX + "/{pulse_id}/html")
    async def pulse_html(
        pulse_id: str,
        _actor: dict = Depends(require_any_portal),
    ):
        from fastapi.responses import HTMLResponse  # noqa: PLC0415
        doc = await db.trench_safety_pulses.find_one({"id": pulse_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Pulse not found")
        return HTMLResponse(render_pulse_email(doc.get("snapshot", {})))
