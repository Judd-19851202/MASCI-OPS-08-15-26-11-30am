"""TRACK 16.12 · Prediction Engine.

Deterministic forecasts derived from existing expirations + action
items. No ML, no probabilistic guessing — every forecast can be traced
back to the record that generated it.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from lib.transport_intelligence_core import (
    TENANT, SCHEMA_VERSION, now_iso, days_until,
    write_intelligence_audit,
)


def _bucket(days: Optional[int]) -> str:
    if days is None:
        return "unknown"
    if days < 0:
        return "overdue"
    if days <= 7:
        return "due_this_week"
    if days <= 30:
        return "due_30_days"
    if days <= 90:
        return "due_90_days"
    return "beyond_horizon"


async def _doc_forecasts(db) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    cur = db.driver_documents.find({"tenant": TENANT})
    for d in await cur.to_list(2000):
        days = days_until(d.get("expires_at"))
        if days is None or days > 120:
            continue
        out.append({
            "kind": "documentation_expiration",
            "subject_type": "driver_document",
            "subject_id": d.get("id"),
            "transport_person_id": d.get("transport_person_id"),
            "due_in_days": days,
            "bucket": _bucket(days),
            "record_label": d.get("document_type"),
        })
    return out


async def _inspection_forecasts(db) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        cur = db.transport_truck_inspections.find({"tenant": TENANT})
        for ins in await cur.to_list(2000):
            days = days_until(ins.get("expires_at"))
            if days is None or days > 120:
                continue
            out.append({
                "kind": "inspection_expiration",
                "subject_type": "transport_truck_inspection",
                "subject_id": ins.get("id"),
                "transport_truck_id": ins.get("transport_truck_id"),
                "due_in_days": days,
                "bucket": _bucket(days),
                "record_label": "Hauler Readiness Inspection",
            })
    except Exception:  # noqa: BLE001
        pass
    return out


async def _orientation_forecasts(db) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        cur = db.transport_certificates.find({"tenant": TENANT})
        for c in await cur.to_list(2000):
            days = days_until(c.get("expires_at"))
            if days is None or days > 120:
                continue
            out.append({
                "kind": "orientation_renewal",
                "subject_type": "transport_certificate",
                "subject_id": c.get("id"),
                "transport_person_id": c.get("transport_person_id"),
                "due_in_days": days,
                "bucket": _bucket(days),
                "record_label": "Orientation certificate",
            })
    except Exception:  # noqa: BLE001
        pass
    return out


def _risk_from_actions(actions: List[Dict[str, Any]]) -> str:
    sev = {"critical": 0, "block": 0, "warn": 0, "info": 0,
            "blocking": 0, "urgent": 0}
    for a in actions:
        s = (a.get("severity") or "info")
        sev[s] = sev.get(s, 0) + 1
    if sev["critical"] or sev["blocking"]:
        return "high"
    if sev["block"] or sev["urgent"] or sev["warn"] >= 3:
        return "elevated"
    if sev["warn"]:
        return "watch"
    return "low"


async def carrier_risk_forecast(db) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    carriers = await db.carriers.find({"tenant": TENANT}).to_list(500)
    for c in carriers:
        actions = await db.transport_action_items.find({
            "tenant": TENANT,
            "status": {"$in": ["open", "in_progress"]},
            "$or": [{"entity_id": c["id"]},
                     {"entity_type": "carrier", "entity_id": c["id"]}],
        }).to_list(200)
        out.append({
            "kind": "carrier_risk",
            "subject_type": "carrier", "subject_id": c["id"],
            "carrier_legal_name": c.get("legal_name"),
            "risk": _risk_from_actions(actions),
            "open_actions": len(actions),
        })
    return out


async def compute_predictions(db) -> Dict[str, Any]:
    doc = await _doc_forecasts(db)
    insp = await _inspection_forecasts(db)
    orient = await _orientation_forecasts(db)
    carrier_risk = await carrier_risk_forecast(db)

    by_bucket: Dict[str, int] = {}
    for r in doc + insp + orient:
        b = r.get("bucket", "unknown")
        by_bucket[b] = by_bucket.get(b, 0) + 1

    report = {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "generated_at": now_iso(),
        "horizon_days": 120,
        "by_bucket": by_bucket,
        "documentation_expirations": doc,
        "inspection_expirations": insp,
        "orientation_renewals": orient,
        "carrier_risk": carrier_risk,
        "summary": {
            "documentation": len(doc),
            "inspections": len(insp),
            "orientations": len(orient),
            "carriers_with_risk": sum(
                1 for r in carrier_risk if r["risk"] in ("high", "elevated")),
        },
    }
    await write_intelligence_audit(
        db, kind="predictions_refresh",
        subject_type="predictions", subject_id=None,
        snapshot={"summary": report["summary"], "by_bucket": by_bucket})
    return report
