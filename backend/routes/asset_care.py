"""routes/asset_care.py · Track 13.33ABC.

Operational Asset Care & Readiness Command Center.

Endpoints (all under /api/asset-care/, admin · asset-admin only):
  GET /summary       Executive snapshot (counts)
  GET /readiness     Per-asset readiness list (Ready / Warning / Not Ready / Needs Review)
  GET /work-queue    Asset Admin daily buckets
  GET /alerts        Renewal fan-out (expired · 7d · 30d · 60d · 90d)
  GET /notifications-matrix  Static notification matrix (event → audience → resolution)

Reads existing collections only:
  • equipment_master
  • operational_attachments (host_kind="asset")
  • fleet_defect_items     (open defects)
  • equipment_inspections  (pre-op / DVIR results)
  • asset_required_doc_overrides

NO new collection. NO new map engine. NO RTS authority.
Readiness is ADVISORY only — Shop & Dispatch hard locks preserved.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from services.required_documents import (
    ASSET_DOC_TYPES, doc_label, required_documents_for, renewal_mirror_field,
)


def _days_to(date_iso: Optional[str]) -> Optional[int]:
    if not date_iso:
        return None
    try:
        d = datetime.fromisoformat(str(date_iso).replace("Z", "+00:00")).date()
        return (d - date.today()).days
    except Exception:
        return None


RENEWAL_FIELDS = [
    ("registration_expiration", "Registration"),
    ("insurance_expiration",    "Insurance"),
    ("dot_expiration",          "DOT"),
    ("calibration_expiration",  "Calibration"),
    ("inspection_expiration",   "Inspection"),
    ("warranty_expiration",     "Warranty"),
]


def _classify(asset: Dict[str, Any], required_docs: List[str],
              present_doc_types: set, open_defects_count: int) -> Dict[str, Any]:
    """Derive readiness status — Ready / Warning / Not Ready / Needs Review.
    Returns {status, reasons[]} — read-only advisory."""
    reasons: List[str] = []
    asset_type = asset.get("asset_type")
    lifecycle = (asset.get("lifecycle_status") or "").lower()
    taxonomy_verified = bool(asset.get("taxonomy_verified"))

    # Needs Review
    if not asset_type or not taxonomy_verified:
        if lifecycle in ("retired", "disposed", "sold"):
            return {"status": "Not Ready", "reasons": ["Asset retired"]}
        return {
            "status": "Needs Review",
            "reasons": ["Asset classification needs verification"],
        }

    # Lifecycle terminal states
    if lifecycle in ("retired", "disposed", "sold"):
        return {"status": "Not Ready", "reasons": ["Asset retired"]}

    not_ready = False

    # Renewals — Not Ready when expired (any tracked renewal)
    for field, label in RENEWAL_FIELDS:
        days = _days_to(asset.get(field))
        if days is None:
            continue
        if days < 0:
            not_ready = True
            reasons.append(f"{label} expired ({-days}d ago)")
        elif days <= 7:
            reasons.append(f"{label} expires in {days}d")
        elif days <= 30:
            reasons.append(f"{label} expires in {days}d")

    # Required docs missing
    missing_req = [d for d in required_docs if d not in present_doc_types]
    if missing_req:
        critical = {"registration", "insurance_card", "dot_document",
                    "calibration_certificate", "inspection_certificate"}
        missing_critical = [d for d in missing_req if d in critical]
        if missing_critical:
            not_ready = True
            reasons.extend(
                f"Missing {doc_label(d)}" for d in missing_critical[:3]
            )
        else:
            reasons.extend(f"Pending {doc_label(d)}" for d in missing_req[:3])

    # Open defects
    if open_defects_count > 0:
        not_ready = True
        reasons.append(
            f"{open_defects_count} open defect{'s' if open_defects_count != 1 else ''}"
        )

    # Maintenance hold / OOS
    if asset.get("maintenance_hold") or asset.get("out_of_service"):
        not_ready = True
        reasons.append("Maintenance hold / OOS")

    if not_ready:
        return {"status": "Not Ready", "reasons": reasons[:5]}
    if reasons:
        return {"status": "Warning", "reasons": reasons[:5]}
    return {"status": "Ready", "reasons": []}


def register_asset_care_routes(app, db, require_admin_dep: Callable, require_admin_or_asset_admin_dep: Optional[Callable] = None) -> APIRouter:
    router = APIRouter(prefix="/api/asset-care", tags=["asset-care"])

    # TRACK 15.13E — read dep for the Asset Care portal read endpoints
    # (summary · readiness · alerts · work-queue · notifications-matrix).
    # Defaults to the legacy admin/PM gate for back-compat.
    _read_dep = require_admin_or_asset_admin_dep or require_admin_dep

    async def _gather(asset_type_filter: Optional[str] = None):
        q: Dict[str, Any] = {"$or": [
            {"is_active": True},
            {"active": True},
            {"status": {"$nin": ["retired", "disposed", "sold"]}},
        ]}
        if asset_type_filter:
            q["asset_type"] = asset_type_filter
        cur = db.equipment_master.find(q, {"_id": 0})
        assets = [a async for a in cur]
        ids = {a.get("id") for a in assets}
        # Documents grouped by asset
        docs_cur = db.operational_attachments.find(
            {"host_kind": "asset", "host_id": {"$in": list(ids)}},
            {"_id": 0, "host_id": 1, "type": 1, "expiration_date": 1},
        )
        docs_by: Dict[str, set] = {}
        async for d in docs_cur:
            docs_by.setdefault(d.get("host_id"), set()).add(d.get("type"))
        # Open defects per asset (best-effort)
        defects_by: Dict[str, int] = {}
        try:
            dc = db.fleet_defect_items.find(
                {"status": {"$nin": ["resolved", "closed", "cleared", "wo_completed"]}},
                {"_id": 0, "equipment_master_id": 1, "unit_number": 1},
            )
            unit_to_id = {a.get("unit_number"): a.get("id") for a in assets}
            async for d in dc:
                aid = d.get("equipment_master_id") or unit_to_id.get(d.get("unit_number"))
                if aid:
                    defects_by[aid] = defects_by.get(aid, 0) + 1
        except Exception:
            pass
        # Overrides for required docs
        overrides_cur = db.asset_required_doc_overrides.find({}, {"_id": 0})
        overrides_map: Dict[str, Dict[str, str]] = {}
        async for row in overrides_cur:
            overrides_map[row["asset_type"]] = row.get("levels") or {}
        try:
            from services.asset_taxonomy import behavior_for
        except Exception:
            behavior_for = lambda _: {}  # noqa: E731

        results = []
        for a in assets:
            at = a.get("asset_type")
            base = required_documents_for(at, behavior_for(at) if at else {})
            ov = overrides_map.get(at, {})
            required = [d for d in base if ov.get(d, "required") == "required"]
            for d, lvl in ov.items():
                if lvl == "required" and d in ASSET_DOC_TYPES and d not in required:
                    required.append(d)
            present = docs_by.get(a.get("id"), set())
            cls = _classify(a, required, present, defects_by.get(a.get("id"), 0))
            results.append({
                "asset_id": a.get("id"),
                "unit_number": a.get("unit_number") or a.get("display_label") or a.get("id"),
                "asset_class": a.get("asset_class"),
                "asset_type": at,
                "lifecycle_status": a.get("lifecycle_status"),
                "readiness_status": cls["status"],
                "reasons": cls["reasons"],
                "open_defects": defects_by.get(a.get("id"), 0),
                "missing_required": [d for d in required if d not in present],
                "taxonomy_verified": bool(a.get("taxonomy_verified")),
            })
        return results

    @router.get("/summary")
    async def summary(actor=Depends(_read_dep)):  # noqa: ARG001
        rows = await _gather()
        counts = {"Ready": 0, "Warning": 0, "Not Ready": 0, "Needs Review": 0}
        missing_docs_total = 0
        for r in rows:
            counts[r["readiness_status"]] = counts.get(r["readiness_status"], 0) + 1
            missing_docs_total += len(r["missing_required"])
        # Renewals buckets
        bucket = {"expired": 0, "7": 0, "30": 0, "60": 0, "90": 0}
        async for a in db.equipment_master.find(
            {"$or": [{"is_active": True}, {"active": True}]},
            {"_id": 0, **{f: 1 for f, _ in RENEWAL_FIELDS}},
        ):
            for f, _ in RENEWAL_FIELDS:
                d = _days_to(a.get(f))
                if d is None:
                    continue
                if d < 0: bucket["expired"] += 1
                elif d <= 7: bucket["7"] += 1
                elif d <= 30: bucket["30"] += 1
                elif d <= 60: bucket["60"] += 1
                elif d <= 90: bucket["90"] += 1
        return {
            "total_assets": len(rows),
            "readiness": counts,
            "missing_documents_total": missing_docs_total,
            "renewals": bucket,
        }

    @router.get("/readiness")
    async def readiness(
        status: Optional[str] = Query(default=None),
        asset_type: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=1000),
        actor=Depends(_read_dep),  # noqa: ARG001
    ):
        rows = await _gather(asset_type)
        if status:
            rows = [r for r in rows if r["readiness_status"].lower() == status.lower()]
        order = {"Not Ready": 0, "Warning": 1, "Needs Review": 2, "Ready": 3}
        rows.sort(key=lambda r: order.get(r["readiness_status"], 9))
        return {"count": len(rows), "items": rows[:limit]}

    @router.get("/work-queue")
    async def work_queue(actor=Depends(_read_dep)):  # noqa: ARG001
        rows = await _gather()
        gps_survey_tech = {"GPS / Machine Control", "Survey Equipment", "Technology Equipment"}
        return {
            "needs_classification_review": [r for r in rows if r["readiness_status"] == "Needs Review"][:50],
            "missing_required_documents": [r for r in rows if r["missing_required"]][:50],
            "gps_survey_tech_review": [
                r for r in rows
                if r.get("asset_class") in gps_survey_tech
                and (not r.get("taxonomy_verified") or r["readiness_status"] != "Ready")
            ][:50],
            "open_defects": [r for r in rows if r["open_defects"] > 0][:50],
        }

    @router.get("/alerts")
    async def alerts(actor=Depends(_read_dep)):  # noqa: ARG001
        out: List[Dict[str, Any]] = []
        async for a in db.equipment_master.find(
            {"$or": [{"is_active": True}, {"active": True}]},
            {"_id": 0, "id": 1, "unit_number": 1, "display_label": 1,
             "asset_type": 1, **{f: 1 for f, _ in RENEWAL_FIELDS}},
        ):
            for field, label in RENEWAL_FIELDS:
                d = _days_to(a.get(field))
                if d is None or d > 90:
                    continue
                if d < 0:
                    bucket = "Expired"; severity = "critical"
                elif d <= 7:
                    bucket = "Due in 7 days"; severity = "high"
                elif d <= 30:
                    bucket = "Due in 30 days"; severity = "medium"
                elif d <= 60:
                    bucket = "Due in 60 days"; severity = "low"
                else:
                    bucket = "Due in 90 days"; severity = "info"
                out.append({
                    "asset_id": a.get("id"),
                    "unit_number": a.get("unit_number") or a.get("display_label") or a.get("id"),
                    "asset_type": a.get("asset_type"),
                    "renewal_type": label,
                    "expiration_date": a.get(field),
                    "days_remaining": d,
                    "bucket": bucket,
                    "severity": severity,
                    "recommended_action": f"Upload renewed {label} document or update expiration date.",
                    "open_asset_profile": f"/admin/assets/{a.get('id')}?tab=documents",
                })
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        out.sort(key=lambda x: (order.get(x["severity"], 9), x["days_remaining"]))
        return {"count": len(out), "items": out[:500]}

    @router.get("/notifications-matrix")
    async def notifications_matrix(actor=Depends(_read_dep)):  # noqa: ARG001
        events = [
            # (event, trigger, audience, dashboard, resolution)
            ("registration_expired",       "Renewal date < today",      ["Asset Admin", "Ops"],   True,  "Upload renewed Registration"),
            ("registration_expiring",      "Renewal date in 30 days",   ["Asset Admin"],          True,  "Upload renewed Registration"),
            ("insurance_expired",          "Renewal date < today",      ["Asset Admin", "Ops"],   True,  "Upload renewed Insurance"),
            ("insurance_expiring",         "Renewal date in 30 days",   ["Asset Admin"],          True,  "Upload renewed Insurance"),
            ("dot_expired",                "Renewal date < today",      ["Asset Admin", "Dispatch"], True, "Upload renewed DOT document"),
            ("dot_expiring",               "Renewal date in 30 days",   ["Asset Admin"],          True,  "Upload renewed DOT document"),
            ("calibration_expired",        "Renewal date < today",      ["Asset Admin"],          True,  "Schedule calibration"),
            ("calibration_expiring",       "Renewal date in 30 days",   ["Asset Admin"],          True,  "Schedule calibration"),
            ("inspection_expired",         "Renewal date < today",      ["Asset Admin"],          True,  "Schedule inspection"),
            ("inspection_expiring",        "Renewal date in 30 days",   ["Asset Admin"],          True,  "Schedule inspection"),
            ("warranty_expiring",          "Renewal date in 60 days",   ["Asset Admin"],          True,  "Review warranty options"),
            ("required_document_missing",  "Required doc not on file",  ["Asset Admin"],          True,  "Upload required document"),
            ("asset_photo_missing",        "Suggested photos missing",  ["Asset Admin"],          True,  "Upload Asset Photo (optional)"),
            ("asset_classification_review", "taxonomy_verified=false",  ["Asset Admin"],          True,  "Verify class/type on Review Queue"),
            ("new_asset_added",            "POST /asset-spine/assets",  ["Asset Admin", "Ops"],   True,  "—"),
            ("asset_retired",              "lifecycle_status=retired",  ["Asset Admin", "Ops"],   True,  "Resolve all open alerts"),
            ("asset_transferred",          "Transfer recorded",         ["Asset Admin", "Dispatch"], True, "—"),
            ("asset_assigned",             "Assignment recorded",       ["Asset Admin", "PM"],    True,  "—"),
            ("employee_offboarded_assets", "Offboarding with assets",   ["Asset Admin", "HR"],    True,  "Reclaim assigned assets"),
            ("preop_failed",               "Pre-Op fail_count > 0",     ["Shop", "Asset Admin"],  True,  "Shop triage"),
            ("dvir_failed",                "DVIR fail_count > 0",       ["Shop", "Dispatch"],     True,  "Shop triage"),
            ("asset_oos",                  "out_of_service=true",       ["Shop", "Dispatch"],     True,  "Shop repair"),
            ("maintenance_hold",           "maintenance_hold=true",     ["Shop", "Dispatch"],     True,  "Shop release"),
            ("pm_overdue",                 "PM past due",               ["Shop", "PM"],           True,  "Schedule PM"),
            ("pm_due_soon",                "PM within window",          ["PM"],                   True,  "Schedule PM"),
        ]
        return {
            "count": len(events),
            "items": [
                {
                    "event": e[0],
                    "trigger": e[1],
                    "audience": e[2],
                    "dashboard_visible": e[3],
                    "in_app_notification": False,  # foundation only · delivery deferred
                    "email": False,
                    "resolution": e[4],
                }
                for e in events
            ],
            "delivery_status": {
                "dashboard": "live",
                "in_app_notification": "deferred · platform notification center not yet built",
                "email": "deferred · awaits Resend integration for renewal cadence",
                "sms": "out_of_scope",
            },
        }

    app.include_router(router)
    return router
