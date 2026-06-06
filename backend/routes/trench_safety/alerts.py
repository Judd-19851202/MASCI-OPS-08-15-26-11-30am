"""Trench Safety alerts — Phase 4B derived view.

NO new alerts collection. This endpoint computes alerts on-demand from
the existing source-of-truth collections (assets, holds, certifications,
inspections, repairs). This guarantees the alert feed cannot drift from
the operational state.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from ._helpers import certification_status_for


_KIND_SEVERITY = {
    "critical_damage":       "Critical",
    "expired_certification": "Major",
    "missing_certification": "Major",
    "failed_inspection":     "Major",
    "hold_applied":          "Major",
    "due_soon_30":           "Minor",
    "due_soon_60":           "Minor",
    "due_soon_90":           "Minor",
    "inspection_overdue":    "Minor",
}


def register_alerts_routes(
    api_router: APIRouter,
    db,
    *,
    require_any_portal,
) -> None:

    @api_router.get("/trench-safety/alerts")
    async def list_alerts(
        asset_id: Optional[str] = Query(default=None),
        kind: Optional[str] = Query(default=None),
        _actor: dict = Depends(require_any_portal),
    ):
        now = datetime.now(timezone.utc)
        # 1. Active assets
        a_q: Dict[str, Any] = {"is_active": True}
        if asset_id:
            a_q["asset_id"] = asset_id
        assets = await db.trench_safety_assets.find(a_q, {"_id": 0}).to_list(2000)
        asset_by_id = {a["asset_id"]: a for a in assets}
        asset_ids = list(asset_by_id.keys())

        # 2. Active holds
        holds = await db.trench_safety_holds.find(
            {"asset_id": {"$in": asset_ids}, "is_active": True},
            {"_id": 0},
        ).to_list(5000)

        # 3. Active certifications
        certs = await db.trench_safety_certifications.find(
            {"asset_id": {"$in": asset_ids}, "status": "Active"},
            {"_id": 0},
        ).to_list(5000)
        certs_by_asset: Dict[str, List[Dict]] = {}
        for c in certs:
            certs_by_asset.setdefault(c["asset_id"], []).append(c)

        # 4. Latest inspections
        # Lightweight: pull the most recent fail per asset, plus
        # last_inspection_at metadata already on the asset.
        latest_fail = {}
        async for ins in db.trench_safety_inspections.find(
            {"asset_id": {"$in": asset_ids}, "result": "Fail"},
            {"_id": 0},
        ).sort("submitted_at", -1).limit(500):
            if ins["asset_id"] not in latest_fail:
                latest_fail[ins["asset_id"]] = ins

        inspection_cutoff = (now - timedelta(days=30)).isoformat()
        alerts: List[Dict[str, Any]] = []

        # Hold alerts (one per active hold)
        for h in holds:
            alerts.append({
                "asset_id":   h["asset_id"],
                "kind":       "hold_applied",
                "hold_kind":  h["kind"],
                "severity":   "Critical" if h["kind"] == "Safety Hold" else "Major",
                "opened_at":  h.get("opened_at"),
                "message":    f"{h['kind']} active: {h.get('reason') or 'reason not recorded'}",
                "link":       f"/safety/trench-safety/assets/{h['asset_id']}",
                "source_ref": h.get("source_ref"),
            })
            # Surface critical_damage as a distinct alert kind too
            if h["kind"] == "Safety Hold":
                alerts.append({
                    "asset_id":   h["asset_id"],
                    "kind":       "critical_damage",
                    "severity":   "Critical",
                    "opened_at":  h.get("opened_at"),
                    "message":    f"Critical damage / safety event recorded: {h.get('reason') or ''}".strip(),
                    "link":       f"/safety/trench-safety/assets/{h['asset_id']}",
                    "source_ref": h.get("source_ref"),
                })

        # Certification alerts (per asset)
        for aid, a in asset_by_id.items():
            if not a.get("requires_certification"):
                continue
            a_certs = certs_by_asset.get(aid, [])
            cstatus = certification_status_for(True, a_certs, now)
            if cstatus == "Missing":
                alerts.append({
                    "asset_id":  aid,
                    "kind":      "missing_certification",
                    "severity":  "Major",
                    "opened_at": a.get("updated_at"),
                    "message":   "Required certification missing — upload to clear hold",
                    "link":      f"/safety/trench-safety/assets/{aid}",
                })
                continue
            if cstatus == "Expired":
                alerts.append({
                    "asset_id":  aid,
                    "kind":      "expired_certification",
                    "severity":  "Major",
                    "opened_at": a.get("updated_at"),
                    "message":   "All certifications expired",
                    "link":      f"/safety/trench-safety/assets/{aid}",
                })
                continue
            # Due Soon — calculate the closest expiration window
            soonest_days = None
            for c in a_certs:
                exp = c.get("expires_at") or ""
                try:
                    if len(exp) == 10:
                        dt = datetime.strptime(exp, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    else:
                        dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
                except Exception:  # noqa: BLE001
                    continue
                d = (dt - now).days
                if soonest_days is None or d < soonest_days:
                    soonest_days = d
            if soonest_days is None:
                continue
            if soonest_days <= 30:
                k = "due_soon_30"
            elif soonest_days <= 60:
                k = "due_soon_60"
            elif soonest_days <= 90:
                k = "due_soon_90"
            else:
                continue
            alerts.append({
                "asset_id":  aid,
                "kind":      k,
                "severity":  "Minor",
                "opened_at": a.get("updated_at"),
                "message":   f"Certification expires in {soonest_days} days",
                "link":      f"/safety/trench-safety/assets/{aid}",
            })

        # Failed inspection alerts (latest fail per asset that's still open)
        for aid, ins in latest_fail.items():
            a = asset_by_id.get(aid)
            if not a:
                continue
            # Only surface if asset still on Inspection Hold or Safety Hold from inspection
            holds_for_asset = [h["kind"] for h in holds if h["asset_id"] == aid]
            if "Inspection Hold" not in holds_for_asset and "Safety Hold" not in holds_for_asset:
                continue
            alerts.append({
                "asset_id":   aid,
                "kind":       "failed_inspection",
                "severity":   "Critical" if ins.get("severity") == "Critical" else "Major",
                "opened_at":  ins.get("submitted_at"),
                "message":    f"Failed {ins.get('inspection_type','Inspection')} (severity {ins.get('severity','None')})",
                "link":       f"/safety/trench-safety/assets/{aid}",
                "source_ref": f"inspection:{ins.get('id')}",
            })

        # Inspection overdue alerts
        for aid, a in asset_by_id.items():
            last = a.get("last_inspection_at")
            if not last or last < inspection_cutoff:
                alerts.append({
                    "asset_id":  aid,
                    "kind":      "inspection_overdue",
                    "severity":  "Minor",
                    "opened_at": last,
                    "message":   "No inspection in the past 30 days" if last else "No inspection on record",
                    "link":      f"/safety/trench-safety/assets/{aid}",
                })

        # Apply optional filter
        if kind:
            alerts = [x for x in alerts if x["kind"] == kind]

        counts: Dict[str, int] = {}
        for x in alerts:
            counts[x["kind"]] = counts.get(x["kind"], 0) + 1

        return {
            "alerts": alerts,
            "count": len(alerts),
            "counts": counts,
            "generated_at": now.isoformat(),
        }
