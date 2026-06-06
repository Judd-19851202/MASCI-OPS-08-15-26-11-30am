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

        return {
            "total_active_assets": active,
            "total_all_assets": len(docs),
            "counts_by_type": counts_by_type,
            "counts_by_status": counts_by_status,
            "counts_by_condition": counts_by_condition,
            "alerts": {
                "missing_serial_number": missing_serial,
                "missing_manufacturer": missing_manufacturer,
                "missing_tabulated_data": missing_tabulated,
                "needs_review": needs_review,
                "open_repairs": open_repairs,
                "inspections_due": inspections_due,
                "certifications_expiring": certs_expiring,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
