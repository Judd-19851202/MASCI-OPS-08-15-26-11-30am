"""Aggregate dashboard endpoint — used by Safety/Admin trench-safety hub."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from ._models import (
    ASSET_TYPES,
    CONDITIONS,
    OPERATIONAL_STATUSES,
)


def register_dashboard_routes(
    api_router: APIRouter,
    db,
    require_any_portal,
) -> None:

    @api_router.get("/trench-safety/dashboard")
    async def dashboard(_actor: dict = Depends(require_any_portal)):
        # Pull every active + retired asset once for in-memory roll-up.
        # 7 seeded units today; ceiling of a few hundred even at fleet
        # scale — single-query aggregate is fine.
        docs: List[Dict[str, Any]] = await db.trench_safety_assets.find(
            {}, {"_id": 0}
        ).to_list(5000)

        counts_by_type = {t: 0 for t in ASSET_TYPES}
        counts_by_status = {s: 0 for s in OPERATIONAL_STATUSES}
        # Active-scoped status counts (is_active only) so the executive
        # summary can present an internally-reconciling ACTIVE breakdown,
        # distinct from the all-lifecycle counts_by_status below.
        counts_by_status_active = {s: 0 for s in OPERATIONAL_STATUSES}
        counts_by_condition = {c: 0 for c in CONDITIONS}
        active = 0
        missing_serial = 0
        missing_manufacturer = 0
        missing_tabulated = 0
        needs_review = 0

        for d in docs:
            t = d.get("asset_type") or "Trench Box"
            s = d.get("operational_status") or "Available"
            c = d.get("condition") or "Good"
            counts_by_type[t] = counts_by_type.get(t, 0) + 1
            counts_by_status[s] = counts_by_status.get(s, 0) + 1
            counts_by_condition[c] = counts_by_condition.get(c, 0) + 1
            if d.get("is_active"):
                active += 1
                counts_by_status_active[s] = counts_by_status_active.get(s, 0) + 1
            if d.get("missing_serial_number"):
                missing_serial += 1
            if d.get("missing_manufacturer"):
                missing_manufacturer += 1
            if d.get("tabulated_data_missing"):
                missing_tabulated += 1
            if d.get("needs_review"):
                needs_review += 1

        # Open repairs
        open_repairs = await db.trench_safety_repairs.count_documents(
            {"status": {"$in": ["Open", "In Progress"]}}
        )

        # Inspections due — assets whose last_inspection_at is null or
        # older than 30 days (Daily) / 365 days (Monthly is implementation
        # detail, for the dashboard we surface "no inspection on record").
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        inspections_due = sum(
            1
            for d in docs
            if d.get("is_active")
            and (not d.get("last_inspection_at") or d["last_inspection_at"] < cutoff)
        )

        # Certifications expiring inside 30 days
        cert_cutoff = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        certs_expiring = sum(
            1
            for d in docs
            if d.get("certification_expires_at")
            and d["certification_expires_at"] <= cert_cutoff
        )

        # Phase 8B — additional operational alerts derived from existing
        # collections. No new collections, no parallel state.
        # Active assets only — retired plates don't generate work.
        active_docs = [d for d in docs if d.get("is_active")]

        on_hold_count = sum(
            1 for d in active_docs
            if d.get("operational_status") in {
                "Inspection Hold", "Maintenance Hold",
                "Safety Hold", "Certification Hold",
            }
        )

        no_project = sum(
            1 for d in active_docs
            if not d.get("current_project_id") and not d.get("current_project_name")
        )

        # Photos: assets that have zero rows in trench_safety_photos
        photo_rows = await db.trench_safety_photos.aggregate([
            {"$group": {"_id": "$asset_id", "n": {"$sum": 1}}},
        ]).to_list(5000)
        assets_with_photos = {r["_id"] for r in photo_rows}
        missing_photos = sum(
            1 for d in active_docs
            if d.get("asset_id") not in assets_with_photos
        )

        # Road Plates without rated_capacity_lb captured
        road_plate_missing_capacity = sum(
            1 for d in active_docs
            if d.get("asset_type") == "Road Plate"
            and not d.get("rated_capacity_lb")
        )

        # Recent activity — events in audit_events within last 7 days
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        recent_activity_7d = await db.audit_events.count_documents(
            {"kind": {"$regex": "^trench_"}, "ts": {"$gte": seven_days_ago}}
        )

        return {
            "total_active_assets": active,
            "total_all_assets": len(docs),
            "counts_by_type": counts_by_type,
            "counts_by_status": counts_by_status,
            "counts_by_status_active": counts_by_status_active,
            "counts_by_condition": counts_by_condition,
            # Scope contract — each block below is a GOVERNED-DISTINCT
            # population/window; the UI must not present them as one
            # denominator. total_active_assets (is_active flag) and
            # counts_by_status_active are the in-service population;
            # counts_by_status/_type/_condition + total_all_assets cover
            # ALL lifecycle states incl. retired & inactive; alerts.* are
            # active-scoped work signals; recent_activity_7d is an
            # audit-event count over the last 7 days (a different entity).
            "scopes": {
                "total_active_assets": "assets where is_active=true (in-service)",
                "counts_by_status_active": "operational_status buckets over in-service (is_active) assets",
                "counts_by_status": "operational_status buckets over ALL assets (incl. retired & inactive)",
                "counts_by_type": "asset_type buckets over ALL assets",
                "total_all_assets": "every asset row incl. retired & inactive",
                "alerts": "work signals scoped to in-service (is_active) assets + open repairs",
                "recent_activity_7d": "audit_events (kind trench_*) within the last 7 days",
            },
            "alerts": {
                "missing_serial_number": missing_serial,
                "missing_manufacturer": missing_manufacturer,
                "missing_tabulated_data": missing_tabulated,
                "needs_review": needs_review,
                "open_repairs": open_repairs,
                "inspections_due": inspections_due,
                "certifications_expiring": certs_expiring,
                # Phase 8B additions
                "on_hold": on_hold_count,
                "no_project_assignment": no_project,
                "missing_photos": missing_photos,
                "road_plate_missing_capacity": road_plate_missing_capacity,
            },
            "recent_activity_7d": recent_activity_7d,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
